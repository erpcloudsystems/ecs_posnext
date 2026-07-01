<template>
  <v-container fluid class="item-manager pa-5">
    <!-- Header -->
    <v-row class="mb-2">
      <v-col cols="12">
        <div class="d-flex align-center justify-space-between">
          <h1 class="item-manager__title">{{ __("Item Manager") }}</h1>
          <v-btn
            color="primary"
            @click="openNewItemDialog"
            dark
            class="text-none rounded-lg px-5"
            elevation="0"
          >
            <v-icon left small>mdi-plus</v-icon>
            {{ __("Add New Item") }}
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Search and Filter -->
    <v-card
      class="item-manager__content-card mb-0 pa-5 rounded-xl"
      elevation="1"
    >
      <v-row align="center" class="mb-4">
        <v-col cols="12" md="4">
          <v-text-field
            v-model="searchQuery"
            :placeholder="__('Search')"
            prepend-inner-icon="mdi-magnify"
            clearable
            filled
            rounded
            dense
            hide-details
            class="item-manager__search"
            background-color="#F4F6FB"
            @input="debounceSearch"
          ></v-text-field>
        </v-col>
        <v-spacer></v-spacer>
        <v-col cols="auto">
          <div class="d-flex align-center" style="gap: 10px">
            <v-select
              v-model="filterGroup"
              :items="itemGroups"
              :label="__('Item Group')"
              item-text="name"
              item-value="name"
              clearable
              outlined
              dense
              hide-details
              class="item-manager__filter-select"
              style="max-width: 180px"
            >
              <template v-slot:prepend-inner>
                <v-icon small class="mr-1">mdi-filter-variant</v-icon>
              </template>
            </v-select>
            <v-select
              v-model="filterClassification"
              :items="itemClassifications"
              :label="__('Classification')"
              item-text="name"
              item-value="name"
              clearable
              outlined
              dense
              hide-details
              class="item-manager__filter-select"
              style="max-width: 180px"
            >
              <template v-slot:prepend-inner>
                <v-icon small class="mr-1">mdi-sort-variant</v-icon>
              </template>
            </v-select>
            <v-btn
              outlined
              color="grey"
              class="text-none rounded-lg"
              @click="loadItems"
              :loading="loading"
            >
              <v-icon left small>mdi-refresh</v-icon>
              {{ __("Refresh") }}
            </v-btn>
          </div>
        </v-col>
      </v-row>

      <!-- Items Table -->
      <v-data-table
        :headers="headers"
        :items="filteredItems"
        :loading="loading"
        :items-per-page="15"
        class="item-manager__table elevation-0"
        :search="searchQuery"
      >
        <template v-slot:item.image="{ item }">
          <v-avatar size="36" class="my-1" color="#F4F6FB">
            <v-img v-if="item.image" :src="item.image"></v-img>
            <v-icon v-else color="grey lighten-1" small
              >mdi-image-outline</v-icon
            >
          </v-avatar>
        </template>

        <template v-slot:item.item_name="{ item }">
          <div class="py-1">
            <div class="item-manager__name-primary">{{ item.item_name }}</div>
            <div
              class="item-manager__name-secondary"
              v-if="item.custom_item_name_arabic"
            >
              {{ item.custom_item_name_arabic }}
            </div>
          </div>
        </template>

        <template v-slot:item.enabled_item_bundle="{ item }">
          <v-chip
            :color="item.enabled_item_bundle ? '#EDE7F6' : '#F5F5F5'"
            :text-color="item.enabled_item_bundle ? '#5E60CE' : '#8A94A6'"
            small
            label
            class="font-weight-medium"
          >
            {{ item.enabled_item_bundle ? __("Bundle") : __("Normal") }}
          </v-chip>
        </template>

        <template v-slot:item.standard_rate="{ item }">
          <span class="font-weight-medium">{{
            formatCurrency(item.standard_rate)
          }}</span>
        </template>

        <template v-slot:item.disabled="{ item }">
          <v-chip
            :color="item.disabled ? '#FFEBEE' : '#E8F5E9'"
            :text-color="item.disabled ? '#C62828' : '#2E7D32'"
            small
            label
            class="font-weight-medium"
          >
            {{ item.disabled ? __("Disabled") : __("Active") }}
          </v-chip>
        </template>

        <template v-slot:item.actions="{ item }">
          <div class="d-flex align-center justify-center" style="gap: 2px">
            <v-btn
              icon
              x-small
              class="item-manager__action-btn"
              @click="editItem(item)"
              :title="__('Edit')"
            >
              <v-icon small>mdi-pencil-outline</v-icon>
            </v-btn>
            <v-btn
              icon
              x-small
              class="item-manager__action-btn"
              @click="viewBundleOptions(item)"
              :title="__('View Bundle')"
              v-if="item.enabled_item_bundle"
            >
              <v-icon small>mdi-eye-outline</v-icon>
            </v-btn>
            <v-btn
              icon
              x-small
              class="item-manager__action-btn"
              @click="duplicateItem(item)"
              :title="__('Duplicate')"
            >
              <v-icon small>mdi-content-copy</v-icon>
            </v-btn>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Add/Edit Item Dialog -->
    <v-dialog v-model="itemDialog" max-width="1000px" persistent scrollable>
      <v-card>
        <v-card-title class="primary white--text">
          <span>{{ isEditing ? __("Edit Item") : __("Add New Item") }}</span>
          <v-spacer></v-spacer>
          <v-btn icon dark @click="closeItemDialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-card-text class="pa-4" style="max-height: 70vh; overflow-y: auto">
          <v-form ref="itemForm" v-model="formValid">
            <!-- Basic Information -->
            <v-row>
              <v-col cols="12">
                <h3 class="mb-3 primary--text">
                  <v-icon color="primary" class="mr-1">mdi-information</v-icon>
                  {{ __("Basic Information") }}
                </h3>
                <v-divider class="mb-3"></v-divider>
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="currentItem.item_code"
                  :label="__('Item Code')"
                  :rules="[rules.required]"
                  outlined
                  dense
                  :disabled="isEditing"
                  prepend-inner-icon="mdi-barcode"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="currentItem.item_name"
                  :label="__('Item Name (English)')"
                  :rules="[rules.required]"
                  outlined
                  dense
                  prepend-inner-icon="mdi-tag"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="currentItem.item_name_arabic"
                  :label="__('Item Name (Arabic)')"
                  outlined
                  dense
                  dir="rtl"
                  prepend-inner-icon="mdi-abjad-arabic"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-autocomplete
                  v-model="currentItem.item_group"
                  :items="itemGroups"
                  :label="__('Item Group')"
                  :rules="[rules.required]"
                  item-text="name"
                  item-value="name"
                  outlined
                  dense
                  prepend-inner-icon="mdi-folder"
                ></v-autocomplete>
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="4">
                <v-autocomplete
                  v-model="currentItem.item_classification"
                  :items="itemClassifications"
                  :label="__('Item Classification')"
                  item-text="name"
                  item-value="name"
                  outlined
                  dense
                  clearable
                  prepend-inner-icon="mdi-shape"
                ></v-autocomplete>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model.number="currentItem.standard_rate"
                  :label="__('Price')"
                  type="number"
                  outlined
                  dense
                  prepend-inner-icon="mdi-currency-usd"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="currentItem.image"
                  :label="__('Image URL')"
                  outlined
                  dense
                  prepend-inner-icon="mdi-image"
                ></v-text-field>
              </v-col>
            </v-row>

            <!-- Bundle Settings -->
            <v-row class="mt-4">
              <v-col cols="12">
                <h3 class="mb-3 primary--text">
                  <v-icon color="primary" class="mr-1"
                    >mdi-package-variant</v-icon
                  >
                  {{ __("Bundle Settings") }}
                </h3>
                <v-divider class="mb-3"></v-divider>
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="3">
                <v-switch
                  v-model="currentItem.enabled_item_bundle"
                  :label="__('Enable Bundle Options')"
                  color="primary"
                  inset
                ></v-switch>
              </v-col>
              <v-col cols="12" md="3">
                <v-switch
                  v-model="currentItem.enable_product_bundle"
                  :label="__('Enable Product Bundle')"
                  color="warning"
                  inset
                ></v-switch>
              </v-col>
              <v-col cols="12" md="3">
                <v-switch
                  v-model="currentItem.custom_fast_sell"
                  :label="__('Fast Sell (Skip Dialog)')"
                  color="success"
                  inset
                  :disabled="!currentItem.enabled_item_bundle"
                ></v-switch>
              </v-col>
            </v-row>

            <!-- Bundle Options -->
            <template v-if="currentItem.enabled_item_bundle">
              <v-row class="mt-4">
                <v-col cols="12">
                  <div class="d-flex align-center justify-space-between">
                    <h3 class="primary--text">
                      <v-icon color="primary" class="mr-1"
                        >mdi-format-list-bulleted</v-icon
                      >
                      {{ __("Bundle Options") }}
                    </h3>
                    <v-btn color="success" small @click="addBundleOption">
                      <v-icon left small>mdi-plus</v-icon>
                      {{ __("Add Option") }}
                    </v-btn>
                  </div>
                  <v-divider class="my-3"></v-divider>
                </v-col>
              </v-row>

              <v-row
                v-for="(opt, index) in currentItem.bundle_options"
                :key="index"
                class="bundle-option-row"
              >
                <v-col cols="12" md="2">
                  <v-autocomplete
                    v-model="opt.item_code"
                    :items="availableItems"
                    :label="__('Item')"
                    item-text="item_name"
                    item-value="item_code"
                    outlined
                    dense
                    hide-details
                    @change="onBundleItemSelect(opt, $event)"
                  ></v-autocomplete>
                </v-col>
                <v-col cols="12" md="2">
                  <v-autocomplete
                    v-model="opt.item_classification"
                    :items="itemClassifications"
                    :label="__('Classification')"
                    item-text="name"
                    item-value="name"
                    outlined
                    dense
                    hide-details
                  ></v-autocomplete>
                </v-col>
                <v-col cols="12" md="1">
                  <v-text-field
                    v-model.number="opt.qty"
                    :label="__('Qty')"
                    type="number"
                    outlined
                    dense
                    hide-details
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="1">
                  <v-text-field
                    v-model.number="opt.max_required"
                    :label="__('Max')"
                    type="number"
                    outlined
                    dense
                    hide-details
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="1">
                  <v-text-field
                    v-model.number="opt.rate"
                    :label="__('Rate')"
                    type="number"
                    outlined
                    dense
                    hide-details
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="2">
                  <v-select
                    v-model="opt.state"
                    :items="stateOptions"
                    :label="__('State')"
                    outlined
                    dense
                    hide-details
                  ></v-select>
                </v-col>
                <v-col
                  cols="12"
                  md="2"
                  v-if="opt.item_classification === 'Size'"
                >
                  <v-autocomplete
                    v-model="opt.custom_main_item"
                    :items="availableItems"
                    :label="__('Main Item')"
                    item-text="item_name"
                    item-value="item_code"
                    outlined
                    dense
                    hide-details
                    clearable
                  ></v-autocomplete>
                </v-col>
                <v-col
                  cols="6"
                  md="1"
                  class="d-flex align-center justify-center"
                >
                  <v-checkbox
                    v-model="opt.is_bundle"
                    :label="__('Bundle')"
                    dense
                    hide-details
                    class="mt-0 mr-0"
                  ></v-checkbox>
                </v-col>
                <v-col
                  cols="6"
                  md="1"
                  class="d-flex align-center justify-center"
                >
                  <v-checkbox
                    v-model="opt.hide_from_pos"
                    :label="__('Hide')"
                    dense
                    hide-details
                    class="mt-0 mr-0"
                  ></v-checkbox>
                </v-col>
                <v-col cols="12" md="1" class="d-flex align-center">
                  <v-btn
                    icon
                    small
                    color="error"
                    @click="removeBundleOption(index)"
                  >
                    <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </v-col>
              </v-row>

              <v-row v-if="currentItem.bundle_options.length === 0">
                <v-col cols="12">
                  <v-alert type="info" text>
                    {{
                      __(
                        "No bundle options added yet. Click 'Add Option' to add items to this bundle.",
                      )
                    }}
                  </v-alert>
                </v-col>
              </v-row>
            </template>

            <!-- Product Bundle (Stock Items) -->
            <template v-if="currentItem.enable_product_bundle">
              <v-row class="mt-6">
                <v-col cols="12">
                  <div class="d-flex align-center justify-space-between">
                    <h3 class="warning--text">
                      <v-icon color="warning" class="mr-1"
                        >mdi-warehouse</v-icon
                      >
                      {{ __("Product Bundle (Stock Items)") }}
                    </h3>
                    <v-btn color="warning" small @click="addStockItem">
                      <v-icon left small>mdi-plus</v-icon>
                      {{ __("Add Stock Item") }}
                    </v-btn>
                  </div>
                  <p class="text-caption grey--text mt-1">
                    {{ __("Items that will be deducted from stock when sold") }}
                  </p>
                  <v-divider class="my-3"></v-divider>
                </v-col>
              </v-row>

              <v-row
                v-for="(item, index) in currentItem.stock_items"
                :key="'stock-' + index"
                class="stock-item-row"
              >
                <v-col cols="12" md="3">
                  <v-autocomplete
                    v-model="item.item_code"
                    :items="stockItems"
                    :label="__('Stock Item')"
                    item-text="item_name"
                    item-value="item_code"
                    outlined
                    dense
                    hide-details
                    @change="onStockItemSelect(item, $event)"
                  ></v-autocomplete>
                </v-col>
                <v-col cols="6" md="1">
                  <v-text-field
                    v-model.number="item.qty"
                    :label="__('Qty')"
                    type="number"
                    outlined
                    dense
                    hide-details
                  ></v-text-field>
                </v-col>
                <v-col cols="6" md="1">
                  <v-text-field
                    v-model="item.uom"
                    :label="__('UOM')"
                    outlined
                    dense
                    hide-details
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="2">
                  <v-autocomplete
                    v-model="item.custom_product_item_classification"
                    :items="productItemClassifications"
                    :label="__('Classification')"
                    item-text="name"
                    item-value="name"
                    outlined
                    dense
                    hide-details
                    clearable
                  ></v-autocomplete>
                </v-col>
                <v-col cols="12" md="2">
                  <v-autocomplete
                    v-model="item.custom_teigger_item"
                    :items="availableItems"
                    :label="__('Trigger 1')"
                    item-text="item_name"
                    item-value="item_code"
                    outlined
                    dense
                    hide-details
                    clearable
                  ></v-autocomplete>
                </v-col>
                <v-col cols="12" md="2">
                  <v-autocomplete
                    v-model="item.custom_teigger_item_2"
                    :items="availableItems"
                    :label="__('Trigger 2')"
                    item-text="item_name"
                    item-value="item_code"
                    outlined
                    dense
                    hide-details
                    clearable
                  ></v-autocomplete>
                </v-col>
              </v-row>
              <v-row
                v-for="(item, index) in currentItem.stock_items"
                :key="'stock-check-' + index"
                class="stock-item-row mt-0 pt-0"
                style="margin-top: -8px !important"
              >
                <v-col cols="12" md="5"></v-col>
                <v-col cols="4" md="2" class="d-flex align-center">
                  <v-checkbox
                    v-model="item.custom_spicy"
                    :label="__('Spicy')"
                    dense
                    hide-details
                    class="mt-0"
                  ></v-checkbox>
                </v-col>
                <v-col cols="4" md="2" class="d-flex align-center">
                  <v-checkbox
                    v-model="item.custom_regular"
                    :label="__('Regular')"
                    dense
                    hide-details
                    class="mt-0"
                  ></v-checkbox>
                </v-col>
                <v-col cols="4" md="1" class="d-flex align-center">
                  <v-btn
                    icon
                    small
                    color="error"
                    @click="removeStockItem(index)"
                  >
                    <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </v-col>
              </v-row>

              <v-row v-if="currentItem.stock_items.length === 0">
                <v-col cols="12">
                  <v-alert type="warning" text>
                    {{
                      __(
                        "No stock items added yet. Add items that will be deducted from inventory.",
                      )
                    }}
                  </v-alert>
                </v-col>
              </v-row>
            </template>
          </v-form>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions class="pa-4">
          <v-btn color="grey" text @click="closeItemDialog">
            <v-icon left>mdi-close</v-icon>
            {{ __("Cancel") }}
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            @click="saveItem"
            :loading="saving"
            :disabled="!formValid"
          >
            <v-icon left>mdi-content-save</v-icon>
            {{ isEditing ? __("Update") : __("Create") }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- View Bundle Options Dialog -->
    <v-dialog v-model="viewBundleDialog" max-width="800px">
      <v-card>
        <v-card-title class="primary white--text">
          <v-icon dark class="mr-2">mdi-package-variant</v-icon>
          {{ __("Bundle Options for") }}: {{ viewingItem.item_name }}
          <v-spacer></v-spacer>
          <v-btn icon dark @click="viewBundleDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-4">
          <v-data-table
            :headers="bundleHeaders"
            :items="viewingItem.bundle_options || []"
            :items-per-page="10"
            class="elevation-1"
          >
            <template v-slot:item.is_bundle="{ item }">
              <v-icon :color="item.is_bundle ? 'success' : 'grey'">
                {{ item.is_bundle ? "mdi-check-circle" : "mdi-close-circle" }}
              </v-icon>
            </template>
            <template v-slot:item.custom_hide_from_pos="{ item }">
              <v-icon :color="item.custom_hide_from_pos ? 'warning' : 'grey'">
                {{ item.custom_hide_from_pos ? "mdi-eye-off" : "mdi-eye" }}
              </v-icon>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar
      v-model="snackbar"
      :color="snackbarColor"
      top
      right
      :timeout="3000"
    >
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbar = false">{{
          __("Close")
        }}</v-btn>
      </template>
    </v-snackbar>

    <!-- Product Editor Dialog -->
    <ProductEditor
      v-model="productEditorDialog"
      :edit-item="editingProduct"
      @saved="onProductSaved"
      @close="onProductEditorClose"
    />
  </v-container>
