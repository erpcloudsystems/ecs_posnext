<template>
  <div>
    <v-autocomplete
      dense
      clearable
      auto-select-first
      solo
      color="#E71D36"
      :label="__('Driver')"
      v-model="customer"
      :items="customers"
      item-text="full_name"
      item-value="name"
      background-color="white"
      :no-data-text="__('Driver not found')"
      hide-details
      :filter="customFilter"
      :disabled="readonly"
    >
      <template v-slot:item="data">
        <template>
          <v-list-item-content class="list-hover">
            <v-list-item-title
              class="main_color subtitle-1"
              v-html="data.item.full_name"
            ></v-list-item-title>
            <v-list-item-subtitle
              v-if="data.item.full_name != data.item.name"
              v-html="`${__('ID')}: ${data.item.name}`"
            ></v-list-item-subtitle>
          </v-list-item-content>
        </template>
      </template>
    </v-autocomplete>
  </div>
</template>

<script>
import { evntBus } from "../../bus";
export default {
  data: () => ({
    pos_profile: "",
    customers: [],
    customer: "",
    readonly: false,
    customer_info: {},
    search: "",
  }),

  components: {},

  methods: {
    get_drivers_names() {
      const vm = this;
      if (this.customers.length > 0) {
        return;
      }
      if (vm.pos_profile.posa_local_storage && localStorage.customer_storage) {
        vm.customers = JSON.parse(localStorage.getItem("divers_storage"));
      }
      frappe.call({
        method: "posawesome.posawesome.api.posapp.get_drivers_names",
        args: {
          pos_profile: this.pos_profile.pos_profile,
        },
        callback: function (r) {
          if (r.message) {
            vm.customers = r.message;
            console.log(r.message);
            console.info("loadCustomers");
            if (vm.pos_profile.posa_local_storage) {
              localStorage.setItem("divers_storage", "");
              localStorage.setItem("divers_storage", JSON.stringify(r.message));
            }
          }
        },
      });
    },
    new_customer() {
      this.customer_info.mobile_no = this.search;
      console.log("this.customer_info", this.customer_info);
      evntBus.$emit("open_update_customer", this.customer_info, true);
    },
    edit_customer() {
      evntBus.$emit("open_update_customer", this.customer_info);
    },
    customFilter(item, queryText, itemText) {
      this.search = queryText;
      const textOne = item.full_name ? item.full_name.toLowerCase() : "";
      const textFifth = item.name.toLowerCase();
      const searchText = queryText.toLowerCase();

      return (
        textOne.indexOf(searchText) > -1 ||
        textTwo.indexOf(searchText) > -1 ||
        textThree.indexOf(searchText) > -1 ||
        textFour.indexOf(searchText) > -1 ||
        textFifth.indexOf(searchText) > -1
      );
    },
  },

  computed: {},

  created: function () {
    this.$nextTick(function () {
      evntBus.$on("register_pos_profile", (pos_profile) => {
        this.pos_profile = pos_profile;
        this.get_drivers_names();
      });
      evntBus.$on("payments_register_pos_profile", (pos_profile) => {
        this.pos_profile = pos_profile;
        this.get_drivers_names();
      });
      evntBus.$on("set_customer", (customer) => {
        this.customer = customer;
        console.log(this.customer);
      });
      evntBus.$on("add_customer_to_list", (customer) => {
        this.customers.push(customer);
      });
      evntBus.$on("set_customer_readonly", (value) => {
        this.readonly = value;
      });
      evntBus.$on("set_driver_info_to_edit", (data) => {
        this.customer_info = data;
      });
      evntBus.$on("fetch_customer_details", () => {
        this.get_drivers_names();
      });
    });
  },

  watch: {
    customer() {
      console.log(this.customer);
      evntBus.$emit("update_driver", this.customer);
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
