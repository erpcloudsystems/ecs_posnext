frappe.pages['daily_operation_planning'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Daily Operation Planning'),
		single_column: true
	});

	// Add custom styles
	$('<style>')
		.prop('type', 'text/css')
		.html(`
			.dop-filters { 
				display: flex; 
				flex-wrap: wrap; 
				gap: 10px; 
				margin-bottom: 15px; 
				padding: 15px;
				background: #f5f7fa;
				border-radius: 8px;
			}
			.dop-filters .frappe-control { 
				margin-bottom: 0 !important; 
				min-width: 150px;
			}
			.dop-table-wrapper {
				overflow-x: auto;
			}
			.dop-table {
				width: 100%;
				border-collapse: collapse;
				font-size: 13px;
			}
			.dop-table th, .dop-table td {
				border: 1px solid #d1d8dd;
				padding: 8px 10px;
				text-align: right;
			}
			.dop-table th {
				background: #f0f4f7;
				font-weight: 600;
				position: sticky;
				top: 0;
			}
			.dop-table tr:nth-child(even) {
				background: #fafbfc;
			}
			.dop-table tr:hover {
				background: #e8f4fd;
			}
			.dop-table .editable-input {
				width: 70px;
				padding: 4px 6px;
				border: 1px solid #d1d8dd;
				border-radius: 4px;
				text-align: center;
			}
			.dop-table .editable-input:focus {
				border-color: #5e64ff;
				outline: none;
			}
			.dop-table .positive { color: #36a500; font-weight: 600; }
			.dop-table .negative { color: #ff5858; }
			.dop-summary {
				margin-top: 15px;
				padding: 10px 15px;
				background: #e3f2fd;
				border-radius: 6px;
				font-size: 13px;
			}
			.dop-actions {
				margin-bottom: 15px;
			}
		`)
		.appendTo('head');

	new DailyOperationPlanning(page);
};

class DailyOperationPlanning {
	constructor(page) {
		this.page = page;
		this.data = [];
		this.filters = {};
		this.make();
	}

	make() {
		this.setup_page_actions();
		this.setup_filters();
		this.setup_table_container();
	}

	setup_page_actions() {
		this.page.set_primary_action(__('تحديث'), () => this.refresh_data(), 'refresh');
		
		this.page.set_secondary_action(__('إنشاء طلب مواد'), () => this.create_material_request(), 'add');
		
		this.page.add_menu_item(__('تصدير Excel'), () => this.export_to_excel());
		this.page.add_menu_item(__('طباعة'), () => this.print_report());
	}

	setup_filters() {
		const filters_html = `<div class="dop-filters"></div>`;
		$(this.page.body).append(filters_html);
		
		const $filters = $(this.page.body).find('.dop-filters');

		// Company filter
		this.company_field = frappe.ui.form.make_control({
			df: {
				fieldtype: 'Link',
				options: 'Company',
				fieldname: 'company',
				label: __('الشركة'),
				default: frappe.defaults.get_default('company'),
				onchange: () => this.on_filter_change()
			},
			parent: $filters,
			render_input: true
		});

		// Warehouse filter
		this.warehouse_field = frappe.ui.form.make_control({
			df: {
				fieldtype: 'Link',
				options: 'Warehouse',
				fieldname: 'warehouse',
				label: __('المخزن'),
				reqd: 1,
				onchange: () => this.on_filter_change()
			},
			parent: $filters,
			render_input: true
		});

		// Date filter
		this.date_field = frappe.ui.form.make_control({
			df: {
				fieldtype: 'Date',
				fieldname: 'posting_date',
				label: __('التاريخ'),
				default: frappe.datetime.get_today(),
				reqd: 1,
				onchange: () => this.on_filter_change()
			},
			parent: $filters,
			render_input: true
		});

		// Weeks count filter
		this.weeks_field = frappe.ui.form.make_control({
			df: {
				fieldtype: 'Int',
				fieldname: 'weeks_count',
				label: __('عدد الأسابيع'),
				default: 4,
				onchange: () => this.on_filter_change()
			},
			parent: $filters,
			render_input: true
		});

		// Item Group filter
		this.item_group_field = frappe.ui.form.make_control({
			df: {
				fieldtype: 'Link',
				options: 'Item Group',
				fieldname: 'item_group',
				label: __('مجموعة الأصناف'),
				onchange: () => this.on_filter_change()
			},
			parent: $filters,
			render_input: true
		});

		// Only operation items filter
		this.only_operation_field = frappe.ui.form.make_control({
			df: {
				fieldtype: 'Check',
				fieldname: 'only_operation_items',
				label: __('أصناف التشغيل فقط'),
				default: 1,
				onchange: () => this.on_filter_change()
			},
			parent: $filters,
			render_input: true
		});

		// Global growth factor — applied to ALL items when set
		this.global_growth_field = frappe.ui.form.make_control({
			df: {
				fieldtype: 'Float',
				fieldname: 'global_growth_factor',
				label: __('نسبة الزيادة الإجمالية'),
				description: __('تُطبَّق على جميع الأصناف عند تحديدها'),
				onchange: () => this.apply_global_growth()
			},
			parent: $filters,
			render_input: true
		});
	}