</template>

<script>
import ProductEditor from "./ProductEditor.vue";

export default {
  name: "ItemManager",
  components: {
    ProductEditor,
  },
  data() {
    return {
      loading: false,
      saving: false,
      searchQuery: "",
      filterGroup: null,
      filterClassification: null,
      items: [],
      itemGroups: [],
      itemClassifications: [],
      availableItems: [],
      stockItems: [],
      productItemClassifications: [],
      itemDialog: false,
      viewBundleDialog: false,
      isEditing: false,
      formValid: false,
      currentItem: this.getEmptyItem(),
      viewingItem: {},
      productEditorDialog: false,
      editingProduct: null,
      snackbar: false,
      snackbarColor: "success",
      snackbarText: "",
      searchTimeout: null,
      headers: [
        { text: "", value: "image", sortable: false, width: "50px" },
        { text: this.__("Item Code"), value: "item_code" },
        { text: this.__("Item Name"), value: "item_name", width: "220px" },
        { text: this.__("Group"), value: "item_group" },
        {
          text: this.__("Classification"),
          value: "custom_item_classification",
        },
        { text: this.__("Price"), value: "standard_rate", align: "end" },
        {
          text: this.__("Type"),
          value: "enabled_item_bundle",
          align: "center",
        },
        { text: this.__("Status"), value: "disabled", align: "center" },
        {
          text: this.__("Actions"),
          value: "actions",
          sortable: false,
          align: "center",
          width: "120px",
        },
      ],
      bundleHeaders: [
        { text: this.__("Item Code"), value: "item_code" },
        { text: this.__("Item Name"), value: "item_name" },
        { text: this.__("Classification"), value: "item_classification" },
        { text: this.__("Qty"), value: "qty", align: "center" },
        { text: this.__("Max"), value: "max_required", align: "center" },
        { text: this.__("Rate"), value: "rate", align: "end" },
        { text: this.__("State"), value: "state" },
        { text: this.__("Bundle"), value: "is_bundle", align: "center" },
        {
          text: this.__("Hidden"),
          value: "custom_hide_from_pos",
          align: "center",
        },
      ],
      stateOptions: [
        "",
        "Item Must Be Selected",
        "Minimum 1 Item is Required In Section",
      ],
      rules: {
        required: (v) => !!v || this.__("Required"),
      },
    };
  },

  computed: {
    filteredItems() {
      let result = this.items;
      if (this.filterGroup) {
        result = result.filter((i) => i.item_group === this.filterGroup);
      }
      if (this.filterClassification) {
        result = result.filter(
          (i) => i.custom_item_classification === this.filterClassification,
        );
      }
      return result;
    },
  },

  methods: {
    __(text) {
      return __(text);
    },

    formatCurrency(value) {
      return parseFloat(value || 0).toFixed(2);
    },

    getEmptyItem() {
      return {
        item_code: "",
        item_name: "",
        item_name_arabic: "",
        item_group: "",
        item_classification: "",
        standard_rate: 0,
        image: "",
        enabled_item_bundle: false,
        enable_product_bundle: false,
        custom_fast_sell: false,
        bundle_options: [],
        stock_items: [],
      };
    },

    showMessage(text, color = "success") {
      this.snackbarText = text;
      this.snackbarColor = color;
      this.snackbar = true;
    },

    debounceSearch() {
      clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(() => {
        // Search is handled by v-data-table
      }, 300);
    },

    async loadItems() {
      this.loading = true;
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_items_for_bundle",
        });
        this.items = res.message || [];
      } catch (e) {
        this.showMessage(e.message || "Error loading items", "error");
      }
      this.loading = false;
    },

    async loadItemGroups() {
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_item_groups",
        });
        this.itemGroups = res.message || [];
      } catch (e) {
        console.error(e);
      }
    },

    async loadItemClassifications() {
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_item_classifications",
        });
        this.itemClassifications = res.message || [];
      } catch (e) {
        console.error(e);
      }
    },

    openNewItemDialog() {
      this.$emit("add-item");
    },

    openNewItemDialogOld() {
      this.isEditing = false;
      this.currentItem = this.getEmptyItem();
      this.itemDialog = true;
    },

    async editItem(item) {
      this.$emit("edit-item", item);
    },

    onProductSaved() {
      this.loadItems();
      this.showMessage(__("Product saved successfully"));
    },

    onProductEditorClose() {
      this.editingProduct = null;
    },

    async editItemOld(item) {
      this.isEditing = true;
      this.loading = true;
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_item_with_options",
          args: { item_code: item.item_code },
        });
        if (res.message && res.message.success) {
          const data = res.message.item;
          this.currentItem = {
            item_code: data.item_code,
            item_name: data.item_name,
            item_name_arabic: data.item_name_arabic || "",
            item_group: data.item_group,
            item_classification: data.item_classification || "",
            standard_rate: data.standard_rate || 0,
            image: data.image || "",
            enabled_item_bundle: !!data.enabled_item_bundle,
            enable_product_bundle: !!data.enable_product_bundle,
            custom_fast_sell: !!data.custom_fast_sell,
            bundle_options: (data.bundle_options || []).map((opt) => ({
              item_code: opt.item_code,
              item_name: opt.item_name,
              item_classification: opt.item_classification,
              qty: opt.qty || 0,
              max_required: opt.max_required || 1,
              rate: opt.rate || 0,
              state: opt.state || "",
              is_bundle: !!opt.is_bundle,
              hide_from_pos: !!opt.custom_hide_from_pos,
              custom_main_item: opt.custom_main_item || "",
            })),
            stock_items: [],
          };
          // Load Product Bundle (stock items) if enabled
          if (this.currentItem.enable_product_bundle) {
            await this.loadProductBundle(item.item_code);
          }
          this.itemDialog = true;
        } else {
          this.showMessage(
            res.message?.message || "Error loading item",
            "error",
          );
        }
      } catch (e) {
        this.showMessage(e.message || "Error", "error");
      }
      this.loading = false;
    },

    async viewBundleOptions(item) {
      this.loading = true;
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_item_with_options",
          args: { item_code: item.item_code },
        });
        if (res.message && res.message.success) {
          this.viewingItem = res.message.item;
          this.viewBundleDialog = true;
        }
      } catch (e) {
        this.showMessage(e.message || "Error", "error");
      }
      this.loading = false;
    },

    duplicateItem(item) {
      this.isEditing = false;
      this.currentItem = {
        ...this.getEmptyItem(),
        item_name: item.item_name + " (Copy)",
        item_name_arabic: item.custom_item_name_arabic,
        item_group: item.item_group,
        item_classification: item.custom_item_classification,
        standard_rate: item.standard_rate,
      };
      this.itemDialog = true;
    },

    closeItemDialog() {
      this.itemDialog = false;
      this.currentItem = this.getEmptyItem();
      if (this.$refs.itemForm) {
        this.$refs.itemForm.resetValidation();
      }
    },

    addBundleOption() {
      this.currentItem.bundle_options.push({
        item_code: "",
        item_name: "",
        item_classification: "",
        qty: 0,
        max_required: 1,
        rate: 0,
        state: "",
        is_bundle: false,
        hide_from_pos: false,
        custom_main_item: "",
      });
    },

    removeBundleOption(index) {
      this.currentItem.bundle_options.splice(index, 1);
    },

    // Stock Items (Product Bundle) Methods
    addStockItem() {
      this.currentItem.stock_items.push({
        item_code: "",
        item_name: "",
        qty: 1,
        uom: "Unit",
        custom_product_item_classification: "",
        custom_teigger_item: "",
        custom_teigger_item_2: "",
        custom_spicy: false,
        custom_regular: false,
        custom_hide: false,
      });
    },

    removeStockItem(index) {
      this.currentItem.stock_items.splice(index, 1);
    },

    onStockItemSelect(item, itemCode) {
      const found = this.stockItems.find((i) => i.item_code === itemCode);
      if (found) {
        item.item_name = found.item_name;
        item.uom = found.stock_uom || "Unit";
      }
    },

    async loadStockItems() {
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_stock_items",
        });
        this.stockItems = res.message || [];
      } catch (e) {
        console.error(e);
      }
    },

    async loadProductItemClassifications() {
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_product_item_classifications",
        });
        this.productItemClassifications = res.message || [];
      } catch (e) {
        console.error(e);
      }
    },

    onBundleItemSelect(opt, itemCode) {
      const found = this.availableItems.find((i) => i.item_code === itemCode);
      if (found) {
        opt.item_name = found.item_name;
      }
    },

    async loadProductBundle(itemCode) {
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_product_bundle",
          args: { item_code: itemCode },
        });
        if (res.message && res.message.success && res.message.exists) {
          this.currentItem.stock_items = (res.message.items || []).map(
            (item) => ({
              item_code: item.item_code,
              item_name: item.item_name,
              qty: item.qty || 1,
              uom: item.uom || "Unit",
              custom_product_item_classification:
                item.custom_product_item_classification || "",
              custom_teigger_item: item.custom_teigger_item || "",
              custom_teigger_item_2: item.custom_teigger_item_2 || "",
              custom_spicy: !!item.custom_spicy,
              custom_regular: !!item.custom_regular,
              custom_hide: !!item.custom_hide,
            }),
          );
        }
      } catch (e) {
        console.error(e);
      }
    },

    async saveProductBundle() {
      if (
        this.currentItem.enable_product_bundle &&
        this.currentItem.stock_items.length > 0
      ) {
        await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.create_product_bundle",
          args: {
            item_code: this.currentItem.item_code,
            items: this.currentItem.stock_items,
          },
        });
      } else if (!this.currentItem.enable_product_bundle) {
        // Delete Product Bundle if disabled
        await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.delete_product_bundle",
          args: { item_code: this.currentItem.item_code },
        });
      }
    },

    onBundleItemSelect(opt, itemCode) {
      const found = this.availableItems.find((i) => i.item_code === itemCode);
      if (found) {
        opt.item_name = found.item_name;
        opt.item_classification = found.custom_item_classification || "";
        opt.rate = found.standard_rate || 0;
      }
    },

    async saveItem() {
      if (!this.$refs.itemForm.validate()) return;
      this.saving = true;

      try {
        let res;
        if (this.isEditing) {
          // Update existing item
          await frappe.call({
            method: "ecs_posnext.ecs_posnext.custom_api.item_manager.update_item",
            args: {
              item_code: this.currentItem.item_code,
              updates: {
                item_name: this.currentItem.item_name,
                custom_item_name_arabic: this.currentItem.item_name_arabic,
                item_group: this.currentItem.item_group,
                custom_item_classification:
                  this.currentItem.item_classification,
                standard_rate: this.currentItem.standard_rate,
                image: this.currentItem.image,
                enabled_item_bundle: this.currentItem.enabled_item_bundle
                  ? 1
                  : 0,
                custom_fast_sell: this.currentItem.custom_fast_sell ? 1 : 0,
              },
            },
          });

          // Update bundle options
          if (this.currentItem.enabled_item_bundle) {
            await frappe.call({
              method:
                "ecs_posnext.ecs_posnext.custom_api.item_manager.clear_bundle_options",
              args: { item_code: this.currentItem.item_code },
            });
            for (const opt of this.currentItem.bundle_options) {
              await frappe.call({
                method:
                  "ecs_posnext.ecs_posnext.custom_api.item_manager.add_bundle_option",
                args: {
                  item_code: this.currentItem.item_code,
                  option: opt,
                },
              });
            }
          }
          // Save Product Bundle (stock items)
          await this.saveProductBundle();
          this.showMessage(__("Item updated successfully"));
        } else {
          // Create new item
          if (
            this.currentItem.enabled_item_bundle &&
            this.currentItem.bundle_options.length > 0
          ) {
            res = await frappe.call({
              method:
                "ecs_posnext.ecs_posnext.custom_api.item_manager.create_bundle_item",
              args: {
                item_code: this.currentItem.item_code,
                item_name: this.currentItem.item_name,
                item_group: this.currentItem.item_group,
                item_name_arabic: this.currentItem.item_name_arabic,
                standard_rate: this.currentItem.standard_rate,
                image: this.currentItem.image,
                custom_fast_sell: this.currentItem.custom_fast_sell ? 1 : 0,
                bundle_options: this.currentItem.bundle_options,
              },
            });
          } else {
            res = await frappe.call({
              method:
                "ecs_posnext.ecs_posnext.custom_api.item_manager.create_item",
              args: {
                item_code: this.currentItem.item_code,
                item_name: this.currentItem.item_name,
                item_group: this.currentItem.item_group,
                item_name_arabic: this.currentItem.item_name_arabic,
                item_classification: this.currentItem.item_classification,
                standard_rate: this.currentItem.standard_rate,
                image: this.currentItem.image,
                enabled_item_bundle: this.currentItem.enabled_item_bundle
                  ? 1
                  : 0,
                custom_fast_sell: this.currentItem.custom_fast_sell ? 1 : 0,
              },
            });
          }
          if (res.message && res.message.success) {
            // Save Product Bundle for new item
            await this.saveProductBundle();
            this.showMessage(res.message.message);
          } else {
            this.showMessage(res.message?.message || "Error", "error");
            this.saving = false;
            return;
          }
        }

        this.closeItemDialog();
        this.loadItems();
      } catch (e) {
        this.showMessage(e.message || "Error saving item", "error");
      }
      this.saving = false;
    },
  },

  mounted() {
    this.loadItems();
    this.loadItemGroups();
    this.loadItemClassifications();
    this.loadStockItems();
    this.loadProductItemClassifications();
    // Load available items for bundle selection
    this.loadItems().then(() => {
      this.availableItems = this.items;
    });
  },
};
</script>

