frappe.pages["call_center_per_hour"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Call Center per Hour"),
		single_column: true,
	});

	const $container = $(`<div id="call-center-per-hour-app" class="py-4"></div>`);
	$(page.body).append($container);

	_add_styles_cc();
	_init_app_cc();
};

function _add_styles_cc() {
	const css = `
    .ccph-filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; align-items: stretch; }
    .ccph-filter-block { display: flex; flex-direction: column; justify-content: space-between; gap: 8px; background: #fff; border: 1px solid #e6e9ef; border-radius: 10px; padding: 10px 12px; box-shadow: 0 6px 14px rgba(0,0,0,0.035); height: 110px; }
    .ccph-filter-block .control-label { margin: 0; font-weight: 700; font-size: 11px; color: #52606d; text-transform: uppercase; letter-spacing: 0.04em; text-align: center; }
    .ccph-card { background: #fff; border: 1px solid #e6e9ef; border-radius: 12px; box-shadow: 0 10px 22px rgba(0,0,0,0.04); padding: 14px; margin-bottom: 14px; }
    .ccph-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }
    .ccph-kpi { text-align: center; padding: 10px; border-radius: 10px; background: #f8fafc; border: 1px solid #eef1f5; }
    .ccph-kpi .label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: #6b7b8c; font-weight: 700; }
    .ccph-kpi .value { font-size: 18px; font-weight: 700; color: #1f2933; }
    .ccph-section-title { text-align: center; font-weight: 700; letter-spacing: 0.02em; margin-bottom: 12px; }
    .ccph-table { width: 100%; border-collapse: collapse; }
    .ccph-table th, .ccph-table td { padding: 8px 10px; border-bottom: 1px solid #f1f3f5; text-align: left; }
    .ccph-table th { background: #f8fafc; text-transform: uppercase; font-size: 11px; letter-spacing: 0.02em; }
    .ccph-chart { min-height: 260px; }
    .ccph-action { display: flex; align-items: flex-end; justify-content: flex-end; }
    .ccph-action .btn { padding: 8px 16px; font-weight: 600; border-radius: 8px; }
  `;
	const tag = document.createElement("style");
	tag.innerHTML = css;
	document.head.appendChild(tag);
}

function _init_app_cc() {
	if (!window.Vue) {
		const s = document.createElement("script");
		s.src = "https://cdn.jsdelivr.net/npm/vue@2.7.14/dist/vue.min.js";
		s.onload = render_app_cc;
		document.head.appendChild(s);
	} else {
		render_app_cc();
	}
}

