import { shiftState } from "@/composables/useShift"
import { userResource } from "@/data/user"
import { createRouter, createWebHistory } from "vue-router"
import { call } from "@/utils/apiWrapper"
import { session } from "./data/session"

const routes = [
	{
		path: "/",
		name: "POSSale",
		component: () => import("@/pages/POSSale.vue"),
	},
	{
		name: "Build",
		path: "/build",
		component: () => import("@/pages/Build.vue"),
		meta: { requiresRole: true },
	},
	{
		name: "BuildProductDetail",
		path: "/build/:item_code",
		component: () => import("@/pages/BuildProductDetail.vue"),
		props: true,
		meta: { requiresRole: true },
	},
	{
		name: "Login",
		path: "/account/login",
		component: () => import("@/pages/Login.vue"),
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

// Keyed by session.user so a logout/login as a different user re-checks access
let buildAccessCache = { user: undefined, allowed: false }

router.beforeEach(async (to, from, next) => {
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
	} else if (to.meta.requiresRole) {
		if (buildAccessCache.user !== session.user) {
			let allowed = false
			try {
				allowed = await call("ecs_posnext.api.items.has_build_access")
			} catch {
				allowed = false
			}
			buildAccessCache = { user: session.user, allowed }
		}
		next(buildAccessCache.allowed ? undefined : { name: "POSSale" })
	} else {
		next()
	}
})

export default router
