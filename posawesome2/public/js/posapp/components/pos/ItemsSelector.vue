<template>
  <div>
    <v-card
      class="selection modern-shell mx-auto mt-3"
      style="max-height: 75vh; height: 75vh"
    >
      <v-progress-linear
        :active="loading"
        :indeterminate="loading"
        absolute
        top
        color="info"
      ></v-progress-linear>
      <v-row class="items px-2 py-1">
        <v-col class="pb-0 mb-2">
          <v-text-field
            dense
            clearable
            autofocus
            outlined
            color="primary"
            :label="__('Search Items')"
            :hint="
              __('Search by item code, serial number, batch no or barcode')
            "
            hide-details
            v-model="debounce_search"
            @keydown.esc="esc_event"
            @keydown.enter="search_onchange"
            ref="debounce_search"
            class="search-input"
          ></v-text-field>
        </v-col>
        <v-col cols="3" class="pb-0 mb-2" v-if="pos_profile.posa_input_qty">
          <v-text-field
            dense
            outlined
            color="primary"
            :label="__('QTY')"
            background-color="white"
            hide-details
            v-model.number="qty"
            type="number"
            @keydown.enter="enter_event"
            @keydown.esc="esc_event"
          ></v-text-field>
        </v-col>
        <v-col cols="2" class="pb-0" v-if="pos_profile.posa_new_line">
          <v-checkbox
            v-model="new_line"
            color="accent"
            value="true"
            :label="__('NLine')"
            class="d-flex align-items-center"
            dense
            hide-details
          ></v-checkbox>
        </v-col>
        <v-col cols="12" class="pt-0 mt-0">
          <div
            fluid
            class="items"
            v-if="items_view == 'card' && toggle_sales_persson == 1"
          >
            <v-row dense class="overflow-y-auto" style="max-height: 67vh">
              <v-col
                v-for="(item, idx) in sales_persons"
                :key="idx"
                min-height="200"
                sm="12"
                md="3"
                lg="4"
                xl="3"
              >
                <v-card
                  class="mx-auto text-center selection-card"
                  max-width="344"
                  hover="hover"
                  @click="open_items_groups(item)"
                >
                  <v-img
                    :src="
                      item.custom_logo_image ||
                      '/assets/posawesome/js/posapp/components/pos/placeholder-image.png'
                    "
                    class="selection-card__image"
                    gradient="to bottom, rgba(0,0,0,0.05), rgba(0,0,0,0.45)"
                    height="150px"
                  ></v-img>

                  <v-card-title class="text-center selection-card__title">
                    <h6
                      class="text-uppercase w-100"
                      v-text="item.sales_person_name"
                    ></h6>
                  </v-card-title>
                </v-card>
              </v-col>
            </v-row>
          </div>
          <div
            fluid
            class="items"
            v-if="items_view == 'card' && toggle_item_group == 1"
          >
            <v-row dense class="overflow-y-auto" style="max-height: 67vh">
              <v-col sm="12" md="3" lg="4" xl="3" min-height="200">
                <v-card
                  hover="hover"
                  @click="back_to_sales_person"
                  class="d-flex flex-column align-center justify-center group-card back-card"
                  style="height: 100%"
                >
                  <v-icon
                    size="50px"
                    class="flex-column align-center justify-center back-card__icon"
                  >
                    mdi-arrow-left
                  </v-icon>
                </v-card>
              </v-col>

              <v-col
                v-for="(item, idx) in items_group"
                :key="idx"
                xl="2"
                lg="3"
                md="3"
                sm="3"
                cols="1"
                min-height="200"
              >
                <v-card
                  hover="hover"
                  @click="open_items(item)"
                  class="group-card"
                >
                  <v-img
                    :src="
                      item.custom_logo_image ||
                      '/assets/posawesome/js/posapp/components/pos/placeholder-image.png'
                    "
                    class="group-card__image"
                    gradient="to bottom, rgba(0,0,0,0.05), rgba(0,0,0,0.45)"
                    height="150px"
                  >
                  </v-img>
                  <v-card-title class="text-center group-card__title">
                    <h6
                      class="text-uppercase w-100 text-caption font-weight-bold"
                    >
                      {{ item.name || item }}
                    </h6>
                  </v-card-title>
                </v-card>
              </v-col>
            </v-row>
          </div>
          <div
            fluid
            class="items"
            v-if="items_view == 'card' && toggle_items == 1"
          >
            <v-row dense class="overflow-y-auto" style="max-height: 67vh">
              <v-col sm="12" md="3" lg="4" xl="3" min-height="200">
                <v-card
                  hover="hover"
                  @click="back_to_sales_person_2"
                  class="d-flex flex-column align-center justify-center group-card back-card"
                  style="height: 100%"
                >
                  <v-icon
                    size="50px"
                    class="flex-column align-center justify-center back-card__icon"
                  >
                    mdi-arrow-left
                  </v-icon>
                </v-card>
              </v-col>

              <v-col
                xl="2"
                lg="3"
                md="3"
                sm="3"
                cols="1"
                v-for="(item, idx) in filtred_items"
                :key="idx"
                min-height="200"
              >
                <v-card hover="hover" @click="add_item(item)" class="item-card">
                  <v-img
                    :src="
                      item.image ||
                      '/assets/posawesome/js/posapp/components/pos/placeholder-image.png'
                    "
                    class="item-card__image"
                    gradient="to bottom, rgba(0,0,0,0.05), rgba(0,0,0,0.45)"
                    height="150px"
                  >
                  </v-img>
                  <v-card-text
                    v-text="item.item_name"
                    class="item-card__title"
                  ></v-card-text>
                  <v-card-text class="item-card__price">
                    {{ currencySymbol(item.currency) || "" }}
                    {{ formtCurrency(item.rate) || 0 }}
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </div>
        </v-col>
      </v-row>
    </v-card>
    <v-card class="cards mb-0 mt-3 pa-2 action-bar">
      <v-row no-gutters align="center" justify="center">
        <!-- <v-col cols="4" class="mt-2">
          <v-btn small block color="primary" text @click="show_offers"
            >{{ offersCount }} {{ __("Offers") }} : {{ appliedOffersCount }}
            {{ __("Applied") }}</v-btn
          >
        </v-col> -->
        <v-col cols="4" class="pa-1">
          <v-btn
            block
            class="action-button action-button--accent"
            depressed
            @click="show_item_selected"
          >
            {{ __("Items Selected") }}
          </v-btn>
        </v-col>
        <v-col cols="4" class="pa-1">
          <v-btn
            block
            class="action-button action-button--ghost"
            text
            @click="get_draft_invoices"
            >{{ __("Held") }}
          </v-btn>
        </v-col>
        <v-col cols="4" class="pa-1">
          <v-btn
            block
            class="action-button action-button--ghost"
            text
            :class="{ 'disable-events': !pos_profile.posa_allow_return }"
            @click="open_returns"
            >{{ __("Return") }}
          </v-btn>
        </v-col>

        <v-col cols="4" class="pa-1">
          <v-btn
            block
            class="action-button action-button--outline"
            outlined
            color="primary"
            @click="new_invoice"
            >{{ __("Save/New") }}
          </v-btn>
        </v-col>

        <v-col cols="4" class="pa-1">
          <v-btn
            block
            class="action-button action-button--ghost"
            text
            @click="show_advanced_payment"
          >
            {{ __("Advanced Payment") }}
          </v-btn>
        </v-col>

        <v-col class="col-4 pa-1">
          <v-btn
            block
            class="action-button action-button--primary"
            color="primary"
            dark
            @click="show_payment"
          >
            {{ __("Order") }}
          </v-btn>
        </v-col>
        <v-col cols="4" class="pa-1">
          <v-btn
            block
            class="action-button action-button--danger"
            text
            @click="cancel_dialog"
            >{{ __("Cancel") }}
          </v-btn>
        </v-col>
        <v-col class="col-4 pa-1">
          <v-btn
            block
            class="action-button action-button--warning"
            text
            @click="create_complaint"
          >
            {{ __("Create Complaint") }}
          </v-btn>
        </v-col>
        <v-col
          v-if="pos_profile.posa_allow_print_draft_invoices"
          cols="4"
          class="pa-1"
        >
          <v-btn
            block
            class="action-button action-button--ghost"
            text
            @click="print_draft_invoice"
            >{{ __("Print Draft") }}
          </v-btn>
        </v-col>
        <v-col cols="4" class="pa-1">
          <v-btn
            block
            class="action-button action-button--accent"
            depressed
            @click="show_coupons"
            >{{ couponsCount }} {{ __("Coupons") }}</v-btn
          >
        </v-col>
      </v-row>
    </v-card>
  </div>
