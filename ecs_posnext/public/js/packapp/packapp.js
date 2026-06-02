import { createApp } from "vue";
import Home from "./Home.vue";

frappe.provide("frappe.PackApp");

frappe.PackApp.packapp = class {
  constructor({ parent }) {
    this.$parent = $(document);
    this.page = parent.page;
    this.make_body();
  }
  make_body() {
    this.$el = this.$parent.find(".main-section");
    const app = createApp(Home);
    app.config.globalProperties.__ = window.__;
    app.config.globalProperties.frappe = window.frappe;
    app.mount(this.$el[0]);
  }
};
