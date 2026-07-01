<template>
  <div>
    <v-dialog
      v-model="create_dialog_complaint"
      max-width="700"
      v-show="!isBundle"
    >
      <v-card>
        <v-card-title class="text-h5">
          <span class="headline main_color">{{
            __("Create Complaint ?")
          }}</span>
        </v-card-title>
        <v-container>
          <v-row>
            <v-col cols="6">
              <v-select
                dense
                hide-details
                solo
                color="#E71D36"
                background-color="white"
                :items="complaintFiltered"
                :label="__('Type')"
                v-model="complaintType"
              ></v-select>
            </v-col>
            <v-col cols="6">
              <v-select
                dense
                hide-details
                solo
                color="#E71D36"
                background-color="white"
                :items="needActionsFiltered"
                :label="__('Action Required')"
                v-model="need_action"
              ></v-select>
            </v-col>
          </v-row>

          <v-textarea
            :label="__('Complaint Details')"
            v-model="complaint"
            outlined
          ></v-textarea>
        </v-container>
        <v-card-actions>
          <v-btn color="warning" @click="create_dialog_complaint = false">
            {{ __("Cancel") }}
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn color="success" @click="create_complaint">
            {{ __("Create") }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog v-model="information_dialog" max-width="500" v-show="!isBundle">
      <v-card>
        <v-card-title class="text-h5">
          <span
            class="headline main_color"
            v-if="customer_info.black_list == 1"
            >{{ __("This Customer is in Black List") }}</span
          >
          <span class="headline main_color" v-if="customer_info.vip == 1">{{
            __("This Customer is VIP")
          }}</span>
        </v-card-title>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="warning" @click="information_dialog = false">
            {{ __("Ok") }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog v-model="cancel_dialog" max-width="330" v-show="!isBundle">
      <v-card>
        <v-card-title class="text-h5">
          <span class="headline main_color">{{
            __("Cancel Current Invoice ?")
          }}</span>
        </v-card-title>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="cancel_invoice">
            {{ __("Cancel") }}
          </v-btn>
          <v-btn color="warning" @click="cancel_dialog = false">
            {{ __("Back") }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-card class="order-panel cards my-0 py-0 mt-3" v-show="!isBundle">
      <v-dialog v-model="show_password_dialog" max-width="400px">
        <v-card>
          <v-card-title class="headline">{{
            __("Enter Authorization Password")
          }}</v-card-title>
          <v-card-text>
            <v-text-field
              v-model="password_input"
              :label="__('Password')"
              type="password"
              dense
              outlined
            ></v-text-field>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn text color="error" @click="cancelPasswordDialog">{{
              __("Cancel")
            }}</v-btn>
            <v-btn text color="primary" @click="validatePassword">{{
              __("OK")
            }}</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <v-dialog
        v-model="customerDialog"
        max-width="600px"
        persistent
        content-class="custom-dialog rounded-lg"
      >
        <v-card class="p-4" style="background-color: white !important">
          <v-card-title class="text-center py-2">
            <h6
              class="headline main_color font-weight-black w-100"
              style="text-transform: uppercase"
            >
              {{ __("Customer Details") }}
            </h6>
          </v-card-title>
          <v-container>
            <v-row align="center" class="items py-1">
              <v-col
                v-if="pos_profile.posa_allow_sales_order"
                cols="12"
                class="p-0"
              >
                <Customer></Customer>
              </v-col>
              <v-col
                v-if="!pos_profile.posa_allow_sales_order"
                cols="12"
                class="pt-0 px-0 pb-4"
              >
                <Customer></Customer>
              </v-col>
              <v-col
                v-if="!pos_profile.posa_allow_sales_order"
                cols="6"
                class="pt-0 px-0 pb-4"
              >
                <VisitDate></VisitDate>
              </v-col>
              <v-col
                v-if="!pos_profile.posa_allow_sales_order"
                cols="6"
                class="pt-0 px-0 pb-4"
              >
                <SalesOrder></SalesOrder>
              </v-col>
              <v-col
                v-if="pos_profile.posa_allow_sales_order"
                cols="3"
                class="pt-0 px-0 pb-4"
              >
                <v-select
                  v-if="1 == 0"
                  dense
                  hide-details
                  outlined
                  color="#E91E63"
                  background-color="white"
                  :items="invoiceTypes"
                  :label="__('Type')"
                  v-model="invoiceType"
                  :disabled="invoiceType == 'Return'"
                  hidden
                ></v-select>
              </v-col>
            </v-row>
            <v-row align="center" class="items py-1 mt-0 pt-0">
              <v-col cols="12" class="pt-0 px-0 pb-4">
                <v-select
                  dense
                  hide-details
                  solo
                  color="#E71D36"
                  background-color="white"
                  :items="orderTypeOptionsFiltered"
                  :label="__('Order Type')"
                  v-model="orderType"
                  class="p-0"
                ></v-select>
              </v-col>
              <v-col cols="12" class="pt-0 px-0 pb-4">
                <v-autocomplete
                  v-if="orderType == 'Dinin'"
                  multiple
                  chips
                  dense
                  clearable
                  auto-select-first
                  solo
                  color="black"
                  :label="__('Table No')"
                  v-model="table_no"
                  :items="table_numbers"
                  item-text="name"
                  item-value="name"
                  background-color="white"
                  :no-data-text="__('All Tables Are Busy')"
                  hide-details
                  :filter="table_noFilter"
                >
                  <template v-slot:item="data">
                    <template>
                      <v-list-item-content>
                        <v-list-item-title
                          class="text-black subtitle-1"
                          v-html="data.item.no"
                        ></v-list-item-title>
                      </v-list-item-content>
                    </template>
                  </template>
                </v-autocomplete>
                <v-autocomplete
                  v-if="orderType == 'Delivery'"
                  dense
                  clearable
                  auto-select-first
                  solo
                  color="#E71D36"
                  :label="__('Address')"
                  v-model="shipping_address_name"
                  :items="addresses"
                  item-text="address_title"
                  item-value="name"
                  background-color="white"
                  :no-data-text="__('Address not found')"
                  hide-details
                  :filter="addressFilter"
                  append-icon="mdi-plus"
                  @click:append="new_address"
                >
                  <template v-slot:item="data">
                    <template>
                      <v-list-item-content>
                        <v-list-item-title
                          class="subtitle-1"
                          v-html="data.item.address_title"
                        ></v-list-item-title>
                        <v-list-item-title
                          class="subtitle-1"
                          v-html="data.item.address_line1"
                        ></v-list-item-title>
                        <v-list-item-subtitle
                          class="subtitle-1"
                          v-if="data.item.address_line2"
                          v-html="data.item.address_line2"
                        ></v-list-item-subtitle>
                        <v-list-item-subtitle
                          class="subtitle-1"
                          v-if="data.item.city"
                          v-html="data.item.city"
                        ></v-list-item-subtitle>
                        <v-list-item-subtitle
                          class="subtitle-1"
                          v-if="data.item.state"
                          v-html="data.item.state"
                        ></v-list-item-subtitle>
                        <v-list-item-subtitle
                          class="subtitle-1"
                          v-if="data.item.country"
                          v-html="data.item.mobile_no"
                        ></v-list-item-subtitle>
                        <v-list-item-subtitle
                          class="subtitle-1"
                          v-if="data.item.address_type"
                          v-html="data.item.address_type"
                        ></v-list-item-subtitle>
                        <v-list-item-subtitle
                          class="subtitle-1"
                          v-if="data.item.territory"
                          v-html="data.item.territory"
                        ></v-list-item-subtitle>
                      </v-list-item-content>
                    </template>
                  </template>
                </v-autocomplete>
              </v-col>
            </v-row>
            <v-row
              align="center"
              class="items py-1 mt-0 pt-0"
              v-if="pos_profile.posa_use_delivery_charges"
            >
              <v-col
                cols="8"
                class="pt-0 px-0 pb-4"
                v-if="orderType == 'False'"
              >
                <v-autocomplete
                  dense
                  clearable
                  auto-select-first
                  solo
                  color="#E71D36"
                  :label="__('Delivery Charges')"
                  v-model="selcted_delivery_charges"
                  :items="delivery_charges"
                  item-text="name"
                  return-object
                  background-color="white"
                  :no-data-text="__('Charges not found')"
                  hide-details
                  :filter="deliveryChargesFilter"
                  :disabled="readonly"
                  @change="update_delivery_charges()"
                >
                  <template v-slot:item="data">
                    <template>
                      <v-list-item-content>
                        <v-list-item-title
                          class="main_color subtitle-1"
                          v-html="data.item.name"
                        ></v-list-item-title>
                        <v-list-item-subtitle
                          v-html="`Rate: ${data.item.rate}`"
                        ></v-list-item-subtitle>
                      </v-list-item-content>
                    </template>
                  </template>
                </v-autocomplete>
              </v-col>
              <v-col
                cols="4"
                class="pt-0 px-0 pb-4"
                v-if="orderType == 'Delivery'"
              >
                <v-text-field
                  dense
                  solo
                  color="#E71D36"
                  :label="__('Territory')"
                  background-color="white"
                  hide-details
                  :value="shipping_address_territory"
                  disabled
                ></v-text-field>
              </v-col>
              <v-col
                cols="4"
                class="pt-0 px-0 pb-4"
                v-if="orderType == 'Delivery'"
              >
                <v-text-field
                  dense
                  solo
                  color="#E71D36"
                  :label="__('Delivery Charges Rate')"
                  background-color="white"
                  hide-details
                  :value="formtCurrency(delivery_charges_rate)"
                  :prefix="currencySymbol(pos_profile.currency)"
                  disabled
                ></v-text-field>
              </v-col>
            </v-row>
            <v-row align="center" class="items py-1 mt-0 pt-0">
              <v-col cols="12" class="px-0 py-4">
                <v-autocomplete
                  dense
                  clearable
                  auto-select-first
                  solo
                  color="#E71D36"
                  :label="__('Branch')"
                  v-model="branch"
                  :items="branches"
                  item-text="name"
                  item-value="name"
                  background-color="white"
                  :no-data-text="__('Branch not found')"
                  hide-details
                >
                  <template v-slot:item="data">
                    <template>
                      <v-list-item-content>
                        <v-list-item-title
                          class="text-black subtitle-1"
                          v-html="data.item.name"
                        ></v-list-item-title>
                      </v-list-item-content>
                    </template>
                  </template>
                </v-autocomplete>
              </v-col>
            </v-row>
          </v-container>
          <v-card-actions class="p-0">
            <v-btn
              color="#000"
              style="padding: 0 30px !important"
              dark
              @click="close_customer"
              >{{ __("Close") }}</v-btn
            >
            <v-spacer></v-spacer>
            <v-btn
              color="#E71D36"
              style="padding: 0 30px !important"
              dark
              @click="close_dialog"
              >{{ __("Save") }}</v-btn
            >
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-row
        align="center"
        class="items px-2 py-1 mt-0 pt-0"
        v-if="pos_profile.posa_allow_change_posting_date"
      >
        <v-col
          v-if="pos_profile.posa_allow_change_posting_date"
          cols="4"
          class="pb-2"
        >
          <v-menu
            ref="invoice_posting_date"
            v-model="invoice_posting_date"
            :close-on-content-click="false"
            transition="scale-transition"
            dense
          >
            <template v-slot:activator="{ on, attrs }">
              <v-text-field
                v-model="posting_date"
                :label="__('Posting Date')"
                readonly
                outlined
                dense
                background-color="white"
                clearable
                color="#E91E63"
                hide-details
                v-bind="attrs"
                v-on="on"
              ></v-text-field>
            </template>
            <v-date-picker
              v-model="posting_date"
              no-title
              scrollable
              color="#E91E63"
              @input="invoice_posting_date = false"
            >
            </v-date-picker>
          </v-menu>
        </v-col>
      </v-row>

      <div class="my-0 py-0 overflow-y-auto" style="max-height: 50vh">
        <template @mouseover="style = 'cursor: pointer'">
          <v-data-table
            :headers="items_headers"
            :items="items"
            :single-expand="singleExpand"
            :expanded.sync="expanded"
            show-expand
            item-key="posa_row_id"
            class="elevation-1"
            :items-per-page="itemsPerPage"
            hide-default-footer
          >
            <template v-slot:item.qty="{ item }"
              >{{ formtFloat(item.qty, 0) }}
            </template>
            <template v-slot:item.rate="{ item }"
              >{{ currencySymbol(pos_profile.currency) }}
              {{ formtCurrency(item.rate) }}
            </template>
            <template v-slot:item.amount="{ item }"
              >{{ currencySymbol(pos_profile.currency) }}
              {{
                formtCurrency(
                  flt(item.qty, float_precision) *
                    flt(item.rate, currency_precision),
                )
              }}
            </template>
            <template v-slot:item.posa_is_offer="{ item }">
              <v-simple-checkbox
                :value="!!item.posa_is_offer || !!item.posa_is_replace"
                disabled
              ></v-simple-checkbox>
            </template>

            <template v-slot:expanded-item="{ headers, item }">
              <td :colspan="headers.length" class="ma-0 pa-0">
                <v-row class="ma-0 pa-0">
                  <v-col cols="1">
                    <v-btn
                      :disabled="!!item.posa_is_offer || !!item.posa_is_replace"
                      icon
                      color="error"
                      @click.stop="remove_item(item)"
                    >
                      <v-icon>mdi-delete</v-icon>
                    </v-btn>
                  </v-col>
                  <v-col cols="1">
                    <v-btn
                      :disabled="!!item.posa_is_offer || !!item.posa_is_replace"
                      icon
                      color="#E91E63"
                      @click.stop="subtract_one(item)"
                    >
                      <v-icon>mdi-minus-circle-outline</v-icon>
                    </v-btn>
                  </v-col>
                  <v-col cols="1">
                    <v-btn
                      :disabled="!!item.posa_is_offer || !!item.posa_is_replace"
                      icon
                      color="#E91E63"
                      @click.stop="add_one(item)"
                    >
                      <v-icon>mdi-plus-circle-outline</v-icon>
                    </v-btn>
                  </v-col>
                </v-row>
                <v-row class="ma-0 pa-0">
                  <!-- <v-col cols="4">
                    <v-text-field
                      dense
                      outlined
                      color="#E91E63"
                      :label="__('Item Code')"
                      background-color="white"
                      hide-details
                      v-model="item.item_code"
                      disabled
                    ></v-text-field>
                  </v-col> -->
                  <v-col cols="6">
                    <v-text-field
                      dense
                      outlined
                      color="#E91E63"
                      :label="__('QTY')"
                      background-color="white"
                      hide-details
                      :value="formtFloat(item.qty, 0)"
                      @change="[
                        setFormatedFloat(
                          item,
                          'qty',
                          null,
                          false,
                          false,
                          $event,
                        ),
                        calc_stock_qty(item, $event),
                      ]"
                      :rules="[isNumber]"
                      :disabled="!!item.posa_is_offer || !!item.posa_is_replace"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="6">
                    <v-select
                      dense
                      background-color="white"
                      :label="__('UOM')"
                      v-model="item.uom"
                      :items="item.item_uoms"
                      outlined
                      item-text="uom"
                      item-value="uom"
                      hide-details
                      @change="calc_uom(item, $event)"
                      :disabled="
                        !!invoice_doc.is_return ||
                        !!item.posa_is_offer ||
                        !!item.posa_is_replace
                      "
                    >
                    </v-select>
                  </v-col>
                  <!-- <v-col cols="4">
                    <v-text-field
                      dense
                      outlined
                      color="#E91E63"
                      :label="__('Rate')"
                      background-color="white"
                      hide-details
                      :prefix="currencySymbol(pos_profile.currency)"
                      :value="formtCurrency(item.rate)"
                      @change="
                        [
                          setFormatedCurrency(
                            item,
                            'rate',
                            null,
                            false,
                            $event
                          ),
                          calc_prices(item, $event),
                        ]
                      "
                      :rules="[isNumber]"
                      id="rate"
                      :disabled="
                        !!item.posa_is_offer ||
                        !!item.posa_is_replace ||
                        !!item.posa_offer_applied ||
                        !pos_profile.posa_allow_user_to_edit_rate ||
                        !!invoice_doc.is_return
                          ? true
                          : false
                      "
                    ></v-text-field>
                  </v-col> -->
                  <v-col cols="6">
                    <v-text-field
                      dense
                      outlined
                      color="#E91E63"
                      @focus="triggerPasswordDialog"
                      :label="__('Discount Percentage')"
                      background-color="white"
                      hide-details
                      :value="formtFloat(item.discount_percentage, 0)"
                      @change="[
                        setFormatedCurrency(
                          item,
                          'discount_percentage',
                          null,
                          true,
                          $event,
                        ),
                        calc_prices(item, $event),
                      ]"
                      :rules="[isNumber]"
                      id="discount_percentage"
                      :disabled="
                        !!item.posa_is_offer ||
                        !!item.posa_is_replace ||
                        item.posa_offer_applied ||
                        !pos_profile.posa_allow_user_to_edit_item_discount ||
                        !!invoice_doc.is_return
                          ? true
                          : false
                      "
                      suffix="%"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="6">
                    <v-text-field
                      dense
                      outlined
                      @focus="triggerPasswordDialog"
                      color="#E91E63"
                      :label="__('Discount Amount')"
                      background-color="white"
                      hide-details
                      :value="formtCurrency(item.discount_amount)"
                      :rules="[isNumber]"
                      @change="[
                        setFormatedCurrency(
                          item,
                          'discount_amount',
                          null,
                          true,
                          $event,
                        ),
                        ,
                        calc_prices(item, $event),
                      ]"
                      :prefix="currencySymbol(pos_profile.currency)"
                      id="discount_amount"
                      :disabled="
                        !!item.posa_is_offer ||
                        !!item.posa_is_replace ||
                        !!item.posa_offer_applied ||
                        !pos_profile.posa_allow_user_to_edit_item_discount ||
                        !!invoice_doc.is_return
                          ? true
                          : false
                      "
                    ></v-text-field>
                  </v-col>
                  <!-- <v-col cols="4">
                    <v-text-field
                      dense
                      outlined
                      color="#E91E63"
                      :label="__('Price list Rate')"
                      background-color="white"
                      hide-details
                      :value="formtCurrency(item.price_list_rate)"
                      disabled
                      :prefix="currencySymbol(pos_profile.currency)"
                    ></v-text-field>
                  </v-col> -->
                  <v-col cols="6">
                    <v-text-field
                      dense
                      outlined
                      color="#E91E63"
                      :label="__('Available QTY')"
                      background-color="white"
                      hide-details
                      :value="formtFloat(item.actual_qty, 0)"
                      disabled
                    ></v-text-field>
                  </v-col>
                  <!-- <v-col cols="4">
                    <v-text-field
                      dense
                      outlined
                      color="#E91E63"
                      :label="__('Group')"
                      background-color="white"
                      hide-details
                      v-model="item.item_group"
                      disabled
                    ></v-text-field>
                  </v-col>
                  <v-col cols="4">
                    <v-text-field
                      dense
                      outlined
                      color="#E91E63"
                      :label="__('Stock QTY')"
                      background-color="white"
                      hide-details
                      :value="formtFloat(item.stock_qty, 0)"
                      disabled
                    ></v-text-field>
                  </v-col>
                  <v-col cols="4">
                    <v-text-field
                      dense
                      outlined
                      color="#E91E63"
                      :label="__('Stock UOM')"
                      background-color="white"
                      hide-details
                      v-model="item.stock_uom"
                      disabled
                    ></v-text-field>
                  </v-col> 
                  <v-col align="center" cols="4" v-if="item.posa_offer_applied">
                    <v-checkbox
                      dense
                      :label="__('Offer Applied')"
                      v-model="item.posa_offer_applied"
                      readonly
                      hide-details
                      class="shrink mr-2 mt-0"
                    ></v-checkbox>
                  </v-col>
                  <v-col
                    cols="4"
                    v-if="item.has_serial_no == 1 || item.serial_no"
                  >
                    <v-text-field
                      dense
                      outlined
                      color="#E91E63"
                      :label="__('Serial No QTY')"
                      background-color="white"
                      hide-details
                      v-model="item.serial_no_selected_count"
                      type="number"
                      disabled
                    ></v-text-field>
                  </v-col> 
                  <v-col
                    cols="12"
                    v-if="item.has_serial_no == 1 || item.serial_no"
                  >
                    <v-autocomplete
                      v-model="item.serial_no_selected"
                      :items="item.serial_no_data"
                      item-text="serial_no"
                      outlined
                      dense
                      chips
                      color="#E91E63"
                      small-chips
                      :label="__('Serial No')"
                      multiple
                      @change="set_serial_no(item)"
                    ></v-autocomplete>
                  </v-col> 
                  <v-col
                    cols="4"
                    v-if="item.has_batch_no == 1 || item.batch_no"
                  >
                    <v-text-field
                      dense
                      outlined
                      color="#E91E63"
                      :label="__('Batch No. Available QTY')"
                      background-color="white"
                      hide-details
                      :value="formtFloat(item.actual_batch_qty, 0)"
                      disabled
                    ></v-text-field>
                  </v-col>
                  <v-col
                    cols="4"
                    v-if="item.has_batch_no == 1 || item.batch_no"
                  >
                    <v-text-field
                      dense
                      outlined
                      color="#E91E63"
                      :label="__('Batch No Expiry Date')"
                      background-color="white"
                      hide-details
                      v-model="item.batch_no_expiry_date"
                      disabled
                    ></v-text-field>
                  </v-col> 
                  <v-col
                    cols="8"
                    v-if="item.has_batch_no == 1 || item.batch_no"
                  >
                    <v-autocomplete
                      v-model="item.batch_no"
                      :items="item.batch_no_data"
                      item-text="batch_no"
                      outlined
                      dense
                      color="#E91E63"
                      :label="__('Batch No')"
                      @change="set_batch_qty(item, $event)"
                    >
                      <template v-slot:item="data">
                        <template>
                          <v-list-item-content>
                            <v-list-item-title
                              v-html="data.item.batch_no"
                            ></v-list-item-title>
                            <v-list-item-subtitle
                              v-html="
                                `Available QTY  '${data.item.batch_qty}' - Expiry Date ${data.item.expiry_date}`
                              "
                            ></v-list-item-subtitle>
                          </v-list-item-content>
                        </template>
  </template>
  </v-autocomplete>
  </v-col> -->
                  <v-col
                    cols="6"
                    v-if="
                      pos_profile.posa_allow_sales_order &&
                      invoiceType == 'Order'
                    "
                  >
                    <v-menu
                      ref="item_delivery_date"
                      v-model="item.item_delivery_date"
                      :close-on-content-click="false"
                      :return-value.sync="item.posa_delivery_date"
                      transition="scale-transition"
                      dense
                    >
                      <template v-slot:activator="{ on, attrs }">
                        <v-text-field
                          v-model="item.posa_delivery_date"
                          :label="__('Delivery Date')"
                          readonly
                          outlined
                          dense
                          clearable
                          color="#E91E63"
                          hide-details
                          v-bind="attrs"
                          v-on="on"
                        ></v-text-field>
                      </template>
                      <v-date-picker
                        v-model="item.posa_delivery_date"
                        no-title
                        scrollable
                        color="#E91E63"
                        :min="frappe.datetime.now_date()"
                      >
                        <v-spacer></v-spacer>
                        <v-btn
                          text
                          color="#E91E63"
                          @click="item.item_delivery_date = false"
                        >
                          {{ __("Cancel") }}
                        </v-btn>
                        <v-btn
                          text
                          color="#E91E63"
                          @click="[
                            $refs.item_delivery_date.save(
                              item.posa_delivery_date,
                            ),
                            validate_due_date(item),
                          ]"
                        >
                          {{ __("OK") }}
                        </v-btn>
                      </v-date-picker>
                    </v-menu>
                  </v-col>
                  <v-col
                    cols="12"
                    v-if="pos_profile.posa_display_additional_notes"
                  >
                    <v-textarea
                      class="pa-0"
                      outlined
                      dense
                      clearable
                      color="#E91E63"
                      auto-grow
                      rows="5"
                      :label="__('Additional Notes')"
                      v-model="item.posa_notes"
                      :value="item.posa_notes"
                    ></v-textarea>
                  </v-col>
                </v-row>
              </td>
            </template>
          </v-data-table>
        </template>
      </div>
    </v-card>
    <v-card class="cards mb-0 mt-3 m-1 grey lighten-5" v-show="!isBundle">
      <v-row class="pa-1 m-1 pr-1">
        <v-col cols="12" class="">
          <v-row>
            <v-col cols="6" class="">
              <v-text-field
                :value="formtFloat(total_qty, 0)"
                :label="__('Total Qty')"
                outlined
                dense
                readonly
                hide-details
                color="accent"
              ></v-text-field>
            </v-col>
            <v-col
              v-if="!pos_profile.posa_use_percentage_discount"
              cols="6"
              class=""
            >
              <v-text-field
                :value="formtCurrency(discount_amount)"
                @change="
                  setFormatedCurrency(
                    discount_amount,
                    'discount_amount',
                    null,
                    false,
                    $event,
                  )
                "
                @focus="triggerPasswordDialog"
                :readonly="!discount_edit_enabled"
                :rules="[isNumber]"
                :label="__('Additional Discount')"
                ref="discount"
                outlined
                dense
                hide-details
                color="warning"
                :prefix="currencySymbol(pos_profile.currency)"
                :disabled="
                  !pos_profile.posa_allow_user_to_edit_additional_discount ||
                  discount_percentage_offer_name
                "
              ></v-text-field>
            </v-col>
            <v-col
              v-if="pos_profile.posa_use_percentage_discount"
              cols="6"
              class=""
            >
              <v-text-field
                :value="formtFloat(additional_discount_percentage, 2, true)"
                @change="[
                  setFormatedFloat(
                    additional_discount_percentage,
                    'additional_discount_percentage',
                    null,
                    false,
                    false,
                    $event,
                  ),
                  update_discount_umount(),
                ]"
                :rules="[isNumber]"
                :label="__('Additional Discount %')"
                @focus="triggerPasswordDialog"
                :readonly="!discount_edit_enabled"
                suffix="%"
                ref="percentage_discount"
                outlined
                dense
                color="warning"
                hide-details
                :disabled="
                  !pos_profile.posa_allow_user_to_edit_additional_discount ||
                  discount_percentage_offer_name
                "
              ></v-text-field>
            </v-col>
            <v-col
              v-if="pos_profile.posa_use_percentage_discount"
              cols="6"
              class=""
            >
              <v-text-field
                :value="setFormatedCurrency(discount_amount, 0)"
                @change="[
                  setFormatedCurrency(
                    discount_amount,
                    'discount_amount',
                    null,
                    false,
                    $event,
                  ),
                  // update_discount_umount(),
                ]"
                @focus="triggerPasswordDialog"
                :readonly="!discount_edit_enabled"
                :rules="[isNumber]"
                :label="__('Discount Amount')"
                suffix="EGP"
                ref="discount_amount"
                outlined
                dense
                color="warning"
                hide-details
                :disabled="
                  !pos_profile.posa_allow_user_to_edit_additional_discount ||
                  discount_percentage_offer_name
                    ? true
                    : false
                "
              ></v-text-field>
            </v-col>
            <v-col cols="6" class="mt-2">
              <v-text-field
                :value="formtCurrency(total_items_discount_amount)"
                :prefix="currencySymbol(pos_profile.currency)"
                :label="__('Items Discounts')"
                outlined
                dense
                color="warning"
                readonly
                hide-details
              ></v-text-field>
            </v-col>

            <v-col cols="6" class="mt-2">
              <v-text-field
                :value="formtCurrency(subtotal)"
                :prefix="currencySymbol(pos_profile.currency)"
                :label="__('Total')"
                outlined
                dense
                readonly
                hide-details
                color="success"
              ></v-text-field>
            </v-col>
          </v-row>
        </v-col>
      </v-row>
    </v-card>
    <v-dialog
      v-model="isBundle"
      max-width="1200px"
      class="overflow-y-none"
      :persistent="isBundle == 1"
      @click:outside="clear_bundle"
    >
      <v-card class="bundle-dialog-card" v-if="isBundle">
        <div class="bundle-header">
          <v-btn icon class="bundle-header__close" @click="close_bundle_2">
            <v-icon>mdi-close</v-icon>
          </v-btn>
          <div class="bundle-header__content">
            <h3 class="bundle-title">{{ item_dialog.item_name }}</h3>
            <span class="bundle-subtitle">
              {{ __("Tailor this order without changing your flow.") }}
            </span>
          </div>
        </div>
        <v-divider></v-divider>
        <div class="bundle-body">
          <template>
            <v-row class="bundle-grid" no-gutters>
              <v-col cols="9" class="bundle-grid__left">
                <div
                  v-for="(classifiedItems, classification) in groupedItems"
                  :key="classification"
                  class="bundle-category"
                >
                  <div class="bundle-category__title">
                    <span>{{ classification }}</span>
                  </div>

                  <!-- Check if this classification has template items with nested selection -->
                  <template
                    v-if="hasTemplateItemsInClassification(classifiedItems)"
                  >
                    <!-- Nested Attribute Selection for Template Items -->
                    <div
                      class="nested-variant-selection pa-3 mb-2"
                      style="background: #f8f9fa; border-radius: 8px"
                    >
                      <div
                        v-for="attr in getClassificationAttributes(
                          classifiedItems,
                        )"
                        :key="attr.attribute"
                        class="mb-3"
                      >
                        <div class="text-subtitle-2 font-weight-medium mb-2">
                          {{ attr.attribute }}
                        </div>
                        <v-chip-group
                          v-model="
                            nestedSelections[
                              classification + '_' + attr.attribute
                            ]
                          "
                          active-class="primary white--text"
                          @change="
                            onNestedAttributeChange(
                              classification,
                              classifiedItems,
                            )
                          "
                        >
                          <v-chip
                            v-for="val in attr.values"
                            :key="val.attribute_value"
                            :value="val.attribute_value"
                            outlined
                            label
                          >
                            {{ val.attribute_value }}
                          </v-chip>
                        </v-chip-group>
                      </div>

                      <!-- Selected Variant Display -->
                      <div
                        v-if="
                          getSelectedVariantForClassification(
                            classification,
                            classifiedItems,
                          )
                        "
                        class="mt-2 pa-2 d-flex align-center justify-space-between"
                        style="background: #e8f5e9; border-radius: 4px"
                      >
                        <div>
                          <v-icon small color="success" class="mr-1"
                            >mdi-check-circle</v-icon
                          >
                          <span class="font-weight-medium">{{
                            getSelectedVariantForClassification(
                              classification,
                              classifiedItems,
                            ).item_name
                          }}</span>
                          <span class="ml-2 primary--text"
                            >{{
                              getSelectedVariantForClassification(
                                classification,
                                classifiedItems,
                              ).standard_rate
                            }}
                            {{ __("EGP") }}</span
                          >
                        </div>
                        <div class="d-flex align-center">
                          <v-btn
                            icon
                            small
                            color="primary"
                            @click="
                              decreaseNestedVariantQty(
                                classification,
                                classifiedItems,
                              )
                            "
                          >
                            <v-icon>mdi-minus</v-icon>
                          </v-btn>
                          <span class="mx-2 font-weight-bold">{{
                            getNestedVariantQty(classification)
                          }}</span>
                          <v-btn
                            icon
                            small
                            color="secondary"
                            @click="
                              increaseNestedVariantQty(
                                classification,
                                classifiedItems,
                              )
                            "
                          >
                            <v-icon>mdi-plus</v-icon>
                          </v-btn>
                        </div>
                      </div>
                    </div>
                  </template>

                  <!-- Regular Items (non-template) -->
                  <v-row v-else class="bundle-category__items" dense>
                    <v-col
                      v-for="(item, idx) in classifiedItems"
                      v-if="!item.hide"
                      :key="idx"
                      cols="4"
                      class="bundle-item-wrapper"
                    >
                      <v-card
                        hover
                        class="bundle-item-card"
                        :class="bundleItemClasses(item)"
                      >
                        <div class="bundle-item-card__info">
                          <p class="bundle-item-card__name">
                            {{ truncateProductTitle(item.item_name, 26) }}
                          </p>
                          <span class="bundle-item-card__price">
                            {{ item.rate }} {{ __("EGP") }}
                          </span>
                        </div>
                        <div class="bundle-item-card__controls">
                          <v-btn
                            icon
                            small
                            class="bundle-stepper__btn"
                            color="primary"
                            @click="decreaseQty(item)"
                            :disabled="item.qty == 0"
                          >
                            <v-icon>mdi-minus</v-icon>
                          </v-btn>
                          <div
                            v-if="
                              !['Sandwich Pieces', 'Pieces'].includes(
                                item.item_classification,
                              )
                            "
                            class="bundle-stepper__value"
                          >
                            {{ item.qty }}
                          </div>
                          <v-btn
                            icon
                            small
                            class="bundle-stepper__btn"
                            color="secondary"
                            @click="increaseQty(item)"
                            :disabled="item.dummy"
                          >
                            <v-icon>mdi-plus</v-icon>
                          </v-btn>
                        </div>
                      </v-card>
                    </v-col>
                  </v-row>
                </div>
              </v-col>
              <v-col cols="3" class="bundle-grid__right">
                <div class="bundle-summary">
                  <div class="bundle-summary__box">
                    <label class="bundle-summary__label">
                      {{ __("Quantity") }}
                    </label>
                    <v-text-field
                      class="bundle-qty-field"
                      color="primary"
                      clearable
                      hide-details
                      :value="formtFloat(item_dialog.qty, 0)"
                      @change="[
                        setFormatedFloat(
                          item_dialog,
                          'qty',
                          null,
                          false,
                          false,
                          $event,
                        ),
                        calc_stock_qty(item_dialog, $event),
                      ]"
                      :rules="[isNumber]"
                    >
                      <template v-slot:prepend>
                        <v-icon
                          class="bundle-qty-field__btn"
                          color="secondary"
                          @click.stop="add_one(item_dialog)"
                        >
                          mdi-plus
                        </v-icon>
                      </template>
                      <template v-slot:append>
                        <v-icon
                          class="bundle-qty-field__btn"
                          color="secondary"
                          @click.stop="subtract_one(item_dialog)"
                        >
                          mdi-minus
                        </v-icon>
                      </template>
                    </v-text-field>
                  </div>
                  <div class="bundle-summary__box">
                    <label class="bundle-summary__label">
                      {{ __("Additional Notes") }}
                    </label>
                    <v-textarea
                      auto-grow
                      class="bundle-notes"
                      color="primary"
                      v-model="item_dialog.posa_notes"
                      :value="item_dialog.posa_notes"
                      row="4"
                    ></v-textarea>
                  </div>
                </div>
              </v-col>
            </v-row>
          </template>
          <template>
            <div v-if="showAlert" class="bundle-alert">
              {{
                __("You can select exactly {0} scoops and 1 Cup", [
                  number_of_scoops,
                ])
              }}
            </div>
            <div v-if="select_customer" class="bundle-alert">
              {{ __("Please Select Customer first") }}
            </div>
          </template>
        </div>
        <v-divider></v-divider>
        <v-card-actions class="bundle-actions">
          <v-btn
            class="bundle-action bundle-action--ghost"
            text
            @click="close_bundle_2"
          >
            {{ __("Close") }}
          </v-btn>
          <v-btn
            class="bundle-action bundle-action--primary"
            color="primary"
            dark
            @click="clear_bundle"
          >
            {{ __("Submit") }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-card v-if="customer" class="customer-panel mt-3" v-show="!isBundle">
      <div class="customer-panel__actions">
        <v-btn
          small
          text
          color="secondary"
          class="customer-panel__edit"
          @click="customerDialog = true"
        >
          <v-icon left small>mdi-account-edit</v-icon>
          {{ __("Edit") }}
        </v-btn>
      </div>
      <div class="customer-panel__header">
        <div class="customer-panel__avatar">
          {{ customerInitials }}
        </div>
        <div class="customer-panel__identity">
          <div class="customer-panel__name">
            {{ customer_info.customer_name }}
          </div>
          <div class="customer-panel__meta">
            <v-icon small color="secondary" class="mr-1">mdi-cellphone</v-icon>
            <span>{{ customer_info.mobile_no || __("Not provided") }}</span>
          </div>
          <div
            v-if="customer_info.custom_other_mobile_no"
            class="customer-panel__meta"
          >
            <v-icon small color="secondary" class="mr-1">mdi-phone</v-icon>
            <span>{{ customer_info.custom_other_mobile_no }}</span>
          </div>
        </div>
      </div>
      <div
        class="customer-panel__tags"
        v-if="
          branch ||
          customer_info.custom_last_branch ||
          customer_info.custom_favorite_branch
        "
      >
        <v-chip
          v-if="branch"
          class="customer-tag"
          small
          color="secondary"
          text-color="white"
          label
        >
          {{ branch }}
        </v-chip>
        <v-chip
          v-if="customer_info.custom_last_branch"
          class="customer-tag"
          outlined
          small
        >
          {{ __("Last Visit: {0}", [customer_info.custom_last_branch]) }}
        </v-chip>
        <v-chip
          v-if="customer_info.custom_favorite_branch"
          class="customer-tag"
          outlined
          small
        >
          {{ __("Fav Branch: {0}", [customer_info.custom_favorite_branch]) }}
        </v-chip>
      </div>
      <div class="customer-panel__stats">
        <div class="customer-stat">
          <span class="customer-stat__label">{{ __("Previous Orders") }}</span>
          <span class="customer-stat__value">{{
            customer_info.previous_orders || 0
          }}</span>
        </div>
        <div
          class="customer-stat customer-stat--interactive"
          @click="showCustomerComplaint"
        >
          <span class="customer-stat__label">{{ __("Complaints") }}</span>
          <span class="customer-stat__value">{{
            customer_info.no_compliant || 0
          }}</span>
        </div>
        <div class="customer-stat" v-if="customer_info.custom_favorite_item">
          <span class="customer-stat__label">{{ __("Fav Item") }}</span>
          <span class="customer-stat__value">{{
            customer_info.custom_favorite_item
          }}</span>
        </div>
        <div class="customer-stat" v-if="delivery_charges_rate">
          <span class="customer-stat__label">{{ __("Charge Rate") }}</span>
          <span class="customer-stat__value">{{ delivery_charges_rate }}</span>
        </div>
      </div>
      <div class="customer-panel__toggles">
        <div class="customer-toggle">
          <div>
            <span class="customer-toggle__label">{{ __("VIP") }}</span>
            <span class="customer-toggle__hint">{{
              __("Priority customer")
            }}</span>
          </div>
          <v-switch
            inset
            dense
            color="secondary"
            v-model="customer_info.vip"
            @change="updateVip"
          ></v-switch>
        </div>
        <div class="customer-toggle">
          <div>
            <span class="customer-toggle__label">{{ __("Blacklist") }}</span>
            <span class="customer-toggle__hint">{{
              __("Restrict access if needed")
            }}</span>
          </div>
          <v-switch
            inset
            dense
            color="error"
            v-model="customer_info.black_list"
            @change="updateBlackList"
          ></v-switch>
        </div>
      </div>
      <div class="customer-panel__address" v-if="shipping_address_name">
        <div class="customer-panel__address-label">
          {{ __("Address") }}
        </div>
        <p class="customer-panel__address-text">
          {{ shipping_address_name_line }}
        </p>
      </div>
      <div class="customer-panel__address" v-if="shipping_address_territory">
        <div class="customer-panel__address-label">
          {{ __("Territory") }}
        </div>
        <p class="customer-panel__address-text">
          {{ shipping_address_territory }}
        </p>
      </div>
      <div class="customer-panel__actions customer-panel__actions--bottom">
        <v-btn
          outlined
          small
          color="secondary"
          class="customer-panel__complaints"
          @click="showCustomerComplaint"
        >
          <v-icon left small>mdi-message-alert-outline</v-icon>
          {{ __("View Complaints") }}
        </v-btn>
      </div>
      <div
        class="modal fade"
        id="complaintModal"
        tabindex="-1"
        role="dialog"
        aria-labelledby="complaintModalLabel"
        aria-hidden="true"
      >
        <div class="modal-dialog modal-lg" role="document">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="complaintModalLabel">
                {{ __("Customer Complaints") }}
              </h5>
              <button
                type="button"
                class="close"
                data-dismiss="modal"
                aria-label="Close"
              >
                <span aria-hidden="true">&times;</span>
              </button>
            </div>
            <div class="modal-body">
              <div
                v-for="comp in complaints"
                :key="comp.name"
                class="mb-3 pb-2 border-bottom"
              >
                <p>
                  <strong>{{ __("Customer") }}:</strong>
                  {{ comp.customer_name }}
                </p>
                <p>
                  <strong>{{ __("Date") }}:</strong> {{ comp.complaint_date }}
                </p>
                <p>
                  <strong>{{ __("Status") }}:</strong> {{ comp.status }}
                </p>
                <p>
                  <strong>{{ __("Type") }}:</strong> {{ comp.type }}
                </p>
                <p>
                  <strong>{{ __("Action Required") }}:</strong>
                  {{ comp.need_action }}
                </p>
                <p>
                  <strong>{{ __("Branch") }}:</strong> {{ comp.branch }}
                </p>
                <p>
                  <strong>{{ __("Details") }}:</strong>
                </p>
                <p>{{ comp.complaint_details || __("No details provided") }}</p>
              </div>
            </div>
            <div class="modal-footer">
              <button
                type="button"
                class="btn btn-secondary"
                data-dismiss="modal"
              >
                {{ __("Close") }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </v-card>
  </div>
</template>

<script>
import { evntBus } from "../../bus";
import format from "../../format";
import Customer from "./Customer.vue";
export default {
  mixins: [format],
  data() {
    return {
      // Customize
      bundel_items: [],
      branches: [],
      information_dialog: false,
      complaintFiltered: [],
      needActionsFiltered: ["Yes", "No"],
      need_action: null,
      complaintType: null,
      selected_bundel_items: [],
      si_bundel_items: [],
      showAlert: false,
      isBundle: 0,
      itemDialog: 0,
      // Nested variant selection
      nestedSelections: {},
      nestedVariantQty: {},
      maxRequiredQty: 1,
      table_numbers: [],
      table_no: [],
      complaint: null,
      create_dialog_complaint: false,
      picked_list_for_item_bundel: [],

      // selectable:[],
      product_bundel: [
        {
          text: __("Name"),
          align: "start",
          sortable: true,
          value: "item_name",
        },
        {
          text: __("Item Classification"),
          value: "item_classification",
          align: "center",
        },
        { text: __("QTY"), value: "qty", align: "center" },
        { text: __("Rate"), value: "rate", align: "center" },
        { text: __("State"), value: "state", align: "center" },
        { text: __("Max"), value: "max_required", align: "center" },
        // {text: __("Rate"), value: "rate", align: "center"},
      ],
      addresses: [],
      shipping_address_name: null,
      shipping_address_name_line: null,
      shipping_address_territory: null,
      branch: null,
      pickup: false,
      readonly: false,
      must_be_selected: false,
      // Standard
      pos_profile: "",
      pos_opening_shift: "",
      stock_settings: "",
      invoice_doc: "",
      return_doc: "",
      customer: "",
      customer_info: "",
      discount_amount: 0,
      additional_discount_percentage: 0,
      total_tax: 0,
      items: [],
      item_dialog: {},
      posOffers: [],
      posa_offers: [],
      posa_coupons: [],
      allItems: [],
      discount_percentage_offer_name: null,
      invoiceTypes: ["Invoice", "Order"],
      invoiceType: "Invoice",
      orderTypes: ["Pickup", "Delivery", "Car Service", "Dinin", "Talabat"],
      orderType: "Pickup",
      itemsPerPage: 1000,
      expanded: [],
      singleExpand: true,
      cancel_dialog: false,
      float_precision: 2,
      currency_precision: 2,
      sales_person: null,
      new_line: true,
      delivery_charges: [],
      delivery_charges_rate: 0,
      selcted_delivery_charges: {},
      invoice_posting_date: false,
      customerDialog: false,

      discount_edit_enabled: false,
      show_password_dialog: false,
      password_input: "",
      discount_field_to_enable: "", // either 'amount' or 'percentage'
      complaints: {},
      posting_date: frappe.datetime.nowdate(),
      items_headers: [
        {
          text: __("Name"),
          align: "start",
          sortable: true,
          value: "item_name",
        },
        { text: __("QTY"), value: "qty", align: "center" },
        // { text: __("UOM"), value: "uom", align: "center" },
        { text: __("Rate"), value: "rate", align: "center" },
        { text: __("Amount"), value: "amount", align: "center" },
        // { text: __("is Offer"), value: "posa_is_offer", align: "center" },
      ],
    };
  },

  components: {
    Customer,
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

    maxQuantitiesPerClassification() {
      const maxQuantities = {};
      this.bundel_items.forEach((item) => {
        maxQuantities[item.item_classification] = item.max_required;
      });
      return maxQuantities;
    },
    groupedItems() {
      // Filter out items where item_classification === "Packages"
      const filteredItems = this.bundel_items.filter(
        (item) => item.item_classification !== "Packages",
      );

      // Group remaining items by classification
      return filteredItems.reduce((acc, item) => {
        const classification = item.item_classification;
        if (!acc[classification]) {
          acc[classification] = [];
        }
        acc[classification].push(item);
        return acc;
      }, {});
    },

    classificationSelections() {
      // Calculate whether each classification has reached its max selection

      return this.si_bundel_items.reduce((acc, item) => {
        const classification = item.item_classification;
        acc[classification] = (acc[classification] || 0) + item.qty;
        return acc;
      }, {});
    },
    customerInitials() {
      const name =
        (this.customer_info && this.customer_info.customer_name) ||
        this.customer ||
        "";
      const parts = name.trim().split(/\s+/).filter(Boolean);
      if (!parts.length) {
        return "--";
      }
      return parts
        .slice(0, 2)
        .map((p) => p.charAt(0).toUpperCase())
        .join("");
    },
    total_qty() {
      this.close_payments();
      let qty = 0;
      this.items.forEach((item) => {
        qty += flt(item.qty);
      });
      return this.flt(qty, this.float_precision);
    },
    Total() {
      let sum = 0;
      this.items.forEach((item) => {
        sum += flt(item.qty) * flt(item.rate);
      });
      return this.flt(sum, this.currency_precision);
    },
    subtotal() {
      this.close_payments();
      let sum = 0;
      this.items.forEach((item) => {
        sum += flt(item.qty) * flt(item.rate);
      });
      sum -= this.flt(this.discount_amount);
      sum += this.flt(this.delivery_charges_rate);
      return this.flt(sum, this.currency_precision);
    },
    total_items_discount_amount() {
      let sum = 0;
      this.items.forEach((item) => {
        sum += flt(item.qty) * flt(item.discount_amount);
      });
      return this.flt(sum, this.float_precision);
    },
  },

  methods: {
    bundleItemClasses(item) {
      return {
        "bundle-item-card--active": !item.dummy && item.qty > 0,
        "bundle-item-card--locked": item.dummy,
        "bundle-item-card--locked-active": item.dummy && item.qty > 0,
      };
    },

    // Nested Variant Selection Methods
    hasTemplateItemsInClassification(classifiedItems) {
      return classifiedItems.some(
        (item) => item.is_template && item.let_customer_choose,
      );
    },

    getClassificationAttributes(classifiedItems) {
      // Get unique attributes from all template items in this classification
      const templateItem = classifiedItems.find(
        (item) => item.is_template && item.let_customer_choose,
      );
      if (!templateItem || !templateItem.template_attributes) return [];
      return templateItem.template_attributes;
    },

    onNestedAttributeChange(classification, classifiedItems) {
      // Find matching variant based on selected attributes
      const templateItem = classifiedItems.find(
        (item) => item.is_template && item.let_customer_choose,
      );
      if (!templateItem || !templateItem.template_variants) return;

      const attributes = templateItem.template_attributes || [];
      const selectedAttrs = {};

      attributes.forEach((attr) => {
        const key = classification + "_" + attr.attribute;
        if (this.nestedSelections[key]) {
          selectedAttrs[attr.attribute] = this.nestedSelections[key];
        }
      });

      // Store selected attributes for later use
      this.$set(
        this.nestedSelections,
        classification + "_selectedAttrs",
        selectedAttrs,
      );
      this.$forceUpdate();
    },

    getSelectedVariantForClassification(classification, classifiedItems) {
      const templateItem = classifiedItems.find(
        (item) => item.is_template && item.let_customer_choose,
      );
      if (!templateItem || !templateItem.template_variants) return null;

      const attributes = templateItem.template_attributes || [];
      const selectedAttrs = {};

      attributes.forEach((attr) => {
        const key = classification + "_" + attr.attribute;
        if (this.nestedSelections[key]) {
          selectedAttrs[attr.attribute] = this.nestedSelections[key];
        }
      });

      // Check if all attributes are selected
      if (Object.keys(selectedAttrs).length !== attributes.length) return null;

      // Find matching variant
      return templateItem.template_variants.find((v) => {
        if (!v.attributes) return false;
        return attributes.every((attr) => {
          const variantAttr = v.attributes.find(
            (a) => a.attribute === attr.attribute,
          );
          return (
            variantAttr &&
            variantAttr.attribute_value === selectedAttrs[attr.attribute]
          );
        });
      });
    },

    getNestedVariantQty(classification) {
      return this.nestedVariantQty[classification] || 0;
    },

    increaseNestedVariantQty(classification, classifiedItems) {
      const variant = this.getSelectedVariantForClassification(
        classification,
        classifiedItems,
      );
      if (!variant) return;

      const currentQty = this.nestedVariantQty[classification] || 0;
      this.$set(this.nestedVariantQty, classification, currentQty + 1);

      // Add variant to bundle
      const variantItem = {
        ...variant,
        item_code: variant.item_code,
        item_name: variant.item_name,
        rate: variant.standard_rate,
        qty: 1,
        item_classification: classification,
        posa_row_id: this.item_dialog.posa_row_id,
        parent_item_code: this.item_dialog.item_code,
        is_nested_variant: true,
      };

      this.add_bundel_items(variantItem);
    },

    decreaseNestedVariantQty(classification, classifiedItems) {
      const currentQty = this.nestedVariantQty[classification] || 0;
      if (currentQty <= 0) return;

      this.$set(this.nestedVariantQty, classification, currentQty - 1);

      // Remove variant from bundle
      const variant = this.getSelectedVariantForClassification(
        classification,
        classifiedItems,
      );
      if (variant) {
        const variantItem = {
          item_code: variant.item_code,
          qty: 0,
          item_classification: classification,
          posa_row_id: this.item_dialog.posa_row_id,
        };
        this.add_bundel_items(variantItem);
      }
    },

    updateVip() {
      // if (this.customer_info.vip == 1 && this.customer_info.black_list == 1) {
      //   frappe.msgprint(__("A customer cannot be both VIP and Blacklisted."));
      //   this.customer_info.vip = 0; // Revert the change
      //   return;
      // }
      frappe.call({
        method: "frappe.client.set_value",
        args: {
          doctype: "Customer",
          name: this.customer_info.name,
          fieldname: "custom_vip",
          value: this.customer_info.vip ? 1 : 0, // ERPNext stores as Int(0/1)
        },
        callback: (r) => {
          if (!r.exc) {
            frappe.show_alert({
              message: __("Customer updated successfully"),
              indicator: "green",
            });
          } else {
            frappe.msgprint(__("Error updating customer"));
          }
        },
      });
    },
    updateBlackList() {
      // if (this.customer_info.vip == 1 && this.customer_info.black_list == 1) {
      //   frappe.msgprint(__("A customer cannot be both VIP and Blacklisted."));
      //   this.customer_info.black_list = 0; // Revert the change
      //   return;
      // }
      frappe.call({
        method: "frappe.client.set_value",
        args: {
          doctype: "Customer",
          name: this.customer_info.name,
          fieldname: "custom_black_list",
          value: this.customer_info.black_list ? 1 : 0, // ERPNext stores as Int(0/1)
        },
        callback: (r) => {
          if (!r.exc) {
            frappe.show_alert({
              message: __("Customer updated successfully"),
              indicator: "green",
            });
          } else {
            frappe.msgprint(__("Error updating customer"));
          }
        },
      });
    },
    showCustomerComplaint() {
      console.log("Fetching customer complaints...");
      const customer = this.customer_info.name; // must be the Customer *name*
      frappe.call({
        method: "posawesome.posawesome.api.posapp.list_customer_complaints",
        args: { customer },
        callback: (r) => {
          const rows = r.message || [];
          if (rows.length) {
            this.complaints = rows;
            console.log("Complaints fetched:", this.complaints);
            $("#complaintModal").modal("show");
          } else {
            frappe.msgprint("No complaints found for this customer.");
          }
        },
        error: (e) => {
          frappe.msgprint(e.message || "Failed to fetch complaints.");
        },
      });
    },
    handleHeaderClick(item) {
      this.isBundle = 1;
      this.checkIsProdBundle(item); // no item here unless you pass it from somewhere else
    },
    saveBranchToCookie(branch) {
      if (branch) {
        document.cookie = `selected_branch=${branch}; path=/; max-age=${
          60 * 60 * 24
        }`; // 1 day expiration
      }
    },
    displayRate(item) {
      return item?.rate || item?.rate_price_list_test || "0";
    },
    triggerPasswordDialog(event) {
      console.log("Password dialog triggered", this.pos_profile.name);
      if (
        !this.discount_edit_enabled &&
        this.pos_profile.name !== "Call Center"
      ) {
        event.target.blur();
        this.show_password_dialog = true;
      }
    },
    cancelPasswordDialog() {
      this.show_password_dialog = false;
      this.password_input = "";
    },
    validatePassword() {
      if (this.password_input === this.pos_profile?.custom_discaunt_password) {
        this.discount_edit_enabled = true;
        this.show_password_dialog = false;
        this.password_input = "";
      } else {
        evntBus.$emit("show_mesage", {
          text: `خطأ في كلمة المرور`,
          color: "error",
        });
      }
    },
    close_customer() {
      this.customer = null;
      this.address = null;
      this.shipping_address_name = null;
      this.shipping_address_name_line = null;
      this.shipping_address_territory = null;
      this.cancel_invoice();
      this.customerDialog = false;
    },
    increaseQty(item) {
      const vm = this;

      if (item.item_code != "Spicy") {
        this.bundel_items.forEach((i) => {
          if (
            i.item_code == "Spicy" &&
            item.item_classification == i.item_classification
          ) {
            i.dummy = true;
          }
        });
      }
      if (item.item_code != "Regular") {
        this.bundel_items.forEach((i) => {
          if (
            i.item_code == "Regular" &&
            item.item_classification == i.item_classification
          ) {
            i.dummy = true;
          }
        });
      }
      if (item.item_code == "Large") {
        this.bundel_items.forEach((i) => {
          if (i.custom_large) {
            i.hide = false;
            item.addons = true;
          }
        });
      }

      if (item.item_code == "Meduim") {
        this.bundel_items.forEach((i) => {
          if (i.custom_meduim) {
            i.hide = false;
            item.addons = true;
          }
        });
      }
      if (item.item_code == "Spicy") {
        this.bundel_items.forEach((i) => {
          if (i.is_spicy) {
            i.qty = Number(i.closed_item) - 1;
            vm.increaseQtyAndAddBundle(i);
          }
        });
      }

      if (item.item_code == "Regular") {
        this.bundel_items.forEach((i) => {
          if (i.is_regular) {
            i.qty = Number(i.closed_item) - 1;

            vm.increaseQtyAndAddBundle(i);
          }
        });
      }
      // this.bundel_items.forEach((i) => {
      //     if (item.item_code == i.custom_teigger_item) {

      //       i.qty = i.closed_item;
      //     }
      //   });
      // item.qty = item.closed_item - 1

      // Check if item is a template and customer can choose variant - open variant selector
      if (
        item.is_template &&
        item.let_customer_choose &&
        item.template_variants &&
        item.template_variants.length > 0
      ) {
        evntBus.$emit(
          "open_option_variant_selector",
          item,
          (selectedVariant) => {
            // Replace item with selected variant
            item.original_item_code = item.item_code;
            item.item_code = selectedVariant.item_code;
            item.item_name = selectedVariant.item_name;
            item.rate = selectedVariant.standard_rate;
            item.selected_variant = selectedVariant;
            vm.increaseQtyAndAddBundle(item);
          },
        );
      } else {
        vm.increaseQtyAndAddBundle(item);
      }
    },
    // Customize
    increaseQtyAndAddBundle(item) {
      // if (item.is_bundle)
      //   this.bundel_items = this.bundel_items.filter(
      //     (i) => !i.custom_teigger_item
      //   );
      if (
        item.closed_item &&
        Number(item.closed_item) > 0 &&
        item.item_classification == "Pieces"
      ) {
        item.qty = Number(item.closed_item);
        item.dummy = true;
      } else if (
        (item.item_classification == "Sandwich Pieces" ||
          item.item_classification == "Pieces") &&
        item.parent_group
      ) {
        item.qty = 1;
        item.dummy = true;

        this.add_bundel_items(item);
        if (item.qty == 0) {
          // this.picked_list_for_item_bundel =
          //   this.picked_list_for_item_bundel.filter(
          //     (i) =>
          //       i.item_code != item.item_code && i.posa_row_id == item.posa_row_id
          //   );
        }
      } else item.qty++;
      // Increment the qty before calling the method
      //       // item.dummy = true;
      let sum_qty = 0;
      this.bundel_items.forEach((i) => {
        if (i.item_classification == item.item_classification) {
          sum_qty += i.qty;
        }
      });
      let sum_qty_2 = 0;
      this.bundel_items.forEach((i) => {
        if (
          i.item_classification == item.item_classification &&
          item.custom_teigger_item &&
          i.custom_teigger_item == item.item_code
        ) {
          sum_qty_2 += i.qty + item.qty;
        }
      });
      if (!item.custom_teigger_item) {
        this.bundel_items.forEach((i) => {
          if (
            i.item_classification == item.item_classification &&
            i.max_required == sum_qty &&
            !item.filled
          ) {
            i.dummy = true;

            if (item.filled) {
              this.bundel_items.forEach((i) => {
                if (i.item_classification == item.item_classification) {
                  i.dummy = true;
                }
              });
            }
          }
        });

        this.bundel_items.forEach((i) => {
          if (
            item.filled &&
            i.item_classification == item.item_classification &&
            i.item_code != item.item_code
          ) {
            i.dummy = true;
          }
          if (
            i.item_classification == item.item_classification &&
            i.max_required == item.qty &&
            i.item_code == item.item_code &&
            item.filled
          ) {
            i.dummy = true;

            if (item.filled) {
              this.bundel_items.forEach((i) => {
                if (i.item_classification == item.item_classification) {
                  i.dummy = true;
                }
              });
            }
          }
        });
      }
      if (sum_qty_2 == item.closed_item) {
        item.dummy = true;
        this.bundel_items.forEach((i) => {
          if (
            ((i.item_code == item.custom_teigger_item ||
              i.item_code == item.custom_teigger_item_2) &&
              i.item_classification == item.item_classification) ||
            ((i.custom_teigger_item == item.item_code ||
              i.custom_teigger_item_2 == item.item_code) &&
              i.item_classification == item.item_classification)
          ) {
            i.dummy = true;
          }
        });
      }

      this.append_pecies_in_bundle(item);
      // Call the method to add bundle items
      this.add_bundel_items(item);
      const data = {
        picked_list_for_item_bundel: this.picked_list_for_item_bundel,
        items: this.items,
      };
      evntBus.$emit("set_picked_list_for_item_bundel", data);
    },
    decreaseQty(item) {
      if (item.is_bundle || item.item_classification == "Size") {
        this.bundel_items = this.bundel_items.filter(
          (i) => i.item_classification != "Chicken Pieces",
        );
        this.bundel_items = this.bundel_items.filter(
          (i) => i.item_classification != "Sandwich Pieces",
        );
        this.bundel_items = this.bundel_items.filter(
          (i) => i.item_classification != "Pieces",
        );
      }
      const vm = this;
      if (item.state == "Item Must Be Selected") return;
      if (item.item_code == "Spicy") {
        this.bundel_items.forEach((i) => {
          if (i.is_spicy) {
            i.qty = 1;
            vm.decreaseQtyAndAddBundle(i);
          }
        });
      }
      if (item.item_code == "Large") {
        this.bundel_items.forEach((i) => {
          if (i.custom_large) {
            i.hide = true;
          }
        });
      }

      if (item.item_code == "Meduim") {
        this.bundel_items.forEach((i) => {
          if (i.custom_meduim) {
            i.hide = true;
          }
        });
      }
      if (item.item_code == "Regular") {
        this.bundel_items.forEach((i) => {
          if (i.is_regular) {
            i.qty = 1;
            vm.decreaseQtyAndAddBundle(i);
          }
        });
      }
      vm.decreaseQtyAndAddBundle(item);
    },
    decreaseQtyAndAddBundle(item) {
      if (
        item.item_classification == "Sandwich Pieces" ||
        item.item_classification == "Pieces"
      ) {
        item.qty = 0;
        item.dummy = false;
        this.add_bundel_items(item);
        if (item.qty == 0) {
          // this.picked_list_for_item_bundel =
          //   this.picked_list_for_item_bundel.filter(
          //     (i) =>
          //       i.item_code != item.item_code && i.posa_row_id == item.posa_row_id
          //   );
        }
      } else {
        item.qty -= 1;
        item.dummy = false;
        let sum_qty = 0;

        this.bundel_items.forEach((i) => {
          if (i.item_classification == item.item_classification) {
            sum_qty += i.qty;
          }
        });
        let sum_qty_2 = 0;
        this.bundel_items.forEach((i) => {
          if (
            i.item_classification == item.item_classification &&
            item.custom_teigger_item &&
            i.custom_teigger_item == item.item_code
          ) {
            sum_qty_2 += i.qty + item.qty;
          }
        });
        if (!item.custom_teigger_item) {
          this.bundel_items.forEach((i) => {
            if (
              i.item_classification == item.item_classification &&
              i.max_required != sum_qty &&
              !item.filled
            ) {
              i.dummy = false;
              if (item.filled) {
                this.bundel_items.forEach((i) => {
                  if (i.item_classification == item.item_classification) {
                    i.dummy = false;
                  }
                });
              }
            }
          });
          this.bundel_items.forEach((i) => {
            if (
              item.filled &&
              i.item_classification == item.item_classification &&
              i.item_code == item.item_code
            ) {
              i.dummy = false;
            }
            if (
              i.item_classification == item.item_classification &&
              item.qty == 0 &&
              item.filled
            ) {
              i.dummy = false;

              if (item.filled) {
                this.bundel_items.forEach((i) => {
                  if (i.item_classification == item.item_classification) {
                    i.dummy = false;
                  }
                });
              }
            }
          });
        }
        if (sum_qty_2 != item.closed_item) {
          item.dummy = false;
          this.bundel_items.forEach((i) => {
            if (
              ((i.item_code == item.custom_teigger_item ||
                i.item_code == item.custom_teigger_item_2) &&
                i.item_classification == item.item_classification) ||
              ((i.custom_teigger_item == item.item_code ||
                i.custom_teigger_item_2 == item.item_code) &&
                i.item_classification == item.item_classification)
            ) {
              i.dummy = false;
            }
          });
        }
        if (item.is_bundle) {
          this.bundel_items = this.bundel_items.filter(
            (i) =>
              i.item_classification != "Chicken Pieces" ||
              i.item_classification != "Sandwich Pieces",
          );
        }
        if (item.is_bundle)
          this.bundel_items = this.bundel_items.filter(
            (i) => !i.custom_teigger_item,
          );
        this.add_bundel_items(item);
        if (item.qty == 0) {
          // this.picked_list_for_item_bundel =
          //   this.picked_list_for_item_bundel.filter(
          //     (i) =>
          //       i.item_code != item.item_code && i.posa_row_id == item.posa_row_id
          //   );
        }
      }
      const data = {
        picked_list_for_item_bundel: this.picked_list_for_item_bundel,
        items: this.items,
      };
      evntBus.$emit("set_picked_list_for_item_bundel", data);
    },
    initializeItems(item_main) {
      // Set initial states outside of computed properties
      this.bundel_items.forEach((item) => {
        item.parent_group = item_main.item_group;
        item.selected = false;
        if (item.state === "Item Must Be Selected") {
          item.selected = true;
          this.add_bundel_items(item);
          // Ensure initial selection
        }
      });
    },
    close_bundle_2() {
      this.isBundle = 0;
      this.bundel_items = [];
      const last_item = this.items.at(0);
      this.items.shift();
      this.picked_list_for_item_bundel =
        this.picked_list_for_item_bundel.filter(
          (i) => i.posa_row_id != last_item.posa_row_id,
        );
      const data = {
        picked_list_for_item_bundel: this.picked_list_for_item_bundel,
        items: this.items,
      };
      evntBus.$emit("set_picked_list_for_item_bundel", data);
    },
    clear_bundle() {
      this.items.forEach((el) => {
        if (
          this.item_dialog.posa_row_id == el.posa_row_id ||
          this.item_dialog.posa_row_id == el.old_posa_row_id
        ) {
          el.posa_notes = this.item_dialog.posa_notes;
          el.qty = this.item_dialog.qty;
        }
      });

      if (this.bundel_items.length > 0) {
        const itemss = this.bundel_items.reduce((acc, item) => {
          const classification = item.item_classification; // Use item_classification as the key
          if (!acc[classification]) {
            acc[classification] = [];
          }
          acc[classification].push(item);
          return acc;
        }, {});
        let is_vaild = 1;
        console.log(this.bundel_items);
        this.bundel_items.forEach((el) => {
          if (
            el.qty == 0 &&
            el.state == "Minimum 1 Item is Required In Section" &&
            !el.hide
          ) {
            let count_qty = 0;
            let max_qty = 0;
            console.log(el.item_classification, itemss[el.item_classification]);
            itemss[el.item_classification].forEach((i) => {
              if (!i.hide) count_qty += i.qty;
              if (i.item_classification == "Checken Pieces" && !i.hide) {
                max_qty = i.max_required;
              }
            });
            if (count_qty == 0) {
              evntBus.$emit("show_mesage", {
                text: __(
                  `Item Classification {0} Minimum 1 Item is Required In Section!`,
                  [el.item_classification],
                ),
                color: "warning",
              });
              is_vaild = 0;
            }
            console.log(
              "count_qty < max_qty",
              count_qty < max_qty,
              count_qty,
              max_qty,
            );
            if (el.item_classification == "Checken Pieces" && !el.hide) {
              if (count_qty < max_qty) {
                evntBus.$emit("show_mesage", {
                  text: __(
                    `Item Classification {0} Minimum 1 Item is Required In Section!`,
                    [el.item_classification],
                  ),
                  color: "warning",
                });
                is_vaild = 0;
              }
            }
          }
        });
        if (is_vaild == 1) {
          this.bundel_items = [];
          this.isBundle = 0;
        } else {
          this.isBundle = 1;
        }
      } else this.bundel_items = [];
    },
    close_dialog(item) {
      if (this.customer) {
        this.customerDialog = false;
      } else {
        this.customerDialog = true;

        evntBus.$emit("show_mesage", {
          text: __(`Select Customer`),
          color: "warning",
        });
        return;
      }
      if (this.branch) {
        this.customerDialog = false;
      } else {
        this.customerDialog = true;
        evntBus.$emit("show_mesage", {
          text: __(`Select Branch`),
          color: "warning",
        });
        return;
      }

      if (this.orderType == "Delivery" && this.shipping_address_name == null) {
        this.customerDialog = true;
        evntBus.$emit("show_mesage", {
          text: __(`Select Address`),
          color: "warning",
        });
        return;
      }

      // evntBus.$emit("set_customer", this.customer);
      // evntBus.$emit("set_customer_readonly", 1);
    },
    isItemDisabled(item) {
      return item.selectable; // Adjust the condition as needed
    },
    new_address() {
      const data = {
        customer: this.customer,
        address: this.shipping_address_name,
      };
      evntBus.$emit("open_new_address", data);
    },
    addressFilter(item, queryText, itemText) {
      const textOne = item.address_title
        ? item.address_title.toLowerCase()
        : "";
      const textTwo = item.address_line1
        ? item.address_line1.toLowerCase()
        : "";
      const textThree = item.address_line2
        ? item.address_line2.toLowerCase()
        : "";
      const textFour = item.city ? item.city.toLowerCase() : "";
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
    table_noFilter(item, queryText, itemText) {
      const textOne = item.name ? item.name.toLowerCase() : "";
      const textTwo = item.name ? item.name.toLowerCase() : "";
      const textThree = item.name ? item.name.toLowerCase() : "";
      const textFour = item.name ? item.name.toLowerCase() : "";
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
    get_addresses() {
      const vm = this;
      if (!vm.customer) {
        return;
      }
      frappe.call({
        method: "posawesome.posawesome.api.posapp.get_customer_addresses",
        args: { customer: vm.customer },
        async: true,
        callback: function (r) {
          if (!r.exc) {
            vm.addresses = r.message;
          } else {
            vm.addresses = [];
          }
        },
      });
    },
    get_tables() {
      const vm = this;
      frappe.call({
        method: "posawesome.posawesome.api.posapp.get_table_no",
        args: {
          branch: vm.pos_profile.branch,
        },
        async: true,
        callback: function (r) {
          if (!r.exc) {
            vm.table_numbers = r.message;
          } else {
            vm.table_numbers = [];
          }
        },
      });
    },
    set_branch() {
      const vm = this;
      this.addresses.forEach((address) => {
        if (address.name == vm.shipping_address_name) {
          vm.branch = address.branch;
          vm.shipping_address_name_line = address.address_line1;
          vm.shipping_address_territory = address.territory;
          vm.saveBranchToCookie(vm.branch);
        }
      });
    },
    get_branches() {
      const vm = this;
      if (!vm.pos_profile) {
        return;
      }
      frappe.call({
        method: "posawesome.posawesome.custom_api.branch.get_branches",
        args: { pos_profile: vm.pos_profile },
        async: true,
        callback: function (r) {
          if (!r.exc) {
            if (vm.pos_profile.name == "Call Center") vm.branches = r.message;
            else {
              vm.branches = [{ name: vm.pos_profile.branch }];
              vm.branch = vm.pos_profile.branch;
              vm.saveBranchToCookie(vm.branch);
            }
            // vm.branch = this.pos_profile.name;
          } else {
            vm.branches = [];
          }
        },
      });
    },
    async getBundleOptions(item) {
      // Try custom bundle options first
      const customOptions = await this.checkIsProdBundle(item);
      if (customOptions && customOptions.length) return customOptions;
      // Fallback to Product Bundle items
      const bundleItems = await this.getProductBundleItems(item.item_code);
      return bundleItems || [];
    },
    async checkIsProdBundle(item) {
      // Normalize price list before server call
      this.item_dialog = item;
      this.item_dialog.price_list = this.sales_person;
      item.price_list = this.sales_person;

      const res = await frappe.call({
        method:
          "posawesome.posawesome.custom_api.product_bundle.checkIsProdBundle",
        args: {
          item_code: item.item_code,
        },
      });

      if (res && res.message) {
        return res.message;
      }
      return [];
    },
    async getProductBundleItems(item_code) {
      const res = await frappe.call({
        method: "posawesome.posawesome.custom_api.product_bundle.get_items",
        args: {
          item_code: item_code,
        },
      });
      return res && res.message ? res.message : [];
    },
    add_small_items(item) {
      const self = this;

      let response = frappe.call({
        method: "posawesome.posawesome.custom_api.product_bundle.get_items_2",
        args: {
          item_code: item.item_code,
        },
        callback: function (r) {
          if (r.message) {
            return r.message;
          }
        },
      });
      return response;
    },
    childProdBundle(item) {
      const self = this;

      let response = frappe.call({
        method: "posawesome.posawesome.custom_api.product_bundle.get_items",
        args: {
          item_code: item.item_code,
        },
        callback: function (r) {
          if (r.message) {
            self.isBundle = 1;
            self.initializeItems(item);

            return r.message;
          }
        },
      });
      return response;
    },

    async append_pecies_in_bundle(item) {
      let previous_item_code = item.item_code;
      let previous_item_name = item.item_name;
      console.log("itemszzzzzzzzzzzzzzzzzzz", item);
      if (item.item_classification == "Size") {
        let item_old = item;
        previous_item_code = item.item_name;
        previous_item_name = item.item_code;
        item.price_list = this.sales_person;
        item.is_bundle = true;
        item.item_code = item.custom_main_item;
        item.item_name = item.custom_main_item;
        const old_item_posa_row_id = item.posa_row_id;
        this.items = this.items.filter(
          (i) => i.posa_row_id != item.posa_row_id,
        );
        item.old_posa_row_id = item.posa_row_id;
        returen_item = this.add_item(item);
        item.posa_row_id = returen_item.posa_row_id;
        this.bundel_items.forEach((i) => {
          if (i.posa_row_id == old_item_posa_row_id) {
            i.posa_row_id = item.posa_row_id;
            ((i.parent_item_code = this.item_dialog.item_code),
              (i.parent_group = this.item_dialog.item_group));
          }
        });
        this.picked_list_for_item_bundel.forEach((i) => {
          if (i.posa_row_id == old_item_posa_row_id) {
            i.posa_row_id = item.posa_row_id;
            ((i.parent_item_code = this.item_dialog.item_code),
              (i.parent_group = this.item_dialog.item_group));
          }
        });
      }

      if (item.is_bundle) {
        const data = await this.childProdBundle(item);
        const index = await this.bundel_items.findIndex(
          (i) => i.item_code === item.item_code,
        );
        let bundleqty = 0;
        data.message.forEach((i) => {
          i.addons = item.addons;
          bundleqty += i.qty;
        });
        // this.add_bundel_items(myData);
        //bundleqty / 2
        if (
          item.item_classification == "Sandwich" ||
          item.item_classification == "Sauces" ||
          item.item_classification == "Size" ||
          item.item_classification == "Chicken Strips" ||
          item.item_classification == "Wings"
        ) {
          let title = "Pieces";

          // else if(item.item_classification == "Size") {
          //   title = "Chicken Pieces";
          // }
          // else if(item.item_classification == "Chicken Strips") {
          //   title = "Chicken Strips Pieces";
          // }
          // else if(item.item_classification == "Wings") {
          //   title = "Wings Pieces";
          // }
          // if(item.item_group === 'Fatta') {
          //   title = "Fatta";
          // }
          let is_hide = true;
          is_type = false;
          this.bundel_items.forEach((el) => {
            if (el.item_classification == "Type") is_type = true;
          });
          data.message.forEach((i) => {
            if (i.parent_group == "Sandwiches") {
              title = "Sandwich Pieces";
            }
            if (i.parent_group == "Fatta") {
              title = "Fatta";
            }

            if (i.custom_hide === false) {
              is_hide = false;
            }
            const myData = {
              item_name: i.item_code,
              item_code: i.item_code,
              max_required: bundleqty,
              closed_item: i.custom_qty_closed,
              dummy: true,
              custom_teigger_item: i.custom_teigger_item,
              custom_teigger_item_2: i.custom_teigger_item_2,
              parent_teigger_item: item.item_code,
              selected: true,
              qty: 0,
              qty_closed: 1,
              filled: i.filled,
              hide: i.custom_hide,
              item_classification: title,
              item_classification_pakage: i.custom_product_item_classification,
              state: item.state,
              posa_row_id: item.posa_row_id,
              is_spicy: i.custom_spicy,
              is_regular: i.custom_regular,
              parent_item_code: this.item_dialog.item_code,
              parent_group: this.item_dialog.item_group,
            };
            if (myData.qty <= 0) {
              myData.dummy = false;
              myData.selected = false;
            }

            if (
              item.item_classification == "Sandwich" ||
              item.item_classification == "Size" ||
              item.item_classification == "Sauces" ||
              item.item_classification == "Fries" ||
              item.item_classification == "Rice" ||
              item.item_classification == "Salad" ||
              // item.item_classification == "Sandwich" ||
              item.state == "Item Must Be Selected"
            ) {
              myData.qty = Number(i.custom_qty_closed);
              myData.dummy = true;
              myData.selected = true;
            }
            if (
              myData.is_spicy ||
              myData.is_regular ||
              myData.custom_large ||
              myData.custom_meduim
            )
              myData.qty = 0;
            // if(item.item_classification == "Size"){
            //   myData.qty = i.custom_qty_closed;
            // }
            i.parent_group = this.item_dialog.item_group;
            if (is_hide) {
              console.log("bundellllllls", JSON.stringify(this.bundel_items));
              if (is_type) this.bundel_items.splice(3, 0, myData);
              else this.bundel_items.splice(index + 1, 0, myData);
            }

            this.add_bundel_items(myData);
          });
        } else {
          let title = "";

          let is_hide = true;
          data.message.forEach((i) => {
            if (i.parent_group == "Sandwiches") {
              title = "Sandwich Pieces";
            }
            if (i.parent_group == "Fatta") {
              title = "Fatta";
            }
            if (i.custom_hide === false) {
              is_hide = false;
            }
            const myData = {
              item_name: i.item_code,
              item_code: i.item_code,
              max_required: bundleqty / 2 || Number(i.custom_qty_closed),
              closed_item:
                i.qty || bundleqty / 2 || Number(i.custom_qty_closed),
              dummy: false,
              custom_teigger_item: i.custom_teigger_item,
              custom_teigger_item_2: i.custom_teigger_item_2,
              parent_teigger_item: item.item_code,
              selected: false,
              qty: 0,
              qty_closed: Number(i.custom_qty_closed),
              filled: i.filled,
              item_classification: "Checken Pieces",
              item_classification_pakage: i.custom_product_item_classification,
              state: item.state,
              hide: i.custom_hide,
              posa_row_id: item.posa_row_id,
              is_spicy: i.custom_spicy,
              is_regular: i.custom_regular,
              parent_group: this.item_dialog.item_group,

              parent_item_code: this.item_dialog.item_code,
            };
            if (
              item.item_classification == "Sauces" ||
              item.item_classification == "Fries" ||
              item.item_classification == "Rice" ||
              item.item_classification == "Salad"
            ) {
              myData.qty = i.qty * item.qty;
            }
            if (
              myData.is_spicy ||
              myData.is_regular ||
              myData.custom_large ||
              myData.custom_meduim
            )
              myData.qty = 0;
            i.parent_group = this.item_dialog.item_group;
            if (is_hide) {
              this.bundel_items.splice(index + 1, 0, myData);
            }
            // this.bundel_items.splice(index + 1, 0, myData);
            // for (let j = 0; j < item.qty; j++)
            this.add_bundel_items(myData);
          });
        }
      }
      if (item.item_classification == "Size") {
        item.item_code = previous_item_code;
        item.item_name = previous_item_name;
        item.is_bundle = false;
      }
    },
    add_bundel_items(item, plus = false) {
      item.parent_group = this.item_dialog.item_group;
      if (item.item_code == "Spicy" || item.item_code == "Regular") {
        // item.addons = true
        let index = -1;
        index = this.picked_list_for_item_bundel.findIndex(
          (i) =>
            i.item_code == item.item_code && i.posa_row_id == item.posa_row_id,
        );
        // item.addons = true
        if (index == -1) this.picked_list_for_item_bundel.push(item);
        else if (index != -1) {
          this.picked_list_for_item_bundel[index].qty = item.qty;
        }
        return;
      }
      if (plus) {
        item.addons = true;
        let index = -1;
        index = this.picked_list_for_item_bundel.findIndex(
          (i) =>
            i.item_code == item.item_code && i.posa_row_id == item.posa_row_id,
        );
        if (index == -1) this.picked_list_for_item_bundel.push(item);
        else if (index != -1) {
          this.picked_list_for_item_bundel[index].qty +=
            this.picked_list_for_item_bundel[index].qty;
        }
        return;
      }
      if (item.rate && item.qty > 0 && item.item_classification != "Size") {
        let index = -1;
        index = this.picked_list_for_item_bundel.findIndex(
          (i) =>
            i.item_code == item.item_code && i.posa_row_id == item.posa_row_id,
        );
        item.addons = true;
        if (index == -1) {
          item.custom_hide_print = true;
          const returned_item = this.add_item(item);
          item.custom_hide_print = false;
          item.real_posa = returned_item.posa_row_id;
          this.picked_list_for_item_bundel.push(item);
        } else if (index != -1) {
          this.picked_list_for_item_bundel[index].qty = item.qty;
          this.items.forEach((el) => {
            if (el.posa_row_id == item.real_posa) el.qty = item.qty;
          });
        }
      } else {
        let previous_item_code = item.item_code;
        let previous_item_name = item.item_name;

        if (item.item_classification == "Size") {
          previous_item_code = item.item_name;
          previous_item_name = item.item_code;
          item.price_list = this.sales_person;
          item.is_bundle = true;
          item.item_code = item.custom_main_item;
          item.item_name = item.custom_main_item;
        }

        if (item.is_bundle) {
          let index = -1;
          index = this.picked_list_for_item_bundel.findIndex(
            (i) =>
              i.item_code == item.item_code &&
              i.posa_row_id == item.posa_row_id,
          );
          if (index == -1) this.picked_list_for_item_bundel.push(item);
          else if (index != -1) {
            this.picked_list_for_item_bundel[index].qty = item.qty;
          }
          if (item.item_classification == "Size") {
            item.item_code = previous_item_code;
            item.item_name = previous_item_name;
            item.is_bundle = false;
          }

          return;
        }

        let index = -1;
        index = this.picked_list_for_item_bundel.findIndex(
          (i) =>
            i.item_code == item.item_code && i.posa_row_id == item.posa_row_id,
        );
        if (index == -1) this.picked_list_for_item_bundel.push(item);
        else if (index != -1) {
          this.picked_list_for_item_bundel[index].qty = item.qty;
        }
        // if (item.qty == 0 ) {
        //   if (item.item_classification =="Sandwich Pieces" || item.item_classification == "Fatta") {
        //     this.picked_list_for_item_bundel =
        //     this.picked_list_for_item_bundel.filter(
        //       (i) =>
        //       i.posa_row_id != item.posa_row_id
        //     );
        //   } else  {
        //         this.picked_list_for_item_bundel =
        //   this.picked_list_for_item_bundel.filter(
        //     (i) =>i.item_code == item.item_code &&
        //     i.posa_row_id == item.posa_row_id
        //   );
        //   }

        // }
        item.item_code = previous_item_code;
        item.item_name = previous_item_name;
        item.is_bundle = false;
      }
    },

    disableOtherItemsInClassification(classification) {
      // Set `selected` to true for all items in the classification
      this.bundel_items.forEach((i) => {
        if (i.item_classification === classification && !i.selected) {
          i.selected = true;
          i.dummy = true;
        }
      });
    },

    resetClassification(classification) {
      // Reset items in the classification if necessary
      this.bundel_items.forEach((item) => {
        if (item.item_classification === classification) {
          item.selected = false;
          item.dummy = false;
        }
      });
      // Remove items from `si_bundel_items`
      this.si_bundel_items = this.si_bundel_items.filter(
        (item) => item.item_classification !== classification,
      );
    },
    get_packed_items() {
      const packed_items_list = [];

      // this.items.forEach(el=>{
      //   this.picked_list_for_item_bundel.forEach((el2)=>{
      //     if(el.posa_row_id == el2.posa_row_id)
      //       {
      //         const totals = el2.qty  * el.qty
      //         el2.qty =totals
      //         console.log("don't here me",el2.qty* el.qty )
      //       }
      //   })
      // })
      const picked_list_for_item = this.picked_list_for_item_bundel.filter(
        (i) => i.qty > 0,
      );
      picked_list_for_item.forEach((item) => {
        let adjusted_qty = item.qty;

        // Convert to kg if item classification matches
        const classes_to_convert = ["Fries", "Sauces", "Salad", "Rice"];
        if (
          classes_to_convert.includes(item.item_classification) &&
          item.custom_qty_gram
        ) {
          adjusted_qty = (flt(item.custom_qty_gram) * flt(item.qty)) / 1000;
        }

        const new_item = {
          parent_item: item.parent_item_code,
          item_code: item.item_code,
          packed_quantity: item.packed_quantity,
          set_no: item.set_no,
          combo_qty: item.combo_qty,
          quantity: adjusted_qty,
          default_item: item.default_item,
          qty: adjusted_qty,
          rate: item.rate,

          posa_row_id: item.posa_row_id,
          parent_item_code: this.item_dialog.item_code,
        };
        if (item.item_classification == "Sandwich") {
          new_item.custom_sandwatich_offer = 1;
        }
        packed_items_list.push(new_item);
      });
      console.log(packed_items_list);
      return packed_items_list;
    },

    // Standard
    remove_item(item) {
      const index = this.items.findIndex(
        (el) => el.posa_row_id == item.posa_row_id,
      );
      if (index >= 0) {
        this.items.splice(index, 1);
      }
      const idx = this.expanded.findIndex(
        (el) => el.posa_row_id == item.posa_row_id,
      );
      if (idx >= 0) {
        this.expanded.splice(idx, 1);
      }
      // Customize
      this.picked_list_for_item_bundel =
        this.picked_list_for_item_bundel.filter((element) => {
          return element.posa_row_id != item.posa_row_id;
        });
      const picked_list_for_item = this.picked_list_for_item_bundel;
      const data = {
        picked_list_for_item_bundel: picked_list_for_item,
        items: this.items,
      };
      evntBus.$emit("set_picked_list_for_item_bundel", data);
    },

    add_one(item) {
      item.qty++;
      if (item.qty == 0) {
        this.remove_item(item);
      }
      this.calc_stock_qty(item, item.qty);
      this.$forceUpdate();
      // this.picked_list_for_item_bundel.forEach(el=>{
      //   if(el.posa_row_id == item.posa_row_id)

      // })
    },
    subtract_one(item) {
      item.qty--;
      if (item.qty == 0) {
        this.remove_item(item);
      }
      this.calc_stock_qty(item, item.qty);
      this.$forceUpdate();
    },

    add_item(item) {
      let redturned_item = null;
      if (!item.uom) {
        item.uom = item.stock_uom;
      }
      let index = -1;
      if (!this.new_line) {
        index = this.items.findIndex(
          (el) =>
            el.item_code === item.item_code &&
            el.uom === item.uom &&
            !el.posa_is_offer &&
            !el.posa_is_replace &&
            el.batch_no === item.batch_no,
        );
      }
      if (index === -1 || this.new_line) {
        const new_item = this.get_new_item(item);
        if (item.has_serial_no && item.to_set_serial_no) {
          new_item.serial_no_selected = [];
          new_item.serial_no_selected.push(item.to_set_serial_no);
          item.to_set_serial_no = null;
        }
        if (item.has_batch_no && item.to_set_batch_no) {
          new_item.batch_no = item.to_set_batch_no;
          item.to_set_batch_no = null;
          item.batch_no = null;
          this.set_batch_qty(new_item, new_item.batch_no, false);
        }
        this.items.unshift(new_item);
        this.update_item_detail(new_item);
        redturned_item = new_item;
      } else {
        const cur_item = this.items[index];
        this.update_items_details([cur_item]);
        if (item.has_serial_no && item.to_set_serial_no) {
          if (cur_item.serial_no_selected.includes(item.to_set_serial_no)) {
            evntBus.$emit("show_mesage", {
              text: __(`This Serial Number {0} has already been added!`, [
                item.to_set_serial_no,
              ]),
              color: "warning",
            });
            item.to_set_serial_no = null;
            return;
          }
          cur_item.serial_no_selected.push(item.to_set_serial_no);
          item.to_set_serial_no = null;
        }
        if (!cur_item.has_batch_no) {
          cur_item.qty += item.qty || 1;
          this.calc_stock_qty(cur_item, cur_item.qty);
        } else {
          if (
            (cur_item.stock_qty < cur_item.actual_batch_qty &&
              cur_item.batch_no == item.batch_no) ||
            !cur_item.batch_no
          ) {
            cur_item.qty += item.qty || 1;
            this.calc_stock_qty(cur_item, cur_item.qty);
          } else {
            const new_item = this.get_new_item(cur_item);
            new_item.batch_no = item.batch_no || item.to_set_batch_no;
            new_item.batch_no_expiry_date = "";
            new_item.actual_batch_qty = "";
            new_item.qty = item.qty || 1;
            if (new_item.batch_no) {
              this.set_batch_qty(new_item, new_item.batch_no, false);
              item.to_set_batch_no = null;
              item.batch_no = null;
            }
            this.items.unshift(new_item);
          }
        }
        this.set_serial_no(cur_item);
        redturned_item = cur_item;
      }
      this.$forceUpdate();
      console.log("eeeeeeeeee", this.items);
      return redturned_item;
    },

    get_new_item(item) {
      const new_item = { ...item };
      if (!item.qty) {
        item.qty = 1;
      }
      if (!item.posa_is_offer) {
        item.posa_is_offer = 0;
      }
      if (!item.posa_is_replace) {
        item.posa_is_replace = "";
      }
      new_item.stock_qty = item.qty;
      new_item.discount_amount = 0;
      new_item.discount_percentage = 0;
      new_item.discount_amount_per_item = 0;
      new_item.price_list_rate = item.rate;
      new_item.qty = item.qty;
      new_item.uom = item.uom ? item.uom : item.stock_uom;
      new_item.actual_batch_qty = "";
      new_item.conversion_factor = 1;
      new_item.posa_offers = JSON.stringify([]);
      new_item.posa_offer_applied = 0;
      new_item.posa_is_offer = item.posa_is_offer;
      new_item.posa_is_replace = item.posa_is_replace || null;
      new_item.is_free_item = 0;
      new_item.posa_notes = "";
      new_item.posa_delivery_date = "";
      new_item.posa_row_id = this.makeid(20);
      if (
        (!this.pos_profile.posa_auto_set_batch && new_item.has_batch_no) ||
        new_item.has_serial_no
      ) {
        this.expanded.push(new_item);
      }
      return new_item;
    },

    cancel_invoice() {
      const doc = this.get_invoice_doc();
      this.invoiceType = this.pos_profile.posa_default_sales_order
        ? "Order"
        : "Invoice";
      this.invoiceTypes = ["Invoice", "Order"];
      this.posting_date = frappe.datetime.nowdate();
      if (doc.name && this.pos_profile.posa_allow_delete) {
        frappe.call({
          method: "posawesome.posawesome.api.posapp.delete_invoice",
          args: { invoice: doc.name },
          async: true,
          callback: function (r) {
            if (r.message) {
              evntBus.$emit("show_mesage", {
                text: r.message,
                color: "warning",
              });
            }
          },
        });
      }
      this.items = [];
      this.posa_offers = [];
      evntBus.$emit("set_pos_coupons", []);
      this.posa_coupons = [];
      this.customer = this.pos_profile.customer;
      this.invoice_doc = "";
      this.return_doc = "";
      this.discount_amount = 0;
      this.additional_discount_percentage = 0;
      this.delivery_charges_rate = 0;
      this.selcted_delivery_charges = {};
      this.shipping_address_name = null;
      this.picked_list_for_item_bundel = [];
      this.pickup = 0;

      evntBus.$emit("set_customer_readonly", false);
      this.customerDialog = true;
      this.cancel_dialog = false;
      const picked_list_for_item = this.picked_list_for_item_bundel.filter(
        (element) => {
          return element.qty == 0 || element.addons;
        },
      );
      const data = {
        picked_list_for_item_bundel: picked_list_for_item,
        items: this.items,
      };
      evntBus.$emit("set_picked_list_for_item_bundel", data);
    },

    new_invoice(data = {}) {
      let old_invoice = null;
      evntBus.$emit("set_customer_readonly", false);
      this.expanded = [];
      this.posa_offers = [];
      evntBus.$emit("set_pos_coupons", []);
      this.posa_coupons = [];
      this.return_doc = "";
      const doc = this.get_invoice_doc();
      if (doc.name) {
        old_invoice = this.update_invoice(doc);
      } else {
        if (doc.items.length) {
          old_invoice = this.update_invoice(doc);
        }
      }
      if (!data.name && !data.is_return) {
        this.items = [];
        this.customer = this.pos_profile.customer;
        this.invoice_doc = "";
        this.discount_amount = 0;
        this.additional_discount_percentage = 0;
        this.invoiceType = this.pos_profile.posa_default_sales_order
          ? "Order"
          : "Invoice";
        this.invoiceTypes = ["Invoice", "Order"];
      } else {
        if (data.is_return) {
          evntBus.$emit("set_customer_readonly", true);
          this.invoiceType = "Return";
          this.invoiceTypes = ["Return"];
        }
        this.invoice_doc = data;
        this.items = data.items;
        this.update_items_details(this.items);
        this.posa_offers = data.posa_offers || [];
        this.items.forEach((item) => {
          if (!item.posa_row_id) {
            item.posa_row_id = this.makeid(20);
          }
          if (item.batch_no) {
            this.set_batch_qty(item, item.batch_no);
          }
        });
        this.customer = data.customer;
        this.posting_date = data.posting_date || frappe.datetime.nowdate();
        this.discount_amount = data.discount_amount;
        this.custom_table_number = data.custom_table_number;
        this.custom_so_type = data.custom_so_type;
        this.additional_discount_percentage =
          data.additional_discount_percentage;
        this.items.forEach((item) => {
          if (item.serial_no) {
            item.serial_no_selected = [];
            const serial_list = item.serial_no.split("\n");
            serial_list.forEach((element) => {
              if (element.length) {
                item.serial_no_selected.push(element);
              }
            });
            item.serial_no_selected_count = item.serial_no_selected.length;
          }
        });
      }
      return old_invoice;
    },

    async new_order(data = {}) {
      let old_invoice = null;
      evntBus.$emit("set_customer_readonly", false);
      this.expanded = [];
      this.posa_offers = [];
      evntBus.$emit("set_pos_coupons", []);
      this.posa_coupons = [];
      this.return_doc = "";
      if (!data.name && !data.is_return) {
        this.items = [];
        this.customer = this.pos_profile.customer;
        this.invoice_doc = "";
        this.discount_amount = 0;
        this.additional_discount_percentage = 0;
        this.invoiceType = "Invoice";
        this.invoiceTypes = ["Invoice", "Order"];
      } else {
        if (data.is_return) {
          evntBus.$emit("set_customer_readonly", true);
          this.invoiceType = "Return";
          this.invoiceTypes = ["Return"];
        }
        this.invoice_doc = data;
        this.items = data.items;
        this.update_items_details(this.items);
        this.posa_offers = data.posa_offers || [];
        this.items.forEach((item) => {
          if (!item.posa_row_id) {
            item.posa_row_id = this.makeid(20);
          }
          if (item.batch_no) {
            this.set_batch_qty(item, item.batch_no);
          }
        });
        this.customer = data.customer;
        this.posting_date = data.posting_date || frappe.datetime.nowdate();
        this.discount_amount = data.discount_amount;
        this.additional_discount_percentage =
          data.additional_discount_percentage;
        this.items.forEach((item) => {
          if (item.serial_no) {
            item.serial_no_selected = [];
            const serial_list = item.serial_no.split("\n");
            serial_list.forEach((element) => {
              if (element.length) {
                item.serial_no_selected.push(element);
              }
            });
            item.serial_no_selected_count = item.serial_no_selected.length;
          }
        });
      }
      return old_invoice;
    },

    get_invoice_doc() {
      let doc = {};
      if (this.invoice_doc.name) {
        doc = { ...this.invoice_doc };
      }
      doc.doctype = "Sales Invoice";
      doc.is_pos = 1;
      doc.ignore_pricing_rule = 1;
      doc.company = doc.company || this.pos_profile.company;
      doc.pos_profile =
        this.pos_profile.name == `Call Center`
          ? this.branch
          : this.pos_profile.name;
      doc.pos_profile = doc.pos_profile || this.pos_profile.name;
      doc.price_list = this.sales_person;
      doc.selling_price_list = this.sales_person;
      doc.campaign = doc.campaign || this.pos_profile.campaign;
      doc.currency = doc.currency || this.pos_profile.currency;
      doc.naming_series = doc.naming_series || this.pos_profile.naming_series;
      doc.customer = this.customer;
      doc.items = this.get_invoice_items();
      doc.total = this.subtotal;
      doc.discount_amount = flt(this.discount_amount);
      doc.additional_discount_percentage = flt(
        this.additional_discount_percentage,
      );
      doc.posa_pos_opening_shift =
        (this.pos_opening_shift && this.pos_opening_shift.name) || null;
      doc.payments = this.get_payments();
      doc.taxes = [];
      doc.is_return = this.invoice_doc.is_return;
      doc.return_against = this.invoice_doc.return_against;
      doc.posa_offers = this.posa_offers;
      doc.posa_coupons = this.posa_coupons;
      doc.posa_delivery_charges = this.selcted_delivery_charges
        ? this.selcted_delivery_charges.name
        : null;
      doc.posa_delivery_charges_rate = this.delivery_charges_rate || 0;
      doc.shipping_address_name = this.shipping_address_name || null;
      doc.posa_delivery_date = frappe.datetime.nowdate();
      doc.selected_packed_items = this.get_packed_items();
      doc.packed_items = this.get_packed_items();
      doc.posting_date = this.posting_date;
      doc.pickup = this.pickup;
      doc.branch = this.branch;
      doc.custom_so_type = this.orderType;
      const hasTables = Array.isArray(this.table_no) && this.table_no.length;
      doc.custom_table_number = hasTables ? this.table_no[0] : null;
      const tables = [];
      if (hasTables) {
        this.table_no.forEach((el) => {
          tables.push({
            table_name: el,
          });
        });
      }
      doc.custom_numbers_of_table = tables;
      doc.sales_person = this.sales_person;
      return doc;
    },
    async get_invoice_from_order_doc() {
      let doc = {};
      if (this.invoice_doc.doctype == "Sales Order") {
        await frappe.call({
          method:
            "posawesome.posawesome.api.posapp.create_sales_invoice_from_order",
          args: {
            sales_order: this.invoice_doc.name,
          },
          // async: false,
          callback: function (r) {
            if (r.message) {
              doc = r.message;
            }
          },
        });
      } else {
        doc = this.invoice_doc;
      }
      const Items = [];
      const updatedItemsData = this.get_invoice_items();
      doc.items.forEach((item) => {
        const updatedData = updatedItemsData.find(
          (updatedItem) => updatedItem.item_code === item.item_code,
        );
        if (updatedData) {
          item.item_code = updatedData.item_code;
          item.posa_row_id = updatedData.posa_row_id;
          item.posa_offers = updatedData.posa_offers;
          item.posa_offer_applied = updatedData.posa_offer_applied;
          item.posa_is_offer = updatedData.posa_is_offer;
          item.posa_is_replace = updatedData.posa_is_replace;
          item.is_free_item = updatedData.is_free_item;
          item.qty = flt(updatedData.qty);
          item.rate = flt(updatedData.rate);
          item.uom = updatedData.uom;
          item.amount = flt(updatedData.qty) * flt(updatedData.rate);
          item.conversion_factor = updatedData.conversion_factor;
          item.serial_no = updatedData.serial_no;
          item.discount_percentage = flt(updatedData.discount_percentage);
          item.discount_amount = flt(updatedData.discount_amount);
          item.batch_no = updatedData.batch_no;
          item.posa_notes = updatedData.posa_notes;
          item.posa_delivery_date = updatedData.posa_delivery_date;
          item.price_list_rate = updatedData.price_list_rate;
          Items.push(item);
        }
      });

      doc.items = Items;
      const newItems = [...doc.items];
      const existingItemCodes = new Set(newItems.map((item) => item.item_code));
      updatedItemsData.forEach((updatedItem) => {
        if (!existingItemCodes.has(updatedItem.item_code)) {
          newItems.push(updatedItem);
        }
      });
      doc.items = newItems;
      doc.update_stock = 1;
      doc.is_pos = 1;
      doc.payments = this.get_payments();
      return doc;
    },

    get_invoice_items() {
      const items_list = [];
      this.items.forEach((item) => {
        const new_item = {
          item_code: item.item_code,
          posa_row_id: item.posa_row_id,
          posa_offers: item.posa_offers,
          posa_offer_applied: item.posa_offer_applied,
          posa_is_offer: item.posa_is_offer,
          posa_is_replace: item.posa_is_replace,
          is_free_item: item.is_free_item,
          custom_hide_print: item.custom_hide_print,
          qty: flt(item.qty),
          rate: flt(item.rate),
          uom: item.uom,
          amount: flt(item.qty) * flt(item.rate),
          conversion_factor: item.conversion_factor,
          serial_no: item.serial_no,
          discount_percentage: flt(item.discount_percentage),
          discount_amount: flt(item.discount_amount),
          batch_no: item.batch_no,
          posa_notes: item.posa_notes,
          posa_delivery_date: item.posa_delivery_date,
          price_list_rate: item.price_list_rate,
        };
        items_list.push(new_item);
      });

      return items_list;
    },

    get_order_items() {
      const items_list = [];
      this.items.forEach((item) => {
        const new_item = {
          item_code: item.item_code,
          posa_row_id: item.posa_row_id,
          posa_offers: item.posa_offers,
          posa_offer_applied: item.posa_offer_applied,
          posa_is_offer: item.posa_is_offer,
          posa_is_replace: item.posa_is_replace,
          is_free_item: item.is_free_item,
          qty: flt(item.qty),
          rate: flt(item.rate),
          uom: item.uom,
          amount: flt(item.qty) * flt(item.rate),
          conversion_factor: item.conversion_factor,
          serial_no: item.serial_no,
          discount_percentage: flt(item.discount_percentage),
          discount_amount: flt(item.discount_amount),
          batch_no: item.batch_no,
          posa_notes: item.posa_notes,
          posa_delivery_date: item.posa_delivery_date,
          price_list_rate: item.price_list_rate,
        };
        items_list.push(new_item);
      });

      return items_list;
    },

    get_payments() {
      const payments = [];
      this.pos_profile.payments.forEach((payment) => {
        if (!payment.custom_hide_from_pos)
          payments.push({
            amount: 0,
            mode_of_payment: payment.mode_of_payment,
            default: payment.default,
            custom_hide_from_pos: payment.custom_hide_from_pos,
            custom_sales_person: payment.custom_sales_person,
            account: "",
          });
      });
      return payments;
    },

    update_invoice(doc) {
      const vm = this;
      frappe.call({
        method: "posawesome.posawesome.api.posapp.update_invoice",
        args: {
          data: doc,
        },
        async: false,
        callback: function (r) {
          if (r.message) {
            vm.invoice_doc = r.message;
            // Customize
            this.si_bundel_items = [];
          }
        },
      });
      return this.invoice_doc;
    },
    create_complaint() {
      const vm = this;
      this.create_dialog_complaint = false;
      frappe.call({
        method: "posawesome.posawesome.api.posapp.create_complaint",
        args: {
          complaint_details: vm.complaint,
          customer: vm.customer_info.name,
          complaintType: vm.complaintType,
          need_action: vm.need_action,
          branch: vm.branch,
        },
        callback: function (r) {
          if (r.message) {
            evntBus.$emit("show_mesage", {
              text: __(`The Complaint has been created successfully`),
              color: "success",
            });
            vm.customer_info.no_compliant += 1;
            vm.complaint = null;
          }
        },
      });
    },
    update_invoice_from_order(doc) {
      const vm = this;
      frappe.call({
        method: "posawesome.posawesome.api.posapp.update_invoice_from_order",
        args: {
          data: doc,
        },
        async: false,
        callback: function (r) {
          if (r.message) {
            vm.invoice_doc = r.message;
          }
        },
      });
      return this.invoice_doc;
    },

    process_invoice() {
      const doc = this.get_invoice_doc();
      if (doc.name) {
        return this.update_invoice(doc);
      } else {
        return this.update_invoice(doc);
      }
    },

    async process_invoice_from_order() {
      const doc = await this.get_invoice_from_order_doc();
      var up_invoice;
      if (doc.name) {
        up_invoice = await this.update_invoice_from_order(doc);
        return up_invoice;
      } else {
        return this.update_invoice_from_order(doc);
      }
    },

    async show_payment() {
      let validate_pass = true;
      this.items.forEach((item) => {
        if (
          this.customer_info.posa_discount &&
          (item.discount_percentage > this.customer_info.posa_discount ||
            flt(item.discount_percentage) +
              flt(this.additional_discount_percentage) >
              this.customer_info.posa_discount)
        ) {
          validate_pass = false;
        }
      });
      if (!validate_pass) {
        evntBus.$emit("show_mesage", {
          text: __(`Maximum discount for Customer is {0}%`, [
            this.customer_info.posa_discount,
          ]),
          color: "error",
        });
        return;
      }
      evntBus.$emit("send_invoice_doc_payment", this.invoice_doc);

      if (!this.customer) {
        evntBus.$emit("show_mesage", {
          text: __(`There is no Customer !`),
          color: "error",
        });
        return;
      }
      if (!this.items.length) {
        evntBus.$emit("show_mesage", {
          text: __(`There is no Items !`),
          color: "error",
        });
        return;
      }
      if (!this.validate()) {
        return;
      }
      if (this.invoice_doc.doctype == "Sales Order") {
        evntBus.$emit("show_payment", "true");
        const invoice_doc = await this.process_invoice_from_order();
        evntBus.$emit("send_invoice_doc_payment", invoice_doc);
      } else if (this.invoice_doc.doctype == "Sales Invoice") {
        const sales_invoice_item = this.invoice_doc.items[0];
        var sales_invoice_item_doc = {};
        frappe.call({
          method:
            "posawesome.posawesome.api.posapp.get_sales_invoice_child_table",
          args: {
            sales_invoice: this.invoice_doc.name,
            sales_invoice_item: sales_invoice_item.name,
          },
          async: false,
          callback: function (r) {
            if (r.message) {
              sales_invoice_item_doc = r.message;
            }
          },
        });
        if (sales_invoice_item_doc.sales_order) {
          evntBus.$emit("show_payment", "true");
          const invoice_doc = await this.process_invoice_from_order();
          evntBus.$emit("send_invoice_doc_payment", invoice_doc);
        } else {
          evntBus.$emit("show_payment", "true");
          const invoice_doc = this.process_invoice();
          evntBus.$emit("send_invoice_doc_payment", invoice_doc);
        }
      } else {
        evntBus.$emit("show_payment", "true");
        const invoice_doc = this.process_invoice();
        evntBus.$emit("send_invoice_doc_payment", invoice_doc);
      }
      evntBus.$emit("set_sales_person_in_payment", this.sales_person);
    },
    OpeningDialog() {
      self.isBundle = 1;
    },
    validate() {
      let value = true;
      this.items.forEach((item) => {
        if (
          this.pos_profile.posa_max_discount_allowed &&
          !item.posa_offer_applied
        ) {
          if (item.discount_amount && this.flt(item.discount_amount) > 0) {
            // calc discount percentage
            const discount_percentage =
              (this.flt(item.discount_amount) * 100) /
              this.flt(item.price_list_rate);
            if (
              discount_percentage > this.pos_profile.posa_max_discount_allowed
            ) {
              evntBus.$emit("show_mesage", {
                text: __(
                  `Discount percentage for item '{0}' cannot be greater than {1}%`,
                  [item.item_name, this.pos_profile.posa_max_discount_allowed],
                ),
                color: "error",
              });
              value = false;
            }
          }
        }
        if (this.stock_settings.allow_negative_stock != 1) {
          if (
            this.invoiceType == "Invoice" &&
            ((item.is_stock_item && item.stock_qty && !item.actual_qty) ||
              (item.is_stock_item && item.stock_qty > item.actual_qty))
          ) {
            evntBus.$emit("show_mesage", {
              text: __(
                `The existing quantity '{0}' for item '{1}' is not enough`,
                [item.actual_qty, item.item_name],
              ),
              color: "error",
            });
            value = false;
          }
        }
        if (item.qty == 0) {
          evntBus.$emit("show_mesage", {
            text: __(`Quantity for item '{0}' cannot be Zero (0)`, [
              item.item_name,
            ]),
            color: "error",
          });
          value = false;
        }
        if (
          item.max_discount > 0 &&
          item.discount_percentage > item.max_discount
        ) {
          evntBus.$emit("show_mesage", {
            text: __(`Maximum discount for Item {0} is {1}%`, [
              item.item_name,
              item.max_discount,
            ]),
            color: "error",
          });
          value = false;
        }
        if (item.has_serial_no) {
          if (
            !this.invoice_doc.is_return &&
            (!item.serial_no_selected ||
              item.stock_qty != item.serial_no_selected.length)
          ) {
            evntBus.$emit("show_mesage", {
              text: __(`Selected serial numbers of item {0} is incorrect`, [
                item.item_name,
              ]),
              color: "error",
            });
            value = false;
          }
        }
        if (item.has_batch_no) {
          if (item.stock_qty > item.actual_batch_qty) {
            evntBus.$emit("show_mesage", {
              text: __(
                `The existing batch quantity of item {0} is not enough`,
                [item.item_name],
              ),
              color: "error",
            });
            value = false;
          }
        }
        if (this.pos_profile.posa_allow_user_to_edit_additional_discount) {
          const clac_percentage = (this.discount_amount / this.Total) * 100;
          if (clac_percentage > this.pos_profile.posa_max_discount_allowed) {
            evntBus.$emit("show_mesage", {
              text: __(`The discount should not be higher than {0}%`, [
                this.pos_profile.posa_max_discount_allowed,
              ]),
              color: "error",
            });
            value = false;
          }
        }
        if (this.invoice_doc.is_return) {
          if (this.subtotal >= 0) {
            evntBus.$emit("show_mesage", {
              text: __(`Return Invoice Total Not Correct`),
              color: "error",
            });
            value = false;
            return value;
          }
          if (Math.abs(this.subtotal) > Math.abs(this.return_doc.total)) {
            evntBus.$emit("show_mesage", {
              text: __(`Return Invoice Total should not be higher than {0}`, [
                this.return_doc.total,
              ]),
              color: "error",
            });
            value = false;
            return value;
          }
          this.items.forEach((item) => {
            const return_item = this.return_doc.items.find(
              (element) => element.item_code == item.item_code,
            );

            if (!return_item) {
              evntBus.$emit("show_mesage", {
                text: __(
                  `The item {0} cannot be returned because it is not in the invoice {1}`,
                  [item.item_name, this.return_doc.name],
                ),
                color: "error",
              });
              value = false;
              return value;
            } else if (
              Math.abs(item.qty) > Math.abs(return_item.qty) ||
              Math.abs(item.qty) == 0
            ) {
              evntBus.$emit("show_mesage", {
                text: __(`The QTY of the item {0} cannot be greater than {1}`, [
                  item.item_name,
                  return_item.qty,
                ]),
                color: "error",
              });
              value = false;
              return value;
            }
          });
        }
      });
      return value;
    },

    get_draft_invoices() {
      const vm = this;
      frappe.call({
        method: "posawesome.posawesome.api.posapp.get_draft_invoices",
        args: {
          pos_opening_shift: this.pos_opening_shift.name,
        },
        async: false,
        callback: function (r) {
          if (r.message) {
            evntBus.$emit("open_drafts", r.message);
          }
        },
      });
    },

    get_draft_orders() {
      const vm = this;
      frappe.call({
        method: "posawesome.posawesome.api.posapp.search_orders",
        args: {
          company: this.pos_profile.company,
          currency: this.pos_profile.currency,
        },
        async: false,
        callback: function (r) {
          if (r.message) {
            evntBus.$emit("open_orders", r.message);
          }
        },
      });
    },

    open_returns() {
      evntBus.$emit("open_returns", this.pos_profile.company);
    },

    close_payments() {
      evntBus.$emit("show_payment", "false");
    },

    update_items_details(items) {
      if (!items.length > 0) {
        return;
      }
      const vm = this;
      if (!vm.pos_profile) return;
      frappe.call({
        method: "posawesome.posawesome.api.posapp.get_items_details",
        async: false,
        args: {
          pos_profile: vm.pos_profile,
          items_data: items,
        },
        callback: function (r) {
          if (r.message) {
            items.forEach((item) => {
              const updated_item = r.message.find(
                (element) => element.posa_row_id == item.posa_row_id,
              );
              item.actual_qty = updated_item.actual_qty;
              item.serial_no_data = updated_item.serial_no_data;
              item.batch_no_data = updated_item.batch_no_data;
              item.item_uoms = updated_item.item_uoms;
              item.has_batch_no = updated_item.has_batch_no;
              item.has_serial_no = updated_item.has_serial_no;
            });
          }
        },
      });
    },

    update_item_detail(item) {
      if (!item.item_code || this.invoice_doc.is_return) {
        return;
      }
      const vm = this;
      frappe.call({
        method: "posawesome.posawesome.api.posapp.get_item_detail",
        args: {
          warehouse: this.pos_profile.warehouse,
          doc: this.get_invoice_doc(),
          price_list: item.price_list,
          item: {
            item_code: item.item_code,
            customer: this.customer,
            doctype: "Sales Invoice",
            name: "New Sales Invoice 1",
            company: this.pos_profile.company,
            conversion_rate: 1,
            qty: item.qty,
            price_list_rate: item.price_list_rate,
            child_docname: "New Sales Invoice Item 1",
            cost_center: this.pos_profile.cost_center,
            currency: this.pos_profile.currency,
            // plc_conversion_rate: 1,
            pos_profile: this.pos_profile.name,
            uom: item.uom,
            tax_category: "",
            transaction_type: "selling",
            update_stock: this.pos_profile.update_stock,
            price_list: item.price_list
              ? item.price_list
              : this.get_price_list(),
            has_batch_no: item.has_batch_no,
            serial_no: item.serial_no,
            batch_no: item.batch_no,
            is_stock_item: item.is_stock_item,
          },
        },
        callback: function (r) {
          if (r.message) {
            const data = r.message;
            if (data.batch_no_data) {
              item.batch_no_data = data.batch_no_data;
            }
            if (
              item.has_batch_no &&
              vm.pos_profile.posa_auto_set_batch &&
              !item.batch_no &&
              data.batch_no_data
            ) {
              item.batch_no_data = data.batch_no_data;
              vm.set_batch_qty(item, item.batch_no, false);
            }
            if (data.has_pricing_rule) {
            } else if (
              vm.pos_profile.posa_apply_customer_discount &&
              vm.customer_info.posa_discount > 0 &&
              vm.customer_info.posa_discount <= 100
            ) {
              if (
                item.posa_is_offer == 0 &&
                !item.posa_is_replace &&
                item.posa_offer_applied == 0
              ) {
                if (item.max_discount > 0) {
                  item.discount_percentage =
                    item.max_discount < vm.customer_info.posa_discount
                      ? item.max_discount
                      : vm.customer_info.posa_discount;
                } else {
                  item.discount_percentage = vm.customer_info.posa_discount;
                }
              }
            }
            if (!item.batch_price) {
              if (
                !item.is_free_item &&
                !item.posa_is_offer &&
                !item.posa_is_replace
              ) {
                item.price_list_rate = data.price_list_rate;
              }
            }
            item.last_purchase_rate = data.last_purchase_rate;
            item.projected_qty = data.projected_qty;
            item.reserved_qty = data.reserved_qty;
            item.conversion_factor = data.conversion_factor;
            item.stock_qty = data.stock_qty;
            item.actual_qty = data.actual_qty;
            item.stock_uom = data.stock_uom;
            ((item.has_serial_no = data.has_serial_no),
              (item.has_batch_no = data.has_batch_no),
              vm.calc_item_price(item));
          }
        },
      });
    },

    fetch_customer_details() {
      const vm = this;
      if (this.customer) {
        frappe.call({
          method: "posawesome.posawesome.api.posapp.get_customer_info",
          args: {
            customer: vm.customer,
          },
          async: false,
          callback: (r) => {
            const message = r.message;
            if (!r.exc) {
              vm.customer_info = {
                ...message,
              };
              if (
                vm.customer_info.vip == 1 ||
                vm.customer_info.black_list == 1
              ) {
                vm.information_dialog = true;
              }
            }
            vm.update_price_list();
          },
        });
      }
    },

    get_price_list() {
      let price_list = this.pos_profile.selling_price_list;
      if (this.customer_info && this.pos_profile) {
        const { customer_price_list, customer_group_price_list } =
          this.customer_info;
        const pos_price_list = this.pos_profile.selling_price_list;
        if (customer_price_list && customer_price_list != pos_price_list) {
          price_list = customer_price_list;
        } else if (
          customer_group_price_list &&
          customer_group_price_list != pos_price_list
        ) {
          price_list = customer_group_price_list;
        }
      }
      return price_list;
    },

    update_price_list() {
      let price_list = this.get_price_list();
      if (price_list == this.pos_profile.selling_price_list) {
        price_list = null;
      }
      evntBus.$emit("update_customer_price_list", price_list);
    },
    update_discount_umount() {
      const value = flt(this.additional_discount_percentage);
      if (value >= -100 && value <= 100) {
        this.discount_amount = (this.Total * value) / 100;
      } else {
        this.additional_discount_percentage = 0;
        this.discount_amount = 0;
      }
    },

    calc_prices(item, value, $event) {
      if (event.target.id === "rate") {
        item.discount_percentage = 0;
        if (value < item.price_list_rate) {
          item.discount_amount = this.flt(
            this.flt(item.price_list_rate) - flt(value),
            this.currency_precision,
          );
        } else if (value < 0) {
          item.rate = item.price_list_rate;
          item.discount_amount = 0;
        } else if (value > item.price_list_rate) {
          item.discount_amount = 0;
        }
      } else if (event.target.id === "discount_amount") {
        if (value < 0) {
          item.discount_amount = 0;
          item.discount_percentage = 0;
        } else {
          item.rate = flt(item.price_list_rate) - flt(value);
          item.discount_percentage = 0;
        }
      } else if (event.target.id === "discount_percentage") {
        if (value < 0) {
          item.discount_amount = 0;
          item.discount_percentage = 0;
        } else {
          item.rate = this.flt(
            flt(item.price_list_rate) -
              (flt(item.price_list_rate) * flt(value)) / 100,
            this.currency_precision,
          );
          item.discount_amount = this.flt(
            flt(item.price_list_rate) - flt(+item.rate),
            this.currency_precision,
          );
        }
      }
    },

    calc_item_price(item) {
      if (!item.posa_offer_applied) {
        if (item.price_list_rate) {
          item.rate = item.price_list_rate;
        }
      }
      if (item.discount_percentage) {
        item.rate =
          flt(item.price_list_rate) -
          (flt(item.price_list_rate) * flt(item.discount_percentage)) / 100;
        item.discount_amount = this.flt(
          flt(item.price_list_rate) - flt(item.rate),
          this.currency_precision,
        );
      } else if (item.discount_amount) {
        item.rate = this.flt(
          flt(item.price_list_rate) - flt(item.discount_amount),
          this.currency_precision,
        );
      }
    },

    calc_uom(item, value) {
      const new_uom = item.item_uoms.find((element) => element.uom == value);
      item.conversion_factor = new_uom.conversion_factor;
      if (!item.posa_offer_applied) {
        item.discount_amount = 0;
        item.discount_percentage = 0;
      }
      if (item.batch_price) {
        item.price_list_rate = item.batch_price * new_uom.conversion_factor;
      }
      this.update_item_detail(item);
    },

    calc_stock_qty(item, value) {
      item.stock_qty = item.conversion_factor * value;
    },

    set_serial_no(item) {
      if (!item.has_serial_no) return;
      item.serial_no = "";
      item.serial_no_selected.forEach((element) => {
        item.serial_no += element + "\n";
      });
      item.serial_no_selected_count = item.serial_no_selected.length;
      if (item.serial_no_selected_count != item.stock_qty) {
        item.qty = item.serial_no_selected_count;
        this.calc_stock_qty(item, item.qty);
        this.$forceUpdate();
      }
    },

    set_batch_qty(item, value, update = true) {
      const existing_items = this.items.filter(
        (element) =>
          element.item_code == item.item_code &&
          element.posa_row_id != item.posa_row_id,
      );
      const used_batches = {};
      item.batch_no_data.forEach((batch) => {
        used_batches[batch.batch_no] = {
          ...batch,
          used_qty: 0,
          remaining_qty: batch.batch_qty,
        };
        existing_items.forEach((element) => {
          if (element.batch_no && element.batch_no == batch.batch_no) {
            used_batches[batch.batch_no].used_qty += element.qty;
            used_batches[batch.batch_no].remaining_qty -= element.qty;
            used_batches[batch.batch_no].batch_qty -= element.qty;
          }
        });
      });

      // set item batch_no based on:
      // 1. if batch has expiry_date we should use the batch with the nearest expiry_date
      // 2. if batch has no expiry_date we should use the batch with the earliest manufacturing_date
      // 3. we should not use batch with remaining_qty = 0
      // 4. we should the highest remaining_qty
      const batch_no_data = Object.values(used_batches)
        .filter((batch) => batch.remaining_qty > 0)
        .sort((a, b) => {
          if (a.expiry_date && b.expiry_date) {
            return a.expiry_date - b.expiry_date;
          } else if (a.expiry_date) {
            return -1;
          } else if (b.expiry_date) {
            return 1;
          } else if (a.manufacturing_date && b.manufacturing_date) {
            return a.manufacturing_date - b.manufacturing_date;
          } else if (a.manufacturing_date) {
            return -1;
          } else if (b.manufacturing_date) {
            return 1;
          } else {
            return b.remaining_qty - a.remaining_qty;
          }
        });
      if (batch_no_data.length > 0) {
        let batch_to_use = null;
        if (value) {
          batch_to_use = batch_no_data.find((batch) => batch.batch_no == value);
        }
        if (!batch_to_use) {
          batch_to_use = batch_no_data[0];
        }
        item.batch_no = batch_to_use.batch_no;
        item.actual_batch_qty = batch_to_use.batch_qty;
        item.batch_no_expiry_date = batch_to_use.expiry_date;
        if (batch_to_use.batch_price) {
          item.batch_price = batch_to_use.batch_price;
          item.price_list_rate = batch_to_use.batch_price;
          item.rate = batch_to_use.batch_price;
        } else if (update) {
          item.batch_price = null;
          this.update_item_detail(item);
        }
      } else {
        item.batch_no = null;
        item.actual_batch_qty = null;
        item.batch_no_expiry_date = null;
        item.batch_price = null;
      }
      // update item batch_no_data from batch_no_data
      item.batch_no_data = batch_no_data;
    },

    shortOpenPayment(e) {
      if (e.key === "s" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        this.show_payment();
      }
    },

    shortDeleteFirstItem(e) {
      if (e.key === "d" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        this.remove_item(this.items[0]);
      }
    },

    shortOpenFirstItem(e) {
      if (e.key === "a" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        this.expanded = [];
        this.expanded.push(this.items[0]);
      }
    },

    shortSelectDiscount(e) {
      if (e.key === "z" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        this.$refs.discount.focus();
      }
    },

    makeid(length) {
      let result = "";
      const characters = "abcdefghijklmnopqrstuvwxyz0123456789";
      const charactersLength = characters.length;
      for (var i = 0; i < length; i++) {
        result += characters.charAt(
          Math.floor(Math.random() * charactersLength),
        );
      }
      return result;
    },

    checkOfferIsAppley(item, offer) {
      let applied = false;
      const item_offers = JSON.parse(item.posa_offers);
      for (const row_id of item_offers) {
        const exist_offer = this.posa_offers.find((el) => row_id == el.row_id);
        if (exist_offer && exist_offer.offer_name == offer.name) {
          applied = true;
          break;
        }
      }
      return applied;
    },

    handelOffers() {
      function isCurrentTimeInRange(fromTime, toTime) {
        const now = new Date();

        // Create Date objects for fromTime and toTime (using today's date)
        const from = new Date(now.toDateString() + " " + fromTime);
        const to = new Date(now.toDateString() + " " + toTime);
        console.log(from, to, now);
        return now >= from && now <= to;
      }
      const offers = [];
      this.posOffers.forEach((offer) => {
        let is_apply_pos_offer = false;
        if (offer.days.length == 0) {
          is_apply_pos_offer = true;
          if (offer.from_time && offer.to_time) {
            if (!isCurrentTimeInRange(offer.from_time, offer.to_time)) {
              is_apply_pos_offer = false;
            }
          }
        } else {
          const today = new Date().getDay();
          console.log("today,", today);
          if (offer.days.includes(today)) {
            is_apply_pos_offer = true;
            if (offer.from_time && offer.to_time) {
              console.log(
                !isCurrentTimeInRange(offer.from_time, offer.to_time),
                isCurrentTimeInRange(offer.from_time, offer.to_time),
              );
              if (!isCurrentTimeInRange(offer.from_time, offer.to_time)) {
                is_apply_pos_offer = false;
              }
            }
          }
        }
        if (is_apply_pos_offer && offer.price_list == this.sales_person) {
          if (offer.apply_on === "Item Code") {
            const itemOffer = this.getItemOffer(offer);
            if (itemOffer) {
              offers.push(itemOffer);
            }
          } else if (offer.apply_on === "Item Group") {
            const groupOffer = this.getGroupOffer(offer);
            if (groupOffer) {
              offers.push(groupOffer);
            }
          } else if (offer.apply_on === "Brand") {
            const brandOffer = this.getBrandOffer(offer);
            if (brandOffer) {
              offers.push(brandOffer);
            }
          } else if (offer.apply_on === "Transaction") {
            const transactionOffer = this.getTransactionOffer(offer);
            if (transactionOffer) {
              offers.push(transactionOffer);
            }
          }
        }
      });

      this.setItemGiveOffer(offers);
      this.updatePosOffers(offers);
    },

    setItemGiveOffer(offers) {
      // Set item give offer for replace
      offers.forEach((offer) => {
        if (
          offer.apply_on == "Item Code" &&
          offer.apply_type == "Item Code" &&
          offer.replace_item
        ) {
          offer.give_item = offer.item;
          offer.apply_item_code = offer.item;
        } else if (
          offer.apply_on == "Item Group" &&
          offer.apply_type == "Item Group" &&
          offer.replace_cheapest_item
        ) {
          const offerItemCode = this.getCheapestItem(offer).item_code;
          offer.give_item = offerItemCode;
          offer.apply_item_code = offerItemCode;
        }
      });
    },

    getCheapestItem(offer) {
      let itemsRowID;
      if (typeof offer.items === "string") {
        itemsRowID = JSON.parse(offer.items);
      } else {
        itemsRowID = offer.items;
      }
      const itemsList = [];
      itemsRowID.forEach((row_id) => {
        itemsList.push(this.getItemFromRowID(row_id));
      });
      const result = itemsList.reduce(function (res, obj) {
        return !obj.posa_is_replace &&
          !obj.posa_is_offer &&
          obj.price_list_rate < res.price_list_rate
          ? obj
          : res;
      });
      return result;
    },

    getItemFromRowID(row_id) {
      const item = this.items.find((el) => el.posa_row_id == row_id);
      return item;
    },

    checkQtyAnountOffer(offer, qty, amount) {
      let min_qty = false;
      let max_qty = false;
      let min_amt = false;
      let max_amt = false;
      const applys = [];

      if (offer.min_qty || offer.min_qty == 0) {
        if (qty >= offer.min_qty) {
          min_qty = true;
        }
        applys.push(min_qty);
      }

      if (offer.max_qty > 0) {
        if (qty <= offer.max_qty) {
          max_qty = true;
        }
        applys.push(max_qty);
      }

      if (offer.min_amt > 0) {
        if (amount >= offer.min_amt) {
          min_amt = true;
        }
        applys.push(min_amt);
      }

      if (offer.max_amt > 0) {
        if (amount <= offer.max_amt) {
          max_amt = true;
        }
        applys.push(max_amt);
      }
      let apply = false;
      if (!applys.includes(false)) {
        apply = true;
      }
      const res = {
        apply: apply,
        conditions: { min_qty, max_qty, min_amt, max_amt },
      };
      return res;
    },

    checkOfferCoupon(offer) {
      if (offer.coupon_based) {
        const coupon = this.posa_coupons.find(
          (el) => offer.name == el.pos_offer,
        );
        if (coupon) {
          offer.coupon = coupon.coupon;
          return true;
        } else {
          return false;
        }
      } else {
        offer.coupon = null;
        return true;
      }
    },

    getItemOffer(offer) {
      let apply_offer = null;
      if (offer.apply_on === "Item Code") {
        if (this.checkOfferCoupon(offer)) {
          this.items.forEach((item) => {
            if (!item.posa_is_offer && item.item_code === offer.item) {
              const items = [];
              if (
                offer.offer === "Item Price" &&
                item.posa_offer_applied &&
                !this.checkOfferIsAppley(item, offer)
              ) {
              } else {
                const res = this.checkQtyAnountOffer(
                  offer,
                  item.stock_qty,
                  item.stock_qty * item.price_list_rate,
                );
                if (res.apply) {
                  items.push(item.posa_row_id);
                  offer.items = items;
                  apply_offer = offer;
                }
              }
            }
          });
        }
      }
      return apply_offer;
    },

    getGroupOffer(offer) {
      let apply_offer = null;
      if (offer.apply_on === "Item Group") {
        if (this.checkOfferCoupon(offer)) {
          const items = [];
          let total_count = 0;
          let total_amount = 0;
          this.items.forEach((item) => {
            if (!item.posa_is_offer && item.item_group === offer.item_group) {
              if (
                offer.offer === "Item Price" &&
                item.posa_offer_applied &&
                !this.checkOfferIsAppley(item, offer)
              ) {
              } else {
                total_count += item.stock_qty;
                total_amount += item.stock_qty * item.price_list_rate;
                items.push(item.posa_row_id);
              }
            }
          });
          if (total_count || total_amount) {
            const res = this.checkQtyAnountOffer(
              offer,
              total_count,
              total_amount,
            );
            if (res.apply) {
              offer.items = items;
              apply_offer = offer;
            }
          }
        }
      }
      return apply_offer;
    },

    getBrandOffer(offer) {
      let apply_offer = null;
      if (offer.apply_on === "Brand") {
        if (this.checkOfferCoupon(offer)) {
          const items = [];
          let total_count = 0;
          let total_amount = 0;
          this.items.forEach((item) => {
            if (!item.posa_is_offer && item.brand === offer.brand) {
              if (
                offer.offer === "Item Price" &&
                item.posa_offer_applied &&
                !this.checkOfferIsAppley(item, offer)
              ) {
              } else {
                total_count += item.stock_qty;
                total_amount += item.stock_qty * item.price_list_rate;
                items.push(item.posa_row_id);
              }
            }
          });
          if (total_count || total_amount) {
            const res = this.checkQtyAnountOffer(
              offer,
              total_count,
              total_amount,
            );
            if (res.apply) {
              offer.items = items;
              apply_offer = offer;
            }
          }
        }
      }
      return apply_offer;
    },
    getTransactionOffer(offer) {
      let apply_offer = null;
      if (offer.apply_on === "Transaction") {
        if (this.checkOfferCoupon(offer)) {
          let total_qty = 0;
          this.items.forEach((item) => {
            if (!item.posa_is_offer && !item.posa_is_replace) {
              total_qty += item.stock_qty;
            }
          });
          const items = [];
          const total_count = total_qty;
          const total_amount = this.Total;
          if (total_count || total_amount) {
            const res = this.checkQtyAnountOffer(
              offer,
              total_count,
              total_amount,
            );
            if (res.apply) {
              this.items.forEach((item) => {
                items.push(item.posa_row_id);
              });
              offer.items = items;
              apply_offer = offer;
            }
          }
        }
      }
      return apply_offer;
    },

    updatePosOffers(offers) {
      evntBus.$emit("update_pos_offers", offers);
    },

    updateInvoiceOffers(offers) {
      this.posa_offers.forEach((invoiceOffer) => {
        const existOffer = offers.find(
          (offer) => invoiceOffer.row_id == offer.row_id,
        );
        if (!existOffer) {
          this.removeApplyOffer(invoiceOffer);
        }
      });
      offers.forEach((offer) => {
        const existOffer = this.posa_offers.find(
          (invoiceOffer) => invoiceOffer.row_id == offer.row_id,
        );
        if (existOffer) {
          existOffer.items = JSON.stringify(offer.items);
          if (
            existOffer.offer === "Give Product" &&
            existOffer.give_item &&
            existOffer.give_item != offer.give_item
          ) {
            const item_to_remove = this.items.find(
              (item) => item.posa_row_id == existOffer.give_item_row_id,
            );
            if (item_to_remove) {
              const updated_item_offers = offer.items.filter(
                (row_id) => row_id != item_to_remove.posa_row_id,
              );
              offer.items = updated_item_offers;
              this.remove_item(item_to_remove);
              existOffer.give_item_row_id = null;
              existOffer.give_item = null;
            }
            const newItemOffer = this.ApplyOnGiveProduct(offer);
            if (offer.replace_cheapest_item) {
              const cheapestItem = this.getCheapestItem(offer);
              const oldBaseItem = this.items.find(
                (el) => el.posa_row_id == item_to_remove.posa_is_replace,
              );
              newItemOffer.qty = item_to_remove.qty;
              if (oldBaseItem && !oldBaseItem.posa_is_replace) {
                oldBaseItem.qty += item_to_remove.qty;
              } else {
                const restoredItem = this.ApplyOnGiveProduct(
                  {
                    given_qty: item_to_remove.qty,
                  },
                  item_to_remove.item_code,
                );
                restoredItem.posa_is_offer = 0;
                this.items.unshift(restoredItem);
              }
              newItemOffer.posa_is_offer = 0;
              newItemOffer.posa_is_replace = cheapestItem.posa_row_id;
              const diffQty = cheapestItem.qty - newItemOffer.qty;
              if (diffQty <= 0) {
                newItemOffer.qty += diffQty;
                this.remove_item(cheapestItem);
                newItemOffer.posa_row_id = cheapestItem.posa_row_id;
                newItemOffer.posa_is_replace = newItemOffer.posa_row_id;
              } else {
                cheapestItem.qty = diffQty;
              }
            }
            this.items.unshift(newItemOffer);
            existOffer.give_item_row_id = newItemOffer.posa_row_id;
            existOffer.give_item = newItemOffer.item_code;
          } else if (
            existOffer.offer === "Give Product" &&
            existOffer.give_item &&
            existOffer.give_item == offer.give_item &&
            (offer.replace_item || offer.replace_cheapest_item)
          ) {
            this.$nextTick(function () {
              const offerItem = this.getItemFromRowID(
                existOffer.give_item_row_id,
              );
              const diff = offer.given_qty - offerItem.qty;
              if (diff > 0) {
                const itemsRowID = JSON.parse(existOffer.items);
                const itemsList = [];
                itemsRowID.forEach((row_id) => {
                  itemsList.push(this.getItemFromRowID(row_id));
                });
                const existItem = itemsList.find(
                  (el) =>
                    el.item_code == offerItem.item_code &&
                    el.posa_is_replace != offerItem.posa_row_id,
                );
                if (existItem) {
                  const diffExistQty = existItem.qty - diff;
                  if (diffExistQty > 0) {
                    offerItem.qty += diff;
                    existItem.qty -= diff;
                  } else {
                    offerItem.qty += existItem.qty;
                    this.remove_item(existItem);
                  }
                }
              }
            });
          } else if (existOffer.offer === "Item Price") {
            this.ApplyOnPrice(offer);
          } else if (existOffer.offer === "Grand Total") {
            this.ApplyOnTotal(offer);
          }
          this.addOfferToItems(existOffer);
        } else {
          this.applyNewOffer(offer);
        }
      });
    },

    removeApplyOffer(invoiceOffer) {
      if (invoiceOffer.offer === "Item Price") {
        this.RemoveOnPrice(invoiceOffer);
        const index = this.posa_offers.findIndex(
          (el) => el.row_id === invoiceOffer.row_id,
        );
        this.posa_offers.splice(index, 1);
      }
      if (invoiceOffer.offer === "Give Product") {
        const item_to_remove = this.items.find(
          (item) => item.posa_row_id == invoiceOffer.give_item_row_id,
        );
        const index = this.posa_offers.findIndex(
          (el) => el.row_id === invoiceOffer.row_id,
        );
        this.posa_offers.splice(index, 1);
        this.remove_item(item_to_remove);
      }
      if (invoiceOffer.offer === "Grand Total") {
        this.RemoveOnTotal(invoiceOffer);
        const index = this.posa_offers.findIndex(
          (el) => el.row_id === invoiceOffer.row_id,
        );
        this.posa_offers.splice(index, 1);
      }
      if (invoiceOffer.offer === "Loyalty Point") {
        const index = this.posa_offers.findIndex(
          (el) => el.row_id === invoiceOffer.row_id,
        );
        this.posa_offers.splice(index, 1);
      }
      this.deleteOfferFromItems(invoiceOffer);
    },

    applyNewOffer(offer) {
      if (offer.offer === "Item Price") {
        this.ApplyOnPrice(offer);
      }
      if (offer.offer === "Give Product") {
        let itemsRowID;
        if (typeof offer.items === "string") {
          itemsRowID = JSON.parse(offer.items);
        } else {
          itemsRowID = offer.items;
        }
        if (
          offer.apply_on == "Item Code" &&
          offer.apply_type == "Item Code" &&
          offer.replace_item
        ) {
          const item = this.ApplyOnGiveProduct(offer, offer.item);
          item.posa_is_replace = itemsRowID[0];
          const baseItem = this.items.find(
            (el) => el.posa_row_id == item.posa_is_replace,
          );
          const diffQty = baseItem.qty - offer.given_qty;
          item.posa_is_offer = 0;
          if (diffQty <= 0) {
            item.qty = baseItem.qty;
            this.remove_item(baseItem);
            item.posa_row_id = item.posa_is_replace;
          } else {
            baseItem.qty = diffQty;
          }
          this.items.unshift(item);
          offer.give_item_row_id = item.posa_row_id;
        } else if (
          offer.apply_on == "Item Group" &&
          offer.apply_type == "Item Group" &&
          offer.replace_cheapest_item
        ) {
          const itemsList = [];
          itemsRowID.forEach((row_id) => {
            itemsList.push(this.getItemFromRowID(row_id));
          });
          const baseItem = itemsList.find(
            (el) => el.item_code == offer.give_item,
          );
          const item = this.ApplyOnGiveProduct(offer, offer.give_item);
          item.posa_is_offer = 0;
          item.posa_is_replace = baseItem.posa_row_id;
          const diffQty = baseItem.qty - offer.given_qty;
          if (diffQty <= 0) {
            item.qty = baseItem.qty;
            this.remove_item(baseItem);
            item.posa_row_id = item.posa_is_replace;
          } else {
            baseItem.qty = diffQty;
          }
          this.items.unshift(item);
          offer.give_item_row_id = item.posa_row_id;
        } else {
          const item = this.ApplyOnGiveProduct(offer);
          this.items.unshift(item);
          if (item) {
            offer.give_item_row_id = item.posa_row_id;
          }
        }
      }
      if (offer.offer === "Grand Total") {
        this.ApplyOnTotal(offer);
      }
      if (offer.offer === "Loyalty Point") {
        evntBus.$emit("show_mesage", {
          text: __("Loyalty Point Offer Applied"),
          color: "success",
        });
      }

      const newOffer = {
        offer_name: offer.name,
        row_id: offer.row_id,
        apply_on: offer.apply_on,
        offer: offer.offer,
        items: JSON.stringify(offer.items),
        give_item: offer.give_item,
        give_item_row_id: offer.give_item_row_id,
        offer_applied: offer.offer_applied,
        coupon_based: offer.coupon_based,
        coupon: offer.coupon,
      };
      this.posa_offers.push(newOffer);
      this.addOfferToItems(newOffer);
    },

    ApplyOnGiveProduct(offer, item_code) {
      if (!item_code) {
        item_code = offer.give_item;
      }
      const items = this.allItems;
      const item = items.find((item) => item.item_code == item_code);
      if (!item) {
        return;
      }
      const new_item = { ...item };
      new_item.qty = offer.given_qty;
      new_item.stock_qty = offer.given_qty;
      new_item.rate = offer.discount_type === "Rate" ? offer.rate : item.rate;
      new_item.discount_amount =
        offer.discount_type === "Discount Amount" ? offer.discount_amount : 0;
      new_item.discount_percentage =
        offer.discount_type === "Discount Percentage"
          ? offer.discount_percentage
          : 0;
      new_item.discount_amount_per_item = 0;
      new_item.uom = item.uom ? item.uom : item.stock_uom;
      new_item.actual_batch_qty = "";
      new_item.conversion_factor = 1;
      new_item.posa_offers = JSON.stringify([]);
      new_item.posa_offer_applied = 0;
      new_item.posa_is_offer = 1;
      new_item.posa_is_replace = null;
      new_item.posa_notes = "";
      new_item.posa_delivery_date = "";
      new_item.is_free_item =
        (offer.discount_type === "Rate" && !offer.rate) ||
        (offer.discount_type === "Discount Percentage" &&
          offer.discount_percentage == 0)
          ? 1
          : 0;
      new_item.posa_row_id = this.makeid(20);
      new_item.price_list_rate =
        (offer.discount_type === "Rate" && !offer.rate) ||
        (offer.discount_type === "Discount Percentage" &&
          offer.discount_percentage == 0)
          ? 0
          : item.rate;
      if (
        (!this.pos_profile.posa_auto_set_batch && new_item.has_batch_no) ||
        new_item.has_serial_no
      ) {
        this.expanded.push(new_item);
      }
      this.update_item_detail(new_item);
      return new_item;
    },

    ApplyOnPrice(offer) {
      this.items.forEach((item) => {
        if (offer.items.includes(item.posa_row_id)) {
          const item_offers = JSON.parse(item.posa_offers);
          if (!item_offers.includes(offer.row_id)) {
            if (offer.discount_type === "Rate") {
              item.rate = offer.rate;
            } else if (offer.discount_type === "Discount Percentage") {
              item.discount_percentage += offer.discount_percentage;
            } else if (offer.discount_type === "Discount Amount") {
              item.discount_amount += offer.discount_amount;
            }
            item.posa_offer_applied = 1;
            this.calc_item_price(item);
          }
        }
      });
    },

    RemoveOnPrice(offer) {
      this.items.forEach((item) => {
        const item_offers = JSON.parse(item.posa_offers);
        if (item_offers.includes(offer.row_id)) {
          const originalOffer = this.posOffers.find(
            (el) => el.name == offer.offer_name,
          );
          if (originalOffer) {
            if (originalOffer.discount_type === "Rate") {
              item.rate = item.price_list_rate;
            } else if (originalOffer.discount_type === "Discount Percentage") {
              item.discount_percentage -= offer.discount_percentage;
              if (!item.discount_percentage) {
                item.discount_percentage = 0;
                item.discount_amount = 0;
                item.rate = item.price_list_rate;
              }
            } else if (originalOffer.discount_type === "Discount Amount") {
              item.discount_amount -= offer.discount_amount;
            }
            this.calc_item_price(item);
          }
        }
      });
    },

    ApplyOnTotal(offer) {
      if (!offer.name) {
        offer = this.posOffers.find((el) => el.name == offer.offer_name);
      }
      if (
        (!this.discount_percentage_offer_name ||
          this.discount_percentage_offer_name == offer.name) &&
        offer.discount_percentage > 0 &&
        offer.discount_percentage <= 100
      ) {
        this.discount_amount = this.flt(
          (flt(this.Total) * flt(offer.discount_percentage)) / 100,
          this.currency_precision,
        );
        this.discount_percentage_offer_name = offer.name;
      }
    },

    RemoveOnTotal(offer) {
      if (
        this.discount_percentage_offer_name &&
        this.discount_percentage_offer_name == offer.offer_name
      ) {
        this.discount_amount = 0;
        this.discount_percentage_offer_name = null;
      }
    },

    addOfferToItems(offer) {
      const offer_items = JSON.parse(offer.items);
      offer_items.forEach((el) => {
        this.items.forEach((exist_item) => {
          if (exist_item.posa_row_id == el) {
            const item_offers = JSON.parse(exist_item.posa_offers);
            if (!item_offers.includes(offer.row_id)) {
              item_offers.push(offer.row_id);
              if (offer.offer === "Item Price") {
                exist_item.posa_offer_applied = 1;
              }
            }
            exist_item.posa_offers = JSON.stringify(item_offers);
          }
        });
      });
    },

    deleteOfferFromItems(offer) {
      const offer_items = JSON.parse(offer.items);
      offer_items.forEach((el) => {
        this.items.forEach((exist_item) => {
          if (exist_item.posa_row_id == el) {
            const item_offers = JSON.parse(exist_item.posa_offers);
            const updated_item_offers = item_offers.filter(
              (row_id) => row_id != offer.row_id,
            );
            if (offer.offer === "Item Price") {
              exist_item.posa_offer_applied = 0;
            }
            exist_item.posa_offers = JSON.stringify(updated_item_offers);
          }
        });
      });
    },

    validate_due_date(item) {
      const today = frappe.datetime.now_date();
      const parse_today = Date.parse(today);
      const new_date = Date.parse(item.posa_delivery_date);
      if (new_date < parse_today) {
        setTimeout(() => {
          item.posa_delivery_date = today;
        }, 0);
      }
    },
    load_print_page(invoice_name) {
      const print_format =
        this.pos_profile.print_format_for_online ||
        this.pos_profile.print_format;
      const letter_head = this.pos_profile.letter_head || 0;
      const url =
        frappe.urllib.get_base_url() +
        "/printview?doctype=Sales%20Invoice&name=" +
        invoice_name +
        "&trigger_print=1" +
        "&format=" +
        print_format +
        "&no_letterhead=" +
        letter_head;
      const printWindow = window.open(url, "Print");
      printWindow.addEventListener(
        "load",
        function () {
          printWindow.print();
          // printWindow.close();
          // NOTE : uncomoent this to auto closing printing window
        },
        true,
      );
    },

    print_draft_invoice() {
      if (!this.pos_profile.posa_allow_print_draft_invoices) {
        evntBus.$emit("show_mesage", {
          text: __(`You are not allowed to print draft invoices`),
          color: "error",
        });
        return;
      }
      let invoice_name = this.invoice_doc.name;
      frappe.run_serially([
        () => {
          const invoice_doc = this.new_invoice();
          invoice_name = invoice_doc.name ? invoice_doc.name : invoice_name;
        },
        () => {
          this.load_print_page(invoice_name);
        },
      ]);
    },
    set_delivery_charges() {
      const vm = this;
      if (
        !this.pos_profile ||
        !this.customer ||
        !this.pos_profile.posa_use_delivery_charges
      ) {
        this.delivery_charges = [];
        this.delivery_charges_rate = 0;
        this.selcted_delivery_charges = {};
        return;
      }
      this.delivery_charges_rate = 0;
      this.selcted_delivery_charges = {};

      args = {
        company: this.pos_profile.company,
        pos_profile: this.pos_profile.name,
        customer: this.customer,
      };
      if (this.shipping_address_name) {
        args["shipping_address_name"] = this.shipping_address_name;
      }
      frappe.call({
        method:
          "posawesome.posawesome.api.posapp.get_applicable_delivery_charges",
        args: args,
        async: true,
        callback: function (r) {
          if (r.message) {
            vm.delivery_charges = r.message;
            if (vm.delivery_charges && vm.shipping_address_name) {
              vm.selcted_delivery_charges = vm.delivery_charges[0];
              vm.delivery_charges_rate = vm.delivery_charges[0].rate;
            }
          }
        },
      });
    },

    deliveryChargesFilter(item, queryText, itemText) {
      const textOne = item.name.toLowerCase();
      const searchText = queryText.toLowerCase();
      return textOne.indexOf(searchText) > -1;
    },

    update_delivery_charges() {
      if (this.selcted_delivery_charges) {
        this.delivery_charges_rate = this.selcted_delivery_charges.rate;
      } else {
        this.delivery_charges_rate = 0;
      }
    },
    truncateProductTitle(title, maxLength = 50) {
      if (!title) return title;
      if (title.length <= maxLength) {
        return title;
      }

      const lastSpace = title.substring(0, maxLength).lastIndexOf(" ");

      if (lastSpace === -1) {
        return title.substring(0, maxLength) + "...";
      }

      return title.substring(0, lastSpace) + "...";
    },

    // Map orderType to packaging field name
    getPackagingFieldForOrderType(orderType) {
      const map = {
        Delivery: "packaging_delivery",
        Takeaway: "packaging_takeaway",
        Pickup: "packaging_takeaway",
        Dinin: "packaging_dinein",
        "Car Service": "packaging_takeaway",
        Talabat: "packaging_delivery",
      };
      return map[orderType] || "packaging_delivery";
    },

    // Update packaging items based on order type - add to packed_items for stock deduction (not cart)
    async updatePackagingItems() {
      // Remove old packaging items from picked_list
      this.picked_list_for_item_bundel =
        this.picked_list_for_item_bundel.filter(
          (item) => !item.is_packaging_item,
        );

      // Get packaging field based on order type
      const packagingField = this.getPackagingFieldForOrderType(this.orderType);

      // Collect item codes that need packaging (from cart items)
      const itemCodes = this.items
        .filter((item) => !item.is_packaging_item && !item.posa_is_offer)
        .map((item) => ({ item_code: item.item_code, qty: item.qty }));

      if (!itemCodes.length) return;

      // Fetch packaging for all items
      try {
        const res = await frappe.call({
          method:
            "posawesome.posawesome.doctype.pos_packaging_rule.pos_packaging_rule.get_packaging_for_items",
          args: {
            items: JSON.stringify(itemCodes),
            order_type: this.orderType,
          },
        });

        if (res.message && res.message.length) {
          // Add packaging items to packed_items for stock deduction (not cart)
          res.message.forEach((pkg) => {
            const existingPkg = this.picked_list_for_item_bundel.find(
              (i) => i.item_code === pkg.item_code && i.is_packaging_item,
            );
            if (existingPkg) {
              existingPkg.qty = pkg.qty;
            } else {
              this.picked_list_for_item_bundel.push({
                item_code: pkg.item_code,
                item_name: pkg.item_name || pkg.item_code,
                qty: pkg.qty,
                rate: 0,
                uom: pkg.uom || "Unit",
                is_packaging_item: true,
                addons: true,
                parent_item_code: this.items[0]?.item_code || "",
                posa_row_id: this.items[0]?.posa_row_id || this.makeid(20),
              });
            }
          });
        }
      } catch (e) {
        console.error("Error fetching packaging items:", e);
      }
    },
  },

  mounted() {
    // Customize
    evntBus.$on("add_item", async (item) => {
      // Always clear the customer dialog so bundled modals can show
      this.customerDialog = false;
      item.price_list = this.sales_person;

      // Check for bundle items FIRST before adding to cart
      // Skip if item comes from Variants.vue (already processed there)
      let bundleItems = [];
      if (!item.custom_fast_sell && !item.from_variants) {
        bundleItems = await this.getBundleOptions(item);
      }

      // If item has bundle options, open BundleSelector WITHOUT adding to cart
      if (bundleItems && bundleItems.length) {
        evntBus.$emit(
          "open_bundle_selector",
          item,
          bundleItems,
          this.pos_profile,
        );
        return;
      }

      // No bundle items - add to cart normally
      const posa_row_id = this.add_item(item).posa_row_id;
      item.posa_row_id = posa_row_id;
      this.item_dialog = item;

      // Handle selected ingredients from Variants.vue (Product Bundle items user chose to keep)
      if (item.selected_ingredients && item.selected_ingredients.length > 0) {
        item.selected_ingredients.forEach((ing) => {
          this.picked_list_for_item_bundel.push({
            item_code: ing.item_code,
            item_name: ing.item_name,
            rate: ing.rate || 0,
            qty: ing.qty || 1,
            uom: ing.uom || "Unit",
            addons: true,
            is_product_bundle_item: true,
            parent_item_code: item.item_code,
            parent_item_name: item.item_name,
            posa_row_id: posa_row_id,
          });
        });
      }

      // Add removed ingredients to notes for printing
      if (item.removed_ingredients && item.removed_ingredients.length > 0) {
        const removedNote = "بدون: " + item.removed_ingredients.join("، ");
        const cartItem = this.items.find((i) => i.posa_row_id === posa_row_id);
        if (cartItem) {
          cartItem.posa_notes = cartItem.posa_notes
            ? cartItem.posa_notes + " | " + removedNote
            : removedNote;
        }
      }

      // Handle selected addons from Variants.vue
      if (item.selected_addons && item.selected_addons.length > 0) {
        const addonQty = item.qty || 1;

        // Add addons with price > 0 as separate cart items (visible in invoice)
        item.selected_addons.forEach((addon) => {
          const addonPrice = parseFloat(addon.price || 0);
          if (addonPrice > 0) {
            const addonItem = {
              item_code: addon.item_code,
              item_name: addon.item_name,
              rate: addonPrice,
              qty: addonQty,
              uom: addon.uom || "Unit",
              posa_is_offer: false,
              posa_is_replace: false,
              posa_row_id: posa_row_id,
              parent_item_code: item.item_code,
            };
            console.log(
              "Adding addon to cart:",
              addonItem.item_code,
              "price:",
              addonPrice,
            );
            this.add_item(addonItem);
          }
        });

        // Prepare addons to check for Product Bundle (qty=1 because backend will multiply by parent qty)
        const addonsToCheck = item.selected_addons.map((addon) => ({
          item_code: addon.item_code,
          qty: 1,
          posa_row_id: posa_row_id,
          parent_item_code: item.item_code,
        }));

        // Fetch Product Bundle items for addons
        const addonsWithProductBundle = new Set();
        try {
          const res = await frappe.call({
            method:
              "posawesome.posawesome.api.posapp.get_product_bundle_items_for_pos",
            args: {
              item_codes: JSON.stringify(addonsToCheck),
            },
          });

          // Add Product Bundle items to packed_items
          if (res.message && res.message.length) {
            res.message.forEach((pbItem) => {
              // Track which addons have Product Bundle
              addonsWithProductBundle.add(pbItem.parent_item_code);

              this.picked_list_for_item_bundel.push({
                item_code: pbItem.item_code,
                item_name: pbItem.item_name,
                rate: pbItem.rate || 0,
                qty: pbItem.qty,
                uom: pbItem.uom || "Unit",
                addons: true,
                is_product_bundle_item: true,
                parent_item_code: pbItem.parent_item_code,
                posa_row_id: posa_row_id,
              });
            });
          }
        } catch (e) {
          console.error("Error fetching product bundle items for addons:", e);
        }

        // Only add addons that DON'T have Product Bundle (to avoid duplication)
        // qty=1 because backend will multiply by parent item qty
        item.selected_addons.forEach((addon) => {
          if (!addonsWithProductBundle.has(addon.item_code)) {
            this.picked_list_for_item_bundel.push({
              item_code: addon.item_code,
              item_name: addon.item_name,
              rate: addon.price || 0,
              qty: 1,
              uom: addon.uom || "Unit",
              is_addon: true,
              addons: true,
              parent_item_code: item.item_code,
              parent_item_name: item.item_name,
              posa_row_id: posa_row_id,
            });
          }
        });

        // Update packaging after adding addons
        this.updatePackagingItems();
      }

      await this.add_small_items(item).then((r) => {
        if (r.message) {
          item.qty = 0;
          this.picked_list_for_item_bundel.push(this.item_dialog);
          r.message.forEach((i) => {
            const myData = {
              item_name: i.item_code,
              item_code: i.item_code,
              max_required: i.custom_qty_closed,
              closed_item: i.qty,
              dummy: false,
              custom_teigger_item: i.custom_teigger_item,
              custom_teigger_item_2: i.custom_teigger_item_2,
              parent_teigger_item: item.item_code,
              selected: false,
              qty: i.qty,
              qty_closed: i.custom_qty_closed,
              filled: i.filled,
              item_classification: "Chicken Pieces",
              item_classification_pakage: i.custom_product_item_classification,
              state: item.state,
              hide: i.custom_hide,
              posa_row_id: item.posa_row_id,
              is_spicy: i.custom_spicy,
              is_regular: i.custom_regular,
              parent_group: this.item_dialog.item_group,
              // addons :true,
              parent_item_code: this.item_dialog.item_code,
            };
            this.picked_list_for_item_bundel.push(myData);
          });
        }
      });

      // Update packaging items after adding item
      this.updatePackagingItems();

      // Add to picked_list for non-bundle items
      if (!item.is_bundle) {
        let index = this.picked_list_for_item_bundel.findIndex(
          (i) =>
            i.item_code == item.item_code && i.posa_row_id == item.posa_row_id,
        );
        if (index == -1) {
          this.picked_list_for_item_bundel.push({
            parent_item_code: item.item_code,
            parent_group: item.item_group,
            posa_row_id: posa_row_id,
            ...item,
          });
        } else {
          this.picked_list_for_item_bundel[index].qty += 1;
        }
      }

      const data = {
        picked_list_for_item_bundel: this.picked_list_for_item_bundel,
        items: this.items,
      };
      evntBus.$emit("set_picked_list_for_item_bundel", data);
    });

    // Standard
    evntBus.$on("register_pos_profile", (data) => {
      this.password_input = "";
      this.pos_profile = data.pos_profile;
      evntBus.$emit("payments_register_pos_profile", this.pos_profile);
      this.branch =
        this.pos_profile.name == "Call Center" ? "" : this.pos_profile.name;
      this.saveBranchToCookie(this.branch);
      this.customer = data.pos_profile.customer;
      this.pos_opening_shift = data.pos_opening_shift;
      this.stock_settings = data.stock_settings;
      this.float_precision =
        frappe.defaults.get_default("float_precision") || 2;
      this.currency_precision =
        frappe.defaults.get_default("currency_precision") || 2;
      this.invoiceType = this.pos_profile.posa_default_sales_order
        ? "Order"
        : "Invoice";
      this.get_branches();
      this.customerDialog =
        this.pos_profile.name == "Call Center" ? true : false;
    });
    evntBus.$on("update_customer", (customer) => {
      this.customer = customer;
      this.branch =
        this.pos_profile.name == "Call Center" ? "" : this.pos_profile.name;
      this.saveBranchToCookie(this.branch);
    });
    evntBus.$on("fetch_customer_details", () => {
      this.fetch_customer_details();
    });
    evntBus.$on("new_invoice", () => {
      this.invoice_doc = "";
      this.cancel_invoice();
    });
    evntBus.$on("load_invoice", (data) => {
      this.custom_table_number = data.custom_table_number;
      this.custom_so_type = data.custom_so_type;
      this.new_invoice(data);

      if (this.invoice_doc.is_return) {
        this.discount_amount = -data.discount_amount;
        this.additional_discount_percentage =
          -data.additional_discount_percentage;
        this.return_doc = data;
      } else {
        evntBus.$emit("set_pos_coupons", data.posa_coupons);
      }
    });
    evntBus.$on("load_order", (data) => {
      this.new_order(data);
      // evntBus.$emit("set_pos_coupons", data.posa_coupons);
    });
    evntBus.$on("set_offers", (data) => {
      this.posOffers = data;
    });
    evntBus.$on("set_shipping_address_name_after_add", (data) => {
      this.shipping_address_name = data;
    });
    evntBus.$on("update_invoice_offers", (data) => {
      this.updateInvoiceOffers(data);
    });
    evntBus.$on("update_invoice_coupons", (data) => {
      this.posa_coupons = data;
      this.handelOffers();
    });
    evntBus.$on("set_all_items", (data) => {
      this.allItems = data;
      this.items.forEach((item) => {
        this.update_item_detail(item);
      });
    });
    evntBus.$on("set_sales_person_in_invoice", (data) => {
      this.sales_person = data;
    });
    evntBus.$on("add_the_new_address", (data) => {
      this.addresses.push(data);
      // this.$forceUpdate();
    });

    evntBus.$on("load_return_invoice", (data) => {
      this.new_invoice(data.invoice_doc);
      this.discount_amount = -data.return_doc.discount_amount;
      this.additional_discount_percentage =
        -data.return_doc.additional_discount_percentage;
      this.return_doc = data.return_doc;
    });
    evntBus.$on("set_new_line", (data) => {
      this.new_line = data;
    });

    evntBus.$on("set_get_draft_invoices", (data) => {
      this.get_draft_invoices();
    });
    evntBus.$on("set_open_returns", (data) => {
      this.open_returns();
    });
    evntBus.$on("set_cancel_dialog", (data) => {
      this.cancel_dialog = true;
    });
    evntBus.$on("set_new_invoice", (data) => {
      this.new_invoice();
      this.custom_so_type = "Pickup";
      this.custom_table_number = null;
    });
    evntBus.$on("set_show_payment", (data) => {
      this.show_payment();
    });
    evntBus.$on("set_create_complaint", (data) => {
      this.create_dialog_complaint = true;
      // this.show_payment();
    });
    evntBus.$on("set_show_advanced_payment", (data) => {
      this.show_advanced_payment();
    });
    evntBus.$on("set_print_draft_invoice", (data) => {
      this.print_draft_invoice();
    });
    evntBus.$on("set_picked_list_for_item_bundel_after_submit", (data) => {
      this.orderType = "Pickup";
      this.table_no = null;
      this.picked_list_for_item_bundel = [];
      const picked_list_for_item = this.picked_list_for_item_bundel.filter(
        (element) => {
          return element.qty == 0 || element.addons;
        },
      );
      const data_g = {
        picked_list_for_item_bundel: picked_list_for_item,
        items: this.items,
      };
      evntBus.$emit("set_picked_list_for_item_bundel", data_g);
    });

    // Handle new BundleSelector confirmation
    evntBus.$on("bundle_selection_confirmed", async (data) => {
      const { item, selectedItems, totalPrice, qty, notes } = data;

      // Add main item with qty and notes (keep original rate)
      item.qty = qty || 1;
      if (notes) {
        item.posa_notes = notes;
      }
      console.log("Adding main item to cart with rate:", item.rate);
      const posa_row_id = this.add_item(item).posa_row_id;
      const bundleQty = qty || 1;

      // Add extras with price > 0 as separate cart items
      selectedItems.forEach((bundleItem) => {
        const extraRate = parseFloat(
          bundleItem.rate || bundleItem.standard_rate || 0,
        );
        if (extraRate > 0) {
          const extraItem = {
            item_code: bundleItem.item_code,
            item_name: bundleItem.item_name,
            rate: extraRate,
            qty: bundleQty,
            uom: bundleItem.uom || "Unit",
            posa_is_offer: false,
            posa_is_replace: false,
            posa_row_id: posa_row_id,
            parent_item_code: item.item_code,
          };
          console.log(
            "Adding extra item to cart:",
            extraItem.item_code,
            "rate:",
            extraRate,
          );
          this.add_item(extraItem);
        }
      });

      // Prepare items to check for Product Bundle (qty=1 because backend will multiply by parent qty)
      const itemsToCheck = selectedItems.map((bundleItem) => ({
        item_code: bundleItem.item_code,
        qty: 1,
        posa_row_id: posa_row_id,
        parent_item_code: item.item_code,
      }));

      // Fetch Product Bundle items for selected items
      const itemsWithProductBundle = new Set();
      try {
        const res = await frappe.call({
          method:
            "posawesome.posawesome.api.posapp.get_product_bundle_items_for_pos",
          args: {
            item_codes: JSON.stringify(itemsToCheck),
          },
        });

        // Add Product Bundle items to packed_items
        if (res.message && res.message.length) {
          res.message.forEach((pbItem) => {
            // Track which items have Product Bundle
            itemsWithProductBundle.add(pbItem.parent_item_code);

            this.picked_list_for_item_bundel.push({
              item_code: pbItem.item_code,
              item_name: pbItem.item_name,
              rate: pbItem.rate || 0,
              qty: pbItem.qty,
              uom: pbItem.uom || "Unit",
              addons: true,
              is_product_bundle_item: true,
              parent_item_code: pbItem.parent_item_code,
              posa_row_id: posa_row_id,
            });
          });
        }
      } catch (e) {
        console.error("Error fetching product bundle items:", e);
      }

      // Add ALL selected items for display in picked_list (even if they have Product Bundle)
      selectedItems.forEach((bundleItem) => {
        this.picked_list_for_item_bundel.push({
          item_code: bundleItem.item_code,
          item_name: bundleItem.item_name,
          rate: bundleItem.rate || 0,
          qty: bundleItem.qty || 1,
          uom: bundleItem.uom || "Unit",
          addons: true,
          parent_item_code: item.item_code,
          parent_item_name: item.item_name,
          posa_row_id: posa_row_id,
          // Mark if this item has Product Bundle (for stock, ingredients already added above)
          has_product_bundle: itemsWithProductBundle.has(bundleItem.item_code),
          // Mark default selected items from Combo Component
          default_selected: bundleItem.default_selected || false,
          // Mark if this is a variant selection (user chose this variant)
          is_variant: bundleItem.is_variant || false,
        });
      });

      // Update packaging items after adding bundle
      this.updatePackagingItems();

      // Sync picked_list_for_item_bundel to ItemsSelector
      const syncData = {
        picked_list_for_item_bundel: this.picked_list_for_item_bundel,
        items: this.items,
      };
      evntBus.$emit("set_picked_list_for_item_bundel", syncData);

      evntBus.$emit("show_mesage", {
        text: __("Item added to order"),
        color: "success",
      });
    });

    evntBus.$emit("fetch_customer_details", this.pos_profile);
  },
  beforeDestroy() {
    evntBus.$off("register_pos_profile");
    evntBus.$off("add_item");
    evntBus.$off("update_customer");
    evntBus.$off("fetch_customer_details");
    evntBus.$off("new_invoice");
    evntBus.$off("set_offers");
    evntBus.$off("update_invoice_offers");
    evntBus.$off("update_invoice_coupons");
    evntBus.$off("set_all_items");
  },
  created() {
    const vm = this;
    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "Complaint Type",
        fields: ["name"],
        limit_page_length: 100,
      },
      async: false,
      callback: function (r) {
        if (r.message) {
          r.message.forEach((name) => {
            vm.complaintFiltered.push(name.name);
          });
        }
      },
    });
    evntBus.$emit("fetch_customer_details", this.pos_profile);
    document.addEventListener("keydown", this.shortOpenPayment.bind(this));
    document.addEventListener("keydown", this.shortDeleteFirstItem.bind(this));
    document.addEventListener("keydown", this.shortOpenFirstItem.bind(this));
    document.addEventListener("keydown", this.shortSelectDiscount.bind(this));
  },
  destroyed() {
    document.removeEventListener("keydown", this.shortOpenPayment);
    document.removeEventListener("keydown", this.shortDeleteFirstItem);
    document.removeEventListener("keydown", this.shortOpenFirstItem);
    document.removeEventListener("keydown", this.shortSelectDiscount);
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
    customerDialog() {
      // evntBus.$emit("fetch_customer_details", this.pos_profile);
    },
    customer() {
      evntBus.$emit("fetch_customer_details", this.pos_profile);
      this.close_payments();
      evntBus.$emit("set_customer", this.customer);
      this.fetch_customer_details();
      this.get_addresses();
      this.set_delivery_charges();
    },

    orderType() {
      this.shipping_address_name = null;
      this.delivery_charges_rate = null;
      this.selcted_delivery_charges = null;
      if (this.orderType == "Dinin") {
        this.get_tables();
      } else {
        this.table_no = null;
      }
      // Update packaging items when order type changes
      this.updatePackagingItems();
    },
    shipping_address_name() {
      this.set_delivery_charges();
      this.set_branch();
    },
    customer_info() {
      evntBus.$emit("set_customer_info_to_edit", this.customer_info);
    },
    expanded(data_value) {
      // this.update_items_details(data_value);
      if (data_value.length > 0) {
        this.update_item_detail(data_value[0]);
      }
    },
    discount_percentage_offer_name() {
      evntBus.$emit("update_discount_percentage_offer_name", {
        value: this.discount_percentage_offer_name,
      });
    },
    items: {
      deep: true,
      handler(items) {
        this.handelOffers();
        this.$forceUpdate();
      },
    },
    invoiceType() {
      evntBus.$emit("update_invoice_type", this.invoiceType);
    },
    discount_amount() {
      if (!this.discount_amount || this.discount_amount == 0) {
        this.additional_discount_percentage = 0;
      } else if (this.pos_profile.posa_use_percentage_discount) {
        this.additional_discount_percentage =
          (this.discount_amount / this.Total) * 100;
      } else {
        this.additional_discount_percentage = 0;
      }
    },
    branch(newBranch) {
      this.saveBranchToCookie(newBranch);
    },
  },
};
</script>

<style scoped>
.customer-panel {
  background: linear-gradient(135deg, #ffffff 0%, #f7f9fd 100%);
  border-radius: 22px;
  box-shadow: 0 24px 48px rgba(23, 34, 59, 0.12);
  padding: 20px 24px 16px;
}

.customer-panel__actions {
  display: flex;
  justify-content: flex-end;
}

.customer-panel__edit {
  text-transform: none !important;
  font-weight: 600;
}

.customer-panel__header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.customer-panel__avatar {
  width: 54px;
  height: 54px;
  border-radius: 16px;
  background: rgba(44, 200, 194, 0.18);
  color: #17223b;
  font-weight: 700;
  font-size: 1.2rem;
  display: grid;
  place-items: center;
}

.customer-panel__identity {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.customer-panel__name {
  font-size: 1.15rem;
  font-weight: 700;
  color: #17223b;
}

.customer-panel__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgba(23, 34, 59, 0.65);
  font-size: 0.85rem;
}

.customer-panel__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 16px 0 8px;
}

.customer-tag {
  background: rgba(23, 34, 59, 0.05);
  font-weight: 600;
  letter-spacing: 0.02em;
}

.customer-panel__stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.customer-stat {
  background: rgba(23, 34, 59, 0.05);
  border-radius: 14px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease;
}

.customer-stat--interactive {
  cursor: pointer;
}

.customer-stat--interactive:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 26px rgba(23, 34, 59, 0.12);
}

