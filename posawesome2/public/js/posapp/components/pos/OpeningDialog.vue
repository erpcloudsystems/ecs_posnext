<template>
  <v-row justify="center">
    <v-dialog v-model="isOpen" persistent max-width="600px">
      <v-card>
        <v-card-title>
          <span class="headline primary--text">{{
            __("Create POS Opening Shift")
          }}</span>
        </v-card-title>
        <v-card-text>
          <v-container>
            <v-row>
              <v-col cols="12">
                <v-autocomplete
                  :items="companies"
                  :label="__('Company')"
                  v-model="company"
                  required
                />
              </v-col>
              <v-col cols="12">
                <v-autocomplete
                  :items="pos_profiles"
                  :label="__('POS Profile')"
                  v-model="pos_profile"
                  required
                />
              </v-col>
              <v-col cols="12">
                <v-data-table
                  :headers="payments_methods_headers"
                  :items="payments_methods"
                  item-key="mode_of_payment"
                  class="elevation-1"
                  :items-per-page="itemsPerPage"
                  hide-default-footer
                >
                  <template v-slot:item.amount="props">
                    <v-edit-dialog :return-value.sync="props.item.amount">
                      {{ currencySymbol(props.item.currency) }}
                      {{ formtCurrency(props.item.amount) }}
                      <template v-slot:input>
                        <v-text-field
                          v-model="props.item.amount"
                          :rules="[max25chars]"
                          :label="__('Edit')"
                          single-line
                          counter
                          type="number"
                        />
                      </template>
                    </v-edit-dialog>
                  </template>
                </v-data-table>
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" dark @click="go_desk">{{ __("Cancel") }}</v-btn>
          <v-btn
            color="success"
            :disabled="is_loading"
            dark
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
import format from "../../format";

export default {
  mixins: [format],
  props: ["dialog"],
  data() {
    return {
      isOpen: this.dialog ? this.dialog : false,
      dialog_data: {},
      is_loading: false,
      companies: [],
      company: "",
      pos_profiles_data: [],
      pos_profiles: [],
      pos_profile: "",
      shift_windows: [],
      allow_sales_all_day: false,
      payments_method_data: [],
      payments_methods: [],
      payments_methods_headers: [
        {
          text: __("Mode of Payment"),
          align: "start",
          sortable: false,
          value: "mode_of_payment",
        },
        {
          text: __("Opening Amount"),
          value: "amount",
          align: "center",
          sortable: false,
        },
      ],
      itemsPerPage: 100,
      max25chars: (v) => v.length <= 12 || __("Input too long!"),
      pagination: {},
      snack: false,
      snackColor: "",
      snackText: "",
    };
  },
  watch: {
    company(val) {
      this.pos_profiles = [];
      this.pos_profiles_data.forEach((element) => {
        if (element.company === val) {
          this.pos_profiles.push(element.name);
        }
      });
      if (this.pos_profiles.length) {
        this.pos_profile = this.pos_profiles[0];
        this.set_shift_windows(this.pos_profile);
      } else {
        this.pos_profile = "";
        this.shift_windows = [];
      }
    },
    pos_profile(val) {
      this.payments_methods = [];
      this.payments_method_data.forEach((element) => {
        if (element.parent === val && !element.custom_hide) {
          this.payments_methods.push({
            mode_of_payment: element.mode_of_payment,
            amount: 0,
            currency: element.currency,
          });
        }
      });
      this.set_shift_windows(val);
    },
  },
  methods: {
    close_opening_dialog() {
      evntBus.$emit("close_opening_dialog");
    },
    get_opening_dialog_data() {
      const vm = this;
      frappe.call({
        method: "posawesome.posawesome.api.posapp.get_opening_dialog_data",
        args: {},
        callback: function (r) {
          if (r.message) {
            r.message.companies.forEach((element) => {
              vm.companies.push(element.name);
            });
            vm.company = vm.companies[0];
            vm.pos_profiles_data = r.message.pos_profiles_data;
            let isCall_center = false;
            vm.pos_profiles_data.forEach((element) => {
              if (element.name === "Call Center") {
                isCall_center = true;
                vm.pos_profile = element.name;
              }
            });
            vm.payments_method_data = r.message.payments_method;
            vm.set_shift_windows(vm.pos_profile);
            if (isCall_center) vm.submit_dialog();
          }
        },
      });
    },
    getCurrentTimeFormatted() {
      const now = new Date();
      const hours = String(now.getHours()).padStart(2, "0");
      const minutes = String(now.getMinutes()).padStart(2, "0");
      const seconds = String(now.getSeconds()).padStart(2, "0");
      return `${hours}:${minutes}:${seconds}`;
    },
    set_shift_windows(profileName) {
      this.shift_windows = [];
      this.allow_sales_all_day = false;
      const profile = this.pos_profiles_data.find(
        (p) => p.name === profileName,
      );
      if (!profile) return;
      this.allow_sales_all_day = !!profile.posa_allow_sales_whole_day;
      [
        ["posa_shift_1_start", "posa_shift_1_end"],
        ["posa_shift_2_start", "posa_shift_2_end"],
      ].forEach(([startKey, endKey]) => {
        if (profile[startKey] && profile[endKey]) {
          this.shift_windows.push({
            start: profile[startKey],
            end: profile[endKey],
          });
        }
      });
    },
    getTimeInMinutes(timeStr) {
      const [h, m, s] = timeStr.split(":").map(Number);
      return h * 60 + m + s / 60;
    },
    submit_dialog() {
      const currentTime = this.getCurrentTimeFormatted();
      const nowTime = this.getTimeInMinutes(currentTime);
      if (this.allow_sales_all_day) {
        // Bypass shift window validation when enabled on POS Profile
        this.finish_submit();
        return;
      }
      const windows =
        this.shift_windows && this.shift_windows.length
          ? this.shift_windows
          : [
              { start: "13:00:00", end: "22:00:00" },
              { start: "22:00:00", end: "06:00:00" },
            ];
      const isWithinShift = windows.some((w) => {
        const startTime = this.getTimeInMinutes(w.start);
        const endTime = this.getTimeInMinutes(w.end);
        if (Number.isNaN(startTime) || Number.isNaN(endTime)) return false;
        return startTime < endTime
          ? nowTime >= startTime && nowTime <= endTime
          : nowTime >= startTime || nowTime <= endTime;
      });
      if (!this.company || !this.pos_profile || !isWithinShift) {
        evntBus.$emit("show_mesage", {
          text: __("Outside the configured shift window for this POS Profile."),
          color: "error",
        });
        return;
      }
      this.finish_submit();
    },
    finish_submit() {
      this.is_loading = true;
      const vm = this;
      return frappe
        .call("posawesome.posawesome.api.posapp.create_opening_voucher", {
          pos_profile: this.pos_profile,
          company: this.company,
          balance_details: this.payments_methods,
        })
        .then((r) => {
          if (r.message) {
            evntBus.$emit("register_pos_data", r.message);
            evntBus.$emit("set_company", r.message.company);
            vm.close_opening_dialog();
            vm.is_loading = false;
          }
        })
        .catch((err) => {
          vm.is_loading = false;
          const errorMessage =
            err.message || err._server_messages
              ? JSON.parse(err._server_messages || "[]")[0]?.message ||
                __("Failed to open shift")
              : __("Failed to open shift");
          evntBus.$emit("show_mesage", {
            text: errorMessage,
            color: "error",
          });
        });
    },
    go_desk() {
      frappe.set_route("/");
      location.reload();
    },
  },
  created: function () {
    this.$nextTick(function () {
      this.get_opening_dialog_data();
    });
  },
};
</script>
