<template>
	<Dialog v-model="show" :options="{ title: isEditMode ? __('Edit Customer') : __('Create New Customer'), size: 'md' }">
		<template #body-content>
			<div class="flex flex-col gap-5">
				<!-- Customer Name (Required) -->
				<div>
					<label class="block text-start text-sm font-medium text-gray-700 mb-2">
						{{ __("Customer Name") }} <span class="text-red-500">*</span>
					</label>
					<Input
						v-model="customerData.customer_name"
						type="text"
						:placeholder="__('Enter customer name')"
						required
					/>
				</div>

				<!-- Row: Mobile No, Other Mobile No, Gender -->
				<div class="grid grid-cols-3 gap-3">
					<!-- Mobile Number (Required) -->
					<div>
						<label class="block text-start text-sm font-medium text-gray-700 mb-2">
							{{ __("Mobile No") }} <span class="text-red-500">*</span>
						</label>
						<input
							v-model="customerData.mobile_no"
							type="tel"
							:placeholder="__('Mobile No')"
							required
							class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>

					<!-- Other Mobile No (Optional) -->
					<div>
						<label class="block text-start text-sm font-medium text-gray-700 mb-2">
							{{ __("Other Mobile No") }}
						</label>
						<input
							v-model="customerData.custom_other_mobile_no"
							type="tel"
							:placeholder="__('Other Mobile No')"
							class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>

					<!-- Gender (Optional) -->
					<div>
						<label class="block text-start text-sm font-medium text-gray-700 mb-2">
							{{ __("Gender") }}
						</label>
						<select
							v-model="customerData.gender"
							class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
						>
							<option value="">{{ __("Gender") }}</option>
							<option value="Male">{{ __("Male") }}</option>
							<option value="Female">{{ __("Female") }}</option>
							<option value="Other">{{ __("Other") }}</option>
							<option value="Prefer not to say">{{ __("Prefer not to say") }}</option>
						</select>
					</div>
				</div>

				<!-- Row: Birthday, Customer Group -->
				<div class="grid grid-cols-2 gap-3">
					<!-- Birthday (Optional) -->
					<div>
						<label class="block text-start text-sm font-medium text-gray-700 mb-2">
							{{ __("Birthday") }}
						</label>
						<Input
							v-model="customerData.custom_birthday"
							type="date"
							:placeholder="__('Birthday')"
						/>
					</div>

					<!-- Customer Group (Required) -->
					<div>
						<label class="block text-start text-sm font-medium text-gray-700 mb-2">
							{{ __("Customer Group") }} <span class="text-red-500">*</span>
						</label>
						<select
							v-model="customerData.customer_group"
							class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
						>
							<option value="">{{ __("Select Customer Group") }}</option>
							<option v-for="group in customerGroups" :key="group" :value="group">
								{{ group }}
							</option>
						</select>
					</div>
				</div>
			</div>
		</template>

		<template #actions>
			<div class="flex flex-col gap-2">
				<!-- Permission Warning -->
				<div v-if="!hasPermission" class="px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg">
					<div class="flex items-start gap-2">
						<svg class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
							<path
								fill-rule="evenodd"
								d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
								clip-rule="evenodd"
							/>
						</svg>
						<div class="flex-1">
							<p class="text-sm font-medium text-amber-900">{{ __("Permission Required") }}</p>
							<p class="text-xs text-amber-700 mt-0.5">
								{{ __("You don't have permission to create customers. Contact your administrator.") }}
							</p>
						</div>
					</div>
				</div>

				<div class="flex gap-2">
					<Button
						variant="solid"
						@click="handleCreate"
						:loading="isSubmitting || checkingPermission"
						:disabled="!customerData.customer_name || !customerData.mobile_no || !customerData.customer_group || !hasPermission"
					>
						{{ isEditMode ? __("Save Changes") : __("Submit") }}
					</Button>
					<Button variant="subtle" @click="show = false">
						{{ __("Close") }}
					</Button>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
