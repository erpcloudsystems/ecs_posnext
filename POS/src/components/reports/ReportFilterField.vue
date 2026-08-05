<template>
	<div :style="{ minWidth: widthStyle }" class="flex-shrink-0">
		<label class="block text-xs font-medium text-gray-600 mb-1 truncate" :title="filter.label">
			{{ filter.label }}
			<span v-if="filter.reqd" class="text-red-500">*</span>
			<FeatherIcon v-if="isLocked" name="lock" class="w-3 h-3 inline-block align-text-bottom" />
		</label>

		<!-- Locked: fixed by the POS, e.g. a branch filter following the open shift -->
		<input
			v-if="isLocked"
			type="text"
			:value="lockedText"
			:title="lockedTitle"
			disabled
			readonly
			:class="[inputClass, 'bg-gray-100 text-gray-600 cursor-not-allowed']"
		/>

		<!-- Check -->
		<label
			v-else-if="filter.fieldtype === 'Check'"
			class="flex items-center gap-2 h-[38px] px-3 border border-gray-300 rounded-lg bg-white cursor-pointer"
		>
			<input
				type="checkbox"
				:checked="!!modelValue"
				@change="emitValue($event.target.checked ? 1 : 0)"
				class="rounded border-gray-300"
			/>
			<span class="text-sm text-gray-700">{{ modelValue ? __('Yes') : __('No') }}</span>
		</label>

		<!-- Date range: the report expects [from, to] -->
		<div v-else-if="filter.fieldtype === 'DateRange'" class="flex items-center gap-1">
			<input
				type="date"
				:value="rangeValue[0]"
				@change="emitRange(0, $event.target.value)"
				:class="inputClass"
			/>
			<input
				type="date"
				:value="rangeValue[1]"
				@change="emitRange(1, $event.target.value)"
				:class="inputClass"
			/>
		</div>

		<!-- Date / Datetime / Time -->
		<input
			v-else-if="dateInputType"
			:type="dateInputType"
			:value="modelValue || ''"
			@change="emitValue($event.target.value)"
			:class="inputClass"
		/>

		<!-- Select -->
		<select
			v-else-if="filter.fieldtype === 'Select'"
			:value="modelValue ?? ''"
			@change="emitValue($event.target.value)"
			:class="inputClass"
		>
			<option value="">{{ __('All') }}</option>
			<option v-for="option in filter.values || []" :key="option" :value="option">
				{{ __(option) }}
			</option>
		</select>

		<!-- Numbers -->
		<input
			v-else-if="isNumeric"
			type="number"
			:step="filter.fieldtype === 'Int' ? 1 : 'any'"
			:value="modelValue ?? ''"
			@input="emitValue($event.target.value === '' ? null : Number($event.target.value))"
			:class="inputClass"
		/>

		<!-- Link: searched against the server so long lists stay usable -->
		<div v-else-if="filter.fieldtype === 'Link'" @focusin="primeLinkOptions">
			<AutocompleteSelect
				:model-value="modelValue || ''"
				:options="linkOptions"
				:loading="searching"
				:placeholder="linkPlaceholder"
				@update:model-value="emitValue($event)"
				@search="searchLinkOptions"
			/>
		</div>

		<!-- MultiSelectList: chips, typed or picked -->
		<div v-else-if="filter.fieldtype === 'MultiSelectList'" class="relative">
			<div
				class="flex flex-wrap items-center gap-1 min-h-[38px] px-2 py-1 border border-gray-300 rounded-lg bg-white focus-within:ring-2 focus-within:ring-indigo-500"
			>
				<span
					v-for="entry in selectedList"
					:key="entry"
					class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 text-xs font-medium max-w-[160px]"
				>
					<span class="truncate">{{ entry }}</span>
					<button type="button" @click="removeEntry(entry)" class="hover:text-indigo-900">
						<FeatherIcon name="x" class="w-3 h-3" />
					</button>
				</span>
				<input
					v-model="multiSearch"
					type="text"
					:placeholder="selectedList.length ? '' : linkPlaceholder"
					class="flex-1 min-w-[80px] text-sm border-0 focus:outline-none focus:ring-0 p-1"
					@focus="openSuggestions"
					@input="onMultiInput"
					@keydown.enter.prevent="addTypedEntry"
					@keydown.backspace="onMultiBackspace"
					@blur="closeSuggestionsSoon"
				/>
			</div>

			<div
				v-if="showSuggestions && suggestions.length"
				class="absolute z-20 mt-1 w-full max-h-56 overflow-y-auto bg-white border border-gray-200 rounded-lg shadow-lg"
			>
				<button
					v-for="option in suggestions"
					:key="option.value"
					type="button"
					class="w-full text-start px-3 py-2 text-sm hover:bg-gray-50"
					@mousedown.prevent="addEntry(option.value)"
				>
					<span class="text-gray-800">{{ option.value }}</span>
					<span v-if="option.description" class="text-gray-400 ms-2 text-xs">
						{{ option.description }}
					</span>
				</button>
			</div>
		</div>

		<!-- Data and anything without a dedicated widget -->
		<input
			v-else
			type="text"
			:value="modelValue ?? ''"
			@input="emitValue($event.target.value)"
			:class="inputClass"
			:placeholder="filter.description || ''"
		/>
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"
import { computed, onMounted, ref } from "vue"
import AutocompleteSelect from "@/components/common/AutocompleteSelect.vue"
import { call } from "@/utils/apiWrapper"
import { logger } from "@/utils/logger"

