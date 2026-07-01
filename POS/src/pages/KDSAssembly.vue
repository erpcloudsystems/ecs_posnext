<template>
  <div class="min-h-screen bg-gray-900 text-white">

    <!-- Branch selector -->
    <div v-if="!selectedBranch" class="flex flex-col items-center justify-center min-h-screen gap-8 p-8">
      <h1 class="text-4xl font-bold">Kitchen Display — Assembly</h1>
      <p class="text-gray-400 text-xl">Select a branch for this screen</p>
      <div class="grid gap-4 w-full max-w-md">
        <button
          v-for="branch in branches"
          :key="branch"
          @click="selectBranch(branch)"
          class="py-5 px-8 rounded-xl text-2xl font-semibold bg-gray-700 hover:bg-indigo-600 active:scale-95 transition-all text-white shadow-lg"
        >
          {{ branch }}
        </button>
      </div>
    </div>

    <!-- Main view -->
    <div v-else class="flex flex-col" style="height: 100vh">
      <!-- Header -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700 shrink-0">
        <div class="flex items-center gap-3">
          <button @click="clearBranch" class="text-gray-400 hover:text-white text-sm px-3 py-1 rounded bg-gray-700 hover:bg-gray-600">
            ← Change Branch
          </button>
          <h1 class="text-2xl font-bold">{{ selectedBranch }} — Assembly</h1>
        </div>
        <span class="text-gray-500 text-sm">{{ activeOrders.length }} order(s)</span>
      </div>

      <!-- Body: orders grid + right sidebar -->
      <div class="flex flex-1 overflow-hidden">

        <!-- Orders grid -->
        <div class="flex-1 overflow-y-auto p-4">
          <div v-if="activeOrders.length === 0" class="flex flex-col items-center justify-center h-full text-gray-500">
            <div class="text-6xl mb-4">✓</div>
            <p class="text-2xl">No pending orders</p>
          </div>

          <div class="grid gap-4" style="grid-template-columns: repeat(auto-fill, minmax(320px, 1fr))">
        <div
          v-for="order in activeOrders"
          :key="order.name"
          class="rounded-xl overflow-hidden shadow-xl bg-gray-800 flex flex-col"
        >
          <div
            class="px-4 py-3 flex items-center justify-between"
            :class="{
              'bg-green-600': timerColor(order) === 'green',
              'bg-amber-500': timerColor(order) === 'amber',
              'bg-red-600':   timerColor(order) === 'red',
            }"
          >
            <div>
              <div class="text-4xl font-black tracking-tighter">
                {{ order.custom_number_order || ('#' + order.order_no) }}
              </div>
              <div class="text-xs opacity-60 mt-0.5">#{{ order.order_no }} · {{ order.status }}</div>
            </div>
            <div class="text-right">
              <div class="text-2xl font-mono font-bold">{{ timerLabel(order) }}</div>
              <div class="text-xs opacity-75">{{ formatTime(order.order_time) }}</div>
            </div>
          </div>

          <div class="flex-1 p-4 space-y-3">
            <div
              v-for="(group, gi) in groupedItems(order)"
              :key="group.name || gi"
            >
              <!-- Main item row -->
              <div class="flex items-start justify-between gap-2">
                <div class="flex-1">
                  <span class="text-lg font-semibold">{{ group.item_name }}</span>
                  <span v-if="group.kds_station" class="ml-2 text-xs text-gray-400 bg-gray-700 px-2 py-0.5 rounded">
                    {{ group.kds_station }}
                  </span>
                  <span v-if="group.kds_station && group.station_status === 'Ready'" class="ml-2 text-xs text-green-400 bg-green-900 px-2 py-0.5 rounded">
                    ✓ Ready
                  </span>
                </div>
                <span class="text-2xl font-bold text-yellow-300 shrink-0">×{{ group.qty }}</span>
              </div>

              <!-- Component items (expanded from combo) -->
              <div v-if="group.children.length" class="mt-2 ml-3 border-l-2 border-gray-600 pl-3 space-y-1.5">
                <div
                  v-for="(child, ci) in group.children"
                  :key="child.name || ci"
                  class="flex items-center justify-between gap-2"
                >
                  <div class="flex-1">
                    <span :class="child.station_status === 'Ready' ? 'text-green-300' : 'text-gray-200'" class="text-sm font-medium">
                      {{ child.item_name }}
                    </span>
                    <span v-if="child.kds_station" class="ml-1.5 text-xs text-gray-500">{{ child.kds_station }}</span>
                    <!-- Removed ingredients in component -->
                    <span
                      v-for="(ri, ri_idx) in parseRemoved(child.removed_ingredients)"
                      :key="ri_idx"
                      class="ml-2 text-xs text-red-400 line-through"
                    >✕ {{ typeof ri === 'string' ? ri : ri }}</span>
                  </div>
                  <span class="text-xs font-bold px-2 py-0.5 rounded shrink-0"
                    :class="child.station_status === 'Ready'
                      ? 'bg-green-900 text-green-300'
                      : 'bg-gray-700 text-gray-400'"
                  >
                    {{ child.station_status === 'Ready' ? '✓' : '…' }}
                  </span>
                </div>
              </div>

              <!-- Removed ingredients on main item -->
              <ul v-if="parseRemoved(group.removed_ingredients).length" class="mt-0.5 ml-3 space-y-0.5">
                <li
                  v-for="(ri, ri_idx) in parseRemoved(group.removed_ingredients)"
                  :key="ri_idx"
                  class="text-xs text-red-400 flex items-baseline gap-1"
                >
                  <span>✕</span><span class="line-through">{{ ri.item_name || ri }}</span>
                </li>
              </ul>
            </div>
          </div>

          <div class="px-4 pb-2 text-xs text-gray-500">{{ order.sales_invoice }}</div>

          <!-- Done: only when all stations ready (or no stations configured) -->

          <div class="p-3">
            <button
              @click="markDone(order)"
              class="w-full py-3 rounded-lg text-xl font-bold active:scale-95 transition-all"
              :class="canMarkDone(order)
                ? 'bg-white text-gray-900 hover:bg-gray-100'
                : 'bg-amber-500 text-white hover:bg-amber-400'"
            >
              {{ canMarkDone(order) ? 'Done' : 'Force Done ⚡' }}
            </button>
          </div>
        </div>
        </div><!-- end grid -->
        </div><!-- end orders scroll area -->

        <!-- Right sidebar: item summary -->
        <div class="w-56 shrink-0 bg-gray-800 border-l border-gray-700 flex flex-col overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-700 shrink-0">
            <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider">ملخص الأصناف</div>
            <div class="text-xs text-gray-600 mt-0.5">{{ activeOrders.length }} order(s)</div>
          </div>
          <div class="flex-1 overflow-y-auto p-3 space-y-2">
            <div v-if="itemSummary.length === 0" class="text-gray-600 text-sm text-center pt-6">—</div>
            <div
              v-for="item in itemSummary"
              :key="item.item_name"
              class="flex items-center justify-between gap-2 bg-gray-700 rounded-lg px-3 py-2"
            >
              <span class="text-white text-sm leading-tight">{{ item.item_name }}</span>
              <span class="bg-yellow-400 text-gray-900 rounded-full px-2 py-0.5 text-xs font-black shrink-0">{{ item.qty }}</span>
            </div>
          </div>
        </div>

      </div><!-- end body flex -->
    </div><!-- end main view -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue"
