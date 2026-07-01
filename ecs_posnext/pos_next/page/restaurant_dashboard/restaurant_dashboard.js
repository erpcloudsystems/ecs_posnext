frappe.provide("ecs_posnext.pages.restaurant_dashboard");

frappe.pages["restaurant_dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Restaurant Operations Dashboard"),
		single_column: true,
	});

	const $container = $(`
		<div id="restaurant-dashboard-app" class="py-4"></div>
	`);
	$(page.body).append($container);

	_add_styles();

	const scripts = [
		"https://cdn.jsdelivr.net/npm/vue@2.7.14/dist/vue.min.js",
		"https://cdn.jsdelivr.net/npm/chart.js",
	];

	_load_scripts(scripts).then(() => init_dashboard(page)).catch((e) => {
		console.error("Failed to load dashboard scripts", e);
		frappe.msgprint(__("Failed to load dashboard resources."));
	});
};

function _load_scripts(urls) {
	return Promise.all(
		urls.map(
			(src) =>
				new Promise((resolve, reject) => {
					if (document.querySelector(`script[src="${src}"]`)) return resolve();
					const s = document.createElement("script");
					s.src = src;
					s.onload = resolve;
					s.onerror = reject;
					document.head.appendChild(s);
				})
		)
	);
}

function _add_styles() {
	const css = `
		.rd-grid { display: grid; gap: 12px; }
		.rd-grid.kpis { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
		.rd-card { background: #fff; border-radius: 10px; box-shadow: 0 6px 16px rgba(0,0,0,0.05); padding: 14px; transition: transform .15s ease, box-shadow .15s ease; }
		.rd-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.08); }
		.rd-section { margin-top: 18px; }
		.rd-section h4 { font-weight: 700; margin-bottom: 10px; }
		.rd-table { width: 100%; border-collapse: collapse; }
		.rd-table th, .rd-table td { padding: 8px 10px; border-bottom: 1px solid #f1f3f5; }
		.rd-table th { background: #f8fafc; text-transform: uppercase; font-size: 11px; letter-spacing: 0.02em; }
		.rd-badge { padding: 3px 8px; border-radius: 999px; font-size: 11px; background: #eef2ff; color: #4338ca; }
		.rd-filter-bar { display: flex; flex-wrap: wrap; gap: 8px; }
		.rd-filter-bar .form-control { min-width: 150px; }
	`;
	const tag = document.createElement("style");
	tag.innerHTML = css;
	document.head.appendChild(tag);
}