<style scoped>
/* ===== Layout & Container ===== */
.item-manager {
  background: #f4f6fb;
  min-height: 100vh;
}

.item-manager__title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1a1a2e;
  letter-spacing: -0.02em;
}

.item-manager__content-card {
  border: 1px solid #e0e6f0;
}

/* ===== Search Field ===== */
.item-manager__search >>> .v-input__slot {
  border: none !important;
  box-shadow: none !important;
  min-height: 38px !important;
}

.item-manager__search >>> .v-input__slot::before,
.item-manager__search >>> .v-input__slot::after {
  display: none !important;
}

/* ===== Filter Selects ===== */
.item-manager__filter-select >>> .v-input__slot {
  min-height: 36px !important;
}

/* ===== Data Table ===== */
.item-manager__table {
  border-radius: 0;
}

.item-manager__table >>> table {
  border-collapse: collapse;
}

.item-manager__table >>> thead tr th {
  background: #f8f9fc !important;
  color: #8a94a6 !important;
  font-weight: 600 !important;
  font-size: 0.75rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.04em !important;
  border-bottom: 1px solid #e0e6f0 !important;
  padding-top: 14px !important;
  padding-bottom: 14px !important;
  white-space: nowrap;
}

.item-manager__table >>> tbody tr td {
  border-bottom: 1px solid #f0f2f8 !important;
  padding-top: 14px !important;
  padding-bottom: 14px !important;
  font-size: 0.875rem;
  color: #3a3a4a;
  vertical-align: middle;
}