import { call } from "frappe-ui"
import { useRoute, useRouter } from "vue-router"
import { initSocket } from "@/socket"

const route = useRoute()
const router = useRouter()

const branches = ref([])
const selectedBranch = ref(route.query.branch || "")
const warningThreshold = ref(70)

const orders = ref([])
const timerTick = ref(0)
const orderColors = new Map()
const knownOrderNames = new Set()

let tickInterval = null
let pollInterval = null
let socket = null

const activeOrders = computed(() => orders.value)

// Aggregate all non-component items across active orders into a summary list
const itemSummary = computed(() => {
  const map = {}
  for (const order of orders.value) {
    for (const item of (order.items || [])) {
      if (!item.is_component) continue
      const name = item.item_name || item.item_code
      map[name] = (map[name] || 0) + (item.qty || 0)
    }
  }
  return Object.entries(map)
    .map(([item_name, qty]) => ({ item_name, qty }))
    .sort((a, b) => b.qty - a.qty)
})

// ── Branch ──────────────────────────────────────────────────────────
async function loadBranches() {
  try {
    const result = await call("ecs_posnext.ecs_posnext.api.dispatcher.get_branches")
    branches.value = (result || []).map((b) => b.name)
  } catch (e) {
    console.error("Failed to load branches", e)
  }
}

function selectBranch(branch) {
  selectedBranch.value = branch
  router.replace({ query: { branch } })
}

function clearBranch() {
  selectedBranch.value = ""
  router.replace({ query: {} })
  orders.value = []
  orderColors.clear()
}

// ── Timer ────────────────────────────────────────────────────────────
function timerState(order) {
  timerTick.value
  const elapsed = Date.now() - new Date(order.order_time)
  const targetMs = (order.target_minutes || 15) * 60000
  const pct = (elapsed / targetMs) * 100
  const mm = String(Math.floor(elapsed / 60000)).padStart(2, "0")
  const ss = String(Math.floor((elapsed % 60000) / 1000)).padStart(2, "0")
  if (pct >= 100) {
    const over = elapsed - targetMs
    const omm = String(Math.floor(over / 60000)).padStart(2, "0")
    const oss = String(Math.floor((over % 60000) / 1000)).padStart(2, "0")
    return { color: "red", label: `+${omm}:${oss}` }
  }
  if (pct >= warningThreshold.value) return { color: "amber", label: `${mm}:${ss}` }
  return { color: "green", label: `${mm}:${ss}` }
}

function timerColor(order) { return timerState(order).color }
function timerLabel(order) { return timerState(order).label }

