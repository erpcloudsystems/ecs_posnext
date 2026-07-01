<template>
	<Dialog v-model="show" :options="{ size: '5xl' }">
		<template #body-content>
			<div class="flex flex-col gap-6 -mt-4">
				<!-- Header with Icon (Mockup Style) -->
				<div class="flex items-start gap-4 mb-2">
					<div class="w-12 h-12 rounded-2xl bg-cyan-50 flex items-center justify-center flex-shrink-0">
						<svg class="w-6 h-6 text-cyan-500" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd" />
						</svg>
					</div>
					<div class="flex-1 text-start">
						<h3 class="text-xl font-bold text-gray-900 leading-tight">
							{{ __("Create Customer") }}
						</h3>
						<p class="text-sm text-gray-500 mt-1">
							{{ __("Keep customer records sharp while staying on the sale.") }}
						</p>
					</div>
				</div>

				<!-- Separator -->
				<div class="h-px bg-gray-100 w-full"></div>

				<!-- Form Fields -->
				<div class="grid grid-cols-12 gap-5">
					<!-- Customer Name (Full Width) -->
					<div class="col-span-12">
						<input
							v-model="customerData.customer_name"
							type="text"
							:placeholder="__('Customer Name *')"
							class="w-full px-4 py-3 bg-gray-50 border-0 rounded-xl text-sm focus:ring-2 focus:ring-cyan-500 transition-all"
							required
						/>
					</div>

					<!-- Row: Mobile, Other Mobile, Gender -->
					<div class="col-span-12 sm:col-span-4">
						<div class="flex gap-1.5">
							<button
								type="button"
								@click="showCountryDropdown = !showCountryDropdown"
								class="flex items-center justify-center w-12 h-11 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors flex-shrink-0"
							>
								<img
									:src="`https://flagcdn.com/h24/${currentCountryCode}.png`"
									class="w-5 h-auto rounded-sm"
								/>
							</button>
							<input
								v-model="phoneNumber"
								type="tel"
								:placeholder="__('Mobile No *')"
								class="flex-1 min-w-0 px-4 py-3 bg-gray-50 border-0 rounded-xl text-sm focus:ring-2 focus:ring-cyan-500 transition-all"
								@input="updateMobileNumber"
							/>
						</div>
					</div>

					<div class="col-span-12 sm:col-span-4">
						<input
							v-model="customerData.custom_other_mobile_no"
							type="text"
							:placeholder="__('Other Mobile No')"
							class="w-full px-4 py-3 bg-gray-50 border-0 rounded-xl text-sm focus:ring-2 focus:ring-cyan-500 transition-all"
						/>
					</div>

					<div class="col-span-12 sm:col-span-4">
						<select
							v-model="customerData.gender"
							class="w-full h-11 px-4 bg-gray-50 border-0 rounded-xl text-sm focus:ring-2 focus:ring-cyan-500 transition-all appearance-none"
							style="background-image: url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23666%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E'); background-repeat: no-repeat; background-position: right 1rem center; background-size: 0.65rem auto;"
						>
							<option value="">{{ __("Gender") }}</option>
							<option value="Male">{{ __("Male") }}</option>
							<option value="Female">{{ __("Female") }}</option>
						</select>
					</div>

					<!-- Row: Birthday -->
					<div class="col-span-12">
						<input
							v-model="customerData.birthday"
							type="text"
							onfocus="(this.type='date')"
							onblur="(this.type='text')"
							:placeholder="__('Birthday')"
							class="w-full px-4 py-3 bg-gray-50 border-0 rounded-xl text-sm focus:ring-2 focus:ring-cyan-500 transition-all"
						/>
					</div>

					<!-- Delivery Address (Call Center + Delivery only) -->
					<template v-if="showAddressFields">
						<div class="col-span-12">
							<div class="h-px bg-gray-100 w-full my-1"></div>
							<p class="text-xs font-bold text-cyan-600 uppercase tracking-wide mt-2 mb-1">{{ __("Delivery Address") }}</p>
						</div>
						<!-- City -->
						<div class="col-span-12 sm:col-span-6">
							<select
								v-model="addressData.city"
								class="w-full h-11 px-4 bg-gray-50 border-0 rounded-xl text-sm focus:ring-2 focus:ring-cyan-500 transition-all appearance-none"
							>
								<option value="">{{ __("City *") }}</option>
								<option v-for="c in addressCities" :key="c.name" :value="c.name">{{ c.territory_name || c.name }}</option>
							</select>
						</div>
						<!-- Zone (searchable) -->
						<div class="col-span-12 sm:col-span-6 relative" ref="zoneDropdownRef">
							<input
								v-model="zoneSearch"
								type="text"
								:placeholder="loadingAddressZones ? __('Loading...') : !addressData.city ? __('Select city first') : __('Search zone...')"
								:disabled="!addressData.city || loadingAddressZones"
								@focus="zoneOpen = true"
								@input="zoneOpen = true; addressData.territory = ''"
								class="w-full px-4 py-3 bg-gray-50 border-0 rounded-xl text-sm focus:ring-2 focus:ring-cyan-500 transition-all disabled:opacity-50"
								autocomplete="off"
							/>
							<!-- Dropdown -->
							<div
								v-if="zoneOpen && filteredZones.length > 0"
								class="absolute z-50 top-full mt-1 w-full bg-white rounded-xl shadow-lg border border-gray-100 max-h-48 overflow-y-auto"
							>
								<button
									v-for="z in filteredZones"
									:key="z.name"
									type="button"
									@mousedown.prevent="selectZone(z)"
									class="w-full text-start px-4 py-2.5 text-sm hover:bg-cyan-50 hover:text-cyan-700 transition-colors"
									:class="addressData.territory === z.name ? 'bg-cyan-50 text-cyan-700 font-semibold' : 'text-gray-700'"
								>
									{{ z.territory_name || z.name }}
								</button>
							</div>
						</div>
						<!-- Street -->
						<div class="col-span-12">
							<input
								v-model="addressData.custom_street"
								type="text"
								:placeholder="__('Street *')"
								class="w-full px-4 py-3 bg-gray-50 border-0 rounded-xl text-sm focus:ring-2 focus:ring-cyan-500 transition-all"
							/>
						</div>
						<!-- Building / Floor / Apartment -->
						<div class="col-span-12 sm:col-span-4">
							<input v-model="addressData.custom_building_name" type="text" :placeholder="__('Building')" class="w-full px-4 py-3 bg-gray-50 border-0 rounded-xl text-sm focus:ring-2 focus:ring-cyan-500 transition-all"/>
						</div>
						<div class="col-span-12 sm:col-span-4">
							<input v-model="addressData.custom_floor" type="text" :placeholder="__('Floor')" class="w-full px-4 py-3 bg-gray-50 border-0 rounded-xl text-sm focus:ring-2 focus:ring-cyan-500 transition-all"/>
						</div>
						<div class="col-span-12 sm:col-span-4">
							<input v-model="addressData.custom_apartment" type="text" :placeholder="__('Apartment')" class="w-full px-4 py-3 bg-gray-50 border-0 rounded-xl text-sm focus:ring-2 focus:ring-cyan-500 transition-all"/>
						</div>
						<!-- Landmark -->
						<div class="col-span-12">
							<input v-model="addressData.custom_mark" type="text" :placeholder="__('Landmark')" class="w-full px-4 py-3 bg-gray-50 border-0 rounded-xl text-sm focus:ring-2 focus:ring-cyan-500 transition-all"/>
						</div>
					</template>
				</div>
			</div>
		</template>

		<template #actions>
			<div class="flex items-center justify-end gap-3 w-full mt-2">
				<button
					@click="show = false"
					class="px-6 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 transition-colors"
				>
					{{ __("Close") }}
				</button>
				<button
					@click="handleCreate"
					:disabled="!customerData.customer_name || !hasPermission"
					class="px-8 py-2.5 bg-cyan-500 hover:bg-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-all shadow-lg shadow-cyan-100"
				>
					<span v-if="createCustomerResource.loading || updateCustomerResource.loading" class="flex items-center gap-2">
						<div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
						{{ __("Submitting...") }}
					</span>
					<span v-else>{{ __("Submit") }}</span>
				</button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