function init_dashboard(page) {
	/* eslint-disable no-new */
	new Vue({
		el: "#restaurant-dashboard-app",
		data() {
			const today = frappe.datetime.get_today();
			return {
				loading: false,
				filters: {
					from_date: today,
					to_date: today,
					branchesString: "",
					order_type: "",
					price_list: "",
					mode_of_payment: "",
					cancel_status: "",
					employee: "",
				},
				kpis: {},
				order_type_summary: [],
				price_list_summary: [],
				top_items: [],
				peak_hours: [],
				branch_comparison: [],
				charts: {},
			};
		},
		computed: {
			kpiCards() {
				return [
					{ key: "total_orders", label: __("Total Orders"), icon: "mdi-counter", color: "#0ea5e9", anchor: "order-type-section" },
					{ key: "total_value", label: __("Total Order Value"), icon: "mdi-cash", color: "#22c55e", anchor: "order-type-section" },
					{ key: "avg_order_value", label: __("Avg Order Value"), icon: "mdi-chart-donut", color: "#f97316", anchor: "order-type-section" },
					{ key: "customers_served", label: __("Customers Served"), icon: "mdi-account-group", color: "#6366f1", anchor: "order-type-section" },
					{ key: "cancelled_count", label: __("Cancelled Orders"), icon: "mdi-close-octagon", color: "#ef4444", anchor: "order-type-section" },
					{ key: "cancelled_value", label: __("Cancelled Value"), icon: "mdi-cancel", color: "#ef4444", anchor: "order-type-section" },
					{ key: "discount_total", label: __("Discount Total"), icon: "mdi-tag-multiple", color: "#a855f7", anchor: "order-type-section" },
					{ key: "net_sales", label: __("Net Sales"), icon: "mdi-cash-check", color: "#16a34a", anchor: "order-type-section" },
				].map((card) => ({
					...card,
					value: this.kpis[card.key] || 0,
				}));
			},
		},
		mounted() {
			this.fetchMetrics();
		},
		methods: {
			getCurrencyCode() {
				return frappe.boot?.sysdefaults?.currency || frappe.boot?.sysdefaults?.default_currency || "USD";
			},
			formatCurrency(val) {
				const num = Number(val || 0);
				const code = this.getCurrencyCode();
				try {
					return new Intl.NumberFormat(undefined, { style: "currency", currency: code }).format(num);
				} catch (e) {
					return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
				}
			},
			formatNumber(val) {
				const num = Number(val || 0);
				return num.toLocaleString(undefined, { maximumFractionDigits: 2 });
			},
			scrollTo(anchor) {
				const el = document.getElementById(anchor);
				if (el) {
					el.scrollIntoView({ behavior: "smooth" });
				}
			},
			fetchMetrics() {
				this.loading = true;
				const branches =
					this.filters.branchesString && this.filters.branchesString.length
						? this.filters.branchesString.split(",").map((b) => b.trim()).filter(Boolean)
						: [];
				const payload = {
					from_date: this.filters.from_date,
					to_date: this.filters.to_date,
					branches: branches.join(","),
					order_type: this.filters.order_type,
					price_list: this.filters.price_list,
					mode_of_payment: this.filters.mode_of_payment,
					cancel_status: this.filters.cancel_status,
					employee: this.filters.employee,
				};
				frappe.call({
					method: "ecs_posnext.api.dashboard.get_ops_metrics",
					args: payload,
				}).then((r) => {
					const data = r.message || {};
					this.kpis = data.kpis || {};
					this.order_type_summary = data.order_type_summary || [];
					this.price_list_summary = data.price_list_summary || [];
					this.top_items = data.top_items || [];
					this.peak_hours = data.peak_hours || [];
					this.branch_comparison = data.branch_comparison || [];
					this.$nextTick(() => this.drawCharts());
				}).finally(() => {
					this.loading = false;
				});
			},
			setDatePreset(preset) {
				const today = frappe.datetime.get_today();
				if (preset === "today") {
					this.filters.from_date = today;
					this.filters.to_date = today;
				} else if (preset === "yesterday") {
					const y = frappe.datetime.add_days(today, -1);
					this.filters.from_date = y;
					this.filters.to_date = y;
				} else if (preset === "week") {
					const week_start = frappe.datetime.week_start(today);
					this.filters.from_date = week_start;
					this.filters.to_date = today;
				} else if (preset === "month") {
					const month_start = frappe.datetime.month_start(today);
					this.filters.from_date = month_start;
					this.filters.to_date = today;
				}
				this.fetchMetrics();
			},
			drawCharts() {
				this.drawOrderTypeChart();
				this.drawPriceListChart();
				this.drawPeakHoursChart();
				this.drawBranchChart();
			},
			_destroyChart(key) {
				if (this.charts[key]) {
					this.charts[key].destroy();
					this.charts[key] = null;
				}
			},
			drawOrderTypeChart() {
				const ctx = document.getElementById("order-type-chart");
				if (!ctx || !window.Chart) return;
				this._destroyChart("orderType");
				const labels = this.order_type_summary.map((d) => d.type);
				const values = this.order_type_summary.map((d) => d.value);
				this.charts.orderType = new Chart(ctx, {
					type: "pie",
					data: {
						labels,
						datasets: [
							{
								data: values,
								backgroundColor: ["#22c55e", "#0ea5e9", "#a855f7", "#f97316", "#6366f1", "#f59e0b"],
							},
						],
					},
					options: { responsive: true, plugins: { legend: { position: "bottom" } } },
				});
			},
			drawPriceListChart() {
				const ctx = document.getElementById("price-list-chart");
				if (!ctx || !window.Chart) return;
				this._destroyChart("priceList");
				const labels = this.price_list_summary.map((d) => d.channel);
				const values = this.price_list_summary.map((d) => d.value);
				this.charts.priceList = new Chart(ctx, {
					type: "bar",
					data: {
						labels,
						datasets: [
							{
								label: __("Order Value"),
								data: values,
								backgroundColor: "#0ea5e9",
							},
						],
					},
					options: {
						responsive: true,
						scales: { y: { beginAtZero: true } },
					},
				});
			},
			drawPeakHoursChart() {
				const ctx = document.getElementById("peak-hours-chart");
				if (!ctx || !window.Chart) return;
				this._destroyChart("peakHours");
				const labels = this.peak_hours.map((d) => `${d.hour}:00`);
				const orders = this.peak_hours.map((d) => d.orders);
				const avg = this.peak_hours.map((d) => d.avg_value);
				this.charts.peakHours = new Chart(ctx, {
					type: "line",
					data: {
						labels,
						datasets: [
							{
								label: __("Orders"),
								data: orders,
								borderColor: "#22c55e",
								backgroundColor: "rgba(34,197,94,0.1)",
								fill: true,
							},
							{
								label: __("Avg Value"),
								data: avg,
								borderColor: "#0ea5e9",
								backgroundColor: "rgba(14,165,233,0.1)",
								fill: true,
							},
						],
					},
					options: { responsive: true, scales: { y: { beginAtZero: true } } },
				});
			},
			drawBranchChart() {
				const ctx = document.getElementById("branch-chart");
				if (!ctx || !window.Chart) return;
				this._destroyChart("branch");
				const labels = this.branch_comparison.map((d) => d.branch);
				const values = this.branch_comparison.map((d) => d.value);
				this.charts.branch = new Chart(ctx, {
					type: "bar",
					data: {
						labels,
						datasets: [
							{
								label: __("Branch Sales"),
								data: values,
								backgroundColor: "#6366f1",
							},
						],
					},
					options: { responsive: true, scales: { y: { beginAtZero: true } } },
				});
			},
			exportCSV() {
				const rows = [
					["Section", "Label", "Value"],
					...this.order_type_summary.map((d) => ["Order Type", d.type, d.value]),
					...this.price_list_summary.map((d) => ["Price List", d.channel, d.value]),
					...this.top_items.map((d) => ["Top Item", d.item_name, d.value]),
				];
				const csv = rows.map((r) => r.map((c) => `"${c}"`).join(",")).join("\n");
				const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
				const link = document.createElement("a");
				link.href = URL.createObjectURL(blob);
				link.download = "restaurant_dashboard.csv";
				link.click();
			},
			exportExcel() {
				// Simple TSV export compatible with Excel
				const rows = [
					["Section", "Label", "Value"],
					...this.order_type_summary.map((d) => ["Order Type", d.type, d.value]),
					...this.price_list_summary.map((d) => ["Price List", d.channel, d.value]),
					...this.top_items.map((d) => ["Top Item", d.item_name, d.value]),
				];
				const tsv = rows.map((r) => r.join("\t")).join("\n");
				const blob = new Blob([tsv], { type: "application/vnd.ms-excel" });
				const link = document.createElement("a");
				link.href = URL.createObjectURL(blob);
				link.download = "restaurant_dashboard.xls";
				link.click();
			},
		},
		template: `
			<div>
				<div class="rd-section rd-card">
					<div class="rd-filter-bar">
						<input type="date" class="form-control" v-model="filters.from_date" />
						<input type="date" class="form-control" v-model="filters.to_date" />
						<input type="text" class="form-control" :placeholder="__('Branches (comma separated)')" v-model="filters.branchesString" />
						<input type="text" class="form-control" :placeholder="__('Order Type')" v-model="filters.order_type" />
						<input type="text" class="form-control" :placeholder="__('Price List')" v-model="filters.price_list" />
						<input type="text" class="form-control" :placeholder="__('Mode of Payment')" v-model="filters.mode_of_payment" />
						<input type="text" class="form-control" :placeholder="__('Cancel Status')" v-model="filters.cancel_status" />
						<input type="text" class="form-control" :placeholder="__('Employee')" v-model="filters.employee" />
						<button class="btn btn-primary" :disabled="loading" @click="fetchMetrics()">{{ __('Apply') }}</button>
						<div class="btn-group">
							<button class="btn btn-default" @click="setDatePreset('today')">{{ __('Today') }}</button>
							<button class="btn btn-default" @click="setDatePreset('yesterday')">{{ __('Yesterday') }}</button>
							<button class="btn btn-default" @click="setDatePreset('week')">{{ __('This Week') }}</button>
							<button class="btn btn-default" @click="setDatePreset('month')">{{ __('This Month') }}</button>
						</div>
						<button class="btn btn-secondary" @click="exportCSV()">{{ __('CSV') }}</button>
						<button class="btn btn-secondary" @click="exportExcel()">{{ __('Excel') }}</button>
					</div>
				</div>

				<div class="rd-section">
					<div class="rd-grid kpis">
						<div v-for="card in kpiCards" :key="card.key" class="rd-card" :style="{borderTop: '4px solid ' + card.color}" @click="scrollTo(card.anchor)">
							<div class="text-muted text-uppercase" style="font-size: 11px;">{{ card.label }}</div>
							<div class="h4 mb-0">{{ formatCurrency(card.value) }}</div>
						</div>
					</div>
				</div>

				<div class="rd-section rd-card" id="order-type-section">
					<h4>{{ __('Orders by Type') }}</h4>
					<div class="row">
						<div class="col-md-6">
							<table class="rd-table">
								<thead>
									<tr>
										<th>{{ __('Type') }}</th>
										<th class="text-right">{{ __('Orders') }}</th>
										<th class="text-right">{{ __('Value') }}</th>
										<th class="text-right">{{ __('%') }}</th>
									</tr>
								</thead>
								<tbody>
									<tr v-for="row in order_type_summary" :key="row.type">
										<td>{{ row.type }}</td>
										<td class="text-right">{{ row.orders }}</td>
										<td class="text-right">{{ formatCurrency(row.value) }}</td>
										<td class="text-right">{{ row.contribution_pct.toFixed(1) }}%</td>
									</tr>
								</tbody>
							</table>
						</div>
						<div class="col-md-6">
							<canvas id="order-type-chart" height="220"></canvas>
						</div>
					</div>
				</div>

				<div class="rd-section rd-card">
					<h4>{{ __('Price List / Channel') }}</h4>
					<div class="row">
						<div class="col-md-6">
							<table class="rd-table">
								<thead>
									<tr>
										<th>{{ __('Channel') }}</th>
										<th class="text-right">{{ __('Orders') }}</th>
										<th class="text-right">{{ __('Value') }}</th>
										<th class="text-right">{{ __('%') }}</th>
									</tr>
								</thead>
								<tbody>
									<tr v-for="row in price_list_summary" :key="row.channel">
										<td>{{ row.channel }}</td>
										<td class="text-right">{{ row.orders }}</td>
										<td class="text-right">{{ formatCurrency(row.value) }}</td>
										<td class="text-right">{{ row.contribution_pct.toFixed(1) }}%</td>
									</tr>
								</tbody>
							</table>
						</div>
						<div class="col-md-6">
							<canvas id="price-list-chart" height="220"></canvas>
						</div>
					</div>
				</div>

				<div class="rd-section rd-card">
					<h4>{{ __('Top Items') }}</h4>
					<table class="rd-table">
						<thead>
							<tr>
								<th>{{ __('Item') }}</th>
								<th class="text-right">{{ __('Qty') }}</th>
								<th class="text-right">{{ __('Value') }}</th>
								<th class="text-right">{{ __('%') }}</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="row in top_items" :key="row.item_code">
								<td>{{ row.item_name || row.item_code }}</td>
								<td class="text-right">{{ row.qty }}</td>
								<td class="text-right">{{ formatCurrency(row.value) }}</td>
								<td class="text-right">{{ row.contribution_pct.toFixed(1) }}%</td>
							</tr>
						</tbody>
					</table>
				</div>

				<div class="rd-section rd-card">
					<h4>{{ __('Peak Hours') }}</h4>
					<canvas id="peak-hours-chart" height="250"></canvas>
				</div>

				<div class="rd-section rd-card" v-if="branch_comparison && branch_comparison.length">
					<h4>{{ __('Branch Comparison') }}</h4>
					<div class="row">
						<div class="col-md-6">
							<table class="rd-table">
								<thead>
									<tr>
										<th>{{ __('Branch') }}</th>
										<th class="text-right">{{ __('Orders') }}</th>
										<th class="text-right">{{ __('Value') }}</th>
										<th class="text-right">{{ __('Avg Order Value') }}</th>
									</tr>
								</thead>
								<tbody>
									<tr v-for="row in branch_comparison" :key="row.branch">
										<td>{{ row.branch }}</td>
										<td class="text-right">{{ row.orders }}</td>
										<td class="text-right">{{ formatCurrency(row.value) }}</td>
										<td class="text-right">{{ formatCurrency(row.avg_order_value) }}</td>
									</tr>
								</tbody>
							</table>
						</div>
						<div class="col-md-6">
							<canvas id="branch-chart" height="220"></canvas>
						</div>
					</div>
				</div>
			</div>
		`,
	});
}
