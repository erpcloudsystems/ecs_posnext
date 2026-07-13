<template>
	<Dialog v-model="show" :options="{ title: __('Select Delivery Address'), size: '3xl' }">
		<template #body-content>
			<div class="space-y-4 py-2">
				<div v-if="loading" class="flex items-center justify-center py-12">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
				</div>

				<div v-else-if="addresses.length === 0" class="flex flex-col items-center justify-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-200">
					<div class="w-16 h-16 bg-white rounded-full shadow-sm flex items-center justify-center mb-4">
						<svg class="w-8 h-8 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
						</svg>
					</div>
					<p class="text-sm font-medium text-gray-900 mb-1">{{ __("No addresses found") }}</p>
					<p class="text-xs text-gray-500 mb-6 text-center px-6">{{ __("This customer doesn't have any delivery addresses yet.") }}</p>
					<button
						type="button"
						@click="showAddDialog = true"
						class="px-4 py-2 bg-blue-600 text-white text-sm font-bold rounded-xl hover:bg-blue-700 transition-all shadow-sm active:scale-95"
					>
						{{ __("+ Add New Address") }}
					</button>
				</div>

				<div v-else class="space-y-3">
					<div class="flex items-center justify-between px-1">
						<p class="text-xs font-bold text-gray-500 uppercase tracking-wider">{{ __("Saved Addresses") }}</p>
						<button
							type="button"
							@click="showAddDialog = true"
							class="text-xs font-bold text-blue-600 hover:text-blue-700"
						>
							{{ __("+ Add New") }}
						</button>
					</div>
					
					<div class="grid grid-cols-1 gap-2.5 max-h-[60vh] overflow-y-auto pr-1 custom-scrollbar">
						<div
							v-for="addr in addresses"
							:key="addr.name"
							class="relative rounded-xl border transition-all duration-200 group"
							:class="selectedAddress === addr.name
								? 'bg-blue-50 border-blue-500 ring-1 ring-blue-500 shadow-sm'
								: 'bg-white border-gray-200 hover:border-blue-300 hover:bg-gray-50'"
						>
							<button
								type="button"
								@click="selectAddress(addr)"
								class="text-start w-full p-3.5 pr-10"
							>
								<div class="flex items-start gap-3">
									<div
										class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5"
										:class="selectedAddress === addr.name ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-400 group-hover:bg-blue-50 group-hover:text-blue-500'"
									>
										<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
										</svg>
									</div>
									<div class="flex-1 min-w-0">
										<div class="flex items-center gap-2 mb-1">
											<p class="text-sm font-bold text-gray-900 truncate">
												{{ addr.address_title || addr.name }}
											</p>
											<span v-if="addr.is_primary_address" class="px-1.5 py-0.5 bg-blue-100 text-blue-700 text-[9px] font-bold rounded uppercase tracking-tighter">
												{{ __("Primary") }}
											</span>
										</div>
										<div class="text-xs text-gray-500 leading-relaxed line-clamp-2" v-html="addr.address_display">
										</div>
									</div>
									<div v-if="selectedAddress === addr.name" class="flex-shrink-0 mt-2">
										<div class="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center">
											<svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
											</svg>
										</div>
									</div>
								</div>
							</button>
							<!-- Edit button -->
							<button
								type="button"
								@click.stop="openEditDialog(addr)"
								class="absolute top-2.5 right-2.5 w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
								:title="__('Edit address')"
							>
								<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
								</svg>
							</button>
						</div>
					</div>
				</div>
			</div>
		</template>
		<template #actions>
			<div class="flex gap-2 w-full">
				<Button variant="subtle" class="flex-1" @click="show = false">
					{{ __("Close") }}
				</Button>
			</div>
		</template>
	</Dialog>

	<!-- Edit Address Dialog -->
	<Dialog v-model="showEditDialog" :options="{ title: __('Edit Address'), size: 'md' }">
		<template #body-content>
			<div class="space-y-5 py-2">
				<div class="grid grid-cols-2 gap-4">
					<div class="col-span-2">
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("Address Title") }} <span class="text-red-500">*</span></label>
						<Input v-model="editAddress.address_title" :placeholder="__('e.g. Home, Office, Apartment 4B')" />
					</div>
					<div class="col-span-2">
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("City") }} <span class="text-red-500">*</span></label>
						<select
							v-model="editAddress.city"
							@change="onEditCityChange"
							class="w-full h-10 px-3 py-2 bg-white border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
						>
							<option value="" disabled>{{ __("Select City") }}</option>
							<option v-for="t in parentTerritories" :key="t.name" :value="t.name">
								{{ t.territory_name || t.name }}
							</option>
						</select>
					</div>
					<div class="col-span-2">
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("Zone") }} <span class="text-red-500">*</span></label>
						<select
							v-model="editAddress.territory"
							:disabled="!editAddress.city || loadingEditZones"
							class="w-full h-10 px-3 py-2 bg-white border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
						>
							<option value="" disabled>{{ loadingEditZones ? __('Loading...') : __('Select Zone') }}</option>
							<option v-for="t in editChildTerritories" :key="t.name" :value="t.name">
								{{ t.territory_name || t.name }}
							</option>
						</select>
					</div>
					<div class="col-span-2">
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("Street") }} <span class="text-red-500">*</span></label>
						<Input v-model="editAddress.custom_street" :placeholder="__('Street name')" />
					</div>
					<div>
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("Building Name") }}</label>
						<Input v-model="editAddress.custom_building_name" :placeholder="__('Building name')" />
					</div>
					<div>
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("Floor") }}</label>
						<Input v-model="editAddress.custom_floor" :placeholder="__('Floor')" />
					</div>
					<div>
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("Apartment") }}</label>
						<Input v-model="editAddress.custom_apartment" :placeholder="__('Apartment')" />
					</div>
					<div>
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("Mark / Landmark") }}</label>
						<Input v-model="editAddress.custom_mark" :placeholder="__('Nearby landmark')" />
					</div>
				</div>
			</div>
		</template>
		<template #actions>
			<div class="flex gap-3 w-full">
				<Button
					variant="solid"
					class="flex-1"
					:loading="saving"
					:disabled="!isEditValid"
					@click="saveEditedAddress"
				>
					{{ __("Save Changes") }}
				</Button>
				<Button variant="subtle" class="flex-1" @click="showEditDialog = false">
					{{ __("Back") }}
				</Button>
			</div>
		</template>
	</Dialog>

	<!-- Add Address Dialog (Nested) -->
	<Dialog v-model="showAddDialog" :options="{ title: __('Add New Address'), size: 'md' }">
		<template #body-content>
			<div class="space-y-5 py-2">
				<div class="grid grid-cols-2 gap-4">
					<div class="col-span-2">
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("Address Title") }} <span class="text-red-500">*</span></label>
						<Input v-model="newAddress.address_title" :placeholder="__('e.g. Home, Office, Apartment 4B')" />
					</div>
					<!-- City: Parent Territory Select -->
					<div class="col-span-2">
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("City") }} <span class="text-red-500">*</span></label>
						<select
							v-model="newAddress.city"
							@change="onCityChange"
							class="w-full h-10 px-3 py-2 bg-white border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
						>
							<option value="" disabled>{{ __("Select City") }}</option>
							<option v-for="t in parentTerritories" :key="t.name" :value="t.name">
								{{ t.territory_name || t.name }}
							</option>
						</select>
					</div>
					<!-- Territory Zone: Child of selected City -->
					<div class="col-span-2">
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("Zone") }} <span class="text-red-500">*</span></label>
						<select
							v-model="newAddress.territory"
							:disabled="!newAddress.city || loadingZones"
							class="w-full h-10 px-3 py-2 bg-white border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
						>
							<option value="" disabled>{{ loadingZones ? __('Loading...') : __('Select Zone') }}</option>
							<option v-for="t in childTerritories" :key="t.name" :value="t.name">
								{{ t.territory_name || t.name }}
							</option>
						</select>
					</div>
					<div class="col-span-2">
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("Street") }} <span class="text-red-500">*</span></label>
						<Input v-model="newAddress.custom_street" :placeholder="__('Street name')" />
					</div>
					<div>
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("Building Name") }}</label>
						<Input v-model="newAddress.custom_building_name" :placeholder="__('Building name')" />
					</div>
					<div>
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("Floor") }}</label>
						<Input v-model="newAddress.custom_floor" :placeholder="__('Floor')" />
					</div>
					<div>
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("Apartment") }}</label>
						<Input v-model="newAddress.custom_apartment" :placeholder="__('Apartment')" />
					</div>
					<div>
						<label class="block text-xs font-bold text-gray-700 mb-2">{{ __("Mark / Landmark") }}</label>
						<Input v-model="newAddress.custom_mark" :placeholder="__('Nearby landmark')" />
					</div>
				</div>
			</div>
		</template>
		<template #actions>
			<div class="flex gap-3 w-full">
				<Button
					variant="solid"
					class="flex-1"
					:loading="adding"
					:disabled="!isValid"
					@click="addNewAddress"
				>
					{{ __("Save Address") }}
				</Button>
				<Button variant="subtle" class="flex-1" @click="showAddDialog = false">
					{{ __("Back") }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { ref, onMounted, computed, watch } from "vue"
import { call } from "@/utils/apiWrapper"
import { Button, Dialog, Input } from "frappe-ui"
import { useToast } from "@/composables/useToast"
import { usePOSShiftStore } from "@/stores/posShift"

const props = defineProps({
	modelValue: Boolean,
	customer: {
		type: String,
		required: true
	},
	selectedAddress: {
		type: String,
		default: null
	}
})

const emit = defineEmits(["update:modelValue", "select"])
const { showSuccess, showError } = useToast()
const shiftStore = usePOSShiftStore()

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit("update:modelValue", val)
})

