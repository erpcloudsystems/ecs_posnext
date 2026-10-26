import { ref } from "vue"
import { call } from "frappe-ui"

// Table Number name -> no, shared by every component that displays tables
const tableNoByName = ref({})
let loadPromise = null

function loadTables() {
	if (!loadPromise) {
		loadPromise = call("frappe.client.get_list", {
			doctype: "Table Number",
			fields: ["name", "no"],
			limit_page_length: 0,
		})
			.then((rows) => {
				tableNoByName.value = Object.fromEntries((rows || []).map((t) => [t.name, t.no]))
			})
			.catch((error) => {
				console.error("Failed to load table numbers:", error)
				loadPromise = null
			})
	}
	return loadPromise
}

/**
 * Display table numbers (Table Number.no) instead of document names, which
 * are random hashes for tables created after numbers became unique per branch.
 */
export function useTableLabels() {
	loadTables()

	function tableLabel(name) {
		return tableNoByName.value[name] || name
	}

	return { tableLabel }
}
