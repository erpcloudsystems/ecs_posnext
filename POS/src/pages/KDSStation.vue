<template>
  <div class="min-h-screen bg-gray-900 text-white">

    <!-- Branch selector -->
    <div v-if="!selectedBranch" class="flex flex-col items-center justify-center min-h-screen gap-8 p-8">
      <h1 class="text-4xl font-bold">{{ stationName }}</h1>
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
    <div v-else class="p-4">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <button @click="clearBranch" class="text-gray-400 hover:text-white text-sm px-3 py-1 rounded bg-gray-700 hover:bg-gray-600">
            ← Change Branch
          </button>
          <div>
            <h1 class="text-2xl font-bold">{{ stationName }}</h1>
            <p class="text-gray-400 text-sm">{{ selectedBranch }}</p>
          </div>
        </div>
        <span class="text-gray-500 text-sm">{{ orders.length }} order(s)</span>
      </div>

      <div v-if="orders.length === 0" class="flex flex-col items-center justify-center h-96 text-gray-500">
        <div class="text-6xl mb-4">✓</div>
        <p class="text-2xl">No pending items</p>
      </div>

      <div class="grid gap-4" style="grid-template-columns: repeat(auto-fill, minmax(320px, 1fr))">
        <div
          v-for="order in orders"
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
              <div class="text-xs opacity-60 mt-0.5">#{{ order.order_no }}</div>
            </div>
            <div class="text-right">
              <div class="text-2xl font-mono font-bold">{{ timerLabel(order) }}</div>
              <div class="text-xs opacity-75">{{ formatTime(order.order_time) }}</div>
            </div>
          </div>

          <div class="flex-1 p-4 space-y-4">
            <div
              v-for="(group, gi) in groupedStationItems(order)"
              :key="gi"
            >
              <!-- ── Regular item (not a combo component) ── -->
              <template v-if="group.type === 'item'">
                <div class="flex items-start justify-between gap-2">
                  <div class="flex-1">
                    <span class="text-xl font-semibold">{{ group.item.item_name }}</span>
                    <span v-if="group.item.is_special" class="ml-2 text-xs text-red-300 bg-red-900 px-2 py-0.5 rounded font-bold">SPECIAL</span>
                  </div>
                  <span class="text-2xl font-bold text-yellow-300 shrink-0">×{{ group.item.qty }}</span>
                </div>
                <!-- Ingredients: active (•) and removed (✕ struck through) -->
                <template v-if="computeIngredients(group.item.ingredients, group.item.removed_ingredients).active.length || computeIngredients(group.item.ingredients, group.item.removed_ingredients).removed.length">
                  <ul class="mt-1.5 ml-2 space-y-0.5">
                    <li v-for="(ing, ii) in computeIngredients(group.item.ingredients, group.item.removed_ingredients).active" :key="'ing-' + ii"
                      class="flex items-baseline gap-1.5 text-sm text-gray-300">
                      <span class="text-gray-500">•</span>
                      <span>{{ ing.item_name || ing }}</span>
                    </li>
                    <li v-for="(ri, ri_idx) in computeIngredients(group.item.ingredients, group.item.removed_ingredients).removed" :key="'rm-' + ri_idx"
                      class="flex items-baseline gap-1.5 text-sm text-red-400">
                      <span>✕</span><span class="line-through">{{ ri }}</span>
                    </li>
                  </ul>
                </template>
                <div v-if="group.item.special_notes" class="text-sm text-amber-300 mt-1 ml-2">{{ group.item.special_notes }}</div>
              </template>

              <!-- ── Combo group: main meal name + its components ── -->
              <template v-if="group.type === 'combo'">
                <!-- Main meal header -->
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-base font-bold text-indigo-300">{{ group.comboName }}</span>
                  <span class="text-xs text-gray-500 bg-gray-700 px-2 py-0.5 rounded">combo</span>
                </div>
                <!-- Components for this station -->
                <div class="ml-2 border-l-2 border-indigo-800 pl-3 space-y-3">
                  <div v-for="(child, ci) in group.children" :key="child.name || ci">
                    <div class="flex items-start justify-between gap-2">
                      <div class="flex-1">
                        <span class="text-xl font-semibold">{{ child.item_name }}</span>
                        <span v-if="child.is_special" class="ml-2 text-xs text-red-300 bg-red-900 px-2 py-0.5 rounded font-bold">SPECIAL</span>
                      </div>
                      <span class="text-2xl font-bold text-yellow-300 shrink-0">×{{ child.qty }}</span>
                    </div>
                    <!-- Ingredient list: active + removed -->
                    <template v-if="computeIngredients(child.ingredients, child.removed_ingredients).active.length || computeIngredients(child.ingredients, child.removed_ingredients).removed.length">
                      <ul class="mt-1.5 ml-2 space-y-0.5">
                        <li v-for="(ing, ii) in computeIngredients(child.ingredients, child.removed_ingredients).active" :key="'ing-' + ii"
                          class="flex items-baseline gap-1.5 text-sm text-gray-300">
                          <span class="text-gray-500">•</span>
                          <span>{{ ing.item_name || ing }}</span>
                        </li>
                        <li v-for="(ri, ri_idx) in computeIngredients(child.ingredients, child.removed_ingredients).removed" :key="'rm-' + ri_idx"
                          class="flex items-baseline gap-1.5 text-sm text-red-400">
                          <span>✕</span><span class="line-through">{{ ri }}</span>
                        </li>
                      </ul>
                    </template>
                    <div v-if="child.special_notes" class="text-sm text-amber-300 mt-1 ml-2">{{ child.special_notes }}</div>
                  </div>
                </div>
              </template>
            </div>
          </div>

          <div class="px-4 pb-2 text-xs text-gray-500">
            <span v-if="order.custom_number_order" class="font-medium text-gray-400">{{ order.custom_number_order }} · </span>{{ order.sales_invoice }}
          </div>

          <div class="p-3 flex gap-2">
            <button
              @click="markStationDone(order)"
              class="flex-1 py-3 rounded-lg text-xl font-bold bg-white text-gray-900 hover:bg-gray-100 active:scale-95 transition-all"
            >
              Done
            </button>
            <button
              v-if="stationInfo && stationInfo.enable_special_print && hasSpecial(order)"
              @click="printSpecial(order)"
              class="py-3 px-4 rounded-lg text-lg font-bold bg-amber-500 text-gray-900 hover:bg-amber-400 active:scale-95 transition-all"
            >
              Print
            </button>
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

