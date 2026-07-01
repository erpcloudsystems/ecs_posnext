<template>
  <v-container fluid class="container1">
    <!-- Back Button -->
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
            @click="back_to_invoice"
          >
            {{ __("Back") }}
          </v-btn>
        </v-col>
      </v-row>
    </v-card>

    <!-- Orders Table with expandable rows -->
    <v-card>
      <!-- <v-toolbar flat>
        <v-text-field
          v-model="search"
          append-icon="mdi-magnify"
          label="Search Orders"
          single-line
          hide-details
          class="flex-grow-1"
        ></v-text-field>

        <v-btn
          icon
          color="primary"
          @click="get_sales_order"
          :title="'Refresh Orders'"
        >
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
      </v-toolbar> -->

      <!-- Toolbar with Search + Date Filter -->
      <v-toolbar flat dense>
        <v-spacer></v-spacer>

        <!-- Search -->
        <v-text-field
          v-model="search"
          :label="__('Search')"
          prepend-icon="mdi-magnify"
          dense
          hide-details
          style="max-width: 250px"
          @input="get_sales_order"
        ></v-text-field>

        <!-- Date Filter -->
        <v-menu
          v-model="menu"
          :close-on-content-click="false"
          transition="scale-transition"
          offset-y
          max-width="290"
          min-width="290"
        >
          <template v-slot:activator="{ on, attrs }">
            <v-text-field
              style="max-width: 250px; margin-left: 16px"
              v-model="filterDate"
              :label="__('Filter by Date')"
              prepend-icon="mdi-calendar"
              readonly
              dense
              hide-details
              v-bind="attrs"
              v-on="on"
            ></v-text-field>
          </template>
          <v-date-picker
            v-model="filterDate"
            @input="menu = false"
          ></v-date-picker>
        </v-menu>
      </v-toolbar>

      <v-data-table
        :headers="headers"
        :items="filteredTasks"
        item-key="name"
        show-expand
        :expanded.sync="expanded"
        :search="search"
        :items-per-page="50"
        class="frappe-table"
        dense
        :footer-props="{ 'items-per-page-options': [10, 20, 50, 100] }"
      >
        <template v-slot:item.status_name="{ item }">
          <v-chip :color="getStatusColor(item.status_name)" dark small>
            {{ item.status_name }}
          </v-chip>
        </template>

        <!-- Actions column -->
        <template v-slot:item.actions="{ item }">
          <v-icon
            small
            color="black"
            class="mr-2 large-icon"
            @click.stop="handleClickSalesOrder(item.name)"
          >
            mdi-eye
          </v-icon>

          <v-icon
            small
            color="black"
            class="mr-2 large-icon"
            @click.stop="printOrder(item.name)"
          >
            mdi-printer
          </v-icon>

          <v-icon
            small
            color="black"
            class="mr-2 large-icon"
            @click.stop="editOrder(item.name)"
          >
            mdi-pencil
          </v-icon>

          <v-icon
            small
            class="large-icon"
            color="red"
            @click.stop="deleteOrder(item.name)"
          >
            mdi-delete
          </v-icon>
        </template>

        <template v-slot:item.addToKitchen="{ item }">
          <v-icon
            v-if="item.status_name.toLowerCase() === 'pending'"
            small
            color="red"
            class="mr-2 large-icon"
            title="Add to Kitchen"
            @click.stop="addToKitchen(item.name)"
          >
            mdi-plus-circle
          </v-icon>

          <v-icon
            small
            color="black"
            class="mr-2 large-icon"
            @click.stop="printOrder_In_Kitchen(item.name)"
          >
            mdi-printer
          </v-icon>
        </template>
      </v-data-table>
    </v-card>

    <!-- Dialog to show selected order items -->
    <v-dialog v-model="itemDetails" max-width="800px">
      <v-card>
        <v-card-text>
          <v-progress-linear
            v-if="item_loading"
            indeterminate
            color="primary"
            class="mb-4"
          ></v-progress-linear>

          <v-data-table
            :headers="selected_items_header"
            :items="selected_items"
            dense
            hide-default-footer
          >
            <template v-slot:item.item_code="{ item }">
              <v-icon small class="mr-1">mdi-file-document-outline</v-icon>
              {{ item.item_code }}
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="passwordDialog" max-width="400">
      <v-card>
        <v-card-title class="headline">{{
          __("Confirm Password")
        }}</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="passwordInput"
            :error-messages="passwordError"
            :label="__('Enter Your Password')"
            type="password"
            autocomplete="off"
            dense
            outlined
          ></v-text-field>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text color="grey" @click="cancelDelete">{{
            __("Cancel")
          }}</v-btn>
          <v-btn color="red" text @click="confirmDelete">{{
            __("Confirm")
          }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { evntBus } from "../../bus";

export default {
  data() {
    return {
      search: "",
      expanded: [],
      selected_items_header: [
        {
          text: __("Item"),
          align: "start",
          sortable: true,
          value: "item_code",
        },
        { text: __("QTY"), align: "start", sortable: true, value: "qty" },
      ],
      flatTasks: [], // orders with nested items
      headers: [
        { text: __("Order"), value: "custom_number_order", align: "start" },
        { text: __("Customer"), value: "customer_name", align: "start" },
        { text: __("Branch"), value: "branch", align: "start" },
        {
          text: __("Transaction Date"),
          value: "transaction_date",
          align: "start",
        },
        { text: __("Order Type"), value: "custom_so_type", align: "start" },
        { text: __("Status"), value: "status_name", align: "start" },
        { text: __("Total"), value: "grand_total", align: "start" },
        {
          text: __("Actions"),
          value: "actions",
          sortable: false,
          align: "start",
        },
        {
          text: __("Add To Kitchen"),
          value: "addToKitchen",
          sortable: false,
          align: "start",
        },
      ],
      itemDetails: false,
      selected_items: [],
      item_loading: false,
      passwordDialog: false,
      passwordInput: "",
      deleteSalesOrderToConfirm: null, // store sales_order to delete after password confirmed
      passwordError: "", // optional error message,
      pos_profile: null, // store pos profile data
      filterDate: null,
      menu: false, // for date filter menu
    };
  },
  computed: {
    filteredTasks() {
      if (!this.filterDate) return this.flatTasks;
      return this.flatTasks.filter((task) => {
        return task.transaction_date === this.filterDate;
      });
    },
  },
  methods: {
    back_to_invoice() {
      window.location.href = frappe.urllib.get_base_url() + "/app/posapp";
    },
    deleteOrder(sales_order) {
      this.deleteSalesOrderToConfirm = sales_order;
      this.passwordInput = "";
      this.passwordError = "";
      this.passwordDialog = true;
    },

    handleInvoiceSubmit(status) {
      console.log("Invoice submitted event received:", status);
      this.get_sales_order();
    },
    // Confirm password and delete if correct
    confirmDelete() {
      const correctPassword = this.pos_profile?.custom_discaunt_password;
      if (this.passwordInput === correctPassword) {
        this.passwordDialog = false;

        frappe.call({
          method:
            "posawesome.posawesome.api.kitchen_order.cancel_sales_order_and_invoices",
          args: { sales_order: this.deleteSalesOrderToConfirm },
          callback: (r) => {
            if (!r.exc) {
              frappe.msgprint(
                __("Sales Order and linked invoices cancelled successfully."),
              );
              this.get_sales_order();
            } else {
              frappe.msgprint(__("Error cancelling order."));
            }
          },
        });
      } else {
        this.passwordError = __("Password is incorrect. Please try again.");
      }
    },

    cancelDelete() {
      this.passwordDialog = false;
      this.passwordInput = "";
      this.passwordError = "";
      this.deleteSalesOrderToConfirm = null;
    },

    getStatusColor(status) {
      switch (status) {
        case "Preparing":
          return "blue";
        case "Dining":
          return "red";
        case "Packing":
          return "orange";
        case "Delivery":
          return "purple";
        case "Completed":
          return "green";
        default:
          return "grey";
      }
    },

    get_sales_order() {
      frappe.call({
        method: "posawesome.posawesome.api.kitchen_order.get_sales_order2",
        callback: (r) => {
          if (!r.exc) {
            // Assuming your backend returns an array of orders with nested items array
            this.flatTasks = r.message || [];
          }
        },
      });
    },

    handleClickSalesOrder(sales_order) {
      this.itemDetails = true;
      this.item_loading = true;
      frappe.call({
        method: "posawesome.posawesome.api.kitchen_order.get_items_sales_order",
        args: { name: sales_order },
        callback: (r) => {
          if (!r.exc) {
            const [spi, items] = r.message || [[], []];
            let allItems = [...items];
            this.selected_items = allItems.map((i) => ({
              item_code: i.item_code || i.item_name || "",
              qty: i.qty || 0,
            }));
            this.item_loading = false;
          }
        },
      });
    },
    addToKitchen(sales_order) {
      frappe.call({
        method:
          "posawesome.posawesome.api.kitchen_order.update_status_to_preparing",
        args: { sales_order },
        callback: (r) => {
          if (!r.exc) {
            this.printOrder_In_Kitchen(sales_order);
            this.get_sales_order();
          } else {
            frappe.msgprint(__("Failed to update status."));
          }
        },
      });
    },
    printOrder_In_Kitchen(sales_order) {
      frappe.call({
        method:
          "posawesome.posawesome.api.kitchen_order.get_sales_invoice_from_order",
        args: { sales_order },
        callback: (r) => {
          if (r.message && r.message.length > 0) {
            let invoice_name = r.message[0].parent;
            window.open(
              `/printview?doctype=Sales Invoice&name=${invoice_name}&trigger_print=1&format=Kitchen%20Receipt&no_letterhead=0`,
              "_blank",
            );
          } else {
            frappe.msgprint(
              __("No linked Sales Invoice found for this order."),
            );
          }
        },
      });
    },

    printOrder(sales_order) {
      frappe.call({
        method:
          "posawesome.posawesome.api.kitchen_order.get_sales_invoice_from_order",
        args: { sales_order },
        callback: (r) => {
          if (r.message && r.message.length > 0) {
            let invoice_name = r.message[0].parent;
            window.open(
              `/printview?doctype=Sales Invoice&name=${invoice_name}&trigger_print=1&format=NEW%20Receipt&no_letterhead=0`,
              "_blank",
            );
          } else {
            frappe.msgprint(
              __("No linked Sales Invoice found for this order."),
            );
          }
        },
      });
    },

    editOrder(sales_order) {
      frappe.set_route("posapp", { sales_order });
    },
    check_opening_entry() {
      return frappe
        .call("posawesome.posawesome.api.posapp.check_opening_shift", {
          user: frappe.session.user,
        })
        .then((r) => {
          if (r.message) {
            this.pos_profile = r.message.pos_profile;
          }
        });
    },
  },
  mounted() {
    frappe.realtime.on("sales_order_created", (data) => {
      this.get_sales_order();
    });
    this.get_sales_order();

    this.check_opening_entry().then(() => {});
  },
};
</script>

<style scoped>
.frappe-table {
  font-size: 14px;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}

.frappe-table thead th {
  background-color: #f5f5f5;
  color: #444;
  font-weight: 600;
  border-bottom: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}

.frappe-table tbody td {
  padding: 10px 12px;
  vertical-align: middle;
  border-bottom: 1px solid #eee;
  color: #333;
}

.v-chip {
  font-weight: 600;
  text-transform: capitalize;
}

.v-icon {
  cursor: pointer;
  transition: color 0.3s ease;
}

.v-icon:hover {
  color: #1976d2;
}
.large-icon {
  font-size: 48px; /* Customize the font size */
}
</style>
