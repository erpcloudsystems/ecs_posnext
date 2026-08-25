frappe.pages["daily_item_sales_summary"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Daily Item Sales Summary"),
		single_column: true,
	});

	const $container = $(`
		<div id="daily-item-sales-summary-app" class="py-4"></div>
	`);
	$(page.body).append($container);

	_add_styles();
	_load_scripts(["https://cdn.jsdelivr.net/npm/vue@2.7.14/dist/vue.min.js"])
		.then(() => init_app())
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
		.diss-filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 8px; align-items: end; }
		.diss-card { background: #fff; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); padding: 12px; }
		.diss-table { width: 100%; border-collapse: collapse; }
		.diss-table th, .diss-table td { padding: 8px 10px; border-bottom: 1px solid #f1f3f5; text-align: left; }
		.diss-table th { background: #f8fafc; text-transform: uppercase; font-size: 11px; letter-spacing: 0.02em; }
		.diss-table tr.diss-item-row td { font-weight: 600; background: #fbfdff; }
		.diss-table tr.diss-branch-row td:first-child { padding-left: 26px; color: #52606d; }
		.diss-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; }
		.diss-filter-label { font-size: 11px; text-transform: uppercase; color: #52606d; margin-bottom: 2px; }
	`;
	const tag = document.createElement("style");
	tag.innerHTML = css;
	document.head.appendChild(tag);
}

function init_app() {
	/* eslint-disable no-new */
	new Vue({
		el: "#daily-item-sales-summary-app",
		data() {
			return {
				loading: false,
				filters: {
					business_day: "",
					branches: [],
					warehouses: [],
					item_groups: [],
					items: [],
				},
				item_summary: [],
				branch_detail: [],
				totals: {},
				ctrls: {},
				showBranchBreakdown: true,
			};
		},
		computed: {
			kpiCards() {
				return [
					{ key: "item_count", label: __("Items Sold"), color: "#0ea5e9", isCount: true },
					{ key: "total_qty", label: __("Total Qty Sold"), color: "#22c55e", isCount: true },
					{ key: "invoice_count", label: __("No. of Invoices"), color: "#a855f7", isCount: true },
					{ key: "total_amount", label: __("Total Sales Amount"), color: "#16a34a", isCount: false },
				].map((c) => ({ ...c, value: this.totals[c.key] || 0 }));
			},
			// item_code -> list of its branch rows, for nesting under each summary row
			branchesByItem() {
				const map = {};
				(this.branch_detail || []).forEach((row) => {
					if (!map[row.item_code]) map[row.item_code] = [];
					map[row.item_code].push(row);
				});
				return map;
			},
		},
		mounted() {
			this.initControls();
			this.fetchData();
		},
		methods: {
			initControls() {
				this.makeLinkSingle(this.$refs.businessDayCtrl, "POS Business Day", "business_day");
				this.makeLinkMulti(this.$refs.branchCtrl, "Branch", "branches");
				this.makeLinkMulti(this.$refs.warehouseCtrl, "Warehouse", "warehouses");
				this.makeLinkMulti(this.$refs.itemGroupCtrl, "Item Group", "item_groups");
				this.makeLinkMulti(this.$refs.itemCtrl, "Item", "items");
			},
			makeLinkSingle(parentEl, doctype, modelKey) {
				if (!parentEl) return;
				const df = {
					fieldtype: "Link",
					label: doctype,
					options: doctype,
					onchange: () => {},
				};
				const ctrl = frappe.ui.form.make_control({
					df,
					parent: parentEl,
					render_input: true,
				});
				ctrl.$input && ctrl.$input.addClass("form-control");
				const handleChange = () => {
					this.filters[modelKey] = ctrl.get_value() || "";
					this.fetchData();
				};
				ctrl.onchange = handleChange;
				df.onchange = handleChange;
				this.ctrls[modelKey] = ctrl;
			},
			makeLinkMulti(parentEl, doctype, modelKey) {
				if (!parentEl) return;
				const df = {
					fieldtype: "MultiSelectList",
					label: doctype,
					get_data: function (txt) {
						return frappe.db.get_link_options(doctype, txt);
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
						vals = raw.split(",").map((v) => v.trim()).filter(Boolean);
					}
					this.filters[modelKey] = vals;
					this.fetchData();
				};
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
			fetchData() {
				this.loading = true;
				frappe.call({
					method: "ecs_posnext.api.daily_item_sales_summary.get_daily_item_sales_summary",
					args: { filters: this.filters },
				}).then((r) => {
					const data = r.message || {};
					this.item_summary = data.item_summary || [];
					this.branch_detail = data.branch_detail || [];
					this.totals = data.totals || {};
				}).finally(() => {
					this.loading = false;
				});
			},
			exportExcel() {
				open_url_post(
					"/api/method/ecs_posnext.api.daily_item_sales_summary.download_excel",
					{ filters: JSON.stringify(this.filters) }
				);
			},
		},
		template: `
			<div class="diss-page">
				<div class="diss-card">
					<div class="diss-filters">
						<div>
							<div class="diss-filter-label">{{ __('Business Day') }}</div>
							<div ref="businessDayCtrl"></div>
						</div>
						<div>
							<div class="diss-filter-label">{{ __('Branch') }}</div>
							<div ref="branchCtrl"></div>
						</div>
						<div>
							<div class="diss-filter-label">{{ __('Warehouse') }}</div>
							<div ref="warehouseCtrl"></div>
						</div>
						<div>
							<div class="diss-filter-label">{{ __('Item Group') }}</div>
							<div ref="itemGroupCtrl"></div>
						</div>
						<div>
							<div class="diss-filter-label">{{ __('Item') }}</div>
							<div ref="itemCtrl"></div>
						</div>
						<div>
							<button type="button" class="btn btn-primary btn-sm" :disabled="loading" @click="fetchData">{{ __('Refresh') }}</button>
							<button type="button" class="btn btn-secondary btn-sm" @click.prevent="exportExcel()">{{ __('Excel') }}</button>
						</div>
					</div>
				</div>

				<div class="diss-kpis mt-3">
					<div v-for="card in kpiCards" :key="card.key" class="diss-card" :style="{borderTop: '3px solid ' + card.color}">
						<div class="text-muted" style="font-size: 11px; text-transform: uppercase;">{{ card.label }}</div>
						<div class="h5 mb-0">{{ card.isCount ? formatNumber(card.value) : formatCurrency(card.value) }}</div>
					</div>
				</div>

				<div class="diss-card mt-3">
					<h5 style="cursor:pointer;" @click="showBranchBreakdown = !showBranchBreakdown">
						{{ __('Item Sales Summary') }}
						<span class="text-muted" style="font-size:12px;">
							{{ showBranchBreakdown ? __('(Hide Branch Breakdown)') : __('(Show Branch Breakdown)') }}
						</span>
					</h5>
					<table class="diss-table">
						<thead>
							<tr>
								<th>{{ __('Item Code') }}</th>
								<th>{{ __('Item Name') }}</th>
								<th>{{ __('Branch') }}</th>
								<th class="text-right">{{ __('Total Qty Sold') }}</th>
								<th class="text-right">{{ __('No. of Invoices') }}</th>
								<th class="text-right">{{ __('Total Sales Amount') }}</th>
							</tr>
						</thead>
						<tbody>
							<template v-for="row in item_summary">
								<tr class="diss-item-row" :key="row.item_code">
									<td>{{ row.item_code }}</td>
									<td>{{ row.item_name }}</td>
									<td>{{ __('All Branches') }}</td>
									<td class="text-right">{{ formatNumber(row.total_qty) }}</td>
									<td class="text-right">{{ formatNumber(row.invoice_count) }}</td>
									<td class="text-right">{{ formatCurrency(row.total_amount) }}</td>
								</tr>
								<tr
									class="diss-branch-row"
									v-if="showBranchBreakdown"
									v-for="branchRow in (branchesByItem[row.item_code] || [])"
									:key="row.item_code + '-' + branchRow.branch"
								>
									<td></td>
									<td></td>
									<td>{{ branchRow.branch }}</td>
									<td class="text-right">{{ formatNumber(branchRow.total_qty) }}</td>
									<td class="text-right">{{ formatNumber(branchRow.invoice_count) }}</td>
									<td class="text-right">{{ formatCurrency(branchRow.total_amount) }}</td>
								</tr>
							</template>
							<tr v-if="!item_summary.length">
								<td colspan="6" class="text-muted text-center">{{ __('No sales found for the selected filters.') }}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
		`,
	});
}
