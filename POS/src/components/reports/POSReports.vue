<template>
	<Transition name="fade">
		<div
			v-if="show"
			class="fixed inset-0 bg-black bg-opacity-50 z-[300]"
			@click.self="handleClose"
		>
			<div class="fixed inset-0 flex items-center justify-center p-2 sm:p-4">
				<div class="w-full max-w-7xl bg-white rounded-xl shadow-2xl overflow-hidden flex flex-col h-[95vh]">

					<!-- Header -->
					<div class="flex items-center justify-between px-4 sm:px-6 py-4 border-b bg-gradient-to-r from-indigo-50 to-sky-50 flex-shrink-0">
						<div class="flex items-center gap-3 min-w-0">
							<button
								v-if="selectedReport"
								@click="backToList"
								class="p-2 hover:bg-white/60 rounded-lg transition-colors flex-shrink-0"
								:title="__('Back to reports')"
							>
								<FeatherIcon name="arrow-left" class="w-5 h-5 text-gray-600 rtl:rotate-180" />
							</button>
							<div v-else class="p-2 bg-indigo-100 rounded-lg flex-shrink-0">
								<FeatherIcon name="pie-chart" class="w-6 h-6 text-indigo-600" />
							</div>
							<div class="min-w-0">
								<h2 class="text-lg sm:text-xl font-bold text-gray-900 truncate">
									{{ selectedReport ? definitionLabel : __('Reports') }}
								</h2>
								<p class="text-xs sm:text-sm text-gray-600 mt-0.5 truncate">
									{{ headerSubtitle }}
								</p>
							</div>
						</div>
						<button @click="handleClose" class="p-2 hover:bg-white/60 rounded-lg transition-colors flex-shrink-0">
							<FeatherIcon name="x" class="w-5 h-5 text-gray-600" />
						</button>
					</div>

					<!-- ============ Report picker ============ -->
					<template v-if="!selectedReport">
						<div class="px-4 sm:px-6 py-3 border-b bg-white flex items-center gap-3 flex-shrink-0">
							<div class="relative flex-1 max-w-sm">
								<FeatherIcon
									name="search"
									class="w-4 h-4 text-gray-400 absolute top-1/2 -translate-y-1/2 start-3"
								/>
								<input
									v-model="reportSearch"
									type="text"
									:placeholder="__('Search reports...')"
									class="w-full ps-9 pe-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
								/>
							</div>
							<button
								@click="loadReports"
								:disabled="loadingReports"
								class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-60"
							>
								<FeatherIcon name="refresh-cw" class="w-4 h-4" :class="{ 'animate-spin': loadingReports }" />
								<span class="hidden sm:inline">{{ __('Refresh') }}</span>
							</button>
						</div>

						<div class="flex-1 overflow-y-auto p-4 sm:p-6 bg-gray-50">
							<div v-if="loadingReports" class="flex flex-col items-center justify-center py-16">
								<div class="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-500 mb-3"></div>
								<p class="text-sm font-medium text-gray-600">{{ __('Loading reports...') }}</p>
							</div>

							<div v-else-if="!reports.length" class="text-center py-16">
								<FeatherIcon name="inbox" class="w-10 h-10 text-gray-300 mx-auto mb-3" />
								<p class="text-sm font-medium text-gray-600">{{ __('No reports available') }}</p>
								<p class="text-xs text-gray-500 mt-1 max-w-md mx-auto">
									{{ __('Add the reports you need in POS Report Settings. Reports you are not permitted to run are not listed.') }}
								</p>
							</div>

							<div v-else-if="!filteredReports.length" class="text-center py-16 text-sm text-gray-500">
								{{ __('No reports match "{0}"', [reportSearch]) }}
							</div>

							<div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
								<button
									v-for="report in filteredReports"
									:key="report.report"
									@click="openReport(report)"
									class="flex items-center gap-3 p-4 bg-white rounded-xl border border-gray-200 shadow-sm hover:border-indigo-300 hover:shadow-md transition-all text-start"
								>
									<div class="p-2.5 bg-indigo-50 rounded-lg flex-shrink-0">
										<FeatherIcon :name="report.icon || 'bar-chart-2'" class="w-5 h-5 text-indigo-600" />
									</div>
									<div class="min-w-0">
										<div class="text-sm font-semibold text-gray-900 truncate">{{ report.label }}</div>
										<div class="text-xs text-gray-500 truncate">
											{{ report.ref_doctype ? __(report.ref_doctype) : __(report.report_type) }}
										</div>
									</div>
								</button>
							</div>
						</div>
					</template>

					<!-- ============ Report viewer ============ -->
					<template v-else>
						<!-- Filters -->
						<div v-if="visibleFilters.length" class="border-b bg-white flex-shrink-0">
							<div class="px-4 sm:px-6 py-3 flex flex-wrap items-end gap-3">
								<ReportFilterField
									v-for="filter in visibleFilters"
									:key="filter.fieldname"
									:filter="filter"
									:values="filterValues"
									v-model="filterValues[filter.fieldname]"
								/>
							</div>
						</div>

						<!-- Toolbar -->
						<div class="px-4 sm:px-6 py-3 border-b bg-gray-50 flex flex-wrap items-center gap-2 flex-shrink-0">
							<button
								@click="runReport"
								:disabled="running"
								class="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-semibold disabled:opacity-60"
							>
								<FeatherIcon name="refresh-cw" class="w-4 h-4" :class="{ 'animate-spin': running }" />
								{{ running ? __('Running...') : __('Refresh') }}
							</button>

							<div class="flex-1"></div>

							<span v-if="rows.length" class="text-xs text-gray-500 me-1">
								{{ __('{0} rows', [rows.length]) }}
							</span>

							<button
								v-if="definition?.can_export"
								@click="handleExport('Excel')"
								:disabled="!rows.length || exporting"
								class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
								:title="__('Export as Excel')"
							>
								<FeatherIcon name="download" class="w-4 h-4" />
								<span class="hidden sm:inline">{{ __('Excel') }}</span>
							</button>

							<button
								v-if="definition?.can_export"
								@click="handleExport('CSV')"
								:disabled="!rows.length || exporting"
								class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
								:title="__('Export as CSV')"
							>
								<FeatherIcon name="file-text" class="w-4 h-4" />
								<span class="hidden sm:inline">{{ __('CSV') }}</span>
							</button>

							<button
								@click="handlePrint"
								:disabled="!rows.length || printing"
								class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
								:title="__('Print')"
							>
								<FeatherIcon name="printer" class="w-4 h-4" :class="{ 'animate-pulse': printing }" />
								<span class="hidden sm:inline">{{ printing ? __('Printing...') : __('Print') }}</span>
							</button>
						</div>

						<!-- Result -->
						<div class="flex-1 overflow-auto bg-gray-50">
							<div v-if="loadingDefinition || running" class="flex flex-col items-center justify-center py-16">
								<div class="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-500 mb-3"></div>
								<p class="text-sm font-medium text-gray-600">
									{{ loadingDefinition ? __('Loading report...') : __('Running report...') }}
								</p>
							</div>

							<div v-else-if="errorMessage" class="m-4 sm:m-6 p-4 bg-red-50 border border-red-200 rounded-xl">
								<div class="flex items-start gap-3">
									<FeatherIcon name="alert-circle" class="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
									<div class="min-w-0">
										<p class="text-sm font-semibold text-red-800">{{ __('Could not run this report') }}</p>
										<p class="text-sm text-red-700 mt-1 break-words">{{ errorMessage }}</p>
									</div>
								</div>
							</div>

							<template v-else>
								<TranslatedHTML
									v-if="reportMessage"
									:key="reportMessage"
									tag="div"
									:inner="reportMessage"
									class="px-4 sm:px-6 pt-4 text-sm text-gray-700"
								/>

								<div v-if="!rows.length" class="text-center py-16">
									<FeatherIcon name="search" class="w-10 h-10 text-gray-300 mx-auto mb-3" />
									<p class="text-sm font-medium text-gray-600">{{ __('Nothing to show') }}</p>
									<p class="text-xs text-gray-500 mt-1">
										{{ __('Change the filters and press Refresh.') }}
									</p>
								</div>

								<div v-else class="p-4 sm:p-6">
									<div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-x-auto">
										<table class="min-w-full text-sm">
											<thead class="bg-gray-50 sticky top-0 z-10">
												<tr>
													<th class="px-3 py-2 text-xs font-semibold text-gray-500 text-start w-12">#</th>
													<th
														v-for="column in columns"
														:key="column.fieldname"
														class="px-3 py-2 text-xs font-semibold text-gray-600 whitespace-nowrap border-s border-gray-100"
														:class="isNumericColumn(column) ? 'text-end' : 'text-start'"
														:style="column.width ? { minWidth: `${column.width}px` } : null"
													>
														{{ __(column.label || column.fieldname) }}
													</th>
												</tr>
											</thead>
											<tbody>
												<tr
													v-for="(row, rowIndex) in rows"
													:key="rowIndex"
													:class="[
														rowIndex === totalRowIndex
															? 'bg-gray-50 font-semibold border-t-2 border-gray-300'
															: 'hover:bg-indigo-50/40',
														'border-t border-gray-100',
													]"
												>
													<td class="px-3 py-2 text-xs text-gray-400">
														{{ rowIndex === totalRowIndex ? '' : rowIndex + 1 }}
													</td>
													<td
														v-for="(column, columnIndex) in columns"
														:key="column.fieldname"
														class="px-3 py-2 text-gray-800 border-s border-gray-50"
														:class="isNumericColumn(column) ? 'text-end whitespace-nowrap tabular-nums' : ''"
													>
														{{ formatReportValue(getCellValue(row, column, columnIndex), column) }}
													</td>
												</tr>
											</tbody>
										</table>
									</div>
								</div>
							</template>
						</div>
					</template>
				</div>
			</div>
		</div>
	</Transition>

	<!-- Print Settings Dialog -->
	<Transition name="fade">
		<div
			v-if="showPrintSettings"
			class="fixed inset-0 bg-black bg-opacity-60 z-[400] flex items-center justify-center p-4"
			@click.self="showPrintSettings = false"
		>
			<div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden">
				<!-- Header -->
				<div class="flex items-center justify-between px-6 py-4 border-b">
					<h3 class="text-base font-semibold text-gray-900">{{ __('Print Settings') }}</h3>
					<button @click="showPrintSettings = false" class="p-1 hover:bg-gray-100 rounded-lg transition-colors">
						<FeatherIcon name="x" class="w-4 h-4 text-gray-500" />
					</button>
				</div>

				<!-- Body -->
				<div class="px-6 py-5 flex flex-col gap-4">
					<!-- Orientation -->
					<div class="flex flex-col gap-1.5">
						<label class="text-sm font-medium text-gray-700">{{ __('Orientation') }}</label>
						<select
							v-model="printOrientation"
							class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
						>
							<option value="Landscape">{{ __('Landscape') }}</option>
							<option value="Portrait">{{ __('Portrait') }}</option>
						</select>
					</div>

					<!-- Print Format -->
					<div class="flex flex-col gap-1.5">
						<label class="text-sm font-medium text-gray-700">{{ __('Print Format') }}</label>
						<select
							v-model="printFormat"
							class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
						>
							<option
								v-for="opt in printLayoutOptions"
								:key="opt.value"
								:value="opt.value"
							>{{ opt.label }}</option>
						</select>
					</div>

					<!-- With Letter Head -->
					<label class="flex items-center gap-3 cursor-pointer select-none">
						<input
							type="checkbox"
							v-model="printWithLetterhead"
							class="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
						/>
						<span class="text-sm text-gray-700">{{ __('With Letter head') }}</span>
					</label>

					<!-- Include Filters -->
					<label class="flex items-center gap-3 cursor-pointer select-none">
						<input
							type="checkbox"
							v-model="printIncludeFilters"
							class="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
						/>
						<span class="text-sm text-gray-700">{{ __('Include filters') }}</span>
					</label>
				</div>

				<!-- Footer -->
				<div class="px-6 pb-5 flex justify-end">
					<button
						@click="handlePrintSubmit"
						class="px-5 py-2 bg-gray-900 text-white text-sm font-semibold rounded-lg hover:bg-gray-700 transition-colors"
					>
						{{ __('Submit') }}
					</button>
				</div>
			</div>
		</div>
	</Transition>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"
