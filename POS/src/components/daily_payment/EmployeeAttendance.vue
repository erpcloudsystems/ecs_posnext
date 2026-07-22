<template>
	<Transition name="fade">
		<div
			v-if="show"
			class="fixed inset-0 bg-black bg-opacity-50 z-[300]"
			@click.self="handleClose"
		>
			<div class="fixed inset-0 flex items-center justify-center p-4">
				<div class="w-full max-w-2xl bg-white rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">

					<!-- Header -->
					<div class="flex items-center justify-between px-6 py-5 border-b bg-gradient-to-r from-teal-50 to-emerald-50 flex-shrink-0">
						<div class="flex items-center gap-3">
							<div class="p-2 bg-teal-100 rounded-lg">
								<FeatherIcon name="user-check" class="w-6 h-6 text-teal-600" />
							</div>
							<div>
								<h2 class="text-xl font-bold text-gray-900">{{ __('Employee Attendance') }}</h2>
								<p class="text-sm text-gray-600 mt-0.5">
									{{ branch ? __('Branch: {0}', [branch]) : __('Mark employee attendance') }}
								</p>
							</div>
						</div>
						<button @click="handleClose" class="p-2 hover:bg-white/50 rounded-lg transition-colors">
							<FeatherIcon name="x" class="w-5 h-5 text-gray-600" />
						</button>
					</div>

					<!-- Filter Bar -->
					<div class="px-6 py-4 border-b bg-white flex flex-wrap items-end gap-3 flex-shrink-0">
						<!-- Date -->
						<div class="min-w-[160px]">
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __('Date') }}</label>
							<input
								v-model="date"
								type="date"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
							/>
						</div>

						<!-- Get Employees Button -->
						<button
							@click="loadEmployees"
							:disabled="loading"
							class="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors text-sm font-semibold disabled:opacity-60"
						>
							<FeatherIcon name="refresh-cw" class="w-4 h-4" :class="{ 'animate-spin': loading }" />
							{{ loading ? __('Loading...') : __('Get Employees') }}
						</button>
					</div>

					<!-- Content -->
					<div class="flex-1 overflow-y-auto p-6 bg-gray-50">

						<!-- Loading -->
						<div v-if="loading" class="flex flex-col items-center justify-center py-12">
							<div class="animate-spin rounded-full h-10 w-10 border-b-2 border-teal-500 mb-3"></div>
							<p class="text-sm font-medium text-gray-600">{{ __('Loading employees...') }}</p>
						</div>

						<template v-else>
							<!-- Already Marked -->
							<div v-if="marked.length" class="mb-5 bg-white rounded-xl border border-gray-200 shadow-sm p-4">
								<h3 class="text-sm font-semibold text-gray-700 mb-3">{{ __('Marked Attendance') }}</h3>
								<div class="flex flex-col gap-2 max-h-40 overflow-y-auto">
									<div
										v-for="entry in marked"
										:key="entry.employee"
										class="flex items-center justify-between px-3 py-2 rounded-lg bg-gray-50"
									>
										<span class="text-sm text-gray-800">{{ entry.employee }} : {{ entry.employee_name }}</span>
										<span
											class="text-xs font-semibold px-2 py-0.5 rounded"
											:class="statusBadgeClass(entry.status)"
										>
											{{ entry.status }}
										</span>
									</div>
								</div>
							</div>

							<!-- Unmarked Employees -->
							<div v-if="unmarked.length" class="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
								<div class="flex items-center justify-between mb-3">
									<div class="flex items-center gap-2">
										<h3 class="text-sm font-semibold text-gray-700">{{ __('Unmarked Employees') }}</h3>
										<span
											v-if="selectedEmployees.length"
											class="text-xs font-semibold px-2 py-0.5 rounded-full bg-teal-100 text-teal-700"
										>
											{{ __('{0} selected', [selectedEmployees.length]) }}
										</span>
									</div>
									<label class="flex items-center gap-2 text-xs text-gray-600">
										<input type="checkbox" v-model="selectAll" @change="toggleSelectAll" />
										{{ __('Select All') }}
									</label>
								</div>
								<div class="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-64 overflow-y-auto mb-4">
									<label
										v-for="entry in unmarked"
										:key="entry.employee"
										class="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer text-sm"
									>
										<input type="checkbox" :value="entry.employee" v-model="selectedEmployees" />
										{{ entry.employee }} : {{ entry.employee_name }}
									</label>
								</div>

								<!-- Status -->
								<div class="flex flex-wrap items-end gap-3">
									<div class="min-w-[160px]">
										<label class="block text-xs font-medium text-gray-600 mb-1">{{ __('Status') }}</label>
										<select
											v-model="status"
											class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
										>
											<option value="">{{ __('Select Status') }}</option>
											<option value="Present">{{ __('Present') }}</option>
											<option value="Absent">{{ __('Absent') }}</option>
											<option value="Half Day">{{ __('Half Day') }}</option>
										</select>
									</div>
									<button
										@click="markAttendance"
										:disabled="marking || !selectedEmployees.length || !status"
										class="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors text-sm font-semibold disabled:opacity-60"
									>
										{{
											marking
												? __('Marking...')
												: selectedEmployees.length
													? __('Mark Attendance ({0})', [selectedEmployees.length])
													: __('Mark Attendance')
										}}
									</button>
								</div>
							</div>

							<!-- Nothing to mark -->
							<div v-if="loaded && !unmarked.length && !marked.length" class="text-center py-12 text-sm text-gray-500">
								{{ __('No employees found for the selected date.') }}
							</div>
							<div v-else-if="loaded && !unmarked.length && marked.length" class="text-center py-6 text-sm text-gray-500 mt-4">
								{{ __('Attendance for all employees has already been marked.') }}
							</div>
						</template>
					</div>
				</div>
			</div>
		</div>
	</Transition>
