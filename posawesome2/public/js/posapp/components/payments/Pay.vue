<template>
  <div fluid>
    <v-row v-show="!dialog">
      <v-col md="8" cols="12" class="pb-2 pr-0">
        <v-card
          class="main mx-auto grey lighten-5 mt-3 p-3 pb-16 overflow-y-auto"
          style="max-height: 94vh; height: 94vh"
        >
          <Customer></Customer>
          <v-divider></v-divider>
          <div>
            <v-row>
              <v-col md="7" cols="12">
                <p>
                  <strong>{{ __("Invoices") }}</strong>
                  <span v-if="total_outstanding_amount" class="primary--text"
                    >{{ __("- Total Outstanding") }} :
                    {{ currencySymbol(pos_profile.currency) }}
                    {{ formtCurrency(total_outstanding_amount) }}</span
                  >
                </p>
              </v-col>
              <v-col md="5" cols="12">
                <p v-if="total_selected_invoices" class="golden--text text-end">
                  <span>{{ __("Total Selected :") }}</span>
                  <span>
                    {{ currencySymbol(pos_profile.currency) }}
                    {{ formtCurrency(total_selected_invoices) }}
                  </span>
                </p>
              </v-col>
            </v-row>
            <v-row align="center" no-gutters class="mb-1">
              <v-col md="4" cols="12">
                <v-select
                  dense
                  outlined
                  hide-details
                  clearable
                  background-color="white"
                  v-model="pos_profile_search"
                  :items="pos_profiles_list"
                  item-value="name"
                  label="Select POS Profile"
                ></v-select>
              </v-col>
              <v-col> </v-col>
              <v-col md="3" cols="12">
                <v-btn
                  block
                  color="warning"
                  dark
                  @click="get_outstanding_invoices"
                  >{{ __("Search") }}</v-btn
                >
              </v-col>
            </v-row>
            <!-- <v-data-table
              :headers="invoices_headers"
              :items="outstanding_invoices"
              item-key="name"
              class="elevation-1 mt-0"
              show-select
              v-model="selected_invoices"
              :loading="invoices_loading"
              checkbox-color="primary"
              @item-selected="onInvoiceSelected"
            >
              <template v-slot:item.grand_total="{ item }">
                {{ currencySymbol(item.currency) }}
                {{ formtCurrency(item.grand_total) }}
              </template>
<template v-slot:item.outstanding_amount="{ item }">
                <span class="primary--text"
                  >{{ currencySymbol(item.currency) }}
                  {{ formtCurrency(item.outstanding_amount) }}</span
                >
              </template>
