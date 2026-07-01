<template>
  <div>
    <v-autocomplete
      dense
      clearable
      auto-select-first
      solo
      color="#E71D36"
      :label="__('Customer')"
      v-model="customer"
      :items="customers"
      item-text="customer_name"
      item-value="name"
      background-color="white"
      :no-data-text="__('Customer not found')"
      hide-details
      :filter="() => true"
      :disabled="readonly"
      :loading="customerLoading"
      :search-input.sync="searchTerm"
      append-icon="mdi-plus"
      @update:search-input="onSearchInput"
      @click:append="new_customer"
      prepend-inner-icon="mdi-account-edit"
      @click:prepend-inner="edit_customer"
    >
      <template v-slot:item="data">
        <template>
          <v-list-item-content class="list-hover">
            <v-list-item-title
              class="main_color subtitle-1"
              v-html="data.item.customer_name"
            ></v-list-item-title>
            <v-list-item-subtitle
              v-if="data.item.customer_name != data.item.name"
              v-html="`${__('ID')}: ${data.item.name}`"
            ></v-list-item-subtitle>
            <v-list-item-subtitle
              v-if="data.item.tax_id"
              v-html="`${__('TAX ID')}: ${data.item.tax_id}`"
            ></v-list-item-subtitle>
            <v-list-item-subtitle
              v-if="data.item.email_id"
              v-html="`${__('Email')}: ${data.item.email_id}`"
            ></v-list-item-subtitle>
            <v-list-item-subtitle
              v-if="data.item.mobile_no"
              v-html="`${__('Mobile No')}: ${data.item.mobile_no}`"
            ></v-list-item-subtitle>
            <v-list-item-subtitle
              v-if="data.item.primary_address"
              v-html="`${__('Primary Address')}: ${data.item.primary_address}`"
            ></v-list-item-subtitle>
          </v-list-item-content>
        </template>
      </template>
    </v-autocomplete>

    <div class="mt-8 mb-4" v-if="ready && !isPaymentScreen">
      <v-autocomplete
        dense
        clearable
        auto-select-first
        solo
        color="#E71D36"
        :label="__('Driver')"
        v-model="driver"
        :items="drivers"
        item-text="full_name"
        item-value="name"
        background-color="white"
        :no-data-text="__('Driver not found')"
        hide-details
        :disabled="readonly"
        prepend-inner-icon="mdi-account"
        @change="onDriverChange"
      >
        <template v-slot:item="data">
          <template>
            <v-list-item-content class="list-hover">
              <v-list-item-title
                class="main_color subtitle-1"
                v-html="data.item.full_name"
              ></v-list-item-title>
            </v-list-item-content>
          </template>
        </template>
      </v-autocomplete>
    </div>

    <div class="mb-8">
      <UpdateCustomer></UpdateCustomer>
    </div>
  </div>
</template>