/**
 * CreateCustomerDialog - Quick customer creation from POS
 *
 * Fields:
 * - customer_name (required)
 * - mobile_no (required, checked for duplicates)
 * - custom_other_mobile_no (optional)
 * - gender (optional select)
 * - custom_birthday (optional date)
 * - customer_group (required, fetched from Customer Group doctype)
 *
 * On submit:
 * 1. Validates required fields
 * 2. Checks duplicate mobile_no
 * 3. Creates Customer doc via frappe.client.insert
 * 4. Emits customer-created so parent sets as active POS customer
 * 5. Shows frappe.show_alert success
 * 6. Errors shown via frappe.msgprint
 */

import { usePOSPermissions } from "@/composables/usePermissions"
import { logger } from "@/utils/logger"
import { Button, Dialog, Input, createResource } from "frappe-ui"
import { computed, onMounted, ref, watch } from "vue"

const log = logger.create("CreateCustomerDialog")

// =============================================================================
// Composables & Stores
// =============================================================================

const { canCreateCustomer } = usePOSPermissions()

// =============================================================================
// Props & Emits
// =============================================================================

const props = defineProps({
	modelValue: Boolean,
	posProfile: String,
	initialName: String,
	customer: Object, // Customer object for edit mode
})

const emit = defineEmits(["update:modelValue", "customer-created", "customer-updated"])

// =============================================================================
// State
// =============================================================================

const hasPermission = ref(true)
const checkingPermission = ref(false)
const isSubmitting = ref(false)

const customerGroups = ref([])

const customerData = ref({
	customer_name: "",
	mobile_no: "",
	custom_other_mobile_no: "",
	gender: "",
	custom_birthday: "",
	customer_group: "",
})

// =============================================================================
// Computed
// =============================================================================

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit("update:modelValue", val),
})

const isEditMode = computed(() => !!props.customer?.name)

// =============================================================================
// API Resources
// =============================================================================

const createCustomerResource = createResource({
	url: "frappe.client.insert",
	makeParams: () => ({
		doc: {
			doctype: "Customer",
			customer_name: customerData.value.customer_name,
			customer_type: "Individual",
			customer_group: customerData.value.customer_group,
			mobile_no: customerData.value.mobile_no,
			gender: customerData.value.gender || undefined,
			custom_other_mobile_no: customerData.value.custom_other_mobile_no || undefined,
			custom_birthday: customerData.value.custom_birthday || undefined,
		},
	}),
	onSuccess: (data) => {
		frappe.show_alert({
			message: __("Customer {0} created successfully", [data.customer_name]),
			indicator: "green",
		})
		emit("customer-created", data)
		show.value = false
	},
	onError: (error) => {
		log.error("Error creating customer", error)
		frappe.msgprint({
			title: __("Error"),
			message: error.message || __("Failed to create customer"),
			indicator: "red",
		})
	},
})

const updateCustomerResource = createResource({
	url: "frappe.client.set_value",
	makeParams: () => ({
		doctype: "Customer",
		name: props.customer?.name,
		fieldname: {
			customer_name: customerData.value.customer_name,
			customer_group: customerData.value.customer_group,
			mobile_no: customerData.value.mobile_no,
			gender: customerData.value.gender || "",
			custom_other_mobile_no: customerData.value.custom_other_mobile_no || "",
			custom_birthday: customerData.value.custom_birthday || "",
		},
	}),
	onSuccess: (data) => {
		frappe.show_alert({
			message: __("Customer {0} updated successfully", [data.customer_name]),
			indicator: "green",
		})
		emit("customer-updated", data)
		show.value = false
	},
	onError: (error) => {
		log.error("Error updating customer", error)
		frappe.msgprint({
			title: __("Error"),
			message: error.message || __("Failed to update customer"),
			indicator: "red",
		})
	},
})

/** Fetch customer groups (non-group nodes only) */
const customerGroupsResource = createResource({
	url: "frappe.client.get_list",
	makeParams: () => ({
		doctype: "Customer Group",
		fields: ["name"],
		filters: { is_group: 0 },
		limit_page_length: 500,
	}),
	auto: false,
	onSuccess: (data) => {
		if (data?.length) {
			customerGroups.value = data.map((d) => d.name)
		}
	},
	onError: (err) => log.error("Error loading Customer Groups", err),
})

