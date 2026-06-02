frappe.pages['prepapp'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Preparing Orders',
		single_column: true
	});

	this.page.$PrepApp = new frappe.PrepApp.prepapp({ parent: this.page });
};
