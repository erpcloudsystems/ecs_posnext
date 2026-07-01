<template>
  <v-container fluid>
    <v-card flat class="cards mb-2 mt-2 py-0" style="max-height: 11vh; height: 11vh">
      <v-row align="start" no-gutters>
        <v-col cols="3">
          <v-btn block class="pa-1" large color="warning" dark @click="back_to_invoice">
            {{ __("Back") }}
          </v-btn>
        </v-col>
      </v-row>
    </v-card>
    <div class="row columns">
      <v-card-title>{{ __("Delivery") }}</v-card-title>
    </div>
    <v-autocomplete style="max-width: 200px" v-model="selectedDriver" :items="drivers" item-text="full_name"
      item-value="name" label="Search Driver" outlined dense @focus="handleFocus" :search-input.sync="search" />
    <v-dialog v-model="itemDetails" max-width="1200px" class="overflow-y-none grey lighten-5">
      <v-card class="cards my-0 p-0 grey lighten-5" v-if="itemDetails">
        <v-data-table :headers="selected_items_header" :items="selected_items" :loading="item_loading" item-key="name"
          class="elevation-1 mt-0">
        </v-data-table>
      </v-card>
    </v-dialog>
    <div class="kanban-board">
      <div class="row columns" style="margin: 0">
        <v-card v-for="task in filteredTasks" :key="task.id" outlined class="" style="
            border-top-width: 6px;
            border-top-style: solid;
            border-radius: 15px;
            box-shadow: 0 1px 1px rgba(0, 0, 0, 0.08),
              0 2px 2px rgba(0, 0, 0, 0.08), 0 4px 4px rgba(0, 0, 0, 0.08);
            transition: box-shadow 0.3s ease;
          " :style="task.custom_so_type == 'Delivery'
            ? 'border-top-color: #E53A40'
            : task.custom_so_type == 'Pickup' ||
              task.custom_so_type == 'Pick Up'
              ? 'border-top-color: #379392'
              : task.custom_so_type == 'Car Service'
                ? 'border-top-color: #6AAFE6'
                : 'border-top-color: #FFBC42'
            " min-width="250px">
          <!-- Timer component that accepts inputTime -->
          <v-card-title class="cursor-pointer p-3 pb-2 text-center d-block" style="color: gray"
            @click="handleClickSalesOrder(task.name)">
            #{{ task.custom_number_order || task.name }} {{ task.branch }}
          </v-card-title>
          <v-card-title class="px-3 py-0 text-center d-block">
            {{ task.customer_name }}
          </v-card-title>
          <v-card-title class="px-3 py-0 text-center d-block" v-if="task.custom_table_no">
            T {{ task.custom_table_no }}
          </v-card-title>
          <v-divider></v-divider>
          <div style="
              display: flex;
              justify-content: space-between;
              padding: 0 1rem;
              align-items: center;
            ">
            <span v-if="task.custom_so_type" style="padding: 2px 7px; border-radius: 4px; font-size: 12px" :style="task.custom_so_type == 'Delivery'
              ? 'color: #E53A40; background-color: #fde4e4;'
              : task.custom_so_type == 'Pickup' ||
                task.custom_so_type == 'Pick Up'
                ? 'color: #379392; background-color: #d6f1ec;'
                : task.custom_so_type == 'Car Service'
                  ? 'color: #6AAFE6; background-color: #e0f0fb;'
                  : ''
              ">
              {{ task.custom_so_type }}
            </span>

            <Timer :inputTime="task.time || 1800" :id="task.name" />
            <button style="
                color: rgb(22, 163, 74);
                font-weight: 500;
                font-size: 12px;
                background: rgb(22 163 74 / 10%);
                border-radius: 4px;
                padding: 2px 10px;
              " v-if="task.status_name == 'Delivery'" @click="
                onClickHandle(
                  task.name,
                  task.custom_so_type,
                  task.name,
                  task.branch
                )
                ">
              {{ __("Done") }}
            </button>
          </div>
          <!-- <div style="text-align: left;">{{ task.custom_so_type }}</div> -->
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
                {{ item.item }} <span style="color: rgb(22, 163, 74);">{{ item.item_qty }}</span>
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
import Timer from "../../Timer.vue";
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
      selectedDriver: null,
      drivers: [],
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
  computed: {
    filteredTasks() {
      let tasks = this.columns.tasks || [];

      // فلترة حسب الـ branch إذا كان متوفر
      // if (this.branch) {
      //   tasks = tasks.filter((task) => task.branch === this.branch);
      // }

      // فلترة حسب السائق إذا تم اختياره
      if (this.selectedDriver) {
        tasks = tasks.filter((task) => task.driver === this.selectedDriver);
      }

      return tasks;
    },
  },
  watch: {
    search(val) {
      this.filterDrivers(val); // أو get_driver(val) إذا كنت تجلب من API
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
    back_to_invoice() {
      window.location.href = frappe.urllib.get_base_url() + "/app/posapp";
    },

    handleFocus() {
      this.get_driver();
    },
    get_driver() {
      frappe.db
        .get_list("Driver", {
          fields: ["name", "full_name"],
          limit: 1000,
        })
        .then((data) => {
          this.drivers = data;
        });
    },
    filterDrivers(search) {
      console.log("Filtering with:", search);
      // ممكن فلترة محلية أو استعلام سيرفر
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
        default:
          return "";
      }
    },

    onClickHandle(so) {
      frappe.call({
        method: "posawesome.posawesome.api.kitchen_order.update_sales_order",
        args: {
          name: so,
          status: "Completed",
        },
        callback: (r) => {
          this.columns.tasks.forEach(function (item) {
            if (item.name === so) {
              item.status_name = "Completed";
            }
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
      // const column = this.columns.find(col => col.name === data.status_name);
      const existingTask = this.columns.tasks.find(
        (task) => task.id == data.order_id
      );

      if (!existingTask) {
        // Add the new task to the correct column
        this.columns.tasks.push({
          id: data.order_id,
          driver: data.driver,
          name: data.order_id,
          status_name: data.status_name,
          customer_name: data.customer_name,
          timer: data.status_name,
          custom_so_type: data.custom_so_type,
          branch: data.branch,
          items: data.items,
          posa_notes: data.posa_notes,
        });
      }
    },
    get_sales_order() {
      const args = {
        status: "Delivery",
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
          }
        },
      });
    },
  },
  mounted: function () {
    this.get_driver();

    this.$nextTick(() => {
      this.get_driver();
    });
    this.branch = this.getBranchFromCookie();
    // Fetch data when the component is mounted
    this.get_sales_order();
    frappe.realtime.on("order_delivery", this.handleRealtimeUpdate);
  },
  beforeDestroy() {
    // Cleanup the realtime listener
    frappe.realtime.off("order_delivery", this.handleRealtimeUpdate);
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

.ready-to-pick-up-column {
  background-color: #0275d8;
  /* Light blue */
  color: white;
}

.completed-column {
  background-color: #5cb85c;
  color: white;
}
</style>
