<template>
	<Transition name="fade">
		<div
			v-if="show"
			class="fixed inset-0 bg-black bg-opacity-60 z-[400] flex items-center justify-center p-4"
			@click.self="handleClose"
		>
			<div class="w-full max-w-2xl bg-white rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">

				<!-- Header -->
				<div class="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-green-50 to-emerald-50 flex-shrink-0">
					<div class="flex items-center gap-3">
						<div class="p-2 bg-green-100 rounded-lg">
							<svg class="w-5 h-5 text-green-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
							</svg>
						</div>
						<div>
							<h3 class="text-lg font-bold text-gray-900">{{ __('New Daily Payment') }}</h3>
							<p v-if="branch" class="text-xs text-gray-500">{{ __('Branch: {0}', [branch]) }}</p>
						</div>
					</div>
					<button @click="handleClose" class="p-2 hover:bg-gray-100 rounded-lg transition-colors">
						<svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
						</svg>
					</button>
				</div>

				<!-- Form Body -->
				<div class="flex-1 overflow-y-auto p-6">
					<div class="flex flex-col gap-6">

						<!-- Type Section: Checkboxes -->
						<div class="bg-gray-50 rounded-xl p-4 border border-gray-200">
							<p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">{{ __('Payment Type') }}</p>
							<div class="flex flex-wrap gap-4">
								<!-- Payment to Employees -->
								<label class="flex items-center gap-3 cursor-pointer select-none group">
									<div
										@click="form.payment_to_employees = !form.payment_to_employees"
										:class="[
											'w-11 h-6 rounded-full transition-colors relative flex-shrink-0',
											form.payment_to_employees ? 'bg-green-600' : 'bg-gray-300'
										]"
									>
										<div :class="[
											'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
											form.payment_to_employees ? 'translate-x-5' : 'translate-x-0'
										]"></div>
									</div>
									<span class="text-sm font-medium text-gray-800">{{ __('Payment to Employees') }}</span>
								</label>

								<!-- Expenses -->
								<label class="flex items-center gap-3 cursor-pointer select-none group">
									<div
										@click="form.expenses = !form.expenses"
										:class="[
											'w-11 h-6 rounded-full transition-colors relative flex-shrink-0',
											form.expenses ? 'bg-amber-500' : 'bg-gray-300'
										]"
									>
										<div :class="[
											'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
											form.expenses ? 'translate-x-5' : 'translate-x-0'
										]"></div>
									</div>
									<span class="text-sm font-medium text-gray-800">{{ __('Expenses') }}</span>
								</label>

								<!-- Deduction -->
								<label class="flex items-center gap-3 cursor-pointer select-none group">
									<div
										@click="form.deduction = !form.deduction"
										:class="[
											'w-11 h-6 rounded-full transition-colors relative flex-shrink-0',
											form.deduction ? 'bg-red-500' : 'bg-gray-300'
										]"
									>
										<div :class="[
											'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
											form.deduction ? 'translate-x-5' : 'translate-x-0'
										]"></div>
									</div>
									<span class="text-sm font-medium text-gray-800">{{ __('Deduction') }}</span>
								</label>
							</div>
						</div>

						<!-- Base Fields: Date, Branch, Mode of Payment -->
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
							<!-- Date -->
							<div>
								<label class="block text-sm font-semibold text-gray-700 mb-1.5">
									{{ __('Date') }}
									<span class="text-red-500 ms-0.5">*</span>
								</label>
								<input
									v-model="form.date"
									type="date"
									class="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
									:class="{ 'border-red-400': errors.date }"
								/>
								<p v-if="errors.date" class="text-xs text-red-500 mt-1">{{ errors.date }}</p>
							</div>

							<!-- Branch (read-only, pre-filled) -->
							<div>
								<label class="block text-sm font-semibold text-gray-700 mb-1.5">
									{{ __('Branch') }}
									<span class="text-red-500 ms-0.5">*</span>
								</label>
								<input
									v-model="form.branch"
									type="text"
									readonly
									class="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm bg-gray-50 text-gray-600 cursor-not-allowed"
								/>
							</div>

							<!-- Mode of Payment -->
							<div class="sm:col-span-2">
								<label class="block text-sm font-semibold text-gray-700 mb-1.5">{{ __('Mode of Payment') }}</label>
								<select
									v-model="form.mode_of_payment"
									class="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white"
								>
									<option value="">{{ __('-- Select --') }}</option>
									<option v-for="m in paymentMethodOptions" :key="m" :value="m">{{ m }}</option>
								</select>
							</div>
						</div>

						<!-- Employee Section (conditional) -->
						<Transition name="slide-down">
							<div v-if="form.payment_to_employees" class="border border-blue-200 rounded-xl p-4 bg-blue-50/40">
								<p class="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-4">{{ __('Employee Details') }}</p>
								<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
									<!-- Employee -->
									<div>
										<label class="block text-sm font-semibold text-gray-700 mb-1.5">
											{{ __('Employee') }}
										</label>
										<LinkInput
											v-model="form.employee"
											doctype="Employee"
											query="ecs_posnext.api.daily_payment.employee_query"
											:filters="branch ? { branch } : null"
											:placeholder="__('Search by ID or name...')"
											@select="onEmployeeSelect"
										/>
									</div>

									<!-- Employee Name (read-only) -->
									<div>
										<label class="block text-sm font-semibold text-gray-700 mb-1.5">{{ __('Employee Name') }}</label>
										<input
											v-model="form.employee_name"
											type="text"
											readonly
											class="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm bg-gray-50 text-gray-600 cursor-not-allowed"
											:placeholder="__('Auto-filled from employee')"
										/>
									</div>

									<!-- Amount -->
									<div>
										<label class="block text-sm font-semibold text-gray-700 mb-1.5">
											{{ __('Amount') }}
											<span class="text-red-500 ms-0.5">*</span>
										</label>
										<input
											v-model.number="form.amount"
											type="number"
											min="0"
											step="0.01"
											class="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
											:class="{ 'border-red-400': errors.amount }"
											:placeholder="__('Enter amount')"
										/>
										<p v-if="errors.amount" class="text-xs text-red-500 mt-1">{{ errors.amount }}</p>
									</div>

									<!-- Loan Product -->
									<div>
										<label class="block text-sm font-semibold text-gray-700 mb-1.5">
											{{ __('Loan Product') }}
											<span class="text-red-500 ms-0.5">*</span>
										</label>
										<LinkInput
											v-model="form.loan_product"
											doctype="Loan Product"
											:placeholder="__('Select loan product...')"
										/>
										<p v-if="errors.loan_product" class="text-xs text-red-500 mt-1">{{ errors.loan_product }}</p>
									</div>
								</div>
							</div>
						</Transition>

						<!-- Deduction Section (conditional) -->
						<Transition name="slide-down">
							<div v-if="form.deduction" class="border border-red-200 rounded-xl p-4 bg-red-50/40">
								<p class="text-xs font-semibold text-red-600 uppercase tracking-wide mb-4">{{ __('Deduction Details') }}</p>
								<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
									<!-- Employee -->
									<div>
										<label class="block text-sm font-semibold text-gray-700 mb-1.5">
											{{ __('Employee') }}
											<span class="text-red-500 ms-0.5">*</span>
										</label>
										<LinkInput
											v-model="form.employee"
											doctype="Employee"
											query="ecs_posnext.api.daily_payment.employee_query"
											:filters="branch ? { branch } : null"
											:placeholder="__('Search by ID or name...')"
											@select="onEmployeeSelect"
										/>
										<p v-if="errors.deductionEmployee" class="text-xs text-red-500 mt-1">{{ errors.deductionEmployee }}</p>
									</div>

									<!-- Employee Name (read-only) -->
									<div>
										<label class="block text-sm font-semibold text-gray-700 mb-1.5">{{ __('Employee Name') }}</label>
										<input
											v-model="form.employee_name"
											type="text"
											readonly
											class="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm bg-gray-50 text-gray-600 cursor-not-allowed"
											:placeholder="__('Auto-filled from employee')"
										/>
									</div>

									<!-- Amount -->
									<div>
										<label class="block text-sm font-semibold text-gray-700 mb-1.5">
											{{ __('Amount') }}
											<span class="text-red-500 ms-0.5">*</span>
										</label>
										<input
											v-model.number="form.amount"
											type="number"
											min="0"
											step="0.01"
											class="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
											:class="{ 'border-red-400': errors.deductionAmount }"
											:placeholder="__('Enter amount')"
										/>
										<p v-if="errors.deductionAmount" class="text-xs text-red-500 mt-1">{{ errors.deductionAmount }}</p>
									</div>

									<!-- Salary Component -->
									<div>
										<label class="block text-sm font-semibold text-gray-700 mb-1.5">
											{{ __('Salary Component') }}
										</label>
										<LinkInput
											v-model="form.salary_component"
											doctype="Salary Component"
											:placeholder="__('Select salary component...')"
										/>
									</div>
								</div>
							</div>
						</Transition>

						<!-- General Expenses Table (conditional) -->
						<Transition name="slide-down">
							<div v-if="form.expenses" class="border border-amber-200 rounded-xl p-4 bg-amber-50/40">
								<div class="flex items-center justify-between mb-4">
									<p class="text-xs font-semibold text-amber-700 uppercase tracking-wide">{{ __('General Expenses') }}</p>
									<button
										@click="addExpenseRow"
										class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white rounded-lg transition-colors"
										style="background-color:#d97706"
									>
										<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
										</svg>
										{{ __('Add Row') }}
									</button>
								</div>

								<!-- Table Header -->
								<div class="grid grid-cols-[1fr_120px_1fr_32px] gap-2 mb-2 px-1">
									<span class="text-xs font-semibold text-gray-500">{{ __('Expense Type') }}</span>
									<span class="text-xs font-semibold text-gray-500">{{ __('Amount') }}</span>
									<span class="text-xs font-semibold text-gray-500">{{ __('Description') }}</span>
									<span></span>
								</div>

								<!-- Empty state -->
								<div v-if="form.general_expenses.length === 0" class="text-center py-6 text-sm text-gray-400 border border-dashed border-amber-300 rounded-lg">
									{{ __('No expense rows. Click "Add Row" to add.') }}
								</div>

								<!-- Rows -->
								<div class="flex flex-col gap-2">
									<div
										v-for="(row, idx) in form.general_expenses"
										:key="idx"
										class="grid grid-cols-[1fr_120px_1fr_32px] gap-2 items-start bg-white rounded-lg p-2 border border-amber-100"
									>
										<LinkInput
											v-model="row.expense_claim_type"
											doctype="Expense Claim Type"
											:placeholder="__('Type...')"
											size="sm"
										/>
										<input
											v-model.number="row.amount"
											type="number"
											min="0"
											step="0.01"
											class="w-full px-2 py-1.5 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-amber-400"
											placeholder="0.00"
										/>
										<input
											v-model="row.description"
											type="text"
											class="w-full px-2 py-1.5 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-amber-400"
											:placeholder="__('Description...')"
										/>
										<button
											@click="removeExpenseRow(idx)"
											class="w-8 h-8 flex items-center justify-center text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors mt-0.5"
										>
											<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
											</svg>
										</button>
									</div>
								</div>

								<!-- Total -->
								<div v-if="form.general_expenses.length > 0" class="mt-3 flex justify-end">
									<span class="text-sm font-bold text-amber-800">
										{{ __('Total: {0}', [expensesTotal]) }}
									</span>
								</div>
							</div>
						</Transition>

					</div>
				</div>

				<!-- Footer -->
				<div class="px-6 py-4 border-t bg-gray-50 flex items-center justify-end gap-3 flex-shrink-0">
					<button
						@click="handleClose"
						class="px-5 py-2.5 text-sm font-semibold text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
					>
						{{ __('Cancel') }}
					</button>
					<button
						@click="handleSave"
						:disabled="saving"
						class="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white rounded-lg transition-colors disabled:opacity-60"
						style="background-color:#16a34a"
					>
						<svg v-if="saving" class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
						</svg>
						<svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
						</svg>
						{{ saving ? __('Saving...') : __('Save') }}
					</button>
				</div>

			</div>
		</div>
	</Transition>

	<!-- LinkInput is used inline via component registration below -->