import { computed, ref, watch } from "vue"
import TranslatedHTML from "@/components/common/TranslatedHTML.vue"
import ReportFilterField from "@/components/reports/ReportFilterField.vue"
import { useToast } from "@/composables/useToast"
import { call } from "@/utils/apiWrapper"
import { logger } from "@/utils/logger"
import { isOffline } from "@/utils/offline/sync"
import {
	exportReport,
	formatReportValue,
	getCellValue,
	isNumericColumn,
	printHtmlString,
	printReport,
	visibleColumns,
} from "@/utils/reportOutput"

const log = logger.create("POSReports")
const { showError, showSuccess } = useToast()

const props = defineProps({
	modelValue: Boolean,
	posProfile: {
		type: String,
		default: null,
	},
	branch: {
		type: String,
		default: null,
	},
})

const emit = defineEmits(["update:modelValue"])

const show = ref(props.modelValue)

const reports = ref([])
const loadingReports = ref(false)
const reportSearch = ref("")

const selectedReport = ref(null)
const definition = ref(null)
const loadingDefinition = ref(false)

const filterValues = ref({})
const columns = ref([])
const rows = ref([])
const reportMessage = ref("")
const running = ref(false)
const exporting = ref(false)
const errorMessage = ref("")
const addTotalRow = ref(false)