// =============================================================================
// Validation & Duplicate Check
// =============================================================================

/**
 * Check if another Customer already has the same mobile_no.
 * Returns true if a duplicate exists, false otherwise.
 */
const checkDuplicateMobile = async (mobileNo) => {
	try {
		const filters = { mobile_no: mobileNo }
		// In edit mode, exclude the current customer
		if (isEditMode.value && props.customer?.name) {
			filters.name = ["!=", props.customer.name]
		}
		const result = await frappe.call({
			method: "frappe.client.get_count",
			args: {
				doctype: "Customer",
				filters,
			},
		})
		return (result?.message || 0) > 0
	} catch (err) {
		log.error("Duplicate check failed", err)
		return false
	}
}

const handleCreate = async () => {
	// 1. Validate required fields
	if (!customerData.value.customer_name?.trim()) {
		frappe.msgprint({
			title: __("Validation Error"),
			message: __("Customer Name is required"),
			indicator: "orange",
		})
		return
	}
	if (!customerData.value.mobile_no?.trim()) {
		frappe.msgprint({
			title: __("Validation Error"),
			message: __("Mobile No is required"),
			indicator: "orange",
		})
		return
	}
	if (!customerData.value.customer_group) {
		frappe.msgprint({
			title: __("Validation Error"),
			message: __("Customer Group is required"),
			indicator: "orange",
		})
		return
	}

	isSubmitting.value = true
	try {
		// 2. Check duplicate mobile_no
		const isDuplicate = await checkDuplicateMobile(customerData.value.mobile_no.trim())
		if (isDuplicate) {
			frappe.msgprint({
				title: __("Duplicate Mobile No"),
				message: __("Another customer already has the mobile number {0}", [customerData.value.mobile_no]),
				indicator: "red",
			})
			return
		}

		// 3. Create or update
		if (isEditMode.value) {
			await updateCustomerResource.submit()
		} else {
			await createCustomerResource.submit()
		}
	} catch (err) {
		log.error("handleCreate error", err)
		frappe.msgprint({
			title: __("Error"),
			message: err.message || __("An unexpected error occurred"),
			indicator: "red",
		})
	} finally {
		isSubmitting.value = false
	}
}

// =============================================================================
// Dialog Lifecycle
// =============================================================================

const loadDialogData = async () => {
	customerGroupsResource.reload()
	checkPermissions()
}

const checkPermissions = async () => {
	checkingPermission.value = true
	try {
		hasPermission.value = await canCreateCustomer()
	} catch (err) {
		log.error("Permission check failed", err)
		hasPermission.value = false
	} finally {
		checkingPermission.value = false
	}
}

const resetForm = () => {
	Object.assign(customerData.value, {
		customer_name: "",
		mobile_no: "",
		custom_other_mobile_no: "",
		gender: "",
		custom_birthday: "",
		customer_group: "",
	})
}

// =============================================================================
// Watchers
// =============================================================================

watch(
	() => props.initialName,
	(name) => name && (customerData.value.customer_name = name)
)

// Pre-fill form when customer prop changes (edit mode)
watch(
	() => props.customer,
	(customer) => {
		if (customer?.name) {
			customerData.value.customer_name = customer.customer_name || ""
			customerData.value.mobile_no = customer.mobile_no || ""
			customerData.value.custom_other_mobile_no = customer.custom_other_mobile_no || ""
			customerData.value.gender = customer.gender || ""
			customerData.value.custom_birthday = customer.custom_birthday || ""
			customerData.value.customer_group = customer.customer_group || ""
		}
	},
	{ immediate: true }
)

watch(
	() => props.modelValue,
	async (isOpen) => {
		show.value = isOpen
		isOpen ? await loadDialogData() : resetForm()
	}
)

watch(show, (val) => emit("update:modelValue", val))

// =============================================================================
// Lifecycle Hooks
// =============================================================================

onMounted(() => {
	loadDialogData()
})
</script>
