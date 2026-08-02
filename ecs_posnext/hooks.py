from ecs_posnext.utils import get_build_version

app_name = "ecs_posnext"
app_title = "POS Next"
app_publisher = "BrainWise"
app_description = "POS built on ERPNext that brings together real-time billing, stock management, multi-user access, offline mode, and direct ERP integration. Run your store or restaurant with confidence and control, while staying 100% open source."
app_email = "support@brainwise.me"
app_license = "agpl-3.0"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "ecs_posnext",
# 		"logo": "/assets/ecs_posnext/logo.png",
# 		"title": "POS Next",
# 		"route": "/ecs_posnext",
# 		"has_permission": "ecs_posnext.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# Get unique build version for cache busting
_asset_version = get_build_version()

# include js, css files in header of desk.html
# app_include_css = f"/assets/ecs_posnext/css/ecs_posnext.css?v={_asset_version}"
# app_include_js = f"/assets/ecs_posnext/js/ecs_posnext.js?v={_asset_version}"

# include js, css files in header of web template
# web_include_css = "/assets/ecs_posnext/css/ecs_posnext.css"
# web_include_js = "/assets/ecs_posnext/js/ecs_posnext.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "ecs_posnext/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "ecs_posnext/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "ecs_posnext.utils.jinja_methods",
# 	"filters": "ecs_posnext.utils.jinja_filters"
# }

# Fixtures
# --------
fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			[
				"name",
				"in",
				[
					"Sales Invoice-posa_pos_opening_shift",
					"Sales Invoice-posa_is_printed",
					"Item-custom_company",
					"Item-custom_allow_rate_edit",
					"POS Profile-posa_cash_mode_of_payment",
					"POS Profile-posa_allow_delete",
					"POS Profile-posa_block_sale_beyond_available_qty",
					"Mode of Payment-is_wallet_payment",
					"Sales Invoice-custom_order_type",
					"POS Profile-custom_shift_start_time",
					"POS Profile-custom_shift_end_time",
					"Sales Invoice Item-posa_row_id",
					"Customer Complaint-custom_complaint_number",
					"Customer Complaint-custom_response_by",
					"Driver-dispatch_current_status",
					"Driver-dispatch_active_shift",
					"Payment Entry-custom_dispatch_shift",
					"Item-kds_station",
					"Sales Invoice Item-custom_selected_components",
					"Sales Invoice Item-is_bundle",
					"Sales Invoice Item-removed_ingredients",
					"Pricing Rule-custom_allowed_branches",
					"POS Profile-custom_business_day_section",
					"POS Profile-custom_enable_business_day_control",
					"POS Profile-custom_business_day_start_time",
					"POS Profile-custom_sales_cutoff_time",
					"POS Profile-custom_mandatory_closing_deadline_time",
					"POS Profile-custom_block_new_pos_opening_until_prev_closed",
					"POS Profile-custom_block_sales_after_cutoff",
					"POS Profile-custom_require_all_cashier_shifts_closed",
					"POS Profile-custom_require_no_unpaid_invoices",
					"POS Profile-custom_require_no_partly_paid_invoices",
					"POS Profile-custom_require_no_draft_orders",
					"POS Profile-custom_require_no_on_hold_orders",
					"POS Profile-custom_require_no_open_kds_orders",
					"POS Profile-custom_auto_close_business_day_when_ready",
					"POS Profile-custom_supervisor_opens_cashier_shifts",
					"Sales Invoice-custom_pos_business_day",
					"Sales Invoice-custom_pos_cashier_shift",
					"Payment Entry-custom_pos_business_day",
					"Payment Entry-custom_pos_cashier_shift",
					"Sales Invoice-custom_return_source"
				]
			]
		]
	},
	{
		"dt": "Print Format",
		"filters": [
			[
				"name",
				"in",
				[
					"POS Next Receipt",
					"Cashier Closing Small Paper"
				]
			]
		]
	},
    {
        "dt": "Role",
        "filters": [
            ["role_name", "in", ["POSNext Cashier", "Kitchen", "POSNext Supervisor", "POSNext Branch Manager", "POSNext Operations Manager"]]
        ]
    },
    {
        "dt": "Custom DocPerm",
        "filters": [
            ["role", "in", ["POSNext Cashier"]]
        ]
    }
]

