<template>
  <v-container fluid>
    <v-card
      flat
      class="cards mb-2 mt-2 py-0"
      style="max-height: 11vh; height: 11vh"
    >
      <v-row align="start" no-gutters>
        <v-col cols="3">
          <v-btn
            block
            class="pa-1"
            large
            color="warning"
            dark
            @click="back_to_invoices"
          >
            {{ __("Back") }}
          </v-btn>
        </v-col>
      </v-row>
    </v-card>
    <div class="row columns">
      <v-card-title>{{ __("Preparing") }}</v-card-title>
    </div>
    <template v-if="itemDetails">
      <div>
        <v-card
          class="selection mx-auto grey lighten-5"
          style="max-height: 80vh; height: 80vh"
        >
          <v-card-title>
            <span class="text-h6 primary--text">{{
              __("Items Selected")
            }}</span>
          </v-card-title>
          <div class="my-0 py-0 overflow-y-auto" style="max-height: 75vh">
            <template>
              <v-container>
                <v-data-table
                  v-model="expanded"
                  :headers="headers"
                  :items="item_selected"
                  :single-expand="singleExpand"
                  :expanded.sync="expanded"
                  :loading="item_loading"
                  show-expand
                  item-key="posa_row_id"
                  class="elevation-1"
                  hide-default-footer
                >
                  <!-- Main row content -->

                  <!-- Expandable row content -->
                  <template v-slot:expanded-item="{ headers, item }">
                    <td :colspan="headers.length" class="ma-0 pa-0">
                      <v-data-table
                        :headers="subHeaders"
                        :items="item.items"
                        dense
                        :loading="item_loading"
                        hide-default-footer
                      >
                      </v-data-table>
                    </td>
                  </template>
                </v-data-table>
              </v-container>
            </template>
          </div>
        </v-card>

        <v-card
          flat
          style="max-height: 11vh; height: 11vh"
          class="cards mb-0 mt-3 py-0"
        >
          <v-row align="start" no-gutters>
            <v-col cols="12">
              <v-btn
                block
                class="pa-1"
                large
                color="warning"
                dark
                @click="back_to_invoice"
                >{{ __("Back") }}</v-btn
              >
            </v-col>
          </v-row>
        </v-card>
      </div>
    </template>
    <div class="kanban-board">
      <div class="row columns" style="margin: 0">
        <v-card
          v-if="!itemDetails"
          v-for="task in filteredTasks"
          :key="task.id"
          outlined
          class=""
          style="
            border-top-width: 6px;
            border-top-style: solid;
            border-radius: 15px;
            box-shadow:
              0 1px 1px rgba(0, 0, 0, 0.08),
              0 2px 2px rgba(0, 0, 0, 0.08),
              0 4px 4px rgba(0, 0, 0, 0.08);
            transition: box-shadow 0.3s ease;
          "
          :style="
            task.custom_so_type == 'Delivery'
              ? 'border-top-color: #E53A40'
              : task.custom_so_type == 'Pickup' ||
                  task.custom_so_type == 'Pick Up'
                ? 'border-top-color: #379392'
                : task.custom_so_type == 'Car Service'
                  ? 'border-top-color: #6AAFE6'
                  : 'border-top-color: #FFBC42'
          "
          min-width="250px"
        >
          <!-- Timer component that accepts inputTime -->
          <v-card-title
            class="cursor-pointer p-3 pb-2 text-center d-block"
            style="color: gray"
            @click="handleClickSalesOrder(task.name)"
          >
            #{{ task.custom_number_order || task.name }} {{ task.branch }}
          </v-card-title>
          <v-card-title class="px-3 py-0 text-center d-block">
            {{ task.customer_name }}
          </v-card-title>
          <v-divider></v-divider>
          <div
            style="
              display: flex;
              justify-content: space-between;
              padding: 0 1rem;
              align-items: center;
            "
          >
            <span
              v-if="task.custom_so_type"
              style="padding: 2px 7px; border-radius: 4px; font-size: 12px"
              :style="
                task.custom_so_type == 'Delivery'
                  ? 'color: #E53A40; background-color: #fde4e4;'
                  : task.custom_so_type == 'Pickup' ||
                      task.custom_so_type == 'Pick Up'
                    ? 'color: #379392; background-color: #d6f1ec;'
                    : task.custom_so_type == 'Car Service'
                      ? 'color: #6AAFE6; background-color: #e0f0fb;'
                      : ''
              "
            >
              {{ task.custom_so_type }}
            </span>
            <Timer :inputTime="task.time || 1800" :id="task.name" />
            <button
              style="
                color: rgb(22, 163, 74);
                font-weight: 500;
                font-size: 12px;
                background: rgb(22 163 74 / 10%);
                border-radius: 4px;
                padding: 2px 10px;
              "
              @click="
                onClickHandle(
                  task.name,
                  task.custom_so_type,
                  task.name,
                  task.branch,
                )
              "
            >
              {{ __("Done") }}
            </button>
          </div>
          <!-- <div style="text-align: left;">{{ task.custom_so_type }}</div> -->
          <v-divider></v-divider>
          <div
            style="
              display: flex;
              justify-content: flex-start;
              padding: 0 1rem;
              align-items: center;
            "
          >
            <span
              class="mr-4"
              style="font-weight: 500; font-size: 16px; color: black"
            >
              {{ __("Total") }} :
            </span>
            <span style="font-weight: 500; font-size: 14px; color: gray">
              {{ task.grand_total }}
            </span>
          </div>
          <v-divider v-if="task.posa_notes"></v-divider>
          <div class="px-3 text-center">
            <span>
              {{ task.posa_notes }}
            </span>
          </div>
          <v-divider></v-divider>
          <div>
            <ul>
              <li v-for="item in task.items" :key="item">
                {{ item }}
              </li>
            </ul>
          </div>
        </v-card>
      </div>
    </div>
  </v-container>
