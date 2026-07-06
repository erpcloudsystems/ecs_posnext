<template>
	<div class="flex flex-col h-full bg-gray-50 min-h-0">
		<!-- Breadcrumb (only when drilled into a sub-group) -->
		<div
			v-if="stack.length"
			class="flex items-center gap-1 px-2 sm:px-3 py-2 bg-white border-b border-gray-200 overflow-x-auto scrollbar-hide"
		>
			<button
				class="flex items-center gap-1 text-[11px] sm:text-xs font-medium text-blue-600 hover:text-blue-700 whitespace-nowrap"
				@click="goRoot"
			>
				<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
				</svg>
				<span>{{ __('All Groups') }}</span>
			</button>
			<template v-for="(node, i) in stack" :key="node.item_group">
				<span class="text-gray-300 text-xs">›</span>
				<button
					class="text-[11px] sm:text-xs font-medium whitespace-nowrap"
					:class="i === stack.length - 1 ? 'text-gray-700' : 'text-blue-600 hover:text-blue-700'"
					@click="goTo(i)"
				>
					{{ __(node.item_group) }}
				</button>
			</template>
		</div>

		<!-- Group cards -->
		<div class="flex-1 overflow-y-auto p-1.5 sm:p-3 min-h-0">
			<div
				v-if="currentNodes.length"
				class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-1.5 sm:gap-2"
			>
				<button
					v-for="node in currentNodes"
					:key="node.item_group"
					class="group relative flex flex-col items-center justify-center text-center bg-white border border-gray-200 rounded-lg p-2 sm:p-3 min-h-[72px] sm:min-h-[96px] hover:border-blue-400 hover:shadow-md active:bg-gray-50 cursor-pointer transition-[border-color,box-shadow] touch-manipulation"
					@click="onCardClick(node)"
				>
					<!-- chevron for parent groups -->
					<svg
						v-if="hasChildren(node)"
						class="absolute top-1 end-1 w-3.5 h-3.5 text-gray-300 group-hover:text-blue-400"
						fill="none" stroke="currentColor" viewBox="0 0 24 24"
					>
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
					</svg>

					<!-- icon: folder for groups, tag for leaves -->
					<div
						class="flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 rounded-lg"
						:class="hasChildren(node) ? 'bg-amber-50 text-amber-500' : 'bg-blue-50 text-blue-500'"
					>
						<svg v-if="hasChildren(node)" class="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z"/>
						</svg>
						<svg v-else class="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5a1.99 1.99 0 011.414.586l7 7a2 2 0 010 2.828l-5 5a2 2 0 01-2.828 0l-7-7A1.99 1.99 0 014 9V4a1 1 0 011-1z"/>
						</svg>
					</div>

					<span class="mt-1.5 sm:mt-2 text-[11px] sm:text-xs font-medium text-gray-800 leading-tight line-clamp-2">
						{{ __(node.item_group) }}
					</span>
					<span v-if="hasChildren(node)" class="mt-0.5 text-[9px] sm:text-[10px] text-gray-400">
						{{ __('{0} groups', [node.children.length]) }}
					</span>
				</button>
			</div>

			<!-- empty -->
			<div v-else class="flex flex-col items-center justify-center h-full text-center py-10">
				<svg class="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z"/>
				</svg>
				<p class="mt-2 text-xs font-medium text-gray-500">{{ __('No item groups configured for this POS Profile') }}</p>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, watch } from "vue"

const props = defineProps({
	groups: {
		type: Array,
		default: () => [],
	},
})

const emit = defineEmits(["select"])

// Stack of parent nodes drilled into; empty = top level.
const stack = ref([])

const currentNodes = computed(() =>
	stack.value.length
		? stack.value[stack.value.length - 1].children || []
		: props.groups,
)

function hasChildren(node) {
	return (
		!!node &&
		node.is_group &&
		Array.isArray(node.children) &&
		node.children.length > 0
	)
}

function onCardClick(node) {
	if (hasChildren(node)) {
		stack.value = [...stack.value, node]
	} else {
		emit("select", node.item_group)
	}
}

function goRoot() {
	stack.value = []
}

function goTo(index) {
	stack.value = stack.value.slice(0, index + 1)
}

// Reset to top level whenever the group set changes (e.g. profile switch).
watch(
	() => props.groups,
	() => {
		stack.value = []
	},
)
</script>
