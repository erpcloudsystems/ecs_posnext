<template>
  <v-app class="container1">
    <v-main>
      <ItemManagerNavbar v-if="!showEditor"></ItemManagerNavbar>
      <!-- Show NewProductEditor if editing/adding, otherwise show ItemManager list -->
      <NewProductEditor
        v-if="showEditor"
        :item-id="currentItemId"
        @back="goToList"
      />
      <ItemManager v-else @edit-item="editItem" @add-item="addItem" />
    </v-main>
  </v-app>
</template>

<script>
import ItemManager from "../posapp/components/ItemManager/ItemManager.vue";
import NewProductEditor from "../posapp/components/ItemManager/NewProductEditor.vue";
import ItemManagerNavbar from "./ItemManagerNavbar.vue";

export default {
  components: {
    ItemManagerNavbar,
    ItemManager,
    NewProductEditor,
  },
  props: {
    itemId: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      showEditor: false,
      currentItemId: null,
    };
  },
  methods: {
    remove_frappe_nav() {
      this.$nextTick(function () {
        $(".page-head").remove();
        $(".navbar.navbar-default.navbar-fixed-top").remove();
      });
    },
    editItem(item) {
      this.currentItemId = item.item_code;
      this.showEditor = true;
      window.history.pushState(
        {},
        "",
        `/app/item_manager/${encodeURIComponent(item.item_code)}`,
      );
    },
    addItem() {
      this.currentItemId = "new";
      this.showEditor = true;
      window.history.pushState({}, "", "/app/item_manager/new");
    },
    goToList() {
      this.showEditor = false;
      this.currentItemId = null;
      window.history.pushState({}, "", "/app/item_manager");
    },
  },
  mounted() {
    this.remove_frappe_nav();
    // Check if we have an itemId from URL
    if (this.itemId) {
      this.currentItemId = this.itemId;
      this.showEditor = true;
    }
  },
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
  background: #f4f6fb;
}
</style>
