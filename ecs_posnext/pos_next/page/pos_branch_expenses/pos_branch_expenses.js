frappe.pages["pos-branch-expenses"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Branch Expenses"),
		single_column: true,
	});

	const state = { branches: [], current: null };

	const branch_field = page.add_field({
		fieldname: "pos_profile",
		label: __("Branch"),
		fieldtype: "Select",
		options: [],
		change: () => load(),
	});
	const from_field = page.add_field({
		fieldname: "from_date",
		label: __("From"),
		fieldtype: "Date",
		default: frappe.datetime.month_start(),
		change: () => load(),
	});
	const to_field = page.add_field({
		fieldname: "to_date",
		label: __("To"),
		fieldtype: "Date",
		default: frappe.datetime.month_end(),
		change: () => load(),
	});

	page.set_primary_action(__("New Expense"), () => open_expense_dialog(), "add");
	page.add_menu_item(__("Refresh"), () => load());
	page.add_menu_item(__("Expense Types"), () => frappe.set_route("List", "Expense Claim Type"));

	const $body = $('<div class="bx-wrap" style="padding:12px 4px"></div>').appendTo(page.body);

	frappe
		.call("ecs_posnext.api.branch_expense.get_allowed_branches")
		.then((r) => {
			state.branches = r.message || [];
			if (!state.branches.length) {
				$body.html(empty(__("You are not permitted to record expenses for any branch.")));
				return;
			}
			branch_field.df.options = state.branches.map((b) => b.name);
			branch_field.refresh();
			branch_field.set_value(state.branches[0].name);
		});

	// ------------------------------------------------------------------
	// Loading + rendering
	// ------------------------------------------------------------------
	function load() {
		const pos_profile = branch_field.get_value();
		if (!pos_profile) return;
		$body.html(loading());

		Promise.all([
			frappe.call("ecs_posnext.api.branch_expense.get_branch_expense_state", { pos_profile }),
			frappe.call("ecs_posnext.api.branch_expense.list_expenses", {
				pos_profile,
				from_date: from_field.get_value(),
				to_date: to_field.get_value(),
			}),
		])
			.then(([s, l]) => {
				state.current = s.message;
				render(s.message, l.message);
			})
			.catch(() => $body.html(empty(__("Could not load expenses for this branch."))));
	}

	function render(info, listing) {
		const money = (v) => format_currency(flt(v), info.currency);
		$body.empty();

		$body.append(`
			<div class="row" style="margin-bottom:16px">
				${card(__("Branch Safe Balance"), money(info.branch_safe_balance), info.branch_safe_account || __("Not configured"), "blue")}
				${card(__("Spent Today"), money(info.spent_today), info.pos_profile, "orange")}
				${card(__("Spent in Range"), money(listing.total), `${from_field.get_value()} → ${to_field.get_value()}`, "red")}
			</div>
		`);

		if (!info.branch_safe_account) {
			$body.append(
				`<div class="alert alert-warning">${__(
					"No branch safe account is configured for {0}. Set it in POS Settings before recording expenses.",
					[info.pos_profile]
				)}</div>`
			);
		}
		if (!(info.expense_types || []).length) {
			$body.append(
				`<div class="alert alert-warning">${__(
					"No Expense Type has an account mapped for {0}. Add one under Expense Claim Type.",
					[info.company]
				)}</div>`
			);
		}

		if (!listing.expenses.length) {
			$body.append(empty(__("No expenses recorded in this period.")));
			return;
		}

		const rows = listing.expenses
			.map((e) => {
				const cancelled = e.docstatus === 2 || e.status === "Cancelled";
				return `
				<tr style="${cancelled ? "opacity:.5;text-decoration:line-through" : ""}">
					<td>${frappe.datetime.str_to_user(e.posting_date)}</td>
					<td><a href="/app/pos-branch-expense/${e.name}">${e.name}</a></td>
					<td>${frappe.utils.escape_html(e.expense_claim_type || "")}</td>
					<td class="text-muted small">${frappe.utils.escape_html(e.description || "")}</td>
					<td class="text-right"><b>${money(e.amount)}</b></td>
					<td>${
						e.receipt
							? `<a href="${e.receipt}" target="_blank">${__("View")}</a>`
							: `<span class="text-muted">—</span>`
					}</td>
					<td>${
						e.journal_entry
							? `<a href="/app/journal-entry/${e.journal_entry}">${e.journal_entry}</a>`
							: "—"
					}</td>
					<td class="text-center">${
						cancelled
							? `<span class="indicator-pill red">${__("Cancelled")}</span>`
							: `<button class="btn btn-xs btn-danger bx-cancel" data-name="${e.name}">${__("Cancel")}</button>`
					}</td>
				</tr>`;
			})
			.join("");

		$body.append(`
			<div class="frappe-card" style="padding:0;overflow-x:auto">
				<table class="table table-hover" style="margin:0">
					<thead>
						<tr>
							<th>${__("Date")}</th><th>${__("Expense")}</th><th>${__("Type")}</th>
							<th>${__("Description")}</th><th class="text-right">${__("Amount")}</th>
							<th>${__("Receipt")}</th><th>${__("Journal Entry")}</th><th></th>
						</tr>
					</thead>
					<tbody>${rows}</tbody>
				</table>
			</div>
		`);

		$body.find(".bx-cancel").on("click", function () {
			const name = $(this).data("name");
			frappe.confirm(
				__("Cancel expense {0}? Its Journal Entry will be reversed and the money returns to the branch safe.", [name]),
				() => {
					frappe.call({
						method: "ecs_posnext.api.branch_expense.cancel_expense",
						args: { name },
						freeze: true,
						callback: () => {
							frappe.show_alert({ message: __("Expense cancelled."), indicator: "orange" });
							load();
						},
					});
				}
			);
		});
	}

	// ------------------------------------------------------------------
	// New expense
	// ------------------------------------------------------------------
	function open_expense_dialog() {
		const info = state.current;
		if (!info) return;
		if (!info.branch_safe_account) {
			frappe.msgprint(__("Configure the branch safe account before recording expenses."));
			return;
		}
		const types = info.expense_types || [];
		if (!types.length) {
			frappe.msgprint(__("Map at least one Expense Claim Type to an account for {0} first.", [info.company]));
			return;
		}

		const d = new frappe.ui.Dialog({
			title: __("New Expense — {0}", [info.pos_profile]),
			fields: [
				{
					fieldtype: "HTML",
					options: `<div class="alert alert-info" style="margin-bottom:10px">${__(
						"Paying from {0} — available {1}",
						[info.branch_safe_account, format_currency(flt(info.branch_safe_balance), info.currency)]
					)}</div>`,
				},
				{
					fieldname: "expense_claim_type",
					label: __("Expense Type"),
					fieldtype: "Select",
					options: types.map((t) => t.expense_type),
					reqd: 1,
				},
				{ fieldname: "amount", label: __("Amount"), fieldtype: "Currency", reqd: 1 },
				{ fieldtype: "Column Break" },
				{
					fieldname: "posting_date",
					label: __("Date"),
					fieldtype: "Date",
					default: frappe.datetime.get_today(),
					reqd: 1,
				},
				{ fieldtype: "Section Break" },
				{ fieldname: "description", label: __("Description"), fieldtype: "Small Text", reqd: 1 },
				{
					fieldname: "receipt",
					label: __("Receipt / Invoice"),
					fieldtype: "Attach",
					reqd: 1,
					description: __("A photo or scan of the receipt is required."),
				},
			],
			primary_action_label: __("Record & Pay"),
			primary_action: (values) => {
				if (flt(values.amount) > flt(info.branch_safe_balance)) {
					frappe.msgprint(__("Amount exceeds the branch safe balance."));
					return;
				}
				d.hide();
				frappe.call({
					method: "ecs_posnext.api.branch_expense.record_expense",
					args: {
						pos_profile: info.pos_profile,
						expense_claim_type: values.expense_claim_type,
						amount: values.amount,
						description: values.description,
						receipt: values.receipt,
						posting_date: values.posting_date,
					},
					freeze: true,
					freeze_message: __("Posting expense..."),
					callback: (r) => {
						if (r.message) {
							frappe.show_alert({
								message: __("Expense {0} posted.", [r.message.name]),
								indicator: "green",
							});
						}
						load();
					},
				});
			},
		});
		d.show();
	}

	// ------------------------------------------------------------------
	// Small helpers
	// ------------------------------------------------------------------
	function card(label, value, sub, colour) {
		return `
			<div class="col-sm-4">
				<div class="frappe-card" style="padding:14px">
					<div class="text-muted small">${label}</div>
					<div class="h4 text-${colour}" style="margin:4px 0">${value}</div>
					<div class="text-muted small">${frappe.utils.escape_html(sub || "")}</div>
				</div>
			</div>`;
	}

	function empty(msg) {
		return `<div class="text-muted text-center" style="padding:48px">${msg}</div>`;
	}

	function loading() {
		return `<div class="text-muted text-center" style="padding:48px">${__("Loading...")}</div>`;
	}
};
