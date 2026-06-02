frappe.pages['packapp'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Packing Orders',
		single_column: true
	});

	this.page.$PackApp = new frappe.PackApp.packapp({ parent: this.page });
};
