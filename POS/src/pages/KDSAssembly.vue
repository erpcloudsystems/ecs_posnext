<template>
  <div class="min-h-screen bg-black text-white">

    <!-- Branch selector -->
    <div v-if="!selectedBranch" class="flex flex-col items-center justify-center min-h-screen gap-8 p-8">
      <h1 class="text-4xl font-bold">Kitchen Display — Assembly</h1>
      <p class="text-gray-400 text-xl">Select a branch for this screen</p>
      <div class="grid gap-4 w-full max-w-md">
        <button
          v-for="branch in branches"
          :key="branch"
          @click="selectBranch(branch)"
          class="py-5 px-8 rounded-xl text-2xl font-semibold bg-gray-800 hover:bg-emerald-600 active:scale-95 transition-all text-white shadow-lg"
        >
          {{ branch }}
        </button>
      </div>
    </div>

    <!-- Main view -->
    <div v-else class="flex flex-col" style="height: 100vh">

      <!-- ===== Top header ===== -->
      <header class="flex items-center justify-between px-5 py-3 border-b border-neutral-800 shrink-0 bg-black">
        <div class="flex items-center gap-5">
          <!-- Logo -->
          <div class="flex items-center gap-2">
            <div class="text-2xl font-black tracking-tight leading-none text-emerald-500">mumo</div>
            <div class="text-[9px] leading-tight text-neutral-500 font-semibold uppercase tracking-widest">Kitchen<br>Display System</div>
          </div>
          <div class="h-8 w-px bg-neutral-800"></div>
          <div class="flex items-center gap-2">
            <h1 class="text-2xl font-bold">{{ selectedBranch }} — Assembly</h1>
            <span class="flex items-center gap-1 text-emerald-500 text-sm font-semibold">
              <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Online
            </span>
          </div>
        </div>

        <div class="flex items-center gap-2.5">
          <button
            @click="soundOn = !soundOn"
            class="flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors border"
            :class="soundOn ? 'bg-neutral-900 border-neutral-700 text-white' : 'bg-neutral-900 border-neutral-800 text-neutral-500'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
              <template v-if="soundOn"><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></template>
              <template v-else><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></template>
            </svg>
            Sound {{ soundOn ? 'ON' : 'OFF' }}
          </button>

          <div class="relative">
            <button
              @click="showFilter = !showFilter"
              class="flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors border bg-neutral-900 border-neutral-700 text-white"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
              </svg>
              Filter ({{ typeFilter.size }})
            </button>
            <div v-if="showFilter" class="absolute right-0 mt-2 w-44 bg-neutral-900 border border-neutral-700 rounded-lg shadow-2xl z-30 p-2 space-y-1">
              <button
                v-for="t in TYPE_ORDER"
                :key="t"
                @click="toggleFilter(t)"
                class="w-full flex items-center justify-between gap-2 px-2.5 py-2 rounded-md text-sm text-left transition-colors"
                :class="typeFilter.has(t) ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:bg-neutral-800'"
              >
                <span class="flex items-center gap-2">
                  <span class="w-2.5 h-2.5 rounded-sm" :style="{ background: TYPE_META[t].color }"></span>
                  {{ TYPE_META[t].label }}
                </span>
                <svg v-if="typeFilter.has(t)" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
              </button>
            </div>
          </div>

          <button
            @click="showSummary = !showSummary"
            class="flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors border"
            :class="showSummary ? 'bg-neutral-900 border-neutral-700 text-white' : 'bg-neutral-900 border-neutral-800 text-neutral-500'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
            Summary
          </button>

          <button @click="clearBranch" title="Change branch" class="p-2 rounded-lg bg-neutral-900 border border-neutral-700 text-neutral-300 hover:text-white transition-colors">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
          </button>
        </div>
      </header>

      <!-- ===== Stats row ===== -->
      <div class="flex items-stretch gap-3 px-5 py-3 shrink-0 overflow-x-auto">
        <div class="flex gap-3">
          <div v-for="s in statCards" :key="s.label" class="min-w-[104px] rounded-xl bg-neutral-900/70 border border-neutral-800 px-4 py-2.5">
            <div class="text-3xl font-black leading-none" :style="{ color: s.color }">{{ s.value }}</div>
            <div class="text-[11px] text-neutral-400 mt-1 leading-tight">{{ s.label }}<span v-if="s.sub" class="block text-neutral-600">{{ s.sub }}</span></div>
          </div>
        </div>

        <div class="flex-1"></div>

        <div class="rounded-xl bg-neutral-900/70 border border-neutral-800 px-4 py-2.5 flex items-center gap-3">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#a3a3a3" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2"/><path d="M5 3 2 6"/><path d="m22 6-3-3"/></svg>
          <div>
            <div class="text-[11px] text-neutral-400">Average Time</div>
            <div class="text-2xl font-black leading-none">{{ averageLabel }}</div>
          </div>
        </div>

        <div class="rounded-xl bg-neutral-900/70 border border-neutral-800 px-4 py-2.5 flex flex-col justify-center">
          <div class="text-[11px] text-neutral-400">Station</div>
          <div class="text-lg font-bold leading-tight">Assembly</div>
        </div>

        <div class="rounded-xl bg-neutral-900/70 border border-neutral-800 px-4 py-2.5 flex flex-col justify-center items-end">
          <div class="text-2xl font-black leading-none">{{ clockTime }}</div>
          <div class="text-[11px] text-neutral-400 mt-1">{{ clockDate }}</div>
        </div>
      </div>

      <!-- ===== Orders grid + summary sidebar ===== -->
      <div class="flex-1 flex overflow-hidden">
      <div class="flex-1 overflow-y-auto px-5 pb-3">
        <div v-if="visibleOrders.length === 0" class="flex flex-col items-center justify-center h-full text-neutral-600">
          <div class="text-6xl mb-4">✓</div>
          <p class="text-2xl">No pending orders</p>
        </div>

        <div class="grid gap-3.5" style="grid-template-columns: repeat(auto-fill, minmax(278px, 1fr))">
          <div
            v-for="order in visibleOrders"
            :key="order.name"
            class="rounded-2xl overflow-hidden bg-neutral-950 border flex flex-col"
            :style="{ borderColor: statusColor(order) + '55' }"
          >
            <!-- Card header — background tinted by the timer state (green / amber / red) -->
            <div class="flex items-center justify-between px-3.5 pt-3.5 pb-2" :style="{ backgroundColor: statusColor(order) + '33' }">
              <div class="flex items-center gap-2.5">
                <div class="w-14 h-14 rounded-xl flex items-center justify-center shrink-0" :style="{ background: baseTypeMeta(order).color }">
                  <span class="inline-flex scale-[1.7]" v-html="baseTypeMeta(order).icon"></span>
                </div>
                <div>
                  <div class="text-2xl font-black leading-none tracking-tight">{{ displayNumber(order) }}</div>
                  <div class="text-[11px] text-neutral-500 mt-1">{{ formatClock(order.order_time) }}</div>
                </div>
              </div>
              <div class="text-right">
                <div class="text-xl font-mono font-bold leading-none text-white">{{ timerLabel(order) }}</div>
                <div class="text-[10px] font-bold mt-1 flex items-center justify-end gap-1" :style="{ color: statusColor(order) }">
                  <span class="w-1.5 h-1.5 rounded-full" :style="{ background: statusColor(order) }"></span>{{ statusLabel(order) }}
                </div>
              </div>
            </div>

            <!-- Order type badge (+ payment type under it) + who -->
            <div class="flex items-start justify-between px-3.5 pb-2">
              <div class="flex flex-col items-start gap-1">
                <span class="text-[10px] font-black px-2 py-1 rounded tracking-wider" :style="{ background: baseTypeMeta(order).color, color: '#fff' }">
                  {{ baseTypeMeta(order).label }}
                </span>
                <span v-if="payMeta(order)" class="text-[9px] font-black tracking-wider" :style="{ color: payMeta(order).color }">
                  {{ payMeta(order).emoji }} {{ payMeta(order).labelEn }}
                </span>
              </div>
              <div class="flex flex-col items-end gap-0.5 max-w-[55%]">
                <span class="text-[11px] text-neutral-400 font-medium truncate w-full text-right">{{ whoLabel(order) }}</span>
                <span v-if="customerLine(order)" class="text-xs text-white font-semibold truncate w-full text-right">👤 {{ customerLine(order) }}</span>
                <span v-if="windowNo(order)" class="text-xs font-black text-sky-300 truncate w-full text-right" dir="rtl">🪟 شباك {{ windowNo(order) }}</span>
              </div>
            </div>

            <div class="mx-3.5 border-t border-neutral-800"></div>

            <!-- Order-level note -->
            <div v-if="order.order_note" class="mx-3.5 mt-2 px-2.5 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-lg font-bold text-right" dir="rtl">
              📝 {{ order.order_note }}
            </div>

            <!-- Items -->
            <div class="flex-1 px-3.5 py-2.5 space-y-3">
              <div v-for="(group, gi) in groupedItems(order)" :key="group.name || gi">
                <div class="flex items-start justify-between gap-2 mb-1.5">
                  <span class="text-2xl font-black text-yellow-300 shrink-0">×{{ fmtQty(group.qty) }}</span>
                  <span class="text-base font-bold text-right leading-tight flex-1 min-w-0 break-words whitespace-normal" dir="rtl">{{ group.item_name }}</span>
                </div>

                <div class="space-y-1">
                  <div
                    v-for="(row, ri) in componentRows(group)"
                    :key="ri"
                    class="flex items-start gap-2 text-sm"
                  >
                    <span
                      class="w-4 h-4 rounded flex items-center justify-center shrink-0 mt-0.5"
                      :class="row.ready ? 'bg-emerald-500' : 'border border-neutral-600'"
                    >
                      <svg v-if="row.ready" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="3.5"><polyline points="20 6 9 17 4 12"/></svg>
                    </span>
                    <span class="text-neutral-200 flex-1 min-w-0 text-right leading-tight break-words whitespace-normal" dir="rtl" :class="{ 'line-through text-neutral-600': row.removed }">{{ row.name }}</span>
                    <span class="font-mono font-bold text-xs shrink-0" :class="row.ready ? 'text-emerald-400' : 'text-neutral-500'">{{ row.done }}/{{ row.total }}</span>
                  </div>
                  <!-- per-item (component) note -->
                  <div v-for="(row, ni) in componentRows(group)" :key="'n'+ni">
                    <div v-if="row.note" class="text-base font-semibold text-amber-300/90 text-right pr-6" dir="rtl">📝 {{ row.note }}</div>
                  </div>

                  <!-- removed ingredients on the group -->
                  <div v-for="(ri, idx) in parseRemoved(group.removed_ingredients)" :key="'r'+idx" class="flex items-center gap-2 text-xs text-red-400">
                    <span class="w-4 text-center">✕</span>
                    <span class="flex-1 text-right line-through" dir="rtl">{{ ri.item_name || ri }}</span>
                  </div>

                  <div v-if="group.special_notes" class="text-base font-semibold text-amber-300/90 text-right pt-0.5" dir="rtl">📝 {{ group.special_notes }}</div>
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-2 p-2.5">
              <button
                @click="markDone(order)"
                class="flex-1 py-2.5 rounded-lg text-base font-bold active:scale-95 transition-all"
                :class="canMarkDone(order) ? 'bg-emerald-500 text-black hover:bg-emerald-400' : 'bg-amber-500 text-black hover:bg-amber-400'"
              >
                {{ canMarkDone(order) ? 'Mark Done' : 'Force Done ⚡' }}
              </button>
              <button class="w-10 py-2.5 rounded-lg bg-neutral-800 text-neutral-400 hover:text-white font-bold">···</button>
            </div>
          </div>
        </div>
      </div>

        <!-- Summary sidebar (aggregated components across visible orders) -->
        <aside v-if="showSummary" class="w-60 shrink-0 bg-neutral-950 border-l border-neutral-800 flex flex-col overflow-hidden">
          <div class="px-4 py-3 border-b border-neutral-800 shrink-0">
            <div class="text-xs font-bold text-neutral-300 uppercase tracking-wider">Items Summary</div>
            <div class="text-[11px] text-neutral-600 mt-0.5" dir="rtl">ملخص الأصناف · {{ visibleOrders.length }} order(s)</div>
          </div>
          <div class="flex-1 overflow-y-auto p-3 space-y-2">
            <div v-if="itemSummary.length === 0" class="text-neutral-600 text-sm text-center pt-6">—</div>
            <div v-for="item in itemSummary" :key="item.item_name" class="flex items-center justify-between gap-2 bg-neutral-900 rounded-lg px-3 py-2">
              <span class="text-neutral-200 text-sm leading-tight text-right flex-1" dir="rtl">{{ item.item_name }}</span>
              <span class="bg-yellow-400 text-black rounded-full px-2 py-0.5 text-xs font-black shrink-0">{{ fmtQty(item.qty) }}</span>
            </div>
          </div>
        </aside>
      </div>

      <!-- ===== Footer ===== -->
      <div class="shrink-0 border-t border-neutral-800 bg-black">
        <div class="flex items-center justify-between px-5 py-2.5">
          <div class="flex items-center gap-5">
            <div v-for="t in TYPE_ORDER" :key="t" class="flex items-center gap-2">
              <div class="w-6 h-6 rounded-md flex items-center justify-center" :style="{ background: TYPE_META[t].color }">
                <span v-html="TYPE_META[t].icon"></span>
              </div>
              <div class="leading-none">
                <div class="text-[11px] font-bold">{{ TYPE_META[t].label }}</div>
                <div class="text-[10px] text-neutral-500" dir="rtl">{{ TYPE_META[t].ar }}</div>
              </div>
            </div>
          </div>
          <button @click="loadOrders" class="flex items-center gap-2 px-4 py-2 rounded-lg bg-neutral-900 border border-neutral-700 text-sm font-semibold hover:bg-neutral-800">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
            Refresh
          </button>
        </div>
        <div class="flex items-center gap-5 px-5 py-1.5 border-t border-neutral-900 text-[11px] text-neutral-500">
          <span class="flex items-center gap-1.5"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>Auto refresh: 15s</span>
          <span class="flex items-center gap-1.5">🔔 New order alert: <b :class="soundOn ? 'text-emerald-400' : 'text-neutral-600'">{{ soundOn ? 'ON' : 'OFF' }}</b></span>
          <span class="flex items-center gap-1.5">🔴 Overdue alert: <b :class="soundOn ? 'text-emerald-400' : 'text-neutral-600'">{{ soundOn ? 'ON' : 'OFF' }}</b></span>
          <span>Show completed: <b class="text-neutral-600">OFF</b></span>
          <span>Sort by: Time (Oldest)</span>
          <span class="flex-1"></span>
          <span class="text-neutral-600">KDS v2.5.0</span>
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
import { ORDER_CATEGORY_META, orderCategoryKey } from "@/utils/orderCategory"