	setup_table_container() {
		const table_html = `
			<div class="dop-actions"></div>
			<div class="dop-table-wrapper">
				<table class="dop-table">
					<thead></thead>
					<tbody></tbody>
				</table>
			</div>
			<div class="dop-summary"></div>
		`;
		$(this.page.body).append(table_html);
	}

	on_filter_change() {
		// Debounce filter changes
		clearTimeout(this.filter_timeout);
		this.filter_timeout = setTimeout(() => {
			// Auto refresh disabled - user must click refresh
		}, 500);
	}

	get_filters() {
		return {
			company: this.company_field.get_value(),
			warehouse: this.warehouse_field.get_value(),
			posting_date: this.date_field.get_value(),
			weeks_count: this.weeks_field.get_value() || 4,
			item_group: this.item_group_field.get_value(),
			only_operation_items: this.only_operation_field.get_value() ? 1 : 0
		};
	}

	async refresh_data() {
		const filters = this.get_filters();
		
		if (!filters.warehouse) {
			frappe.msgprint(__('يجب اختيار المخزن'));
			return;
		}

		if (!filters.posting_date) {
			frappe.msgprint(__('يجب اختيار التاريخ'));
			return;
		}

		frappe.show_progress(__('جاري التحميل...'), 30, 100);

		try {
			const r = await frappe.call({
				method: 'ecs_posnext.pos_next.page.daily_operation_planning.daily_operation_planning.get_planning_data',
				args: { filters: filters }
			});

			frappe.hide_progress();

			if (r.message) {
				this.data = r.message.data || [];
				this.columns = r.message.columns || [];
				this.render_table();
				this.render_summary();
			}
		} catch (e) {
			frappe.hide_progress();
			frappe.msgprint(__('خطأ في تحميل البيانات'));
			console.error(e);
		}
	}

	render_table() {
		const $thead = $(this.page.body).find('.dop-table thead');
		const $tbody = $(this.page.body).find('.dop-table tbody');
		
		$thead.empty();
		$tbody.empty();

		if (!this.data.length) {
			$tbody.html('<tr><td colspan="20" style="text-align:center;padding:30px;">لا توجد بيانات</td></tr>');
			return;
		}

		// Build header
		let header_html = '<tr>';
		header_html += '<th>#</th>';
		header_html += '<th>' + __('كود الصنف') + '</th>';
		header_html += '<th>' + __('اسم الصنف') + '</th>';
		header_html += '<th>' + __('الوحدة') + '</th>';
		
		const weeks_count = Math.min(this.get_filters().weeks_count || 4, 4);
		for (let i = 1; i <= weeks_count; i++) {
			header_html += '<th>' + __('أسبوع {0}', [i]) + '</th>';
		}
		
		header_html += '<th>' + __('معدل يوم') + '</th>';
		header_html += '<th>' + __('نسبة الزيادة') + '</th>';
		header_html += '<th>' + __('إجمالي المطلوب') + '</th>';
		header_html += '<th>' + __('جرد اليوم') + '</th>';
		header_html += '<th>' + __('المطلوب') + '</th>';
		header_html += '</tr>';
		$thead.html(header_html);

		// Build rows
		this.data.forEach((row, idx) => {
			// Preserve original per-item growth factor on first render
			if (row._original_growth_factor === undefined) {
				row._original_growth_factor = row.growth_factor;
			}
			let row_html = '<tr data-item="' + row.item_code + '">';
			row_html += '<td>' + (idx + 1) + '</td>';
			row_html += '<td>' + (row.item_code || '') + '</td>';
			row_html += '<td>' + (row.item_name || '') + '</td>';
			row_html += '<td>' + (row.stock_uom || '') + '</td>';
			
			for (let i = 1; i <= weeks_count; i++) {
				const qty = row['week_' + i + '_qty'] || 0;
				row_html += '<td>' + this.format_number(qty) + '</td>';
			}
			
			row_html += '<td>' + this.format_number(row.daily_avg_qty) + '</td>';
			
			// Editable growth factor
			row_html += '<td><input type="number" class="editable-input growth-factor" value="' + 
				(row.growth_factor || 1.3) + '" step="0.1" min="0" data-item="' + row.item_code + '"></td>';
			
			row_html += '<td class="gross-required">' + this.format_number(row.gross_required_qty) + '</td>';
			row_html += '<td>' + this.format_number(row.current_stock_qty) + '</td>';
			
			const net_class = row.net_required_qty > 0 ? 'positive' : '';
			row_html += '<td class="net-required ' + net_class + '">' + this.format_number(row.net_required_qty) + '</td>';
			
			row_html += '</tr>';
			$tbody.append(row_html);
		});

		// Bind events for editable growth factor
		$tbody.find('.growth-factor').on('change', (e) => this.on_growth_factor_change(e));
	}