/**
 * CreateCustomerDialog - Quick customer creation from POS
 *
 * Features:
 * - Country code selector with flag icons and search
 * - Auto-sets territory based on selected country
 * - Permission checking before allowing creation
 * - Lazy loads countries data when dialog opens (not on app startup)
 */

import { usePOSPermissions } from "@/composables/usePermissions"
import { useToast } from "@/composables/useToast"
import { useCountriesStore } from "@/stores/countries"
import { usePOSCartStore } from "@/stores/posCart"
import { usePOSShiftStore } from "@/stores/posShift"
import { logger } from "@/utils/logger"
import { call } from "@/utils/apiWrapper"
import { Button, Dialog, Input, createResource } from "frappe-ui"
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"

const log = logger.create("CreateCustomerDialog")

// =============================================================================
// Composables & Stores
// =============================================================================

const countriesStore = useCountriesStore()
const cartStore = usePOSCartStore()
const shiftStore = usePOSShiftStore()
const { canCreateCustomer } = usePOSPermissions()
const { showSuccess, showError } = useToast()

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
const selectedCountryCode = ref("")
const phoneNumber = ref("")
const showCountryDropdown = ref(false)
const countrySearchQuery = ref("")
const dropdownRef = ref(null)
const countrySearchRef = ref(null)

