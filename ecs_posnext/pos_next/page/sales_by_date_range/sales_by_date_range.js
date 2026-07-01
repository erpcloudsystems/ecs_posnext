frappe.pages["sales_by_date_range"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Sales by Date Range"),
		single_column: true,
	});

	const $container = $(`<div id="sales-by-date-range-app" class="py-4"></div>`);
	$(page.body).append($container);

	_add_styles_dr();
	_init_app_dr();
};

function _add_styles_dr() {
	const css = `
    .dr-filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; align-items: stretch; }
    .dr-filter-block { display: flex; flex-direction: column; justify-content: space-between; gap: 8px; background: #fff; border: 1px solid #e6e9ef; border-radius: 10px; padding: 10px 12px; box-shadow: 0 6px 14px rgba(0,0,0,0.035); height: 110px; }
    .dr-filter-block .control-label { margin: 0; font-weight: 700; font-size: 11px; color: #52606d; text-transform: uppercase; letter-spacing: 0.04em; text-align: center; }
    .dr-card { background: #fff; border: 1px solid #e6e9ef; border-radius: 12px; box-shadow: 0 10px 22px rgba(0,0,0,0.04); padding: 14px; margin-bottom: 14px; min-height: 140px; }
    .dr-card .h6 { text-align: center; font-weight: 700; letter-spacing: 0.02em; margin-bottom: 12px; }
    .dr-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }
    .dr-table { width: 100%; border-collapse: collapse; }
    .dr-table th, .dr-table td { padding: 8px 10px; border-bottom: 1px solid #f1f3f5; text-align: left; }
    .dr-table th { background: #f8fafc; text-transform: uppercase; font-size: 11px; letter-spacing: 0.02em; }
    .dr-filter-input .control-input-wrapper { width: 100%; }
    .dr-filter-input input { width: 100%; }
    .dr-action { display: flex; align-items: flex-end; justify-content: flex-end; }
    .dr-action .btn { padding: 8px 16px; font-weight: 600; border-radius: 8px; }
    .dr-mode-selector { display: flex; gap: 12px; justify-content: center; margin-bottom: 20px; }
    .dr-mode-btn { padding: 12px 24px; border: 2px solid #e6e9ef; border-radius: 10px; background: #fff; cursor: pointer; font-weight: 600; transition: all 0.2s; }
    .dr-mode-btn:hover { border-color: #3b82f6; }
    .dr-mode-btn.active { border-color: #3b82f6; background: #3b82f6; color: #fff; }
    .dr-modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1050; }
    .dr-modal { background: #fff; border-radius: 12px; padding: 24px; min-width: 400px; box-shadow: 0 20px 40px rgba(0,0,0,0.2); }
    .dr-modal-title { font-size: 18px; font-weight: 700; margin-bottom: 20px; text-align: center; }
  `;
	const tag = document.createElement("style");
	tag.innerHTML = css;
	document.head.appendChild(tag);
}

function _init_app_dr() {
	if (!window.Vue) {
		const s = document.createElement("script");
		s.src = "https://cdn.jsdelivr.net/npm/vue@2.7.14/dist/vue.min.js";
		s.onload = render_app_dr;
		document.head.appendChild(s);
	} else {
		render_app_dr();
	}
}