</template>

<script setup>
import { call } from "frappe-ui"
import { computed, defineComponent, h, nextTick, reactive, ref, watch } from "vue"
import { useToast } from "@/composables/useToast"
import { logger } from "@/utils/logger"
import { getSetting } from "@/utils/offline/db"
import { enqueueOperation } from "@/utils/offline/operations"
import { isOffline } from "@/utils/offline/sync"

const log = logger.create("DailyPaymentForm")
const { showSuccess, showError } = useToast()

const props = defineProps({
	modelValue: Boolean,
	branch: {
		type: String,
		default: null,
	},
	paymentMethods: {
		type: Array,
		default: () => [],
	},
	posOpeningShift: {
		type: String,
		default: null,
	},
})

const emit = defineEmits(["update:modelValue", "saved"])

const paymentMethodOptions = computed(() => props.paymentMethods || [])

const show = ref(props.modelValue)
const saving = ref(false)
const errors = reactive({})

function todayStr() {
	return new Date().toISOString().split("T")[0]
}

const form = reactive({
	date: todayStr(),
	branch: props.branch || "",
	mode_of_payment: "",
	payment_to_employees: false,
	expenses: false,
	deduction: false,
	employee: "",
	employee_name: "",
	company: "",
	amount: null,
	loan_product: "سلفة من الراتب",
	salary_component: "خصم من الراتب",
	general_expenses: [],
})

