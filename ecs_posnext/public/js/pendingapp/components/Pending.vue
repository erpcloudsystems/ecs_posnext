<template>
  <div class="order-container">
    <!-- Top bar -->
    <div class="top-bar">
      <button class="btn btn-back" @click="backToInvoices">{{ __("Back") }}</button>
      <h3 class="page-title">{{ __("Pending") }}</h3>
      <button class="btn btn-done-all" @click="completeAllOrders" :disabled="completingAll">
        {{ completingAll ? __("Processing...") : __("Done All") }}
      </button>
    </div>

    <!-- Item details overlay -->
    <div v-if="itemDetails" class="overlay" @click.self="itemDetails = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ __("Items Selected") }}</h3>
          <button class="btn-close-modal" @click="itemDetails = false">&times;</button>
        </div>
        <div class="modal-body">
          <div v-if="item_loading" class="loading-text">{{ __("Loading...") }}</div>
          <table v-else class="items-table">
            <thead>
              <tr>
                <th>{{ __("Item") }}</th>
                <th>{{ __("QTY") }}</th>
                <th>{{ __("Notes") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in item_selected" :key="item.name">
                <td>{{ item.item_name }}</td>
                <td>{{ item.qty }}</td>
                <td>{{ item.posa_notes }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Orders grid -->
    <div class="orders-grid">
      <div
        v-for="task in filteredTasks"
        :key="task.id"
        class="order-card"
        :style="{ borderTopColor: getTopColor(task) }"
      >
        <div class="card-header" @click="handleClickSalesOrder(task.name)">
          #{{ task.custom_number_order || task.name }}
        </div>
        <div class="card-timer" :class="getTimerClass(task)">
          {{ getElapsedTime(task.creation) }}
        </div>
        <div class="card-customer">{{ task.customer_name }}</div>
        <div v-if="task.custom_table_no" class="card-table">T {{ task.custom_table_no }}</div>
        <hr class="card-divider" />
        <div class="card-action-row">
          <span v-if="task.custom_so_type" class="so-type-badge" :style="getTypeBadgeStyle(task)">
            {{ task.custom_so_type }}
          </span>
          <button class="btn-done" @click="onClickHandle(task)">{{ __("Done") }}</button>
        </div>
        <template v-if="task.posa_notes">
          <hr class="card-divider" />
          <div class="card-notes">{{ task.posa_notes }}</div>
        </template>
        <hr class="card-divider" />
        <ul class="card-items">
          <li v-for="(item, idx) in task.items" :key="idx">
            <span>{{ item.item }}</span>
            <span class="item-notes">{{ item.posa_notes }}</span>
            <span class="item-qty">{{ item.item_qty }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- Loading overlay -->
    <div v-if="loading" class="overlay">
      <div class="spinner"></div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue';

export default {
  setup() {
    const columns = ref([]);
    const loading = ref(false);
    const completingAll = ref(false);
    const itemDetails = ref(false);
    const item_selected = ref([]);
    const item_loading = ref(false);
    const currentTime = ref(new Date());
    let elapsedTimeInterval = null;
    let notificationSound = null;

    const filteredTasks = computed(() => columns.value.tasks || []);

    function getBranchFromCookie() {
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'selected_branch') return decodeURIComponent(value);
      }
      return null;
    }

    function backToInvoices() {
      window.location.href = frappe.urllib.get_base_url() + '/app/posapp';
    }

    function get_sales_order() {
      columns.value = [];
      frappe.call({
        method: 'posawesome.posawesome.api.kitchen_order.get_sales_order3',
        args: { status: 'Pending' },
        callback: (r) => {
          if (!r.exc && r.message && r.message.length > 0) {
            columns.value = r.message[0];
          }
        },
      });
    }

    function handleClickSalesOrder(sales_order) {
      itemDetails.value = true;
      item_loading.value = true;
      frappe.call({
        method: 'posawesome.posawesome.api.kitchen_order.get_items_sales_order',
        args: { name: sales_order },
        callback: (r) => {
          if (!r.exc) {
            item_selected.value = r.message[1];
            item_loading.value = false;
          }
        },
      });
    }

    function onClickHandle(task) {
      const so = task.name;
      const item_row_names = task.items ? task.items.map(i => i.item_row_name) : [];
      let elapsedSeconds = 0;
      if (task.creation) {
        elapsedSeconds = Math.floor((new Date() - new Date(task.creation)) / 1000);
      }
      frappe.call({
        method: 'posawesome.posawesome.api.kitchen_order.update_item_status',
        args: {
          name: so,
          status: 'Preparing',
          item_row_names: JSON.stringify(item_row_names),
          time: elapsedSeconds,
        },
        callback: () => {
          columns.value.tasks = columns.value.tasks.filter(item => item.name !== so);
        },
      });
    }

    async function completeAllOrders() {
      const tasks = filteredTasks.value;
      if (!tasks || tasks.length === 0) {
        frappe.show_alert(__('No orders to complete'));
        return;
      }
      completingAll.value = true;
      try {
        for (const task of tasks) {
          const item_row_names = task.items ? task.items.map(i => i.item_row_name) : [];
          let elapsedSeconds = 0;
          if (task.creation) {
            elapsedSeconds = Math.floor((new Date() - new Date(task.creation)) / 1000);
          }
          await frappe.call({
            method: 'posawesome.posawesome.api.kitchen_order.update_item_status',
            args: {
              name: task.name,
              status: 'Preparing',
              item_row_names: JSON.stringify(item_row_names),
              time: elapsedSeconds,
            },
          });
        }
        get_sales_order();
        frappe.show_alert({ message: __('All orders marked as Done'), indicator: 'green' });
      } catch (error) {
        frappe.show_alert({ message: __('Error completing orders'), indicator: 'red' });
      } finally {
        completingAll.value = false;
      }
    }

    function getElapsedTime(creation) {
      if (!creation) return '';
      const diffSeconds = Math.floor((currentTime.value - new Date(creation)) / 1000);
      if (diffSeconds < 0) return '00:00:00';
      const h = Math.floor(diffSeconds / 3600).toString().padStart(2, '0');
      const m = Math.floor((diffSeconds % 3600) / 60).toString().padStart(2, '0');
      const s = (diffSeconds % 60).toString().padStart(2, '0');
      return `${h}:${m}:${s}`;
    }

    function getTimerClass(task) {
      if (!task.creation) return '';
      const s = Math.floor((new Date() - new Date(task.creation)) / 1000);
      if (s > 600) return 'timer-red';
      if (s > 300) return 'timer-orange';
      return 'timer-green';
    }

    function getTopColor(task) {
      const t = task.custom_so_type;
      if (t === 'Delivery') return '#E53A40';
      if (t === 'Pickup' || t === 'Pick Up') return '#379392';
      if (t === 'Car Service') return '#6AAFE6';
      return '#FFBC42';
    }

    function getTypeBadgeStyle(task) {
      const t = task.custom_so_type;
      if (t === 'Delivery') return 'color:#E53A40;background:#fde4e4';
      if (t === 'Pickup' || t === 'Pick Up') return 'color:#379392;background:#d6f1ec';
      if (t === 'Car Service') return 'color:#6AAFE6;background:#e0f0fb';
      return '';
    }

    function handleNewOrder() {
      if (notificationSound) notificationSound.play().catch(() => {});
      get_sales_order();
    }

    onMounted(() => {
      notificationSound = new Audio('/assets/frappe/sounds/alert.mp3');
      get_sales_order();
      frappe.realtime.on('order_pending', handleNewOrder);
      frappe.realtime.on('order_cancelled', get_sales_order);
      elapsedTimeInterval = setInterval(() => { currentTime.value = new Date(); }, 1000);
    });

    onBeforeUnmount(() => {
      frappe.realtime.off('order_pending', handleNewOrder);
      frappe.realtime.off('order_cancelled', get_sales_order);
      if (elapsedTimeInterval) clearInterval(elapsedTimeInterval);
    });

    return {
      columns, loading, completingAll, itemDetails, item_selected, item_loading,
      filteredTasks, currentTime,
      backToInvoices, handleClickSalesOrder, onClickHandle, completeAllOrders,
      getElapsedTime, getTimerClass, getTopColor, getTypeBadgeStyle,
    };
  },
};
</script>

<style scoped>
.order-container { padding: 8px; }
.top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding: 8px 0; }
.page-title { margin: 0; font-size: 20px; font-weight: 600; }
.btn { padding: 8px 24px; border: none; border-radius: 6px; font-size: 16px; font-weight: 500; cursor: pointer; }
.btn-back { background: #FF9800; color: #fff; }
.btn-back:hover { background: #F57C00; }
.btn-done-all { background: #66BB6A; color: #fff; }
.btn-done-all:hover { background: #43A047; }
.btn-done-all:disabled { opacity: 0.6; cursor: not-allowed; }
.orders-grid { display: flex; flex-wrap: wrap; gap: 16px; }
.order-card {
  min-width: 250px; max-width: 300px; flex: 1 1 250px;
  border: 1px solid #e0e0e0; border-top-width: 6px; border-top-style: solid;
  border-radius: 15px; background: #fff; padding: 0;
  box-shadow: 0 1px 1px rgba(0,0,0,0.08), 0 2px 2px rgba(0,0,0,0.08), 0 4px 4px rgba(0,0,0,0.08);
  transition: box-shadow 0.3s ease;
}
.order-card:hover { box-shadow: 0 2px 4px rgba(0,0,0,0.12), 0 4px 8px rgba(0,0,0,0.12); }
.card-header { text-align: center; padding: 12px 12px 4px; color: gray; font-size: 18px; font-weight: 600; cursor: pointer; }
.card-timer { text-align: center; font-size: 14px; padding: 2px 0; }
.timer-green { color: #16a34a; }
.timer-orange { color: #ea580c; }
.timer-red { color: #dc2626; }
.card-customer { text-align: center; padding: 4px 12px; font-weight: 500; font-size: 16px; }
.card-table { text-align: center; padding: 0 12px 4px; font-size: 14px; }
.card-divider { margin: 4px 0; border: none; border-top: 1px solid #e0e0e0; }
.card-action-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 16px; }
.so-type-badge { padding: 2px 7px; border-radius: 4px; font-size: 18px; font-weight: 500; }
.btn-done { color: #16a34a; font-weight: 500; font-size: 18px; background: rgba(22,163,74,0.1); border: none; border-radius: 4px; padding: 2px 10px; cursor: pointer; }
.btn-done:hover { background: rgba(22,163,74,0.2); }
.card-notes { text-align: center; padding: 4px 12px; font-size: 13px; color: #555; }
.card-items { list-style: none; padding: 4px 16px 12px; margin: 0; }
.card-items li { display: flex; justify-content: space-between; gap: 8px; padding: 2px 0; font-size: 14px; }
.item-notes { color: #888; font-size: 12px; }
.item-qty { color: #16a34a; font-weight: 600; }

/* Overlay / Modal */
.overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); z-index: 1000; display: flex; align-items: center; justify-content: center; }
.modal-card { background: #fff; border-radius: 12px; width: 90%; max-width: 800px; max-height: 80vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #e0e0e0; }
.modal-header h3 { margin: 0; color: #0097A7; }
.btn-close-modal { background: none; border: none; font-size: 24px; cursor: pointer; color: #666; }
.modal-body { padding: 16px 20px; }
.items-table { width: 100%; border-collapse: collapse; }
.items-table th, .items-table td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }
.items-table th { font-weight: 600; background: #f5f5f5; }
.loading-text { text-align: center; padding: 20px; color: #888; }
.spinner { width: 48px; height: 48px; border: 4px solid #e0e0e0; border-top-color: #0097A7; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
