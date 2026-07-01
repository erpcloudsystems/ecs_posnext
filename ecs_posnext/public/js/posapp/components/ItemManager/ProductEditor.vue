<template>
  <v-dialog v-model="dialog" max-width="1200px" persistent scrollable>
    <v-card class="product-editor">
      <!-- Header -->
      <v-card-title class="pa-4 d-flex align-center header">
        <v-icon class="mr-2" color="primary">mdi-arrow-left</v-icon>
        <div>
          <div class="text-h6 font-weight-bold">
            {{
              isEditing
                ? __("Edit Product") + ": " + product.name
                : __("Add New Product")
            }}
          </div>
          <div class="text-caption grey--text">
            {{ __("Modify product details, variants, or combo items.") }}
          </div>
        </div>
        <v-spacer></v-spacer>
        <v-btn icon @click="closeDialog">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text class="pa-0" style="max-height: 75vh; overflow-y: auto">
        <v-row no-gutters>
          <!-- Left Panel - Product Info -->
          <v-col
            cols="12"
            md="5"
            class="pa-6"
            style="border-right: 1px solid #e0e6f0"
          >
            <!-- Product Type & Category -->
            <v-row>
              <v-col cols="6">
                <div class="field-label">{{ __("Product Type") }}</div>
                <v-select
                  v-model="product.product_type"
                  :items="productTypes"
                  item-text="label"
                  item-value="value"
                  outlined
                  dense
                  hide-details
                  class="mt-1"
                ></v-select>
              </v-col>
              <v-col cols="6">
                <div class="field-label">{{ __("Category") }}</div>
                <v-autocomplete
                  v-model="product.category"
                  :items="categories"
                  item-text="name"
                  item-value="name"
                  outlined
                  dense
                  hide-details
                  class="mt-1"
                ></v-autocomplete>
              </v-col>
            </v-row>

            <!-- Product Recipe Card -->
            <v-card outlined class="mt-4 pa-3" style="background: #f8f9fa">
              <div class="d-flex align-center justify-space-between">
                <div>
                  <div class="font-weight-medium">
                    {{ __("Product Recipe") }}
                  </div>
                  <div class="text-caption grey--text">
                    {{
                      __(
                        "Manage ingredients and billing of materials for this product.",
                      )
                    }}
                  </div>
                </div>
                <v-btn outlined small @click="openRecipeDialog">
                  <v-icon left small>mdi-tune-variant</v-icon>
                  {{ __("Manage Recipe") }}
                </v-btn>
              </div>
            </v-card>

            <!-- Name -->
            <div class="mt-4">
              <div class="field-label">{{ __("Name") }}</div>
              <v-text-field
                v-model="product.name"
                outlined
                dense
                hide-details
                class="mt-1"
                :placeholder="__('Product name')"
              ></v-text-field>
            </div>

            <!-- Base Price -->
            <div class="mt-4">
              <div class="field-label">{{ __("Base Price") }}</div>
              <v-text-field
                v-model.number="product.base_price"
                type="number"
                outlined
                dense
                hide-details
                class="mt-1"
                min="0"
              ></v-text-field>
            </div>

            <!-- Description -->
            <div class="mt-4">
              <div class="field-label">{{ __("Description") }}</div>
              <v-textarea
                v-model="product.description"
                outlined
                dense
                hide-details
                rows="3"
                class="mt-1"
                :placeholder="__('Optional product description...')"
              ></v-textarea>
            </div>

            <!-- Image URL -->
            <div class="mt-4">
              <div class="field-label">{{ __("Image URL") }}</div>
              <v-text-field
                v-model="product.image_url"
                outlined
                dense
                hide-details
                class="mt-1"
                placeholder="https://example.com/image.jpg"
              ></v-text-field>
            </div>

            <!-- Toggles -->
            <v-row class="mt-4">
              <v-col cols="6">
                <div class="toggle-card pa-3">
                  <div class="d-flex align-center justify-space-between">
                    <span class="font-weight-medium">{{
                      __("Available")
                    }}</span>
                    <v-switch
                      v-model="product.available"
                      dense
                      hide-details
                      class="mt-0 pt-0"
                      color="primary"
                    ></v-switch>
                  </div>
                </div>
              </v-col>
              <v-col cols="6">
                <div class="toggle-card pa-3">
                  <div class="d-flex align-center justify-space-between">
                    <span class="font-weight-medium">{{ __("Active") }}</span>
                    <v-switch
                      v-model="product.active"
                      dense
                      hide-details
                      class="mt-0 pt-0"
                      color="primary"
                    ></v-switch>
                  </div>
                </div>
              </v-col>
            </v-row>

            <!-- Quick Sell -->
            <v-card outlined class="mt-4 pa-3" style="background: #e3f2fd">
              <div class="d-flex align-center justify-space-between">
                <div>
                  <div class="font-weight-medium">
                    {{ __("Quick Sell (Fast)") }}
                  </div>
                  <div class="text-caption grey--text">
                    {{ __("Skip dialog & add directly to cart.") }}
                  </div>
                </div>
                <v-switch
                  v-model="product.quick_sell"
                  dense
                  hide-details
                  class="mt-0 pt-0"
                  color="primary"
                ></v-switch>
              </div>
            </v-card>
          </v-col>

          <!-- Right Panel - Variants or Combo Components -->
          <v-col cols="12" md="7" class="pa-6" style="background: #fafafa">
            <!-- Standard Product - Variants -->
            <template v-if="product.product_type === 'standard'">
              <div class="d-flex align-center justify-space-between mb-4">
                <div class="text-subtitle-1 font-weight-medium">
                  {{ __("Variants") }}
                  <span class="grey--text">({{ __("Optional") }})</span>
                </div>
                <v-btn outlined small color="primary" @click="addVariant">
                  <v-icon left small>mdi-plus</v-icon>
                  {{ __("Add Variant") }}
                </v-btn>
              </div>

              <!-- Variants List -->
              <div
                v-for="(variant, index) in product.variants"
                :key="'variant-' + index"
                class="variant-card mb-3"
              >
                <v-row align="center" no-gutters>
                  <v-col cols="5">
                    <div class="field-label-sm">{{ __("Name") }}</div>
                    <v-text-field
                      v-model="variant.name"
                      outlined
                      dense
                      hide-details
                      class="mt-1"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="4" class="pl-2">
                    <div class="field-label-sm">{{ __("Price") }}</div>
                    <v-text-field
                      v-model.number="variant.price"
                      type="number"
                      outlined
                      dense
                      hide-details
                      class="mt-1"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="3" class="pl-2 d-flex align-end justify-end">
                    <v-btn
                      icon
                      small
                      color="error"
                      @click="removeVariant(index)"
                      class="mt-4"
                    >
                      <v-icon>mdi-close</v-icon>
                    </v-btn>
                  </v-col>
                </v-row>
                <div class="mt-2">
                  <v-btn
                    text
                    small
                    color="primary"
                    @click="openVariantRecipe(variant)"
                  >
                    <v-icon left small>mdi-tune-variant</v-icon>
                    {{ __("CONFIGURE") }} {{ variant.name.toUpperCase() }}
                    {{ __("RECIPE") }}
                  </v-btn>
                </div>
              </div>

              <div
                v-if="product.variants.length === 0"
                class="text-center pa-6 grey--text"
              >
                <v-icon large color="grey lighten-1"
                  >mdi-tag-multiple-outline</v-icon
                >
                <div class="mt-2">{{ __("No variants added yet") }}</div>
              </div>
            </template>

            <!-- Combo/Meal Product - Components -->
            <template v-else>
              <div class="d-flex align-center justify-space-between mb-4">
                <div class="text-subtitle-1 font-weight-medium">
                  {{ __("Combo Components") }}
                </div>
                <v-btn outlined small color="primary" @click="addComponent">
                  <v-icon left small>mdi-plus</v-icon>
                  {{ __("Add Component") }}
                </v-btn>
              </div>

              <!-- Components List -->
              <div
                v-for="(component, cIndex) in product.components"
                :key="'component-' + cIndex"
                class="component-card mb-4"
              >
                <!-- Component Header -->
                <v-row align="center" no-gutters class="mb-2">
                  <v-col cols="6">
                    <div class="field-label-sm">{{ __("Component Name") }}</div>
                    <v-text-field
                      v-model="component.name"
                      outlined
                      dense
                      hide-details
                      class="mt-1"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="2" class="pl-2">
                    <div class="field-label-sm">{{ __("Min") }}</div>
                    <v-text-field
                      v-model.number="component.min"
                      type="number"
                      outlined
                      dense
                      hide-details
                      class="mt-1"
                      min="0"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="2" class="pl-2">
                    <div class="field-label-sm">{{ __("Max") }}</div>
                    <v-text-field
                      v-model.number="component.max"
                      type="number"
                      outlined
                      dense
                      hide-details
                      class="mt-1"
                      min="0"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="2" class="pl-2 d-flex align-end justify-end">
                    <v-btn
                      icon
                      small
                      color="error"
                      @click="removeComponent(cIndex)"
                      class="mt-4"
                    >
                      <v-icon>mdi-close</v-icon>
                    </v-btn>
                  </v-col>
                </v-row>

                <!-- Component Options -->
                <div class="options-section mt-3">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span
                      class="text-caption text-uppercase grey--text font-weight-medium"
                      >{{ __("OPTIONS") }}</span
                    >
                    <v-btn
                      text
                      x-small
                      color="primary"
                      @click="addOption(component)"
                    >
                      <v-icon left x-small>mdi-plus</v-icon>
                      {{ __("Add Option") }}
                    </v-btn>
                  </div>

                  <div
                    v-for="(option, oIndex) in component.options"
                    :key="'option-' + cIndex + '-' + oIndex"
                    class="option-row mb-2"
                  >
                    <v-row align="center" no-gutters>
                      <v-col cols="5">
                        <v-autocomplete
                          v-model="option.item_code"
                          :items="availableItems"
                          item-text="item_name"
                          item-value="item_code"
                          outlined
                          dense
                          hide-details
                          @change="onOptionItemSelect(option, $event)"
                        ></v-autocomplete>
                      </v-col>
                      <v-col
                        cols="2"
                        class="pl-2 d-flex align-center justify-center"
                      >
                        <v-btn icon x-small @click="openOptionSettings(option)">
                          <v-icon small>mdi-tune-variant</v-icon>
                        </v-btn>
                      </v-col>
                      <v-col cols="3" class="pl-2">
                        <v-text-field
                          v-model.number="option.price"
                          type="number"
                          outlined
                          dense
                          hide-details
                          prefix="+"
                        ></v-text-field>
                      </v-col>
                      <v-col cols="2" class="pl-2 d-flex justify-end">
                        <v-btn
                          icon
                          x-small
                          color="error"
                          @click="removeOption(component, oIndex)"
                        >
                          <v-icon small>mdi-close</v-icon>
                        </v-btn>
                      </v-col>
                    </v-row>
                    <!-- Variant Selection for Option -->
                    <v-row v-if="option.show_variant" no-gutters class="mt-1">
                      <v-col cols="2">
                        <span class="text-caption grey--text"
                          >{{ __("Variant") }}:</span
                        >
                      </v-col>
                      <v-col cols="10">
                        <v-select
                          v-model="option.variant"
                          :items="getItemVariants(option.item_code)"
                          item-text="name"
                          item-value="name"
                          outlined
                          dense
                          hide-details
                          class="variant-select"
                        ></v-select>
                      </v-col>
                    </v-row>
                  </div>
                </div>
              </div>

              <div
                v-if="product.components.length === 0"
                class="text-center pa-6 grey--text"
              >
                <v-icon large color="grey lighten-1"
                  >mdi-package-variant</v-icon
                >
                <div class="mt-2">{{ __("No components added yet") }}</div>
              </div>
            </template>
          </v-col>
        </v-row>
      </v-card-text>

      <!-- Footer Actions -->
      <v-card-actions class="pa-4 footer">
        <v-spacer></v-spacer>
        <v-btn outlined @click="closeDialog" class="mr-2">
          {{ __("Cancel") }}
        </v-btn>
        <v-btn color="primary" @click="saveProduct" :loading="saving">
          {{ __("Save Changes") }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: "ProductEditor",
  props: {
    value: {
      type: Boolean,
      default: false,
    },
    editItem: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      dialog: false,
      saving: false,
      isEditing: false,
      product: this.getEmptyProduct(),
      productTypes: [
        { label: this.__("Standard"), value: "standard" },
        { label: this.__("Combo / Meal"), value: "combo" },
      ],
      categories: [],
      availableItems: [],
      itemVariantsMap: {},
    };
  },
  watch: {
    value(val) {
      this.dialog = val;
      if (val) {
        this.loadData();
        if (this.editItem) {
          this.loadProduct(this.editItem);
        } else {
          this.product = this.getEmptyProduct();
          this.isEditing = false;
        }
      }
    },
    dialog(val) {
      this.$emit("input", val);
    },
  },
  methods: {
    __(text) {
      return __(text);
    },

    getEmptyProduct() {
      return {
        item_code: "",
        name: "",
        product_type: "standard",
        category: "",
        base_price: 0,
        description: "",
        image_url: "",
        available: true,
        active: true,
        quick_sell: false,
        variants: [],
        components: [],
      };
    },

    async loadData() {
      await Promise.all([this.loadCategories(), this.loadAvailableItems()]);
    },

    async loadCategories() {
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_item_groups",
        });
        this.categories = res.message || [];
      } catch (e) {
        console.error(e);
      }
    },

    async loadAvailableItems() {
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_items_for_bundle",
        });
        this.availableItems = res.message || [];
      } catch (e) {
        console.error(e);
      }
    },

    async loadProduct(item) {
      this.isEditing = true;
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_item_with_options",
          args: { item_code: item.item_code },
        });
        if (res.message && res.message.success) {
          const data = res.message.item;
          this.product = {
            item_code: data.item_code,
            name: data.item_name,
            product_type: data.enabled_item_bundle ? "combo" : "standard",
            category: data.item_group,
            base_price: data.standard_rate || 0,
            description: data.description || "",
            image_url: data.image || "",
            available: true,
            active: !data.disabled,
            quick_sell: !!data.custom_fast_sell,
            variants: [],
            components: this.parseComponents(data.bundle_options || []),
          };
        }
      } catch (e) {
        console.error(e);
      }
    },

    parseComponents(bundleOptions) {
      // Group bundle options by classification into components
      const componentsMap = {};
      bundleOptions.forEach((opt) => {
        const classification = opt.item_classification || "Default";
        if (!componentsMap[classification]) {
          componentsMap[classification] = {
            name: classification,
            min: opt.qty || 0,
            max: opt.max_required || 1,
            options: [],
          };
        }
        componentsMap[classification].options.push({
          item_code: opt.item_code,
          item_name: opt.item_name,
          price: opt.rate || 0,
          variant: "",
          show_variant: false,
        });
      });
      return Object.values(componentsMap);
    },

    addVariant() {
      this.product.variants.push({
        name: "",
        price: 0,
        recipe: [],
      });
    },

    removeVariant(index) {
      this.product.variants.splice(index, 1);
    },

    addComponent() {
      this.product.components.push({
        name: "",
        min: 0,
        max: 1,
        options: [],
      });
    },

    removeComponent(index) {
      this.product.components.splice(index, 1);
    },

    addOption(component) {
      component.options.push({
        item_code: "",
        item_name: "",
        price: 0,
        variant: "",
        show_variant: false,
      });
    },

    removeOption(component, index) {
      component.options.splice(index, 1);
    },

    onOptionItemSelect(option, itemCode) {
      const found = this.availableItems.find((i) => i.item_code === itemCode);
      if (found) {
        option.item_name = found.item_name;
        option.price = found.standard_rate || 0;
      }
    },

    getItemVariants(itemCode) {
      // Return variants for an item if available
      return this.itemVariantsMap[itemCode] || [];
    },

    openRecipeDialog() {
      this.$emit("open-recipe", this.product);
    },

    openVariantRecipe(variant) {
      this.$emit("open-variant-recipe", { product: this.product, variant });
    },

    openOptionSettings(option) {
      option.show_variant = !option.show_variant;
    },

    closeDialog() {
      this.dialog = false;
      this.product = this.getEmptyProduct();
      this.$emit("close");
    },

    async saveProduct() {
      this.saving = true;
      try {
        if (this.isEditing) {
          await this.updateProduct();
        } else {
          await this.createProduct();
        }
        this.$emit("saved");
        this.closeDialog();
      } catch (e) {
        console.error(e);
        frappe.show_alert({
          message: e.message || "Error saving product",
          indicator: "red",
        });
      }
      this.saving = false;
    },

    async createProduct() {
      const bundleOptions = this.buildBundleOptions();

      if (this.product.product_type === "combo" && bundleOptions.length > 0) {
        await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.create_bundle_item",
          args: {
            item_code: this.product.name.replace(/\s+/g, "-").toUpperCase(),
            item_name: this.product.name,
            item_group: this.product.category,
            standard_rate: this.product.base_price,
            image: this.product.image_url,
            description: this.product.description,
            custom_fast_sell: this.product.quick_sell ? 1 : 0,
            bundle_options: bundleOptions,
          },
        });
      } else {
        await frappe.call({
          method: "ecs_posnext.ecs_posnext.custom_api.item_manager.create_item",
          args: {
            item_code: this.product.name.replace(/\s+/g, "-").toUpperCase(),
            item_name: this.product.name,
            item_group: this.product.category,
            standard_rate: this.product.base_price,
            image: this.product.image_url,
            description: this.product.description,
            enabled_item_bundle: this.product.product_type === "combo" ? 1 : 0,
            custom_fast_sell: this.product.quick_sell ? 1 : 0,
          },
        });
      }
      frappe.show_alert({
        message: __("Product created successfully"),
        indicator: "green",
      });
    },

    async updateProduct() {
      // Update basic info
      await frappe.call({
        method: "ecs_posnext.ecs_posnext.custom_api.item_manager.update_item",
        args: {
          item_code: this.product.item_code,
          updates: {
            item_name: this.product.name,
            item_group: this.product.category,
            standard_rate: this.product.base_price,
            image: this.product.image_url,
            description: this.product.description,
            enabled_item_bundle: this.product.product_type === "combo" ? 1 : 0,
            custom_fast_sell: this.product.quick_sell ? 1 : 0,
            disabled: this.product.active ? 0 : 1,
          },
        },
      });

      // Update bundle options for combo
      if (this.product.product_type === "combo") {
        await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.clear_bundle_options",
          args: { item_code: this.product.item_code },
        });

        const bundleOptions = this.buildBundleOptions();
        for (const opt of bundleOptions) {
          await frappe.call({
            method:
              "ecs_posnext.ecs_posnext.custom_api.item_manager.add_bundle_option",
            args: {
              item_code: this.product.item_code,
              option: opt,
            },
          });
        }
      }

      frappe.show_alert({
        message: __("Product updated successfully"),
        indicator: "green",
      });
    },

    buildBundleOptions() {
      const options = [];
      this.product.components.forEach((component) => {
        component.options.forEach((opt) => {
          options.push({
            item_code: opt.item_code,
            item_name: opt.item_name,
            item_classification: component.name,
            qty: component.min,
            max_required: component.max,
            rate: opt.price,
            state:
              component.min > 0 ? "Minimum 1 Item is Required In Section" : "",
            hide_from_pos: 0,
          });
        });
      });
      return options;
    },
  },
};
</script>