const addresses = ref([])
const loading = ref(false)
const adding = ref(false)
const saving = ref(false)
const showAddDialog = ref(false)
const showEditDialog = ref(false)

const editAddress = ref({
	name: "",
	address_title: "",
	city: "",
	territory: "",
	custom_street: "",
	custom_building_name: "",
	custom_floor: "",
	custom_apartment: "",
	custom_mark: "",
	country: "Egypt",
})
const editChildTerritories = ref([])
const loadingEditZones = ref(false)

const isEditValid = computed(() =>
	editAddress.value.address_title && editAddress.value.custom_street &&
	editAddress.value.city && editAddress.value.territory
)

const newAddress = ref({
	address_title: "",
	address_line1: "",
	address_line2: "",
	city: "",
	country: "Egypt",
	territory: "",
	custom_street: "",
	custom_building_name: "",
	custom_floor: "",
	custom_apartment: "",
	custom_mark: ""
})

const parentTerritories = ref([])
const childTerritories = ref([])
const loadingZones = ref(false)
const territories = ref([])

const isValid = computed(() => {
	return newAddress.value.address_title && newAddress.value.custom_street && newAddress.value.city && newAddress.value.territory
})

async function fetchParentTerritories() {
	try {
		const res = await call("ecs_posnext.api.customers.get_parent_territories")
		parentTerritories.value = res || []
	} catch (err) {
		console.error("Error fetching parent territories:", err)
	}
}