// Guards the auto-run below: the signature of the filters the last run used, so a
// filter edit that changes nothing the report sees does not re-query.
let lastRunSignature = null
let autoRunTimer = null

const showPrintSettings = ref(false)
const printOrientation = ref("Landscape")
const printFormat = ref("")
const printWithLetterhead = ref(false)
const printIncludeFilters = ref(true)
const printing = ref(false)

watch(
	() => props.modelValue,
	(val) => {
		show.value = val
		if (val) {
			backToList()
			loadReports()
		}
	},
)

watch(show, (val) => {
	emit("update:modelValue", val)
})

const filteredReports = computed(() => {
	const query = reportSearch.value.trim().toLowerCase()
	if (!query) return reports.value
	return reports.value.filter(
		(report) =>
			report.label.toLowerCase().includes(query) ||
			report.report.toLowerCase().includes(query),
	)
})

const definitionLabel = computed(() => definition.value?.label || selectedReport.value?.label || "")

const visibleFilters = computed(() =>
	(definition.value?.filters || []).filter((filter) => !filter.hidden),
)

const headerSubtitle = computed(() => {
	if (!selectedReport.value) {
		return props.branch ? __("Branch: {0}", [props.branch]) : __("Run and print your reports")
	}
	return definition.value?.ref_doctype ? __(definition.value.ref_doctype) : ""
})

