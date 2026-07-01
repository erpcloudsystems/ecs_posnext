<template>
  <div fluid class="mt-2">
    <ClosingDialog></ClosingDialog>
    <Drafts></Drafts>
    <!-- <SalesOrders></SalesOrders> -->
    <Returns></Returns>
    <NewAddress></NewAddress>
    <MpesaPayments></MpesaPayments>
    <Variants></Variants>
    <OptionVariantSelector></OptionVariantSelector>
    <BundleSelector></BundleSelector>
    <OpeningDialog v-if="dialog" :dialog="dialog"></OpeningDialog>
    <v-row v-show="!dialog">
      <v-col
        v-show="!payment && !offers && !coupons && !selected_item"
        xl="9"
        lg="9"
        md="9"
        sm="9"
        cols="12"
        class="pos pr-0"
      >
        <ItemsSelector></ItemsSelector>
      </v-col>
      <v-col
        v-show="offers"
        xl="9"
        lg="9"
        md="9"
        sm="9"
        cols="12"
        class="pos pr-0"
      >
        <PosOffers></PosOffers>
      </v-col>
      <v-col
        v-show="coupons"
        xl="9"
        lg="9"
        md="9"
        sm="9"
        cols="12"
        class="pos pr-0"
      >
        <PosCoupons></PosCoupons>
      </v-col>
      <v-col
        v-show="selected_item"
        xl="9"
        lg="9"
        md="9"
        sm="9"
        cols="12"
        class="pos pr-0"
      >
        <PosSelectedItem></PosSelectedItem>
      </v-col>
      <v-col
        v-show="payment"
        xl="9"
        lg="9"
        md="9"
        sm="9"
        cols="12"
        class="pos pr-0"
      >
        <Payments></Payments>
      </v-col>
      <v-col xl="3" lg="3" md="3" sm="3" cols="12" class="pos">
        <Invoice></Invoice>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import { evntBus } from "../../bus";
import format from "../../format";
import BundleSelector from "./BundleSelector.vue";
import ClosingDialog from "./ClosingDialog.vue";
import Drafts from "./Drafts.vue";
import Invoice from "./Invoice.vue";
import ItemsSelector from "./ItemsSelector.vue";
import MpesaPayments from "./Mpesa-Payments.vue";
import NewAddress from "./NewAddress.vue";
import OpeningDialog from "./OpeningDialog.vue";
import OptionVariantSelector from "./OptionVariantSelector.vue";
import Payments from "./Payments.vue";
import PosCoupons from "./PosCoupons.vue";
import PosOffers from "./PosOffers.vue";
import PosSelectedItem from "./PosSelectedItem.vue";
import Returns from "./Returns.vue";
import SalesOrders from "./SalesOrders.vue";
import Variants from "./Variants.vue";

