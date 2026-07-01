<template>
  <v-dialog v-model="dialog" max-width="900px" persistent scrollable>
    <v-card>
      <!-- Header -->
      <v-card-title class="primary white--text d-flex align-center">
        <v-icon dark class="mr-2">mdi-chef-hat</v-icon>
        <div>
          <div>{{ __("Product Recipe") }}</div>
          <div class="text-caption font-weight-regular">{{ productName }}</div>
        </div>
        <v-spacer></v-spacer>
        <v-btn icon dark @click="closeDialog">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text class="pa-4" style="max-height: 65vh; overflow-y: auto">
        <!-- Info Alert -->
        <v-alert type="info" text dense class="mb-4">
          {{
            __(
              "Add stock items that will be deducted from inventory when this product is sold.",
            )
          }}
        </v-alert>

        <!-- Add Item Button -->
        <div class="d-flex justify-end mb-3">
          <v-btn color="primary" small @click="addRecipeItem">
            <v-icon left small>mdi-plus</v-icon>
            {{ __("Add Ingredient") }}
          </v-btn>
        </div>

        <!-- Recipe Items Table -->
        <v-simple-table v-if="recipeItems.length > 0" class="recipe-table">
          <template v-slot:default>
            <thead>
              <tr>
                <th style="width: 30%">{{ __("Stock Item") }}</th>
                <th style="width: 12%">{{ __("Qty") }}</th>
                <th style="width: 12%">{{ __("UOM") }}</th>
                <th style="width: 20%">{{ __("Classification") }}</th>
                <th style="width: 18%">{{ __("Trigger Item") }}</th>
                <th style="width: 8%"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in recipeItems" :key="index">
                <td>
                  <v-autocomplete
                    v-model="item.item_code"
                    :items="stockItems"
                    item-text="item_name"
                    item-value="item_code"
                    outlined
                    dense
                    hide-details
                    @change="onStockItemSelect(item, $event)"
                  ></v-autocomplete>
                </td>
                <td>
                  <v-text-field
                    v-model.number="item.qty"
                    type="number"
                    outlined
                    dense
                    hide-details
                    min="0"
                    step="0.01"
                  ></v-text-field>
                </td>
                <td>
                  <v-text-field
                    v-model="item.uom"
                    outlined
                    dense
                    hide-details
                  ></v-text-field>
                </td>
                <td>
                  <v-autocomplete
                    v-model="item.custom_product_item_classification"
                    :items="classifications"
                    item-text="name"
                    item-value="name"
                    outlined
                    dense
                    hide-details
                    clearable
                  ></v-autocomplete>
                </td>
                <td>
                  <v-autocomplete
                    v-model="item.custom_teigger_item"
                    :items="triggerItems"
                    item-text="item_name"
                    item-value="item_code"
                    outlined
                    dense
                    hide-details
                    clearable
                    :placeholder="__('Optional')"
                  ></v-autocomplete>
                </td>
                <td class="text-center">
                  <v-btn
                    icon
                    small
                    color="error"
                    @click="removeRecipeItem(index)"
                  >
                    <v-icon small>mdi-delete</v-icon>
                  </v-btn>
                </td>
              </tr>
              <!-- Additional Options Row -->
              <tr
                v-for="(item, index) in recipeItems"
                :key="'opts-' + index"
                class="options-row"
              >
                <td colspan="6" class="pa-2">
                  <div class="d-flex align-center">
                    <span class="text-caption grey--text mr-4"
                      >{{ __("Options") }}:</span
                    >
                    <v-checkbox
                      v-model="item.custom_spicy"
                      :label="__('Spicy')"
                      dense
                      hide-details
                      class="mt-0 mr-4"
                    ></v-checkbox>
                    <v-checkbox
                      v-model="item.custom_regular"
                      :label="__('Regular')"
                      dense
                      hide-details
                      class="mt-0 mr-4"
                    ></v-checkbox>
                    <v-checkbox
                      v-model="item.custom_hide"
                      :label="__('Hide from POS')"
                      dense
                      hide-details
                      class="mt-0"
                    ></v-checkbox>
                  </div>
                </td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>

        <!-- Empty State -->
        <div v-else class="text-center pa-8 grey--text">
          <v-icon size="64" color="grey lighten-2">mdi-package-variant</v-icon>
          <div class="mt-3 text-h6">{{ __("No ingredients added") }}</div>
          <div class="text-caption">
            {{ __("Add stock items that make up this product") }}
          </div>
        </div>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-4">
        <v-btn
          text
          color="error"
          @click="clearAllItems"
          v-if="recipeItems.length > 0"
        >
          <v-icon left small>mdi-delete-sweep</v-icon>
          {{ __("Clear All") }}
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn outlined @click="closeDialog">
          {{ __("Cancel") }}
        </v-btn>
        <v-btn color="primary" @click="saveRecipe" :loading="saving">
          <v-icon left small>mdi-content-save</v-icon>
          {{ __("Save Recipe") }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: "RecipeDialog",
  props: {
    value: {
      type: Boolean,
      default: false,
    },
    itemCode: {
      type: String,
      default: "",
    },
    productName: {
      type: String,
      default: "",
    },
    variantName: {
      type: String,
      default: "",
    },
  },
  data() {
    return {
      dialog: false,
      saving: false,
      loading: false,
      recipeItems: [],
      stockItems: [],
      classifications: [],
      triggerItems: [],
    };
  },
  watch: {
    value(val) {
      this.dialog = val;
      if (val) {
        // Use nextTick to ensure itemCode prop is updated
        this.$nextTick(() => {
          this.loadData();
        });
      }
    },
    dialog(val) {
      this.$emit("input", val);
    },
    itemCode: {
      handler(val) {
        // Reload data when itemCode changes while dialog is open
        if (val && this.dialog) {
          this.loadData();
        }
      },
      immediate: false,
    },
  },
  methods: {
    __(text) {
      return __(text);
    },

    async loadData() {
      this.loading = true;
      await Promise.all([
        this.loadStockItems(),
        this.loadClassifications(),
        this.loadTriggerItems(),
        this.loadExistingRecipe(),
      ]);
      this.loading = false;
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

    async loadClassifications() {
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_product_item_classifications",
        });
        this.classifications = res.message || [];
      } catch (e) {
        console.error(e);
      }
    },

    async loadTriggerItems() {
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_items_for_bundle",
        });
        this.triggerItems = res.message || [];
      } catch (e) {
        console.error(e);
      }
    },

    async loadExistingRecipe() {
      console.log("Loading recipe for item:", this.itemCode);
      if (!this.itemCode) {
        console.log("No itemCode provided");
        this.recipeItems = [];
        return;
      }

      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_product_bundle",
          args: { item_code: this.itemCode },
        });

        console.log("Recipe response:", res.message);

        if (res.message && res.message.success && res.message.exists) {
          this.recipeItems = (res.message.items || []).map((item) => ({
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
          }));
          console.log("Loaded recipe items:", this.recipeItems.length);
        } else {
          this.recipeItems = [];
          console.log("No existing recipe found");
        }
      } catch (e) {
        console.error("Error loading recipe:", e);
        this.recipeItems = [];
      }
    },

    addRecipeItem() {
      this.recipeItems.push({
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

    removeRecipeItem(index) {
      this.recipeItems.splice(index, 1);
    },

    onStockItemSelect(item, itemCode) {
      const found = this.stockItems.find((i) => i.item_code === itemCode);
      if (found) {
        item.item_name = found.item_name;
        item.uom = found.stock_uom || "Unit";
      }
    },

    clearAllItems() {
      if (confirm(this.__("Are you sure you want to clear all ingredients?"))) {
        this.recipeItems = [];
      }
    },

    closeDialog() {
      this.dialog = false;
      this.$emit("close");
    },

    async saveRecipe() {
      console.log("Saving recipe for item:", this.itemCode);
      console.log("Recipe items to save:", this.recipeItems);

      if (!this.itemCode) {
        frappe.show_alert({
          message: this.__("Please save the product first"),
          indicator: "orange",
        });
        return;
      }

      this.saving = true;
      try {
        if (this.recipeItems.length > 0) {
          // Create or update Product Bundle
          console.log("Calling create_product_bundle API...");
          const res = await frappe.call({
            method:
              "ecs_posnext.ecs_posnext.custom_api.item_manager.create_product_bundle",
            args: {
              item_code: this.itemCode,
              items: this.recipeItems,
            },
          });

          console.log("Save response:", res.message);

          if (res.message && res.message.success) {
            frappe.show_alert({
              message: this.__("Recipe saved successfully"),
              indicator: "green",
            });
            this.$emit("saved", this.recipeItems);
            this.closeDialog();
          } else {
            throw new Error(res.message?.message || "Error saving recipe");
          }
        } else {
          // Delete Product Bundle if no items
          await frappe.call({
            method:
              "ecs_posnext.ecs_posnext.custom_api.item_manager.delete_product_bundle",
            args: { item_code: this.itemCode },
          });
          frappe.show_alert({
            message: this.__("Recipe cleared"),
            indicator: "blue",
          });
          this.$emit("saved", []);
          this.closeDialog();
        }
      } catch (e) {
        console.error(e);
        frappe.show_alert({
          message: e.message || "Error saving recipe",
          indicator: "red",
        });
      }
      this.saving = false;
    },
  },
};
</script>

<style scoped>
/* ===== Local Theme Tokens ===== */
.v-dialog > .v-card {
  --im-bg: #f4f6fb;
  --im-card: #ffffff;
  --im-border: #e0e6f0;
  --im-border-light: #f0f2f8;
  --im-muted: #8a94a6;
  --im-primary: #17223b;
  --im-accent: #5e60ce;
  --im-radius: 14px;
  --im-radius-sm: 10px;
  --im-radius-input: 10px;
  --im-input-bg: #f7f8fa;
  --im-input-border: #e0e6f0;
  --im-text: #2d3348;

  border-radius: var(--im-radius) !important;
}

/* ===== Recipe Table ===== */
.recipe-table {
  border: 1px solid var(--im-border);
  border-radius: var(--im-radius-sm);
  overflow: hidden;
}

.recipe-table th {
  background: var(--im-input-bg) !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--im-muted) !important;
  border-bottom: 1px solid var(--im-border) !important;
  padding: 10px 12px !important;
}

