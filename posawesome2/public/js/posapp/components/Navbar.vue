<template>
  <nav>
    <v-app-bar app height="60" class="elevation-5">
      <v-app-bar-nav-icon
        @click.stop="drawer = !drawer"
        class="[#E71D36]--text"
      ></v-app-bar-nav-icon>
      <v-img
        src="/files/mumo-logo.png"
        alt="POS Awesome"
        max-width="55"
        color="primary"
      ></v-img>
      <v-toolbar-title
        @click="go_desk"
        style="cursor: pointer"
        class="text-uppercase primary--text"
      >
        <span class="font-weight-bold text-xl-h4">
          <span style="color: #3d8493">P</span>
          <span style="color: #e71d36">O</span>
          <span style="color: #d89f65">S</span>
        </span>
        <!-- <span>Mumo</span> -->
      </v-toolbar-title>

      <v-spacer></v-spacer>
      <v-btn
        style="cursor: unset"
        class="font-weight-bold"
        text
        color="#E71D36"
      >
        <span right>{{ pos_profile.name }}</span>
      </v-btn>
      <div class="text-center">
        <v-menu offset-y>
          <template v-slot:activator="{ on, attrs }">
            <v-btn
              color="#E71D36"
              class="font-weight-bold"
              dark
              text
              v-bind="attrs"
              v-on="on"
              >{{ __("Menu") }}</v-btn
            >
          </template>
          <v-card class="mx-auto" max-width="300" tile>
            <v-list dense>
              <v-list-item-group v-model="menu_item" color="#E71D36">
                <v-list-item
                  @click="close_shift_dialog"
                  v-if="
                    !pos_profile.posa_hide_closing_shift &&
                    item == 0 &&
                    pos_profile.name != 'Call Center'
                  "
                >
                  <v-list-item-icon>
                    <v-icon>mdi-content-save-move-outline</v-icon>
                  </v-list-item-icon>
                  <v-list-item-content>
                    <v-list-item-title>{{
                      __("Close Shift")
                    }}</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
                <v-list-item
                  @click="print_last_invoice"
                  v-if="
                    pos_profile.posa_allow_print_last_invoice &&
                    this.last_invoice
                  "
                >
                  <v-list-item-icon>
                    <v-icon>mdi-printer</v-icon>
                  </v-list-item-icon>
                  <v-list-item-content>
                    <v-list-item-title>{{
                      __("Print Last Invoice")
                    }}</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
                <v-divider class="my-0"></v-divider>
                <v-list-item @click="logOut">
                  <v-list-item-icon>
                    <v-icon>mdi-logout</v-icon>
                  </v-list-item-icon>
                  <v-list-item-content>
                    <v-list-item-title>{{ __("Logout") }}</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
                <v-list-item @click="go_about">
                  <v-list-item-icon>
                    <v-icon>mdi-information-outline</v-icon>
                  </v-list-item-icon>
                  <v-list-item-content>
                    <v-list-item-title>{{ __("About") }}</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
              </v-list-item-group>
            </v-list>
          </v-card>
        </v-menu>
      </div>
      <!-- Language Toggle -->
      <v-btn
        @click="toggleLanguage"
        :title="
          currentLang === 'ar' ? 'Switch to English' : 'التبديل إلى العربية'
        "
        class="lang-toggle-btn font-weight-bold mx-1"
        outlined
        x-small
        color="#17223B"
        style="
          min-width: 40px;
          border-radius: 20px;
          font-size: 11px;
          letter-spacing: 0.5px;
        "
      >
        {{ currentLang === "ar" ? "EN" : "AR" }}
      </v-btn>

      <!-- User Info -->
      <div class="user-info d-flex align-center ml-2">
        <v-icon small color="#E71D36" class="mr-1">mdi-account</v-icon>
        <span
          class="font-weight-medium"
          style="color: #e71d36; font-size: 12px"
        >
          {{ employeeCode }} | {{ userName }}
        </span>
      </div>
    </v-app-bar>
    <v-navigation-drawer
      v-model="drawer"
      :mini-variant.sync="mini"
      app
      width="170"
      style="background-color: #000 !important"
    >
      <v-list dark>
        <v-list-item class="px-2">
          <v-list-item-avatar>
            <v-img :src="company_img"></v-img>
          </v-list-item-avatar>

          <v-list-item-title>{{ company }}</v-list-item-title>

          <v-btn icon @click.stop="mini = !mini">
            <v-icon>mdi-chevron-left</v-icon>
          </v-btn>
        </v-list-item>
        <!-- <MyPopup/> -->
        <v-list-item-group v-model="item" color="white">
          <v-list-item
            v-for="item in items"
            :key="item.text"
            @click="changePage(item.text)"
          >
            <v-list-item-icon>
              <v-icon v-text="item.icon"></v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title v-text="item.text"></v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list-item-group>
      </v-list>
    </v-navigation-drawer>
    <v-snackbar v-model="snack" :timeout="5000" :color="snackColor" top right>
      {{ snackText }}
    </v-snackbar>
    <v-dialog v-model="freeze" persistent max-width="290">
      <v-card>
        <v-card-title class="text-h5">
          {{ freezeTitle }}
        </v-card-title>
        <v-card-text>{{ freezeMsg }}</v-card-text>
      </v-card>
    </v-dialog>
  </nav>
