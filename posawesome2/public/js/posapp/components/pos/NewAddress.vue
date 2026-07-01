<template>
  <v-row justify="center">
    <v-dialog v-model="addressDialog" max-width="600px">
      <v-card>
        <v-card-title>
          <span class="headline primary--text">{{
            __("Add New Address")
          }}</span>
        </v-card-title>
        <v-card-text class="pa-0">
          <v-container>
            <v-row>
              <v-col cols="12">
                <v-text-field
                  dense
                  color="primary"
                  :label="__('Address Name')"
                  background-color="white"
                  hide-details
                  v-model="address.name"
                ></v-text-field>
              </v-col>
              <v-col cols="4">
                <v-text-field
                  dense
                  color="primary"
                  :label="__('Floor')"
                  background-color="white"
                  hide-details
                  v-model="address.custom_floor"
                ></v-text-field>
              </v-col>
              <v-col cols="4">
                <v-text-field
                  dense
                  color="primary"
                  :label="__('Apartment No')"
                  background-color="white"
                  hide-details
                  v-model="address.custom_apartment"
                ></v-text-field>
              </v-col>
              <v-col cols="4">
                <v-text-field
                  dense
                  color="primary"
                  :label="__('Mark')"
                  background-color="white"
                  hide-details
                  v-model="address.custom_mark"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  dense
                  color="primary"
                  :label="__('Address Line 1')"
                  background-color="white"
                  hide-details
                  v-model="address.address_line1"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  dense
                  color="primary"
                  :label="__('Address Line 2')"
                  background-color="white"
                  hide-details
                  v-model="address.address_line2"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-autocomplete
                  clearable
                  dense
                  auto-select-first
                  color="primary"
                  :label="__('Address Type') + ' *'"
                  v-model="address_type"
                  :items="address_types"
                  background-color="white"
                  :no-data-text="__('Address Type not found')"
                  hide-details
                  required
                >
                </v-autocomplete>
              </v-col>
              <v-col cols="6">
                <v-autocomplete
                  clearable
                  dense
                  auto-select-first
                  color="primary"
                  :label="__('City') + ' *'"
                  v-model="city"
                  :items="cities"
                  background-color="white"
                  :no-data-text="__('City not found')"
                  hide-details
                  required
                >
                </v-autocomplete>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  :label="__('State')"
                  dense
                  background-color="white"
                  hide-details
                  v-model="address.state"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-autocomplete
                  clearable
                  dense
                  auto-select-first
                  color="primary"
                  :label="__('Parent Territory') + ' *'"
                  v-model="parent_territory"
                  :items="parent_territorys"
                  background-color="white"
                  :no-data-text="__('Territory not found')"
                  hide-details
                  required
                  @change="getChildTerritorys"
                >
                </v-autocomplete>
              </v-col>
              <v-col cols="6">
                <v-autocomplete
                  clearable
                  dense
                  auto-select-first
                  color="primary"
                  :label="__('Territory') + ' *'"
                  v-model="territory"
                  :items="territorys"
                  background-color="white"
                  :no-data-text="__('Territory not found')"
                  hide-details
                  required
                  :disabled="!parent_territory"
                >
                </v-autocomplete>
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" dark @click="close_dialog">{{
            __("Close")
          }}</v-btn>
          <v-btn color="success" dark @click="submit_dialog">{{
            __("Submit")
          }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-row>
</template>

<script>
import { evntBus } from "../../bus";
export default {
  data: () => ({
    addressDialog: false,
    address: {},
    update_address: null,
    customer: "",
    territory: "",
    territorys: [],
    parent_territory: "",
    parent_territorys: [],
    cities: ["Giza", "Alexandria", "Cairo"],
    city: "",
    address_type: "",
    address_types: [
      "Billing",
      "Shipping",
      "Office",
      "Personal",
      "Plant",
      "Postal",
      "Shop",
      "Subsidiary",
      "Warehouse",
      "Current",
      "Permanent",
      "Other",
    ],
  }),

  methods: {
    close_dialog() {
      this.addressDialog = false;
    },

    getParentTerritorys() {
      if (this.parent_territorys.length > 0) return;
      const vm = this;
      frappe.db
        .get_list("Territory", {
          fields: ["name"],
          filters: { is_group: 1 },
          limit: 5000,
          order_by: "name",
        })
        .then((data) => {
          if (data.length > 0) {
            data.forEach((el) => {
              vm.parent_territorys.push(el.name);
            });
          }
        });
    },
    getChildTerritorys() {
      const vm = this;
      vm.territorys = [];
      vm.territory = "";
      if (!vm.parent_territory) return;
      frappe.db
        .get_list("Territory", {
          fields: ["name"],
          filters: { parent_territory: vm.parent_territory },
          limit: 5000,
          order_by: "name",
        })
        .then((data) => {
          if (data.length > 0) {
            data.forEach((el) => {
              vm.territorys.push(el.name);
            });
          }
        });
    },
    submit_dialog() {
      const vm = this;
      this.address.customer = this.customer;
      this.address.doctype = "Customer";
      this.address.territory = this.territory;
      this.address.address_type = this.address_type;
      if (!this.address_type) {
        evntBus.$emit("show_mesage", {
          text: __("Please select address type"),
          color: "error",
        });
        return;
      }
      this.address.city = this.city;
      this.address.method = this.update_address ? "update" : "create";
      this.address.address_id = this.update_address;
      frappe.call({
        method: "posawesome.posawesome.api.posapp.make_address",
        args: {
          args: this.address,
        },
        callback: (r) => {
          if (!r.exc) {
            evntBus.$emit("add_the_new_address", r.message);
            evntBus.$emit(
              "set_shipping_address_name_after_add",
              r.message.name,
            );
            evntBus.$emit("show_mesage", {
              text: __("Customer Address created successfully."),
              color: "success",
            });
            vm.addressDialog = false;
            vm.customer = "";
            vm.address = {};
          }
        },
      });
    },
    get_address() {
      const vm = this;
      frappe.call({
        method: "posawesome.posawesome.api.posapp.get_address_customer",
        args: {
          address: this.update_address,
        },
        callback: (r) => {
          if (!r.exc) {
            vm.address = r.message;
            console.log(vm.address, "vm.address");
          }
        },
      });
    },
  },
  created: function () {
    evntBus.$on("open_new_address", (data) => {
      this.addressDialog = true;
      this.customer = data.customer;
      console.log("open_new_address", data.address);
      this.update_address = data.address;
      if (this.update_address) {
        this.get_address();
      }
      this.getParentTerritorys();
    });
  },
};
</script>
