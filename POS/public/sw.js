const CACHE_PREFIX = "posnext"
const STATIC_CACHE = `${CACHE_PREFIX}-static-v1`
const ASSET_CACHE = `${CACHE_PREFIX}-assets-v1`
const IMAGE_CACHE = `${CACHE_PREFIX}-images-v1`
const API_CACHE = `${CACHE_PREFIX}-api-v1`

const STATIC_ASSETS = [
	"offline.html",
	"manifest.webmanifest",
	"icon.svg",
	"icon-maskable.svg",
]

function scopedUrl(path) {
	return new URL(path, self.registration.scope).toString()
}

self.addEventListener("install", (event) => {
	event.waitUntil(
		caches
			.open(STATIC_CACHE)
			.then((cache) => cache.addAll(STATIC_ASSETS.map(scopedUrl)))
			.then(() => self.skipWaiting()),
	)
})

self.addEventListener("activate", (event) => {
	event.waitUntil(
		caches
			.keys()
			.then((keys) =>
				Promise.all(
					keys
						.filter((key) => key.startsWith(CACHE_PREFIX) && ![
							STATIC_CACHE,
							ASSET_CACHE,
							IMAGE_CACHE,
							API_CACHE,
						].includes(key))
						.map((key) => caches.delete(key)),
				),
			)
			.then(() => self.clients.claim()),
	)
})

async function cacheFirst(request, cacheName) {
	const cache = await caches.open(cacheName)
	const cached = await cache.match(request)
	if (cached) return cached

	const response = await fetch(request)
	if (response.ok) {
		cache.put(request, response.clone())
	}
	return response
}

async function staleWhileRevalidate(request, cacheName) {
	const cache = await caches.open(cacheName)
	const cached = await cache.match(request)
	const network = fetch(request).then((response) => {
		if (response.ok) {
			cache.put(request, response.clone())
		}
		return response
	})
	return cached || network
}

async function networkFirst(request, cacheName) {
	const cache = await caches.open(cacheName)
	try {
		const response = await fetch(request)
		if (response.ok) {
			cache.put(request, response.clone())
		}
		return response
	} catch (error) {
		const cached = await cache.match(request)
		if (cached) return cached
		throw error
	}
}

self.addEventListener("fetch", (event) => {
	const { request } = event
	if (request.method !== "GET") return

	const url = new URL(request.url)

	if (url.pathname.startsWith("/assets/ecs_posnext/pos/")) {
		event.respondWith(cacheFirst(request, ASSET_CACHE))
		return
	}

	if (/^\/files\/.*\.(jpg|jpeg|png|gif|webp|svg)$/i.test(url.pathname)) {
		event.respondWith(staleWhileRevalidate(request, IMAGE_CACHE))
		return
	}

	if (url.pathname.startsWith("/api/")) {
		event.respondWith(networkFirst(request, API_CACHE))
	}
})
