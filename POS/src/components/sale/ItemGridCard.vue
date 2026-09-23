<template>
	<div
		class="group relative bg-white border border-gray-200 rounded-lg p-1 sm:p-1.5 touch-manipulation transition-[border-color,box-shadow] duration-100 cursor-pointer hover:border-blue-400 hover:shadow-md"
	>
		<!-- Stock Badge - Tap to select, long press to view warehouse availability -->
		<div
			v-if="(item.is_stock_item || item.is_bundle) && !item.has_variants"
			@pointerdown="emit('long-press-start', item)"
			@pointerup="emit('long-press-end')"
			@pointercancel="emit('long-press-cancel')"
			@pointerleave="emit('long-press-cancel')"
			:class="[
				'absolute -top-1.5 -end-1.5 sm:-top-2 sm:-end-2 rounded-md shadow-lg z-10',
				'px-2 sm:px-2.5 py-1 sm:py-1 text-[10px] sm:text-xs font-bold',
				'border-2 border-white cursor-pointer select-none',
				'hover:scale-110 hover:shadow-xl transition-all duration-200',
				stockStatus.color,
				stockStatus.textColor
			]"
			:title="__('Check availability in other warehouses')"
		>
			{{ Math.floor(stockQty) }}
		</div>

		<!-- Item Image -->
		<div class="relative w-8 h-8 sm:w-8 sm:h-8 mx-auto bg-gray-100 rounded-md mb-1.5 sm:mb-1.5 overflow-hidden">
			<!-- Image with conditional blur on hover -->
			<div :class="[
				'w-full h-full transition-all duration-300',
				(item.is_stock_item || item.is_bundle) && stockQty <= 0 ? 'group-hover:blur-sm group-hover:brightness-75' : ''
			]">
				<LazyImage
					v-if="item.image"
					:src="item.image"
					:alt="item.item_name"
					container-class="relative w-full h-full"
					img-class="w-full h-full object-cover"
					root-margin="100px"
				>
					<template #error>
						<svg class="h-8 w-8 sm:h-10 sm:w-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
						</svg>
					</template>
				</LazyImage>
				<div v-else class="w-full h-full flex items-center justify-center">
					<svg class="h-8 w-8 sm:h-10 sm:w-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
					</svg>
				</div>
			</div>

			<!-- Info Icon Overlay - Tap to select, long press to show warehouse availability -->
			<div
				v-if="(item.is_stock_item || item.is_bundle) && stockQty <= 0"
				@pointerdown="emit('long-press-start', item)"
				@pointerup="emit('long-press-end')"
				@pointercancel="emit('long-press-cancel')"
				@pointerleave="emit('long-press-cancel')"
				class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-10 cursor-pointer select-none"
				:title="__('Check availability in other warehouses')"
			>
				<div class="p-2.5 bg-white/80 backdrop-blur-sm rounded-full pointer-events-none">
					<svg class="w-6 h-6 sm:w-7 sm:h-7 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
					</svg>
				</div>
			</div>
		</div>

		<!-- Item Details -->
		<div class="min-w-0">
			<h3 class="text-[12px] sm:text-xl font-semibold text-gray-900 truncate mb-1 leading-tight">
				{{ item.item_name }}
			</h3>
			<p class="text-base sm:text-[10px] text-gray-500 leading-tight">
				<span class="font-semibold text-blue-600">{{ formatCurrency(item.rate || item.price_list_rate || 0) }}</span>
				<span class="text-gray-400">/ {{ item.uom || item.stock_uom || __('Nos', null, 'UOM') }}</span>
			</p>
		</div>
	</div>
</template>

<script setup>
import LazyImage from "@/components/common/LazyImage.vue"
import { useStock } from "@/composables/useStock"
import { computed } from "vue"

// Item card for the items grid. Click/touch listeners set by the parent fall
// through to the root element; stock badge long-press is emitted.
const props = defineProps({
	item: { type: Object, required: true },
	formatCurrency: { type: Function, required: true },
})

const emit = defineEmits(["long-press-start", "long-press-end", "long-press-cancel"])

const { getStockStatus } = useStock()

const stockQty = computed(() => props.item.actual_qty ?? props.item.stock_qty ?? 0)
const stockStatus = computed(() => getStockStatus(stockQty.value))
</script>