<style scoped>
/* ===== Local Theme Tokens ===== */
.product-editor {
  --im-bg: #f4f6fb;
  --im-card: #ffffff;
  --im-border: #e0e6f0;
  --im-border-light: #f0f2f8;
  --im-muted: #8a94a6;
  --im-primary: #17223b;
  --im-primary-light: #e8eeff;
  --im-accent: #5e60ce;
  --im-radius: 14px;
  --im-radius-sm: 10px;
  --im-radius-input: 10px;
  --im-input-bg: #f7f8fa;
  --im-input-border: #e0e6f0;
  --im-text: #2d3348;
  --im-text-secondary: #6b7280;

  border-radius: var(--im-radius) !important;
  overflow: hidden;
}

/* ===== Header ===== */
.product-editor >>> .v-card__title {
  background: var(--im-card) !important;
  border-bottom: 1px solid var(--im-border) !important;
  color: var(--im-primary) !important;
}

/* ===== Footer ===== */
.product-editor >>> .v-card__actions {
  background: var(--im-card) !important;
  border-top: 1px solid var(--im-border) !important;
}

/* ===== Field Labels ===== */
.field-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--im-muted);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.field-label-sm {
  font-size: 11px;
  font-weight: 600;
  color: var(--im-muted);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

/* ===== Toggle Card ===== */
.toggle-card {
  background: var(--im-input-bg);
  border: 1px solid var(--im-border);
  border-radius: var(--im-radius-sm);
}

/* ===== Variant Card ===== */
.variant-card {
  background: var(--im-card);
  border: 1px solid var(--im-border);
  border-radius: var(--im-radius-sm);
  padding: 16px;
  transition: border-color 0.15s ease;
}

.variant-card:hover {
  border-color: var(--im-accent);
}

/* ===== Component Card ===== */
.component-card {
  background: var(--im-card);
  border: 1px solid var(--im-border);
  border-radius: var(--im-radius-sm);
  padding: 16px;
}

/* ===== Options Section ===== */
.options-section {
  background: var(--im-input-bg);
  border-radius: var(--im-radius-sm);
  padding: 14px;
}

/* ===== Option Row ===== */
.option-row {
  background: var(--im-card);
  border: 1px solid var(--im-border);
  border-radius: 8px;
  padding: 10px 14px;
}

/* ===== Variant Select ===== */
.variant-select {
  font-size: 12px;
}

.variant-select >>> .v-input__slot {
  min-height: 28px !important;
}

.variant-select >>> .v-select__selection {
  font-size: 12px;
  color: var(--im-accent);
}

/* ===== Input Overrides (scoped) ===== */
.product-editor >>> .v-text-field--outlined fieldset,
.product-editor >>> .v-select--outlined fieldset,
.product-editor >>> .v-autocomplete--outlined fieldset,
.product-editor >>> .v-textarea--outlined fieldset {
  border-color: var(--im-input-border) !important;
  border-radius: var(--im-radius-input) !important;
  border-width: 1px !important;
}

.product-editor >>> .v-text-field--outlined .v-input__slot,
.product-editor >>> .v-select--outlined .v-input__slot,
.product-editor >>> .v-autocomplete--outlined .v-input__slot,
.product-editor >>> .v-textarea--outlined .v-input__slot {
  background: var(--im-input-bg) !important;
  min-height: 40px !important;
}

.product-editor >>> .v-text-field--outlined.v-input--is-focused fieldset,
.product-editor >>> .v-select--outlined.v-input--is-focused fieldset,
.product-editor >>> .v-autocomplete--outlined.v-input--is-focused fieldset,
.product-editor >>> .v-textarea--outlined.v-input--is-focused fieldset {
  border-color: var(--im-accent) !important;
  box-shadow: 0 0 0 2px rgba(94, 96, 206, 0.12) !important;
}

.product-editor >>> .v-input__slot input,
.product-editor >>> .v-input__slot textarea,
.product-editor >>> .v-select__selection {
  font-size: 13.5px !important;
  color: var(--im-text) !important;
}

.product-editor >>> .v-label {
  font-size: 13px !important;
  color: var(--im-muted) !important;
}

/* ===== Switches ===== */
.product-editor >>> .v-input--switch .v-input--selection-controls__input {
  transform: scale(0.85);
}
</style>
