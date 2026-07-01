<template>
  <v-row justify="center">
    <v-dialog v-model="closingDialog" max-width="900px">
      <v-card class="p-4" style="background-color: white !important">
        <v-card-title class="text-center py-2">
          <h6
            class="headline main_color font-weight-black w-100"
            style="text-transform: uppercase"
          >
            {{ __("Shift Closing") }}
          </h6>
        </v-card-title>
        <v-card-text class="pa-0">
          <v-container>
            <v-row>
              <v-col cols="12" class="mb-3 p-0">
                <template>
                  <v-data-table
                    :headers="headers"
                    :items="
                      dialog_data.payment_reconciliation.filter(
                        (item) => item.custom_hide != 1,
                      )
                    "
                    item-key="mode_of_payment"
                    class="elevation-1 custom-table"
                    :items-per-page="itemsPerPage"
                    hide-default-footer
                  >
                    <template v-slot:item.closing_amount="props">
                      <v-edit-dialog
                        :return-value.sync="props.item.closing_amount"
                      >
                        {{ currencySymbol(pos_profile.currency) }}
                        {{ formtCurrency(props.item.closing_amount) }}
                        <template v-slot:input>
                          <v-text-field
                            v-model="props.item.closing_amount"
                            :rules="[max25chars]"
                            :label="__('Edit')"
                            single-line
                            counter
                            type="number"
                          ></v-text-field>
                        </template>
                      </v-edit-dialog>
                    </template>
                    <template v-slot:item.difference="{ item }">
                      {{ currencySymbol(pos_profile.currency) }}
                      {{
                        item.difference = formtCurrency(
                          item.expected_amount - item.closing_amount,
                        )
                      }}</template
                    >
                    <template v-slot:item.opening_amount="{ item }">
                      {{ currencySymbol(pos_profile.currency) }}
                      {{ formtCurrency(item.opening_amount) }}</template
                    >
                    <template v-slot:item.expected_amount="{ item }">
                      {{ currencySymbol(pos_profile.currency) }}
                      {{ formtCurrency(item.expected_amount) }}</template
                    >
                  </v-data-table>
                </template>
              </v-col>
            </v-row>
            <v-row class="mt-2">
              <v-col cols="12" class="pb-0">
                <h6 class="text-uppercase font-weight-bold main_color">
                  {{ __("Cash Denominations (EGP)") }}
                </h6>
              </v-col>
              <v-col
                v-for="field in cashDenominationFields"
                :key="field.key"
                cols="12"
                sm="6"
                md="4"
              >
                <v-text-field
                  v-model.number="dialog_data[field.key]"
                  :label="field.label"
                  type="number"
                  min="0"
                  dense
                ></v-text-field>
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>
        <v-card-actions class="p-0">
          <v-spacer></v-spacer>
          <v-btn
            color="gray"
            style="padding: 0 30px !important"
            dark
            @click="close_dialog"
            >{{ __("Close") }}</v-btn
          >
          <v-btn
            color="#E71D36"
            style="padding: 0 30px !important"
            dark
            @click="submit_dialog"
            >{{ __("Submit") }}</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog v-model="confirmDialog" max-width="420px">
      <v-card>
        <v-card-title class="headline">{{
          __("Confirm Closing")
        }}</v-card-title>
        <v-card-text :style="{ color: confirmColor }" class="confirm-text">
          {{ confirmMessage }}
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text color="grey" @click="cancel_submit">{{ __("No") }}</v-btn>
          <v-btn
            text
            :style="{ color: confirmColor }"
            @click="confirm_submit"
            >{{ __("Yes, Submit") }}</v-btn
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
  data: () => ({
    closingDialog: false,
    confirmDialog: false,
    confirmMessage: "",
    confirmColor: "#16a34a",
    itemsPerPage: 20,
    dialog_data: {},
    originalObj: {},
    pos_profile: "",
    headers: [
      {
        text: __("Mode of Payment"),
        value: "mode_of_payment",
        align: "start",
        sortable: true,
      },
      {
        text: __("Opening Amount"),
        align: "end",
        sortable: true,
        value: "opening_amount",
      },
      {
        text: __("Closing Amount"),
        value: "closing_amount",
        align: "end",
        sortable: true,
      },
    ],
    max25chars: (v) => v.length <= 20 || __("Input too long!"), // TODO : should validate as number
    pagination: {},
    cashDenominationFields: [
      { key: "cash_200_egp", label: __("200 EGP Notes") },
      { key: "cash_100_egp", label: __("100 EGP Notes") },
      { key: "cash_50_egp", label: __("50 EGP Notes") },
      { key: "cash_20_egp", label: __("20 EGP Notes") },
      { key: "cash_10_egp", label: __("10 EGP Notes") },
      { key: "cash_5_egp", label: __("5 EGP Notes") },
      { key: "cash_1_egp", label: __("1 EGP Coins") },
    ],
  }),
  watch: {},

  methods: {
    close_dialog() {
      this.closingDialog = false;
    },
    submit_dialog() {
      const cashMode =
        (this.pos_profile && this.pos_profile.posa_cash_mode_of_payment) ||
        "Cash";
      const cashRow = this.dialog_data.payment_reconciliation.find(
        (row) => row.mode_of_payment === cashMode,
      );
      const denominationMap = {
        cash_200_egp: 200,
        cash_100_egp: 100,
        cash_50_egp: 50,
        cash_20_egp: 20,
        cash_10_egp: 10,
        cash_5_egp: 5,
        cash_1_egp: 1,
      };
      const denominationTotal = Object.entries(denominationMap).reduce(
        (sum, [key, value]) =>
          sum + (Number(this.dialog_data[key]) || 0) * value,
        0,
      );
      if (cashRow) {
        const closingAmount = Number(cashRow.closing_amount) || 0;
        const precision = this.currency_precision || 2;
        const normalizedClosing = this.flt(closingAmount, precision);
        const normalizedTotal = this.flt(denominationTotal, precision);

        if (Math.abs(normalizedClosing - normalizedTotal) > 0.0001) {
          frappe.msgprint(
            __(
              "Cash closing amount ({0}) must match denominations total ({1})",
              [
                this.formtCurrency(normalizedClosing),
                this.formtCurrency(normalizedTotal),
              ],
            ),
          );
          return;
        }
      }
      this.show_confirmation();
    },
    show_confirmation() {
      const cashMode =
        (this.pos_profile && this.pos_profile.posa_cash_mode_of_payment) ||
        "Cash";
      let cashRow =
        this.dialog_data.payment_reconciliation.find(
          (row) => row.mode_of_payment === cashMode,
        ) || this.dialog_data.payment_reconciliation[0];

      let message = __("Are you sure your data is correct?");
      let color = "#16a34a";
      if (cashRow) {
        const expected = Number(cashRow.expected_amount) || 0;
        const closing = Number(cashRow.closing_amount) || 0;
        const diff = closing - expected;

        if (diff === 0) {
          message = __("Thank you! Your closing is correct.");
          color = "#16a34a"; // green
        } else if (diff < 0) {
          message = __("Your closing is short by {0}.", [
            this.formtCurrency(Math.abs(diff)),
          ]);
          color = "#ef4444"; // red
        } else if (diff > 0) {
          message = __("Your closing is over by {0}.", [
            this.formtCurrency(diff),
          ]);
          color = "#f97316"; // orange
        }
      }
      this.confirmMessage = message;
      this.confirmColor = color;
      this.closingDialog = false;
      this.confirmDialog = true;
    },
    confirm_submit() {
      this.confirmDialog = false;
      evntBus.$emit("submit_closing_pos", this.dialog_data);
      this.closingDialog = false;
    },
    cancel_submit() {
      this.confirmDialog = false;
    },
  },

  created: function () {
    evntBus.$on("open_ClosingDialog", (data) => {
      this.closingDialog = true;
      this.dialog_data = data;
      const result = this.pos_profile.payments.reduce((acc, item) => {
        acc[item.mode_of_payment] = item.custom_hide;
        return acc;
      }, {});
      this.originalObj = result;
      this.dialog_data.payment_reconciliation.forEach((item) => {
        if (this.originalObj[item.mode_of_payment]) {
          item.custom_hide = this.originalObj[item.mode_of_payment];
        } else {
          item.custom_hide = false;
        }
      });
    });
    evntBus.$on("register_pos_profile", (data) => {
      this.pos_profile = data.pos_profile;
      if (!this.pos_profile.hide_expected_amount) {
        this.headers.push({
          text: __("Expected Amount"),
          value: "expected_amount",
          align: "end",
          sortable: false,
        });
        this.headers.push({
          text: __("Difference"),
          value: "difference",
          align: "end",
          sortable: false,
        });
      }
    });
  },
};
</script>

<style scoped>
.main_color {
  color: #e71d36 !important;
}

/* Target header cells */
::v-deep .custom-table .v-data-table-header th {
  background-color: #2c3832 !important;
  color: white !important;
}

/* Target tbody */
::v-deep .custom-table tbody {
  background-color: white !important;
}

::v-deep .custom-table thead th:first-child {
  border-top-left-radius: 8px;
}

::v-deep .custom-table thead th:last-child {
  border-top-right-radius: 8px;
}

::v-deep .custom-table tbody tr:last-child td:first-child {
  border-bottom-left-radius: 8px;
}

::v-deep .custom-table tbody tr:last-child td:last-child {
  border-bottom-right-radius: 8px;
}

.confirm-text {
  font-weight: 600;
}
</style>