.recipe-table td {
  padding: 10px 12px !important;
  border-bottom: 1px solid var(--im-border-light) !important;
  font-size: 13px;
  color: var(--im-text);
}

.options-row {
  background: var(--im-input-bg);
}

.options-row td {
  border-top: none !important;
  padding-top: 4px !important;
  padding-bottom: 10px !important;
}

/* ===== Input Overrides ===== */
.recipe-table >>> .v-text-field--outlined fieldset,
.recipe-table >>> .v-select--outlined fieldset,
.recipe-table >>> .v-autocomplete--outlined fieldset {
  border-color: var(--im-input-border) !important;
  border-radius: var(--im-radius-input) !important;
  border-width: 1px !important;
}

.recipe-table >>> .v-text-field--outlined .v-input__slot,
.recipe-table >>> .v-select--outlined .v-input__slot,
.recipe-table >>> .v-autocomplete--outlined .v-input__slot {
  background: var(--im-card) !important;
  min-height: 36px !important;
}

.recipe-table >>> .v-text-field--outlined.v-input--is-focused fieldset,
.recipe-table >>> .v-select--outlined.v-input--is-focused fieldset,
.recipe-table >>> .v-autocomplete--outlined.v-input--is-focused fieldset {
  border-color: var(--im-accent) !important;
  box-shadow: 0 0 0 2px rgba(94, 96, 206, 0.12) !important;
}
</style>
