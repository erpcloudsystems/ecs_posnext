<template>
  <div class="min-h-screen bg-gray-900 text-white p-6">

    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold">KDS Stations</h1>
        <p class="text-gray-400 text-sm mt-0.5">{{ stations.length }} station(s) active</p>
      </div>
      <div class="flex items-center gap-3">
        <button
          @click="loadStations"
          class="px-4 py-2 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 transition-colors"
        >
          ↻ Refresh
        </button>
        <button
          @click="goToAssembly"
          class="px-5 py-2.5 rounded-lg text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 active:scale-95 transition-all"
        >
          Assembly View →
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="text-gray-500 text-lg">Loading stations…</div>
    </div>

    <!-- No stations -->
    <div v-else-if="stations.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-500">
      <div class="text-5xl mb-4">📋</div>
      <p class="text-xl">No active stations found</p>
      <p class="text-sm mt-2 text-gray-600">Go to KDS Station doctype and create stations with Is Active checked</p>
    </div>

    <!-- Stations grid -->
    <div v-else class="grid gap-5" style="grid-template-columns: repeat(auto-fill, minmax(260px, 1fr))">
      <div
        v-for="station in stations"
        :key="station.name"
        class="bg-gray-800 rounded-2xl overflow-hidden shadow-xl flex flex-col hover:ring-2 hover:ring-indigo-500 transition-all cursor-pointer"
        @click="openStation(station)"
      >
        <!-- Card header -->
        <div class="px-5 pt-5 pb-3 flex items-start justify-between">
          <div>
            <h2 class="text-2xl font-bold leading-tight">{{ station.station_name }}</h2>
            <p v-if="station.branch" class="text-gray-400 text-xs mt-1">{{ station.branch }}</p>
          </div>
          <span
            :class="[
              'text-sm font-bold px-3 py-1 rounded-full shrink-0',
              station.pending_orders > 0
                ? 'bg-amber-500 text-gray-900'
                : 'bg-gray-700 text-gray-400'
            ]"
          >
            {{ station.pending_orders }}
          </span>
        </div>

        <!-- Status label -->
        <div class="px-5 pb-4 flex-1">
          <p class="text-gray-400 text-sm">
            {{ station.pending_orders === 0
              ? 'All clear'
              : station.pending_orders === 1
                ? '1 pending order'
                : `${station.pending_orders} pending orders` }}
          </p>
          <p v-if="station.enable_special_print" class="text-xs text-amber-400 mt-1">
            ★ Special print enabled
          </p>
        </div>

        <!-- Open button -->
        <div class="px-5 pb-5">
          <button
            class="w-full py-3 rounded-xl text-base font-bold transition-all active:scale-95"
            :class="station.pending_orders > 0
              ? 'bg-indigo-600 hover:bg-indigo-500 text-white'
              : 'bg-gray-700 hover:bg-gray-600 text-gray-300'"
            @click.stop="openStation(station)"
          >
            Open Station
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue"
import { call } from "frappe-ui"
import { useRouter } from "vue-router"
import { initSocket } from "@/socket"

const router = useRouter()

const stations = ref([])
const loading = ref(true)

let pollInterval = null
let socket = null

function openStation(station) {
  const query = station.branch ? { branch: station.branch } : {}
  router.push({
    name: "KDSStation",
    params: { station: station.station_name },
    query,
  })
}

function goToAssembly() {
  router.push({ name: "KDSAssembly" })
}

async function loadStations() {
  try {
    const result = await call("ecs_posnext.ecs_posnext.api.kds.get_stations_summary")
    stations.value = result || []
  } catch (_) {}
  loading.value = false
}

onMounted(() => {
  loadStations()
  pollInterval = setInterval(loadStations, 10000)
  socket = initSocket()
  socket.connect()
  socket.on("kds_update", loadStations)
})

onUnmounted(() => {
  clearInterval(pollInterval)
  if (socket) { socket.off("kds_update"); socket = null }
})
</script>