const printLayoutOptions = computed(() => {
	const opts = [{ label: __("Default (Table View)"), value: "" }]
	for (const layout of definition.value?.print_layouts || []) {
		opts.push({ label: layout.label, value: layout.name })
	}
	return opts
})

/** The server appends the total row to the end of the result, so it is the last row. */
const totalRowIndex = computed(() =>
	addTotalRow.value && rows.value.length ? rows.value.length - 1 : -1,
)

/** Filter values keyed by label — what gets printed and written into exports. */
const appliedFilters = computed(() => {
	const applied = {}
	for (const filter of definition.value?.filters || []) {
		const value = filterValues.value[filter.fieldname]
		if (value === null || value === undefined || value === "") continue
		if (Array.isArray(value) && !value.length) continue
		applied[filter.label] =
			filter.fieldtype === "Check" ? (value ? __("Yes") : __("No")) : value
	}
	return applied
})

function handleClose() {
	show.value = false
}

function backToList() {
	clearTimeout(autoRunTimer)
	lastRunSignature = null
	selectedReport.value = null
	definition.value = null
	filterValues.value = {}
	columns.value = []
	rows.value = []
	reportMessage.value = ""
	errorMessage.value = ""
	addTotalRow.value = false
}

watch(definition, (def) => {
	if (def?.print_layouts?.length) {
		printFormat.value = def.print_layouts[0].name
	} else {
		printFormat.value = ""
	}
})

async function loadReports() {
	if (isOffline()) {
		reports.value = []
		showError(__("Reports need a connection to the server"))
		return
	}

	loadingReports.value = true
	try {
		reports.value =
			(await call("ecs_posnext.api.reports.get_pos_reports", {
				pos_profile: props.posProfile || null,
			})) || []
	} catch (error) {
		log.error("Error loading POS reports:", error)
		reports.value = []
		showError(error.message || __("Failed to load reports"))
	} finally {
		loadingReports.value = false
	}
}

async function openReport(report) {
	selectedReport.value = report
	definition.value = null
	errorMessage.value = ""
	columns.value = []
	rows.value = []
	reportMessage.value = ""
	loadingDefinition.value = true

	try {
		const result = await call("ecs_posnext.api.reports.get_report_definition", {
			report_name: report.report,
			pos_profile: props.posProfile || null,
		})
		definition.value = result
		filterValues.value = buildDefaultFilters(result.filters)
	} catch (error) {
		log.error(`Error loading report ${report.report}:`, error)
		errorMessage.value = extractMessage(error)
		loadingDefinition.value = false
		return
	}

	loadingDefinition.value = false

	// Reports that need a mandatory value the report itself does not default
	// would only fail, so wait for the cashier in that case
	if (missingMandatoryFilter.value) return
	runReport()
}

const missingMandatoryFilter = computed(() =>
	(definition.value?.filters || []).some((filter) => {
		if (!filter.reqd) return false
		const value = filterValues.value[filter.fieldname]
		return value === null || value === undefined || value === "" || (Array.isArray(value) && !value.length)
	}),
)