const customerGroups = ref(["Commercial", "Individual", "Non Profit", "Government"])
const territories = ref(["All Territories"])

const customerData = ref({
	customer_name: "",
	mobile_no: "",
	email_id: "",
	customer_group: "Individual",
	territory: "Egypt",
	custom_other_mobile_no: "",
	gender: "",
	birthday: "",
})

// Delivery address state (for Call Center + Delivery orders)
const addressData = ref({
	city: "",
	territory: "",
	custom_street: "",
	custom_building_name: "",
	custom_floor: "",
	custom_apartment: "",
	custom_mark: "",
})
const addressCities = ref([])
const addressZones = ref([])
const loadingAddressZones = ref(false)
const zoneSearch = ref("")
const zoneOpen = ref(false)
const zoneDropdownRef = ref(null)

const filteredZones = computed(() => {
	const q = zoneSearch.value.trim().toLowerCase()
	if (!q) return addressZones.value
	return addressZones.value.filter(z =>
		(z.territory_name || z.name).toLowerCase().includes(q)
	)
})

function selectZone(z) {
	addressData.value.territory = z.name
	zoneSearch.value = z.territory_name || z.name
	zoneOpen.value = false
}

function closeZoneDropdown(e) {
	if (zoneDropdownRef.value && !zoneDropdownRef.value.contains(e.target)) {
		zoneOpen.value = false
	}
}

// =============================================================================
// Computed
// =============================================================================

const showAddressFields = computed(() =>
	cartStore.orderType === "Delivery" &&
	(props.posProfile || "").toLowerCase().includes("call center")
)

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit("update:modelValue", val),
})

const isEditMode = computed(() => !!props.customer?.name)

const currentCountryCode = computed(() => {
	const country = countriesStore.countries.find((c) => c.isd === selectedCountryCode.value)
	return country?.code.toLowerCase() || "eg"
})

const filteredCountries = computed(() => {
	if (!countrySearchQuery.value) return countriesStore.countries

	const query = countrySearchQuery.value.toLowerCase()
	return countriesStore.countries.filter(
		(c) => c.name.toLowerCase().includes(query) || c.isd.includes(query) || c.code.toLowerCase().includes(query)
	)
})

// =============================================================================
// Country & Territory Methods
// =============================================================================

const handleFlagError = (e) => (e.target.style.display = "none")

const selectCountry = (country) => {
	selectedCountryCode.value = country.isd
	showCountryDropdown.value = false
	countrySearchQuery.value = ""
	updateMobileNumber()
}

const updateMobileNumber = () => {
	customerData.value.mobile_no = phoneNumber.value ? `${selectedCountryCode.value}-${phoneNumber.value}` : ""
}

const handleClickOutside = (event) => {
	if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
		showCountryDropdown.value = false
		countrySearchQuery.value = ""
	}
}

const setCountryFromName = (countryName) => {
	if (!countryName) {
		selectedCountryCode.value = "+20"
		return
	}

	const isd = countriesStore.countryNameToISDMap[countryName]
	if (isd) {
		selectedCountryCode.value = isd
		log.info(`Set country code to ${isd} for ${countryName}`)
	} else {
		log.warn(`Country "${countryName}" not found`)
		selectedCountryCode.value = "+20"
	}
}