.customer-stat__label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(23, 34, 59, 0.55);
}

.customer-stat__value {
  font-size: 1.05rem;
  font-weight: 700;
  color: #17223b;
}

.customer-panel__toggles {
  margin-top: 16px;
  border-top: 1px solid rgba(23, 34, 59, 0.08);
  padding-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.customer-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.customer-toggle__label {
  font-weight: 600;
  color: #17223b;
}

.customer-toggle__hint {
  display: block;
  font-size: 0.75rem;
  color: rgba(23, 34, 59, 0.55);
}

.customer-panel__address {
  margin-top: 18px;
  border-top: 1px solid rgba(23, 34, 59, 0.08);
  padding-top: 16px;
}

.customer-panel__address-label {
  font-size: 0.76rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: rgba(23, 34, 59, 0.55);
}

.customer-panel__address-text {
  margin: 6px 0 0;
  color: rgba(23, 34, 59, 0.8);
  font-size: 0.86rem;
  line-height: 1.3;
}

.customer-panel__actions--bottom {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}

.customer-panel__complaints {
  text-transform: none !important;
  font-weight: 600;
  border-radius: 12px !important;
}

.customer-panel__complaints .v-icon {
  margin-right: 6px;
}

.order-panel {
  background: #ffffff !important;
  border-radius: 22px !important;
  box-shadow: 0 26px 48px rgba(23, 34, 59, 0.14);
  max-height: calc(100vh - 260px);
  overflow-y: auto;
  padding: 0 0 12px !important;
}

.bundle-dialog-card {
  background: linear-gradient(135deg, #ffffff 0%, #f4f6fb 100%);
  border-radius: 24px;
  box-shadow: 0 36px 64px rgba(23, 34, 59, 0.18);
  overflow: hidden;
}

.bundle-header {
  display: flex;
  align-items: flex-start;
  gap: 18px;
  padding: 24px 28px 18px;
}

.bundle-header__close {
  background: rgba(23, 34, 59, 0.05) !important;
  color: #17223b !important;
}

.bundle-header__close:hover {
  background: rgba(23, 34, 59, 0.12) !important;
}

.bundle-header__content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.bundle-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: #17223b;
  margin: 0;
}

.bundle-subtitle {
  font-size: 0.9rem;
  color: var(--v-muted-base, #6c7a92);
}

.bundle-body {
  padding: 24px 28px;
  max-height: 60vh;
  overflow-y: auto;
}

.bundle-grid {
  width: 100%;
}

.bundle-grid__left {
  padding-right: 28px !important;
  border-right: 1px solid rgba(23, 34, 59, 0.08);
}

.bundle-grid__right {
  padding-left: 28px !important;
}

.bundle-category {
  margin-bottom: 24px;
}

.bundle-category__title {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  font-weight: 600;
  color: #17223b;
  text-transform: uppercase;
  font-size: 0.85rem;
  margin-bottom: 12px;
}

.bundle-category__title::after {
  content: "";
  display: inline-block;
  height: 1px;
  width: 45px;
  background: linear-gradient(90deg, rgba(44, 200, 194, 0), #2cc8c2);
}

.bundle-item-wrapper {
  padding: 8px !important;
}

.bundle-item-card {
  border-radius: 18px !important;
  padding: 16px 18px !important;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 140px;
  background: rgba(23, 34, 59, 0.04) !important;
  box-shadow: 0 18px 34px rgba(23, 34, 59, 0.08);
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}

.bundle-item-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 28px 50px rgba(23, 34, 59, 0.14);
}

.bundle-item-card__info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bundle-item-card__name {
  margin: 0;
  font-weight: 600;
  color: #17223b;
  font-size: 0.98rem;
}

.bundle-item-card__price {
  font-size: 0.85rem;
  color: rgba(23, 34, 59, 0.7);
  font-weight: 500;
}

.bundle-item-card__controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.bundle-stepper__btn {
  border-radius: 10px !important;
  background: #ffffff !important;
  border: 1px solid rgba(23, 34, 59, 0.12) !important;
  box-shadow: none !important;
}

.bundle-stepper__btn:hover {
  box-shadow: 0 10px 24px rgba(44, 200, 194, 0.18) !important;
}

.bundle-stepper__value {
  min-width: 32px;
  text-align: center;
  font-weight: 600;
  color: #17223b;
}

.bundle-item-card--active {
  background: rgba(44, 200, 194, 0.12) !important;
  border: 1px solid rgba(44, 200, 194, 0.4) !important;
}

.bundle-item-card--locked {
  opacity: 0.65;
  backdrop-filter: blur(2px);
}

.bundle-item-card--locked-active {
  background: rgba(23, 34, 59, 0.12) !important;
  border: 1px dashed rgba(23, 34, 59, 0.3) !important;
}

.bundle-summary {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.bundle-summary__box {
  background: rgba(23, 34, 59, 0.04);
  border-radius: 16px;
  padding: 18px 20px;
  box-shadow: inset 0 0 0 1px rgba(23, 34, 59, 0.06);
}

.bundle-summary__label {
  display: block;
  font-size: 0.82rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: rgba(23, 34, 59, 0.6);
  margin-bottom: 8px;
}

.bundle-qty-field {
  border-radius: 14px;
}

::v-deep .bundle-qty-field .v-input__slot {
  background: #ffffff !important;
  border-radius: 12px !important;
  border: 1px solid rgba(23, 34, 59, 0.1) !important;
  padding: 4px 10px !important;
}

.bundle-qty-field__btn {
  border-radius: 10px;
  padding: 4px;
  cursor: pointer;
}

.bundle-notes {
  border-radius: 14px;
  background: #ffffff !important;
}

::v-deep .bundle-notes .v-input__slot {
  border-radius: 14px !important;
  border: 1px solid rgba(23, 34, 59, 0.1) !important;
  background: #ffffff !important;
}

.bundle-alert {
  margin-top: 16px;
  background: linear-gradient(
    90deg,
    rgba(239, 71, 111, 0.15),
    rgba(239, 71, 111, 0.05)
  );
  color: #ef476f;
  border-radius: 12px;
  padding: 12px 18px;
  font-weight: 600;
}

.bundle-actions {
  justify-content: flex-end;
  gap: 12px;
  padding: 18px 28px 24px;
}

.bundle-action {
  border-radius: 12px !important;
  padding: 10px 26px !important;
  text-transform: none !important;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.bundle-action--ghost {
  color: var(--v-muted-base, #6c7a92) !important;
}

.bundle-action--primary {
  box-shadow: 0 18px 36px rgba(23, 34, 59, 0.22);
}

.border_line_bottom {
  border-bottom: 1px solid lightgray;
}

.disable-events {
  pointer-events: none;
}

span {
  font-size: 16px;
}

.v-col {
  margin-bottom: 8px;
}

.qty-input .v-text-field__slot input {
  text-align: center !important;
}

.custom-dialog {
  background-color: white !important;
  /* padding: 20px !important; */
}

.main_color {
  color: #e71d36 !important;
}

.v-list {
  padding: 0 !important;
  background: white !important;
}

/* Background and text color for dropdown options */
::v-deep .v-menu__content .v-list-item {
  background-color: #e71d36 !important;
  /* Dark green background */
}

/* Background color for the selected item inside the dropdown */
::v-deep .v-list-item--active {
  background-color: #e71d36 !important;
  /* Dark green */
  color: white !important;
  /* White text */
}

.list-hover {
  transition: all 0.3s linear;
}

.list-hover:hover {
  background-color: #e71d36 !important;
  color: white !important;
  cursor: pointer !important;
}

::v-deep
  .theme--light.v-text-field--outlined:not(.v-input--is-focused):not(
    .v-input--has-state
  )
  > .v-input__control
  > .v-input__slot
  fieldset {
  color: #e91e63;
}
</style>