	on_growth_factor_change(e) {
		const $input = $(e.target);
		const item_code = $input.data('item');
		const new_growth = parseFloat($input.val()) || 1;

		// Find the row and recalculate
		const row = this.data.find(r => r.item_code === item_code);
		if (row) {
			row.growth_factor = new_growth;
			row.gross_required_qty = row.daily_avg_qty * new_growth;
			row.net_required_qty = Math.max(0, row.gross_required_qty - row.current_stock_qty);

			// Update cells
			const $tr = $input.closest('tr');
			$tr.find('.gross-required').text(this.format_number(row.gross_required_qty));
			$tr.find('.net-required')
				.text(this.format_number(row.net_required_qty))
				.toggleClass('positive', row.net_required_qty > 0);

			this.render_summary();
		}
	}

	apply_global_growth() {
		const global_growth = parseFloat(this.global_growth_field && this.global_growth_field.get_value()) || 0;
		if (!this.data || !this.data.length) return;

		this.data.forEach(row => {
			const growth = global_growth > 0 ? global_growth : (row._original_growth_factor || row.growth_factor);
			row.growth_factor = growth;
			row.gross_required_qty = row.daily_avg_qty * growth;
			row.net_required_qty = Math.max(0, row.gross_required_qty - row.current_stock_qty);
		});

		// Re-render only the affected columns
		const $tbody = $(this.page.body).find('.dop-table tbody');
		$tbody.find('tr').each((idx, tr) => {
			const item_code = $(tr).data('item');
			const row = this.data.find(r => r.item_code === item_code);
			if (!row) return;
			$(tr).find('.growth-factor').val(row.growth_factor);
			$(tr).find('.gross-required').text(this.format_number(row.gross_required_qty));
			$(tr).find('.net-required')
				.text(this.format_number(row.net_required_qty))
				.toggleClass('positive', row.net_required_qty > 0);
		});

		this.render_summary();
	}

	render_summary() {
		const $summary = $(this.page.body).find('.dop-summary');
		
		if (!this.data.length) {
			$summary.empty();
			return;
		}

		const total_items = this.data.length;
		const items_needed = this.data.filter(r => r.net_required_qty > 0).length;
		
		$summary.html(`
			<strong>${__('ملخص')}:</strong> 
			${__('إجمالي الأصناف')}: ${total_items} | 
			${__('أصناف تحتاج تحضير')}: <span class="positive">${items_needed}</span>
		`);
	}

	format_number(num) {
		if (num === null || num === undefined) return '-';
		return parseFloat(num).toFixed(2);
	}

	export_to_excel() {
		if (!this.data.length) {
			frappe.msgprint(__('لا توجد بيانات للتصدير'));
			return;
		}
		
		// Simple CSV export
		let csv = 'Item Code,Item Name,UOM,Daily Avg,Growth Factor,Gross Required,Current Stock,Net Required\n';
		this.data.forEach(row => {
			csv += `${row.item_code},${row.item_name},${row.stock_uom},${row.daily_avg_qty},${row.growth_factor},${row.gross_required_qty},${row.current_stock_qty},${row.net_required_qty}\n`;
		});
		
		const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
		const link = document.createElement('a');
		link.href = URL.createObjectURL(blob);
		link.download = 'daily_operation_planning.csv';
		link.click();
	}

	print_report() {
		window.print();
	}

	async create_material_request() {
		// Filter items with net_required_qty > 0
		const items_to_request = this.data.filter(r => r.net_required_qty > 0);
		
		if (!items_to_request.length) {
			frappe.msgprint(__('لا توجد أصناف تحتاج طلب مواد'));
			return;
		}

		const filters = this.get_filters();
		
		frappe.confirm(
			__('سيتم إنشاء طلب مواد لـ {0} صنف. هل تريد المتابعة؟', [items_to_request.length]),
			async () => {
				try {
					frappe.show_progress(__('جاري إنشاء طلب المواد...'), 50, 100);
					
					const r = await frappe.call({
						method: 'ecs_posnext.pos_next.page.daily_operation_planning.daily_operation_planning.create_material_request',
						args: {
							items: items_to_request.map(item => ({
								item_code: item.item_code,
								qty: item.net_required_qty,
								uom: item.stock_uom
							})),
							warehouse: filters.warehouse,
							company: filters.company
						}
					});
					
					frappe.hide_progress();
					
					if (r.message) {
						frappe.msgprint({
							title: __('تم بنجاح'),
							indicator: 'green',
							message: __('تم إنشاء طلب المواد: {0}', 
								[`<a href="/app/material-request/${r.message}">${r.message}</a>`])
						});
					}
				} catch (e) {
					frappe.hide_progress();
					frappe.msgprint(__('خطأ في إنشاء طلب المواد'));
					console.error(e);
				}
			}
		);
	}
}
