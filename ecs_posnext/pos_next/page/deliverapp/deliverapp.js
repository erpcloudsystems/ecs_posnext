frappe.pages['deliverapp'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Delivery Orders',
		single_column: true
	});

	this.page.$DeliverApp = new frappe.DeliverApp.deliverapp({ parent: this.page });
};
