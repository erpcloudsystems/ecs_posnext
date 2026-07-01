frappe.pages["sales_by_branch"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Sales by Branch"),
		single_column: true,
	});

	const $container = $(`
		<div id="sales-by-branch-app" class="py-4"></div>
	`);
	$(page.body).append($container);

	const scripts = [
		"https://cdn.jsdelivr.net/npm/vue@2.7.14/dist/vue.min.js",
		"https://cdn.jsdelivr.net/npm/chart.js",
	];

	_add_styles();
	_load_scripts(scripts)
		.then(() => init_app(page))
		.catch(() => frappe.msgprint(__("Failed to load resources")));
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
		.sb-filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 8px; }
		.sb-card { background: #fff; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); padding: 12px; }
		.sb-table { width: 100%; border-collapse: collapse; }
		.sb-table th, .sb-table td { padding: 8px 10px; border-bottom: 1px solid #f1f3f5; text-align: left; }
		.sb-table th { background: #f8fafc; text-transform: uppercase; font-size: 11px; letter-spacing: 0.02em; }
		.sb-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; }
	`;
	const tag = document.createElement("style");
	tag.innerHTML = css;
	document.head.appendChild(tag);
}

function init_app(page) {
	/* eslint-disable no-new */
	new Vue({
		el: "#sales-by-branch-app",
		data() {
			const today = frappe.datetime.get_today();
			return {
				loading: false,
				filters: {
					from_date: today,
					to_date: today,
					branches: [],
					pos_profiles: [],
					items: [],
					item_groups: [],
					owners: [],
				},
				totals: {},
				branch_summary: [],
				detail: [],
				orders: [],
				chart: { labels: [], values: [] },
				charts: {},
				ctrls: {},
				showDetails: true,
				showOrders: true,
			};
		},
		computed: {
			kpiCards() {
				return [
					{ key: "net_sales", label: __("Net Sales"), color: "#16a34a" },
					{ key: "net_with_tax", label: __("Net + Tax"), color: "#0ea5e9" },
					{ key: "tax_amount", label: __("Tax"), color: "#f97316" },
					{ key: "discount_amount", label: __("Discount"), color: "#a855f7" },
					{ key: "gross_sales", label: __("Gross Sales"), color: "#64748b" },
					{ key: "qty", label: __("Qty"), color: "#22c55e" },
				].map((c) => ({ ...c, value: this.totals[c.key] || 0 }));
			},
		},
		mounted() {
			this.initControls();
			this.fetchData();
		},
		methods: {
			initControls() {
				this.makeLinkMulti(this.$refs.branchCtrl, "Branch", "branches");
				this.makeLinkMulti(this.$refs.posProfileCtrl, "POS Profile", "pos_profiles");
				this.makeLinkMulti(this.$refs.itemCtrl, "Item", "items");
				this.makeLinkMulti(this.$refs.itemGroupCtrl, "Item Group", "item_groups");
				this.makeLinkMulti(this.$refs.ownerCtrl, "User", "owners", {
					filters: { enabled: 1, user_type: "System User" },
				});
			},
			makeLinkMulti(parentEl, doctype, modelKey, extra = {}) {
				if (!parentEl) return;
				const df = {
					fieldtype: "MultiSelectList",
					label: doctype,
					get_data: function (txt) {
						return frappe.db.get_link_options(doctype, txt, extra.filters || {});
					},
					onchange: () => {},
				};
				const ctrl = frappe.ui.form.make_control({
					df,
					parent: parentEl,
					render_input: true,
				});
				ctrl.$input && ctrl.$input.addClass("form-control");
				const handleChange = () => {
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
					this.filters[modelKey] = vals;
					this.fetchData();
				};
				// bind to both control change and df onchange
				ctrl.onchange = handleChange;
				df.onchange = handleChange;
				this.ctrls[modelKey] = ctrl;
			},
			formatCurrency(val) {
				return (Number(val) || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			},
			formatNumber(val) {
				return (Number(val) || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
			},
			makePayload() {
				return {
					from_date: this.filters.from_date,
					to_date: this.filters.to_date,
					branches: this.filters.branches,
					pos_profiles: this.filters.pos_profiles,
					items: this.filters.items,
					item_groups: this.filters.item_groups,
					owners: this.filters.owners,
				};
			},
			fetchData() {
				this.loading = true;
				frappe.call({
					method: "ecs_posnext.api.sales_by_branch.get_sales_by_branch",
					args: { filters: this.makePayload() },
				}).then((r) => {
					const data = r.message || {};
					this.totals = data.totals || {};
					this.branch_summary = data.branch_summary || [];
					this.detail = data.detail || [];
					this.orders = data.orders || [];
					this.chart = data.chart || { labels: [], values: [] };
					this.$nextTick(() => this.drawChart());
				}).finally(() => {
					this.loading = false;
				});
			},
			drawChart() {
				const ctx = document.getElementById("branch-chart");
				if (!ctx || !window.Chart) return;
				if (this.charts.branch) {
					this.charts.branch.destroy();
				}
				this.charts.branch = new Chart(ctx, {
					type: "bar",
					data: {
						labels: this.chart.labels || [],
						datasets: [
							{
								label: __("Net Sales"),
								data: this.chart.values || [],
								backgroundColor: "#0ea5e9",
							},
						],
					},
					options: { responsive: true, scales: { y: { beginAtZero: true } } },
				});
			},
			exportCSV() {
				const rows = [
					["Branch", "POS Profile", "Item Code", "Item", "Item Group", "Qty", "Gross", "Discount", "Tax", "Net", "Net+Tax", "Sales %"],
					...this.detail.map((d) => [
						d.branch || "",
						d.pos_profile || "",
						d.item_code || "",
						d.item_name || "",
						d.item_group || "",
						d.qty || 0,
						d.gross_sales || 0,
						d.discount_amount || 0,
						d.tax_amount || 0,
						d.net_sales || 0,
						d.net_with_tax || 0,
						(d.sales_pct || 0).toFixed(2),
					]),
				];
				const csv = rows.map((r) => r.map((c) => `"${c}"`).join(",")).join("\n");
				const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
				const link = document.createElement("a");
				link.href = URL.createObjectURL(blob);
				link.download = "sales_by_branch.csv";
				link.click();
			},
			exportExcel() {
				const rows = [
					["Branch", "POS Profile", "Item Code", "Item", "Item Group", "Qty", "Gross", "Discount", "Tax", "Net", "Net+Tax", "Sales %"],
					...this.detail.map((d) => [
						d.branch || "",
						d.pos_profile || "",
						d.item_code || "",
						d.item_name || "",
						d.item_group || "",
						d.qty || 0,
						d.gross_sales || 0,
						d.discount_amount || 0,
						d.tax_amount || 0,
						d.net_sales || 0,
						d.net_with_tax || 0,
						(d.sales_pct || 0).toFixed(2),
					]),
				];
				const tsv = rows.map((r) => r.join("\t")).join("\n");
				const blob = new Blob([tsv], { type: "application/vnd.ms-excel" });
				const link = document.createElement("a");
				link.href = URL.createObjectURL(blob);
				link.download = "sales_by_branch.xls";
				link.click();
			},
		},
		template: `
			<div class="sb-page">
				<div class="sb-card">
					<div class="sb-filters">
						<input type="date" class="form-control" v-model="filters.from_date" @change="fetchData()" />
						<input type="date" class="form-control" v-model="filters.to_date" @change="fetchData()" />

						<div ref="branchCtrl"></div>
						<div ref="posProfileCtrl"></div>
						<div ref="itemCtrl"></div>
						<div ref="itemGroupCtrl"></div>
						<div ref="ownerCtrl"></div>

						<button type="button" class="btn btn-secondary" @click.prevent="exportCSV()">{{ __('CSV') }}</button>
						<button type="button" class="btn btn-secondary" @click.prevent="exportExcel()">{{ __('Excel') }}</button>
					</div>
				</div>

				<div class="sb-kpis">
					<div v-for="card in kpiCards" :key="card.key" class="sb-card" :style="{borderTop: '3px solid ' + card.color}">
						<div class="text-muted" style="font-size: 11px; text-transform: uppercase;">{{ card.label }}</div>
						<div class="h5 mb-0">{{ ['qty'].includes(card.key) ? formatNumber(card.value) : formatCurrency(card.value) }}</div>
					</div>
				</div>

				<div class="row mt-3">
					<div class="col-md-6 sb-card">
						<h5>{{ __('Branch Summary') }}</h5>
						<table class="sb-table">
							<thead>
								<tr>
									<th>{{ __('Branch') }}</th>
									<th class="text-right">{{ __('Net Sales') }}</th>
									<th class="text-right">{{ __('Tax') }}</th>
									<th class="text-right">{{ __('Net + Tax') }}</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="row in branch_summary" :key="row.branch">
									<td>{{ row.branch }}</td>
									<td class="text-right">{{ formatCurrency(row.net_sales) }}</td>
									<td class="text-right">{{ formatCurrency(row.tax_amount) }}</td>
									<td class="text-right">{{ formatCurrency(row.net_with_tax) }}</td>
								</tr>
							</tbody>
						</table>
					</div>
					<div class="col-md-6 sb-card">
						<h5>{{ __('Branch Sales Chart') }}</h5>
						<canvas id="branch-chart" height="220"></canvas>
					</div>
				</div>

				<div class="sb-card mt-3">
					<h5 style="cursor:pointer;" @click="showDetails = !showDetails">
						{{ __('Sales Details') }}
						<span class="text-muted" style="font-size:12px;">{{ showDetails ? __('(Hide)') : __('(Show)') }}</span>
					</h5>
					<div v-if="showDetails">
						<table class="sb-table">
							<thead>
								<tr>
									<th>{{ __('Branch') }}</th>
									<th>{{ __('POS Profile') }}</th>
									<th>{{ __('Item Code') }}</th>
									<th>{{ __('Item') }}</th>
									<th>{{ __('Item Group') }}</th>
									<th class="text-right">{{ __('Qty') }}</th>
									<th class="text-right">{{ __('Gross') }}</th>
									<th class="text-right">{{ __('Discount') }}</th>
									<th class="text-right">{{ __('Tax') }}</th>
									<th class="text-right">{{ __('Net') }}</th>
									<th class="text-right">{{ __('Net + Tax') }}</th>
									<th class="text-right">{{ __('Sales %') }}</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="row in detail" :key="row.branch + row.item_code + row.pos_profile">
									<td>{{ row.branch }}</td>
									<td>{{ row.pos_profile }}</td>
									<td>{{ row.item_code }}</td>
									<td>{{ row.item_name }}</td>
									<td>{{ row.item_group }}</td>
									<td class="text-right">{{ formatNumber(row.qty) }}</td>
									<td class="text-right">{{ formatCurrency(row.gross_sales) }}</td>
									<td class="text-right">{{ formatCurrency(row.discount_amount) }}</td>
									<td class="text-right">{{ formatCurrency(row.tax_amount) }}</td>
									<td class="text-right">{{ formatCurrency(row.net_sales) }}</td>
									<td class="text-right">{{ formatCurrency(row.net_with_tax) }}</td>
									<td class="text-right">{{ (row.sales_pct || 0).toFixed(2) }}%</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>

				<div class="sb-card mt-3">
					<h5 style="cursor:pointer;" @click="showOrders = !showOrders">
						{{ __('Orders') }}
						<span class="text-muted" style="font-size:12px;">{{ showOrders ? __('(Hide)') : __('(Show)') }}</span>
					</h5>
					<div v-if="showOrders">
						<table class="sb-table">
							<thead>
								<tr>
									<th>{{ __('Order') }}</th>
									<th>{{ __('Customer') }}</th>
									<th>{{ __('Branch') }}</th>
									<th>{{ __('POS Profile') }}</th>
									<th>{{ __('Date') }}</th>
									<th class="text-right">{{ __('Grand Total') }}</th>
									<th class="text-right">{{ __('Discount') }}</th>
									<th class="text-right">{{ __('Tax') }}</th>
									<th class="text-right">{{ __('Net Total') }}</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="row in orders" :key="row.name">
									<td>{{ row.name }}</td>
									<td>{{ row.customer_name }}</td>
									<td>{{ row.branch }}</td>
									<td>{{ row.pos_profile }}</td>
									<td>{{ row.posting_date }}</td>
									<td class="text-right">{{ formatCurrency(row.grand_total) }}</td>
									<td class="text-right">{{ formatCurrency(row.discount_amount) }}</td>
									<td class="text-right">{{ formatCurrency(row.tax_amount) }}</td>
									<td class="text-right">{{ formatCurrency(row.net_total) }}</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>
			</div>
		`,
	});
}
