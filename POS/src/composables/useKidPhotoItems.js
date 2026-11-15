import { ref } from "vue"
import { call } from "@/utils/apiWrapper"

// Shared (module-level) so every component sees the same lists, loaded once.
// ticketItems: items with Ticket Settings -> show the kid photo button.
// photoRequired: membership ticket items -> a photo per ticket is mandatory
// (mirrors ecs_posnext.api.kid_photos._photo_required_item_codes).
const ticketItems = ref(new Set())
const photoRequired = ref(new Set())
let loading = null

function load() {
	if (!loading) {
		loading = call("ecs_posnext.api.kid_photos.get_kid_photo_items")
			.then((res) => {
				const data = res?.message || res || {}
				ticketItems.value = new Set(data.ticket_items || [])
				photoRequired.value = new Set(data.photo_required || [])
			})
			.catch((e) => {
				loading = null // allow a retry next time
				console.warn("Could not load kid photo items", e)
			})
	}
	return loading
}

function ticketCount(item) {
	return Math.max(1, Math.floor(Number(item?.quantity || item?.qty || 1)))
}

function photoCount(item) {
	return (item?.kid_photos || []).filter(Boolean).length
}

function isPhotoRequired(item) {
	return !!item && !item.posa_is_offer && photoRequired.value.has(item.item_code)
}

/** Cart rows of membership items that still miss one or more kid photos. */
function rowsMissingPhotos(items) {
	return (items || []).filter((i) => isPhotoRequired(i) && photoCount(i) < ticketCount(i))
}

export function useKidPhotoItems() {
	return { ticketItems, photoRequired, load, ticketCount, photoCount, isPhotoRequired, rowsMissingPhotos }
}
