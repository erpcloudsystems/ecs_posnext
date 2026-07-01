frappe.pages['item_manager'].on_page_load = function (wrapper) {
	const route = frappe.get_route();
	const item_id = route[1];

	const target = item_id
		? `/pos/item-manager/${encodeURIComponent(item_id)}?desk=1`
		: '/pos/item-manager?desk=1';

	window.location.href = target;
};