# Installation
# ------------

# before_install = "ecs_posnext.install.before_install"
after_install = "ecs_posnext.install.after_install"
after_migrate = "ecs_posnext.install.after_migrate"

# Uninstallation
# ------------

before_uninstall = "ecs_posnext.uninstall.before_uninstall"
# after_uninstall = "ecs_posnext.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "ecs_posnext.utils.before_app_install"
# after_app_install = "ecs_posnext.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "ecs_posnext.utils.before_app_uninstall"
# after_app_uninstall = "ecs_posnext.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "ecs_posnext.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

permission_query_conditions = {
	"Delivery Assignment": "ecs_posnext.ecs_posnext.api.dispatcher.get_delivery_assignment_permission_conditions",
}

# Standard Queries
# ----------------
# Custom query for company-aware item filtering
standard_queries = {
	"Item": "ecs_posnext.validations.item_query"
}

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Sales Invoice": "ecs_posnext.overrides.sales_invoice.CustomSalesInvoice"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Item": {
		"validate": "ecs_posnext.validations.validate_item"
	},
	"Customer": {
		"after_insert": [
			"ecs_posnext.api.customers.auto_assign_loyalty_program",
			"ecs_posnext.realtime_events.emit_customer_event"
		],
		"on_update": "ecs_posnext.realtime_events.emit_customer_event",
		"on_trash": "ecs_posnext.realtime_events.emit_customer_event"
	},
	"Sales Invoice": {
		"validate": [
			"ecs_posnext.api.sales_invoice_hooks.validate",
			"ecs_posnext.api.wallet.validate_wallet_payment"
		],
		"before_cancel": [
			"ecs_posnext.api.business_day.block_closed_period_invoice_cancel",
			"ecs_posnext.api.sales_invoice_hooks.before_cancel"
		],
		"on_submit": [
			"ecs_posnext.realtime_events.emit_stock_update_event",
			"ecs_posnext.realtime_events.emit_order_changed_event",
			"ecs_posnext.api.wallet.process_loyalty_to_wallet",
			"ecs_posnext.api.sales_invoice_hooks.create_payment_entry_on_submit",
			"ecs_posnext.ecs_posnext.api.kds.on_sales_invoice_submit"
		],
		"on_cancel": [
			"ecs_posnext.realtime_events.emit_stock_update_event",
			"ecs_posnext.realtime_events.emit_order_changed_event",
			"ecs_posnext.api.sales_invoice_hooks.cancel_payment_entries_on_cancel",
			"ecs_posnext.ecs_posnext.api.kds.on_sales_invoice_cancel"
		],
		"after_insert": [
			"ecs_posnext.realtime_events.emit_invoice_created_event",
			"ecs_posnext.realtime_events.emit_order_changed_event",
		],
	},
	"POS Profile": {
		"on_update": "ecs_posnext.realtime_events.emit_pos_profile_updated_event"
	},
	"POS Opening Shift": {
		"on_submit": "ecs_posnext.api.cashier_shift.sync_cashier_shift_on_opening",
		"on_cancel": "ecs_posnext.api.cashier_shift.void_cashier_shift_on_opening_cancel"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"cron": {
		"*/15 * * * *": [
			"ecs_posnext.api.business_day_scheduler.process_business_days",
		],
	},
	"hourly": [
		"ecs_posnext.tasks.branding_monitor.monitor_branding_integrity",
	],
	"daily": [
		"ecs_posnext.tasks.cleanup_expired_promotions.cleanup_expired_promotions",
		"ecs_posnext.tasks.branding_monitor.validate_all_active_sessions",
	],
	"monthly": [
		"ecs_posnext.tasks.branding_monitor.reset_tampering_counter",
	],
}

# Testing
# -------

# before_tests = "ecs_posnext.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "ecs_posnext.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "ecs_posnext.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["ecs_posnext.utils.before_request"]
# after_request = ["ecs_posnext.utils.after_request"]

# Job Events
# ----------
# before_job = ["ecs_posnext.utils.before_job"]
# after_job = ["ecs_posnext.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"ecs_posnext.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }


website_route_rules = [{'from_route': '/pos/<path:app_path>', 'to_route': 'pos'},]
