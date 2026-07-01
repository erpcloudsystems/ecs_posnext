<template>
  <v-container fluid class="orders-shell">
    <div class="orders-header">
      <div class="orders-header__left">
        <v-btn
          class="orders-back"
          color="warning"
          dark
          @click="back_to_invoice"
        >
          <v-icon left small>mdi-arrow-left</v-icon>
          {{ __("Back") }}
        </v-btn>
        <div class="orders-quick-actions">
          <v-btn icon class="orders-action orders-action--primary">
            <v-icon small>mdi-plus</v-icon>
          </v-btn>
          <v-btn icon class="orders-action orders-action--accent">
            <v-icon small>mdi-filter-variant</v-icon>
          </v-btn>
          <v-btn icon class="orders-action orders-action--primary">
            <v-icon small>mdi-download</v-icon>
          </v-btn>
        </div>
      </div>
      <div class="orders-header__right">
        <div class="orders-filters">
          <v-text-field
            v-model="search"
            :label="__('Search')"
            prepend-icon="mdi-magnify"
            dense
            hide-details
            style="max-width: 260px"
            @input="get_sales_order"
          ></v-text-field>
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
                style="max-width: 240px"
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
        </div>
      </div>
    </div>

    <div class="orders-status-row">
      <v-chip-group
        v-model="statusFilter"
        row
        active-class="orders-status-chip--active"
        class="orders-status-group"
      >
        <v-chip
          v-for="chip in statusSummary"
          :key="chip.value"
          class="orders-status-chip"
          :value="chip.value"
          outlined
        >
          <span class="orders-status-chip__label">{{ chip.label }}</span>
          <span class="orders-status-chip__count">{{ chip.count }}</span>
        </v-chip>
      </v-chip-group>
    </div>

    <v-card class="orders-table">
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
          <v-btn
            icon
            class="orders-action orders-action--primary mr-2"
            @click.stop="handleClickSalesOrder(item.name)"
          >
            <v-icon small>mdi-eye</v-icon>
          </v-btn>

          <v-menu offset-y>
            <template v-slot:activator="{ on, attrs }">
              <v-btn
                icon
                class="orders-action orders-action--accent mr-2"
                v-bind="attrs"
                v-on="on"
              >
                <v-icon small>mdi-pencil</v-icon>
              </v-btn>
            </template>
            <v-list dense>
              <v-list-item @click.stop="openOrderInline(item.name)">
                <v-list-item-title>{{ __("Edit Inline") }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click.stop="editInPOS(item.name)">
                <v-list-item-title>{{ __("Reopen In POS") }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click.stop="openSalesOrderForm(item.name)">
                <v-list-item-title>{{
                  __("Open Sales Order Form")
                }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>

          <v-btn
            icon
            class="orders-action orders-action--primary mr-2"
            @click.stop="printOrder(item.name)"
          >
            <v-icon small>mdi-printer</v-icon>
          </v-btn>

          <v-btn
            icon
            class="orders-action orders-action--danger"
            @click.stop="deleteOrder(item.name)"
          >
            <v-icon small>mdi-delete</v-icon>
          </v-btn>
        </template>

        <!-- Assign Driver column -->
        <!-- inside Assign Driver column -->
        <template v-slot:item.addToKitchen="{ item }">
          <v-btn
            v-if="item.status_name.toLowerCase() === 'pending'"
            icon
            class="orders-action mr-2"
            :class="
              item.custom_so_type === 'Delivery'
                ? 'orders-action--teal'
                : 'orders-action--success'
            "
            :title="
              item.custom_so_type === 'Delivery'
                ? __('Assign Driver')
                : __('Mark as Completed')
            "
            @click.stop="
              item.custom_so_type === 'Delivery'
                ? openDriverDialog(item.name, item.custom_so_type, item.branch)
                : completeOrder(item.name)
            "
          >
            <v-icon small>
              {{
                item.custom_so_type === "Delivery" ? "mdi-truck" : "mdi-check"
              }}
            </v-icon>
          </v-btn>

          <v-btn
            icon
            class="orders-action orders-action--primary"
            @click.stop="printOrder_In_Kitchen(item.name)"
          >
            <v-icon small>mdi-printer</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Order Items Dialog -->
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

    <!-- Password Confirm Dialog -->
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

    <!-- Driver Assignment Dialog -->
    <v-dialog max-width="600px" v-model="open_driver">
      <v-card>
        <v-card-title class="text-h5">
          <span class="headline main_color">{{ __("Select Driver") }}</span>
        </v-card-title>

        <v-container>
          <v-autocomplete
            v-model="selectedDriver"
            :items="drivers"
            item-title="name"
            item-value="id"
            :label="__('Select Driver')"
            outlined
            dense
          ></v-autocomplete>
        </v-container>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" text @click="resetDriverDialog">{{
            __("Cancel")
          }}</v-btn>
          <v-btn color="success" @click="submit_driver(so, custom_so_type)">
            {{ __("Done") }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
export default {
  data() {
    return {
      search: "",
      statusFilter: "all",
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
      flatTasks: [],
      headers: [
        { text: __("Order"), value: "custom_number_order", align: "start" },
        { text: __("Customer"), value: "customer_name", align: "start" },
        { text: __("Mobile No"), value: "contact_mobile", align: "start" },
        { text: __("Branch"), value: "branch", align: "start" },
        {
          text: __("Transaction Date"),
          value: "transaction_date",
          align: "start",
        },
        { text: __("Order Type"), value: "custom_so_type", align: "start" },
        {
          text: __("Talabat Number"),
          value: "custom_unique_talbat_number",
          align: "start",
        },
        { text: __("Driver"), value: "driver_name", align: "start" },
        // { text: __('Driver'), value: "driver", align: "start" },
        { text: __("Driver Phone"), value: "cell_number", align: "start" },
        { text: __("Status"), value: "status_name", align: "start" },
        { text: __("Total"), value: "grand_total", align: "start" },
        {
          text: __("Actions"),
          value: "actions",
          sortable: false,
          align: "start",
        },
        {
          text: __("Assign Driver"),
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
      deleteSalesOrderToConfirm: null,
      passwordError: "",
      pos_profile: null,
      filterDate: null,
      menu: false,

      // Driver dialog state
      open_driver: false,
      selectedDriver: null,
      drivers: [],
      so: null,
      custom_so_type: null,
    };
  },
  computed: {
    statusSummary() {
      const summary = {};
      this.flatTasks.forEach((task) => {
        const key = (task.status_name || "unknown").toLowerCase();
        summary[key] = (summary[key] || 0) + 1;
      });

      const ordered = [
        "all",
        "pending",
        "preparing",
        "dining",
        "packing",
        "delivery",
        "completed",
        "cancelled",
      ];

      return ordered
        .map((value) => {
          const label =
            value === "all"
              ? __("All")
              : __(value.charAt(0).toUpperCase() + value.slice(1));
          const count =
            value === "all" ? this.flatTasks.length : summary[value] || 0;
          return { value, label, count };
        })
        .filter((chip) => chip.value === "all" || chip.count > 0);
    },
    filteredTasks() {
      let tasks = this.flatTasks.slice();

      if (this.statusFilter && this.statusFilter !== "all") {
        const key = this.statusFilter.toLowerCase();
        tasks = tasks.filter(
          (task) => (task.status_name || "").toLowerCase() === key,
        );
      }

      if (this.filterDate) {
        tasks = tasks.filter((task) =>
          task.transaction_date?.startsWith(this.filterDate),
        );
      }

      return tasks;
    },
  },
  methods: {
    getStatusColor(status) {
      const key = (status || "").toLowerCase();
      const map = {
        pending: "orange lighten-1",
        preparing: "blue lighten-1",
        dining: "deep-purple lighten-1",
        packing: "amber darken-2",
        delivery: "teal",
        completed: "green",
        cancelled: "red lighten-1",
      };
      return map[key] || "grey";
    },
    openOrderInline(sales_order) {
      this.handleClickSalesOrder(sales_order);
    },
    editInPOS(sales_order) {
      const base = frappe.urllib.get_base_url();
      const sanitizedBase =
        base && base.endsWith("/") ? base.slice(0, -1) : base;
      const target = `${sanitizedBase}/app/posapp?sales_order=${encodeURIComponent(sales_order)}`;
      window.location.href = target;
    },
    openSalesOrderForm(sales_order) {
      frappe.set_route("Form", "Sales Order", sales_order);
    },
    back_to_invoice() {
      window.location.href = frappe.urllib.get_base_url() + "/app/posapp";
    },
    // ===== DRIVER FUNCTIONS =====
    openDriverDialog(so, custom_so_type, branch) {
      if (custom_so_type === "Delivery") {
        this.so = so;
        this.custom_so_type = custom_so_type;
        this.open_driver = true;
        this.get_driver(branch);
      } else {
        this.completeOrder(so);
      }
    },
    get_driver(branch) {
      const vm = this;
      frappe.call({
        method: "posawesome.posawesome.api.kitchen_order.get_drivers_by_branch",
        args: { branch: branch },
        async: true,
        callback: (r) => {
          if (r.message) {
            vm.drivers = r.message.map((e) => e.name);
          }
        },
      });
    },
    // ✅ Handle "Completed" case without driver
    completeOrder(so) {
      frappe.call({
        method: "posawesome.posawesome.api.kitchen_order.update_sales_order",
        args: {
          name: so,
          status: "Completed",
          driver: null,
        },
        callback: (r) => {
          if (!r.exc) {
            this.get_sales_order();
            frappe.show_alert(__("Order marked as Completed"));
          }
        },
      });
    },

    // existing driver submit function stays the same
    submit_driver(so, custom_so_type) {
      if (!this.selectedDriver) {
        return frappe.show_alert(__("Please select a driver"));
      }
      const vm = this;
      frappe.call({
        method:
          "posawesome.posawesome.api.kitchen_order.update_sales_order_driver",
        args: {
          name: so,
          status: "Delivery",
          driver: vm.selectedDriver,
        },
        callback: (r) => {
          if (!r.exc) {
            this.get_sales_order();
            frappe.show_alert(__("Driver assigned successfully"));
          }
          this.resetDriverDialog();
        },
      });
    },
    resetDriverDialog() {
      this.open_driver = false;
      this.selectedDriver = null;
      this.so = null;
      this.custom_so_type = null;
    },

    // ===== EXISTING FUNCTIONS =====
    deleteOrder(sales_order) {
      this.deleteSalesOrderToConfirm = sales_order;
      this.passwordInput = "";
      this.passwordError = "";
      this.passwordDialog = true;
    },
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
                "Sales Order and linked invoices cancelled successfully.",
              );
              this.get_sales_order();
            } else {
              frappe.msgprint("Error cancelling order.");
            }
          },
        });
      } else {
        this.passwordError = "Password is incorrect. Please try again.";
      }
    },
    cancelDelete() {
      this.passwordDialog = false;
      this.passwordInput = "";
      this.passwordError = "";
      this.deleteSalesOrderToConfirm = null;
    },
    get_sales_order() {
      frappe.call({
        method: "posawesome.posawesome.api.kitchen_order.get_sales_order2",
        callback: (r) => {
          if (!r.exc) {
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
            this.selected_items = items.map((i) => ({
              item_code: i.item_code || i.item_name || "",
              qty: i.qty || 0,
            }));
            this.item_loading = false;
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
          let invoice_name = r.message?.[0]?.parent;
          if (invoice_name) {
            window.open(
              `/printview?doctype=Sales Invoice&name=${invoice_name}&trigger_print=1&format=Kitchen%20Receipt&no_letterhead=0`,
              "_blank",
            );
          } else {
            frappe.msgprint("No linked Sales Invoice found for this order.");
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
          let invoice_name = r.message?.[0]?.parent;
          if (invoice_name) {
            window.open(
              `/printview?doctype=Sales Invoice&name=${invoice_name}&trigger_print=1&format=NEW%20Receipt&no_letterhead=0`,
              "_blank",
            );
          } else {
            frappe.msgprint("No linked Sales Invoice found for this order.");
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
    frappe.realtime.on("sales_order_created", () => {
      this.get_sales_order();
    });
    frappe.realtime.on("sales_order_updated", (data) => {
      this.get_sales_order(); // re-fetch orders automatically
    });
    this.get_sales_order();
    this.check_opening_entry();
  },
};
</script>
<style scoped>
.orders-shell {
  background: linear-gradient(135deg, #ffffff 0%, #f5f7fb 100%);
  border-radius: 26px;
  min-height: calc(100vh - 140px);
  box-shadow: 0 28px 52px rgba(23, 34, 59, 0.14);
  padding: 24px 28px;
}

.orders-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.orders-header__left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.orders-header__right {
  display: flex;
  align-items: center;
}

.orders-back {
  border-radius: 16px !important;
  text-transform: none !important;
  font-weight: 600;
  letter-spacing: 0.02em;
  box-shadow: 0 20px 38px rgba(238, 116, 60, 0.24);
  padding: 10px 22px !important;
}

.orders-quick-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.orders-filters {
  display: flex;
  align-items: center;
  gap: 12px;
}

.orders-filters ::v-deep .v-input__slot {
  border-radius: 14px !important;
  background: #ffffff !important;
  border: 1px solid rgba(23, 34, 59, 0.08) !important;
  padding-left: 12px !important;
}

.orders-status-row {
  margin: 20px 0 18px;
}

.orders-status-group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.orders-status-chip {
  border-radius: 14px !important;
  padding: 6px 14px !important;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.orders-status-chip__count {
  background: rgba(23, 34, 59, 0.08);
  border-radius: 10px;
  padding: 2px 8px;
  font-size: 0.75rem;
  margin-left: 8px;
}

.orders-status-chip--active {
  background: #2cc8c2 !important;
  border-color: transparent !important;
  color: #ffffff !important;
}

.orders-table {
  border-radius: 20px !important;
  overflow: hidden;
  box-shadow: 0 25px 44px rgba(23, 34, 59, 0.12);
}

.orders-table ::v-deep table {
  border-spacing: 0 8px !important;
}

.orders-table ::v-deep tbody tr {
  background: #ffffff !important;
  box-shadow: 0 12px 24px rgba(23, 34, 59, 0.08);
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}

.orders-table ::v-deep tbody tr:hover {
  transform: translateY(-2px);
  box-shadow: 0 24px 38px rgba(23, 34, 59, 0.16);
}

.status-chip {
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.orders-action {
  border-radius: 12px !important;
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(23, 34, 59, 0.06);
  color: #17223b !important;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}

.orders-action:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(23, 34, 59, 0.18);
}

.orders-action--primary {
  background: rgba(44, 200, 194, 0.15) !important;
  color: #0f6f6b !important;
}

.orders-action--accent {
  background: rgba(94, 96, 206, 0.18) !important;
  color: #1f277f !important;
}

.orders-action--danger {
  background: rgba(239, 71, 111, 0.2) !important;
  color: #ef476f !important;
}

.orders-action--success {
  background: rgba(59, 178, 115, 0.2) !important;
  color: #1f8a4d !important;
}

.orders-action--teal {
  background: rgba(44, 200, 194, 0.22) !important;
  color: #0f6f6b !important;
}

.orders-shell ::-webkit-scrollbar {
  width: 6px;
}

.orders-shell ::-webkit-scrollbar-thumb {
  background: rgba(23, 34, 59, 0.12);
  border-radius: 3px;
}

.orders-shell .v-data-footer {
  border-top: none !important;
}
</style>