function formatTime(dt) {
  if (!dt) return ""
  return new Date(dt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
}

// ── Sound ────────────────────────────────────────────────────────────
function _playNotes(notes) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    notes.forEach(({ freq, start, dur, vol = 0.5 }) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain); gain.connect(ctx.destination)
      osc.type = "sine"; osc.frequency.value = freq
      gain.gain.setValueAtTime(vol, ctx.currentTime + start)
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + start + dur)
      osc.start(ctx.currentTime + start)
      osc.stop(ctx.currentTime + start + dur + 0.05)
    })
  } catch (_) {}
}

function playColorSound(level) {
  _playNotes(
    level === "red"
      ? [{ freq: 1400, start: 0, dur: 0.15 }, { freq: 1400, start: 0.22, dur: 0.15 }]
      : [{ freq: 900, start: 0, dur: 0.2 }],
  )
}

function playDoneSound() {
  _playNotes([
    { freq: 600, start: 0, dur: 0.1, vol: 0.4 },
    { freq: 950, start: 0.13, dur: 0.18, vol: 0.4 },
  ])
}

function playNewOrderSound() {
  _playNotes([
    { freq: 820, start: 0,    dur: 0.09 },
    { freq: 820, start: 0.14, dur: 0.09 },
    { freq: 1050, start: 0.28, dur: 0.13 },
  ])
}

function checkColorChanges() {
  for (const order of orders.value) {
    const newColor = timerState(order).color
    const prev = orderColors.get(order.name)
    if (prev && prev !== newColor) playColorSound(newColor)
    orderColors.set(order.name, newColor)
  }
}

// ── Combo helpers ────────────────────────────────────────────────────
function parseRemoved(raw) {
  if (!raw) return []
  try { const p = typeof raw === "string" ? JSON.parse(raw) : raw; return Array.isArray(p) ? p : [] }
  catch (_) { return [] }
}

function groupedItems(order) {
  const items = order.items || []
  // Top-level items (not components)
  const parents = items.filter((i) => !i.is_component)
  // Index children by combo_group_id
  const childrenByGroup = {}
  for (const item of items.filter((i) => i.is_component)) {
    const gid = item.combo_group_id || ""
    if (!childrenByGroup[gid]) childrenByGroup[gid] = []
    childrenByGroup[gid].push(item)
  }
  return parents.map((p) => ({ ...p, children: childrenByGroup[p.combo_group_id || ""] || [] }))
}

// ── Done gate ────────────────────────────────────────────────────────
function canMarkDone(order) {
  const items = order.items || []
  // Only items with a station assignment matter
  const stationItems = items.filter((i) => i.kds_station)
  if (stationItems.length === 0) return true
  return stationItems.every((i) => i.station_status === "Ready")
}

// ── Data ─────────────────────────────────────────────────────────────
async function loadOrders() {
  if (!selectedBranch.value) return
  try {
    const result = await call(
      "ecs_posnext.ecs_posnext.api.kds.get_active_orders",
      { branch: selectedBranch.value },
    )
    const fresh = result || []
    let hasNew = false
    for (const o of fresh) {
      if (!orderColors.has(o.name)) orderColors.set(o.name, timerState(o).color)
      if (!knownOrderNames.has(o.name)) {
        knownOrderNames.add(o.name)
        hasNew = true
      }
    }
    orders.value = fresh
    if (hasNew) playNewOrderSound()
  } catch (e) {
    console.error("KDS load error", e)
  }
}

async function markDone(order) {
  try {
    await call("ecs_posnext.ecs_posnext.api.kds.complete_order", { kds_order: order.name, force: 1 })
    playDoneSound()
    orders.value = orders.value.filter((o) => o.name !== order.name)
    orderColors.delete(order.name)
    knownOrderNames.delete(order.name)
  } catch (e) {
    console.error("KDS complete error", e)
  }
}

async function loadSettings() {
  try {
    const result = await call(
      "ecs_posnext.ecs_posnext.api.kds.get_settings",
      selectedBranch.value ? { branch: selectedBranch.value } : {},
    )
    warningThreshold.value = result?.settings?.warning_threshold_pct || 70
  } catch (e) {}
}

// ── Live ─────────────────────────────────────────────────────────────
function startLive() {
  if (tickInterval) return
  loadSettings()
  loadOrders()
  tickInterval = setInterval(() => {
    timerTick.value++
    checkColorChanges()
  }, 1000)
  pollInterval = setInterval(loadOrders, 10000)
  socket = initSocket()
  socket.connect()
  socket.on("kds_update", (data) => {
    if (data?.action === "new_order") playNewOrderSound()
    loadOrders()
  })
}

function stopLive() {
  clearInterval(tickInterval); tickInterval = null
  clearInterval(pollInterval); pollInterval = null
  if (socket) { socket.off("kds_update"); socket = null }
}

watch(selectedBranch, (val) => { if (val) startLive(); else stopLive() })

onMounted(async () => {
  await loadBranches()
  if (selectedBranch.value) startLive()
})

onUnmounted(stopLive)
</script>