</v-data-table> -->

            <v-card class="mt-2 mb-2">
              <!-- Filters row -->
              <v-row dense>
                <v-col cols="2">
                  <v-combobox
                    v-model="filters.custom_number_order"
                    :items="orderIds"
                    label="Order ID"
                    dense
                    outlined
                    clearable
                  />
                </v-col>

                <v-col cols="2">
                  <v-select
                    v-model="filters.custom_so_type"
                    :items="orderTypeOptionsFiltered"
                    label="Order Type"
                    dense
                    outlined
                    clearable
                  />
                </v-col>

                <v-col cols="2">
                  <v-select
                    v-model="filters.custom_payment_type"
                    :items="[
                      'Cash on delivery',
                      'Credit Card',
                      'Cash Talabat',
                      'Credit Card on delivary',
                      'Cash',
                    ]"
                    label="Payment Type"
                    dense
                    outlined
                    clearable
                  />
                </v-col>

                <v-col cols="3">
                  <v-combobox
                    v-model="filters.customer_name"
                    :items="customers"
                    label="Customer"
                    dense
                    outlined
                    clearable
                  />
                </v-col>

                <v-col cols="3">
                  <v-menu
                    v-model="dateMenu"
                    :close-on-content-click="false"
                    transition="scale-transition"
                    offset-y
                  >
                    <template v-slot:activator="{ on, attrs }">
                      <v-text-field
                        v-model="filters.posting_date"
                        label="Posting Date"
                        readonly
                        dense
                        outlined
                        clearable
                        v-bind="attrs"
                        v-on="on"
                      />
                    </template>

                    <v-date-picker v-model="filters.posting_date" scrollable>
                      <v-spacer />
                      <v-btn text color="primary" @click="dateMenu = false"
                        >OK</v-btn
                      >
                    </v-date-picker>
                  </v-menu>
                </v-col>
              </v-row>

              <!-- Data table -->
              <v-data-table
                :headers="invoices_headers"
                :items="filteredInvoices"
                item-key="name"
                class="elevation-1 mt-0"
                show-select
                v-model="selected_invoices"
                :loading="invoices_loading"
                checkbox-color="primary"
                @item-selected="onInvoiceSelected"
              >
                <template v-slot:item.grand_total="{ item }">
                  {{ currencySymbol(item.currency) }}
                  {{ formtCurrency(item.grand_total) }}
                </template>

                <template v-slot:item.outstanding_amount="{ item }">
                  <span class="primary--text">
                    {{ currencySymbol(item.currency) }}
                    {{ formtCurrency(item.outstanding_amount) }}
                  </span>
                </template>
              </v-data-table>
            </v-card>

            <v-divider></v-divider>
          </div>
          <div
            v-if="
              pos_profile.posa_allow_reconcile_payments &&
              unallocated_payments.length
            "
          >
            <v-row>
              <v-col md="7" cols="12">
                <p>
                  <strong>{{ __("payments") }}</strong>
                  <span v-if="total_unallocated_amount" class="primary--text">
                    {{ __("- Total Unallocated") }} :
                    {{ currencySymbol(pos_profile.currency) }}
                    {{ formtCurrency(total_unallocated_amount) }}
                  </span>
                </p>
              </v-col>
              <v-col md="5" cols="12">
                <p v-if="total_selected_payments" class="golden--text text-end">
                  <span>{{ __("Total Selected :") }}</span>
                  <span>
                    {{ currencySymbol(pos_profile.currency) }}
                    {{ formtCurrency(total_selected_payments) }}
                  </span>
                </p>
              </v-col>
            </v-row>
            <v-data-table
              :headers="unallocated_payments_headers"
              :items="unallocated_payments"
              item-key="name"
              class="elevation-1 mt-0"
              :single-select="singleSelect"
              show-select
              v-model="selected_payments"
              :loading="unallocated_payments_loading"
              checkbox-color="primary"
            >
              <template v-slot:item.paid_amount="{ item }">
                {{ currencySymbol(item.currency) }}
                {{ formtCurrency(item.paid_amount) }}
              </template>
              <template v-slot:item.unallocated_amount="{ item }">
                <span class="primary--text"
                  >{{ currencySymbol(item.currency) }}
                  {{ formtCurrency(item.unallocated_amount) }}</span
                >
              </template>
            </v-data-table>
            <v-divider></v-divider>
          </div>
          <div v-if="pos_profile.posa_allow_mpesa_reconcile_payments">
            <v-row>
              <v-col md="8" cols="12">
                <p>
                  <span
                    ><strong>{{ __("Search Mpesa Payments") }}</strong></span
                  >
                </p>
              </v-col>
              <v-col md="4" cols="12" v-if="total_selected_mpesa_payments">
                <p class="golden--text text-end">
                  <span>{{ __("Total Selected :") }}</span>
                  <span>
                    {{ currencySymbol(pos_profile.currency) }}
                    {{ formtCurrency(total_selected_mpesa_payments) }}
                  </span>
                </p>
              </v-col>
            </v-row>
            <v-row align="center" no-gutters class="mb-1">
              <v-col md="4" cols="12" class="mr-1">
                <v-text-field
                  dense
                  outlined
                  color="primary"
                  :label="__('Search by Name')"
                  background-color="white"
                  hide-details
                  v-model="mpesa_search_name"
                  clearable
                ></v-text-field>
              </v-col>
              <v-col md="4" cols="12" class="mr-1">
                <v-text-field
                  dense
                  outlined
                  color="primary"
                  :label="__('Search by Mobile')"
                  background-color="white"
                  hide-details
                  v-model="mpesa_search_mobile"
                  clearable
                ></v-text-field>
              </v-col>
              <v-col> </v-col>
              <v-col md="3" cols="12">
                <v-btn
                  block
                  color="warning"
                  dark
                  @click="get_draft_mpesa_payments_register"
                  >{{ __("Search") }}</v-btn
                >
              </v-col>
            </v-row>
            <v-data-table
              :headers="mpesa_payment_headers"
              :items="mpesa_payments"
              item-key="name"
              class="elevation-1 mt-0"
              :single-select="singleSelect"
              show-select
              v-model="selected_mpesa_payments"
              :loading="mpesa_payments_loading"
              checkbox-color="primary"
            >
              <template v-slot:item.amount="{ item }">
                <span class="primary--text">
                  {{ currencySymbol(item.currency) }}
                  {{ formtCurrency(item.amount) }}
                </span>
              </template>
            </v-data-table>
          </div>
        </v-card>
      </v-col>
      <v-col md="4" cols="12" class="pb-3">
        <v-card
          class="invoices mx-auto grey lighten-5 mt-3 p-3"
          style="max-height: 94vh; height: 94vh"
        >
          <strong>
            <h4 class="primary--text">Totals</h4>
            <v-row>
              <v-col md="7" class="mt-1">
                <span>{{ __("Total Invoices:") }}</span>
              </v-col>
              <v-col md="5">
                <v-text-field
                  class="p-0 m-0"
                  dense
                  color="primary"
                  background-color="white"
                  hide-details
                  :value="formtCurrency(total_selected_invoices)"
                  total_selected_invoices
                  readonly
                  flat
                  :prefix="currencySymbol(pos_profile.currency)"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-row v-if="total_selected_payments">
              <v-col md="7" class="mt-1"
                ><span>{{ __("Total Payments:") }}</span></v-col
              >
              <v-col md="5">
                <v-text-field
                  class="p-0 m-0"
                  dense
                  color="primary"
                  background-color="white"
                  hide-details
                  :value="formtCurrency(total_selected_payments)"
                  total_selected_payments
                  readonly
                  flat
                  :prefix="currencySymbol(pos_profile.currency)"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-row v-if="total_selected_mpesa_payments">
              <v-col md="7" class="mt-1"
                ><span>{{ __("Total Mpesa:") }}</span></v-col
              >
              <v-col md="5">
                <v-text-field
                  class="p-0 m-0"
                  dense
                  color="primary"
                  background-color="white"
                  hide-details
                  :value="formtCurrency(total_selected_mpesa_payments)"
                  total_selected_mpesa_payments
                  readonly
                  flat
                  :prefix="currencySymbol(pos_profile.currency)"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-divider v-if="payment_methods.length"></v-divider>
            <div v-if="pos_profile.posa_allow_make_new_payments">
              <h4 class="primary--text">Make New Payment</h4>
              <v-row
                v-if="payment_methods.length"
                v-for="method in payment_methods"
                :key="method.row_id"
              >
                <v-col md="7"
                  ><span class="mt-1">{{ __(method.mode_of_payment) }}:</span>
                </v-col>
                <v-col md="5"
                  ><v-text-field
                    class="p-0 m-0"
                    dense
                    color="primary"
                    background-color="white"
                    hide-details
                    :value="formtCurrency(method.amount)"
                    @change="onAmountChange(method, $event)"
                    payments_methods
                    flat
                    :prefix="currencySymbol(pos_profile.currency)"
                  ></v-text-field
                ></v-col>
                <v-col
                  cols="12"
                  v-if="
                    show_paymentrecieptNumber && activeRowId === method.row_id
                  "
                >
                  <v-text-field
                    v-model="recieptNumber"
                    type="number"
                    label="Enter Bank Payment Code"
                    :rules="[(v) => !!v || 'Bank Payment Code is required']"
                    dense
                    outlined
                    hide-details
                    color="primary"
                  />
                </v-col>
              </v-row>
            </div>

            <v-divider></v-divider>
            <v-row>
              <v-col md="7">
                <h4 class="primary--text mt-1">{{ __("Difference:") }}</h4>
              </v-col>
              <v-col md="5">
                <v-text-field
                  class="p-0 m-0"
                  dense
                  color="primary"
                  background-color="white"
                  hide-details
                  :value="formtCurrency(total_of_diff)"
                  total_of_diff
                  flat
                  readonly
                  :prefix="currencySymbol(pos_profile.currency)"
                ></v-text-field>
              </v-col>
            </v-row>
          </strong>
          <div
            class="pb-6 pr-6"
            style="position: absolute; bottom: 0; width: 100%"
          >
            <v-btn
              block
              color="primary"
              dark
              @click="submit"
              :loading="isSubmitting"
              :disabled="isSubmitting"
            >
              {{ __("Submit") }}
            </v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import { evntBus } from "../../bus";
