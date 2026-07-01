frappe.pages["pos_super_closing"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("POS Super Closing"),
		single_column: true,
	});

	const $body = $(`
		<div class="p-4">
			<div class="form-column" style="max-width: 500px;">
				<div class="form-group">
					<label>${__("Business Day")}</label>
					<input type="date" class="form-control" data-field="business_day" />
				</div>
				<div class="form-group">
					<label>${__("Company")}</label>
					<input type="text" class="form-control" data-field="company" />
				</div>
				<div class="form-group">
					<label>${__("POS Profiles")}</label>
					<div data-field="pos_profiles"></div>
				</div>
				<button class="btn btn-primary" data-action="create">${__("Create Super Closing")}</button>
			</div>
			<div class="mt-3" data-field="result"></div>
		</div>
	`);

	$(page.body).append($body);

	const state = {
		business_day: frappe.datetime.get_today(),
		company: frappe.boot?.default_company || "",
		pos_profiles: [],
		ctrls: {},
	};

	// set defaults
	$body.find('input[data-field="business_day"]').val(state.business_day).on("change", (e) => {
		state.business_day = e.target.value;
	});
	$body.find('input[data-field="company"]').val(state.company).on("change", (e) => {
		state.company = e.target.value;
	});

	// POS profile multiselect
	const df = {
		fieldtype: "MultiSelectList",
		get_data: function (txt) {
			return frappe.db.get_link_options("POS Profile", txt);
		},
	};
	const ctrl = frappe.ui.form.make_control({
		df,
		parent: $body.find('[data-field="pos_profiles"]'),
		render_input: true,
	});
	ctrl.onchange = () => {
		const raw = ctrl.get_value();
		let vals = [];
		if (Array.isArray(raw)) {
			vals = raw.map((v) => (v && v.value ? v.value : v)).filter(Boolean);
		} else if (typeof raw === "string") {
			vals = raw
				.split(",")
				.map((v) => v.trim())
				.filter(Boolean);
		}
		state.pos_profiles = vals;
	};

	$body.find('[data-action="create"]').on("click", () => {
		const resultBox = $body.find('[data-field="result"]');
		resultBox.empty();
		frappe.call({
			method: "ecs_posnext.api.super_closing.make_super_closing",
			args: {
				business_day: state.business_day,
				pos_profiles: state.pos_profiles,
				company: state.company,
			},
			freeze: true,
			freeze_message: __("Creating Super Closing..."),
		})
			.then((r) => {
				if (r.message) {
					const name = r.message;
					resultBox.html(
						`<div class="alert alert-success">
							${__("Super Closing Created")}: <a href="/app/pos-super-closing/${name}" target="_blank">${name}</a>
						</div>`
					);
				}
			})
			.catch((err) => {
				frappe.msgprint({ title: __("Error"), message: err.message || err, indicator: "red" });
			});
	});
};