const log = logger.create("ReportFilterField")

const props = defineProps({
	filter: {
		type: Object,
		required: true,
	},
	modelValue: {
		type: [String, Number, Boolean, Array],
		default: null,
	},
	/**
	 * All current filter values. A few reports resolve a Link's doctype from a
	 * sibling filter (General Ledger's Party follows Party Type), so the field
	 * needs to see the whole set, not just its own value.
	 */
	values: {
		type: Object,
		default: () => ({}),
	},
})

const emit = defineEmits(["update:modelValue"])

const inputClass =
	"w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"

const searching = ref(false)
const linkOptions = ref([])
const suggestions = ref([])
const showSuggestions = ref(false)
const multiSearch = ref("")
let suggestionTimer = null
let blurTimer = null
let primed = false

/**
 * A filter the server pinned: the value is not the cashier's to change.
 *
 * Shown rather than hidden so the figures are visibly scoped — a branch filter is
 * locked to the branch of the open shift, and the server re-applies it on every
 * run, so nothing depends on this staying read-only.
 */
const isLocked = computed(() => !!props.filter.read_only)

const lockedText = computed(() => {
	const value = props.modelValue
	if (Array.isArray(value)) return value.join(", ")
	if (props.filter.fieldtype === "Check") return value ? __("Yes") : __("No")
	return value ?? ""
})

const lockedTitle = computed(() =>
	__("{0} is set by your POS shift and cannot be changed", [props.filter.label]),
)

const isNumeric = computed(() =>
	["Int", "Float", "Currency", "Percent"].includes(props.filter.fieldtype),
)

const dateInputType = computed(() => {
	const map = { Date: "date", Datetime: "datetime-local", Time: "time" }
	return map[props.filter.fieldtype] || null
})

const widthStyle = computed(() => {
	if (props.filter.fieldtype === "DateRange") return "260px"
	if (props.filter.fieldtype === "Check") return "150px"
	return "180px"
})

/** The doctype to search, either declared or taken from a sibling filter. */
const lookupDoctype = computed(() => {
	if (props.filter.link_doctype) return props.filter.link_doctype
	if (props.filter.link_doctype_from) {
		return props.values?.[props.filter.link_doctype_from] || null
	}
	return null
})