function render_app_dr() {
	/* eslint-disable no-new */
	new Vue({
		el: "#sales-by-date-range-app",
		data() {
			return {
				showModeSelector: true,
				mode: "", // "whole_day" or "date_range"
				loading: false,
				ctrls: {},
				filters: {
					working_day: frappe.datetime.get_today(),
					from_date: frappe.datetime.get_today(),
					to_date: frappe.datetime.get_today(),
					shift: "Whole Day",
					branches: [],
					pos_profiles: [],
					cashiers: [],
					items: [],
					order_types: [],
					modes_of_payment: [],
					price_lists: [],
				},
				totals: {},
				branch_summary: [],
				payments: [],
				detail: [],
				invoices_items: [],
				order_categorization: [],
				order_source: [],
				period: {},
				cheque_avg: 0,
				showInvoices: true,
				showItems: false,
				shiftOverrides: {},
			};
		},
		template: `
      <div>
        <!-- Mode Selection Modal -->
        <div class="dr-modal-overlay" v-if="showModeSelector">
          <div class="dr-modal">
            <div class="dr-modal-title">{{ __("Select Report Mode") }}</div>
            <div class="dr-mode-selector" style="flex-direction: column;">
              <button class="dr-mode-btn" :class="{ active: mode === 'whole_day' }" @click="selectMode('whole_day')">
                <i class="fa fa-calendar-day mr-2"></i> {{ __("Whole Day") }}
                <div class="small text-muted mt-1">{{ __("View sales for a single working day") }}</div>
              </button>
              <button class="dr-mode-btn" :class="{ active: mode === 'date_range' }" @click="selectMode('date_range')">
                <i class="fa fa-calendar-alt mr-2"></i> {{ __("Date Range") }}
                <div class="small text-muted mt-1">{{ __("View sales for multiple days") }}</div>
              </button>
            </div>
          </div>
        </div>

        <!-- Main Content -->
        <div v-if="!showModeSelector">
          <!-- Mode Switch Button -->
          <div class="mb-3 text-center">
            <button class="btn btn-sm btn-outline-secondary" @click="showModeSelector = true">
              <i class="fa fa-exchange-alt mr-1"></i> {{ __("Change Mode") }} ({{ mode === 'whole_day' ? __('Whole Day') : __('Date Range') }})
            </button>
          </div>

          <div class="dr-card dr-filters">
            <!-- Whole Day Mode -->
            <template v-if="mode === 'whole_day'">
              <div class="dr-filter-block">
                <label class="control-label">{{ __("Working Day") }}</label>
                <input type="date" class="form-control" v-model="filters.working_day" />
              </div>
              <div class="dr-filter-block">
                <label class="control-label">{{ __("Shift") }}</label>
                <select class="form-control" v-model="filters.shift">
                  <option>Morning</option>
                  <option>Evening</option>
                  <option>Whole Day</option>
                </select>
              </div>
            </template>

            <!-- Date Range Mode -->
            <template v-if="mode === 'date_range'">
              <div class="dr-filter-block">
                <label class="control-label">{{ __("From Date") }}</label>
                <input type="date" class="form-control" v-model="filters.from_date" />
              </div>
              <div class="dr-filter-block">
                <label class="control-label">{{ __("To Date") }}</label>
                <input type="date" class="form-control" v-model="filters.to_date" />
              </div>
            </template>

            <div class="dr-filter-block dr-filter-input">
              <label class="control-label">{{ __("Branches") }}</label>
              <div ref="branchesCtrl"></div>
            </div>
            <div class="dr-filter-block dr-filter-input">
              <label class="control-label">{{ __("POS Profiles") }}</label>
              <div ref="posProfilesCtrl"></div>
            </div>
            <div class="dr-filter-block dr-filter-input">
              <label class="control-label">{{ __("Cashiers") }}</label>
              <div ref="cashiersCtrl"></div>
            </div>
            <div class="dr-filter-block dr-filter-input">
              <label class="control-label">{{ __("Items") }}</label>
              <div ref="itemsCtrl"></div>
            </div>
            <div class="dr-filter-block dr-filter-input">
              <label class="control-label">{{ __("Order Types") }}</label>
              <div ref="orderTypesCtrl"></div>
            </div>
            <div class="dr-filter-block dr-filter-input">
              <label class="control-label">{{ __("Modes of Payment") }}</label>
              <div ref="mopsCtrl"></div>
            </div>
            <div class="dr-filter-block dr-filter-input">
              <label class="control-label">{{ __("Price Lists") }}</label>
              <div ref="priceListsCtrl"></div>
            </div>
            <div class="dr-action">
              <button class="btn btn-primary" :disabled="loading" @click="fetchData">
                {{ loading ? __("Loading...") : __("Fetch") }}
              </button>
            </div>
          </div>

          <div class="dr-card dr-kpis" v-if="!loading">
            <div>
              <div class="text-muted text-uppercase small">{{ __("Grand Total") }}</div>
              <div class="h5">{{ format_currency(totals.grand_total) }}</div>
            </div>
            <div>
              <div class="text-muted text-uppercase small">{{ __("Net Total") }}</div>
              <div class="h5">{{ format_currency(totals.net_total) }}</div>
            </div>
            <div>
              <div class="text-muted text-uppercase small">{{ __("Total Qty") }}</div>
              <div class="h5">{{ totals.total_qty || 0 }}</div>
            </div>
            <div>
              <div class="text-muted text-uppercase small">{{ __("Invoices") }}</div>
              <div class="h5">{{ totals.count || 0 }}</div>
            </div>
            <div v-if="cheque_avg">
              <div class="text-muted text-uppercase small">{{ __("Cheque Average") }}</div>
              <div class="h5">{{ format_currency(cheque_avg) }}</div>
            </div>
            <div v-if="period.start">
              <div class="text-muted text-uppercase small">{{ __("Period") }}</div>
              <div class="small">{{ period.start }} -> {{ period.end }}</div>
            </div>
          </div>

          <div class="dr-card" v-if="branch_summary.length">
            <div class="h6 mb-2">{{ __("Branch Summary") }}</div>
            <table class="dr-table">
              <thead>
                <tr>
                  <th>{{ __("Branch") }}</th>
                  <th>{{ __("Grand Total") }}</th>
                  <th>{{ __("Net Total") }}</th>
                  <th>{{ __("Qty") }}</th>
                  <th>{{ __("#") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in branch_summary" :key="row.branch">
                  <td>{{ row.branch }}</td>
                  <td>{{ format_currency(row.grand_total) }}</td>
                  <td>{{ format_currency(row.net_total) }}</td>
                  <td>{{ row.total_qty }}</td>
                  <td>{{ row.count }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="dr-card" v-if="order_categorization.length">
            <div class="h6 mb-2">{{ __("Order Categorization") }}</div>
            <table class="dr-table">
              <thead>
                <tr>
                  <th>{{ __("Order Type") }}</th>
                  <th>{{ __("Grand Total") }}</th>
                  <th>{{ __("Net Total") }}</th>
                  <th>{{ __("Qty") }}</th>
                  <th>{{ __("#") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in order_categorization" :key="row.order_type">
                  <td>{{ row.order_type }}</td>
                  <td>{{ format_currency(row.grand_total) }}</td>
                  <td>{{ format_currency(row.net_total) }}</td>
                  <td>{{ row.total_qty }}</td>
                  <td>{{ row.count }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="dr-card" v-if="order_source.length">
            <div class="h6 mb-2">{{ __("Order Source (Price List)") }}</div>
            <table class="dr-table">
              <thead>
                <tr>
                  <th>{{ __("Price List") }}</th>
                  <th>{{ __("Grand Total") }}</th>
                  <th>{{ __("Net Total") }}</th>
                  <th>{{ __("Qty") }}</th>
                  <th>{{ __("#") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in order_source" :key="row.price_list">
                  <td>{{ row.price_list }}</td>
                  <td>{{ format_currency(row.grand_total) }}</td>
                  <td>{{ format_currency(row.net_total) }}</td>
                  <td>{{ row.total_qty }}</td>
                  <td>{{ row.count }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="dr-card" v-if="payments.length">
            <div class="h6 mb-2">{{ __("Payments") }}</div>
            <table class="dr-table">
              <thead>
                <tr>
                  <th>{{ __("Mode of Payment") }}</th>
                  <th>{{ __("Amount") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in payments" :key="row.mode_of_payment">
                  <td>{{ row.mode_of_payment }}</td>
                  <td>{{ format_currency(row.amount) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="dr-card" v-if="detail.length">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <div class="h6 mb-0">{{ __("Invoices") }}</div>
              <button class="btn btn-sm btn-link" @click="showInvoices = !showInvoices">
                {{ showInvoices ? __("Hide") : __("Show") }}
              </button>
            </div>
            <div v-if="showInvoices">
              <table class="dr-table">
                <thead>
                  <tr>
                    <th>{{ __("Invoice") }}</th>
                    <th>{{ __("Date") }}</th>
                    <th>{{ __("Time") }}</th>
                    <th>{{ __("Branch") }}</th>
                    <th>{{ __("POS Profile") }}</th>
                    <th>{{ __("Customer") }}</th>
                    <th>{{ __("Grand Total") }}</th>
                    <th>{{ __("Net Total") }}</th>
                    <th>{{ __("Qty") }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in detail" :key="row.name">
                    <td><a :href="invoice_link(row.name)" target="_blank">{{ row.name }}</a></td>
                    <td>{{ row.posting_date }}</td>
                    <td>{{ row.posting_time }}</td>
                    <td>{{ row.branch || __("Unknown") }}</td>
                    <td>{{ row.pos_profile }}</td>
                    <td>{{ row.customer }}</td>
                    <td>{{ format_currency(row.grand_total) }}</td>
                    <td>{{ format_currency(row.net_total) }}</td>
                    <td>{{ row.total_qty }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="dr-card" v-if="invoices_items.length">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <div class="h6 mb-0">{{ __("Invoices with Items") }}</div>
              <button class="btn btn-sm btn-link" @click="showItems = !showItems">
                {{ showItems ? __("Hide") : __("Show") }}
              </button>
            </div>
            <div v-if="showItems">
              <table class="dr-table">
                <thead>
                  <tr>
                    <th>{{ __("Invoice") }}</th>
                    <th>{{ __("Date") }}</th>
                    <th>{{ __("Time") }}</th>
                    <th>{{ __("Branch") }}</th>
                    <th>{{ __("POS Profile") }}</th>
                    <th>{{ __("Customer") }}</th>
                    <th>{{ __("Item") }}</th>
                    <th>{{ __("Item Name") }}</th>
                    <th>{{ __("Qty") }}</th>
                    <th>{{ __("Net Amount") }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in invoices_items" :key="row.sales_invoice + row.item_code + row.item_name">
                    <td><a :href="invoice_link(row.sales_invoice)" target="_blank">{{ row.sales_invoice }}</a></td>
                    <td>{{ row.posting_date }}</td>
                    <td>{{ row.posting_time }}</td>
                    <td>{{ row.branch || __("Unknown") }}</td>
                    <td>{{ row.pos_profile }}</td>
                    <td>{{ row.customer }}</td>
                    <td>{{ row.item_code }}</td>
                    <td>{{ row.item_name }}</td>
                    <td>{{ row.qty }}</td>
                    <td>{{ format_currency(row.net_amount) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    `,
		mounted() {
			// Don't build controls until mode is selected
		},
		methods: {
			selectMode(selectedMode) {
				this.mode = selectedMode;
				this.showModeSelector = false;
				this.$nextTick(() => {
					this.build_controls();
				});
			},
			build_controls() {
				const normalizeCtrlValue = (val) => {
					if (Array.isArray(val)) {
						return val
							.map((v) => {
								if (typeof v === "string") return v.trim();
								if (v && typeof v === "object") {
									return (v.value || v.label || v.name || "").trim();
								}
								return "";
							})
							.filter(Boolean);
					}
					if (typeof val === "string") {
						return val
							.split(",")
							.map((v) => v.trim())
							.filter(Boolean);
					}
					return [];
				};

				const make = (ref, options) => {
					if (!this.$refs[ref]) return;
					try {
						const df = {
							fieldtype: "MultiSelectList",
							fieldname: options.field,
							label: "",
							options: options.doctype || "",
							placeholder: options.placeholder || "",
							get_data: options.get_data || ((txt) => frappe.db.get_link_options(options.doctype, txt)),
							default: (this.filters[options.field] || []).join(", "),
						};
						const ctrl = frappe.ui.form.make_control({
							parent: this.$refs[ref],
							df,
							doc: { [options.field]: this.filters[options.field] || [] },
							render_input: true,
						});
						ctrl.refresh_input();
						ctrl.on_change = () => {
							this.filters[options.field] = normalizeCtrlValue(ctrl.get_value());
							if (options.field === "pos_profiles") {
								const val = this.filters.pos_profiles && this.filters.pos_profiles[0];
								this.loadShiftTimes(val);
							}
						};
						if (ctrl.set_value) {
							ctrl.set_value(this.filters[options.field] || []);
						}
						this.ctrls[ref] = ctrl;
					} catch (e) {
						console.error("Failed to build control", ref, e);
					}
				};
				make("branchesCtrl", { doctype: "Branch", field: "branches", label: __("Branches") });
				make("posProfilesCtrl", { doctype: "POS Profile", field: "pos_profiles", label: __("POS Profiles") });
				make("cashiersCtrl", { doctype: "User", field: "cashiers", label: __("Cashiers") });
				make("itemsCtrl", { doctype: "Item", field: "items", label: __("Items") });
				make("mopsCtrl", { doctype: "Mode of Payment", field: "modes_of_payment", label: __("Modes of Payment") });
				make("priceListsCtrl", { doctype: "Price List", field: "price_lists", label: __("Price Lists") });

				// Order Types
				if (this.$refs.orderTypesCtrl) {
					const df = {
						fieldtype: "Select",
						fieldname: "order_types",
						label: "",
						options: "",
						placeholder: __("Select Order Type"),
					};
					frappe.model.with_doctype("Sales Order", () => {
						const soTypeDf = frappe.meta.get_docfield("Sales Order", "custom_so_type") || {};
						const options = (soTypeDf.options || "")
							.split("\n")
							.map((o) => o.trim())
							.filter(Boolean);
						df.options = options.join("\n");

						const ctrl = frappe.ui.form.make_control({
							parent: this.$refs.orderTypesCtrl,
							df,
							doc: { order_types: (this.filters.order_types || [])[0] || "" },
							render_input: true,
						});
						ctrl.refresh_input();
						ctrl.on_change = () => {
							const val = ctrl.get_value ? ctrl.get_value() : "";
							this.filters.order_types = val ? [val] : [];
						};
						this.ctrls.orderTypesCtrl = ctrl;
					});
				}
			},
			loadShiftTimes(posProfile) {
				this.shiftOverrides = {};
				if (!posProfile) return;
				frappe.db
					.get_value("POS Profile", posProfile, [
						"posa_shift_1_start",
						"posa_shift_1_end",
						"posa_shift_2_start",
						"posa_shift_2_end",
					])
					.then((r) => {
						const v = r && r.message ? r.message : {};
						this.shiftOverrides = {
							s1_start: v.posa_shift_1_start,
							s1_end: v.posa_shift_1_end,
							s2_start: v.posa_shift_2_start,
							s2_end: v.posa_shift_2_end,
						};
					});
			},
			async fetchData() {
				this.loading = true;
				const normalizeForPayload = (v) => {
					if (Array.isArray(v)) {
						return v
							.map((x) => {
								if (typeof x === "string") return x.trim();
								if (x && typeof x === "object") {
									return (x.value || x.label || x.name || "").trim();
								}
								return "";
							})
							.filter(Boolean);
					}
					if (typeof v === "string") {
						return v
							.split(",")
							.map((x) => x.trim())
							.filter(Boolean);
					}
					return [];
				};
				
				Object.keys(this.ctrls || {}).forEach((key) => {
					const ctrl = this.ctrls[key];
					if (ctrl && ctrl.df && ctrl.df.fieldname && ctrl.get_value) {
						this.filters[ctrl.df.fieldname] = normalizeForPayload(ctrl.get_value());
					}
				});
				
				const firstPosProfile = (this.filters.pos_profiles || [])[0] || "";
				if (firstPosProfile && !Object.keys(this.shiftOverrides || {}).length) {
					try {
						const r = await frappe.db.get_value("POS Profile", firstPosProfile, [
							"posa_shift_1_start",
							"posa_shift_1_end",
							"posa_shift_2_start",
							"posa_shift_2_end",
						]);
						const v = r && r.message ? r.message : {};
						this.shiftOverrides = {
							s1_start: v.posa_shift_1_start,
							s1_end: v.posa_shift_1_end,
							s2_start: v.posa_shift_2_start,
							s2_end: v.posa_shift_2_end,
						};
					} catch (e) {
						// ignore
					}
				}
				
				const payload = {
					mode: this.mode,
					working_day: this.filters.working_day,
					from_date: this.filters.from_date,
					to_date: this.filters.to_date,
					shift: this.filters.shift,
					branches: normalizeForPayload(this.filters.branches),
					pos_profiles: normalizeForPayload(this.filters.pos_profiles),
					pos_profile_for_window: firstPosProfile ? [firstPosProfile] : [],
					shift_overrides: this.shiftOverrides,
					cashiers: normalizeForPayload(this.filters.cashiers),
					items: normalizeForPayload(this.filters.items),
					order_types: normalizeForPayload(this.filters.order_types),
					modes_of_payment: normalizeForPayload(this.filters.modes_of_payment),
					price_lists: normalizeForPayload(this.filters.price_lists),
				};
				
				frappe
					.call({
						method: "ecs_posnext.api.sales_by_working_day.get_sales_by_date_range",
						args: { filters: payload },
					})
					.then((r) => {
						const data = r.message || {};
						this.totals = data.totals || {};
						this.branch_summary = data.branch_summary || [];
						this.payments = data.payments || [];
						this.detail = data.detail || [];
						this.period = data.period || {};
						this.invoices_items = data.invoices_items || [];
						this.cheque_avg = data.cheque_avg || 0;
						this.order_categorization = data.order_categorization || [];
						this.order_source = data.order_source || [];
						this.loading = false;
					})
					.catch(() => {
						this.loading = false;
					});
			},
			format_currency(v) {
				const raw = frappe.format(v || 0, { fieldtype: "Currency" });
				const tmp = document.createElement("div");
				tmp.innerHTML = raw;
				return tmp.textContent || tmp.innerText || "";
			},
			invoice_link(name) {
				return `/app/sales-invoice/${name}`;
			},
		},
	});
}
