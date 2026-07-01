<template>
  <v-container fluid class="product-editor-page pa-0">
    <!-- Header -->
    <div class="editor-header pa-4 d-flex align-center">
      <v-btn icon @click="goBack" class="mr-3">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
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
    </div>

    <!-- Loading -->
    <v-progress-linear
      v-if="loading"
      indeterminate
      color="primary"
    ></v-progress-linear>

    <!-- Content -->
    <v-row no-gutters class="editor-content" v-if="!loading">
      <!-- Left Panel - Product Info -->
      <v-col
        cols="12"
        md="5"
        class="pa-6"
        style="border-right: 1px solid #e0e6f0; background: white"
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
        <v-card outlined class="mt-4 pa-3">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="font-weight-medium">{{ __("Product Recipe") }}</div>
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
                <span class="font-weight-medium">{{ __("Available") }}</span>
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
        <v-card outlined class="mt-4 pa-3">
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
      <v-col cols="12" md="7" class="pa-6" style="background: #f4f6fb">
        <!-- Standard Product - Variants -->
        <template v-if="product.product_type === 'standard'">
          <!-- Template Attributes Section -->
          <div class="d-flex align-center justify-space-between mb-3">
            <div class="text-subtitle-1 font-weight-medium">
              {{ __("Variant Attributes") }}
              <span class="grey--text text-caption"
                >({{ __("e.g. Size, Type") }})</span
              >
            </div>
            <v-btn
              outlined
              x-small
              color="primary"
              @click="showAddAttributeDialog = true"
              :disabled="!isEditing"
            >
              <v-icon left x-small>mdi-plus</v-icon>
              {{ __("Add Attribute") }}
            </v-btn>
          </div>

          <!-- Template Attributes Display -->
          <div v-if="templateAttributes.length > 0" class="mb-4">
            <v-chip
              v-for="attr in templateAttributes"
              :key="attr.attribute"
              small
              outlined
              color="primary"
              class="mr-2 mb-2"
            >
              <strong>{{ attr.attribute }}:</strong>&nbsp;
              <span class="grey--text">{{
                attr.values.map((v) => v.value).join(", ")
              }}</span>
            </v-chip>
          </div>
          <div v-else class="text-caption grey--text mb-4">
            {{
              __(
                "No attributes defined. Add attributes like Size or Type to create variants.",
              )
            }}
          </div>

          <v-divider class="mb-4"></v-divider>

          <!-- Variants Section -->
          <div class="d-flex align-center justify-space-between mb-4">
            <div class="text-subtitle-1 font-weight-medium">
              {{ __("Variants") }}
              <span class="grey--text">({{ __("Optional") }})</span>
            </div>
            <v-btn
              outlined
              small
              color="primary"
              @click="openCreateVariantDialog"
              :disabled="!isEditing"
            >
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
                <div class="field-label-sm">{{ __("Variant") }}</div>
                <div class="font-weight-medium">{{ variant.name }}</div>
                <!-- Show attributes -->
                <div
                  v-if="variant.attributes && variant.attributes.length > 0"
                  class="mt-1"
                >
                  <v-chip
                    v-for="attr in variant.attributes"
                    :key="attr.attribute"
                    x-small
                    outlined
                    class="mr-1"
                  >
                    {{ attr.attribute }}: {{ attr.attribute_value }}
                  </v-chip>
                </div>
              </v-col>
              <v-col cols="3" class="pl-2">
                <div class="field-label-sm">{{ __("Price") }}</div>
                <v-text-field
                  v-model.number="variant.price"
                  type="number"
                  outlined
                  dense
                  hide-details
                  class="mt-1"
                  @change="updateVariantPrice(variant)"
                ></v-text-field>
              </v-col>
              <v-col cols="4" class="pl-2 d-flex align-end justify-end">
                <v-btn
                  icon
                  small
                  color="primary"
                  @click="openVariantRecipe(variant)"
                  :disabled="!variant.isExisting"
                  class="mt-4 mr-1"
                >
                  <v-icon>mdi-chef-hat</v-icon>
                </v-btn>
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
            <!-- Status indicator -->
            <div class="mt-1" v-if="variant.isExisting">
              <v-chip x-small color="success" text-color="white" class="mr-2">
                <v-icon x-small left>mdi-check</v-icon>
                {{ __("Saved") }}
              </v-chip>
              <v-chip
                x-small
                color="info"
                text-color="white"
                v-if="variant.has_recipe"
              >
                <v-icon x-small left>mdi-chef-hat</v-icon>
                {{ __("Has Recipe") }}
              </v-chip>
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
                    <v-btn icon x-small @click="toggleOptionSettings(option)">
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
                <!-- Template Item Indicator & Nested Attribute Selection -->
                <v-row
                  v-if="isTemplateItem(option.item_code)"
                  no-gutters
                  class="mt-2"
                >
                  <v-col cols="12">
                    <v-chip
                      x-small
                      color="info"
                      text-color="white"
                      class="mr-2 mb-2"
                    >
                      <v-icon x-small left>mdi-tag-multiple</v-icon>
                      {{ __("Has Variants") }}
                    </v-chip>
                    <v-checkbox
                      v-model="option.let_customer_choose"
                      :label="__('Let customer choose variant in POS')"
                      dense
                      hide-details
                      class="mt-1 mb-2"
                    ></v-checkbox>

                    <!-- Nested Attribute Selection (when not letting customer choose) -->
                    <div
                      v-if="!option.let_customer_choose"
                      class="nested-variant-selection pa-2"
                    >
                      <div class="text-caption font-weight-medium mb-2">
                        {{ __("Select Variant Attributes") }}:
                      </div>

                      <!-- Attribute Selectors -->
                      <div
                        v-for="attr in getOptionItemAttributes(
                          option.item_code,
                        )"
                        :key="attr.attribute"
                        class="mb-2"
                      >
                        <div class="text-caption grey--text mb-1">
                          {{ attr.attribute }}:
                        </div>
                        <v-chip-group
                          v-model="option.selectedAttributes[attr.attribute]"
                          active-class="primary white--text"
                          mandatory
                          @change="onOptionAttributeChange(option)"
                        >
                          <v-chip
                            v-for="val in attr.values"
                            :key="val.attribute_value"
                            :value="val.attribute_value"
                            small
                            outlined
                            label
                          >
                            {{ val.attribute_value }}
                          </v-chip>
                        </v-chip-group>
                      </div>

                      <!-- Selected Variant Display -->
                      <div v-if="option.variant" class="mt-2 pa-2">
                        <v-icon small color="success" class="mr-1"
                          >mdi-check-circle</v-icon
                        >
                        <span class="text-caption font-weight-medium"
                          >{{ __("Selected") }}: {{ option.variant }}</span
                        >
                      </div>
                      <div
                        v-else-if="
                          Object.keys(option.selectedAttributes || {}).length >
                          0
                        "
                        class="mt-2 pa-2"
                      >
                        <v-icon small color="warning" class="mr-1"
                          >mdi-alert</v-icon
                        >
                        <span class="text-caption">{{
                          __("No matching variant found")
                        }}</span>
                      </div>
                    </div>
                  </v-col>
                </v-row>
              </div>
            </div>
          </div>

          <div
            v-if="product.components.length === 0"
            class="text-center pa-6 grey--text"
          >
            <v-icon large color="grey lighten-1">mdi-package-variant</v-icon>
            <div class="mt-2">{{ __("No components added yet") }}</div>
          </div>
        </template>
      </v-col>
    </v-row>

    <!-- Footer Actions -->
    <div class="editor-footer pa-4 d-flex justify-end">
      <v-btn outlined @click="goBack" class="mr-2">
        {{ __("Cancel") }}
      </v-btn>
      <v-btn color="primary" @click="saveProduct" :loading="saving">
        {{ __("Save Changes") }}
      </v-btn>
    </div>

    <!-- Snackbar -->
    <v-snackbar
      v-model="snackbar"
      :color="snackbarColor"
      top
      right
      :timeout="3000"
    >
      {{ snackbarText }}
    </v-snackbar>

    <!-- Recipe Dialog -->
    <RecipeDialog
      v-model="recipeDialog"
      :item-code="recipeItemCode"
      :product-name="product.name"
      :variant-name="selectedVariantName"
      @saved="onRecipeSaved"
      @close="recipeDialog = false"
    />

    <!-- Add Attribute Dialog -->
    <v-dialog v-model="showAddAttributeDialog" max-width="500">
      <v-card>
        <v-card-title>{{ __("Add Variant Attribute") }}</v-card-title>
        <v-card-text>
          <v-autocomplete
            v-model="newAttribute.name"
            :items="availableAttributes"
            item-text="attribute_name"
            item-value="name"
            :label="__('Attribute Name')"
            outlined
            dense
            :placeholder="__('e.g. Size, Type, Flavor')"
            clearable
            @change="onAttributeSelect"
          >
            <template v-slot:no-data>
              <v-list-item>
                <v-list-item-content>
                  <v-list-item-title>
                    {{ __("Type to create new attribute") }}
                  </v-list-item-title>
                </v-list-item-content>
              </v-list-item>
            </template>
          </v-autocomplete>
          <v-text-field
            v-model="newAttribute.values"
            :label="__('Values (comma separated)')"
            outlined
            dense
            :placeholder="__('e.g. Small, Medium, Large')"
            :hint="__('Enter values separated by commas')"
            persistent-hint
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="showAddAttributeDialog = false">{{
            __("Cancel")
          }}</v-btn>
          <v-btn
            color="primary"
            @click="addAttributeToTemplate"
            :loading="saving"
            >{{ __("Add") }}</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Create Variant Dialog -->
    <v-dialog v-model="showCreateVariantDialog" max-width="500">
      <v-card>
        <v-card-title>{{ __("Create Variant") }}</v-card-title>
        <v-card-text>
          <div
            v-for="attr in templateAttributes"
            :key="attr.attribute"
            class="mb-3"
          >
            <v-select
              v-model="newVariant.attributes[attr.attribute]"
              :items="attr.values"
              item-text="value"
              item-value="value"
              :label="attr.attribute"
              outlined
              dense
            ></v-select>
          </div>
          <v-text-field
            v-model.number="newVariant.price"
            type="number"
            :label="__('Price')"
            outlined
            dense
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="showCreateVariantDialog = false">{{
            __("Cancel")
          }}</v-btn>
          <v-btn
            color="primary"
            @click="createVariantCombination"
            :loading="saving"
            >{{ __("Create") }}</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import RecipeDialog from "./RecipeDialog.vue";

