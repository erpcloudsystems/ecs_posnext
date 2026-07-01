<template>
  <v-row justify="center">
    <v-dialog
      v-model="customerDialog"
      max-width="620"
      overlay-color="rgba(23, 34, 59, 0.75)"
      overlay-opacity="0.6"
      content-class="customer-dialog"
      @click:outside="clear_customer"
    >
      <v-card class="customer-dialog-card">
        <div class="dialog-header">
          <div class="dialog-icon">
            <v-icon large color="secondary">mdi-account-circle</v-icon>
          </div>
          <div>
            <h4 class="dialog-title">
              {{ customer_id ? __("Update Customer") : __("Create Customer") }}
            </h4>
            <p class="dialog-subtitle">
              {{ __("Keep customer records sharp while staying on the sale.") }}
            </p>
          </div>
        </div>
        <v-divider class="mb-6"></v-divider>
        <v-card-text class="pa-0">
          <v-container>
            <v-row>
              <v-col cols="12">
                <v-text-field
                  dense
                  color="primary"
                  class="dialog-input"
                  :label="__('Customer Name') + ' *'"
                  hide-details
                  v-model="customer_name"
                ></v-text-field>
              </v-col>
              <!-- <v-col cols="6">
                <v-text-field
                  dense
                  color="primary"
                  :label="__('Tax ID')"
                  background-color="white"
                  hide-details
                  v-model="tax_id"
                ></v-text-field>
              </v-col> -->
              <v-col cols="4">
                <v-text-field
                  dense
                  color="primary"
                  class="dialog-input"
                  :label="__('Mobile No') + ' *'"
                  hide-details
                  v-model="mobile_no"
                ></v-text-field>
              </v-col>
              <v-col cols="4">
                <v-text-field
                  dense
                  color="primary"
                  class="dialog-input"
                  :label="__('Other Mobile No')"
                  hide-details
                  v-model="custom_other_mobile_no"
                ></v-text-field>
              </v-col>
              <!-- <v-col cols="6">
                <v-text-field
                  dense
                  color="primary"
                  :label="__('Email Id')"
                  background-color="white"
                  hide-details
                  v-model="email_id"
                ></v-text-field>
              </v-col> -->
              <v-col cols="4">
                <v-select
                  dense
                  :label="__('Gender')"
                  :items="genders"
                  v-model="gender"
                  color="primary"
                  class="dialog-input"
                ></v-select>
              </v-col>
              <!-- <v-col cols="6">
                <v-text-field
                  dense
                  color="primary"
                  :label="__('Referral Code')"
                  background-color="white"
                  hide-details
                  v-model="referral_code"
                ></v-text-field>
              </v-col> -->
              <v-col cols="6">
                <v-menu
                  ref="birthday_menu"
                  v-model="birthday_menu"
                  :close-on-content-click="false"
                  transition="scale-transition"
                  dense
                >
                  <template v-slot:activator="{ on, attrs }">
                    <v-text-field
                      v-model="birthday"
                      :label="__('Birthday')"
                      readonly
                      dense
                      clearable
                      hide-details
                      v-bind="attrs"
                      v-on="on"
                      class="dialog-input"
                      color="primary"
                    ></v-text-field>
                  </template>
                  <v-date-picker
                    v-model="birthday"
                    color="primary"
                    no-title
                    scrollable
                    :max="frappe.datetime.now_date()"
                    @input="birthday_menu = false"
                  >
                  </v-date-picker>
                </v-menu>
              </v-col>
              <v-col cols="6">
                <v-autocomplete
                  clearable
                  dense
                  auto-select-first
                  color="primary"
                  class="dialog-input"
                  :label="__('Customer Group') + ' *'"
                  v-model="group"
                  :items="groups"
                  :no-data-text="__('Group not found')"
                  hide-details
                  required
                >
                </v-autocomplete>
              </v-col>
              <!-- <v-col cols="6">
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
                >
                </v-autocomplete>
              </v-col> -->
              <!-- <v-col cols="6" v-if="loyalty_program">
                <v-text-field
                  v-model="loyalty_program"
                  :label="__('Loyalty Program')"
                  dense
                  readonly
                  hide-details
                ></v-text-field>
              </v-col>
              <v-col cols="6" v-if="loyalty_points">
                <v-text-field
                  v-model="loyalty_points"
                  :label="__('Loyalty Points')"
                  dense
                  readonly
                  hide-details
                ></v-text-field>
              </v-col> -->
            </v-row>
          </v-container>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn class="dialog-action neutral" text @click="close_dialog">{{
            __("Close")
          }}</v-btn>
          <v-btn
            class="dialog-action primary"
            color="secondary"
            depressed
            @click="submit_dialog"
            >{{ __("Submit") }}</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-row>
