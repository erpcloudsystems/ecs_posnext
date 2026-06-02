frappe.pages['pendingapp'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Pending Orders',
		single_column: true
	});

	this.page.$PendingApp = new frappe.PendingApp.pendingapp({ parent: this.page });
};
