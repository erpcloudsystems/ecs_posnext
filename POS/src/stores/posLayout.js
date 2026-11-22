// Per-user custom order of the POS item grid and item group tabs
// (saved on the server per user + POS Profile, see ecs_posnext.api.pos_layout).
import { defineStore } from "pinia"
import { ref } from "vue"
import { call } from "@/utils/apiWrapper"

export const ALL_ITEMS_KEY = "__all__"
const SAVE_DELAY_MS = 600

export const usePOSLayoutStore = defineStore("posLayout", () => {
	const profile = ref(null)
	const layout = ref({ groups: [], items: {} })
	const arrangeMode = ref(false)
	const saving = ref(false)
	const saveError = ref(null)
	let saveTimer = null

	async function load(posProfile) {
		profile.value = posProfile || null
		layout.value = { groups: [], items: {} }
		if (!posProfile) return
		try {
			const res = await call("ecs_posnext.api.pos_layout.get_pos_layout", { pos_profile: posProfile })
			const data = res?.message || res
			if (profile.value === posProfile && data) {
				layout.value = { groups: data.groups || [], items: data.items || {} }
			}
		} catch (e) {
			console.warn("Could not load POS layout", e)
		}
	}

	function scheduleSave() {
		clearTimeout(saveTimer)
		saveTimer = setTimeout(save, SAVE_DELAY_MS)
	}

	async function save() {
		if (!profile.value) return
		saving.value = true
		saveError.value = null
		try {
			await call("ecs_posnext.api.pos_layout.save_pos_layout", {
				pos_profile: profile.value,
				layout: JSON.stringify(layout.value),
			})
		} catch (e) {
			saveError.value = e
			console.error("Could not save POS layout", e)
		} finally {
			saving.value = false
		}
	}

	async function reset() {
		clearTimeout(saveTimer)
		layout.value = { groups: [], items: {} }
		if (!profile.value) return
		try {
			await call("ecs_posnext.api.pos_layout.reset_pos_layout", { pos_profile: profile.value })
		} catch (e) {
			saveError.value = e
		}
	}

	/** Order `list` by the saved names (from getName); unknown entries keep their order after them. */
	function applyOrder(list, savedNames, getName) {
		if (!savedNames?.length || !list?.length) return list
		const rank = new Map(savedNames.map((n, i) => [n, i]))
		return list
			.map((entry, i) => ({ entry, i, r: rank.has(getName(entry)) ? rank.get(getName(entry)) : Infinity }))
			.sort((a, b) => (a.r === b.r ? a.i - b.i : a.r - b.r))
			.map((x) => x.entry)
	}

	function orderGroups(groups) {
		return applyOrder(groups, layout.value.groups, (g) => g.item_group)
	}

	function orderItems(items, groupKey) {
		return applyOrder(items, layout.value.items[groupKey || ALL_ITEMS_KEY], (i) => i.item_code)
	}

	/** Move entry at `from` to `to` in the currently displayed `names`, and save that order. */
	function moveGroup(names, from, to) {
		const next = move(names, from, to)
		if (!next) return
		layout.value = { ...layout.value, groups: next }
		scheduleSave()
	}

	function moveItem(groupKey, codes, from, to) {
		const next = move(codes, from, to)
		if (!next) return
		layout.value = {
			...layout.value,
			items: { ...layout.value.items, [groupKey || ALL_ITEMS_KEY]: mergeOrder(next, layout.value.items[groupKey || ALL_ITEMS_KEY]) },
		}
		scheduleSave()
	}

	return {
		profile,
		layout,
		arrangeMode,
		saving,
		saveError,
		load,
		reset,
		orderGroups,
		orderItems,
		moveGroup,
		moveItem,
	}
})

function move(list, from, to) {
	if (from === to || from < 0 || to < 0 || from >= list.length || to >= list.length) return null
	const next = [...list]
	const [x] = next.splice(from, 1)
	next.splice(to, 0, x)
	return next
}

/**
 * The grid shows one page at a time: keep the saved order of items that are not
 * on the current page (appended after the visible ones), so arranging page 1
 * doesn't wipe what was arranged for items elsewhere.
 */
function mergeOrder(visible, saved) {
	const seen = new Set(visible)
	return [...visible, ...(saved || []).filter((c) => !seen.has(c))]
}