watch(
	() => props.modelValue,
	(val) => {
		show.value = val
		if (val) {
			resetForm()
		}
	},
)

watch(show, (val) => {
	emit("update:modelValue", val)
})

watch(
	() => props.branch,
	(val) => {
		form.branch = val || ""
	},
)

function resetForm() {
	form.date = todayStr()
	form.branch = props.branch || ""
	form.mode_of_payment = ""
	form.payment_to_employees = false
	form.expenses = false
	form.deduction = false
	form.employee = ""
	form.employee_name = ""
	form.company = ""
	form.amount = null
	form.loan_product = "سلفة من الراتب"
	form.salary_component = "خصم من الراتب"
	form.general_expenses = []
	Object.keys(errors).forEach((k) => delete errors[k])
}

function handleClose() {
	show.value = false
}

async function onEmployeeSelect(value) {
	if (!value) {
		form.employee_name = ""
		form.company = ""
		return
	}
	// Offline: resolve the name from the cached roster instead of the server
	if (isOffline()) {
		try {
			const cached = await getSetting("attendance_employees", null)
			const roster = [...(cached?.unmarked || []), ...(cached?.marked || [])]
			const match = roster.find((e) => e.employee === value)
			form.employee_name = match?.employee_name || ""
			form.company = props.company || form.company || ""
		} catch (e) {
			log.error("Error resolving employee from cache:", e)
		}
		return
	}
	try {
		const result = await call("frappe.client.get_value", {
			doctype: "Employee",
			filters: { name: value },
			fieldname: ["employee_name", "company"],
		})
		if (result) {
			form.employee_name = result.employee_name || ""
			form.company = result.company || ""
		}
	} catch (e) {
		log.error("Error fetching employee details:", e)
	}
}