/* Remove all vertical borders */
.item-manager__table >>> thead tr th,
.item-manager__table >>> tbody tr td {
  border-left: none !important;
  border-right: none !important;
}

/* Row hover */
.item-manager__table >>> tbody tr:hover {
  background: #f0f4ff !important;
}

/* Row selection (via checkbox) */
.item-manager__table >>> tbody tr.v-data-table__selected {
  background: #e8eeff !important;
}

/* ===== Combined Name Column ===== */
.item-manager__name-primary {
  font-weight: 500;
  color: #1a1a2e;
  font-size: 0.875rem;
  line-height: 1.4;
}

.item-manager__name-secondary {
  font-size: 0.775rem;
  color: #8a94a6;
  line-height: 1.3;
  margin-top: 2px;
}

/* ===== Action Buttons ===== */
.item-manager__action-btn {
  color: #8a94a6 !important;
  transition: all 0.15s ease;
}

.item-manager__action-btn:hover {
  color: #3a3a4a !important;
  background: #f0f2f8 !important;
}

/* ===== Table Footer / Pagination ===== */
.item-manager__table >>> .v-data-footer {
  border-top: 1px solid #e0e6f0;
  padding: 8px 16px;
}

/* ===== Dialog Styling ===== */
.item-manager >>> .v-dialog > .v-card {
  border-radius: 14px !important;
  overflow: hidden;
}

