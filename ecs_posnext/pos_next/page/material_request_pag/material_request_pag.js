frappe.pages["material-request-pag"].on_page_load = function (wrapper) {
	new MaterialRequestPage(wrapper);
};

class MaterialRequestPage {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.selectedItems = new Map();
		this.page_start = 0;
		this.page_len = 50;
		this.has_more = false;

		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Material Requests"),
			single_column: true,
		});

		this.make_filters();
		this.make_table();
		this.make_actions();
		this.page.set_indicator(__("Ready"), "blue");
	}

	// 🔧 helper (replacement for frappe.utils.flt)
	flt(value, precision = 2) {
		let num = parseFloat(value);
		if (isNaN(num)) num = 0;
		return parseFloat(num.toFixed(precision));
	}

	make_filters() {
		this.item_type_filter = this.page.add_field({
			label: __("Item Type"),
			fieldname: "item_type",
			fieldtype: "Link",
			options: "POS Item Type",
			reqd: 1,
			change: () => {
				this.page_start = 0;
				this.load_items(true);
			},
		});
	}

	make_actions() {
		this.page.set_primary_action(__("Create Material Request"), () =>
			this.create_material_request()
		);
	}

	make_table() {
		this.$table = $(`
			<div class="mt-4 material-request-table">
				<table class="table table-bordered table-hover">
					<thead>
						<tr>
							<th style="width: 40px;"></th>
							<th>${__("Item")}</th>
							<th>${__("Warehouse")}</th>
							<th class="text-right">${__("Actual Qty")}</th>
							<th class="text-right">${__("Reorder Level")}</th>
							<th class="text-right">${__("Reorder Qty")}</th>
							<th class="text-right">${__("Suggested Qty")}</th>
							<th style="width: 140px;" class="text-right">${__("Request Qty")}</th>
						</tr>
					</thead>
					<tbody class="js-tbody">
						<tr class="js-empty">
							<td colspan="8" class="text-muted text-center">${__(
								"Select an Item Type to view items."
							)}</td>
						</tr>
					</tbody>
				</table>
				<div class="text-center mt-3">
					<button class="btn btn-sm btn-secondary js-load-more" style="display:none;">
						${__("Load More")}
					</button>
				</div>
			</div>
		`).appendTo(this.page.body);

		this.$tbody = this.$table.find(".js-tbody");
		this.$loadMore = this.$table.find(".js-load-more");

		this.$loadMore.on("click", () => {
			this.page_start += this.page_len;
			this.load_items(false);
		});
	}

	load_items(reset = true) {
		const itemType = this.item_type_filter.get_value();
		if (!itemType) {
			this.render_table([]);
			return;
		}

		this.page.set_indicator(__("Loading..."), "orange");

		frappe.call({
			method: "ecs_posnext.pos_next.page.material_request_pag.material_request_pag.get_items",
			args: {
				item_type: itemType,
				page_len: this.page_len,
				page_start: this.page_start,
			},
			callback: (r) => {
				this.page.set_indicator(__("Ready"), "blue");
				const data = r.message || {};
				const items = data.items || [];
				this.has_more = data.has_more || false;

				if (reset) this.render_table(items);
				else this.append_rows(items);

				this.$loadMore.toggle(this.has_more);
			},
			error: () => this.page.set_indicator(__("Ready"), "blue"),
		});
	}

	render_table(items) {
		this.items = items || [];
		this.selectedItems.clear();
		this.$tbody.empty();

		if (!items.length) {
			this.$tbody.html(`
				<tr class="js-empty">
					<td colspan="8" class="text-muted text-center">${__("No items found.")}</td>
				</tr>
			`);
			return;
		}

		const html = items.map((item) => this.build_row_html(item)).join("");
		this.$tbody.html(html);
		this.bind_row_events();
	}

	append_rows(items) {
		if (!items?.length) return;
		const html = items.map((item) => this.build_row_html(item)).join("");
		this.$tbody.append(html);
		this.bind_row_events();
	}

	build_row_html(item) {
		const key = this.get_row_key(item.item_code, item.warehouse);
		const requestQty = this.flt(item.request_qty || item.suggested_qty || 0);
		const format = (val) => this.flt(val || 0, 2);

		return `
			<tr data-key="${frappe.utils.escape_html(key)}"
				data-item="${frappe.utils.escape_html(item.item_code || "")}"
				data-warehouse="${frappe.utils.escape_html(item.warehouse || "")}">
				<td class="text-center"><input type="checkbox" class="js-select-row"></td>
				<td>
					<div class="font-weight-bold">${frappe.utils.escape_html(item.item_code || "")}</div>
					${item.item_name ? `<div class="text-muted small">${frappe.utils.escape_html(item.item_name)}</div>` : ""}
					${item.item_group ? `<div class="text-muted small">${frappe.utils.escape_html(item.item_group)}</div>` : ""}
				</td>
				<td>${frappe.utils.escape_html(item.warehouse || "")}</td>
				<td class="text-right">${format(item.actual_qty)}</td>
				<td class="text-right">${format(item.reorder_level)}</td>
				<td class="text-right">${format(item.reorder_qty)}</td>
				<td class="text-right text-primary">${format(item.suggested_qty)}</td>
				<td class="text-right">
					<input type="number" min="0" step="0.01"
						class="form-control form-control-sm text-right js-qty-input"
						value="${requestQty}">
				</td>
			</tr>
		`;
	}

	bind_row_events() {
		this.$tbody.find(".js-select-row").off("change").on("change", (e) => {
			const $row = $(e.currentTarget).closest("tr");
			const key = $row.data("key");
			const itemCode = $row.data("item");
			const warehouse = $row.data("warehouse");
			let qty = this.flt($row.find(".js-qty-input").val());
			if (qty <= 0) {
				frappe.msgprint(__("Quantity must be greater than zero."));
				e.currentTarget.checked = false;
				return;
			}
			if (e.currentTarget.checked) {
				this.selectedItems.set(key, { item_code: itemCode, warehouse, qty });
			} else {
				this.selectedItems.delete(key);
			}
		});

		this.$tbody.find(".js-qty-input").off("change").on("change", (e) => {
			const $row = $(e.currentTarget).closest("tr");
			const key = $row.data("key");
			let qty = this.flt(e.currentTarget.value);
			if (this.selectedItems.has(key)) {
				this.selectedItems.get(key).qty = qty;
			}
		});
	}

	get_row_key(item, warehouse) {
		return `${item}::${warehouse}`;
	}

	get_selected_items() {
		return Array.from(this.selectedItems.values()).filter(
			(r) => r.item_code && r.warehouse && this.flt(r.qty) > 0
		);
	}

	create_material_request() {
		const items = this.get_selected_items();
		if (!items.length) {
			frappe.msgprint(__("Select at least one item with a quantity greater than zero."));
			return;
		}
		this.prompt_target_warehouse(items);
	}

	prompt_target_warehouse(items) {
		const defaultWarehouse = items[0]?.warehouse || "";

		const dialog = new frappe.ui.Dialog({
			title: __("Select Target Warehouse"),
			fields: [
				{
					fieldname: "warehouse",
					fieldtype: "Link",
					label: __("Target Warehouse"),
					options: "Warehouse",
					reqd: 1,
					default: defaultWarehouse,
				},
			],
			primary_action_label: __("Create"),
			primary_action: (values) => {
				if (!values?.warehouse) {
					frappe.msgprint(__("Please select a warehouse."));
					return;
				}
				dialog.hide();
				this.submit_material_request(items, values.warehouse);
			},
		});

		dialog.show();
	}

	submit_material_request(items, targetWarehouse) {
		frappe.call({
			method: "ecs_posnext.pos_next.page.material_request_pag.material_request_pag.create_material_request",
			args: { items, target_warehouse: targetWarehouse },
			freeze: true,
			callback: (r) => {
				const message = r.message || {};
				const docname = message.material_request;
				if (docname) {
					frappe.msgprint(
						__("Material Request {0} created successfully.", [
							frappe.utils.get_form_link("Material Request", docname),
						])
					);
					this.reset_after_submission();
				}
			},
		});
	}

	reset_after_submission() {
		this.page_start = 0;
		this.has_more = false;
		this.selectedItems.clear();
		this.render_table([]);
		this.$loadMore.hide();
		if (this.item_type_filter) {
			this.item_type_filter.set_value("");
		}
	}
}
