<template>
	<!-- Icon-Only Sidebar - Hidden on Mobile, Visible on Desktop -->
	<div class="hidden lg:flex w-16 flex-shrink-0 bg-white border-e border-gray-200 flex-col items-center py-4 flex flex-col gap-2">
		<!-- Promotions (hidden per request: set v-if back to true / remove to restore) -->
		<button
			v-if="false"
			@click="handleMenuClick('promotions')"
			:class="[
				'w-12 h-12 rounded-lg flex items-center justify-center transition-all relative group',
				activeMenu === 'promotions'
					? 'bg-green-100 text-green-600'
					: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
			]"
			:title="__('Promotions')"
		>
			<FeatherIcon name="tag" class="w-5 h-5" />
			<div class="absolute start-full ms-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
				{{ __('Promotions') }}
			</div>
		</button>

		<!-- Products / Stock (hidden per request: set v-if back to true / remove to restore) -->
		<button
			v-if="false"
			@click="handleMenuClick('products')"
			:class="[
				'w-12 h-12 rounded-lg flex items-center justify-center transition-all relative group',
				activeMenu === 'products'
					? 'bg-purple-100 text-purple-600'
					: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
			]"
			:title="__('Products')"
		>
			<FeatherIcon name="package" class="w-5 h-5" />
			<div class="absolute start-full ms-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
				{{ __('Products') }}
			</div>
		</button>

		<!-- Invoices -->
		<button
			@click="handleMenuClick('invoices')"
			:class="[
				'w-12 h-12 rounded-lg flex items-center justify-center transition-all relative group',
				activeMenu === 'invoices'
					? 'bg-indigo-100 text-indigo-600'
					: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
			]"
			:title="__('Invoice Management')"
		>
			<FeatherIcon name="file-text" class="w-5 h-5" />
			<div class="absolute start-full ms-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
				{{ __('Invoice Management') }}
			</div>
		</button>

		<!-- Daily Payment (hidden per request: set v-if back to true / remove to restore) -->
		<button
			v-if="false"
			@click="handleMenuClick('daily-payment')"
			:class="[
				'w-12 h-12 rounded-lg flex items-center justify-center transition-all relative group',
				activeMenu === 'daily-payment'
					? 'bg-emerald-100 text-emerald-600'
					: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
			]"
			:title="__('Daily Payment')"
		>
			<FeatherIcon name="dollar-sign" class="w-5 h-5" />
			<div class="absolute start-full ms-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
				{{ __('Daily Payment') }}
			</div>
		</button>

		<!-- Spacer to push settings to bottom -->
		<div class="flex-1"></div>

		<!-- Divider -->
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"
import { ref } from "vue"

const emit = defineEmits(["menu-clicked"])

const activeMenu = ref("")

function handleMenuClick(menuItem) {
	activeMenu.value = menuItem
	emit("menu-clicked", menuItem)
}
</script>