.item-manager >>> .v-dialog .v-card__title {
  background: #17223b !important;
  color: white !important;
  font-size: 16px !important;
  font-weight: 700 !important;
  padding: 16px 24px !important;
  border-bottom: none !important;
}

.item-manager >>> .v-dialog .v-card__title .v-icon {
  color: white !important;
}

.item-manager >>> .v-dialog .v-card__text {
  padding: 24px !important;
}

.item-manager >>> .v-dialog .v-card__actions {
  padding: 14px 24px !important;
  border-top: 1px solid #e0e6f0 !important;
  background: #ffffff !important;
}

/* ===== Dialog Input Overrides ===== */
.item-manager >>> .v-dialog .v-text-field--outlined fieldset,
.item-manager >>> .v-dialog .v-select--outlined fieldset,
.item-manager >>> .v-dialog .v-autocomplete--outlined fieldset {
  border-color: #e0e6f0 !important;
  border-radius: 10px !important;
  border-width: 1px !important;
}

.item-manager >>> .v-dialog .v-text-field--outlined .v-input__slot,
.item-manager >>> .v-dialog .v-select--outlined .v-input__slot,
.item-manager >>> .v-dialog .v-autocomplete--outlined .v-input__slot {
  background: #f7f8fa !important;
  min-height: 40px !important;
}

