<template>
	<ul v-if="list.length" class="space-y-0.5" :class="level > 0 ? ['ms-3 border-s ps-2', dark ? 'border-gray-600' : 'border-gray-300'] : ''">
		<li v-for="(comp, i) in list" :key="i" class="text-xs leading-tight">
			<div :class="dark ? 'text-gray-300' : 'text-gray-700'">
				<span v-if="comp.section" :class="dark ? 'text-gray-500' : 'text-gray-400'">{{ comp.section }}: </span>
				<span class="font-medium">{{ comp.item_name || comp.item_code }}</span>
				<span v-if="(comp.quantity || 1) > 1" :class="dark ? 'text-yellow-300' : 'text-gray-500'"> ×{{ comp.quantity }}</span>
			</div>
			<div v-if="attributeText(comp)" :class="dark ? 'text-sky-300' : 'text-sky-700'">{{ attributeText(comp) }}</div>
			<div v-if="comp.selected_addons?.length" :class="dark ? 'text-emerald-300' : 'text-emerald-700'">
				+ {{ comp.selected_addons.map((a) => a.item_name || a.item_code).join(", ") }}
			</div>
			<div v-for="(ri, rix) in comp.removed_ingredient_names || []" :key="'r' + rix" class="text-red-500 line-through">✕ {{ ri }}</div>
			<div v-if="comp.notes" :class="dark ? 'text-amber-300' : 'text-amber-700'">📝 {{ comp.notes }}</div>
			<!-- A nested combo's own picks -->
			<ComboComponentsTree v-if="comp.components?.length" :components="comp.components" :level="level + 1" :dark="dark" />
		</li>
	</ul>
</template>

<script setup>
import { computed } from "vue"

defineOptions({ name: "ComboComponentsTree" })

const props = defineProps({
	// Array, or the JSON string stored in Sales Invoice Item.custom_selected_components
	components: { type: [Array, String], default: () => [] },
	level: { type: Number, default: 0 },
	dark: { type: Boolean, default: false },
})

const list = computed(() => {
	let value = props.components
	if (typeof value === "string") {
		try {
			value = value ? JSON.parse(value) : []
		} catch (_) {
			value = []
		}
	}
	// Fixed items are kitchen/stock only; the cashier-facing UI never lists them
	return Array.isArray(value) ? value.filter((c) => c && !c.is_fixed) : []
})

function attributeText(comp) {
	const attrs = Array.isArray(comp.attributes) ? comp.attributes : []
	return attrs
		.filter((a) => a && a.value)
		.map((a) => `${a.attribute}: ${a.value}`)
		.join(" · ")
}
</script>
