frappe.pages['item_manager'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Item Manager',
		single_column: true
	});

	// Get item_id from URL path: /app/item_manager/[item_id]
	const pathParts = window.location.pathname.split('/');
	const itemManagerIndex = pathParts.findIndex(p => p === 'item_manager');
	const item_id = itemManagerIndex >= 0 && pathParts.length > itemManagerIndex + 1 
		? decodeURIComponent(pathParts[itemManagerIndex + 1]) 
		: null;

	// Pass item_id to the app
	this.page.$ItemManager = new frappe.PosApp.ItemManagerApp(this.page, item_id);

	$('div.navbar-fixed-top').find('.container').css('padding', '0');

	$("head").append("<link href='/assets/posawesome/node_modules/vuetify/dist/vuetify.min.css' rel='stylesheet'>");
	$("head").append("<link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/@mdi/font@6.x/css/materialdesignicons.min.css'>");
	$("head").append("<link rel='stylesheet' href='https://fonts.googleapis.com/css?family=Roboto:100,300,400,500,700,900' />");
};
