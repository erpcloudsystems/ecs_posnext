<template>
  <div class="order-container">
    <div class="top-bar">
      <button class="btn btn-back" @click="goBack">{{ __('Back') }}</button>
      <h3 class="page-title">{{ __('Packing') }}</h3>
      <button class="btn btn-done-all" @click="completeAllOrders" :disabled="completingAll">
        {{ completingAll ? __('Processing...') : __('Done All') }}
      </button>
    </div>

    <!-- Driver selection dialog -->
    <div v-if="openDriver" class="overlay" @click.self="openDriver = false">
      <div class="modal-card" style="max-width: 500px;">
        <div class="modal-header">
          <h3>{{ __('Select Driver') }}</h3>
          <button class="btn-close-modal" @click="openDriver = false">&times;</button>
        </div>
        <div class="modal-body">
          <input v-model="driverSearch" type="text" class="search-input" :placeholder="__('Search Driver...')" />
          <div class="driver-list">
            <div v-for="driver in filteredDrivers" :key="driver.name"
              class="driver-item" :class="{ 'driver-selected': selectedDriver === driver.name }"
              @click="selectedDriver = driver.name">
              {{ driver.full_name || driver.name }}
            </div>
            <div v-if="filteredDrivers.length === 0" class="loading-text">{{ __('No drivers found') }}</div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-back" @click="openDriver = false">{{ __('Cancel') }}</button>
          <button class="btn btn-done-all" @click="submitDriver">{{ __('Done') }}</button>
        </div>
      </div>
    </div>

    <!-- Item details dialog -->
    <div v-if="itemDetails" class="overlay" @click.self="itemDetails = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ __('Items Selected') }}</h3>
          <button class="btn-close-modal" @click="itemDetails = false">&times;</button>
        </div>
        <div class="modal-body">
          <div v-if="itemLoading" class="loading-text">{{ __('Loading...') }}</div>
          <table v-else class="items-table">
            <thead><tr><th>{{ __('Item') }}</th><th>{{ __('QTY') }}</th><th>{{ __('Notes') }}</th></tr></thead>
            <tbody>
              <tr v-for="item in itemSelected" :key="item.name">
                <td>{{ item.item_name }}</td><td>{{ item.qty }}</td><td>{{ item.posa_notes }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="orders-grid">
      <div v-for="task in filteredTasks" :key="task.id" class="order-card" :style="{ borderTopColor: getTopColor(task) }">
        <div class="card-header" @click="handleClickSalesOrder(task.name)">#{{ task.custom_number_order || task.name }}</div>
        <div class="card-timer" :class="getTimerClass(task)">{{ getElapsedTime(task.creation) }}</div>
        <div class="card-customer">{{ task.customer_name }}</div>
        <div v-if="task.custom_table_no" class="card-table">T {{ task.custom_table_no }}</div>
        <hr class="card-divider" />
        <div class="card-action-row">
          <span v-if="task.custom_so_type" class="so-type-badge" :style="getTypeBadgeStyle(task)">{{ task.custom_so_type }}</span>
          <button class="btn-done" @click="onClickHandle(task)">{{ __('Done') }}</button>
        </div>
        <template v-if="task.posa_notes"><hr class="card-divider" /><div class="card-notes">{{ task.posa_notes }}</div></template>
        <hr class="card-divider" />
        <ul class="card-items">
          <li v-for="(item, idx) in task.items" :key="idx">
            <span>{{ item.item }}</span><span class="item-notes">{{ item.posa_notes }}</span><span class="item-qty">{{ item.item_qty }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import { call } from '@/utils/apiWrapper';
import { useSocket, initSocket } from '@/socket';

const router = useRouter();
const columns = ref([]);
const completingAll = ref(false);
const itemDetails = ref(false);
const itemSelected = ref([]);
const itemLoading = ref(false);
const currentTime = ref(new Date());
const openDriver = ref(false);
const selectedDriver = ref(null);
const driverSearch = ref('');
const drivers = ref([]);
const currentSO = ref(null);
const currentTask = ref(null);
const currentElapsedTime = ref(0);
let timerInterval = null;

const filteredTasks = computed(() => columns.value.tasks || []);
const filteredDrivers = computed(() => {
  if (!driverSearch.value) return drivers.value;
  const s = driverSearch.value.toLowerCase();
  return drivers.value.filter(d => (d.full_name || d.name).toLowerCase().includes(s));
});

function goBack() { router.push('/'); }

async function getSalesOrder() {
  columns.value = [];
  try {
    const r = await call('ecs_posnext.api.kitchen_order.get_orders', { status: 'Packing' });
    if (r && r.length > 0) columns.value = r[0];
  } catch (e) { console.error('Error fetching packing orders:', e); }
}

async function getDrivers() {
  try {
    const r = await call('frappe.client.get_list', { doctype: 'Driver', fields: ['name', 'full_name'], limit_page_length: 1000 });
    drivers.value = r || [];
  } catch (e) { console.error('Error fetching drivers:', e); }
}

async function handleClickSalesOrder(salesOrder) {
  itemDetails.value = true; itemLoading.value = true;
  try {
    const r = await call('ecs_posnext.api.kitchen_order.get_items', { name: salesOrder });
    itemSelected.value = r[1] || r;
  } catch (e) { console.error('Error fetching items:', e); }
  finally { itemLoading.value = false; }
}

function onClickHandle(task) {
  currentTask.value = task;
  const elapsedSeconds = task.creation ? Math.floor((new Date() - new Date(task.creation)) / 1000) : 0;
  currentElapsedTime.value = elapsedSeconds;

  if (task.custom_so_type === 'Delivery') {
    currentSO.value = task.name;
    openDriver.value = true;
    getDrivers();
  } else {
    doComplete(task.name, 'Completed', null, elapsedSeconds, task);
  }
}

async function submitDriver() {
  if (!selectedDriver.value) return;
  openDriver.value = false;
  await doComplete(currentSO.value, 'Delivery', selectedDriver.value, currentElapsedTime.value, currentTask.value);
  selectedDriver.value = null;
  driverSearch.value = '';
}

async function doComplete(so, status, driver, elapsedSeconds, task) {
  const item_row_names = task && task.items ? task.items.map(i => i.item_row_name) : [];
  try {
    await call('ecs_posnext.api.kitchen_order.update_item_status', {
      name: so, status, item_row_names: JSON.stringify(item_row_names), driver: driver || null, time: elapsedSeconds,
    });
    columns.value.tasks = columns.value.tasks.filter(item => item.name !== so);
  } catch (e) { console.error('Error completing order:', e); }
}

async function completeAllOrders() {
  const tasks = filteredTasks.value.filter(t => t.custom_so_type !== 'Delivery');
  if (!tasks || tasks.length === 0) return;
  completingAll.value = true;
  try {
    for (const task of tasks) {
      const item_row_names = task.items ? task.items.map(i => i.item_row_name) : [];
      const elapsedSeconds = task.creation ? Math.floor((new Date() - new Date(task.creation)) / 1000) : 0;
      await call('ecs_posnext.api.kitchen_order.update_item_status', {
        name: task.name, status: 'Completed', item_row_names: JSON.stringify(item_row_names), time: elapsedSeconds,
      });
    }
    await getSalesOrder();
  } catch (e) { console.error('Error completing all:', e); }
  finally { completingAll.value = false; }
}

function getElapsedTime(creation) {
  if (!creation) return '';
  const d = Math.floor((currentTime.value - new Date(creation)) / 1000);
  if (d < 0) return '00:00:00';
  return `${String(Math.floor(d / 3600)).padStart(2, '0')}:${String(Math.floor((d % 3600) / 60)).padStart(2, '0')}:${String(d % 60).padStart(2, '0')}`;
}
function getTimerClass(task) { if (!task.creation) return ''; const s = Math.floor((new Date() - new Date(task.creation)) / 1000); if (s > 600) return 'timer-red'; if (s > 300) return 'timer-orange'; return 'timer-green'; }
function getTopColor(task) { const t = task.custom_so_type; if (t === 'Delivery') return '#E53A40'; if (t === 'Pickup' || t === 'Pick Up') return '#379392'; if (t === 'Car Service') return '#6AAFE6'; return '#FFBC42'; }
function getTypeBadgeStyle(task) { const t = task.custom_so_type; if (t === 'Delivery') return 'color:#E53A40;background:#fde4e4'; if (t === 'Pickup' || t === 'Pick Up') return 'color:#379392;background:#d6f1ec'; if (t === 'Car Service') return 'color:#6AAFE6;background:#e0f0fb'; return ''; }

function handleMsgFallback(data) {
  const event = data?.event || data?.message?.event;
  if (event === 'kitchen_order_packing') getSalesOrder();
}

let _socket = null;

function setupSocket() {
  _socket = useSocket();
  if (!_socket) {
    const siteName = window.frappe?.boot?.sitename || window.site_name || window.location.hostname;
    _socket = initSocket(siteName);
  }
  if (_socket) {
    _socket.connect();
    _socket.on('kitchen_order_packing', getSalesOrder);
    _socket.on('msg', handleMsgFallback);
  }
}

onMounted(() => {
  getSalesOrder();
  setupSocket();
  timerInterval = setInterval(() => { currentTime.value = new Date(); }, 1000);
});
onBeforeUnmount(() => {
  if (_socket) {
    _socket.off('kitchen_order_packing', getSalesOrder);
    _socket.off('msg', handleMsgFallback);
  }
  if (timerInterval) clearInterval(timerInterval);
});
</script>

<style scoped>
.order-container { padding: 12px; min-height: 100vh; background: #f8f9fa; }
.top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 22px; font-weight: 700; color: #333; }
.btn { padding: 10px 28px; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
.btn-back { background: #FF9800; color: #fff; } .btn-back:hover { background: #F57C00; }
.btn-done-all { background: #66BB6A; color: #fff; } .btn-done-all:hover { background: #43A047; }
.btn-done-all:disabled { opacity: 0.6; cursor: not-allowed; }
.orders-grid { display: flex; flex-wrap: wrap; gap: 16px; }
.order-card { min-width: 250px; max-width: 310px; flex: 1 1 250px; border: 1px solid #e0e0e0; border-top-width: 6px; border-top-style: solid; border-radius: 14px; background: #fff; box-shadow: 0 1px 2px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.06); transition: box-shadow 0.3s; }
.order-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.card-header { text-align: center; padding: 12px 12px 4px; color: #888; font-size: 18px; font-weight: 700; cursor: pointer; }
.card-timer { text-align: center; font-size: 14px; }
.timer-green { color: #16a34a; } .timer-orange { color: #ea580c; } .timer-red { color: #dc2626; }
.card-customer { text-align: center; padding: 4px 12px; font-weight: 600; font-size: 16px; color: #333; }
.card-table { text-align: center; padding: 0 12px 4px; font-size: 14px; color: #555; }
.card-divider { margin: 4px 0; border: none; border-top: 1px solid #eee; }
.card-action-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 16px; }
.so-type-badge { padding: 2px 8px; border-radius: 6px; font-size: 16px; font-weight: 600; }
.btn-done { color: #16a34a; font-weight: 600; font-size: 17px; background: rgba(22,163,74,0.08); border: none; border-radius: 6px; padding: 4px 14px; cursor: pointer; } .btn-done:hover { background: rgba(22,163,74,0.18); }
.card-notes { text-align: center; padding: 4px 12px; font-size: 13px; color: #666; }
.card-items { list-style: none; padding: 6px 16px 12px; margin: 0; }
.card-items li { display: flex; justify-content: space-between; gap: 8px; padding: 3px 0; font-size: 14px; }
.item-notes { color: #999; font-size: 12px; } .item-qty { color: #16a34a; font-weight: 700; }
.overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 1000; display: flex; align-items: center; justify-content: center; }
.modal-card { background: #fff; border-radius: 14px; width: 90%; max-width: 800px; max-height: 80vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #eee; }
.modal-header h3 { margin: 0; color: #0097A7; }
.btn-close-modal { background: none; border: none; font-size: 24px; cursor: pointer; color: #888; }
.modal-body { padding: 16px 20px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 20px; border-top: 1px solid #eee; }
.items-table { width: 100%; border-collapse: collapse; }
.items-table th, .items-table td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #f0f0f0; }
.items-table th { font-weight: 700; background: #fafafa; }
.loading-text { text-align: center; padding: 24px; color: #999; }
.search-input { width: 100%; padding: 10px 12px; border: 1px solid #ccc; border-radius: 8px; font-size: 14px; margin-bottom: 8px; }
.driver-list { max-height: 250px; overflow-y: auto; }
.driver-item { padding: 10px 12px; cursor: pointer; border-bottom: 1px solid #f5f5f5; border-radius: 6px; }
.driver-item:hover { background: #e3f2fd; }
.driver-selected { background: #bbdefb; font-weight: 700; }
</style>
