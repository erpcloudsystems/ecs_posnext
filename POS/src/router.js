import { shiftState } from "@/composables/useShift"
import { userResource } from "@/data/user"
import { createRouter, createWebHistory } from "vue-router"
import { session } from "./data/session"

const routes = [
	{
		path: "/",
		name: "POSSale",
		component: () => import("@/pages/POSSale.vue"),
	},
	{
		name: "Login",
		path: "/account/login",
		component: () => import("@/pages/Login.vue"),
	},
	{
		name: "ItemManager",
		path: "/item-manager/:itemId?",
		component: () => import("@/pages/ItemManager.vue"),
	},
	{
		name: "NewProductEditor",
		path: "/product-editor/:itemId?",
		component: () => import("@/pages/NewProductEditor.vue"),
	},
	{
		name: "AllOrders",
		path: "/all-orders",
		component: () => import("@/pages/AllOrders.vue"),
	},
	{
		name: "CompleteOrders",
		path: "/complete-orders",
		component: () => import("@/pages/CompleteOrders.vue"),
	},
	{
		name: "NeedMyAction",
		path: "/need-my-action",
		component: () => import("@/pages/NeedMyAction.vue"),
	},
	{
		name: "Complaints",
		path: "/complaints",
		component: () => import("@/pages/Complaints.vue"),
	},
	{
		name: "CashManagement",
		path: "/cash-management",
		component: () => import("@/pages/CashManagement.vue"),
	},
	{
		name: "Dispatcher",
		path: "/dispatcher",
		component: () => import("@/pages/Dispatcher.vue"),
	},
	{
		name: "LiveOrders",
		path: "/live-orders",
		component: () => import("@/pages/LiveOrders.vue"),
	},
	{
		name: "KDSStations",
		path: "/kds/stations",
		component: () => import("@/pages/KDSStations.vue"),
	},
	{
		name: "KDSAssembly",
		path: "/kds/assembly",
		component: () => import("@/pages/KDSAssembly.vue"),
	},
	{
		name: "KDSStation",
		path: "/kds/station/:station",
		component: () => import("@/pages/KDSStation.vue"),
	},
	{
		name: "KitchenTotals",
		path: "/kds/totals",
		component: () => import("@/pages/KitchenTotals.vue"),
	},
	// Catch-all route
	{
		path: "/:pathMatch(.*)*",
		redirect: "/",
	},
]

const router = createRouter({
	history: createWebHistory("/pos"),
	routes,
})

router.beforeEach((to, from, next) => {
	// Check authentication status (session.user is already set in main.js before app mount)
	const isLoggedIn = session.isLoggedIn

	// Only log during development
	if (import.meta.env.DEV) {
		console.log(
			`[Router] ${to.name} (from: ${from.name || "initial"}), auth: ${isLoggedIn}`,
		)
	}

	// Redirect logic
	if (to.name === "Login" && isLoggedIn) {
		next({ name: "POSSale" })
	} else if (to.name !== "Login" && !isLoggedIn) {
		next({ name: "Login" })
	} else {
		next()
	}
})

// Restrict Cashier role from accessing Need My Action page
router.beforeEach((to, from, next) => {
	if (to.name === "NeedMyAction") {
		// Use bootstrap store (Pinia must be active at this point since main.js installs it before router)
		try {
			const { useBootstrapStore } = require("@/stores/bootstrap")
			const bs = useBootstrapStore()
			if (bs.hasRole("Cashier")) return next({ name: "POSSale" })
		} catch {
			// Store not ready yet — allow navigation; ManagementSlider already hides the link
		}
	}
	// Global Cash Management is only for Branch Managers and System Managers.
	if (to.name === "CashManagement") {
		try {
			const { useBootstrapStore } = require("@/stores/bootstrap")
			const bs = useBootstrapStore()
			if (!bs.hasRole("Bransh Manager") && !bs.hasRole("System Manager")) {
				return next({ name: "POSSale" })
			}
		} catch {
			// Store not ready — allow; the backend still enforces access.
		}
	}
	next()
})

export default router