async function fetchChildTerritories(parentTerritory) {
	if (!parentTerritory) {
		childTerritories.value = []
		return
	}
	loadingZones.value = true
	try {
		const res = await call("ecs_posnext.api.customers.get_child_territories", {
			parent_territory: parentTerritory
		})
		childTerritories.value = res || []
	} catch (err) {
		console.error("Error fetching child territories:", err)
	} finally {
		loadingZones.value = false
	}
}

function onCityChange() {
	newAddress.value.territory = ""
	fetchChildTerritories(newAddress.value.city)
}

async function fetchTerritories() {
	try {
		const res = await call("ecs_posnext.api.customers.get_territories", {
			branch: shiftStore.profileBranch
		})
		territories.value = res || []
	} catch (err) {
		console.error("Error fetching territories:", err)
	}
}

async function fetchAddresses() {
	if (!props.customer) return
	loading.value = true
	try {
		const response = await call("ecs_posnext.api.customers.get_customer_addresses", {
			customer: props.customer
		})
		addresses.value = response || []
	} catch (error) {
		console.error("Error fetching addresses:", error)
	} finally {
		loading.value = false
	}
}

function selectAddress(addr) {
	emit("select", addr)
	show.value = false
}

async function addNewAddress() {
	if (!isValid.value) return
	adding.value = true
	try {
		// Build address_line1 from custom fields
		const parts = [
			newAddress.value.custom_street,
			newAddress.value.custom_building_name,
			newAddress.value.custom_floor ? `Floor ${newAddress.value.custom_floor}` : '',
			newAddress.value.custom_apartment ? `Apt ${newAddress.value.custom_apartment}` : '',
		].filter(Boolean)
		const addressLine1 = parts.join(', ') || newAddress.value.custom_street

		const addrDoc = await call("frappe.client.insert", {
			doc: {
				doctype: "Address",
				address_title: newAddress.value.address_title,
				address_line1: addressLine1,
				address_line2: newAddress.value.custom_mark || '',
				city: newAddress.value.city,
				country: newAddress.value.country,
				territory: newAddress.value.territory,
				custom_mark: newAddress.value.custom_mark,
				custom_street: newAddress.value.custom_street,
				custom_floor: newAddress.value.custom_floor,
				custom_apartment: newAddress.value.custom_apartment,
				custom_building_name: newAddress.value.custom_building_name,
				links: [
					{
						link_doctype: "Customer",
						link_name: props.customer
					}
				]
			}
		})
		
		showSuccess(__("Address added successfully"))
		window.frappe?.show_alert?.({ message: __("Address added successfully"), indicator: "green" }, 5)
		showAddDialog.value = false
		
		// Reset form
		newAddress.value = {
			address_title: "",
			address_line1: "",
			address_line2: "",
			city: "",
			country: "Egypt",
			territory: "",
			custom_street: "",
			custom_building_name: "",
			custom_floor: "",
			custom_apartment: "",
			custom_mark: ""
		}
		childTerritories.value = []
		
		await fetchAddresses()
		if (addrDoc && addrDoc.name) {
			selectAddress(addrDoc)
		}
	} catch (error) {
		showError(error.message || __("Failed to add address"))
	} finally {
		adding.value = false
	}
}