</template>

<script>
import { evntBus } from "../../bus";
export default {
  data: () => ({
    customerDialog: false,
    pos_profile: "",
    customer_id: "",
    customer_name: "",
    tax_id: "",
    mobile_no: "",
    custom_other_mobile_no: "",
    email_id: "",
    referral_code: "",
    birthday: null,
    birthday_menu: false,
    group: "",
    groups: [],
    territory: "",
    territorys: [],
    genders: [],
    customer_type: "Individual",
    gender: "",
    loyalty_points: null,
    loyalty_program: null,
  }),
  watch: {},
  methods: {
    close_dialog() {
      this.customerDialog = false;
      this.clear_customer();
    },
    clear_customer() {
      this.customer_name = "";
      this.tax_id = "";
      this.mobile_no = "";
      this.custom_other_mobile_no = "";
      this.email_id = "";
      this.referral_code = "";
      this.birthday = "";
      this.group = frappe.defaults.get_user_default("Customer Group");
      this.territory = frappe.defaults.get_user_default("Territory");
      this.customer_id = "";
      this.customer_type = "Individual";
      this.gender = "";
      this.loyalty_points = null;
      this.loyalty_program = null;
    },
    getCustomerGroups() {
      if (this.groups.length > 0) return;
      const vm = this;
      frappe.db
        .get_list("Customer Group", {
          fields: ["name"],
          filters: { is_group: 0 },
          limit: 1000,
          order_by: "name",
        })
        .then((data) => {
          if (data.length > 0) {
            data.forEach((el) => {
              vm.groups.push(el.name);
            });
          }
        });
    },
    getCustomerTerritorys() {
      if (this.territorys.length > 0) return;
      const vm = this;
      frappe.db
        .get_list("Territory", {
          fields: ["name"],
          filters: { is_group: 0 },
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
    getGenders() {
      const vm = this;
      frappe.db
        .get_list("Gender", {
          fields: ["name"],
          page_length: 10,
        })
        .then((data) => {
          if (data.length > 0) {
            data.forEach((el) => {
              vm.genders.push(el.name);
            });
          }
        });
    },
    submit_dialog() {
      // validate if all required fields are filled
      if (!this.customer_name) {
        evntBus.$emit("show_mesage", {
          text: __("Customer name is required."),
          color: "error",
        });
        return;
      }
      if (!this.mobile_no) {
        evntBus.$emit("show_mesage", {
          text: __("Mobile No is required."),
          color: "error",
        });
        return;
      }
      if (this.mobile_no.length != 11) {
        evntBus.$emit("show_mesage", {
          text: __("Mobile No Must be 11 digits."),
          color: "error",
        });
        return;
      }

      if (!this.group) {
        evntBus.$emit("show_mesage", {
          text: __("Customer group is required."),
          color: "error",
        });
        return;
      }
      // if (!this.territory) {
      //   evntBus.$emit('show_mesage', {
      //     text: __('Customer territory is required.'),
      //     color: 'error',
      //   });
      //   return;
      // }
      if (this.customer_name) {
        const vm = this;
        const args = {
          customer_id: this.customer_id,
          customer_name: this.customer_name,
          company: this.pos_profile.company,
          tax_id: this.tax_id,
          mobile_no: this.mobile_no,
          email_id: this.email_id,
          referral_code: this.referral_code,
          birthday: this.birthday,
          customer_group: this.group,
          custom_other_mobile_no: this.custom_other_mobile_no,
          // territory: this.territory,
          customer_type: this.customer_type,
          gender: this.gender,
          method: this.customer_id ? "update" : "create",
          pos_profile_doc: this.pos_profile,
        };
        frappe.call({
          method: "posawesome.posawesome.api.posapp.create_customer",
          args: args,
          callback: (r) => {
            if (!r.exc && r.message.name) {
              let text = __("Customer created successfully.");
              if (vm.customer_id) {
                text = __("Customer updated successfully.");
              }
              evntBus.$emit("show_mesage", {
                text: text,
                color: "success",
              });
              args.name = r.message.name;
              frappe.utils.play_sound("submit");
              evntBus.$emit("add_customer_to_list", args);
              evntBus.$emit("set_customer", r.message.name);
              evntBus.$emit("fetch_customer_details");
              vm.close_dialog();
            } else {
              frappe.utils.play_sound("error");
              evntBus.$emit("show_mesage", {
                text: __("Customer creation failed."),
                color: "error",
              });
            }
          },
        });
        this.customerDialog = false;
      }
    },
  },
  created: function () {
    evntBus.$on("open_update_customer", (data, new_customer = false) => {
      this.customerDialog = true;
      if (data && !new_customer) {
        this.customer_name = data.customer_name;
        this.customer_id = data.name;
        this.tax_id = data.tax_id;
        this.mobile_no = data.mobile_no;
        this.custom_other_mobile_no = data.custom_other_mobile_no;
        this.email_id = data.email_id;
        this.referral_code = data.referral_code;
        this.birthday = data.birthday;
        this.group = data.customer_group;
        this.territory = data.territory;
        this.loyalty_points = data.loyalty_points;
        this.loyalty_program = data.loyalty_program;
        this.gender = data.gender;
      } else {
        console.log("new_customer", new_customer);
        // this.mobile_no = data.mobile_no;
      }
    });
    evntBus.$on("register_pos_profile", (data) => {
      this.pos_profile = data.pos_profile;
      console.log("pos_profile 1111111111", this.pos_profile);
    });
    evntBus.$on("payments_register_pos_profile", (data) => {
      this.pos_profile = data.pos_profile;
      console.log("pos_profile 222222222222", this.pos_profile);
    });
    this.getCustomerGroups();
    // this.getCustomerTerritorys();
    this.getGenders();
    // set default values for customer group and territory from user defaults
    this.group = frappe.defaults.get_user_default("Customer Group");
    this.territory = frappe.defaults.get_user_default("Territory");
  },
};
</script>

<style scoped>
.customer-dialog-card {
  background: linear-gradient(145deg, #ffffff 0%, #f4f6fb 100%);
  border-radius: 18px;
  padding: 24px 28px 20px;
  box-shadow: 0 22px 45px rgba(23, 34, 59, 0.12);
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 4px;
}

.dialog-icon {
  background: rgba(44, 200, 194, 0.18);
  border-radius: 16px;
  padding: 14px;
}

.dialog-title {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--v-primary-base);
}

.dialog-subtitle {
  margin: 4px 0 0;
  color: var(--v-muted-base, #8a94a6);
  font-size: 0.88rem;
}

::v-deep .dialog-input .v-input__slot {
  background: #f7f8fb !important;
  border-radius: 12px !important;
  border: 1px solid rgba(23, 34, 59, 0.08) !important;
  min-height: 48px;
  box-shadow: none;
  padding-left: 14px;
  transition:
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

::v-deep .dialog-input .v-label {
  color: #6c7a92 !important;
}

::v-deep .dialog-input input,
::v-deep .dialog-input textarea {
  font-weight: 500;
  color: #17223b !important;
}

::v-deep .dialog-input .v-input__slot:hover {
  border-color: rgba(44, 200, 194, 0.45) !important;
  box-shadow: 0 12px 24px rgba(23, 34, 59, 0.1);
}

::v-deep .dialog-input .v-input__slot:focus-within {
  border-color: rgba(44, 200, 194, 0.75) !important;
  box-shadow: 0 18px 32px rgba(44, 200, 194, 0.18);
}

::v-deep .dialog-input .v-select__selections {
  color: #17223b !important;
  font-weight: 500;
}

::v-deep .dialog-input .v-input__append-inner .v-icon,
::v-deep .dialog-input .v-input__prepend-inner .v-icon {
  color: rgba(23, 34, 59, 0.45) !important;
}

.dialog-action {
  min-width: 140px;
  border-radius: 12px !important;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: none !important;
}

.dialog-action.neutral {
  color: var(--v-muted-base, #6c7a92) !important;
}

.dialog-action.primary {
  box-shadow: 0 16px 30px rgba(44, 200, 194, 0.28);
  color: #ffffff !important;
}

::v-deep .v-menu__content .v-list-item {
  background: #ffffff !important;
  border-radius: 12px;
}

::v-deep .v-menu__content .v-list-item:hover {
  background: rgba(44, 200, 194, 0.1) !important;
}

::v-deep .v-list-item--active {
  background: rgba(44, 200, 194, 0.16) !important;
  color: #17223b !important;
}
</style>