.item-manager
  >>> .v-dialog
  .v-text-field--outlined.v-input--is-focused
  fieldset,
.item-manager >>> .v-dialog .v-select--outlined.v-input--is-focused fieldset,
.item-manager
  >>> .v-dialog
  .v-autocomplete--outlined.v-input--is-focused
  fieldset {
  border-color: #5e60ce !important;
  box-shadow: 0 0 0 2px rgba(94, 96, 206, 0.12) !important;
}

.item-manager >>> .v-dialog .v-input__slot input,
.item-manager >>> .v-dialog .v-select__selection {
  font-size: 13.5px !important;
  color: #2d3348 !important;
}

.item-manager >>> .v-dialog .v-label {
  font-size: 13px !important;
  color: #8a94a6 !important;
}

/* ===== Dialog Switches ===== */
.item-manager
  >>> .v-dialog
  .v-input--switch
  .v-input--selection-controls__input {
  transform: scale(0.85);
}

/* ===== Dialog Section Headers ===== */
.item-manager >>> .v-dialog h3 {
  font-size: 14px !important;
  font-weight: 700 !important;
  letter-spacing: -0.01em;
}

/* ===== Dialog Rows ===== */
.bundle-option-row {
  background: #f7f8fa;
  border-radius: 10px;
  margin-bottom: 8px;
  padding: 10px 0;
  border: 1px solid #e0e6f0;
  transition: border-color 0.15s ease;
}

.bundle-option-row:hover {
  border-color: #5e60ce;
  background: #f0f2f8;
}

.stock-item-row {
  background: #fffbf0;
  border-radius: 10px;
  margin-bottom: 8px;
  padding: 10px 0;
  border: 1px solid #e0e6f0;
  border-left: 3px solid #f59e0b;
}

.stock-item-row:hover {
  background: #fff8e1;
}

/* ===== View Bundle Dialog Table ===== */
.item-manager >>> .v-dialog .v-data-table {
  border-radius: 10px !important;
  border: 1px solid #e0e6f0 !important;
  box-shadow: none !important;
}

.item-manager >>> .v-dialog .v-data-table thead th {
  background: #f7f8fa !important;
  color: #8a94a6 !important;
  font-weight: 600 !important;
  font-size: 11px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.04em !important;
  border-bottom: 1px solid #e0e6f0 !important;
}

.item-manager >>> .v-dialog .v-data-table tbody td {
  border-bottom: 1px solid #f0f2f8 !important;
  font-size: 13px !important;
  color: #2d3348 !important;
}
</style>
