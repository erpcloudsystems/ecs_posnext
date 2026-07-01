<template>
  <v-app class="container1">
    <v-main>
      <Navbar @changePage="setPage($event)"></Navbar>
      <component
        v-bind:is="page"
        class="mx-4 md-4"
        style="background: #fbde5c1a !important"
      ></component>
    </v-main>
  </v-app>
</template>

<script>
import Navbar from "./components/Navbar.vue";
import POS from "./components/pos/Pos.vue";
import Payments from "./components/payments/Pay.vue";
import Order from "./components/orders/Order.vue";
import IncommingOrders from "./components/IncommingOrders/IncommingOrders.vue";
import Delivery from "./components/Delivery/Delivery.vue";
import Timer from "./components/Timer/Timer.vue";
import Packing from "./components/Packing/Packing.vue";
import Preparing from "./components/Preparing/Preparing.vue";
import CompleteOrders from "./components/CompleteOrders/CompleteOrders.vue";
import AllOrders from "./components/AllOrders/AllOrders.vue";
import PendingPayments from "./components/PendingPayments/PendingPayments.vue";
import Dispatcher from "./components/Dispatcher/Dispatcher.vue";
import OperatingRate from "./components/OperatingRate/OperatingRate.vue";

export default {
  data: function () {
    return {
      page: "POS",
    };
  },
  components: {
    Navbar,
    POS,
    Payments,
    Order,
    IncommingOrders,
    Delivery,
    Timer,
    Packing,
    Preparing,
    CompleteOrders,
    AllOrders,
    PendingPayments,
    Dispatcher,
    OperatingRate,
  },
  methods: {
    setPage(page) {
      this.page = page;
    },
    remove_frappe_nav() {
      this.$nextTick(function () {
        $(".page-head").remove();
        $(".navbar.navbar-default.navbar-fixed-top").remove();
      });
    },
  },
  mounted() {
    this.remove_frappe_nav();
  },
  updated() {},
  created: function () {
    setTimeout(() => {
      this.remove_frappe_nav();
    }, 1000);
  },
};
</script>

<style scoped>
.container1 {
  margin-top: 0px;
  /* background-color: white !important; */
}
</style>