<script>
import _ from "lodash";
import { evntBus } from "../../bus";
import UpdateCustomer from "./UpdateCustomer.vue";
export default {
  data: () => ({
    pos_profile: "",
    customers: [],
    customer: "",
    readonly: false,
    customer_info: {},
    drivers: [], // <-- Add this
    driver: "",
    isPaymentScreen: false,
    ready: false,
    searchTerm: "",
    customerLoading: false,
    lastQuery: null,
    debouncedFetchCustomers: null,
    customerCacheLoaded: false,
  }),

  components: {
    UpdateCustomer,
  },

  methods: {
    onDriverChange() {
      evntBus.$emit("update_driver", this.driver);
    },

    get_driver_names() {
      const vm = this;
      frappe.call({
        method: "posawesome.posawesome.api.posapp.get_driver_names",
        args: {
          pos_profile: this.pos_profile.pos_profile,
        },
        callback: function (r) {
          if (r.message) {
            vm.drivers = r.message;
          }
        },
      });
    },

    fetchCustomers(term = "") {
      const query = (term || "").trim();
      const profilePayload =
        (this.pos_profile && this.pos_profile.pos_profile) || this.pos_profile;
      // Avoid duplicate fetches for the same query
      if (query === this.lastQuery && this.customers.length) {
        return;
      }
      this.lastQuery = query;

      if (
        !query &&
        this.pos_profile?.posa_local_storage &&
        !this.customerCacheLoaded
      ) {
        const cached = localStorage.getItem("customer_storage");
        if (cached) {
          try {
            this.customers = JSON.parse(cached);
            this.customerCacheLoaded = true;
            return;
          } catch (e) {
            // ignore parse errors and fetch from server
          }
        }
      }

      this.customerLoading = true;
      const args = {
        pos_profile: profilePayload,
        search: query,
        limit: query ? 50 : 20,
      };

      frappe.call({
        method: "posawesome.posawesome.api.posapp.get_customer_names",
        args,
        callback: (r) => {
          this.customerLoading = false;
          if (r.message) {
            this.customers = r.message;
            if (!query && this.pos_profile?.posa_local_storage) {
              localStorage.setItem(
                "customer_storage",
                JSON.stringify(r.message),
              );
              this.customerCacheLoaded = true;
            }
          } else {
            this.customers = [];
          }
        },
        error: () => {
          this.customerLoading = false;
        },
      });
    },

    get_customer_names() {
      this.fetchCustomers("");
    },

    new_customer() {
      this.customer_info.mobile_no = this.searchTerm;
      evntBus.$emit("open_update_customer", this.customer_info, true);
    },
    edit_customer() {
      evntBus.$emit("open_update_customer", this.customer_info);
    },
    onSearchInput(val) {
      this.searchTerm = val;
      if (this.debouncedFetchCustomers) {
        this.debouncedFetchCustomers(val);
      }
    },
  },

  computed: {},
  mounted() {
    this.fetchCustomers("");
  },
  created: function () {
    this.debouncedFetchCustomers = _.debounce(
      (value) => this.fetchCustomers(value),
      250,
    );

    this.$nextTick(function () {
      evntBus.$on("fetch_customer_names", () => {
        this.fetchCustomers("");
      });
      evntBus.$on("register_pos_profile", (pos_profile) => {
        this.pos_profile = pos_profile;
        this.customerCacheLoaded = false;
        this.lastQuery = null;
        this.fetchCustomers("");
        this.isPaymentScreen = true;
        this.ready = true; // now we can render safely

        this.get_driver_names();
      });
      evntBus.$on("payments_register_pos_profile", (pos_profile) => {
        this.pos_profile = pos_profile;
        this.customerCacheLoaded = false;
        this.lastQuery = null;
        this.fetchCustomers("");
        this.get_driver_names();
        this.isPaymentScreen = false;
        this.ready = true; // now we can render safely
      });
      evntBus.$on("set_customer", (customer) => {
        this.customer = customer;
      });
      evntBus.$on("add_customer_to_list", (customer) => {
        this.customers.push(customer);
      });
      evntBus.$on("set_customer_readonly", (value) => {
        this.readonly = value;
      });
      evntBus.$on("set_customer_info_to_edit", (data) => {
        this.customer_info = data;
      });
      evntBus.$on("fetch_customer_details", (pos_profile) => {
        this.pos_profile = pos_profile;
        this.customerCacheLoaded = false;
        this.lastQuery = null;
        this.fetchCustomers("");
        this.isPaymentScreen = true;
        this.ready = true; // now we can render safely

        this.get_driver_names();
      });
    });
  },

  watch: {
    customer() {
      evntBus.$emit("update_customer", this.customer);
    },
    driver() {
      evntBus.$emit("update_driver", this.driver);
    },
  },
};
</script>

<style scoped>
.main_color {
  color: #e71d36 !important;
}

.v-list {
  padding: 0 !important;
  background: white !important;
}

::v-deep .v-list-item {
  padding: 0 !important;
}

::v-deep .primary--text {
  color: #e71d36 !important;
  caret-color: #e71d36 !important;
}

.list-hover {
  padding: 12px !important;
  transition: all 0.3s linear;
}

.list-hover:hover {
  background-color: #e71d36 !important;
  color: white !important;
  cursor: pointer !important;
}

.list-hover:hover * {
  color: white !important;
}
</style>