/** Auto-set territory based on selected country (exact or fuzzy match) */
const updateTerritoryFromCountry = () => {
	if (!territories.value.length) return

	const country = countriesStore.countries.find((c) => c.isd === selectedCountryCode.value)
	if (!country) return

	// Try exact match first
	if (territories.value.includes(country.name)) {
		customerData.value.territory = country.name
		log.info(`Territory set to: ${country.name}`)
		return
	}

	// Try fuzzy match
	const fuzzyMatch = territories.value.find(
		(t) => t.toLowerCase().includes(country.name.toLowerCase()) || country.name.toLowerCase().includes(t.toLowerCase())
	)

	if (fuzzyMatch) {
		customerData.value.territory = fuzzyMatch
		log.info(`Territory set to fuzzy match: ${fuzzyMatch}`)
	}
}

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
			customer_group: customerData.value.customer_group || "Individual",
			territory: customerData.value.territory || "Egypt",
			mobile_no: customerData.value.mobile_no || "",
			email_id: customerData.value.email_id || "",
			custom_other_mobile_no: customerData.value.custom_other_mobile_no || "",
			gender: customerData.value.gender || "",
			birthday: customerData.value.birthday || null,
		},
	}),
	onSuccess: async (data) => {
		showSuccess(__("Customer {0} created successfully", [data.customer_name]))
		window.frappe?.show_alert?.({ message: __("Customer {0} created successfully", [data.customer_name]), indicator: "green" }, 5)
		emit("customer-created", data)

		// Create delivery address when Call Center + Delivery order
		if (showAddressFields.value && addressData.value.custom_street && data.name) {
			try {
				const addrParts = [
					addressData.value.custom_street,
					addressData.value.custom_building_name,
					addressData.value.custom_floor ? `Floor ${addressData.value.custom_floor}` : "",
					addressData.value.custom_apartment ? `Apt ${addressData.value.custom_apartment}` : "",
				].filter(Boolean)
				const addressLine1 = addrParts.join(", ")

				await call("frappe.client.insert", {
					doc: {
						doctype: "Address",
						address_title: data.customer_name,
						address_type: "Shipping",
						address_line1: addressLine1,
						address_line2: addressData.value.custom_mark || "",
						city: addressData.value.city,
						territory: addressData.value.territory,
						custom_street: addressData.value.custom_street,
						custom_building_name: addressData.value.custom_building_name || "",
						custom_floor: addressData.value.custom_floor || "",
						custom_apartment: addressData.value.custom_apartment || "",
						custom_mark: addressData.value.custom_mark || "",
						is_primary_address: 1,
						is_shipping_address: 1,
						links: [{ link_doctype: "Customer", link_name: data.name }],
					},
				})
			} catch (e) {
				log.error("Error creating delivery address", e)
				showError(__("Customer created but address could not be saved"))
			}
		}

		show.value = false
	},
	onError: (error) => {
		log.error("Error creating customer", error)
		showError(error.message || __("Failed to create customer"))
	},
})

const updateCustomerResource = createResource({
	url: "frappe.client.set_value",
	makeParams: () => ({
		doctype: "Customer",
		name: props.customer?.name,
		fieldname: {
			customer_name: customerData.value.customer_name,
			customer_group: customerData.value.customer_group || "Individual",
			territory: customerData.value.territory || "Egypt",
			mobile_no: customerData.value.mobile_no || "",
			email_id: customerData.value.email_id || "",
			custom_other_mobile_no: customerData.value.custom_other_mobile_no || "",
			gender: customerData.value.gender || "",
			birthday: customerData.value.birthday || null,
		},
	}),
	onSuccess: (data) => {
		showSuccess(__("Customer {0} updated successfully", [data.customer_name]))
		emit("customer-updated", data)
		show.value = false
	},
	onError: (error) => {
		log.error("Error updating customer", error)
		showError(error.message || __("Failed to update customer"))
	},
})

/** Helper to create list fetch resources */
const createListResource = (doctype, onSuccess) =>
	createResource({
		url: "frappe.client.get_list",
		makeParams: () => ({
			doctype,
			fields: ["name"],
			filters: doctype === "Customer Group" ? { is_group: 0 } : {},
			limit_page_length: 500,
		}),
		auto: false,
		onSuccess: (data) => data?.length && onSuccess(data.map((d) => d.name)),
		onError: (err) => log.error(`Error loading ${doctype}`, err),
	})

const customerGroupsResource = createListResource("Customer Group", (names) => (customerGroups.value = names))
const territoriesResource = createListResource("Territory", (names) => (territories.value = names))

const posProfileResource = createResource({
	url: "frappe.client.get_value",
	makeParams: () => ({
		doctype: "POS Profile",
		filters: { name: props.posProfile },
		fieldname: ["country"],
	}),
	auto: false,
	onSuccess: (data) => setCountryFromName(data?.country || "Egypt"),
	onError: (err) => {
		log.error("Error loading POS Profile", err)
		selectedCountryCode.value = "+20"
	},
})

// =============================================================================
// Dialog Lifecycle
// =============================================================================