</template>

<script>
import draggable from "vuedraggable";
import Timer from "../Timer/Timer.vue";
export default {
  components: {
    draggable,
    Timer,
  },
  data() {
    return {
      columns: [],
      branch: null,
      itemDetails: false,
      selected_items_header: [
        {
          text: __("Item"),
          align: "start",
          sortable: true,
          value: "item_code",
        },
        {
          text: __("QTY"),
          align: "start",
          sortable: true,
          value: "qty",
        },
      ],
      selected_items: [],
      item_loading: false,
      expanded: [],
      headers: [
        { text: __("Item"), value: "parent_item_code" },
        { text: __("Qty"), value: "qty" },
      ],
      subHeaders: [
        { text: __("Item"), value: "item_code" },
        { text: __("Qty"), value: "qty" },
      ],
      loading: false,
      pos_profile: "",
      item_selected: [],
      allItems: [],
      discount_percentage_offer_name: null,
      itemsPerPage: 1000,
      singleExpand: true,
      items_headers: [
        { text: __("Name"), value: "item_code", align: "start" },
        { text: __("QTY"), value: "qty", align: "start" },
      ],
    };
  },
  computed: {
    filteredTasks() {
      let tasks = this.columns.tasks || [];

      // فلترة حسب الـ branch إذا كان متوفر
      if (this.branch)
        tasks = tasks.filter((task) => task.branch === this.branch);

      return tasks;
    },
  },
  methods: {
    getBranchFromCookie() {
      const cookies = document.cookie.split(";");
      for (let cookie of cookies) {
        const [name, value] = cookie.trim().split("=");
        if (name === "selected_branch") {
          return decodeURIComponent(value);
        }
      }
      return null;
    },
    back_to_invoices() {
      window.location.href = frappe.urllib.get_base_url() + "/app/posapp";
    },

    back_to_invoice() {
      this.itemDetails = false;
    },
    handleClickSalesOrder(sales_order) {
      this.itemDetails = true;
      this.item_loading = true;
      frappe.call({
        method: "posawesome.posawesome.api.kitchen_order.get_items_sales_order",
        args: {
          name: sales_order,
        },
        callback: (r) => {
          if (!r.exc) {
            console.log(r.message);
            const transformed = r.message[0].reduce((acc, curr) => {
              let group = acc.find(
                (g) =>
                  g.parent_item_code === curr.parent_item_code &&
                  g.posa_row_id === curr.posa_row_id,
              );
              if (!group) {
                group = {
                  parent_item_code: curr.parent_item_code,
                  posa_row_id: curr.posa_row_id,
                  items: [],
                };
                acc.push(group);
              }
              group.items.push({ item_code: curr.item_code, qty: curr.qty });
              return acc;
            }, []);
            this.item_selected = transformed;
            const result = r.message[1].reduce((acc, item) => {
              acc[item.posa_row_id] = item;
              return acc;
            }, {});
            this.item_selected.forEach((i) => {
              // i.posa_notes = result[i.posa_row_id].posa_notes
              if (result[i.posa_row_id].posa_notes)
                i.items.push({
                  item_code: "Notes: " + result[i.posa_row_id].posa_notes,
                });
              i.qty = result[i.posa_row_id].qty;
            });
            this.item_loading = false;
          }
        },
      });
      console.log(sales_order);
    },
    getColumnClass(columnName) {
      switch (columnName) {
        case "Preparing":
          return "preparing-column";
        default:
          return "";
      }
    },

    onClickHandle(so) {
      const savedTime = localStorage.getItem(`timer_${so}`);
      let timeInSeconds = 0;
      if (savedTime) {
        const { remainingTime } = JSON.parse(savedTime);
        timeInSeconds = remainingTime > 0 ? remainingTime : 0;
      }
      frappe.call({
        method: "posawesome.posawesome.api.kitchen_order.update_sales_order",
        args: {
          name: so,
          status: "Packing",
          time: timeInSeconds,
        },
        callback: (r) => {
          this.columns.tasks = this.columns.tasks.filter(function (item) {
            return item.name !== so;
          });
        },
      });

      // console.log("Drag changed",   event);
      // console.log("column",   column);
      // Optional: Save changes to a database or server
    },
    cloneTask(task) {
      return { ...task };
    },
    handleRealtimeUpdate(data) {
      console.log(data);
      // Check if the new order should be added to the corresponding column
      // const column = this.columns.tasks.find(col => col.name === data.order_id);
      // Add the new task to the correct column
      this.columns.tasks.push({
        id: data.order_id,
        name: data.order_id,
        status_name: data.status_name,
        customer_name: data.customer_name,
        timer: data.status_name,
        custom_so_type: data.custom_so_type,
        items: data.items,
        branch: data.branch,
        posa_notes: data.posa_notes,
      });
    },
    get_sales_order() {
      const args = {
        status: "Preparing",
      };

      // إضافة branch كفلتر إذا كان متوفر
      if (this.branch) {
        args.branch = this.branch;
      }

      frappe.call({
        method: "posawesome.posawesome.api.kitchen_order.get_sales_order3",
        args: args,
        callback: (r) => {
          if (!r.exc) {
            if (r.message.length > 0) {
              this.columns = r.message[0];
            }
            console.log(r.message);
          }
        },
      });
    },
  },
  mounted: function () {
    this.branch = this.getBranchFromCookie();
    // Fetch data when the component is mounted
    this.get_sales_order();
    frappe.realtime.on("order_preparing", this.handleRealtimeUpdate);
  },
  beforeDestroy() {
    // Cleanup the realtime listener
    frappe.realtime.off("order_preparing", this.handleRealtimeUpdate);
  },
};
</script>

<style scoped>
.kanban-board {
  display: flex;
}
.columns {
  display: flex;
  gap: 20px;
}
.column {
  width: 250px;
}
.column-card {
  padding: 10px;
  background-color: #f4f4f4;
}
.task-list {
  min-height: 50px;
}
.task-card {
  margin-top: 10px;
  background-color: #ffffff;
}
/* Column color styles */
.order-received-column {
  background-color: #fc7e08; /* Light orange */
  color: white;
}

.preparing-column {
  background-color: #5bc0de; /* Light blue */
  color: white;
}

.dining-column {
  background-color: #d9534f; /* Light red */
  color: white;
}

.packing-column {
  background-color: #f7b731; /* Light yellow */
  color: white;
}

.ready-to-pick-up-column {
  background-color: #0275d8; /* Light blue */
  color: white;
}

.completed-column {
  background-color: #5cb85c;
  color: white;
}
</style>
