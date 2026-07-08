<template>
  <div class="flex flex-col bg-neutral-950 text-white" style="height:100vh; overflow:hidden">
    <!-- Header -->
    <header class="shrink-0 flex items-center justify-between px-5 py-3 border-b border-neutral-800 bg-neutral-900/60">
      <div class="flex items-center gap-3">
        <button @click="$router.push('/')" class="text-neutral-400 hover:text-white text-sm px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700">← Back</button>
        <div>
          <h1 class="text-xl font-black leading-none">🍳 Kitchen Totals</h1>
          <div class="text-[11px] text-neutral-500 mt-0.5" dir="rtl">إجمالي كميات الأصناف في المطبخ</div>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <select v-if="branches.length" v-model="selectedBranch"
          class="bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500">
          <option value="">All branches</option>
          <option v-for="b in branches" :key="b" :value="b">{{ b }}</option>
        </select>
        <div class="text-right leading-none">
          <div class="text-2xl font-black text-emerald-400 tabular-nums">{{ totalUnits }}</div>
          <div class="text-[10px] text-neutral-500 mt-1">{{ __('units') }} · {{ totals.length }} {{ __('items') }}</div>
        </div>
        <button @click="loadOrders" title="Refresh" class="px-3 py-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-sm">↻</button>
      </div>
    </header>

    <!-- Station filter -->
    <div v-if="stations.length > 1" class="shrink-0 flex items-center gap-2 px-5 py-2 border-b border-neutral-800 overflow-x-auto">
      <button @click="stationFilter = ''"
        :class="stationFilter === '' ? 'bg-white text-black' : 'bg-neutral-800 text-neutral-300 hover:bg-neutral-700'"
        class="px-3 py-1 rounded-full text-xs font-bold shrink-0">{{ __('All Stations') }}</button>
      <button v-for="s in stations" :key="s" @click="stationFilter = s"
        :class="stationFilter === s ? 'bg-white text-black' : 'bg-neutral-800 text-neutral-300 hover:bg-neutral-700'"
        class="px-3 py-1 rounded-full text-xs font-bold shrink-0">{{ s }}</button>
    </div>

    <!-- Body -->
    <div class="flex-1 overflow-y-auto p-5">
      <div v-if="!totals.length" class="h-full flex flex-col items-center justify-center text-neutral-600">
        <div class="text-6xl mb-3">🍽️</div>
        <p class="text-xl">{{ __('No active orders in the kitchen') }}</p>
      </div>

      <div v-else class="grid gap-3" style="grid-template-columns: repeat(auto-fill, minmax(250px, 1fr))">
        <div v-for="row in totals" :key="row.key"
          class="rounded-2xl bg-neutral-900 border border-neutral-800 p-4 flex items-center gap-4">
          <div class="text-4xl font-black text-yellow-300 tabular-nums shrink-0 w-16 text-center">×{{ fmtQty(row.qty) }}</div>
          <div class="min-w-0 flex-1 text-right" dir="rtl">
            <div class="text-lg font-bold leading-tight break-words">{{ row.item_name }}</div>
            <div v-if="row.station" class="text-[11px] text-neutral-500 mt-1">🏷 {{ row.station }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue"
import { call } from "frappe-ui"
import { useRoute, useRouter } from "vue-router"
import { initSocket } from "@/socket"

function __(s) { return s }

const route = useRoute()
const router = useRouter()

const orders = ref([])
const branches = ref([])
const selectedBranch = ref(route.query.branch || "")
const stationFilter = ref("")
let pollInterval = null
let socket = null

function fmtQty(q) {
  const n = Number(q) || 0
  return Number.isInteger(n) ? n : Math.round(n * 100) / 100
}

async function loadBranches() {
  try {
    const result = await call("ecs_posnext.ecs_posnext.api.dispatcher.get_branches")
    branches.value = (result || []).map((b) => b.name)
  } catch (e) { branches.value = [] }
}

async function loadOrders() {
  try {
    const args = selectedBranch.value ? { branch: selectedBranch.value } : {}
    orders.value = (await call("ecs_posnext.ecs_posnext.api.kds.get_active_orders", args)) || []
  } catch (e) { console.error("Kitchen totals load error", e) }
}

// Aggregate the leaf prep items (components, or the item itself when not a combo)
// across every active kitchen order, summing quantities per item + station.
const aggregate = computed(() => {
  const map = {}
  for (const order of orders.value) {
    const items = order.items || []
    const parents = items.filter((i) => !i.is_component)
    const childrenByGroup = {}
    for (const it of items.filter((i) => i.is_component)) {
      const gid = it.combo_group_id || ""
      if (!childrenByGroup[gid]) childrenByGroup[gid] = []
      childrenByGroup[gid].push(it)
    }
    for (const p of parents) {
      const children = childrenByGroup[p.combo_group_id || ""] || []
      const leaves = children.length ? children : [p]
      for (const leaf of leaves) {
        const name = leaf.item_name || leaf.item_code || "?"
        const station = leaf.kds_station || ""
        const key = station + "||" + name
        if (!map[key]) map[key] = { key, item_name: name, station, qty: 0 }
        map[key].qty += Number(leaf.qty) || 0
      }
    }
  }
  return Object.values(map)
})

const stations = computed(() =>
  [...new Set(aggregate.value.map((r) => r.station).filter(Boolean))].sort()
)

const totals = computed(() => {
  let rows = aggregate.value
  if (stationFilter.value) rows = rows.filter((r) => r.station === stationFilter.value)
  return rows.slice().sort((a, b) => b.qty - a.qty)
})

const totalUnits = computed(() => totals.value.reduce((s, r) => s + r.qty, 0))

watch(selectedBranch, () => {
  router.replace({ query: selectedBranch.value ? { branch: selectedBranch.value } : {} })
  loadOrders()
})

onMounted(async () => {
  await loadBranches()
  await loadOrders()
  pollInterval = setInterval(loadOrders, 10000)
  socket = initSocket()
  socket.connect()
  socket.on("kds_update", loadOrders)
})
onUnmounted(() => {
  clearInterval(pollInterval)
  if (socket) { socket.off("kds_update"); socket = null }
})
</script>
