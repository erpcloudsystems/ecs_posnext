<template>
  <v-container fluid class="container1">
    <!-- Header -->
    <v-card
      flat
      class="cards mb-2 mt-2 py-0"
      style="max-height: 11vh; height: 11vh"
    >
      <v-row align="center" no-gutters>
        <v-col cols="2">
          <v-btn block class="pa-1" large color="warning" dark @click="goBack">
            {{ __("Back") }}
          </v-btn>
        </v-col>
        <v-col cols="6" class="text-center">
          <h2>{{ __("Driver Dispatcher") }}</h2>
        </v-col>
        <v-col cols="2">
          <v-select
            v-model="selectedBranch"
            :items="branches"
            :label="__('Branch')"
            dense
            outlined
            hide-details
            @change="loadData"
          />
        </v-col>
        <v-col cols="2" class="text-right">
          <v-btn color="primary" @click="loadData" :loading="loading">
            <v-icon left>mdi-refresh</v-icon>
            {{ __("Refresh") }}
          </v-btn>
        </v-col>
      </v-row>
    </v-card>

    <v-row>
      <!-- Drivers Panel -->
      <v-col cols="4">
        <v-card class="pa-2" height="80vh" style="overflow-y: auto">
          <v-card-title class="py-2">
            <v-icon left>mdi-account-group</v-icon>
            {{ __("Drivers") }}
          </v-card-title>
          <v-divider></v-divider>

          <v-list dense>
            <v-list-item
              v-for="driver in drivers"
              :key="driver.name"
              :class="{
                'selected-driver':
                  selectedDriver && selectedDriver.name === driver.name,
              }"
              @click="selectDriver(driver)"
              :disabled="!driver.is_available"
            >
              <v-list-item-avatar>
                <v-icon :color="driver.is_available ? 'success' : 'error'">
                  mdi-account-circle
                </v-icon>
              </v-list-item-avatar>
              <v-list-item-content>
                <v-list-item-title>{{ driver.full_name }}</v-list-item-title>
                <v-list-item-subtitle>
                  {{ driver.cell_number }}
                </v-list-item-subtitle>
              </v-list-item-content>
              <v-list-item-action>
                <v-chip
                  :color="driver.is_available ? 'success' : 'error'"
                  small
                  dark
                >
                  {{ driver.active_orders }}/{{ driver.capacity }}
                </v-chip>
              </v-list-item-action>
            </v-list-item>
          </v-list>

          <v-alert v-if="!drivers.length" type="info" dense class="ma-2">
            {{ __("No drivers found for this branch") }}
          </v-alert>
        </v-card>
      </v-col>

      <!-- Orders Panel -->
      <v-col cols="8">
        <v-card class="pa-2" height="80vh" style="overflow-y: auto">
          <v-card-title class="py-2">
            <v-icon left>mdi-package-variant</v-icon>
            {{ __("Pending Delivery Orders") }}
            <v-spacer></v-spacer>
            <v-chip color="primary" small v-if="selectedDriver">
              {{ __("Selected") }}: {{ selectedDriver.full_name }}
            </v-chip>
          </v-card-title>
          <v-divider></v-divider>

          <v-data-table
            :headers="orderHeaders"
            :items="orders"
            :loading="loading"
            item-key="name"
            dense
            :items-per-page="20"
            class="elevation-0"
          >
            <template v-slot:item.status="{ item }">
              <v-chip
                :color="getStatusColor(item.custom_order_in_kitchen_)"
                small
                dark
              >
                {{ item.custom_order_in_kitchen_ }}
              </v-chip>
            </template>

            <template v-slot:item.driver_info="{ item }">
              <span v-if="item.driver">
                <v-icon small color="success">mdi-check</v-icon>
                {{ item.driver_name }}
              </span>
              <span v-else class="text--secondary">
                {{ __("Not Assigned") }}
              </span>
            </template>

            <template v-slot:item.grand_total="{ item }">
              {{ formtCurrency(item.grand_total) }}
            </template>

            <template v-slot:item.actions="{ item }">
              <v-btn
                v-if="!item.driver && selectedDriver"
                small
                color="primary"
                @click="assignDriver(item)"
                :loading="item.assigning"
                :disabled="!selectedDriver.is_available"
              >
                <v-icon small left>mdi-account-plus</v-icon>
                {{ __("Assign") }}
              </v-btn>
              <v-btn
                v-else-if="item.driver"
                small
                color="success"
                @click="confirmDelivery(item)"
                :loading="item.confirming"
              >
                <v-icon small left>mdi-check</v-icon>
                {{ __("Confirm") }}
              </v-btn>
            </template>
          </v-data-table>

          <v-alert
            v-if="!orders.length && !loading"
            type="info"
            dense
            class="ma-2"
          >
            {{ __("No pending delivery orders") }}
          </v-alert>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { evntBus } from "../../bus";
