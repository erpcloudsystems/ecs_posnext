import { call } from "@/utils/apiWrapper"
import { ref } from "vue"

/** Reactive map of Table Number docname -> display number ("no") */
export const tableNoMap = ref({})

let loadPromise = null

/** Load the Table Number list once per page load; safe to call repeatedly */
export function loadTableNames() {
	if (!loadPromise) {
		loadPromise = call("frappe.client.get_list", {
			doctype: "Table Number",
			fields: ["name", "no"],
			limit_page_length: 0,
		})
			.then((rows) => {
				const map = {}
				for (const t of rows || []) {
					map[t.name] = t.no || t.name
				}
				tableNoMap.value = map
			})
			.catch((error) => {
				console.error("Error loading table names:", error)
				loadPromise = null
			})
	}
	return loadPromise
}

/** Resolve a Table Number docname to its display number, falling back to the docname */
export function getTableNo(tableName) {
	return tableNoMap.value[tableName] || tableName
}
