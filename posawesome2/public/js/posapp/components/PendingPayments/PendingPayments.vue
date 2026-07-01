<template>
  <v-container fluid class="container1">
    <!-- Back Button -->
    <v-card flat class="cards mb-2 mt-2 py-0" style="max-height: 11vh; height: 11vh">
      <v-row align="start" no-gutters>
        <v-col cols="3">
          <v-btn block class="pa-1" large color="warning" dark @click="goBack">
            {{ __("Back") }}
          </v-btn>
        </v-col>
        <v-col cols="6" class="text-center">
          <h2 class="mt-2">{{ __("Needs Your Action") }}</h2>
        </v-col>
        <v-col cols="3" class="text-right">
          <v-btn color="primary" @click="fetchPayments" :loading="loading">
            <v-icon left>mdi-refresh</v-icon>
            {{ __("Refresh") }}
          </v-btn>
        </v-col>
      </v-row>
    </v-card>

    <!-- Filters -->
    <v-card class="mb-2 pa-2">
      <v-row dense>
        <v-col cols="12" sm="6" md="3">
          <v-autocomplete v-model="filters.branch" :items="branchOptions" :label="__('Branch')" dense outlined clearable
            hide-details="auto" @change="fetchPayments" />
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-menu v-model="menuFrom" :close-on-content-click="false" transition="scale-transition" offset-y
            min-width="auto">
            <template v-slot:activator="{ on, attrs }">
              <v-text-field v-model="filters.date_from" :label="__('From Date')" prepend-icon="mdi-calendar" readonly
                v-bind="attrs" v-on="on" dense outlined hide-details />
            </template>
            <v-date-picker v-model="filters.date_from" @input="
              menuFrom = false;
            fetchPayments();
            " />
          </v-menu>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-menu v-model="menuTo" :close-on-content-click="false" transition="scale-transition" offset-y
            min-width="auto">
            <template v-slot:activator="{ on, attrs }">
              <v-text-field v-model="filters.date_to" :label="__('To Date')" prepend-icon="mdi-calendar" readonly
                v-bind="attrs" v-on="on" dense outlined hide-details />
            </template>
            <v-date-picker v-model="filters.date_to" @input="
              menuTo = false;
            fetchPayments();
            " />
          </v-menu>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-text-field v-model="search" :label="__('Search')" prepend-icon="mdi-magnify" dense outlined clearable
            hide-details />
        </v-col>
      </v-row>
    </v-card>

    <!-- Payments Table -->
    <v-card>
      <v-data-table :headers="headers" :items="payments" :search="search" :loading="loading" item-key="name"
        :items-per-page="50" class="frappe-table" dense show-select v-model="selectedPayments"
        :footer-props="{ 'items-per-page-options': [10, 20, 50, 100] }">
        <template v-slot:item.posting_date="{ item }">
          {{ formatDate(item.posting_date) }}
        </template>

        <template v-slot:item.paid_amount="{ item }">
          {{ formtCurrency(item.paid_amount) }}
        </template>

        <template v-slot:item.status="{ item }">
          <v-chip color="orange" dark small>
            {{ __("Draft") }}
          </v-chip>
        </template>

        <template v-slot:item.actions="{ item }">
          <v-btn v-if="item.is_closed" small color="success" class="mr-1" @click="approvePayment(item)"
            :loading="item.approving">
            <v-icon small left>mdi-check</v-icon>
            {{ __("Approve") }}
          </v-btn>
          <v-btn v-if="item.is_closed" small color="error" @click="rejectPayment(item)" :loading="item.rejecting">
            <v-icon small left>mdi-close</v-icon>
            {{ __("Reject") }}
          </v-btn>
        </template>

        <template v-slot:item.invoice="{ item }">
          <span v-if="item.references && item.references.length">
            {{ item.references[0].reference_name }}
          </span>
        </template>
      </v-data-table>

      <!-- Bulk Actions -->
      <v-card-actions v-if="selectedPayments.length > 0">
        <v-spacer></v-spacer>
        <v-btn color="success" @click="bulkApprove" :loading="bulkApproving">
          <v-icon left>mdi-check-all</v-icon>
          {{ __("Approve Selected") }} ({{ selectedPayments.length }})
        </v-btn>
        <v-btn color="error" @click="bulkReject" :loading="bulkRejecting">
          <v-icon left>mdi-close-circle</v-icon>
          {{ __("Reject Selected") }} ({{ selectedPayments.length }})
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- Reject Reason Dialog -->
    <v-dialog v-model="rejectDialog" max-width="400">
      <v-card>
        <v-card-title>{{ __("Reject Payment") }}</v-card-title>
        <v-card-text>
          <v-textarea v-model="rejectReason" :label="__('Reason for rejection')" outlined rows="3" />
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="rejectDialog = false">{{ __("Cancel") }}</v-btn>
          <v-btn color="error" @click="confirmReject">{{
            __("Confirm Reject")
          }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { evntBus } from "../../bus";
import format from "../../format";

export default {
  mixins: [format],
  data() {
    const today =
      (frappe?.datetime?.get_today && frappe.datetime.get_today()) ||
      new Date().toISOString().slice(0, 10);

    return {
      search: "",
      loading: false,
      payments: [],
      selectedPayments: [],
      branchOptions: [],
      menuFrom: false,
      menuTo: false,
      filters: {
        branch: null,
        date_from: today,
        date_to: today,
      },
      headers: [
        { text: __("Payment Entry"), value: "name", align: "start" },
        { text: __("Date"), value: "posting_date", align: "start" },
        { text: __("Customer"), value: "party_name", align: "start" },
        { text: __("Branch"), value: "branch", align: "start" },
        {
          text: __("Mode of Payment"),
          value: "mode_of_payment",
          align: "start",
        },
        { text: __("Amount"), value: "paid_amount", align: "end" },
        { text: __("Invoice"), value: "invoice", align: "start" },
        { text: __("Status"), value: "status", align: "center" },
        {
          text: __("Actions"),
          value: "actions",
          sortable: false,
          align: "center",
        },
      ],
      rejectDialog: false,
      rejectReason: "",
      paymentToReject: null,
      bulkApproving: false,
      bulkRejecting: false,
    };
  },

  mounted() {
    this.fetchBranches();
    this.fetchPayments();
  },

  methods: {
    goBack() {
      window.history.back();
    },

    formatDate(date) {
      if (!date) return "";
      return frappe.datetime.str_to_user(date);
    },

    async fetchBranches() {
      try {
        const res = await frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Branch",
            fields: ["name"],
            limit_page_length: 0,
          },
        });
        this.branchOptions = (res.message || []).map((b) => b.name);
      } catch (e) {
        console.error("Failed to fetch branches:", e);
      }
    },

    async fetchPayments() {
      this.loading = true;
      try {
        const res = await frappe.call({
          method:
            "posawesome.posawesome.api.payment_entry.get_pending_payment_entries",
          args: {
            branch: this.filters.branch || null,
            date_from: this.filters.date_from || null,
            date_to: this.filters.date_to || null,
          },
        });
        this.payments = (res.message || []).map((p) => ({
          ...p,
          approving: false,
          rejecting: false,
          is_closed: p.custom_closed == 0 ? true : false
        }));
      } catch (e) {
        console.error("Failed to fetch payments:", e);
        frappe.msgprint(__("Failed to fetch pending payments"));
      }
      this.loading = false;
    },

    async approvePayment(item) {
      item.approving = true;
      try {
        await frappe.call({
          method:
            "posawesome.posawesome.api.payment_entry.approve_payment_entry",
          args: { payment_entry: item.name },
        });
        frappe.show_alert({
          message: __("Payment approved"),
          indicator: "green",
        });
        this.fetchPayments();
      } catch (e) {
        frappe.msgprint(__("Failed to approve payment"));
      }
      item.approving = false;
    },

    rejectPayment(item) {
      this.paymentToReject = item;
      this.rejectReason = "";
      this.rejectDialog = true;
    },

    async confirmReject() {
      if (!this.paymentToReject) return;
      this.paymentToReject.rejecting = true;
      this.rejectDialog = false;
      try {
        await frappe.call({
          method:
            "posawesome.posawesome.api.payment_entry.reject_payment_entry",
          args: {
            payment_entry: this.paymentToReject.name,
            reason: this.rejectReason,
          },
        });
        frappe.show_alert({
          message: __("Payment rejected"),
          indicator: "red",
        });
        this.fetchPayments();
      } catch (e) {
        frappe.msgprint(__("Failed to reject payment"));
      }
      this.paymentToReject.rejecting = false;
      this.paymentToReject = null;
    },

    async bulkApprove() {
      if (!this.selectedPayments.length) return;
      this.bulkApproving = true;
      try {
        for (const payment of this.selectedPayments) {
          await frappe.call({
            method:
              "posawesome.posawesome.api.payment_entry.approve_payment_entry",
            args: { payment_entry: payment.name },
          });
        }
        frappe.show_alert({
          message: __("{0} payments approved", [this.selectedPayments.length]),
          indicator: "green",
        });
        this.selectedPayments = [];
        this.fetchPayments();
      } catch (e) {
        frappe.msgprint(__("Failed to approve some payments"));
      }
      this.bulkApproving = false;
    },

    async bulkReject() {
      if (!this.selectedPayments.length) return;
      this.paymentToReject = { bulk: true, items: this.selectedPayments };
      this.rejectReason = "";
      this.rejectDialog = true;
    },
  },
};
</script>

<style scoped>
.container1 {
  padding: 10px;
}
</style>
