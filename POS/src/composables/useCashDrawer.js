import { ref } from "vue"
import { useToast } from "@/composables/useToast"
import { logger } from "@/utils/logger"
import { openCashDrawer as qzOpenCashDrawer } from "@/utils/qzTray"

const log = logger.create("CashDrawer")

/**
 * Opening the drawer with no sale attached — to give change, to drop a float, to
 * settle a Daily Payment. The pulse goes to the receipt printer, so this needs
 * QZ Tray running on the till exactly as silent printing does.
 *
 * State lives at module scope so the header button, the F7 shortcut and anything
 * else that opens the drawer share one guard: the drawer takes about a second to
 * spring, and a second pulse while it is travelling does nothing but confuse the
 * cashier with a second toast.
 */
const opening = ref(false)

const REOPEN_COOLDOWN_MS = 1000
let lastOpenedAt = 0

export function useCashDrawer() {
	const { showSuccess, showError } = useToast()

	/**
	 * Kick the drawer open.
	 * @returns {Promise<boolean>} true when the pulse was sent
	 */
	async function openDrawer() {
		if (opening.value) return false
		if (Date.now() - lastOpenedAt < REOPEN_COOLDOWN_MS) return false

		opening.value = true
		try {
			await qzOpenCashDrawer()
			lastOpenedAt = Date.now()
			showSuccess(__("Cash drawer opened"))
			return true
		} catch (err) {
			const reason = err?.message || ""
			log.error("Could not open the cash drawer:", reason || err)
			showError(
				reason
					? __("Could not open the cash drawer: {0}", [reason])
					: __("Could not open the cash drawer"),
			)
			return false
		} finally {
			opening.value = false
		}
	}

	return {
		// State
		opening,

		// Actions
		openDrawer,
	}
}