function addExpenseRow() {
	form.general_expenses.push({ expense_claim_type: "", amount: null, description: "" })
}

function removeExpenseRow(idx) {
	form.general_expenses.splice(idx, 1)
}

const expensesTotal = computed(() => {
	const total = form.general_expenses.reduce((s, r) => s + (Number(r.amount) || 0), 0)
	return new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(total)
})

function validate() {
	Object.keys(errors).forEach((k) => delete errors[k])
	let valid = true
	if (!form.date) {
		errors.date = __("Date is required")
		valid = false
	}
	if (form.payment_to_employees) {
		if (!form.amount || form.amount <= 0) {
			errors.amount = __("Amount is required")
			valid = false
		}
		if (!form.loan_product) {
			errors.loan_product = __("Loan Product is required")
			valid = false
		}
	}
	if (form.deduction) {
		if (!form.employee) {
			errors.deductionEmployee = __("Employee is required")
			valid = false
		}
		if (!form.amount || form.amount <= 0) {
			errors.deductionAmount = __("Amount is required")
			valid = false
		}
	}
	return valid
}

async function handleSave() {
	if (!validate()) return
	saving.value = true
	try {
		const payload = {
			date: form.date,
			branch: form.branch,
			mode_of_payment: form.mode_of_payment || null,
			payment_to_employees: form.payment_to_employees ? 1 : 0,
			expenses: form.expenses ? 1 : 0,
			deduction: form.deduction ? 1 : 0,
			employee: (form.payment_to_employees || form.deduction) ? (form.employee || null) : null,
			amount: (form.payment_to_employees || form.deduction) ? (form.amount || null) : null,
			loan_product: form.payment_to_employees ? (form.loan_product || null) : null,
			salary_component: form.deduction ? (form.salary_component || null) : null,
			general_expenses: form.expenses ? JSON.stringify(form.general_expenses) : null,
			pos_opening_shift: props.posOpeningShift || null,
		}

		if (isOffline()) {
			await enqueueOperation("daily_payment", payload)
			showSuccess(__("Daily Payment queued — will sync when back online"))
			emit("saved")
			handleClose()
			return
		}

		await call("ecs_posnext.api.daily_payment.create_daily_payment", payload)
		showSuccess(__("Daily Payment created successfully"))
		emit("saved")
		handleClose()
	} catch (error) {
		log.error("Error saving daily payment:", error)
		showError(error.message || __("Failed to save daily payment"))
	} finally {
		saving.value = false
	}
}