</template>

<script>
import _ from "lodash";
import { evntBus } from "../../bus";
import format from "../../format";
export default {
  mixins: [format],
  data: () => ({
    pos_profile: "",
    toggle_sales_persson: 1,
    toggle_item_group: 0,
    toggle_items: 0,
    flags: {},
    items_view: "list",
    item_group: "",
    loading: false,
    items_group: [],
    items: [],
    search: "",
    first_search: "",
    itemsPerPage: 1000,
    offersCount: 0,
    appliedOffersCount: 0,
    couponsCount: 0,
    sales_persons: [],
    sales_person: null,
    appliedCouponsCount: 0,
    customer_price_list: null,
    customer: null,
    items_data: {},
    picked_list_for_item_bundel: [],
    new_line: true,
    qty: 1,
  }),

  watch: {
    filtred_items(new_value, old_value) {
      if (!this.pos_profile.pose_use_limit_search) {
        if (new_value.length != old_value.length) {
          this.update_items_details(new_value);
        }
      }
    },
    customer() {
      this.get_items();
    },
    new_line() {
      evntBus.$emit("set_new_line", this.new_line);
    },
  },

  methods: {
    get_draft_invoices(item) {
      evntBus.$emit("set_get_draft_invoices", true);

      // console.log('items_groupitems_group', this.items_group)
    },
    open_returns(item) {
      evntBus.$emit("set_open_returns", true);

      // console.log('items_groupitems_group', this.items_group)
    },
    cancel_dialog(item) {
      evntBus.$emit("set_cancel_dialog", true);

      // console.log('items_groupitems_group', this.items_group)
    },
    new_invoice(item) {
      evntBus.$emit("set_new_invoice", true);

      // console.log('items_groupitems_group', this.items_group)
    },
    show_payment(item) {
      evntBus.$emit("set_show_payment", true);

      // console.log('items_groupitems_group', this.items_group)
    },
    create_complaint(item) {
      evntBus.$emit("set_create_complaint", true);

      // console.log('items_groupitems_group', this.items_group)
    },
    show_advanced_payment(item) {
      evntBus.$emit("set_show_advanced_payment", true);

      // console.log('items_groupitems_group', this.items_group)
    },
    print_draft_invoice(item) {
      evntBus.$emit("set_print_draft_invoice", true);

      // console.log('items_groupitems_group', this.items_group)
    },
    open_items_groups(item) {
      this.sales_person = item.custom_price_list;

      this.toggle_sales_persson = 0;
      this.toggle_items = 0;
      this.toggle_item_group = 1;
      evntBus.$emit("set_sales_person_in_invoice", item.sales_person_name);
      localStorage.setItem("selected_sales_person", item.custom_price_list);

      // console.log('items_groupitems_group', this.items_group)
    },
    back_to_sales_person() {
      this.toggle_sales_persson = 1;
      this.toggle_item_group = 0;
      this.toggle_items = 0;

      // console.log('items_groupitems_group', this.items_group)
    },
    back_to_sales_person_2() {
      this.toggle_sales_persson = 0;
      this.toggle_item_group = 1;
      this.toggle_items = 0;

      // console.log('items_groupitems_group', this.items_group)
    },
    open_items(group) {
      this.item_group = group.name || group;
      this.toggle_items = 1;
      this.toggle_sales_persson = 0;
      this.toggle_item_group = 0;
      this.get_items();
    },
    get_sales_person_names() {
      const vm = this;
      if (
        vm.pos_profile.posa_local_storage &&
        localStorage.sales_persons_storage
      ) {
        vm.sales_persons = JSON.parse(
          localStorage.getItem("sales_persons_storage"),
        );
      }
      frappe.call({
        method: "posawesome.posawesome.api.posapp.get_sales_person_names",
        callback: function (r) {
          if (r.message) {
            vm.sales_persons = r.message;
            console.log("hhhhhhhhhhhzzzzzzzzzzzz", vm.sales_persons);
            // vm.filtred_items = r.message;
            if (vm.pos_profile.posa_local_storage) {
              localStorage.setItem("sales_persons_storage", "");
              localStorage.setItem(
                "sales_persons_storage",
                JSON.stringify(r.message),
              );
            }
          }
        },
      });
    },
    show_offers() {
      evntBus.$emit("show_offers", "true");
    },
    async show_item_selected() {
      const data = {
        picked_list_for_item_bundel: this.picked_list_for_item_bundel,
        items_data: this.items_data,
      };
      evntBus.$emit("update_item_selected", data);
      evntBus.$emit("show_item_selected", "true");
    },
    show_coupons() {
      evntBus.$emit("show_coupons", "true");
    },
    get_items() {
      if (!this.pos_profile) {
        console.error("No POS Profile");
        return;
      }
      const vm = this;
      this.loading = true;
      let search = this.get_search(this.first_search);
      let gr = "";
      let sr = "";
      if (search) {
        sr = search;
      }
      gr = vm.item_group;
      if (
        vm.pos_profile.posa_local_storage &&
        localStorage.items_storage &&
        !vm.pos_profile.pose_use_limit_search
      ) {
        vm.items = JSON.parse(localStorage.getItem("items_storage"));
        evntBus.$emit("set_all_items", vm.items);
        vm.loading = false;
      }
      frappe.call({
        method: "posawesome.posawesome.api.posapp.get_items",
        args: {
          pos_profile: vm.pos_profile,
          price_list: vm.sales_person,
          item_group: gr,
          search_value: sr,
          customer: vm.customer,
        },
        callback: function (r) {
          if (r.message) {
            vm.items = r.message;
            evntBus.$emit("set_all_items", vm.items);
            vm.loading = false;
            // console.info("Items Loaded");
            console.log("Items Loaded", vm.items);
            if (
              vm.pos_profile.posa_local_storage &&
              !vm.pos_profile.pose_use_limit_search
            ) {
              localStorage.setItem("items_storage", "");
              try {
                localStorage.setItem(
                  "items_storage",
                  JSON.stringify(r.message),
                );
              } catch (e) {
                console.error(e);
              }
            }
            if (vm.pos_profile.pose_use_limit_search) {
              vm.enter_event();
            }
          }
        },
      });
    },
    get_items_groups() {
      if (!this.pos_profile) {
        console.log("No POS Profile");
        return;
      }
      if (this.pos_profile.item_groups.length > 0) {
        this.pos_profile.item_groups.forEach((element) => {
          if (element.item_group !== "All Item Groups") {
            this.items_group.push(element.item_group);
          }
        });
      } else {
        const vm = this;
        frappe.call({
          method: "posawesome.posawesome.api.posapp.get_items_groups",
          args: {},
          callback: function (r) {
            if (r.message) {
              r.message.forEach((element) => {
                vm.items_group.push(element);
              });
            }
          },
        });
      }
    },
    getItmesHeaders() {
      const items_headers = [
        {
          text: __("Name"),
          align: "start",
          sortable: true,
          value: "item_name",
        },
        {
          text: __("Code"),
          align: "start",
          sortable: true,
          value: "item_code",
        },
        { text: __("Rate"), value: "rate", align: "start" },
        { text: __("Available QTY"), value: "actual_qty", align: "start" },
        { text: __("UOM"), value: "stock_uom", align: "start" },
      ];
      if (!this.pos_profile.posa_display_item_code) {
        items_headers.splice(1, 1);
      }

      return items_headers;
    },
    add_item(item) {
      item = { ...item };
      if (item.has_variants) {
        evntBus.$emit("open_variants_model", item, this.items);
      } else {
        if (!item.qty || item.qty === 1) {
          item.qty = Math.abs(this.qty);
        }
        evntBus.$emit("add_item", item);
        this.qty = 1;
      }
    },
    enter_event() {
      let match = false;
      if (!this.filtred_items.length || !this.first_search) {
        return;
      }
      const qty = this.get_item_qty(this.first_search);
      const new_item = { ...this.filtred_items[0] };
      new_item.qty = flt(qty);
      new_item.item_barcode.forEach((element) => {
        if (this.search == element.barcode) {
          new_item.uom = element.posa_uom;
          match = true;
        }
      });
      if (
        !new_item.to_set_serial_no &&
        new_item.has_serial_no &&
        this.pos_profile.posa_search_serial_no
      ) {
        new_item.serial_no_data.forEach((element) => {
          if (this.search && element.serial_no == this.search) {
            new_item.to_set_serial_no = this.first_search;
            match = true;
          }
        });
      }
      if (this.flags.serial_no) {
        new_item.to_set_serial_no = this.flags.serial_no;
      }
      if (
        !new_item.to_set_batch_no &&
        new_item.has_batch_no &&
        this.pos_profile.posa_search_batch_no
      ) {
        new_item.batch_no_data.forEach((element) => {
          if (this.search && element.batch_no == this.search) {
            new_item.to_set_batch_no = this.first_search;
            new_item.batch_no = this.first_search;
            match = true;
          }
        });
      }
      if (this.flags.batch_no) {
        new_item.to_set_batch_no = this.flags.batch_no;
      }
      if (match) {
        this.add_item(new_item);
        this.search = null;
        this.first_search = null;
        this.debounce_search = null;
        this.flags.serial_no = null;
        this.flags.batch_no = null;
        this.qty = 1;
        this.$refs.debounce_search.focus();
      }
    },
    search_onchange() {
      const vm = this;
      if (vm.pos_profile.pose_use_limit_search) {
        vm.get_items();
      } else {
        vm.enter_event();
      }
    },
    get_item_qty(first_search) {
      let scal_qty = Math.abs(this.qty);
      if (first_search.startsWith(this.pos_profile.posa_scale_barcode_start)) {
        let pesokg1 = first_search.substr(7, 5);
        let pesokg;
        if (pesokg1.startsWith("0000")) {
          pesokg = "0.00" + pesokg1.substr(4);
        } else if (pesokg1.startsWith("000")) {
          pesokg = "0.0" + pesokg1.substr(3);
        } else if (pesokg1.startsWith("00")) {
          pesokg = "0." + pesokg1.substr(2);
        } else if (pesokg1.startsWith("0")) {
          pesokg =
            pesokg1.substr(1, 1) + "." + pesokg1.substr(2, pesokg1.length);
        } else if (!pesokg1.startsWith("0")) {
          pesokg =
            pesokg1.substr(0, 2) + "." + pesokg1.substr(2, pesokg1.length);
        }
        scal_qty = pesokg;
      }
      return scal_qty;
    },
    get_search(first_search) {
      let search_term = "";
      if (
        first_search &&
        first_search.startsWith(this.pos_profile.posa_scale_barcode_start)
      ) {
        search_term = first_search.substr(0, 7);
      } else {
        search_term = first_search;
      }
      return search_term;
    },
    esc_event() {
      this.search = null;
      this.first_search = null;
      this.qty = 1;
      this.$refs.debounce_search.focus();
    },
    update_items_details(items) {
      // set debugger
      const vm = this;
      frappe.call({
        method: "posawesome.posawesome.api.posapp.get_items_details",
        args: {
          pos_profile: vm.pos_profile,
          items_data: items,
        },
        callback: function (r) {
          if (r.message) {
            items.forEach((item) => {
              const updated_item = r.message.find(
                (element) => element.item_code == item.item_code,
              );
              item.actual_qty = updated_item.actual_qty;
              item.serial_no_data = updated_item.serial_no_data;
              item.batch_no_data = updated_item.batch_no_data;
              item.item_uoms = updated_item.item_uoms;
            });
          }
        },
      });
    },
    update_cur_items_details() {
      this.update_items_details(this.filtred_items);
    },
    scan_barcoud() {
      const vm = this;
      onScan.attachTo(document, {
        suffixKeyCodes: [],
        keyCodeMapper: function (oEvent) {
          oEvent.stopImmediatePropagation();
          return onScan.decodeKeyEvent(oEvent);
        },
        onScan: function (sCode) {
          setTimeout(() => {
            vm.trigger_onscan(sCode);
          }, 300);
        },
      });
    },
    trigger_onscan(sCode) {
      if (this.filtred_items.length == 0) {
        evntBus.$emit("show_mesage", {
          text: `No Item has this barcode "${sCode}"`,
          color: "error",
        });
        frappe.utils.play_sound("error");
      } else {
        this.enter_event();
        this.debounce_search = null;
        this.search = null;
      }
    },
    generateWordCombinations(inputString) {
      const words = inputString.split(" ");
      const wordCount = words.length;
      const combinations = [];

      // Helper function to generate all permutations
      function permute(arr, m = []) {
        if (arr.length === 0) {
          combinations.push(m.join(" "));
        } else {
          for (let i = 0; i < arr.length; i++) {
            const current = arr.slice();
            const next = current.splice(i, 1);
            permute(current.slice(), m.concat(next));
          }
        }
      }

      permute(words);

      return combinations;
    },
  },

  computed: {
    filtred_items() {
      this.search = this.get_search(this.first_search);
      if (!this.pos_profile.pose_use_limit_search) {
        let filtred_list = [];
        let filtred_group_list = [];
        if (this.item_group != "ALL") {
          filtred_group_list = this.items.filter((item) =>
            item.item_group
              .toLowerCase()
              .includes(this.item_group.toLowerCase()),
          );
        } else {
          filtred_group_list = this.items;
        }
        if (!this.search || this.search.length < 3) {
          if (
            this.pos_profile.posa_show_template_items &&
            this.pos_profile.posa_hide_variants_items
          ) {
            return (filtred_list = filtred_group_list
              .filter((item) => !item.variant_of)
              .slice(0, 50));
          } else {
            return (filtred_list = filtred_group_list.slice(0, 50));
          }
        } else if (this.search) {
          filtred_list = filtred_group_list.filter((item) => {
            let found = false;
            for (let element of item.item_barcode) {
              if (element.barcode == this.search) {
                found = true;
                break;
              }
            }
            return found;
          });
          if (filtred_list.length == 0) {
            filtred_list = filtred_group_list.filter((item) =>
              item.item_code.toLowerCase().includes(this.search.toLowerCase()),
            );
            if (filtred_list.length == 0) {
              const search_combinations = this.generateWordCombinations(
                this.search,
              );
              filtred_list = filtred_group_list.filter((item) => {
                let found = false;
                for (let element of search_combinations) {
                  element = element.toLowerCase().trim();
                  let element_regex = new RegExp(
                    `.*${element.split("").join(".*")}.*`,
                  );
                  if (element_regex.test(item.item_name.toLowerCase())) {
                    found = true;
                    break;
                  }
                }
                return found;
              });
            }
            if (
              filtred_list.length == 0 &&
              this.pos_profile.posa_search_serial_no
            ) {
              filtred_list = filtred_group_list.filter((item) => {
                let found = false;
                for (let element of item.serial_no_data) {
                  if (element.serial_no == this.search) {
                    found = true;
                    this.flags.serial_no = null;
                    this.flags.serial_no = this.search;
                    break;
                  }
                }
                return found;
              });
            }
            if (
              filtred_list.length == 0 &&
              this.pos_profile.posa_search_batch_no
            ) {
              filtred_list = filtred_group_list.filter((item) => {
                let found = false;
                for (let element of item.batch_no_data) {
                  if (element.batch_no == this.search) {
                    found = true;
                    this.flags.batch_no = null;
                    this.flags.batch_no = this.search;
                    break;
                  }
                }
                return found;
              });
            }
          }
        }
        if (
          this.pos_profile.posa_show_template_items &&
          this.pos_profile.posa_hide_variants_items
        ) {
          return filtred_list.filter((item) => !item.variant_of).slice(0, 50);
        } else {
          return filtred_list.slice(0, 50);
        }
      } else {
        return this.items.slice(0, 50);
      }
    },
    debounce_search: {
      get() {
        return this.first_search;
      },
      set: _.debounce(function (newValue) {
        this.first_search = newValue;
      }, 200),
    },
  },

  created: function () {
    this.$nextTick(function () {});
    // Customize
    this.get_sales_person_names();

    evntBus.$on("focus_search_input", () => {
      this.$refs.debounce_search.focus();
    });
    // Standard
    evntBus.$on("register_pos_profile", (data) => {
      this.pos_profile = data.pos_profile;
      this.get_items();
      this.get_items_groups();
      this.items_view = this.pos_profile.posa_default_card_view
        ? "card"
        : "list";
    });
    evntBus.$on("update_cur_items_details", () => {
      this.update_cur_items_details();
    });
    evntBus.$on("update_offers_counters", (data) => {
      this.offersCount = data.offersCount;
      this.appliedOffersCount = data.appliedOffersCount;
    });
    evntBus.$on("update_coupons_counters", (data) => {
      this.couponsCount = data.couponsCount;
      this.appliedCouponsCount = data.appliedCouponsCount;
    });
    evntBus.$on("update_customer_price_list", (data) => {
      this.customer_price_list = data;
    });
    evntBus.$on("back_to_main_sales", (data) => {
      this.back_to_sales_person();
    });
    evntBus.$on("update_customer", (data) => {
      this.customer = data;
    });
    evntBus.$on("set_picked_list_for_item_bundel", (data) => {
      console.log(
        "data.picked_list_for_item_bundel",
        data.picked_list_for_item_bundel,
      );
      this.picked_list_for_item_bundel = data.picked_list_for_item_bundel;
      this.items_data = data.items;
    });
    evntBus.$emit("set_new_line", this.new_line);
  },

  mounted() {
    this.scan_barcoud();
  },
};
</script>