const linkPlaceholder = computed(() => {
	if (lookupDoctype.value) return __("Search {0}...", [__(lookupDoctype.value)])
	if (props.filter.link_doctype_from) {
		return __("Select {0} first", [props.filter.link_doctype_from.replace(/_/g, " ")])
	}
	return __("Type and press Enter")
})

const rangeValue = computed(() => {
	const value = props.modelValue
	return Array.isArray(value) ? [value[0] || "", value[1] || ""] : ["", ""]
})

const selectedList = computed(() =>
	Array.isArray(props.modelValue) ? props.modelValue : props.modelValue ? [props.modelValue] : [],
)

function emitValue(value) {
	emit("update:modelValue", value)
}

function emitRange(index, value) {
	const next = [...rangeValue.value]
	next[index] = value
	emit("update:modelValue", next[0] || next[1] ? next : null)
}

// ---------------------------------------------------------------------------
// Link / MultiSelectList lookups
// ---------------------------------------------------------------------------

async function fetchOptions(txt) {
	const doctype = lookupDoctype.value
	if (!doctype) return []

	try {
		return await call("ecs_posnext.api.reports.search_filter_options", {
			doctype,
			txt: txt || "",
		})
	} catch (error) {
		log.error(`Lookup failed for ${doctype}:`, error)
		return []
	}
}

async function searchLinkOptions(txt) {
	searching.value = true
	try {
		const results = await fetchOptions(txt)
		const options = results.map((option) => ({
			value: option.value,
			label: option.value,
			subtitle: option.description,
		}))

		// A default value arrives before any search has run; keep it in the list so
		// the input shows it instead of looking empty
		if (props.modelValue && !options.some((option) => option.value === props.modelValue)) {
			options.unshift({ value: props.modelValue, label: props.modelValue })
		}
		linkOptions.value = options
	} finally {
		searching.value = false
	}
}

/** First focus loads the opening page of options; typing narrows it. */
function primeLinkOptions() {
	if (primed || searching.value) return
	primed = true
	searchLinkOptions("")
}

onMounted(() => {
	// Show a default value straight away — AutocompleteSelect renders the label of
	// the matching option, so an unlisted value would read as an empty field
	if (props.filter.fieldtype === "Link" && props.modelValue) {
		linkOptions.value = [{ value: props.modelValue, label: props.modelValue }]
	}
})

function openSuggestions() {
	showSuggestions.value = true
	if (props.filter.values?.length) {
		suggestions.value = props.filter.values.map((value) => ({ value, description: "" }))
	} else {
		loadSuggestions(multiSearch.value)
	}
}

function onMultiInput() {
	showSuggestions.value = true
	if (props.filter.values?.length) {
		const txt = multiSearch.value.toLowerCase()
		suggestions.value = props.filter.values
			.filter((value) => value.toLowerCase().includes(txt))
			.map((value) => ({ value, description: "" }))
		return
	}
	loadSuggestions(multiSearch.value)
}

function loadSuggestions(txt) {
	clearTimeout(suggestionTimer)
	suggestionTimer = setTimeout(async () => {
		suggestions.value = await fetchOptions(txt)
	}, 250)
}

function closeSuggestionsSoon() {
	// Deferred so a click on a suggestion still registers
	blurTimer = setTimeout(() => {
		showSuggestions.value = false
	}, 150)
}

function addEntry(value) {
	if (!value) return
	clearTimeout(blurTimer)
	if (!selectedList.value.includes(value)) {
		emit("update:modelValue", [...selectedList.value, value])
	}
	multiSearch.value = ""
	showSuggestions.value = false
}

function addTypedEntry() {
	const value = multiSearch.value.trim()
	if (value) addEntry(value)
}

function removeEntry(value) {
	emit(
		"update:modelValue",
		selectedList.value.filter((entry) => entry !== value),
	)
}

function onMultiBackspace() {
	if (multiSearch.value === "" && selectedList.value.length) {
		removeEntry(selectedList.value[selectedList.value.length - 1])
	}
}
</script>