// ── LinkInput inline component ─────────────────────────────────────────────
const LinkInput = defineComponent({
	name: "LinkInput",
	props: {
		modelValue: { type: String, default: "" },
		doctype: { type: String, required: true },
		placeholder: { type: String, default: "" },
		size: { type: String, default: "md" },
		query: { type: String, default: null },
		filters: { type: Object, default: null },
	},
	emits: ["update:modelValue", "select"],
	setup(props, { emit }) {
		const inputVal = ref(props.modelValue || "")
		const results = ref([])
		const open = ref(false)
		const searching = ref(false)
		let debounce = null

		watch(
			() => props.modelValue,
			(v) => { inputVal.value = v || "" },
		)

		async function search(txt) {
			searching.value = true
			try {
				// Offline: server link search is unavailable. For Employees, fall
				// back to the roster cached by the attendance screen; other doctypes
				// simply offer no suggestions (the field stays free-text).
				if (isOffline()) {
					if (props.doctype === "Employee") {
						const cached = await getSetting("attendance_employees", null)
						const roster = [
							...(cached?.unmarked || []),
							...(cached?.marked || []),
						]
						const q = (txt || "").toLowerCase()
						results.value = roster
							.filter(
								(e) =>
									!q ||
									`${e.employee} ${e.employee_name || ""}`
										.toLowerCase()
										.includes(q),
							)
							.slice(0, 20)
							.map((e) => ({ value: e.employee, description: e.employee_name }))
					} else {
						results.value = []
					}
					open.value = results.value.length > 0
					return
				}

				const params = {
					txt: txt || "",
					doctype: props.doctype,
					ignore_user_permissions: 0,
					reference_doctype: "Daily Payment",
					page_length: 20,
				}
				if (props.query) params.query = props.query
				if (props.filters) params.filters = JSON.stringify(props.filters)
				const res = await call("frappe.desk.search.search_link", params)
				results.value = res || []
				open.value = results.value.length > 0
			} catch {
				results.value = []
				open.value = false
			} finally {
				searching.value = false
			}
		}

		function onInput(e) {
			inputVal.value = e.target.value
			emit("update:modelValue", inputVal.value)
			clearTimeout(debounce)
			debounce = setTimeout(() => search(inputVal.value), 300)
		}

		function select(item) {
			inputVal.value = item.value
			emit("update:modelValue", item.value)
			emit("select", item.value)
			open.value = false
			results.value = []
		}

		function onBlur() {
			setTimeout(() => { open.value = false }, 200)
		}

		const inputClass = computed(() =>
			props.size === "sm"
				? "w-full px-2 py-1.5 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-green-400"
				: "w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
		)

		return () =>
			h("div", { class: "relative" }, [
				h("input", {
					value: inputVal.value,
					placeholder: props.placeholder,
					autocomplete: "off",
					class: inputClass.value,
					onInput,
					onBlur,
					onFocus: () => { search('') },
				}),
				searching.value
					? h("div", { class: "absolute end-2 top-1/2 -translate-y-1/2" },
						h("svg", { class: "w-4 h-4 animate-spin text-gray-400", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24" },
							h("path", { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: "M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" })
						)
					)
					: null,
				open.value
					? h("div", {
						class: "absolute top-full start-0 end-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-[500] max-h-48 overflow-y-auto",
					},
						results.value.map((item) =>
							h("div", {
								key: item.value,
								class: "px-3 py-2 text-sm text-gray-800 hover:bg-green-50 cursor-pointer border-b border-gray-100 last:border-0",
								onMousedown: (e) => { e.preventDefault(); select(item) },
							}, [
								h("div", { class: "font-medium" }, item.value),
								item.description ? h("div", { class: "text-xs text-gray-400 truncate" }, item.description) : null,
							])
						)
					)
					: null,
			])
	},
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
.slide-down-enter-active,
.slide-down-leave-active {
	transition: all 0.25s ease;
	overflow: hidden;
}
.slide-down-enter-from,
.slide-down-leave-to {
	opacity: 0;
	max-height: 0;
	transform: translateY(-8px);
}
.slide-down-enter-to,
.slide-down-leave-from {
	opacity: 1;
	max-height: 600px;
}
</style>