import format from "../../format";

export default {
  mixins: [format],
  data() {
    return {
      loading: false,
      selectedBranch: null,
      branches: [],
      drivers: [],
      orders: [],
      selectedDriver: null,
      orderHeaders: [
        { text: __("Order #"), value: "custom_number_order", align: "start" },
        { text: __("Customer"), value: "customer_name", align: "start" },
        { text: __("Phone"), value: "contact_mobile", align: "start" },
        { text: __("Total"), value: "grand_total", align: "end" },
        { text: __("Status"), value: "status", align: "center" },
        { text: __("Driver"), value: "driver_info", align: "start" },
        {
          text: __("Actions"),
          value: "actions",
          sortable: false,
          align: "center",
        },
      ],
    };
  },

  mounted() {
    this.loadBranches();
  },

  methods: {
    goBack() {
      window.history.back();
    },

    getStatusColor(status) {
      const colors = {
        Completed: "blue",
        Ready: "teal",
        Packing: "orange",
        Delivery: "purple",
        "Out for Delivery": "indigo",
        Delivered: "success",
      };
      return colors[status] || "grey";
    },

    async loadBranches() {
      try {
        const res = await frappe.call({
          method:
            "posawesome.posawesome.api.dispatcher.get_branches_for_dispatcher",
        });
        this.branches = res.message || [];
        if (this.branches.length) {
          this.selectedBranch = this.branches[0];
          this.loadData();
        }
      } catch (e) {
        console.error("Failed to load branches:", e);
      }
    },

    async loadData() {
      if (!this.selectedBranch) return;
      this.loading = true;
      this.selectedDriver = null;

      try {
        const [driversRes, ordersRes] = await Promise.all([
          frappe.call({
            method:
              "posawesome.posawesome.api.dispatcher.get_drivers_with_capacity",
            args: { branch: this.selectedBranch },
          }),
          frappe.call({
            method:
              "posawesome.posawesome.api.dispatcher.get_pending_delivery_orders",
            args: { branch: this.selectedBranch },
          }),
        ]);

        this.drivers = (driversRes.message || []).map((d) => ({
          ...d,
          assigning: false,
        }));
        this.orders = (ordersRes.message || []).map((o) => ({
          ...o,
          assigning: false,
          confirming: false,
        }));
      } catch (e) {
        console.error("Failed to load data:", e);
        frappe.msgprint(__("Failed to load dispatcher data"));
      }

      this.loading = false;
    },

    selectDriver(driver) {
      if (!driver.is_available) return;
      this.selectedDriver =
        this.selectedDriver?.name === driver.name ? null : driver;
    },

    async assignDriver(order) {
      if (!this.selectedDriver) {
        frappe.msgprint(__("Please select a driver first"));
        return;
      }

      order.assigning = true;
      try {
        await frappe.call({
          method: "posawesome.posawesome.api.dispatcher.assign_driver_to_order",
          args: {
            order_name: order.name,
            driver_name: this.selectedDriver.name,
          },
        });
        frappe.show_alert({
          message: __("Driver assigned successfully"),
          indicator: "green",
        });
        this.loadData();
      } catch (e) {
        frappe.msgprint(__("Failed to assign driver"));
      }
      order.assigning = false;
    },

    async confirmDelivery(order) {
      order.confirming = true;
      try {
        await frappe.call({
          method: "posawesome.posawesome.api.dispatcher.confirm_delivery",
          args: { order_name: order.name },
        });
        frappe.show_alert({
          message: __("Delivery confirmed"),
          indicator: "green",
        });
        this.loadData();
      } catch (e) {
        frappe.msgprint(__("Failed to confirm delivery"));
      }
      order.confirming = false;
    },
  },
};
</script>

<style scoped>
.container1 {
  padding: 10px;
}
.selected-driver {
  background-color: #e3f2fd !important;
  border-left: 4px solid #1976d2;
}
</style>