async function openEditDialog(addr) {
	editAddress.value = {
		name: addr.name,
		address_title: addr.address_title || "",
		city: addr.city || "",
		territory: addr.territory || "",
		custom_street: addr.custom_street || "",
		custom_building_name: addr.custom_building_name || "",
		custom_floor: addr.custom_floor || "",
		custom_apartment: addr.custom_apartment || "",
		custom_mark: addr.custom_mark || "",
		country: addr.country || "Egypt",
	}
	editChildTerritories.value = []
	if (addr.city) {
		loadingEditZones.value = true
		try {
			const res = await call("ecs_posnext.api.customers.get_child_territories", {
				parent_territory: addr.city
			})
			editChildTerritories.value = res || []
		} finally {
			loadingEditZones.value = false
		}
	}
	showEditDialog.value = true
}

async function onEditCityChange() {
	editAddress.value.territory = ""
	editChildTerritories.value = []
	if (!editAddress.value.city) return
	loadingEditZones.value = true
	try {
		const res = await call("ecs_posnext.api.customers.get_child_territories", {
			parent_territory: editAddress.value.city
		})
		editChildTerritories.value = res || []
	} finally {
		loadingEditZones.value = false
	}
}

async function saveEditedAddress() {
	if (!isEditValid.value) return
	saving.value = true
	try {
		const parts = [
			editAddress.value.custom_street,
			editAddress.value.custom_building_name,
			editAddress.value.custom_floor ? `Floor ${editAddress.value.custom_floor}` : "",
			editAddress.value.custom_apartment ? `Apt ${editAddress.value.custom_apartment}` : "",
		].filter(Boolean)
		const addressLine1 = parts.join(", ") || editAddress.value.custom_street

		// Fetch latest doc to get current modified timestamp (avoid TimestampMismatchError)
		const latest = await call("frappe.client.get", {
			doctype: "Address",
			name: editAddress.value.name,
		})

		await call("frappe.client.save", {
			doc: {
				...latest,
				address_title: editAddress.value.address_title,
				address_line1: addressLine1,
				address_line2: editAddress.value.custom_mark || "",
				city: editAddress.value.city,
				country: editAddress.value.country,
				territory: editAddress.value.territory,
				custom_mark: editAddress.value.custom_mark,
				custom_street: editAddress.value.custom_street,
				custom_floor: editAddress.value.custom_floor,
				custom_apartment: editAddress.value.custom_apartment,
				custom_building_name: editAddress.value.custom_building_name,
			}
		})

		showSuccess(__("Address updated successfully"))
		showEditDialog.value = false
		await fetchAddresses()
	} catch (error) {
		showError(error.message || __("Failed to update address"))
	} finally {
		saving.value = false
	}
}

watch(() => props.customer, () => {
	if (show.value) fetchAddresses()
})

watch(show, (newVal) => {
	if (newVal) {
		fetchAddresses()
		fetchTerritories()
		fetchParentTerritories()
	}
})

onMounted(() => {
	if (show.value) fetchAddresses()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
	width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
	background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
	background: #e2e8f0;
	border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
	background: #cbd5e1;
}
</style>