export default {
  mixins: [format],
  data: function () {
    return {
      dialog: false,
      pos_profile: "",
      pos_opening_shift: "",
      payment: false,
      offers: false,
      coupons: false,
      selected_item: false,
    };
  },

  components: {
    ItemsSelector,
    Invoice,
    OpeningDialog,
    Payments,
    Drafts,
    ClosingDialog,
    PosSelectedItem,
    Returns,
    PosOffers,
    PosCoupons,
    NewAddress,
    Variants,
    MpesaPayments,
    SalesOrders,
    OptionVariantSelector,
    BundleSelector,
  },

  methods: {
    check_opening_entry() {
      return frappe
        .call("posawesome.posawesome.api.posapp.check_opening_shift", {
          user: frappe.session.user,
        })
        .then((r) => {
          if (r.message) {
            this.pos_profile = r.message.pos_profile;
            this.pos_opening_shift = r.message.pos_opening_shift;
            this.get_offers(this.pos_profile.name);
            evntBus.$emit("register_pos_profile", r.message);
            evntBus.$emit("fetch_customer_details", this.pos_profile);
            evntBus.$emit("set_company", r.message.company);
            console.info("LoadPosProfile");
            if (r.message.must_close) {
              evntBus.$emit("show_mesage", {
                text: __(
                  "Shift ended. Please close the shift; selling is blocked until then.",
                ),
                color: "warning",
              });
              this.get_closing_data();
            }
          } else {
            this.create_opening_voucher();
          }
        });
    },
    create_opening_voucher() {
      this.dialog = true;
    },
    get_closing_data() {
      return frappe
        .call(
          "posawesome.posawesome.doctype.pos_closing_shift.pos_closing_shift.make_closing_shift_from_opening",
          {
            opening_shift: this.pos_opening_shift,
          },
        )
        .then((r) => {
          if (r.message) {
            evntBus.$emit("open_ClosingDialog", r.message);
          } else {
            // console.log(r);
          }
        });
    },
    submit_closing_pos(data) {
      const vm = this;
      frappe
        .call(
          "posawesome.posawesome.doctype.pos_closing_shift.pos_closing_shift.submit_closing_shift",
          {
            closing_shift: data,
          },
        )
        .then((r) => {
          if (r.message) {
            // Print closing receipt automatically using saved document name
            vm.print_closing_receipt(r.message);
            evntBus.$emit("show_mesage", {
              text: __("POS Shift Closed"),
              color: "success",
            });
            evntBus.$emit("unfreeze");
            vm.check_opening_entry();
          } else {
            console.log(r);
          }
        });
    },
    print_closing_receipt(closing_shift_name) {
      // Use Frappe standard print with Jinja Print Format
      const print_format = "POS Closing Shift Receipt";
      const print_url = frappe.urllib.get_full_url(
        `/api/method/frappe.utils.print_format.download_pdf?doctype=POS%20Closing%20Shift&name=${encodeURIComponent(closing_shift_name)}&format=${encodeURIComponent(print_format)}&no_letterhead=1`,
      );
      const printWindow = window.open(print_url, "_blank");
      if (printWindow) {
        printWindow.focus();
      }
    },
    get_offers(pos_profile) {
      return frappe
        .call("posawesome.posawesome.api.posapp.get_offers", {
          profile: pos_profile,
        })
        .then((r) => {
          if (r.message) {
            console.info("LoadOffers");
            evntBus.$emit("set_offers", r.message);
          }
        });
    },
    get_pos_setting() {
      frappe.db.get_doc("POS Settings", undefined).then((doc) => {
        evntBus.$emit("set_pos_settings", doc);
      });
    },
  },

  mounted: function () {
    this.$nextTick(function () {
      this.check_opening_entry();
      this.get_pos_setting();
      evntBus.$on("close_opening_dialog", () => {
        this.dialog = false;
      });
      evntBus.$on("register_pos_data", (data) => {
        this.pos_profile = data.pos_profile;
        this.get_offers(this.pos_profile.name);
        this.pos_opening_shift = data.pos_opening_shift;
        evntBus.$emit("register_pos_profile", data);
        console.info("LoadPosProfile");
      });
      evntBus.$on("show_payment", (data) => {
        this.payment = true ? data === "true" : false;
        this.offers = false ? data === "true" : false;
        this.coupons = false ? data === "true" : false;
        this.selected_item = false ? data === "true" : false;
      });
      evntBus.$on("show_offers", (data) => {
        this.offers = true ? data === "true" : false;
        this.payment = false ? data === "true" : false;
        this.coupons = false ? data === "true" : false;
        this.selected_item = false ? data === "true" : false;
      });
      evntBus.$on("show_coupons", (data) => {
        this.coupons = true ? data === "true" : false;
        this.offers = false ? data === "true" : false;
        this.payment = false ? data === "true" : false;
        this.selected_item = false ? data === "true" : false;
      });
      evntBus.$on("show_item_selected", (data) => {
        this.coupons = false ? data === "true" : false;
        this.offers = false ? data === "true" : false;
        this.payment = false ? data === "true" : false;
        this.selected_item = true ? data === "true" : false;
      });
      evntBus.$on("open_closing_dialog", () => {
        this.get_closing_data();
      });
      evntBus.$on("submit_closing_pos", (data) => {
        this.submit_closing_pos(data);
      });
    });
  },
  beforeDestroy() {
    evntBus.$off("close_opening_dialog");
    evntBus.$off("register_pos_data");
    evntBus.$off("LoadPosProfile");
    evntBus.$off("show_offers");
    evntBus.$off("show_coupons");
    evntBus.$off("show_item_selected");
    evntBus.$off("open_closing_dialog");
    evntBus.$off("submit_closing_pos");
  },
};
</script>

<style scoped></style>