import format from "../../format";
import Customer from "../pos/Customer.vue";
import UpdateCustomer from "../pos/UpdateCustomer.vue";

export default {
  mixins: [format],
  data: function () {
    return {
      isSubmitting: false,
      filters: {
        custom_number_order: "",
        custom_so_type: null,
        custom_payment_type: null,
        customer_name: "",
        posting_date: null,
        due_date: null,
        grand_total_min: null,
        grand_total_max: null,
      },
      dialog: false,
      driver_name: "",
      pos_profile: "",
      pos_opening_shift: "",
      customer_name: "",
      customer_info: "",
      company: "",
      singleSelect: false,
      invoices_loading: false,
      unallocated_payments_loading: false,
      mpesa_payments_loading: false,
      payment_methods: [],
      outstanding_invoices: [],
      unallocated_payments: [],
      mpesa_payments: [],
      selected_invoices: [],
      selected_payments: [],
      selected_mpesa_payments: [],
      pos_profiles_list: [],
      pos_profile_search: "",
      payment_methods_list: [],
      mpesa_searchname: "",
      mpesa_search_mobile: "",
      recieptNumber: "",
      activeRowId: null,
      show_paymentrecieptNumber: false,
      orderTypes: ["Pickup", "Delivery", "Car Service", "Dinin", "Talabat"],

      invoices_headers: [
        // {
        //   text: __("Invoice"),
        //   align: "start",
        //   sortable: true,
        //   value: "name",
        // },
        {
          text: __("Order ID"),
          align: "start",
          sortable: true,
          value: "custom_number_order",
        },
        {
          text: __("Order Type"),
          align: "start",
          sortable: true,
          value: "custom_so_type",
        },
        {
          text: __("Table Number"),
          align: "start",
          sortable: true,
          value: "custom_table_no",
        },
        {
          text: __("Payment Type"),
          align: "start",
          sortable: true,
          value: "custom_payment_type",
        },
        {
          text: __("Customer"),
          align: "start",
          sortable: true,
          value: "customer_name",
        },
        {
          text: __("Date"),
          align: "start",
          sortable: true,
          value: "posting_date",
        },
        {
          text: __("Due Date"),
          align: "start",
          sortable: true,
          value: "due_date",
        },
        {
          text: __("Total"),
          align: "end",
          sortable: true,
          value: "grand_total",
        },
        {
          text: __("Outstanding"),
          align: "end",
          sortable: true,
          value: "outstanding_amount",
        },
      ],
      unallocated_payments_headers: [
        {
          text: __("Payment ID"),
          align: "start",
          sortable: true,
          value: "name",
        },
        {
          text: __("Customer"),
          align: "start",
          sortable: true,
          value: "customer_name",
        },
        {
          text: __("Date"),
          align: "start",
          sortable: true,
          value: "posting_date",
        },
        {
          text: __("Mode"),
          align: "start",
          sortable: true,
          value: "mode_of_payment",
        },
        {
          text: __("Paid"),
          align: "end",
          sortable: true,
          value: "paid_amount",
        },
        {
          text: __("Unallocated"),
          align: "end",
          sortable: true,
          value: "unallocated_amount",
        },
      ],
      mpesa_payment_headers: [
        {
          text: __("Payment ID"),
          align: "start",
          sortable: true,
          value: "transid",
        },
        {
          text: __("Full Name"),
          align: "start",
          sortable: true,
          value: "full_name",
        },
        {
          text: __("Nobile Number"),
          align: "start",
          sortable: true,
          value: "mobile_no",
        },
        {
          text: __("Date"),
          align: "start",
          sortable: true,
          value: "posting_date",
        },
        {
          text: __("Amount"),
          align: "end",
          sortable: true,
          value: "amount",
        },
      ],
    };
  },

  components: {
    Customer,
    UpdateCustomer,
  },

  methods: {
    async onAmountChange(method, event) {
      this.setFormatedCurrency(method, "amount", null, true, event);
      this.show_paymentrecieptNumber = false;
      this.activeRowId = null;

      if (!method.mode_of_payment) return;

      try {
        const res = await frappe.db.get_value(
          "Mode of Payment",
          method.mode_of_payment,
          "custom_required_receipt",
        );

        const type = res?.message?.custom_required_receipt;

        if (type) {
          this.show_paymentrecieptNumber = true;
          this.activeRowId = method.row_id;
        }
      } catch (error) {
        console.error("Failed to fetch mode of payment type:", error);
      }
    },
    check_opening_entry() {
      return frappe
        .call("posawesome.posawesome.api.posapp.check_opening_shift", {
          user: frappe.session.user,
        })
        .then((r) => {
          if (r.message) {
            this.pos_profile = r.message.pos_profile;
            this.pos_opening_shift = r.message.pos_opening_shift;
            this.company = r.message.company.name;
            evntBus.$emit("register_pos_profile", this.pos_profile);
            evntBus.$emit("payments_register_pos_profile", this.pos_profile);
            evntBus.$emit("set_company", r.message.company);
            this.set_payment_methods();
            this.pos_profile_search = r.message.pos_profile.name;
            this.pos_profiles_list.push(this.pos_profile_search);
            this.payment_methods_list = [];
            this.pos_profile.payments.forEach((element) => {
              this.payment_methods_list.push(element.mode_of_payment);
            });
            this.get_available_pos_profiles();
            this.get_outstanding_invoices();
            this.get_draft_mpesa_payments_register();
            if (r.message.must_close) {
              evntBus.$emit("show_mesage", {
                text: __(
                  "Shift ended. You can reconcile/pay dues before closing.",
                ),
                color: "warning",
              });
            }
          } else {
            this.create_opening_voucher();
          }
        });
    },
    get_available_pos_profiles() {
      if (!this.pos_profile.posa_allow_mpesa_reconcile_payments) return;
      return frappe
        .call(
          "posawesome.posawesome.api.payment_entry.get_available_pos_profiles",
          {
            company: this.company,
            currency: this.pos_profile.currency,
          },
        )
        .then((r) => {
          if (r.message) {
            this.pos_profiles_list = r.message;
          }
        });
    },
    create_opening_voucher() {
      this.dialog = true;
    },
    // fetch_driver_details() {
    //   const vm = this;
    //   if (this.customer_name) {
    //     frappe.call({
    //       method: "posawesome.posawesome.api.posapp.get_driver_info",
    //       args: {
    //         customer: vm.customer_name,
    //       },
    //       async: false,
    //       callback: (r) => {
    //         const message = r.message;
    //         if (!r.exc) {
    //           vm.customer_info = {
    //             ...message,
    //           };
    //           // vm.set_mpesa_search_params();
    //           evntBus.$emit("set_driver_info_to_edit", vm.customer_info);
    //         }
    //       },
    //     });
    //   }
    // },
    fetch_customer_details() {
      const vm = this;
      if (this.customer_name) {
        frappe.call({
          method: "posawesome.posawesome.api.posapp.get_customer_info",
          args: {
            customer: vm.customer_name,
          },
          async: false,
          callback: (r) => {
            const message = r.message;
            if (!r.exc) {
              vm.customer_info = {
                ...message,
              };
              vm.set_mpesa_search_params();
              evntBus.$emit("set_customer_info_to_edit", vm.customer_info);
            }
          },
        });
      }
    },
    onInvoiceSelected(event) {
      evntBus.$emit("set_customer", event.item.customer);
    },
    get_outstanding_invoices() {
      this.invoices_loading = true;
      return frappe
        .call(
          "posawesome.posawesome.api.payment_entry.get_outstanding_invoices",
          {
            customer: this.customer_name,
            company: this.company,
            currency: this.pos_profile.currency,
            pos_profile_name: this.pos_profile_search,
            driver: this.driver_name,
          },
        )
        .then((r) => {
          if (r.message) {
            this.outstanding_invoices = r.message;
            this.invoices_loading = false;
          }
        });
    },
    get_outstanding_invoices_driver() {
      this.invoices_loading = true;
      return frappe
        .call(
          "posawesome.posawesome.api.payment_entry.get_outstanding_invoices_driver_cpy",
          {
            driver: this.customer_name,
            company: this.company,
            currency: this.pos_profile.currency,
            pos_profile_name: this.pos_profile_search,
          },
        )
        .then((r) => {
          if (r.message) {
            this.outstanding_invoices = r.message;
            this.invoices_loading = false;
          }
        });
    },
    get_unallocated_payments() {
      if (!this.pos_profile.posa_allow_reconcile_payments) return;
      this.unallocated_payments_loading = true;
      if (!this.customer_name) {
        this.unallocated_payments = [];
        this.unallocated_payments_loading = false;
        return;
      }
      return frappe
        .call(
          "posawesome.posawesome.api.payment_entry.get_unallocated_payments",
          {
            customer: this.customer_name,
            company: this.company,
            currency: this.pos_profile.currency,
          },
        )
        .then((r) => {
          if (r.message) {
            this.unallocated_payments = r.message;
            this.unallocated_payments_loading = false;
          }
        });
    },
    get_unallocated_payments_driver() {
      if (!this.pos_profile.posa_allow_reconcile_payments) return;
      this.unallocated_payments_loading = true;
      if (!this.customer_name) {
        this.unallocated_payments = [];
        this.unallocated_payments_loading = false;
        return;
      }
      return frappe
        .call(
          "posawesome.posawesome.api.payment_entry.get_unallocated_payments",
          {
            customer: this.customer_name,
            company: this.company,
            currency: this.pos_profile.currency,
          },
        )
        .then((r) => {
          if (r.message) {
            this.unallocated_payments = r.message;
            this.unallocated_payments_loading = false;
          }
        });
    },
    set_mpesa_search_params() {
      if (!this.pos_profile.posa_allow_mpesa_reconcile_payments) return;
      if (!this.customer_name) return;
      this.mpesa_search_name = this.customer_info.customer_name.split(" ")[0];
      if (this.customer_info.mobile_no) {
        this.mpesa_search_mobile =
          this.customer_info.mobile_no.substring(0, 4) +
          " ***** " +
          this.customer_info.mobile_no.substring(9);
      }
    },
    get_draft_mpesa_payments_register() {
      if (!this.pos_profile.posa_allow_mpesa_reconcile_payments) return;
      const vm = this;
      this.mpesa_payments_loading = true;
      return frappe
        .call("posawesome.posawesome.api.m_pesa.get_mpesa_draft_payments", {
          company: vm.company,
          mode_of_payment: null,
          full_name: vm.mpesa_search_name || null,
          mobile_no: vm.mpesa_search_mobile || null,
          payment_methods_list: vm.payment_methods_list,
        })
        .then((r) => {
          if (r.message) {
            vm.mpesa_payments = r.message;
          } else {
            vm.mpesa_payments = [];
          }
          vm.mpesa_payments_loading = false;
        });
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
    clear_all(with_customer_info = true) {
      this.customer_name = "";
      if (with_customer_info) {
        this.customer_info = "";
      }
      this.mpesa_search_mobile = "";
      this.mpesa_search_name = "";
      this.mpesa_payments = [];
      this.selected_mpesa_payments = [];
      this.outstanding_invoices = [];
      this.unallocated_payments = [];
      this.selected_invoices = [];
      this.selected_payments = [];
      this.selected_mpesa_payments = [];
      this.recieptNumber = "";
      this.set_payment_methods();
    },
    submit() {
      if (this.isSubmitting) return;
      this.isSubmitting = true;
      const customer = this.customer_name;
      const vm = this;
      if (!customer) {
        this.isSubmitting = false;
        frappe.throw(__("Please select a customer"));
        return;
      }
      if (vm.recieptNumber == "" && vm.show_paymentrecieptNumber) {
        this.isSubmitting = false;
        frappe.throw(__("Please Enter Receipt Number"));
        return;
      }
      if (
        this.total_selected_payments == 0 &&
        this.total_selected_mpesa_payments == 0 &&
        this.total_payment_methods == 0
      ) {
        this.isSubmitting = false;
        frappe.throw(__("Please make a payment or select an payment"));
        return;
      }
      if (
        this.total_selected_payments > 0 &&
        this.selected_invoices.length == 0
      ) {
        this.isSubmitting = false;
        frappe.throw(__("Please select an invoice"));
        return;
      }
      if (this.total_of_diff != 0) {
        this.isSubmitting = false;
        frappe.throw(__("Please Pay same invoice"));
        return;
      }
      this.payment_methods.forEach((payment) => {
        payment.amount = flt(payment.amount);
      });

      const payload = {};
      payload.customer = customer;
      payload.company = this.company;
      payload.currency = this.pos_profile.currency;
      payload.pos_opening_shift_name = this.pos_opening_shift.name;
      payload.pos_profile_name = this.pos_profile.name;
      payload.pos_profile = this.pos_profile;
      payload.payment_methods = this.payment_methods;
      payload.selected_invoices = this.selected_invoices;
      payload.selected_payments = this.selected_payments;
      payload.total_selected_invoices = flt(this.total_selected_invoices);
      payload.selected_mpesa_payments = this.selected_mpesa_payments;
      payload.total_selected_payments = flt(this.total_selected_payments);
      payload.total_payment_methods = flt(this.total_payment_methods);
      payload.custom_receipt_number = vm.recieptNumber;

      payload.total_selected_mpesa_payments = flt(
        this.total_selected_mpesa_payments,
      );

      frappe.call({
        method: "posawesome.posawesome.api.payment_entry.process_pos_payment",
        args: { payload },
        freeze: true,
        freeze_message: __("Processing Payment"),
        callback: function (r) {
          if (r.message) {
            frappe.utils.play_sound("submit");
            const print_format =
              vm.pos_profile.custom_print_format_for_online ||
              vm.pos_profile.print_format;
            const letter_head = vm.pos_profile.letter_head || 0;
            const url =
              frappe.urllib.get_base_url() +
              "/printview?doctype=Sales%20Invoice&name=" +
              vm.selected_invoices[0].name +
              "&trigger_print=1" +
              "&format=" +
              print_format +
              "&no_letterhead=" +
              letter_head;
            const printWindow = window.open(url, "Print");
            if (printWindow) {
              printWindow.addEventListener(
                "load",
                function () {
                  printWindow.print();
                  // printWindow.close();
                  // NOTE : uncomoent this to auto closing printing window
                },
                true,
              );
            } else {
              frappe.show_alert({
                message: __("Popup blocked. Please allow popups for printing."),
                indicator: "orange",
              });
            }
            frappe.show_alert({
              message: __("Successfully Reconciled"),
              indicator: "green",
            });
            vm.clear_all(false);
            vm.customer_name = customer;
            vm.get_outstanding_invoices();
            vm.get_unallocated_payments();
            vm.set_mpesa_search_params();
            vm.get_draft_mpesa_payments_register();
          }
          vm.isSubmitting = false;
        },
        error: function () {
          vm.isSubmitting = false;
        },
      });
    },
    refreshPayment() {
      this.fetch_customer_details();
      this.get_outstanding_invoices();
      this.get_unallocated_payments();
      this.get_draft_mpesa_payments_register();
    },
  },

  computed: {
    isCallCenter() {
      return (this.pos_profile?.name || "").toLowerCase() === "call center";
    },

    orderTypeOptionsFiltered() {
      const base = this.orderTypes || [];
      if (!this.isCallCenter) return base;
      const allowed = new Set(["Pickup", "Delivery", "Talabat"]);
      return base.filter((x) => allowed.has((x || "").trim()));
    },
    total_outstanding_amount() {
      return this.outstanding_invoices.reduce(
        (acc, cur) => acc + flt(cur.outstanding_amount),
        0,
      );
    },
    total_unallocated_amount() {
      return this.unallocated_payments.reduce(
        (acc, cur) => acc + flt(cur.unallocated_amount),
        0,
      );
    },
    total_selected_invoices() {
      return this.selected_invoices.reduce(
        (acc, cur) => acc + flt(cur.outstanding_amount),
        0,
      );
    },
    total_selected_payments() {
      return this.selected_payments.reduce(
        (acc, cur) => acc + flt(cur.unallocated_amount),
        0,
      );
    },
    total_selected_mpesa_payments() {
      return this.selected_mpesa_payments.reduce(
        (acc, cur) => acc + flt(cur.amount),
        0,
      );
    },
    total_payment_methods() {
      return this.payment_methods.reduce(
        (acc, cur) => acc + flt(cur.amount),
        0,
      );
    },
    total_of_diff() {
      return flt(
        this.total_selected_invoices -
          this.total_selected_payments -
          this.total_selected_mpesa_payments -
          this.total_payment_methods,
      );
    },
    customers() {
      // Extract unique customer names from outstanding_invoices
      const names = this.outstanding_invoices.map((inv) => inv.customer_name);
      return [...new Set(names)]; // remove duplicates
    },
    orderIds() {
      const ids = this.outstanding_invoices.map(
        (inv) => inv.custom_number_order,
      );
      return [...new Set(ids)]; // unique order IDs
    },

    filteredInvoices() {
      return this.outstanding_invoices.filter((inv) => {
        const f = this.filters;

        // Order ID (text search)
        const orderMatch = f.custom_number_order
          ? inv.custom_number_order?.toString().includes(f.custom_number_order)
          : true;

        // Order Type (dropdown exact match)
        const typeMatch = f.custom_so_type
          ? inv.custom_so_type === f.custom_so_type
          : true;

        // Payment Type (dropdown exact match)
        const payMatch = f.custom_payment_type
          ? inv.custom_payment_type === f.custom_payment_type
          : true;

        // Customer (dropdown exact match)
        const customerMatch = f.customer_name
          ? inv.customer_name === f.customer_name
          : true;

        // Posting Date (date exact match)
        const dateMatch = f.posting_date
          ? inv.posting_date === f.posting_date
          : true;

        // Due Date (date exact match)
        const dueDateMatch = f.due_date ? inv.due_date === f.due_date : true;

        // Grand Total (numeric range)
        const totalMinMatch = f.grand_total_min
          ? inv.grand_total >= f.grand_total_min
          : true;

        const totalMaxMatch = f.grand_total_max
          ? inv.grand_total <= f.grand_total_max
          : true;

        // Outstanding Amount (numeric range if you want)
        const outstandingMinMatch = f.outstanding_amount_min
          ? inv.outstanding_amount >= f.outstanding_amount_min
          : true;

        const outstandingMaxMatch = f.outstanding_amount_max
          ? inv.outstanding_amount <= f.outstanding_amount_max
          : true;

        // ✅ Return true only if all filters match
        return (
          orderMatch &&
          typeMatch &&
          payMatch &&
          customerMatch &&
          dateMatch &&
          dueDateMatch &&
          totalMinMatch &&
          totalMaxMatch &&
          outstandingMinMatch &&
          outstandingMaxMatch
        );
      });
    },
  },

  mounted: function () {
    this.$nextTick(function () {
      this.check_opening_entry();
      evntBus.$on("update_customer", (customer_name) => {
        this.clear_all(true);
        this.customer_name = customer_name;
        this.fetch_customer_details();
        this.get_outstanding_invoices();
        this.get_unallocated_payments();
        this.get_draft_mpesa_payments_register();
      });

      evntBus.$on("update_driver", (customer_name) => {
        this.clear_all(true);
        this.customer_name = customer_name;
        // this.fetch_driver_details();
        this.get_outstanding_invoices_driver();
        // this.get_unallocated_payments();
        // this.get_draft_mpesa_payments_register();
      });

      evntBus.$on("fetch_customer_details", () => {
        this.fetch_customer_details();
      });
      frappe.realtime.on("sales_order_created", this.refreshPayment);
      frappe.realtime.on("sales_order_updated", this.refreshPayment);
      // evntBus.$on("fetch_driver_details", () => {
      //   this.fetch_driver_details();
      // });
    });
  },
  beforeDestroy() {
    evntBus.$off("update_customer");
    evntBus.$off("update_driver");
    evntBus.$off("fetch_customer_details");
    // evntBus.$off("fetch_driver_details");
  },
  watch: {
    isCallCenter(newVal) {
      if (newVal && this.filters.custom_so_type) {
        const allowed = new Set(["Pickup", "Delivery", "Talabat"]);
        if (!allowed.has((this.filters.custom_so_type || "").toLowerCase())) {
          this.filters.custom_so_type = null;
        }
      }
    },
  },
};
</script>

<style>
input[total_of_diff] {
  text-align: right;
}

input[payments_methods] {
  text-align: right;
}

input[total_selected_payments] {
  text-align: right;
}

input[total_selected_invoices] {
  text-align: right;
}

input[total_selected_mpesa_payments] {
  text-align: right;
}
</style>