function buildDefaultFilters(filters) {
	const values = {}
	for (const filter of filters || []) {
		if (filter.fieldtype === "MultiSelectList") {
			values[filter.fieldname] = Array.isArray(filter.default) ? filter.default : []
		} else if (filter.fieldtype === "Check") {
			values[filter.fieldname] = filter.default ? 1 : 0
		} else {
			values[filter.fieldname] = filter.default ?? ""
		}
	}
	return values
}

/** Filter values as the report expects them — blanks dropped, not sent as "". */
function buildRunFilters() {
	const payload = {}
	for (const filter of definition.value?.filters || []) {
		const value = filterValues.value[filter.fieldname]
		if (value === null || value === undefined || value === "") continue
		if (Array.isArray(value) && !value.length) continue
		payload[filter.fieldname] = value
	}
	return payload
}

async function runReport() {
	if (!selectedReport.value) return

	if (missingMandatoryFilter.value) {
		showError(__("Please fill in the required filters"))
		return
	}

	clearTimeout(autoRunTimer)
	lastRunSignature = JSON.stringify(buildRunFilters())

	running.value = true
	errorMessage.value = ""
	try {
		const result = await call("ecs_posnext.api.reports.run_pos_report", {
			report_name: selectedReport.value.report,
			filters: lastRunSignature,
			pos_profile: props.posProfile || null,
		})

		columns.value = visibleColumns(result?.columns)
		rows.value = result?.result || []
		reportMessage.value = result?.message || ""
		addTotalRow.value = !!result?.add_total_row && !result?.skip_total_row
	} catch (error) {
		log.error(`Error running report ${selectedReport.value.report}:`, error)
		columns.value = []
		rows.value = []
		errorMessage.value = extractMessage(error)
	} finally {
		running.value = false
	}
}

/**
 * Re-run the report when a filter changes, the way the desk does.
 *
 * Debounced because a Data filter emits on every keystroke, and skipped when the
 * change leaves the payload identical — which is also what stops the defaults
 * assigned in openReport from running the report a second time.
 */
watch(
	filterValues,
	() => {
		if (!selectedReport.value || loadingDefinition.value) return
		if (JSON.stringify(buildRunFilters()) === lastRunSignature) return

		clearTimeout(autoRunTimer)
		autoRunTimer = setTimeout(() => {
			// Silently wait for a mandatory value rather than nagging on every keystroke
			if (missingMandatoryFilter.value) return
			runReport()
		}, 500)
	},
	{ deep: true },
)

async function handleExport(fileFormat) {
	exporting.value = true
	try {
		await exportReport({
			reportName: selectedReport.value.report,
			filters: buildRunFilters(),
			appliedFilters: appliedFilters.value,
			fileFormat,
		})
		showSuccess(__("Export started"))
	} catch (error) {
		log.error("Export failed:", error)
		showError(extractMessage(error) || __("Export failed"))
	} finally {
		exporting.value = false
	}
}

function handlePrint() {
	showPrintSettings.value = true
}

async function handlePrintSubmit() {
	showPrintSettings.value = false
	if (printFormat.value) {
		printing.value = true
		try {
			const html = await call("ecs_posnext.api.reports.render_report_print", {
				report_name: selectedReport.value.report,
				print_layout: printFormat.value,
				filters: JSON.stringify(buildRunFilters()),
				orientation: printOrientation.value,
				with_letterhead: printWithLetterhead.value ? 1 : 0,
				pos_profile: props.posProfile || null,
			})
			printHtmlString(html)
		} catch (error) {
			showError(extractMessage(error) || __("Print failed"))
		} finally {
			printing.value = false
		}
	} else {
		printReport({
			title: definitionLabel.value,
			subtitle: printIncludeFilters.value ? printSubtitle() : "",
			columns: columns.value,
			rows: rows.value,
			appliedFilters: printIncludeFilters.value ? appliedFilters.value : {},
			totalRowIndex: totalRowIndex.value,
			orientation: printOrientation.value,
		})
	}
}

function printSubtitle() {
	const parts = []
	if (props.branch) parts.push(__("Branch: {0}", [props.branch]))
	else if (props.posProfile) parts.push(props.posProfile)
	parts.push(new Date().toLocaleString())
	return parts.join(" • ")
}

/** Frappe wraps thrown messages in _server_messages; surface the readable one. */
function extractMessage(error) {
	const serverMessages = error?.messages?.length ? error.messages.join(" ") : null
	return (
		serverMessages ||
		error?.message ||
		error?.exc_type ||
		__("Something went wrong")
	)
		.toString()
		.replace(/<[^>]*>/g, "")
		.trim()
}
</script>
