<template>
	<div class="flex flex-col bg-gray-50" style="height: 100vh; max-height: 100vh">
		<!-- Header -->
		<div class="flex items-center gap-3 px-3 sm:px-4 py-2.5 sm:py-3 bg-white border-b border-gray-200">
			<button
				@click="router.push({ name: 'POSSale' })"
				class="flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs sm:text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 active:bg-blue-200 touch-manipulation"
				:aria-label="__('Back to POS')"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
				</svg>
				<span>{{ __('Back') }}</span>
			</button>
			<h1 class="text-sm sm:text-base font-semibold text-gray-900 truncate">{{ __('Build') }}</h1>
			<span class="text-xs text-gray-500 hidden sm:inline">{{ __('All products') }}</span>
		</div>

		<!-- Search + Group Filter -->
		<div class="px-3 sm:px-4 py-2 sm:py-3 bg-white border-b border-gray-200 flex items-center gap-2">
			<div class="flex-1 relative min-w-0">
				<div class="absolute inset-y-0 start-0 ps-3 flex items-center pointer-events-none">
					<svg class="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
				</div>
				<input
					v-model="searchTerm"
					type="text"
					:placeholder="__('Search products...')"
					class="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 ps-9 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					:aria-label="__('Search products')"
				/>
			</div>
			<select
				v-model="selectedGroup"
				class="text-sm border border-gray-300 rounded-lg px-2 py-2 max-w-[10rem] sm:max-w-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
				:aria-label="__('Filter by item group')"
			>
				<option :value="null">{{ __('All groups') }}</option>
				<option v-for="group in itemGroups" :key="group" :value="group">{{ __(group) }}</option>
			</select>
		</div>

		<!-- Product Grid -->
		<div class="flex-1 overflow-y-auto px-3 sm:px-4 py-3 sm:py-4 pb-20">
			<div v-if="loading && !products.length" class="flex items-center justify-center h-full text-gray-400 text-sm">
				{{ __('Loading products...') }}
			</div>
			<div v-else-if="!products.length" class="flex items-center justify-center h-full text-gray-400 text-sm">
				{{ __('No products found') }}
			</div>
			<div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2 sm:gap-3">
				<div
					v-for="item in products"
					:key="item.item_code"
					@click="openProduct(item)"
					class="bg-white rounded-lg border border-gray-200 p-2 sm:p-3 flex flex-col cursor-pointer hover:shadow-md hover:border-blue-300 transition-shadow touch-manipulation"
				>
					<div class="relative w-full aspect-square bg-gray-100 rounded-md mb-2 overflow-hidden">
						<LazyImage
							v-if="item.image"
							:src="item.image"
							:alt="item.item_name"
							container-class="relative w-full h-full"
							img-class="w-full h-full object-cover"
							root-margin="150px"
						>
							<template #error>
								<PlaceholderIcon />
							</template>
						</LazyImage>
						<div v-else class="w-full h-full flex items-center justify-center">
							<PlaceholderIcon />
						</div>
					</div>
					<div class="text-xs sm:text-sm font-medium text-gray-900 truncate" :title="item.item_name">
						{{ item.item_name }}
					</div>
					<div class="text-[10px] sm:text-xs text-gray-500 truncate">{{ __(item.item_group) }}</div>
					<div class="mt-1 text-xs sm:text-sm font-semibold text-gray-900">
						{{ formatCurrencyCode(item.price_list_rate, currency) }}
					</div>
				</div>
			</div>

			<!-- Load more -->
			<div v-if="hasMore" class="flex justify-center mt-4">
				<Button variant="outline" :loading="loadingMore" @click="loadMore">
					{{ __('Load more') }}
				</Button>
			</div>
		</div>

		<ReservationCartBar :currency="currency" />
	</div>
</template>

<script setup>
import { Button } from "frappe-ui"
import { computed, h, onMounted, ref, watch } from "vue"
import { useRouter } from "vue-router"
import LazyImage from "@/components/common/LazyImage.vue"
import ReservationCartBar from "@/components/build/ReservationCartBar.vue"
import { call } from "@/utils/apiWrapper"
import { formatCurrencyCode } from "@/utils/currency"

const router = useRouter()

const PAGE_SIZE = 40

const products = ref([])
const itemGroups = ref([])
const searchTerm = ref("")
const selectedGroup = ref(null)
const start = ref(0)
const totalCount = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const currency = ref("SAR")

const hasMore = computed(() => products.value.length < totalCount.value)

const PlaceholderIcon = () =>
	h(
		"svg",
		{
			class: "h-8 w-8 text-gray-300",
			fill: "none",
			stroke: "currentColor",
			viewBox: "0 0 24 24",
		},
		[
			h("path", {
				"stroke-linecap": "round",
				"stroke-linejoin": "round",
				"stroke-width": "2",
				d: "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z",
			}),
		],
	)

async function fetchProducts({ append = false } = {}) {
	if (append) {
		loadingMore.value = true
	} else {
		loading.value = true
		start.value = 0
	}

	try {
		const response = await call("ecs_posnext.api.items.get_all_products", {
			search_term: searchTerm.value || null,
			item_group: selectedGroup.value,
			start: start.value,
			limit: PAGE_SIZE,
		})
		const data = response?.message || response
		products.value = append ? [...products.value, ...(data.items || [])] : data.items || []
		totalCount.value = data.total_count || 0
		currency.value = data.currency || currency.value
	} finally {
		loading.value = false
		loadingMore.value = false
	}
}

function loadMore() {
	start.value += PAGE_SIZE
	fetchProducts({ append: true })
}

function openProduct(item) {
	router.push({ name: "BuildProductDetail", params: { item_code: item.item_code } })
}

async function loadItemGroups() {
	const response = await call("ecs_posnext.api.items.get_build_catalog_item_groups")
	itemGroups.value = response?.message || response || []
}

let searchDebounce = null
watch([searchTerm, selectedGroup], () => {
	clearTimeout(searchDebounce)
	searchDebounce = setTimeout(() => fetchProducts(), 300)
})

onMounted(() => {
	fetchProducts()
	loadItemGroups()
})
</script>
