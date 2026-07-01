<template>
  <nav>
    <v-navigation-drawer
      v-model="drawer"
      :mini-variant.sync="mini"
      app
      permanent
      elevation="0"
      color="#F8F9FB"
      class="border-right"
      width="260"
    >
      <v-list-item class="mb-4">
        <!-- <v-list-item-avatar color="white" elevation="1">
          <v-img :src="company_img" contain></v-img>
        </v-list-item-avatar> -->
        <v-list-item-content v-if="!mini">
          <v-list-item-title
            class="text-h6 font-weight-bold grey--text text--darken-3"
          >
            {{ company }}
          </v-list-item-title>
        </v-list-item-content>
        <v-btn icon @click.stop="mini = !mini" small class="ml-auto">
          <v-icon color="grey darken-1">
            {{ mini ? "mdi-menu" : "mdi-chevron-left" }}
          </v-icon>
        </v-btn>
      </v-list-item>

      <v-list flat class="">
        <v-subheader
          v-if="!mini"
          class="text-overline font-weight-bold grey--text"
          >MENU</v-subheader
        >

        <v-list-item-group color="primary">
          <v-list-item
            @click="goToPOS"
            class="rounded-lg mb-1"
            active-class="active-item"
          >
            <v-list-item-icon>
              <v-icon>mdi-view-dashboard-outline</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title class="font-weight-medium">{{
                __("Back to POS")
              }}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>

          <v-list-item class="rounded-lg mb-1 active-item" active>
            <v-list-item-icon>
              <v-icon color="primary">mdi-package-variant-closed</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title class="font-weight-bold primary--text">{{
                __("Item Manager")
              }}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list-item-group>
      </v-list>
    </v-navigation-drawer>

    <v-snackbar
      v-model="snack"
      :timeout="5000"
      :color="snackColor"
      top
      right
      rounded="pill"
    >
      {{ snackText }}
    </v-snackbar>
  </nav>
</template>

<script>
export default {
  data() {
    return {
      drawer: true,
      mini: false,
      company: "Item Manager",
      company_img: "/files/mumo-logo.png",
      snack: false,
      snackColor: "",
      snackText: "",
    };
  },
  methods: {
    goToPOS() {
      window.location.href = "/app";
    },
    show_mesage(data) {
      this.snack = true;
      this.snackColor = data.color;
      this.snackText = data.text;
    },
  },
};
</script>

<style scoped>
.active-item {
  background-color: #ffffff !important;
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.05) !important;
}

.v-list-item--active::before {
  opacity: 0 !important;
}

.border-right {
  border-right: 1px solid #ededed !important;
}

.v-list-item__icon {
  margin-right: 12px !important;
}
</style>
