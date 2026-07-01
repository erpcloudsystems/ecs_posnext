// Copyright (c) 2024, POSAwesome and contributors
// For license information, please see license.txt

frappe.query_reports["Internal Inventory Audit"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("الشركة"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 0
        },
        {
            "fieldname": "warehouse",
            "label": __("الفرع/المخزن"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "reqd": 1,
            "get_query": function() {
                var company = frappe.query_report.get_filter_value('company');
                return {
                    "filters": {
                        "company": company,
                        "is_group": 0
                    }
                };
            }
        },
        {
            "fieldname": "central_warehouse",
            "label": __("المخزن الرئيسي"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "description": __("لتحديد 'محول من المخزن' - اتركه فارغاً لاعتبار كل التحويلات 'من فرع'"),
            "get_query": function() {
                var company = frappe.query_report.get_filter_value('company');
                return {
                    "filters": {
                        "company": company,
                        "is_group": 0
                    }
                };
            }
        },
        {
            "fieldname": "from_date",
            "label": __("من تاريخ"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_start(),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("إلى تاريخ"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "month",
            "label": __("الشهر"),
            "fieldtype": "Select",
            "options": "\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12",
            "description": __("اختياري - سيتم تحويله لنطاق تاريخ تلقائياً")
        },
        {
            "fieldname": "year",
            "label": __("السنة"),
            "fieldtype": "Select",
            "options": get_year_options(),
            "description": __("اختياري - يستخدم مع الشهر")
        },
        {
            "fieldname": "item_group",
            "label": __("مجموعة الأصناف"),
            "fieldtype": "Link",
            "options": "Item Group"
        },
        {
            "fieldname": "item_code",
            "label": __("الصنف"),
            "fieldtype": "Link",
            "options": "Item",
            "get_query": function() {
                return {
                    "filters": {
                        "is_stock_item": 1,
                        "disabled": 0
                    }
                };
            }
        },
        {
            "fieldname": "include_zero_rows",
            "label": __("إظهار الأصناف بدون حركة"),
            "fieldtype": "Check",
            "default": 0
        }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        // Highlight totals row
        if (data && data.item_code === __("الإجمالي")) {
            value = "<b>" + value + "</b>";
        }
        
        // Highlight variance (negative = shortage in red, positive = excess in green)
        if (column.fieldname === "variance_qty" && data) {
            if (data.variance_qty < 0) {
                value = "<span style='color: red; font-weight: bold;'>" + value + "</span>";
            } else if (data.variance_qty > 0) {
                value = "<span style='color: green; font-weight: bold;'>" + value + "</span>";
            }
        }
        
        return value;
    },
    
    "onload": function(report) {
        // Auto-update dates when month/year changes
        report.page.add_inner_button(__("تطبيق الشهر/السنة"), function() {
            var month = frappe.query_report.get_filter_value('month');
            var year = frappe.query_report.get_filter_value('year');
            
            if (month && year) {
                var from_date = new Date(year, month - 1, 1);
                var to_date = new Date(year, month, 0);
                
                frappe.query_report.set_filter_value('from_date', frappe.datetime.obj_to_str(from_date));
                frappe.query_report.set_filter_value('to_date', frappe.datetime.obj_to_str(to_date));
            }
        });
    }
};

function get_year_options() {
    var current_year = new Date().getFullYear();
    var options = [""];
    for (var i = current_year; i >= current_year - 5; i--) {
        options.push(i.toString());
    }
    return options.join("\n");
}