</template>

<script>
import { evntBus } from "../bus";

export default {
  // components: {MyPopup},
  data() {
    return {
      drawer: false,
      mini: true,
      item: 0,
      items: [
        { text: "POS", icon: "mdi-network-pos" },
        // { text: "Order", icon: "mdi-shopping" },
        // { text: "IncommingOrders", icon: "mdi-shopping" },
        { text: "CompleteOrders", icon: "mdi-shopping" },
        { text: "AllOrders", icon: "mdi-shopping" },
        // { text: "prepapp", icon: "mdi-shopping" },
        // { text: "Preparing", icon: "mdi-shopping" },
        // { text: "packapp", icon: "mdi-shopping" },
        // { text: "Packing", icon: "mdi-shopping" },
        // { text: "deliverapp", icon: "mdi-shopping" },
        // { text: "Delivery", icon: "mdi-shopping" },
      ],
      page: "",
      fav: true,
      menu: false,
      message: false,
      hints: true,
      menu_item: 0,
      snack: false,
      snackColor: "",
      snackText: "",
      company: "POS Awesome",
      company_img: "/files/mumo-logo.png",
      pos_profile: "",
      freeze: false,
      freezeTitle: "",
      freezeMsg: "",
      last_invoice: "",
      userName: "",
      employeeCode: "",
      currentLang:
        frappe.boot.lang || localStorage.getItem("posa_ui_lang") || "en",
    };
  },
  mounted() {
    this.loadUserInfo();
  },
  methods: {
    toggleLanguage() {
      if (window.posawesome && posawesome.lang) {
        posawesome.lang.toggleLanguage();
      } else {
        var next = this.currentLang === "ar" ? "en" : "ar";
        localStorage.setItem("posa_ui_lang", next);
        frappe.call({
          method: "frappe.client.set_value",
          args: {
            doctype: "User",
            name: frappe.session.user,
            fieldname: "language",
            value: next,
          },
          callback: function () {
            location.reload();
          },
        });
      }
    },
    async loadUserInfo() {
      try {
        this.userName = frappe.session.user_fullname || frappe.session.user;
        const employee = await frappe.db.get_value(
          "Employee",
          { user_id: frappe.session.user },
          ["name", "employee_name"],
        );
        if (employee && employee.message) {
          this.employeeCode = employee.message.name || "";
        }
      } catch (e) {
        console.error("Failed to load user info:", e);
      }
    },
    changePage(key) {
      if (key === "deliverapp" || key === "packapp" || key === "prepapp") {
        this.$router.push(`/${key}`);
        return;
      }
      this.$emit("changePage", key);
    },

    go_desk() {
      frappe.set_route("/");
      location.reload();
    },
    go_about() {
      const win = window.open(
        "https://github.com/yrestom/POS-Awesome",
        "_blank",
      );
      win.focus();
    },
    close_shift_dialog() {
      evntBus.$emit("open_closing_dialog");
    },
    show_mesage(data) {
      this.snack = true;
      this.snackColor = data.color;
      this.snackText = data.text;
    },
    logOut() {
      var me = this;
      me.logged_out = true;
      return frappe.call({
        method: "logout",
        callback: function (r) {
          if (r.exc) {
            return;
          }
          frappe.set_route("/login");
          location.reload();
        },
      });
    },
    print_last_invoice() {
      if (!this.last_invoice) return;
      const print_format =
        this.pos_profile.print_format_for_online ||
        this.pos_profile.print_format;
      const letter_head = this.pos_profile.letter_head || 0;
      const url =
        frappe.urllib.get_base_url() +
        "/printview?doctype=Sales%20Invoice&name=" +
        this.last_invoice +
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
        },
        true,
      );
    },
    async checkBranchSupervisorRole() {
      try {
        const pendingPaymentsItem = {
          text: "PendingPayments",
          icon: "mdi-cash-check",
        };
        const dispatcherItem = {
          text: "Dispatcher",
          icon: "mdi-truck-delivery",
        };
        const operatingRateItem = {
          text: "OperatingRate",
          icon: "mdi-chart-line",
        };

        const hasRole = frappe.user_roles.includes("Branch supervisor");
        const hasRoleCallCenterManager = frappe.user_roles.includes(
          "Call center manager",
        );
        const hasRoleCallCenterSupervisor = frappe.user_roles.includes(
          "Call center supervisor",
        );
        if (hasRoleCallCenterManager || hasRoleCallCenterSupervisor) {
          if (!this.items.some((item) => item.text === "PendingPayments")) {
            this.items.push(pendingPaymentsItem);
          }
        }
        console.log("hasRole", hasRole);
        if (hasRole) {
          if (!this.items.some((item) => item.text === "Dispatcher")) {
            this.items.push(dispatcherItem);
          }
          if (!this.items.some((item) => item.text === "OperatingRate")) {
            this.items.push(operatingRateItem);
          }
        }
      } catch (e) {
        console.error("Error checking Branch Supervisor role:", e);
      }
    },
  },
  created: function () {
    this.$nextTick(function () {
      evntBus.$on("show_mesage", (data) => {
        this.show_mesage(data);
      });
      evntBus.$on("set_company", (data) => {
        this.company = data.name;
        this.company_img = data.company_logo
          ? data.company_logo
          : this.company_img;
      });
      evntBus.$on("register_pos_profile", (data) => {
        this.pos_profile = data.pos_profile;
        // const payments = { text: "Payments", icon: "mdi-cash-register" };
        // if (
        //   this.pos_profile.posa_use_pos_awesome_payments &&
        //   // this.items.length !== 3 &&
        //   this.pos_profile.name != "Call Center"
        // ) {
        //   this.items.push(payments);
        // }

        // Add PendingPayments for Branch Supervisor role
        this.checkBranchSupervisorRole();
      });

      // Check Branch Supervisor role on load
      this.checkBranchSupervisorRole();
      evntBus.$on("set_last_invoice", (data) => {
        this.last_invoice = data;
      });
      evntBus.$on("freeze", (data) => {
        this.freeze = true;
        this.freezeTitle = data.title;
        this.freezeMsg = data.msg;
      });
      evntBus.$on("unfreeze", () => {
        this.freeze = false;
        this.freezTitle = "";
        this.freezeMsg = "";
      });
    });
  },
};
</script>

<style scoped>
.margen-top {
  margin-top: 0px;
}

.main_color {
  color: #e71d36 !important;
}
</style>
