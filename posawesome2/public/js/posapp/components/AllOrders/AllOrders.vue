<template>
  <v-container fluid class="container1">
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

    <!-- Orders Table -->
    <v-card>
      <!-- Toolbar with Search + Date Filter -->
      <!-- TOOLBAR -->
      <v-toolbar flat dense class="k-toolbar">
        <!-- left side (optional title) -->
        <div class="k-title d-none d-sm-flex">{{ __("Orders") }}</div>
        <v-spacer></v-spacer>

        <!-- Search -->
        <v-text-field v-model="search" label="Search" prepend-icon="mdi-magnify" dense outlined clearable hide-details
          class="k-search" @input="get_sales_order" />

        <!-- Toggle Filters with counter -->
        <v-badge :content="activeFilterCount" :value="activeFilterCount > 0" overlap color="primary" class="ml-2">
          <v-btn small outlined color="primary" class="k-filter-btn" @click="showFilters = !showFilters">
            <v-icon left>mdi-filter-variant</v-icon>
            {{ showFilters ? __("Hide Filters") : __("Show Filters") }}
          </v-btn>
        </v-badge>
      </v-toolbar>
      <v-divider class="mb-2"></v-divider>

      <!-- FILTER PANEL -->
      <v-slide-y-transition>
        <v-sheet v-if="showFilters" class="filters-sheet">
          <v-row dense>
            <v-col cols="12" sm="6" md="3">
              <v-text-field v-model="filters.custom_number_order" :label="__('Order No.')" dense outlined clearable
                hide-details="auto" />
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-text-field v-model="filters.custom_unique_talbat_number" :label="__('Talabat No.')" dense outlined
                clearable hide-details="auto" />
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-text-field v-model="filters.customer_name" :label="__('Customer')" dense outlined clearable
                hide-details="auto" />
            </v-col>

            <v-col cols="12" sm="6" md="3">
              <v-select v-model="filters.custom_so_type" :items="orderTypeOptions" :label="__('Order Type')" dense
                outlined clearable hide-details="auto" />
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-select v-model="filters.custom_table_no" :items="orderTypeOptions" :label="__('Table No')" dense
                outlined clearable hide-details="auto" />
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-autocomplete v-model="filters.status" :items="statusOptions" :label="__('Status')" dense outlined
                clearable multiple chips small-chips hide-details="auto" />
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-autocomplete v-model="filters.branch" :items="branchOptions" :label="__('Branch')" dense outlined
                clearable multiple chips small-chips hide-details="auto" />
            </v-col>

            <v-col cols="12" sm="6" md="3">
              <v-autocomplete v-model="filters.driver" :items="driverOptions" :label="__('Driver')" dense outlined
                clearable hide-details="auto" />
            </v-col>

            <v-col cols="12" sm="6" md="3">
              <v-text-field v-model="filters.cell_number" :label="__('Driver Phone')" dense outlined clearable
                hide-details="auto" />
            </v-col>

            <v-col cols="12" class="text-right">
              <v-btn small text class="mr-2" @click="resetFilters">
                <v-icon left small>mdi-backspace</v-icon>{{ __("Clear Filters") }}
              </v-btn>
              <v-btn small color="primary" class="ml-1" @click="showFilters = false">
                <v-icon left small>mdi-chevron-up</v-icon>{{ __("Collapse") }}
              </v-btn>
            </v-col>
          </v-row>
        </v-sheet>
      </v-slide-y-transition>

      <v-data-table :headers="headers" :items="filteredTasks" item-key="name" show-expand :expanded.sync="expanded"
        :search="search" :items-per-page="50" class="frappe-table" dense
        :footer-props="{ 'items-per-page-options': [10, 20, 50, 100] }">
        <template v-slot:item.status_name="{ item }">
          <v-chip :color="getStatusColor(item.status_name)" dark small>
            {{ item.status_name }}
          </v-chip>
        </template>

        <!-- Actions column -->
        <template v-slot:item.actions="{ item }">
          <v-icon small color="black" class="mr-2 large-icon" @click.stop="handleClickSalesOrder(item.name)">
            mdi-eye
          </v-icon>

          <v-icon small color="black" class="mr-2 large-icon" @click.stop="printOrder(item.name)">
            mdi-printer
          </v-icon>

          <v-icon v-if="item.outstanding_amount > 0" small color="green" class="mr-2 large-icon"
            @click.stop="PayOrder(item.name)">
            mdi-cash
          </v-icon>
          <!-- <v-icon
            small
            color="black"
            class="mr-2 large-icon"
            @click.stop="editOrder(item.name)"
          >
            mdi-pencil
          </v-icon> -->

          <v-icon small class="large-icon" color="red" @click.stop="deleteOrder(item.name)">
            mdi-delete
          </v-icon>
        </template>

        <!-- Assign Driver column -->
        <!-- inside Assign Driver column -->
        <template v-slot:item.addToKitchen="{ item }">
          <!-- <v-icon
            v-if="item.status_name.toLowerCase() === 'pending'"
            small
            :color="item.custom_so_type === 'Delivery' ? 'teal' : 'green'"
            class="mr-2 large-icon"
            :title="
              item.custom_so_type === 'Delivery'
                ? 'Assign Driver'
                : 'Mark as Completed'
            "
            @click.stop="
              item.custom_so_type === 'Delivery'
                ? openDriverDialog(item.name, item.custom_so_type, item.branch)
                : completeOrder(item.name)
            "
          >
            {{ item.custom_so_type === "Delivery" ? "mdi-truck" : "mdi-check" }}
          </v-icon> -->

          <v-icon small color="black" class="mr-2 large-icon" @click.stop="printOrder_In_Kitchen(item.name)">
            mdi-printer
          </v-icon>
        </template>
      </v-data-table>
    </v-card>

    <!-- Order Items Dialog -->
    <v-dialog v-model="itemDetails" max-width="800px">
      <v-card>
        <v-card-text>
          <v-progress-linear v-if="item_loading" indeterminate color="primary" class="mb-4"></v-progress-linear>

          <v-data-table :headers="selected_items_header" :items="selected_items" dense hide-default-footer>
            <template v-slot:item.item_code="{ item }">
              <v-icon small class="mr-1">mdi-file-document-outline</v-icon>
              {{ item.item_code }}
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-- Payment Confirm Dialog -->
    <v-dialog v-model="dailog_payment" max-width="400">
      <v-card>
        <v-card-title class="headline">{{ __("Payment Outstanding") }}
          {{ outstanding_amount }}</v-card-title>
        <v-card-text>
          <v-row v-if="payment_methods.length" v-for="method in payment_methods" :key="method.row_id">
            <v-col md="7"><span class="mt-1">{{ __(method.mode_of_payment) }}:</span>
            </v-col>
            <v-col md="5"><v-text-field class="p-0 m-0" dense color="primary" background-color="white" hide-details
                :value="formtCurrency(method.amount)" @change="onAmountChange(method, $event)" payments_methods flat
                :prefix="currencySymbol(pos_profile.currency)"></v-text-field></v-col>
            <v-col cols="12" v-if="show_paymentrecieptNumber && activeRowId === method.row_id">
              <v-text-field v-model="recieptNumber" :label="__('Enter Bank Payment Code')"
                :rules="[(v) => !!v || __('Bank Payment Code is required')]" dense outlined hide-details
                color="primary" />
            </v-col>
          </v-row>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text color="grey" @click="cancelDelete">{{
            __("Cancel")
            }}</v-btn>
          <v-btn color="red" text @click="SubmitPayOrder">{{
            __("Confirm")
            }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Password Confirm Dialog -->
    <v-dialog v-model="passwordDialog" max-width="400">
      <v-card>
        <v-card-title class="headline">{{
          __("Authorization Required")
          }}</v-card-title>
        <v-card-text>
          <p>{{ __("Please enter password or scan manager barcode to cancel this order.") }}</p>
          <v-text-field v-model="passwordInput" :error-messages="passwordError" :label="__('Password / Barcode')"
            type="password" autocomplete="off" dense outlined ref="passwordInput" prepend-inner-icon="mdi-barcode-scan"
            @keydown.enter="confirmDelete"></v-text-field>
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

    <!-- Wastage Question Dialog -->
    <v-dialog v-model="wastageQuestionDialog" max-width="400">
      <v-card>
        <v-card-title class="headline">{{ __("Order Cancellation") }}</v-card-title>
        <v-card-text>
          <p>{{ __("Is this order a wastage?") }}</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text color="grey" @click="cancelWastageQuestion">{{ __("Cancel") }}</v-btn>
          <v-btn color="primary" text @click="handleNotWastage">{{ __("No") }}</v-btn>
          <v-btn color="warning" text @click="handleWastage">{{ __("Yes, Wastage") }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Wastage Items Selection Dialog -->
    <v-dialog v-model="wastageItemsDialog" max-width="700">
      <v-card>
        <v-card-title class="headline">{{ __("Select Items for Stock Return") }}</v-card-title>
        <v-card-text>
          <!-- Stock Entry Type Selection -->
          <v-row class="mb-3">
            <v-col cols="12">
              <v-radio-group v-model="wastageStockEntryType" row mandatory>
                <v-radio :label="__('Consumptions')" value="Consumptions" color="orange"></v-radio>
                <v-radio :label="__('Loaded')" value="Loaded" color="blue"></v-radio>
              </v-radio-group>
            </v-col>
          </v-row>

          <v-row v-if="wastageStockEntryType === 'Loaded'" class="mb-3">
            <v-col cols="12">
              <v-autocomplete v-model="selectedEmployee" :items="employees" item-text="employee_name" item-value="name"
                :label="__('Select Employee')" dense outlined clearable :search-input.sync="employeeSearch"
                @update:search-input="searchEmployees">
                <template v-slot:item="{ item }">
                  <v-list-item-content>
                    <v-list-item-title>{{ item.employee_name }}</v-list-item-title>
                    <v-list-item-subtitle>{{ item.name }}</v-list-item-subtitle>
                  </v-list-item-content>
                </template>
              </v-autocomplete>
            </v-col>
          </v-row>

          <p class="mb-3">{{ __("Select items to return to stock. Unselected items will be marked as wastage.") }}</p>
          <v-data-table v-model="selectedReturnItems" :headers="wastageItemsHeaders" :items="wastageItems"
            item-key="item_code" show-select dense hide-default-footer class="elevation-1">
            <template v-slot:item.qty="{ item }">
              <v-text-field v-model.number="item.return_qty" type="number" :max="item.qty" :min="0" dense hide-details
                style="max-width: 80px"></v-text-field>
            </template>
          </v-data-table>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text color="grey" @click="cancelWastageItems">{{ __("Cancel") }}</v-btn>
          <v-btn color="primary" @click="confirmWastageItems">{{ __("Confirm") }}</v-btn>
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
          <v-autocomplete v-model="selectedDriver" :items="drivers" item-title="name" item-value="id"
            :label="__('Select Driver')" outlined dense></v-autocomplete>
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
import { evntBus } from "../../bus";
import format from "../../format";
export default {
  mixins: [format],
  data() {
    const today =
      (frappe?.datetime?.get_today && frappe.datetime.get_today()) ||
      new Date().toISOString().slice(0, 10);

    return {
      search: "",
      dailog_payment: false,
      isSubmitting: false,
      payment_methods: [],
      pos_opening_shift: {},
      selected_invoice_to_pay: null,
      outstanding_amount: 0,
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
        { text: __("Branch"), value: "branch", align: "start" },
        {
          text: __("Transaction Date"),
          value: "transaction_date",
          align: "start",
        },
        { text: __("Order Type"), value: "custom_so_type", align: "start" },
        { text: __("Table Number"), value: "custom_table_no", align: "start" },
        { text: __("Driver"), value: "driver_name", align: "start" },
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

      // old single-date filter kept (optional)
      filterDate: null,
      menu: false,

      // NEW: filter panel
      showFilters: true,
      filters: {
        custom_number_order: "",
        customer_name: "",
        branch: [],
        custom_so_type: null,
        custom_table_no: null,
        status: [],
        driver: null,
        cell_number: "",
        total_min: null,
        total_max: null,
        date_from: today, // YYYY-MM-DD
        date_to: today, // YYYY-MM-DD
      },
      menuFrom: false,
      menuTo: false,

      // options derived from current data
      branchOptions: [],
      statusOptions: [],
      orderTypeOptions: [],
      driverOptions: [],

      // Driver dialog state
      open_driver: false,
      selectedDriver: null,
      drivers: [],
      so: null,
      custom_so_type: null,
      custom_table_no: null,

      // Wastage dialog state
      wastageQuestionDialog: false,
      wastageItemsDialog: false,
      wastageOrderName: null,
      wastageItems: [],
      selectedReturnItems: [],
      wastageStockEntryType: "Consumptions",
      wastageItemsHeaders: [
        { text: __("Item Code"), value: "item_code", align: "start" },
        { text: __("Item Name"), value: "item_name", align: "start" },
        { text: __("Original Qty"), value: "original_qty", align: "center" },
        { text: __("Return Qty"), value: "qty", align: "center" },
      ],
      selectedEmployee: null,
      employees: [],
      employeeSearch: null,
    };
  },

  computed: {
    activeFilterCount() {
      const f = this.filters || {};
      const isFilled = (v) =>
        Array.isArray(v)
          ? v.length > 0
          : v !== null && v !== undefined && String(v).trim() !== "";
      return [
        f.custom_number_order,
        f.custom_unique_talbat_number,
        f.customer_name,
        f.custom_so_type,
        f.custom_table_no,
        f.status,
        f.driver,
        f.cell_number,
        f.date_from,
        f.date_to,
        f.total_min,
        f.total_max,
        f.branch,
      ].filter(isFilled).length;
    },

    filteredTasks() {
      let data = this.flatTasks.slice();
      // Optional legacy single-date filter (still supported)
      if (this.filterDate) {
        data = data.filter((t) =>
          (t.transaction_date || "").startsWith(this.filterDate),
        );
      }

      // PER-COLUMN FILTERS
      const f = this.filters;

      // text contains filters (case-insensitive)
      const ci = (a) => (a ?? "").toString().toLowerCase();
      const has = (val, needle) => ci(val).includes(ci(needle));

      if (f.custom_number_order) {
        data = data.filter((t) =>
          has(t.custom_number_order, f.custom_number_order),
        );
      }
      if (f.custom_unique_talbat_number) {
        data = data.filter((t) =>
          has(t.custom_unique_talbat_number, f.custom_unique_talbat_number),
        );
      }
      if (f.customer_name) {
        const this_data = data;

        data = this_data.filter((t) => has(t.customer_name, f.customer_name));
        if (this.isValidPhoneNumber(f.customer_name))
          data = this_data.filter((t) =>
            has(t.contact_mobile, f.customer_name),
          );
      }
      // Branch (supports multiple). If empty → no filtering (show all)
      if (Array.isArray(f.branch) ? f.branch.length > 0 : !!f.branch) {
        if (Array.isArray(f.branch)) {
          const allowed = new Set(f.branch.map(ci));
          data = data.filter((t) => allowed.has(ci(t.branch)));
        } else {
          data = data.filter((t) => ci(t.branch) === ci(f.branch));
        }
      }

      if (f.custom_so_type) {
        data = data.filter(
          (t) => ci(t.custom_so_type) === ci(f.custom_so_type),
        );
      }
      if (f.custom_table_no) {
        data = data.filter(
          (t) => ci(t.custom_table_no) === ci(f.custom_table_no),
        );
      }
      if (f.status && f.status.length) {
        const set = new Set(f.status.map((s) => ci(s)));
        data = data.filter((t) => set.has(ci(t.status_name)));
      }
      if (f.driver) {
        data = data.filter((t) => ci(t.driver) === ci(f.driver));
      }
      if (f.cell_number) {
        data = data.filter((t) => has(t.cell_number, f.cell_number));
      }
      if (f.total_min != null && f.total_min !== "") {
        const min = Number(f.total_min);
        data = data.filter((t) => Number(t.grand_total || 0) >= min);
      }
      if (f.total_max != null && f.total_max !== "") {
        const max = Number(f.total_max);
        data = data.filter((t) => Number(t.grand_total || 0) <= max);
      }

      // DATE RANGE (inclusive)
      if (f.date_from || f.date_to) {
        const from = f.date_from ? new Date(f.date_from + "T00:00:00") : null;
        const to = f.date_to ? new Date(f.date_to + "T23:59:59") : null;
        data = data.filter((t) => {
          if (!t.transaction_date) return false;
          const d = new Date(t.transaction_date + "T00:00:00");
          if (from && d < from) return false;
          if (to && d > to) return false;
          return true;
        });
      }

      return data;
    },
  },

  watch: {
    // rebuild option lists whenever data changes
    flatTasks: {
      immediate: true,
      handler(list) {
        const uniq = (arr) =>
          Array.from(
            new Set(
              arr.filter((x) => x != null && x !== "").map((x) => x.toString()),
            ),
          ).sort();

        this.branchOptions = uniq(list.map((t) => t.branch));
        this.statusOptions = uniq(list.map((t) => t.status_name));
        this.orderTypeOptions = uniq(list.map((t) => t.custom_so_type));
        this.driverOptions = uniq(list.map((t) => t.driver));
      },
    },
    passwordDialog(val) {
      if (val) {
        setTimeout(() => {
          this.$refs.passwordInput && this.$refs.passwordInput.focus();
        }, 300);
      }
    },
  },

  methods: {
    async onAmountChange(method, event) {
      this.setFormatedCurrency(method, "amount", null, true, event);
      this.show_paymentrecieptNumber = false;
      this.activeRowId = null;

      if (!method.mode_of_payment) return;

      // try {
      //   const res = await frappe.db.get_value(
      //     "Mode of Payment",
      //     method.mode_of_payment,
      //     "custom_required_receipt"
      //   );

      //   const type = res?.message?.custom_required_receipt;

      //   if (type) {
      //     this.show_paymentrecieptNumber = true;
      //     this.activeRowId = method.row_id;
      //   }
      // } catch (error) {
      //   console.error("Failed to fetch mode of payment type:", error);
      // }
    },
    resetFilters() {
      this.filters = {
        custom_number_order: "",
        customer_name: "",
        branch: [],
        custom_so_type: null,
        custom_table_no: null,
        status: [],
        driver: null,
        cell_number: "",
        total_min: null,
        total_max: null,
        date_from: null,
        date_to: null,
      };
      this.filterDate = null; // legacy single-date
    },

    back_to_invoice() {
      window.location.href = frappe.urllib.get_base_url() + "/app/posapp";
    },
    isValidPhoneNumber(phoneNumber) {
      // This regex matches various common US phone number formats:
      // - 10 digits (e.g., 1234567890)
      // - 3-3-4 format with hyphens (e.g., 123-456-7890)
      // - (3) 3-4 format with parentheses and hyphen (e.g., (123) 456-7890)
      isNumber = !Number.isNaN(Number(phoneNumber));
      return isNumber;
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
      frappe.db
        .get_list("Driver", {
          fields: ["name", "full_name", "cell_number"],
          filters: { custom_branch: branch },
          limit: 1000,
        })
        .then((data) => (vm.drivers = data.map((e) => e.name)));
    },
    completeOrder(so) {
      frappe.call({
        method: "posawesome.posawesome.api.kitchen_order.update_sales_order",
        args: { name: so, status: "Completed", driver: null },
        callback: (r) => {
          if (!r.exc) {
            this.get_sales_order();
            frappe.show_alert(__("Order marked as Completed"));
          }
        },
      });
    },
    submit_driver(so, custom_so_type) {
      if (!this.selectedDriver)
        return frappe.show_alert(__("Please select a driver"));
      const vm = this;
      frappe.call({
        method:
          "posawesome.posawesome.api.kitchen_order.update_sales_order_driver",
        args: { name: so, status: "Delivery", driver: vm.selectedDriver },
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
      this.wastageOrderName = sales_order;
      this.passwordInput = "";
      this.passwordError = "";
      this.passwordDialog = true;
    },
    confirmDelete() {
      const correctPassword = this.pos_profile?.custom_discaunt_password;
      if (this.passwordInput === correctPassword) {
        this.passwordDialog = false;
        // Show wastage question dialog instead of directly cancelling
        this.wastageQuestionDialog = true;
      } else {
        this.passwordError = __("Password is incorrect. Please try again.");
      }
    },
    cancelDelete() {
      this.passwordDialog = false;
      this.passwordInput = "";
      this.passwordError = "";
      this.deleteSalesOrderToConfirm = null;
      this.wastageOrderName = null;
    },
    // ===== WASTAGE FUNCTIONS =====
    cancelWastageQuestion() {
      this.wastageQuestionDialog = false;
      this.wastageOrderName = null;
      this.deleteSalesOrderToConfirm = null;
    },
    handleNotWastage() {
      // Not wastage - just cancel the order normally
      this.wastageQuestionDialog = false;
      this.proceedWithCancellation(false, []);
    },
    handleWastage() {
      // Is wastage - show items selection dialog
      this.wastageQuestionDialog = false;
      this.loadOrderItemsForWastage();
    },
    loadOrderItemsForWastage() {
      const vm = this;
      frappe.call({
        method: "posawesome.posawesome.api.kitchen_order.get_stock_items_for_wastage",
        args: { sales_order: this.wastageOrderName },
        callback: (r) => {
          if (!r.exc) {
            const items = r.message || [];
            vm.wastageItems = items.map((i) => ({
              item_code: i.item_code || "",
              item_name: i.item_name || i.item_code || "",
              qty: i.qty || 0,
              original_qty: i.original_qty || i.qty || 0,
              return_qty: i.qty || 0,
              uom: i.uom || "Nos",
              warehouse: i.warehouse || "",
              source: i.source || "",
            }));
            vm.selectedReturnItems = [];
            vm.wastageItemsDialog = true;
          }
        },
      });
    },
    cancelWastageItems() {
      this.wastageItemsDialog = false;
      this.wastageItems = [];
      this.selectedReturnItems = [];
      this.wastageOrderName = null;
      this.deleteSalesOrderToConfirm = null;
    },
    confirmWastageItems() {
      // Items selected = return to stock (automatically when invoice cancelled)
      // Items NOT selected = wastage (need Material Issue)

      // Get selected item codes
      const selectedCodes = new Set(this.selectedReturnItems.map(i => i.item_code));

      // Wastage items = items NOT selected for return
      const wastageItems = this.wastageItems
        .filter(item => !selectedCodes.has(item.item_code))
        .map(item => ({
          item_code: item.item_code,
          qty: item.qty,
          uom: item.uom,
          warehouse: item.warehouse,
        }));

      // Also add partial wastage (original qty - return qty) for selected items
      this.selectedReturnItems.forEach(item => {
        const wastageQty = item.original_qty - (item.return_qty || 0);
        if (wastageQty > 0) {
          wastageItems.push({
            item_code: item.item_code,
            qty: wastageQty,
            uom: item.uom,
            warehouse: item.warehouse,
          });
        }
      });

      // Items to return (for reference only - they return automatically when invoice cancelled)
      const itemsToReturn = this.selectedReturnItems.map((item) => ({
        item_code: item.item_code,
        qty: item.return_qty || item.qty,
        uom: item.uom,
      })).filter(item => item.qty > 0);

      this.wastageItemsDialog = false;
      this.proceedWithCancellation(true, itemsToReturn, wastageItems, this.wastageStockEntryType, this.selectedEmployee);
    },
    proceedWithCancellation(isWastage, itemsToReturn = [], wastageItems = [], stockEntryType = "Consumptions", employee = null) {
      const vm = this;
      frappe.call({
        method: "posawesome.posawesome.api.kitchen_order.cancel_sales_order_with_wastage",
        args: {
          sales_order: this.deleteSalesOrderToConfirm,
          is_wastage: isWastage,
          items_to_return: JSON.stringify(itemsToReturn),
          wastage_items: JSON.stringify(wastageItems),
          stock_entry_type: stockEntryType,
          employee: employee,
        },
        callback: (r) => {
          if (!r.exc) {
            let msg = __("Sales Order and linked invoices cancelled successfully.");
            if (isWastage && wastageItems.length > 0) {
              msg += " " + __("Stock entry created for wastage items.");
            }
            frappe.msgprint(msg);
            vm.get_sales_order();
          } else {
            frappe.msgprint(__("Error cancelling order."));
          }
          vm.wastageItems = [];
          vm.selectedReturnItems = [];
          vm.wastageOrderName = null;
          vm.deleteSalesOrderToConfirm = null;
          vm.wastageStockEntryType = "Consumptions";
          vm.selectedEmployee = null;
        },
      });
    },
    searchEmployees(searchTerm) {
      if (!searchTerm || searchTerm.length < 2) {
        this.employees = [];
        return;
      }
      frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "Employee",
          filters: [
            ["employee_name", "like", `%${searchTerm}%`]
          ],
          fields: ["name", "employee_name"],
          limit: 20,
        },
        callback: (r) => {
          if (!r.exc && r.message) {
            this.employees = r.message;
          }
        },
      });
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
      const args = {
        shift: "Whole Day",
      };
      // Add date range if set
      if (this.filters.date_from) {
        args.date_from = this.filters.date_from;
      }
      if (this.filters.date_to) {
        args.date_to = this.filters.date_to;
      }
      frappe.call({
        method:
          "posawesome.posawesome.api.kitchen_order.get_all_sales_order_in_all_branchs",
        args: args,
        callback: (r) => {
          if (!r.exc) this.flatTasks = r.message || [];
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
    PayOrder(sales_order) {
      const vm = this;
      frappe.call({
        method:
          "posawesome.posawesome.api.kitchen_order.get_sales_invoice_from_order",
        args: { sales_order },
        callback: (r) => {
          vm.dailog_payment = true;
          vm.selected_invoice_to_pay = r.message?.[0]?.parent;
          vm.outstanding_amount = r.message?.[0]?.outstanding_amount;

          // if (invoice_name) {
          //   // window.open(
          //   //   `/printview?doctype=Sales Invoice&name=${invoice_name}&trigger_print=1&format=NEW%20Receipt&no_letterhead=0`,
          //   //   "_blank"
          //   // );
          // } else {
          //   frappe.msgprint("No linked Sales Invoice found for this order.");
          // }
        },
      });
    },
    SubmitPayOrder() {
      if (this.isSubmitting) return;
      this.isSubmitting = true;
      const vm = this;
      const payload = {};
      // payload.customer = customer;
      let totals = 0;
      vm.payment_methods.forEach((method) => (totals += method.amount || 0));
      if (totals > vm.outstanding_amount) {
        this.isSubmitting = false;
        return frappe.msgprint(
          `Total payment amount (${this.formtCurrency(
            totals,
          )}) is less than the outstanding amount (${this.formtCurrency(
            vm.outstanding_amount,
          )}).`,
        );
      }
      payload.company = this.company;
      payload.currency = this.pos_profile.currency;
      payload.pos_opening_shift_name = this.pos_opening_shift.name;
      payload.pos_profile_name = this.pos_profile.name;
      payload.pos_profile = this.pos_profile;
      payload.payment_methods = this.payment_methods;
      payload.selected_invoices = this.selected_invoices;
      payload.selected_invoice = this.selected_invoice_to_pay;
      payload.selected_payments = this.selected_payments;
      payload.total_selected_invoices = flt(this.total_selected_invoices);
      payload.selected_mpesa_payments = this.selected_mpesa_payments;
      payload.total_selected_payments = flt(this.total_selected_payments);
      payload.total_payment_methods = flt(this.total_payment_methods);
      payload.custom_receipt_number = vm.recieptNumber;
      frappe.call({
        method:
          "posawesome.posawesome.api.payment_entry.create_pos_payment_entry",
        args: { payload },
        callback: (r) => {
          vm.dailog_payment = false;
          //  vm.selected_invoice_to_pay =  r.message?.[0]?.parent;
          vm.outstanding_amount = 0;
          vm.selected_invoice_to_pay = null;
          vm.payment_methods.forEach((method) => (method.amount = 0));
          frappe.show_alert(__("Payment successful"));
          vm.isSubmitting = false;
        },
        error: () => {
          vm.isSubmitting = false;
        },
      });
    },
    editOrder(sales_order) {
      frappe.set_route("posapp", { sales_order });
    },
    set_payment_methods() {
      // get payment methods from pos profile
      if (!this.pos_profile.posa_allow_make_new_payments) return;
      this.payment_methods = [];
      this.pos_profile.payments.forEach((method) => {
        this.payment_methods.push({
          mode_of_payment: method.mode_of_payment,
          amount: 0,
          row_id: method.name,
        });
      });
    },
    check_opening_entry() {
      return frappe
        .call("posawesome.posawesome.api.posapp.check_opening_shift", {
          user: frappe.session.user,
        })
        .then((r) => {
          if (r.message) {
            this.pos_profile = r.message.pos_profile;
            this.set_payment_methods();
            this.pos_opening_shift = r.message.pos_opening_shift;
            if (r.message.must_close) {
              evntBus.$emit("show_mesage", {
                text: __(
                  "Shift ended. Please close the shift; selling is blocked until then.",
                ),
                color: "warning",
              });
            }
          }
        });
    },
    load_user_date_range() {
      return frappe
        .call(
          "posawesome.posawesome.doctype.all_orders_settings.all_orders_settings.get_user_date_range",
        )
        .then((r) => {
          if (r.message) {
            // User has specific date range set
            this.filters.date_from = r.message.date_from || null;
            this.filters.date_to = r.message.date_to || null;
          } else {
            // No date range set - use null (API will use whole day)
            this.filters.date_from = null;
            this.filters.date_to = null;
          }
        });
    },
  },

  mounted() {
    frappe.realtime.on("sales_order_created", () => this.get_sales_order());
    frappe.realtime.on("sales_order_updated", () => this.get_sales_order());
    this.load_user_date_range().then(() => this.get_sales_order());
    this.check_opening_entry();
  },
};
</script>

<style scoped>
.large-icon {
  font-size: 26px !important;
  /* Customize the font size */
}

.k-toolbar {
  background: #fff;
  border-radius: 10px;
  padding-inline: 10px;
  box-shadow: 0 2px 14px rgba(0, 0, 0, 0.06);
}

.k-title {
  font-weight: 600;
  font-size: 14px;
  opacity: 0.85;
}

.k-search {
  max-width: 280px;
}

.k-filter-btn {
  border-radius: 999px !important;
  /* pill */
}

/* Filter sheet look */
.filters-sheet {
  background: #fff;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  padding: 12px 14px 8px;
  margin: 6px 8px 10px;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.04);
}

/* Compact chips inside autocomplete */
.v-chip.v-size--small {
  font-size: 11px;
}

/* Better spacing between fields on very small screens */
@media (max-width: 600px) {
  .k-search {
    max-width: 100%;
  }

  .filters-sheet {
    margin: 6px 0 10px;
    border-radius: 10px;
  }
}
</style>
