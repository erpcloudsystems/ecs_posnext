const fs = require('fs');

let content = fs.readFileSync('POS/src/stores/customerSearch.js', 'utf8');

// Replace the ultra-fast search helper and filteredCustomers getter
const newSearchLogic = `
let searchTimeout = null

const filteredCustomers = computed(() => {
return allCustomers.value
})

const recommendations = computed(() => {
const term = searchTerm.value.trim().toLowerCase()
if (!term || term.length < 2) return []

const recs = []

if (/^\\d+$/.test(term)) {
recs.push({
type: "phone",
text: __('Search by phone: {0}', [term]),
icon: "📱",
})
}

if (term.includes("@")) {
recs.push({
type: "email",
text: __('Search by email: {0}', [term]),
icon: "✉️",
})
}

const exactMatch = allCustomers.value.some(
(c) => c.customer_name?.toLowerCase() === term,
)
if (!exactMatch && allCustomers.value.length < 5) {
recs.push({
type: "create",
text: __('Create new customer: {0}', [term]),
icon: "➕",
})
}

return recs
})

async function performSearch(posProfile, term = "") {
loading.value = true
try {
if (!term) {
const cachedCustomers = await offlineWorker.searchCachedCustomers("", 50)

const recentSet = new Set(recentSearches.value)
const frequentSet = new Set(frequentCustomers.value)

const recent = []
const frequent = []
const other = []

for (const c of cachedCustomers) {
if (recentSet.has(c.name)) recent.push(c)
else if (frequentSet.has(c.name)) frequent.push(c)
else other.push(c)
}

allCustomers.value = [...recent, ...frequent, ...other].slice(0, 50)
return
}

if (isOffline()) {
const cachedCustomers = await offlineWorker.searchCachedCustomers(term, 50)
allCustomers.value = cachedCustomers
} else {
const response = await call("ecs_posnext.api.customers.get_customers", {
pos_profile: posProfile,
search_term: term,
limit: 50
})
const results = response?.message || response || []
allCustomers.value = results

if (results.length > 0) {
const active = results.filter((c) => !c.disabled)
if (active.length > 0) {
offlineWorker.cacheCustomers(active).catch(e => log.error("Background cache error", e))
}
}
}
} catch (error) {
log.error("Error searching customers:", error)
allCustomers.value = []
} finally {
loading.value = false
}
}

async function loadAllCustomers(posProfile, forceReload = false) {
if (!posProfile) return
await performSearch(posProfile, "")
}

async function addCustomerToCache(customer) {
try {
const existingWithoutNew = allCustomers.value.filter(
(cust) => cust.name !== customer.name,
)
allCustomers.value = [customer, ...existingWithoutNew]

await offlineWorker.cacheCustomers([customer])
log.success(\`New customer cached: \${customer.customer_name}\`)
} catch (error) {
log.error("Error caching newly created customer:", error)
}
}

// Real-time Push Integration
const { onCustomerUpdate } = useRealtimeCustomers()
onCustomerUpdate(async (data) => {
const { name, action, customer_name, mobile_no, custom_other_mobile_no, email_id, disabled } = data
if (action === "delete" || disabled) {
allCustomers.value = allCustomers.value.filter((c) => c.name !== name)
await offlineWorker.deleteCustomers([name])
log.info(\`Customer removed/disabled via real-time: \${name}\`)
} else {
const customer = {
name,
customer_name,
mobile_no,
custom_other_mobile_no,
email_id,
disabled: !!disabled,
}
await addCustomerToCache(customer)
}
})

function setSearchTerm(term, posProfile = null) {
searchTerm.value = term
selectedIndex.value = -1

if (searchTimeout) clearTimeout(searchTimeout)
searchTimeout = setTimeout(() => {
performSearch(posProfile, term)
}, 300)
}

function clearSearch(posProfile = null) {
searchTerm.value = ""
selectedIndex.value = -1
if (searchTimeout) clearTimeout(searchTimeout)
performSearch(posProfile, "")
}
`;

// Replace from 'function quickMatch' to 'function setSelectedIndex'
const quickMatchIndex = content.indexOf('// Ultra-fast search helper');
const setSelectedIndexIndex = content.indexOf('function setSelectedIndex(index)');

content = content.substring(0, quickMatchIndex) + newSearchLogic + '\n' + content.substring(setSelectedIndexIndex);

// Also remove searchIndex and resultCache since they are no longer needed
content = content.replace(/\n\s*\/\/ Performance optimization: Pre-computed search indices\n\s*const searchIndex = ref\(new Map\(\)\)\n\s*const resultCache = ref\(new Map\(\)\)/g, '');

fs.writeFileSync('POS/src/stores/customerSearch.js', content);