export default {
  name: "ProductEditorPage",
  components: {
    RecipeDialog,
  },
  props: {
    itemId: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      loading: false,
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
      itemAttributesMap: {},
      snackbar: false,
      snackbarColor: "success",
      snackbarText: "",
      recipeDialog: false,
      selectedVariantName: "",
      recipeItemCode: "",
      // Variant Attributes
      templateAttributes: [],
      availableAttributes: [],
      showAddAttributeDialog: false,
      newAttribute: {
        name: "",
        values: "",
      },
      showCreateVariantDialog: false,
      newVariant: {
        attributes: {},
        price: 0,
      },
    };
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

    showMessage(text, color = "success") {
      this.snackbarText = text;
      this.snackbarColor = color;
      this.snackbar = true;
    },

    goBack() {
      this.$emit("back");
    },

    async loadData() {
      this.loading = true;
      await Promise.all([
        this.loadCategories(),
        this.loadAvailableItems(),
        this.loadAvailableAttributes(),
      ]);

      // Load product if editing
      if (this.itemId && this.itemId !== "new") {
        await this.loadProduct(this.itemId);
      }
      this.loading = false;
    },

    async loadAvailableAttributes() {
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_item_attributes",
        });
        this.availableAttributes = res.message || [];
      } catch (e) {
        console.error(e);
      }
    },

    async loadTemplateAttributes() {
      if (!this.product.item_code) return;
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_template_attributes",
          args: { item_code: this.product.item_code },
        });
        if (res.message && res.message.success) {
          this.templateAttributes = res.message.attributes || [];
        }
      } catch (e) {
        console.error(e);
      }
    },

    onAttributeSelect(attrName) {
      // Pre-fill values if attribute already exists
      const attr = this.availableAttributes.find((a) => a.name === attrName);
      if (attr && attr.values && attr.values.length > 0) {
        this.newAttribute.values = attr.values.map((v) => v.value).join(", ");
      }
    },

    async addAttributeToTemplate() {
      if (!this.newAttribute.name) {
        this.showMessage(this.__("Please enter attribute name"), "warning");
        return;
      }

      this.saving = true;
      try {
        const values = this.newAttribute.values
          .split(",")
          .map((v) => v.trim())
          .filter((v) => v);

        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.add_attribute_to_template",
          args: {
            item_code: this.product.item_code,
            attribute_name: this.newAttribute.name,
            values: values,
          },
        });

        if (res.message && res.message.success) {
          this.showMessage(res.message.message);
          this.showAddAttributeDialog = false;
          this.newAttribute = { name: "", values: "" };
          await this.loadTemplateAttributes();
          await this.loadAvailableAttributes();
        } else {
          throw new Error(res.message?.message || "Error adding attribute");
        }
      } catch (e) {
        console.error(e);
        this.showMessage(e.message || "Error adding attribute", "error");
      }
      this.saving = false;
    },

    openCreateVariantDialog() {
      if (this.templateAttributes.length === 0) {
        this.showMessage(this.__("Please add attributes first"), "warning");
        return;
      }
      this.newVariant = {
        attributes: {},
        price: this.product.base_price || 0,
      };
      this.showCreateVariantDialog = true;
    },

    async createVariantCombination() {
      // Build attributes array
      const attributes = [];
      for (const attr of this.templateAttributes) {
        const value = this.newVariant.attributes[attr.attribute];
        if (!value) {
          this.showMessage(this.__("Please select all attributes"), "warning");
          return;
        }
        attributes.push({
          attribute: attr.attribute,
          value: value,
        });
      }

      this.saving = true;
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.create_variant_combination",
          args: {
            template_item_code: this.product.item_code,
            attributes: attributes,
            price: this.newVariant.price,
          },
        });

        if (res.message && res.message.success) {
          this.showMessage(res.message.message);
          this.showCreateVariantDialog = false;
          await this.loadVariants(this.product.item_code);
        } else {
          throw new Error(res.message?.message || "Error creating variant");
        }
      } catch (e) {
        console.error(e);
        this.showMessage(e.message || "Error creating variant", "error");
      }
      this.saving = false;
    },

    async updateVariantPrice(variant) {
      if (!variant.item_code) return;
      try {
        await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.update_item_variant",
          args: {
            variant_item_code: variant.item_code,
            updates: { standard_rate: variant.price },
          },
        });
        this.showMessage(this.__("Price updated"));
      } catch (e) {
        console.error(e);
      }
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

    async loadProduct(itemCode) {
      this.isEditing = true;
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_item_with_options",
          args: { item_code: itemCode },
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
          // Load variants and attributes if standard product
          if (this.product.product_type === "standard") {
            await Promise.all([
              this.loadVariants(itemCode),
              this.loadTemplateAttributes(),
            ]);
          }
        }
      } catch (e) {
        console.error(e);
        this.showMessage(e.message || "Error loading product", "error");
      }
    },

    async loadVariants(itemCode) {
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_item_variants",
          args: { item_code: itemCode },
        });
        if (res.message && res.message.success) {
          this.product.variants = (res.message.variants || []).map((v) => ({
            item_code: v.item_code,
            name: this.extractVariantName(v.item_name, this.product.name),
            price: v.standard_rate || 0,
            has_recipe: v.has_recipe,
            attributes: v.attributes || [],
            isExisting: true,
          }));
        }
      } catch (e) {
        console.error(e);
      }
    },

    extractVariantName(variantItemName, templateName) {
      // Extract variant name from "Template Name - Variant Name"
      if (variantItemName && templateName && variantItemName.includes(" - ")) {
        return variantItemName.split(" - ").slice(1).join(" - ");
      }
      return variantItemName;
    },

    parseComponents(bundleOptions) {
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
          variant: opt.custom_variant || "",
          show_variant: !!opt.custom_variant,
        });
      });
      return Object.values(componentsMap);
    },

    addVariant() {
      this.product.variants.push({
        name: "",
        price: this.product.base_price || 0,
        recipe: [],
        isExisting: false,
        isNew: true,
      });
    },

    async removeVariant(index) {
      const variant = this.product.variants[index];

      if (variant.isExisting && variant.item_code) {
        // Delete from backend
        if (
          !confirm(this.__("Are you sure you want to delete this variant?"))
        ) {
          return;
        }
        try {
          const res = await frappe.call({
            method:
              "ecs_posnext.ecs_posnext.custom_api.item_manager.delete_item_variant",
            args: { variant_item_code: variant.item_code },
          });
          if (res.message && res.message.success) {
            this.showMessage(res.message.message || this.__("Variant deleted"));
          } else {
            throw new Error(res.message?.message || "Error deleting variant");
          }
        } catch (e) {
          console.error(e);
          this.showMessage(e.message || "Error deleting variant", "error");
          return;
        }
      }

      this.product.variants.splice(index, 1);
    },

    async saveVariant(variant) {
      if (!this.product.item_code) {
        this.showMessage(this.__("Please save the product first"), "warning");
        return;
      }
      if (!variant.name) {
        this.showMessage(this.__("Variant name is required"), "error");
        return;
      }

      try {
        if (variant.isExisting && variant.item_code) {
          // Update existing variant
          const res = await frappe.call({
            method:
              "ecs_posnext.ecs_posnext.custom_api.item_manager.update_item_variant",
            args: {
              variant_item_code: variant.item_code,
              updates: {
                standard_rate: variant.price,
              },
            },
          });
          if (res.message && res.message.success) {
            this.showMessage(this.__("Variant updated"));
          } else {
            throw new Error(res.message?.message || "Error updating variant");
          }
        } else {
          // Create new variant
          const res = await frappe.call({
            method:
              "ecs_posnext.ecs_posnext.custom_api.item_manager.create_simple_variant",
            args: {
              template_item_code: this.product.item_code,
              variant_name: variant.name,
              price: variant.price,
            },
          });
          if (res.message && res.message.success) {
            variant.item_code = res.message.variant.item_code;
            variant.isExisting = true;
            variant.isNew = false;
            this.showMessage(res.message.message || this.__("Variant created"));
          } else {
            throw new Error(res.message?.message || "Error creating variant");
          }
        }
      } catch (e) {
        console.error(e);
        this.showMessage(e.message || "Error saving variant", "error");
      }
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
        let_customer_choose: false,
        selectedAttributes: {},
      });
    },

    removeOption(component, index) {
      component.options.splice(index, 1);
    },

    async onOptionItemSelect(option, itemCode) {
      const found = this.availableItems.find((i) => i.item_code === itemCode);
      if (found) {
        option.item_name = found.item_name;
        option.price = found.standard_rate || 0;

        // Initialize selectedAttributes for template items
        if (found.has_variants) {
          this.$set(option, "selectedAttributes", {});
          option.variant = "";
        }
      }
      // Load variants for this item
      await this.loadItemVariants(itemCode);
    },

    toggleOptionSettings(option) {
      option.show_variant = !option.show_variant;
      // Load variants when opening settings
      if (option.show_variant && option.item_code) {
        this.loadItemVariants(option.item_code);
      }
    },

    async loadItemVariants(itemCode) {
      if (!itemCode) {
        return;
      }

      // Skip if already loaded
      if (this.itemVariantsMap[itemCode] !== undefined) {
        return;
      }

      console.log("Loading variants for:", itemCode);

      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_item_variants",
          args: { item_code: itemCode },
        });

        console.log("Variants response for", itemCode, ":", res.message);

        if (
          res.message &&
          res.message.success &&
          res.message.variants &&
          res.message.variants.length > 0
        ) {
          // Map variants with attributes for nested selection
          const variants = res.message.variants.map((v) => ({
            name: v.item_name || v.item_code,
            value: v.item_code,
            item_code: v.item_code,
            standard_rate: v.standard_rate || 0,
            attributes: v.attributes || [],
          }));
          console.log("Mapped variants with attributes:", variants);
          this.$set(this.itemVariantsMap, itemCode, variants);
        } else {
          console.log("No variants found for:", itemCode);
          this.$set(this.itemVariantsMap, itemCode, []);
        }
      } catch (e) {
        console.error("Error loading variants:", e);
        this.$set(this.itemVariantsMap, itemCode, []);
      }
    },

    getItemVariants(itemCode) {
      // Trigger load if not already loaded
      if (itemCode && !this.itemVariantsMap[itemCode]) {
        this.loadItemVariants(itemCode);
      }
      return this.itemVariantsMap[itemCode] || [];
    },

    isTemplateItem(itemCode) {
      // Check if item has variants (is a template)
      if (!itemCode) return false;
      const item = this.availableItems.find((i) => i.item_code === itemCode);
      return item && item.has_variants;
    },

    getOptionItemAttributes(itemCode) {
      // Get attributes for a template item from the loaded variants data
      if (!itemCode || !this.itemVariantsMap[itemCode]) {
        this.loadItemVariants(itemCode);
        return [];
      }

      // Extract unique attributes from variants
      const variants = this.itemVariantsMap[itemCode] || [];
      if (variants.length === 0) return [];

      // Check if we have cached attributes
      if (this.itemAttributesMap && this.itemAttributesMap[itemCode]) {
        return this.itemAttributesMap[itemCode];
      }

      // Build attributes from variants
      const attributesMap = {};
      variants.forEach((v) => {
        if (v.attributes) {
          v.attributes.forEach((attr) => {
            if (!attributesMap[attr.attribute]) {
              attributesMap[attr.attribute] = new Set();
            }
            attributesMap[attr.attribute].add(attr.attribute_value);
          });
        }
      });

      // Convert to array format
      const attributes = Object.keys(attributesMap).map((attrName) => ({
        attribute: attrName,
        values: Array.from(attributesMap[attrName]).map((val) => ({
          attribute_value: val,
        })),
      }));

      // Cache it
      if (!this.itemAttributesMap) {
        this.itemAttributesMap = {};
      }
      this.itemAttributesMap[itemCode] = attributes;

      return attributes;
    },

    onOptionAttributeChange(option) {
      // Find matching variant based on selected attributes
      if (!option.item_code || !option.selectedAttributes) return;

      const variants = this.itemVariantsMap[option.item_code] || [];
      const selectedAttrs = option.selectedAttributes;
      const selectedKeys = Object.keys(selectedAttrs).filter(
        (k) => selectedAttrs[k],
      );

      if (selectedKeys.length === 0) {
        option.variant = null;
        return;
      }

      // Find variant that matches all selected attributes
      const matchingVariant = variants.find((v) => {
        if (!v.attributes) return false;
        return selectedKeys.every((attrName) => {
          const variantAttr = v.attributes.find(
            (a) => a.attribute === attrName,
          );
          return (
            variantAttr &&
            variantAttr.attribute_value === selectedAttrs[attrName]
          );
        });
      });

      if (matchingVariant) {
        option.variant = matchingVariant.item_code;
        // Update price if variant has different price
        if (matchingVariant.standard_rate) {
          option.price = matchingVariant.standard_rate;
        }
      } else {
        option.variant = null;
      }

      this.$forceUpdate();
    },

    openRecipeDialog() {
      if (!this.isEditing || !this.product.item_code) {
        this.showMessage(
          __("Please save the product first before managing recipe"),
          "warning",
        );
        return;
      }
      this.selectedVariantName = "";
      this.recipeItemCode = this.product.item_code;
      console.log("Opening recipe dialog for:", this.recipeItemCode);
      this.$nextTick(() => {
        this.recipeDialog = true;
      });
    },

    onRecipeSaved(recipeItems) {
      this.showMessage(__("Recipe saved successfully"));
      // Update has_recipe status for the variant if applicable
      if (this.selectedVariantName && this.recipeItemCode) {
        const variant = this.product.variants.find(
          (v) => v.item_code === this.recipeItemCode,
        );
        if (variant) {
          variant.has_recipe = recipeItems && recipeItems.length > 0;
        }
      }
    },

    openVariantRecipe(variant) {
      if (!variant.isExisting || !variant.item_code) {
        this.showMessage(
          __("Please save the variant first before managing recipe"),
          "warning",
        );
        return;
      }
      this.selectedVariantName = variant.name || "";
      this.recipeItemCode = variant.item_code;
      console.log("Opening variant recipe dialog for:", this.recipeItemCode);
      this.$nextTick(() => {
        this.recipeDialog = true;
      });
    },

    async saveProduct() {
      if (!this.product.name) {
        this.showMessage(__("Product name is required"), "error");
        return;
      }
      if (!this.product.category) {
        this.showMessage(__("Category is required"), "error");
        return;
      }

      this.saving = true;
      try {
        if (this.isEditing) {
          await this.updateProduct();
        } else {
          await this.createProduct();
        }
        this.showMessage(__("Product saved successfully"));
        setTimeout(() => {
          this.goBack();
        }, 1000);
      } catch (e) {
        console.error(e);
        this.showMessage(e.message || "Error saving product", "error");
      }
      this.saving = false;
    },

    async createProduct() {
      const bundleOptions = this.buildBundleOptions();
      const itemCode = this.product.name.replace(/\s+/g, "-").toUpperCase();

      if (this.product.product_type === "combo" && bundleOptions.length > 0) {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.create_bundle_item",
          args: {
            item_code: itemCode,
            item_name: this.product.name,
            item_group: this.product.category,
            standard_rate: this.product.base_price,
            image: this.product.image_url,
            description: this.product.description,
            custom_fast_sell: this.product.quick_sell ? 1 : 0,
            bundle_options: bundleOptions,
          },
        });
        if (res.message && !res.message.success) {
          throw new Error(res.message.message);
        }
      } else {
        const res = await frappe.call({
          method: "ecs_posnext.ecs_posnext.custom_api.item_manager.create_item",
          args: {
            item_code: itemCode,
            item_name: this.product.name,
            item_group: this.product.category,
            standard_rate: this.product.base_price,
            image: this.product.image_url,
            description: this.product.description,
            enabled_item_bundle: this.product.product_type === "combo" ? 1 : 0,
            custom_fast_sell: this.product.quick_sell ? 1 : 0,
          },
        });
        if (res.message && !res.message.success) {
          throw new Error(res.message.message);
        }
      }
    },

    async updateProduct() {
      // Update basic info
      const res = await frappe.call({
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

      if (res.message && !res.message.success) {
        throw new Error(res.message.message);
      }

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
            variant: opt.variant || "",
          });
        });
      });
      return options;
    },
  },
  mounted() {
    this.loadData();
  },
  watch: {
    itemId: {
      handler(newVal) {
        if (newVal) {
          this.product = this.getEmptyProduct();
          this.isEditing = false;
          this.loadData();
        }
      },
      immediate: false,
    },
  },
};
</script>