</template>

<script setup>
import { FeatherIcon, call } from "frappe-ui"
import { ref, watch } from "vue"
import { useToast } from "@/composables/useToast"
import { logger } from "@/utils/logger"

const log = logger.create("EmployeeAttendance")
const { showSuccess, showError } = useToast()

const props = defineProps({
	modelValue: Boolean,
	company: {
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
const loading = ref(false)
const marking = ref(false)
const loaded = ref(false)

const today = new Date().toISOString().split("T")[0]
const date = ref(today)

const marked = ref([])
const unmarked = ref([])
const selectedEmployees = ref([])
const selectAll = ref(false)
const status = ref("")

watch(
	() => props.modelValue,
	(val) => {
		show.value = val
		if (val) {
			resetState()
			loadEmployees()
		}
	},
)

watch(show, (val) => {
	emit("update:modelValue", val)
})

function resetState() {
	marked.value = []
	unmarked.value = []
	selectedEmployees.value = []
	selectAll.value = false
	status.value = ""
	loaded.value = false
}

function handleClose() {
	show.value = false
}

function statusBadgeClass(status) {
	if (status === "Present") return "bg-green-100 text-green-700"
	if (status === "Half Day") return "bg-amber-100 text-amber-700"
	return "bg-red-100 text-red-700"
}

function toggleSelectAll() {
	selectedEmployees.value = selectAll.value ? unmarked.value.map((e) => e.employee) : []
}

async function loadEmployees() {
	loading.value = true
	selectedEmployees.value = []
	selectAll.value = false
	status.value = ""
	try {
		const result = await call("ecs_posnext.api.employee_attendance.get_employees", {
			date: date.value,
			company: props.company || null,
			branch: props.branch || null,
		})
		marked.value = result?.marked || []
		unmarked.value = result?.unmarked || []
		loaded.value = true
	} catch (error) {
		log.error("Error loading employees:", error)
		showError(error.message || __("Failed to load employees"))
	} finally {
		loading.value = false
	}
}

async function markAttendance() {
	if (!selectedEmployees.value.length || !status.value) return

	marking.value = true
	try {
		await call("ecs_posnext.api.employee_attendance.mark_employee_attendance", {
			employee_list: selectedEmployees.value,
			status: status.value,
			date: date.value,
			company: props.company || null,
		})
		showSuccess(__("Attendance marked successfully"))
		await loadEmployees()
	} catch (error) {
		log.error("Error marking attendance:", error)
		showError(error.message || __("Failed to mark attendance"))
	} finally {
		marking.value = false
	}
}
</script>