const route = useRoute()
const router = useRouter()

const stationName = computed(() => route.params.station || "")
const branches = ref([])
const selectedBranch = ref(route.query.branch || "")
const warningThreshold = ref(70)

const orders = ref([])
const stationInfo = ref(null)
const timerTick = ref(0)
const orderColors = new Map()
const knownOrderNames = new Set() // tracks orders seen since page load

let tickInterval = null
let pollInterval = null
let socket = null

// ── Branch ──────────────────────────────────────────────────────────
async function loadBranches() {
  try {
    const result = await call("ecs_posnext.ecs_posnext.api.dispatcher.get_branches")
    branches.value = (result || []).map((b) => b.name)
  } catch (e) {}
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
  // Two ascending tones — success confirmation
  _playNotes([
    { freq: 600, start: 0, dur: 0.1, vol: 0.4 },
    { freq: 950, start: 0.13, dur: 0.18, vol: 0.4 },
  ])
}

function playNewOrderSound() {
  // Three short beeps — new order alert
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

// ── Data ─────────────────────────────────────────────────────────────
function parseIngredients(raw) {
  if (!raw) return []
  try {
    const parsed = typeof raw === "string" ? JSON.parse(raw) : raw
    return Array.isArray(parsed) ? parsed : []
  } catch (_) { return [] }
}

function parseRemoved(raw) {
  if (!raw) return []
  try {
    const parsed = typeof raw === "string" ? JSON.parse(raw) : raw
    return Array.isArray(parsed) ? parsed : []
  } catch (_) { return [] }
}

// Returns { active: [...], removed: [...names] } for an item's ingredients
function computeIngredients(ingredientsRaw, removedRaw) {
  const all = parseIngredients(ingredientsRaw)
  const removedList = parseRemoved(removedRaw) // names or codes

  if (!removedList.length) return { active: all, removed: [] }

  // Build a code→name map from the full ingredient list
  const codeToName = {}
  all.forEach((ing) => { if (ing.item_code) codeToName[ing.item_code] = ing.item_name || ing.item_code })

  // Resolve removed entries: if it's a code in the map, convert to name
  const removedNames = removedList.map((r) => (typeof r === "string" ? (codeToName[r] || r) : (r.item_name || r)))
  const removedSet = new Set(removedNames)

  // Active = ingredients whose name is not in the removed set
  const active = all.filter((ing) => {
    const n = ing.item_name || ing
    return !removedSet.has(n) && !removedSet.has(ing.item_code)
  })

  return { active, removed: removedNames }
}

function groupedStationItems(order) {
  const items = order.items || []
  const result = []
  const comboMap = {}

  for (const item of items) {
    if (!item.is_component) {
      result.push({ type: "item", item })
    } else {
      const gid = item.combo_group_id || item.name
      if (!comboMap[gid]) {
        comboMap[gid] = { type: "combo", comboName: item.combo_item_name, children: [] }
        result.push(comboMap[gid])
      }
      comboMap[gid].children.push(item)
    }
  }
  return result
}

function hasSpecial(order) {
  return order.items?.some((i) => i.is_special)
}

function printSpecial(order) {
  window.open(
    `${window.location.origin}/printview?doctype=KDS+Order&name=${encodeURIComponent(order.name)}&format=KDS+Special+Ticket`,
    "_blank",
  )
}

async function loadOrders() {
  if (!selectedBranch.value) return
  try {
    const result = await call("ecs_posnext.ecs_posnext.api.kds.get_station_orders", {
      station: stationName.value,
      branch: selectedBranch.value,
    })
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
  } catch (e) {}
}

async function loadSettings() {
  try {
    const result = await call(
      "ecs_posnext.ecs_posnext.api.kds.get_settings",
      selectedBranch.value ? { branch: selectedBranch.value } : {},
    )
    warningThreshold.value = result?.settings?.warning_threshold_pct || 70
    const stations = result?.stations || []
    stationInfo.value = stations.find((s) => s.station_name === stationName.value) || null
  } catch (e) {}
}

async function markStationDone(order) {
  try {
    await call("ecs_posnext.ecs_posnext.api.kds.complete_station", {
      kds_order: order.name,
      station: stationName.value,
    })
    playDoneSound()
    orders.value = orders.value.filter((o) => o.name !== order.name)
    orderColors.delete(order.name)
    knownOrderNames.delete(order.name)
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