function render_app_cc() {
	/* eslint-disable no-new */
	new Vue({
		el: "#call-center-per-hour-app",
		data() {
			return {
				loading: false,
				ctrls: {},
				filters: {
					mode: "whole_day",
					working_day: frappe.datetime.get_today(),
					from_date: frappe.datetime.get_today(),
					to_date: frappe.datetime.get_today(),
					shift: "Morning",
					branch: "",
					cashier: "",
					order_type: "Delivery",
				},
				shiftOverrides: {},
				totals: { count: 0, grand_total: 0, net_total: 0 },
				hours: [],
				period: {},
				chartObj: null,
				chartData: { labels: [], orders: [], grand_totals: [] },
				callCenterUsers: [],
			};
		},
		template: `
      <div>
        <div class="ccph-card ccph-filters">
          <div class="ccph-filter-block">
            <label class="control-label">{{ __("Mode") }}</label>
            <select class="form-control" v-model="filters.mode">
              <option value="whole_day">{{ __("Whole Day") }}</option>
              <option value="date_range">{{ __("Date Range") }}</option>
            </select>
          </div>
          <div class="ccph-filter-block" v-if="filters.mode === 'whole_day'">
            <label class="control-label">{{ __("Working Day") }}</label>
            <input type="date" class="form-control" v-model="filters.working_day" />
          </div>
          <div class="ccph-filter-block" v-if="filters.mode === 'whole_day'">
            <label class="control-label">{{ __("Shift") }}</label>
            <select class="form-control" v-model="filters.shift">
              <option>Morning</option>
              <option>Evening</option>
              <option>Whole Day</option>
            </select>
          </div>
          <div class="ccph-filter-block" v-if="filters.mode === 'date_range'">
            <label class="control-label">{{ __("From Date") }}</label>
            <input type="date" class="form-control" v-model="filters.from_date" />
          </div>
          <div class="ccph-filter-block" v-if="filters.mode === 'date_range'">
            <label class="control-label">{{ __("To Date") }}</label>
            <input type="date" class="form-control" v-model="filters.to_date" />
          </div>
          <div class="ccph-filter-block">
            <label class="control-label">{{ __("Branch") }}</label>
            <div ref="branchCtrl"></div>
          </div>
          <div class="ccph-filter-block">
            <label class="control-label">{{ __("Call Center User") }}</label>
            <select class="form-control" v-model="filters.cashier">
              <option value="">{{ __("All Users") }}</option>
              <option v-for="u in callCenterUsers" :key="u" :value="u">{{ u }}</option>
            </select>
          </div>
          <div class="ccph-filter-block">
            <label class="control-label">{{ __("Order Type") }}</label>
            <select class="form-control" v-model="filters.order_type">
              <option value="ALL">{{ __("ALL") }}</option>
              <option>Delivery</option>
              <option>Pickup</option>
              <option>Dinin</option>
              <option>Talabat</option>
            </select>
          </div>
          <div class="ccph-action">
            <button class="btn btn-primary" :disabled="loading" @click="fetchData">
              {{ loading ? __("Loading...") : __("Fetch") }}
            </button>
          </div>
        </div>

        <div class="ccph-card ccph-kpis">
          <div class="ccph-kpi">
            <div class="label">{{ __("Orders") }}</div>
            <div class="value">{{ totals.count || 0 }}</div>
          </div>
          <div class="ccph-kpi">
            <div class="label">{{ __("Grand Total") }}</div>
            <div class="value">{{ format_currency(totals.grand_total) }}</div>
          </div>
          <div class="ccph-kpi">
            <div class="label">{{ __("Net Total") }}</div>
            <div class="value">{{ format_currency(totals.net_total) }}</div>
          </div>
          <div class="ccph-kpi" v-if="period.start">
            <div class="label">{{ __("Window") }}</div>
            <div class="value" style="font-size:13px;">{{ period.start }} → {{ period.end }}</div>
          </div>
        </div>

        <div class="ccph-card">
          <div class="ccph-section-title">{{ __("Orders per Hour") }}</div>
          <div id="ccph-chart" class="ccph-chart"></div>
        </div>

        <div class="ccph-card" v-if="hours.length">
          <div class="ccph-section-title">{{ __("Hourly Breakdown") }}</div>
          <table class="ccph-table">
            <thead>
              <tr>
                <th>{{ __("Hour") }}</th>
                <th>{{ __("# Orders") }}</th>
                <th>{{ __("Grand Total") }}</th>
                <th>{{ __("Net Total") }}</th>
                <th>{{ __("Payments") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in hours" :key="row.hour">
                <td>{{ row.hour }}</td>
                <td>{{ row.count }}</td>
                <td>{{ format_currency(row.grand_total) }}</td>
                <td>{{ format_currency(row.net_total) }}</td>
                <td>
                  <div v-if="row.mops && row.mops.length">
                    <div v-for="m in row.mops" :key="m.mode_of_payment + m.amount">
                      {{ m.mode_of_payment }}: {{ format_currency(m.amount) }}
                    </div>
                  </div>
                  <div v-else>-</div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    `,
		mounted() {
			this.build_controls();
			this.loadCallCenterUsers();
			this.fetchData();
		},
		methods: {
			build_controls() {
				const vm = this;
				const makeLink = (ref, doctype, field, onChange) => {
					if (!vm.$refs[ref]) return;
					const ctrl = frappe.ui.form.make_control({
						parent: vm.$refs[ref],
						df: {
							fieldtype: "Link",
							fieldname: field,
							options: doctype,
							label: "",
							placeholder: __("Select " + doctype),
							change: function () {
								const val = ctrl.get_value() || "";
								vm.$set(vm.filters, field, val);
								if (onChange) onChange(val);
							},
						},
						render_input: true,
					});
					ctrl.$input.on("awesomplete-selectcomplete", function () {
						const val = ctrl.get_value() || "";
						vm.$set(vm.filters, field, val);
						if (onChange) onChange(val);
					});
					ctrl.$input.on("blur", function () {
						const val = ctrl.get_value() || "";
						vm.$set(vm.filters, field, val);
					});
					ctrl.refresh();
					vm.ctrls[ref] = ctrl;
				};
				makeLink("branchCtrl", "Branch", "branch");
			},
			loadCallCenterUsers() {
				const vm = this;
				frappe.call({
					method: "ecs_posnext.api.call_center_per_hour.get_call_center_users",
					async: true,
				}).then((r) => {
					vm.callCenterUsers = r.message || [];
				});
			},
			async fetchData() {
				this.loading = true;
				const orderTypes = this.filters.order_type === "ALL" 
					? ["Delivery", "Pickup", "Dinin", "Talabat"] 
					: [this.filters.order_type];
				const payload = {
					mode: this.filters.mode,
					working_day: this.filters.working_day,
					from_date: this.filters.from_date,
					to_date: this.filters.to_date,
					shift: this.filters.shift,
					branches: this.filters.branch ? [this.filters.branch] : [],
					cashier: this.filters.cashier || "",
					order_types: orderTypes,
                    shift_overrides: this.shiftOverrides || {},
				};
				frappe
					.call({
						method: "ecs_posnext.api.call_center_per_hour.get_call_center_per_hour",
						args: { filters: payload },
					})
					.then((r) => {
						const data = r.message || {};
						this.totals = data.totals || { count: 0, grand_total: 0, net_total: 0 };
						this.hours = data.hours || [];
						this.period = data.period || {};
						this.chartData = data.chart || { labels: [], orders: [], grand_totals: [] };
						this.$nextTick(() => this.renderChart());
						this.loading = false;
					})
					.catch(() => {
						this.loading = false;
					});
			},
			renderChart() {
				const labels = this.chartData.labels || [];
				const orders = this.chartData.orders || [];
				const grands = this.chartData.grand_totals || [];
				if (!document.getElementById("ccph-chart")) return;
				if (this.chartObj) {
					this.chartObj.update({
						labels,
						datasets: [
							{ name: __("Orders"), type: "bar", values: orders },
							{ name: __("Grand Total"), type: "line", values: grands },
						],
					});
					return;
				}
				this.chartObj = new frappe.Chart("#ccph-chart", {
					title: __("Orders & Amount per Hour"),
					data: {
						labels,
						datasets: [
							{ name: __("Orders"), type: "bar", values: orders },
							{ name: __("Grand Total"), type: "line", values: grands },
						],
					},
					type: "axis-mixed",
					height: 280,
					colors: ["#3b82f6", "#10b981"],
				});
			},
			format_currency(v) {
				const raw = frappe.format(v || 0, { fieldtype: "Currency" });
				const tmp = document.createElement("div");
				tmp.innerHTML = raw;
				return tmp.textContent || tmp.innerText || "";
			},
		},
	});
}