const loadDialogData = async () => {
	// Lazy load countries (non-blocking)
	countriesStore.loadCountries()

	// Load form options
	await territoriesResource.reload()
	customerGroupsResource.reload()
	checkPermissions()

	// Set country from POS Profile
	if (props.posProfile) {
		await posProfileResource.reload()
	} else {
		selectedCountryCode.value = "+20"
	}
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

const handleCreate = async () => {
	if (!customerData.value.customer_name) {
		return showError(__("Customer Name is required"))
	}
	if (isEditMode.value) {
		await updateCustomerResource.submit()
	} else {
		await createCustomerResource.submit()
	}
}

const resetForm = () => {
	Object.assign(customerData.value, {
		customer_name: "",
		mobile_no: "",
		email_id: "",
		customer_group: "Individual",
		territory: "Egypt",
		custom_other_mobile_no: "",
		gender: "",
		birthday: "",
	})
	selectedCountryCode.value = ""
	phoneNumber.value = ""
	resetAddressData()
}

// =============================================================================
// Address helpers (Call Center + Delivery)
// =============================================================================

async function loadAddressCities() {
	try {
		const res = await call("ecs_posnext.api.customers.get_parent_territories")
		addressCities.value = res || []
	} catch (e) {
		log.error("Error loading address cities", e)
	}
}

async function loadAddressZones(city) {
	if (!city) { addressZones.value = []; return }
	loadingAddressZones.value = true
	try {
		const res = await call("ecs_posnext.api.customers.get_child_territories", {
			parent_territory: city,
		})
		addressZones.value = res || []
	} catch (e) {
		log.error("Error loading address zones", e)
	} finally {
		loadingAddressZones.value = false
	}
}

function resetAddressData() {
	Object.assign(addressData.value, {
		city: "", territory: "", custom_street: "", custom_building_name: "",
		custom_floor: "", custom_apartment: "", custom_mark: "",
	})
	addressCities.value = []
	addressZones.value = []
	zoneSearch.value = ""
	zoneOpen.value = false
}

// =============================================================================
// Watchers
// =============================================================================

watch(
	() => props.initialName,
	(name) => name && (customerData.value.customer_name = name)
)

// Load cities when the delivery address section becomes visible
watch(showAddressFields, async (val) => {
	if (val && !addressCities.value.length) await loadAddressCities()
	if (!val) resetAddressData()
}, { immediate: true })

// Load zones when city is selected
watch(() => addressData.value.city, (city) => {
	addressData.value.territory = ""
	zoneSearch.value = ""
	loadAddressZones(city)
})

// Pre-fill form when customer prop changes (edit mode)
watch(
	() => props.customer,
	(customer) => {
		if (customer?.name) {
			customerData.value.customer_name = customer.customer_name || ""
			customerData.value.email_id = customer.email_id || ""
			customerData.value.customer_group = customer.customer_group || "Individual"
			customerData.value.territory = customer.territory || "Egypt"
			customerData.value.custom_other_mobile_no = customer.custom_other_mobile_no || ""
			customerData.value.gender = customer.gender || ""
			customerData.value.birthday = customer.birthday || ""
			// Handle mobile_no with country code
			if (customer.mobile_no) {
				customerData.value.mobile_no = customer.mobile_no
				if (customer.mobile_no.includes("-")) {
					const [code, ...rest] = customer.mobile_no.split("-")
					selectedCountryCode.value = code
					phoneNumber.value = rest.join("-")
				} else {
					phoneNumber.value = customer.mobile_no
				}
			}
		}
	},
	{ immediate: true }
)

watch(
	() => customerData.value.mobile_no,
	(value) => {
		if (value?.includes("-")) {
			const [code, ...rest] = value.split("-")
			selectedCountryCode.value = code
			phoneNumber.value = rest.join("-")
		}
	}
)

watch(selectedCountryCode, async () => {
	await nextTick()
	updateTerritoryFromCountry()
})

watch(showCountryDropdown, async (isOpen) => {
	if (isOpen) {
		await nextTick()
		countrySearchRef.value?.focus()
	}
})

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
	document.addEventListener("click", handleClickOutside)
	document.addEventListener("click", closeZoneDropdown)
})

onBeforeUnmount(() => {
	document.removeEventListener("click", handleClickOutside)
	document.removeEventListener("click", closeZoneDropdown)
})
</script>

<style scoped>
.sr-only {
	position: absolute;
	width: 1px;
	height: 1px;
	padding: 0;
	margin: -1px;
	overflow: hidden;
	clip: rect(0, 0, 0, 0);
	white-space: nowrap;
	border-width: 0;
}
</style>