const route = useRoute()
const router = useRouter()

const branches = ref([])
const selectedBranch = ref(route.query.branch || "")
const warningThreshold = ref(70)

const orders = ref([])
const timerTick = ref(0)
const nowTs = ref(Date.now())
const orderColors = new Map()
const knownOrderNames = new Set()

const soundOn = ref(true)
const showFilter = ref(false)
const typeFilter = ref(new Set())
const showSummary = ref(true)

// Aggregate all component items across visible orders (right-sidebar summary)
const itemSummary = computed(() => {
  const map = {}
  for (const order of visibleOrders.value) {
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

// Print the kitchen receipt for an order
function printOrder(order) {
  if (!order.sales_invoice) return
  window.open(
    `/printview?doctype=Sales Invoice&name=${encodeURIComponent(order.sales_invoice)}&trigger_print=1&format=Kitchen%20Receipt&no_letterhead=0`,
    "_blank",
  )
}

let tickInterval = null
let pollInterval = null
let socket = null

// ── Order-type metadata (icon / colour / labels) ─────────────────────
const ICONS = {
  delivery: '<svg width="18" height="18" viewBox="0 0 24 24" fill="#fff"><circle cx="6" cy="18" r="2.4"/><circle cx="17" cy="18" r="2.4"/><path d="M2 8h6l3.5 6H17" fill="none" stroke="#fff" stroke-width="2"/><rect x="9" y="5" width="6" height="5" rx="1"/><path d="M17 10l2-2h3v2z"/></svg>',
  talabat: '<span style="font-size:8px;font-weight:800;color:#fff;letter-spacing:-.3px">talabat</span>',
  dinein: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><path d="M4 3v7a3 3 0 0 0 3 3v8"/><path d="M4 3v4M7 3v4"/><path d="M18 3c-1.5 0-3 1.8-3 5s1.5 4 3 4v9"/></svg>',
  pickup: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>',
  cod: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.6"/><path d="M6 9v.01M18 15v.01" stroke-linecap="round"/></svg>',
  vod: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/></svg>',
  paid: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
}
// Base order type (header icon + main label) — the 4 kitchen categories
const BASE_TYPE_META = {
  delivery: { key: "delivery", label: "DELIVERY", ar: "دليفري",         color: ORDER_CATEGORY_META.cod.color,    icon: ICONS.delivery },
  talabat:  { key: "talabat",  label: "TALABAT",  ar: "طلبات",          color: ORDER_CATEGORY_META.talabat.color, icon: ICONS.talabat },
  dinein:   { key: "dinein",   label: "DINE IN",  ar: "داين إن",         color: ORDER_CATEGORY_META.dinein.color,  icon: ICONS.dinein },
  pickup:   { key: "pickup",   label: "PICK UP",  ar: "استلام من الفرع", color: ORDER_CATEGORY_META.pickup.color,  icon: ICONS.pickup },
}
function baseTypeKey(order) {
  const k = typeKey(order)
  return (k === "cod" || k === "vod" || k === "paid") ? "delivery" : k
}
function baseTypeMeta(order) { return BASE_TYPE_META[baseTypeKey(order)] || BASE_TYPE_META.pickup }
// Payment sub-label (COD / VOD / PAID) — only meaningful for delivery orders
function payMeta(order) {
  const k = typeKey(order)
  return (k === "cod" || k === "vod" || k === "paid") ? ORDER_CATEGORY_META[k] : null
}
// Colours/labels come from the shared order-category system (matches Dispatcher + print)
const TYPE_META = {
  talabat: { key: "talabat", label: ORDER_CATEGORY_META.talabat.labelEn, ar: ORDER_CATEGORY_META.talabat.labelAr, color: ORDER_CATEGORY_META.talabat.color, icon: ICONS.talabat },
  dinein:  { key: "dinein",  label: ORDER_CATEGORY_META.dinein.labelEn,  ar: ORDER_CATEGORY_META.dinein.labelAr,  color: ORDER_CATEGORY_META.dinein.color,  icon: ICONS.dinein },
  cod:     { key: "cod",     label: ORDER_CATEGORY_META.cod.labelEn,     ar: ORDER_CATEGORY_META.cod.labelAr,     color: ORDER_CATEGORY_META.cod.color,     icon: ICONS.cod },
  vod:     { key: "vod",     label: ORDER_CATEGORY_META.vod.labelEn,     ar: ORDER_CATEGORY_META.vod.labelAr,     color: ORDER_CATEGORY_META.vod.color,     icon: ICONS.vod },
  pickup:  { key: "pickup",  label: ORDER_CATEGORY_META.pickup.labelEn,  ar: ORDER_CATEGORY_META.pickup.labelAr,  color: ORDER_CATEGORY_META.pickup.color,  icon: ICONS.pickup },
  paid:    { key: "paid",    label: ORDER_CATEGORY_META.paid.labelEn,    ar: ORDER_CATEGORY_META.paid.labelAr,    color: ORDER_CATEGORY_META.paid.color,    icon: ICONS.paid },
}
const TYPE_ORDER = ["cod", "vod", "paid", "talabat", "dinein", "pickup"]

function typeKey(order) {
  return orderCategoryKey({
    order_type: order.order_type,
    payment_type: order.custom_payment_type,
    outstanding: order.outstanding_amount,
  })
}
function typeMeta(order) { return TYPE_META[typeKey(order)] }

function whoLabel(order) {
  const k = typeKey(order)
  if (k === "cod" || k === "vod" || k === "paid") return order.rider ? `Rider: ${order.rider}` : "Rider: —"
  if (k === "talabat") return `Rider: ${order.rider || "Talabat"}`
  if (k === "dinein") return order.table_number ? `Table: ${order.table_number}` : "Dine In"
  return order.customer_name || "Customer"
}

// Customer name shown (in addition to the rider) for all delivery order types.
function customerLine(order) {
  const k = typeKey(order)
  if (k === "cod" || k === "vod" || k === "paid" || k === "talabat") return order.customer_name || ""
  return ""
}

// Talabat counter/window number (custom_third_party_referance_number) — Talabat only.
function windowNo(order) {
  return typeKey(order) === "talabat" ? (order.window_no || "") : ""
}

// ── Numbers / clock ──────────────────────────────────────────────────
function displayNumber(order) {
  // Show the real order number as-is (keep hyphens) so supplement orders read
  // correctly — e.g. "M-5-1" instead of "M 5 1".
  const n = order.custom_number_order
  if (n) return String(n)
  return "#" + order.order_no
}
function fmtQty(q) {
  const n = Number(q || 0)
  return Number.isInteger(n) ? n : n.toFixed(0)
}
function formatClock(dt) {
  if (!dt) return ""
  return new Date(dt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
}
const clockTime = computed(() => { nowTs.value; return new Date(nowTs.value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) })
const clockDate = computed(() => { nowTs.value; return new Date(nowTs.value).toLocaleDateString([], { month: "long", day: "numeric", year: "numeric" }) })

// ── Timer / status ───────────────────────────────────────────────────
function elapsedMs(order) {
  timerTick.value
  return Date.now() - new Date(order.order_time).getTime()
}
function timerState(order) {
  const elapsed = elapsedMs(order)
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
const STATUS_COLORS = { green: "#22c55e", amber: "#f59e0b", red: "#ef4444" }
function statusColor(order) { return STATUS_COLORS[timerState(order).color] }
function statusLabel(order) {
  const c = timerState(order).color
  return c === "red" ? "OVERDUE" : c === "amber" ? "DUE SOON" : "ON TIME"
}
function timerLabel(order) { return timerState(order).label }

// ── Filtering ────────────────────────────────────────────────────────
function toggleFilter(t) {
  if (typeFilter.value.has(t)) typeFilter.value.delete(t)
  else typeFilter.value.add(t)
  typeFilter.value = new Set(typeFilter.value)
}
const visibleOrders = computed(() => {
  if (typeFilter.value.size === 0) return orders.value
  return orders.value.filter((o) => typeFilter.value.has(typeKey(o)))
})

// ── Stat cards ───────────────────────────────────────────────────────
const statCards = computed(() => {
  timerTick.value
  let overdue = 0, dueSoon = 0, onTime = 0
  for (const o of visibleOrders.value) {
    const c = timerState(o).color
    if (c === "red") overdue++
    else if (c === "amber") dueSoon++
    else onTime++
  }
  const total = visibleOrders.value.length
  return [
    { label: "Overdue", value: overdue, color: "#ef4444" },
    { label: "Due Soon", sub: "(5–10 min)", value: dueSoon, color: "#f59e0b" },
    { label: "In Progress", sub: "(0–5 min)", value: dueSoon + onTime, color: "#22c55e" },
    { label: "On Time", sub: "(0–5 min)", value: onTime, color: "#22c55e" },
    { label: "Total Orders", value: total, color: "#ffffff" },
  ]
})
const averageLabel = computed(() => {
  timerTick.value
  const list = visibleOrders.value
  if (!list.length) return "00:00"
  const avg = list.reduce((s, o) => s + elapsedMs(o), 0) / list.length
  const mm = String(Math.floor(avg / 60000)).padStart(2, "0")
  const ss = String(Math.floor((avg % 60000) / 1000)).padStart(2, "0")
  return `${mm}:${ss}`
})

// ── Combo helpers ────────────────────────────────────────────────────
function parseRemoved(raw) {
  if (!raw) return []
  try { const p = typeof raw === "string" ? JSON.parse(raw) : raw; return Array.isArray(p) ? p : [] }
  catch (_) { return [] }
}
function groupedItems(order) {
  const items = order.items || []
  const parents = items.filter((i) => !i.is_component)
  const childrenByGroup = {}
  for (const item of items.filter((i) => i.is_component)) {
    const gid = item.combo_group_id || ""
    if (!childrenByGroup[gid]) childrenByGroup[gid] = []
    childrenByGroup[gid].push(item)
  }
  return parents.map((p) => ({ ...p, children: childrenByGroup[p.combo_group_id || ""] || [] }))
}
function isReady(it) {
  return it.station_status === "Ready" || (!it.kds_station && it.station_status !== "Pending" && it.station_status !== "Preparing")
}
// Rows shown under a group's title: its components (with their own notes), or the
// item itself if simple (its note is rendered once via group.special_notes).
function componentRows(group) {
  if (group.children.length) {
    return group.children.map((c) => {
      const total = fmtQty(c.qty)
      const ready = isReady(c)
      return { name: c.item_name, total, done: ready ? total : 0, ready, note: c.special_notes || "" }
    })
  }
  const total = fmtQty(group.qty)
  const ready = isReady(group)
  return [{ name: group.item_name, total, done: ready ? total : 0, ready, note: "" }]
}
function canMarkDone(order) {
  const items = order.items || []
  const stationItems = items.filter((i) => i.kds_station)
  if (stationItems.length === 0) return true
  return stationItems.every((i) => i.station_status === "Ready")
}

// ── Branch ───────────────────────────────────────────────────────────
async function loadBranches() {
  try {
    const result = await call("ecs_posnext.ecs_posnext.api.dispatcher.get_branches")
    branches.value = (result || []).map((b) => b.name)
  } catch (e) { console.error("Failed to load branches", e) }
}
function selectBranch(branch) { selectedBranch.value = branch; router.replace({ query: { branch } }) }
function clearBranch() { selectedBranch.value = ""; router.replace({ query: {} }); orders.value = []; orderColors.clear() }

// ── Sound ────────────────────────────────────────────────────────────
function _playNotes(notes) {
  if (!soundOn.value) return
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
  _playNotes(level === "red"
    ? [{ freq: 1400, start: 0, dur: 0.15 }, { freq: 1400, start: 0.22, dur: 0.15 }]
    : [{ freq: 900, start: 0, dur: 0.2 }])
}
function playDoneSound() { _playNotes([{ freq: 600, start: 0, dur: 0.1, vol: 0.4 }, { freq: 950, start: 0.13, dur: 0.18, vol: 0.4 }]) }
function playNewOrderSound() { _playNotes([{ freq: 820, start: 0, dur: 0.09 }, { freq: 820, start: 0.14, dur: 0.09 }, { freq: 1050, start: 0.28, dur: 0.13 }]) }
function checkColorChanges() {
  for (const order of orders.value) {
    const newColor = timerState(order).color
    const prev = orderColors.get(order.name)
    if (prev && prev !== newColor) playColorSound(newColor)
    orderColors.set(order.name, newColor)
  }
}

// ── Data ─────────────────────────────────────────────────────────────
async function loadOrders() {
  if (!selectedBranch.value) return
  try {
    const result = await call("ecs_posnext.ecs_posnext.api.kds.get_active_orders", { branch: selectedBranch.value })
    const fresh = result || []
    let hasNew = false
    for (const o of fresh) {
      if (!orderColors.has(o.name)) orderColors.set(o.name, timerState(o).color)
      if (!knownOrderNames.has(o.name)) { knownOrderNames.add(o.name); hasNew = true }
    }
    orders.value = fresh
    if (hasNew) playNewOrderSound()
  } catch (e) { console.error("KDS load error", e) }
}
async function markDone(order) {
  // Print the kitchen receipt on Done / Force Done. Fire synchronously within the
  // click gesture so the browser's popup blocker doesn't block the print window.
  printOrder(order)
  try {
    await call("ecs_posnext.ecs_posnext.api.kds.complete_order", { kds_order: order.name, force: 1 })
    playDoneSound()
    orders.value = orders.value.filter((o) => o.name !== order.name)
    orderColors.delete(order.name); knownOrderNames.delete(order.name)
  } catch (e) { console.error("KDS complete error", e) }
}
async function loadSettings() {
  try {
    const result = await call("ecs_posnext.ecs_posnext.api.kds.get_settings", selectedBranch.value ? { branch: selectedBranch.value } : {})
    warningThreshold.value = result?.settings?.warning_threshold_pct || 70
  } catch (e) {}
}

// ── Live ─────────────────────────────────────────────────────────────
function startLive() {
  if (tickInterval) return
  loadSettings(); loadOrders()
  tickInterval = setInterval(() => { timerTick.value++; nowTs.value = Date.now(); checkColorChanges() }, 1000)
  pollInterval = setInterval(loadOrders, 10000)
  socket = initSocket()
  socket.connect()
  socket.on("kds_update", (data) => { if (data?.action === "new_order") playNewOrderSound(); loadOrders() })
}
function stopLive() {
  clearInterval(tickInterval); tickInterval = null
  clearInterval(pollInterval); pollInterval = null
  if (socket) { socket.off("kds_update"); socket = null }
}
watch(selectedBranch, (val) => { if (val) startLive(); else stopLive() })
onMounted(async () => { await loadBranches(); if (selectedBranch.value) startLive() })
onUnmounted(stopLive)
</script>
