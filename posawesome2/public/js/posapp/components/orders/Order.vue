<template>
  <v-container fluid class="m-0 p-0">
    <!-- Back Button -->
    <v-card flat class="cards mb-2 mt-2 py-0" style="max-height: 11vh; height: 11vh">
      <v-row align="start" no-gutters>
        <v-col cols="3">
          <v-btn block class="pa-1" large color="warning" dark @click="back_to_invoice">
            {{ __("Back") }}
          </v-btn>
        </v-col>
      </v-row>
    </v-card>

    <!-- Dialog Section -->
    <v-dialog v-model="itemDetails" max-width="1200px" class="overflow-y-none grey lighten-5">
      <v-card class="cards my-0 p-0 grey lighten-5" v-if="itemDetails">
        <v-data-table :headers="selected_items_header" :items="selected_items" :loading="item_loading" item-key="name"
          class="elevation-1 mt-0">
        </v-data-table>
      </v-card>
    </v-dialog>

    <!-- Kanban Board -->
    <div class="kanban-board">
      <div class="columns">
        <div v-for="(column, columnIndex) in columns" :key="columnIndex" class="column">
          <v-card outlined class="column-card">
            <v-card-title :class="getColumnClass(column.name)">
              {{ column.name }}
            </v-card-title>
            <v-divider></v-divider>

            <v-card v-for="(task, index) in column.tasks" :key="task.id" outlined class="task-card">
              <v-card-text>
                <b>#{{ task.custom_number_order || task.name }} </b> <br />
                <b>Customer: </b> {{ task.customer_name }} <br />
                <b>Branch: </b>{{ task.branch }} <br />
                <b>Total: </b>{{ task.grand_total }} <br />
                <b>Items</b>
                <ul>
                  <li v-for="(item, index) in task.items" :key="index">
                    {{ item }}
                  </li>
                </ul>
              </v-card-text>
            </v-card>
          </v-card>
        </div>
      </div>
    </div>
  </v-container>
</template>

<script>
import draggable from "vuedraggable";

export default {
  components: {
    draggable,
  },
  data() {
    return {
      columns: [],
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
    };
  },
  methods: {
    back_to_invoice() {
      window.location.href = frappe.urllib.get_base_url() + "/app/posapp";
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
            this.selected_items = r.message;
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
        case "Dining":
          return "dining-column";
        case "Packing":
          return "packing-column";
        case "Delivery":
          return "delivery-column";
        case "Completed":
          return "completed-column";
        default:
          return "";
      }
    },
    onDragChange(event, column) {
      // let column = event.newIndex;
      if (event.hasOwnProperty("added")) {
        const name_order = event.added.element.name;
        event.added.element.status_name = column.name;
        frappe.call({
          method: "posawesome.posawesome.api.kitchen_order.update_sales_order",
          args: {
            name: name_order,
            status: event.added.element.status_name,
          },
          callback: (r) => {
            if (!r.exc) {
            }
          },
        });
      }

      // Optional: Save changes to a database or server
    },
    cloneTask(task) {
      return { ...task };
    },
    handleRealtimeUpdate(data) {
      console.log(data);
      // Check if the new order should be added to the corresponding column
      const column = this.columns.find((col) => col.name === data.status_name);
      if (column) {
        // Add the new task to the correct column
        column.tasks.push({
          id: data.order_id,
          name: data.order_id,
          status_name: data.status_name,
        });
      }
    },
    get_sales_order() {
      frappe.call({
        method: "posawesome.posawesome.api.kitchen_order.get_sales_order3",
        callback: (r) => {
          if (!r.exc) {
            this.columns = r.message;
            console.log(r.message);
          }
        },
      });
    },
  },
  mounted: function () {
    // Fetch data when the component is mounted
    frappe.realtime.on("sales_order_created", (data) => {
      this.get_sales_order();
    });
    this.get_sales_order();
    frappe.realtime.on("order_received", this.handleRealtimeUpdate);
  },
  beforeDestroy() {
    // Cleanup the realtime listener
    frappe.realtime.off("order_received", this.handleRealtimeUpdate);
  },
};
</script>

<style scoped>
.kanban-board {
  display: flex;
  overflow: auto;
}

.columns {
  display: flex;
  gap: 20px;
}

.column {
  width: 180px;
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
  background-color: #fc7e08;
  /* Light orange */
  color: white;
}

.preparing-column {
  background-color: #5bc0de;
  /* Light blue */
  color: white;
}

.dining-column {
  background-color: #d9534f;
  /* Light red */
  color: white;
}

.packing-column {
  background-color: #f7b731;
  /* Light yellow */
  color: white;
}

.delivery-column {
  background-color: #0275d8;
  /* Light blue */
  color: white;
}

.completed-column {
  background-color: #5cb85c;
  color: white;
}

.kanban-board {
  display: flex;
  overflow-x: hidden;
  /* prevent horizontal scroll */
  flex-wrap: wrap;
  /* allow columns to wrap to next line if too wide */
  gap: 20px;
  justify-content: center;
  /* center columns horizontally */
  padding-left: 20px;
  /* optional padding for some space */
  padding-right: 20px;
  /* optional padding for some space */
}

.columns {
  display: flex;
  flex-wrap: wrap;
  /* allow wrapping */
  gap: 12px;
  /* max-width: 1200px;  */
  margin-left: auto;
  margin-right: auto;
  width: 100%;
  box-sizing: border-box;
}

.column {
  flex: 1 1 180px;
  /* allow columns to shrink and grow but minimum 180px */
  max-width: 100%;
  box-sizing: border-box;
}

.v-card__text b,
.v-card__text ul li {
  font-size: 11px;
}
</style>
