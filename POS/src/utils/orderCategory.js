// Single source of truth for the 6 order-type categories used across the
// KDS board, the Dispatch Desk, and the Sales Invoice print format.
//
// Delivery orders are split by how they are paid:
//   • outstanding > 0 + card  → VOD (visa on delivery)
//   • outstanding > 0 + cash  → COD (cash on delivery)
//   • outstanding == 0        → PAID (prepaid, any method)

export const ORDER_CATEGORY_META = {
	talabat: { key: "talabat", labelEn: "TALABAT",           labelAr: "طلبات",           color: "#f97316", emoji: "🛵" },
	dinein:  { key: "dinein",  labelEn: "DINE IN",           labelAr: "داين إن",          color: "#7c3aed", emoji: "🍽️" },
	cod:     { key: "cod",     labelEn: "CASH ON DELIVERY",  labelAr: "كاش عند الاستلام",  color: "#16a34a", emoji: "💵" },
	vod:     { key: "vod",     labelEn: "VISA ON DELIVERY",  labelAr: "فيزا عند الاستلام", color: "#2563eb", emoji: "💳" },
	pickup:  { key: "pickup",  labelEn: "PICK UP",           labelAr: "استلام من الفرع",   color: "#eab308", emoji: "🛍️" },
	paid:    { key: "paid",    labelEn: "PAID",              labelAr: "مدفوع",            color: "#14b8a6", emoji: "✅" },
}

// Field names differ per surface, so callers pass a normalized object:
//   { order_type, payment_type, outstanding }
export function orderCategoryKey({ order_type, payment_type, outstanding } = {}) {
	const ot = (order_type || "").toLowerCase().replace(/[\s_-]/g, "")
	const pt = (payment_type || "").toLowerCase()
	if (ot.includes("talabat")) return "talabat"
	if (ot.includes("dine")) return "dinein"
	if (ot.includes("pickup") || ot.includes("takeaway") || ot.includes("take")) return "pickup"
	// Delivery — split by payment
	if (Number(outstanding) > 0) {
		if (pt.includes("credit") || pt.includes("card") || pt.includes("visa")) return "vod"
		return "cod"
	}
	return "paid"
}

export function orderCategory(order) {
	return ORDER_CATEGORY_META[orderCategoryKey(order)]
}
