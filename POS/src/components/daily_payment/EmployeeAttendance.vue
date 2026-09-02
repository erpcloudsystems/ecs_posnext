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

						<!-- Shift — system-determined (the default Shift Type), not a user choice -->
						<div class="min-w-[180px]">
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __('Shift') }}</label>
							<div
								class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-gray-100 text-gray-700 truncate"
								:title="shift || ''"
							>
								{{ loadingShifts ? __('Loading...') : shift || __('No Shift') }}
							</div>
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
								<div class="flex flex-col gap-2 max-h-56 overflow-y-auto">
									<div
										v-for="entry in marked"
										:key="entry.employee"
										class="flex flex-wrap items-center justify-between gap-2 px-3 py-2 rounded-lg bg-gray-50"
									>
										<span class="text-sm text-gray-800">{{ entry.employee }} : {{ entry.employee_name }}</span>
										<div class="flex items-center gap-2 flex-wrap">
											<span
												v-if="entry.shift"
												class="text-xs font-medium px-2 py-0.5 rounded bg-blue-100 text-blue-700"
											>
												{{ entry.shift }}
											</span>
											<span
												class="text-xs font-semibold px-2 py-0.5 rounded"
												:class="statusBadgeClass(entry.status)"
											>
												{{ entry.status }}
											</span>
											<!-- Which correction produced this Half Day -->
											<span
												v-if="halfDayNote(entry)"
												class="text-xs font-medium px-2 py-0.5 rounded bg-gray-200 text-gray-700"
											>
												{{ halfDayNote(entry) }}
											</span>

											<!-- Half Day correction: cancels the record and re-creates it as
											     an amendment, so it asks before committing -->
											<template v-if="halfDayReason(entry)">
												<template v-if="confirmingEmployee === entry.employee">
													<span class="text-xs text-gray-600">{{ __('Mark Half Day?') }}</span>
													<button
														@click="convertToHalfDay(entry)"
														:disabled="converting"
														class="text-xs font-semibold px-2 py-1 rounded bg-amber-600 text-white hover:bg-amber-700 transition-colors disabled:opacity-60"
													>
														{{ converting ? __('Saving...') : __('Confirm') }}
													</button>
													<button
														@click="confirmingEmployee = null"
														:disabled="converting"
														class="text-xs font-semibold px-2 py-1 rounded bg-gray-200 text-gray-700 hover:bg-gray-300 transition-colors disabled:opacity-60"
													>
														{{ __('Cancel') }}
													</button>
												</template>
												<button
													v-else
													@click="confirmingEmployee = entry.employee"
													:disabled="converting"
													class="flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded border border-amber-300 text-amber-700 hover:bg-amber-50 transition-colors disabled:opacity-60"
													:title="halfDayActionTitle(entry)"
												>
													<FeatherIcon
														:name="halfDayReason(entry) === 'late_entry' ? 'log-in' : 'log-out'"
														class="w-3 h-3"
													/>
													{{ halfDayActionLabel(entry) }}
												</button>
											</template>
										</div>
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
import { localDateString } from "@/composables/useFormatters"
import { useToast } from "@/composables/useToast"
import { logger } from "@/utils/logger"
import { getSetting, setSetting } from "@/utils/offline/db"
import { enqueueOperation } from "@/utils/offline/operations"
import { isOffline } from "@/utils/offline/sync"

const log = logger.create("EmployeeAttendance")
const { showSuccess, showError } = useToast()

// Settings-store keys for offline caches
const EMPLOYEES_CACHE_KEY = "attendance_employees"
const SHIFT_TYPES_CACHE_KEY = "attendance_shift_types"

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

const emit = defineEmits(["update:modelValue", "marked"])

const show = ref(props.modelValue)
const loading = ref(false)
const marking = ref(false)
const loaded = ref(false)

// The shift's business date, resolved by the server on every open (see loadShiftTypes).
// Overnight shifts are stamped with the day the shift STARTED, so after midnight this
// is yesterday — a plain calendar date would mark attendance on the wrong day.
// Left editable so attendance can still be back-marked.
const date = ref(localDateString())