<style scoped>
/* ===== Local Theme Tokens ===== */
.product-editor-page {
  --im-bg: #f4f6fb;
  --im-card: #ffffff;
  --im-border: #e0e6f0;
  --im-border-light: #f0f2f8;
  --im-muted: #8a94a6;
  --im-primary: #17223b;
  --im-primary-light: #e8eeff;
  --im-accent: #5e60ce;
  --im-radius: 12px;
  --im-radius-sm: 10px;
  --im-radius-input: 10px;
  --im-input-bg: #f7f8fa;
  --im-input-border: #e0e6f0;
  --im-text: #2d3348;
  --im-text-secondary: #6b7280;

  background: var(--im-bg);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ===== Header ===== */
.editor-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--im-card) !important;
  border-bottom: 1px solid var(--im-border) !important;
}

/* ===== Content ===== */
.editor-content {
  flex: 1;
  overflow-y: auto;
}

/* ===== Footer ===== */
.editor-footer {
  position: sticky;
  bottom: 0;
  z-index: 10;
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

/* ===== Nested Variant Selection ===== */
.nested-variant-selection {
  background: var(--im-input-bg) !important;
  border-radius: var(--im-radius-sm) !important;
}

/* ===== Input Overrides (scoped) ===== */
.product-editor-page >>> .v-text-field--outlined fieldset,
.product-editor-page >>> .v-select--outlined fieldset,
.product-editor-page >>> .v-autocomplete--outlined fieldset,
.product-editor-page >>> .v-textarea--outlined fieldset {
  border-color: var(--im-input-border) !important;
  border-radius: var(--im-radius-input) !important;
  border-width: 1px !important;
}

.product-editor-page >>> .v-text-field--outlined .v-input__slot,
.product-editor-page >>> .v-select--outlined .v-input__slot,
.product-editor-page >>> .v-autocomplete--outlined .v-input__slot,
.product-editor-page >>> .v-textarea--outlined .v-input__slot {
  background: var(--im-input-bg) !important;
  min-height: 40px !important;
}

.product-editor-page >>> .v-text-field--outlined.v-input--is-focused fieldset,
.product-editor-page >>> .v-select--outlined.v-input--is-focused fieldset,
.product-editor-page >>> .v-autocomplete--outlined.v-input--is-focused fieldset,
.product-editor-page >>> .v-textarea--outlined.v-input--is-focused fieldset {
  border-color: var(--im-accent) !important;
  box-shadow: 0 0 0 2px rgba(94, 96, 206, 0.12) !important;
}

.product-editor-page >>> .v-input__slot input,
.product-editor-page >>> .v-input__slot textarea,
.product-editor-page >>> .v-select__selection {
  font-size: 13.5px !important;
  color: var(--im-text) !important;
}

.product-editor-page >>> .v-label {
  font-size: 13px !important;
  color: var(--im-muted) !important;
}

/* ===== Switches ===== */
.product-editor-page >>> .v-input--switch .v-input--selection-controls__input {
  transform: scale(0.85);
}

/* ===== Sub-Dialogs ===== */
.product-editor-page >>> .v-dialog > .v-card {
  border-radius: var(--im-radius) !important;
}

.product-editor-page >>> .v-dialog .v-card__title {
  font-size: 16px !important;
  font-weight: 700 !important;
  color: var(--im-primary) !important;
  padding: 18px 24px !important;
  border-bottom: 1px solid var(--im-border) !important;
}

.product-editor-page >>> .v-dialog .v-card__text {
  padding: 20px 24px !important;
}

.product-editor-page >>> .v-dialog .v-card__actions {
  padding: 14px 24px !important;
  border-top: 1px solid var(--im-border-light) !important;
}
</style>