<style scoped>
.modern-shell {
  background: linear-gradient(145deg, #ffffff 0%, #f3f6fb 100%);
  border-radius: 24px;
  box-shadow: 0 24px 52px rgba(23, 34, 59, 0.1);
  padding: 18px;
}

::v-deep .search-input .v-input__slot {
  border-radius: 14px !important;
  background: #fff !important;
  border: 1px solid rgba(23, 34, 59, 0.08) !important;
  min-height: 48px;
  padding-left: 14px;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

::v-deep .search-input .v-input__slot:hover {
  border-color: rgba(44, 200, 194, 0.6) !important;
  box-shadow: 0 14px 28px rgba(44, 200, 194, 0.16);
}

::v-deep .search-input .v-label {
  color: #6c7a92 !important;
}

.selection-card,
.group-card,
.item-card {
  border-radius: 18px !important;
  background: #ffffff !important;
  box-shadow: 0 14px 30px rgba(23, 34, 59, 0.08);
  cursor: pointer;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}

.selection-card:hover,
.group-card:hover,
.item-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 24px 44px rgba(23, 34, 59, 0.12);
}

.selection-card__image,
.group-card__image,
.item-card__image {
  border-top-left-radius: 18px !important;
  border-top-right-radius: 18px !important;
  object-fit: cover;
}

.selection-card__title,
.group-card__title,
.item-card__title,
.item-card__price {
  text-align: center;
}

.selection-card__title h6,
.group-card__title h6 {
  width: 100%;
  font-weight: 700;
  color: #17223b;
  letter-spacing: 0.06em;
}

.item-card__title {
  font-size: 14px !important;
  font-weight: 600;
  color: #17223b !important;
  padding-top: 12px !important;
  padding-bottom: 4px !important;
}

.item-card__price {
  font-size: 13px !important;
  color: rgba(23, 34, 59, 0.6) !important;
  padding-bottom: 14px !important;
}

.back-card {
  background: rgba(44, 200, 194, 0.1) !important;
  border: 1px dashed rgba(44, 200, 194, 0.4) !important;
}

.back-card__icon {
  color: #2cc8c2 !important;
}

.action-bar {
  background: linear-gradient(
    135deg,
    rgba(44, 200, 194, 0.12),
    rgba(23, 34, 59, 0.08)
  );
  border-radius: 20px;
  border: 1px solid rgba(23, 34, 59, 0.06);
}

.action-button {
  border-radius: 14px !important;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: none !important;
  padding: 12px 18px !important;
  transition:
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.action-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 32px rgba(23, 34, 59, 0.12);
}

.action-button--accent {
  background: linear-gradient(135deg, #2cc8c2, #25b0a9);
  color: #ffffff !important;
}

.action-button--primary {
  background: #17223b !important;
  color: #ffffff !important;
}

.action-button--ghost {
  background: transparent !important;
  color: #17223b !important;
  border: 1px solid rgba(23, 34, 59, 0.08) !important;
}

.action-button--ghost::before,
.action-button--outline::before,
.action-button--danger::before,
.action-button--warning::before {
  background-color: transparent !important;
}

.action-button--outline {
  background: #ffffff !important;
  border: 1px solid rgba(23, 34, 59, 0.14) !important;
}

.action-button--danger {
  color: #ef476f !important;
  border: 1px solid rgba(239, 71, 111, 0.25) !important;
  background: rgba(239, 71, 111, 0.08) !important;
}

.action-button--warning {
  color: #f4a259 !important;
  border: 1px solid rgba(244, 162, 89, 0.25) !important;
  background: rgba(244, 162, 89, 0.08) !important;
}

.disable-events {
  opacity: 0.45;
  pointer-events: none;
}

::v-deep label {
  margin-bottom: 0 !important;
}
</style>