const marked = ref([])
const unmarked = ref([])
const selectedEmployees = ref([])
const selectAll = ref(false)
const status = ref("")

// Half Day correction — the employee whose row is awaiting confirmation.
// Converting cancels a submitted Attendance record and re-creates it as an
// amendment, so it is never a single unguarded tap.
const confirmingEmployee = ref(null)
const converting = ref(false)

// Shift — system-determined (the Shift Type flagged as default), never user-picked.
// Only ever written from the server response in loadShiftTypes().
const shiftTypes = ref([])
const shift = ref("")
const loadingShifts = ref(false)

watch(
	() => props.modelValue,
	async (val) => {
		show.value = val
		if (val) {
			resetState()
			// Resolves the shift and its business date, which loadEmployees() needs
			await loadShiftTypes()
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
	confirmingEmployee.value = null
}

function handleClose() {
	show.value = false
}

function statusBadgeClass(status) {
	if (status === "Present") return "bg-green-100 text-green-700"
	if (status === "Half Day") return "bg-amber-100 text-amber-700"
	return "bg-red-100 text-red-700"
}

/**
 * Which Half Day correction, if any, this marked row can take:
 *  - Present -> "early_exit": the sales person left before the shift ended
 *  - Absent  -> "late_entry": the sales person turned up after it started
 * Anything else (Half Day, On Leave, Work From Home) offers no action.
 */
function halfDayReason(entry) {
	if (entry?.status === "Present") return "early_exit"
	if (entry?.status === "Absent") return "late_entry"
	return null
}

function halfDayActionLabel(entry) {
	return halfDayReason(entry) === "late_entry"
		? __("Arrived Late")
		: __("Left Early")
}

function halfDayActionTitle(entry) {
	return halfDayReason(entry) === "late_entry"
		? __("Arrived after the shift started — mark Half Day")
		: __("Left before the shift ended — mark Half Day")
}

/** Label an existing Half Day with the correction that produced it. */
function halfDayNote(entry) {
	if (entry?.status !== "Half Day") return ""
	if (entry.late_entry && !entry.early_exit) return __("Arrived late")
	if (entry.early_exit && !entry.late_entry) return __("Left early")
	return ""
}

async function convertToHalfDay(entry) {
	const reason = halfDayReason(entry)
	if (!reason || converting.value) return

	converting.value = true
	try {
		const payload = {
			employee_list: [entry.employee],
			reason,
			date: date.value,
			company: props.company || null,
			branch: props.branch || null,
		}

		if (isOffline()) {
			// Server dedups per (employee, date, reason) on flush
			await enqueueOperation("attendance_half_day", payload)
			showSuccess(__("Half Day queued — will sync when back online"))
			// Reflect it locally: loadEmployees() cannot re-read the server offline
			entry.status = "Half Day"
			entry.late_entry = reason === "late_entry" ? 1 : 0
			entry.early_exit = reason === "early_exit" ? 1 : 0
			return
		}

		const result = await call(
			"ecs_posnext.api.employee_attendance.convert_attendance_to_half_day",
			payload,
		)
		// Rows that no longer match the expected status are reported, not thrown
		const skipped = result?.skipped || []
		if (!result?.updated?.length && skipped.length) {
			showError(skipped[0].message || __("Attendance could not be changed"))
		} else {
			showSuccess(__("Attendance changed to Half Day"))
			// A late arrival becomes selectable in POS, an early exit stops being so
			emit("marked")
		}
		await loadEmployees()
	} catch (error) {
		log.error("Error converting attendance to half day:", error)
		showError(error.message || __("Failed to change attendance"))
	} finally {
		converting.value = false
		confirmingEmployee.value = null
	}
}

function toggleSelectAll() {
	selectedEmployees.value = selectAll.value ? unmarked.value.map((e) => e.employee) : []
}

function timeToSeconds(value) {
	// Frappe serialises Time fields as "H:MM:SS", so the hour is not zero-padded
	// and the strings cannot be compared directly
	const parts = String(value ?? "").split(":").map(Number)
	if (parts.length < 2 || parts.some(Number.isNaN)) return null
	return (parts[0] || 0) * 3600 + (parts[1] || 0) * 60 + (parts[2] || 0)
}

/**
 * Offline mirror of the server's business-date rule: while an overnight shift
 * (end <= start) has not ended yet, we are still on the shift that started
 * yesterday, so attendance belongs to yesterday.
 */
function offlineBusinessDate(shiftEntry) {
	const now = new Date()
	const start = timeToSeconds(shiftEntry?.start_time)
	const end = timeToSeconds(shiftEntry?.end_time)
	if (start === null || end === null || end > start) return localDateString(now)

	const nowSeconds = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds()
	if (nowSeconds > end) return localDateString(now)

	const yesterday = new Date(now)
	yesterday.setDate(yesterday.getDate() - 1)
	return localDateString(yesterday)
}

async function loadShiftTypes() {
	loadingShifts.value = true
	try {
		if (isOffline()) {
			const cached = await getSetting(SHIFT_TYPES_CACHE_KEY, null)
			shiftTypes.value = cached?.shift_types || []
			shift.value = cached?.default_shift || cached?.last_shift || ""
			// A cached business_date would be stale, so derive it from the shift's times
			date.value = offlineBusinessDate(
				shiftTypes.value.find((entry) => entry.name === shift.value),
			)
			return
		}
		const result = await call("ecs_posnext.api.employee_attendance.get_shift_types")
		shiftTypes.value = result?.shift_types || []
		// The shift is system-determined, not a user choice
		shift.value = result?.default_shift || ""
		// Server-resolved so it always agrees with the POS craftsman gate
		date.value = result?.business_date || result?.server_date || localDateString()
		// Cache for offline use
		await setSetting(SHIFT_TYPES_CACHE_KEY, result)
	} catch (error) {
		log.error("Error loading shift types:", error)
		shiftTypes.value = []
		shift.value = ""
		date.value = localDateString()
	} finally {
		loadingShifts.value = false
	}
}

async function loadEmployees() {
	loading.value = true
	selectedEmployees.value = []
	selectAll.value = false
	status.value = ""
	confirmingEmployee.value = null
	try {
		if (isOffline()) {
			// Offline: server can't tell us who is already marked, so present the
			// cached roster as selectable (unmarked). Re-marking is idempotent on sync.
			const cached = await getSetting(EMPLOYEES_CACHE_KEY, null)
			const roster = [
				...(cached?.unmarked || []),
				...(cached?.marked || []),
			]
			marked.value = []
			unmarked.value = roster
			loaded.value = true
			return
		}

		const result = await call("ecs_posnext.api.employee_attendance.get_employees", {
			date: date.value,
			company: props.company || null,
			branch: props.branch || null,
		})
		marked.value = result?.marked || []
		unmarked.value = result?.unmarked || []
		loaded.value = true
		// Cache the roster for offline marking
		await setSetting(EMPLOYEES_CACHE_KEY, result)
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
		if (isOffline()) {
			// Queue for sync; server dedups per (employee, date) on flush
			await enqueueOperation("attendance", {
				employee_list: [...selectedEmployees.value],
				status: status.value,
				date: date.value,
				company: props.company || null,
				shift: shift.value || null,
				branch: props.branch || null,
			})
			showSuccess(
				__("Attendance queued — will sync when back online"),
			)
			await loadEmployees()
			return
		}

		await call("ecs_posnext.api.employee_attendance.mark_employee_attendance", {
			employee_list: selectedEmployees.value,
			status: status.value,
			date: date.value,
			company: props.company || null,
			shift: shift.value || null,
			branch: props.branch || null,
		})
		showSuccess(__("Attendance marked successfully"))
		// Craftsmen become visible in POS only once they are marked Present
		emit("marked")
		await loadEmployees()
	} catch (error) {
		log.error("Error marking attendance:", error)
		showError(error.message || __("Failed to mark attendance"))
	} finally {
		marking.value = false
	}
}
</script>
