<template>
  <v-container fluid class="restaurant-editor pa-0">
    <!-- Header -->
    <div class="editor-header">
      <div class="d-flex align-center">
        <v-btn icon @click="goBack" class="mr-3">
          <v-icon color="white">mdi-arrow-left</v-icon>
        </v-btn>
        <div>
          <div class="text-h5 font-weight-bold white--text">
            {{ isEditing ? __("Edit Item") : __("Add New Item") }}
          </div>
          <div class="text-caption white--text" style="opacity: 0.8">
            {{ stepDescriptions[currentStep] }}
          </div>
        </div>
      </div>

      <!-- Progress Steps -->
      <div class="step-indicators mt-4">
        <div
          v-for="(step, index) in steps"
          :key="index"
          class="step-indicator"
          :class="{
            'step-indicator--active': currentStep === index,
            'step-indicator--completed': currentStep > index,
          }"
          @click="goToStep(index)"
        >
          <div class="step-indicator__number">
            <v-icon v-if="currentStep > index" small color="white"
              >mdi-check</v-icon
            >
            <span v-else>{{ index + 1 }}</span>
          </div>
          <div class="step-indicator__label">{{ step.label }}</div>
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
    <div class="editor-content" v-if="!loading">
      <!-- Step 1: Item Type Selection -->
      <div v-show="currentStep === 0" class="step-content">
        <div class="step-title">
          {{ __("What type of item do you want to create?") }}
        </div>

        <v-row class="mt-6">
          <v-col cols="12" md="4" v-for="type in itemTypes" :key="type.value">
            <v-card
              class="type-card"
              :class="{ 'type-card--selected': item.item_type === type.value }"
              @click="selectItemType(type.value)"
              outlined
              hover
            >
              <div class="type-card__icon">
                <v-icon
                  size="48"
                  :color="item.item_type === type.value ? 'primary' : 'grey'"
                >
                  {{ type.icon }}
                </v-icon>
              </div>
              <div class="type-card__title">{{ type.label }}</div>
              <div class="type-card__description">{{ type.description }}</div>
              <div class="type-card__examples">
                <v-chip
                  x-small
                  outlined
                  class="mr-1"
                  v-for="ex in type.examples"
                  :key="ex"
                  >{{ ex }}</v-chip
                >
              </div>
            </v-card>
          </v-col>
        </v-row>
      </div>

      <!-- Step 2: Basic Info -->
      <div v-show="currentStep === 1" class="step-content">
        <div class="step-title">{{ __("Basic Information") }}</div>

        <v-row class="mt-6">
          <v-col cols="12" md="6">
            <!-- Item Name -->
            <div class="form-group">
              <label class="form-label"
                >{{ __("Item Name") }} <span class="required">*</span></label
              >
              <v-text-field
                v-model="item.item_name"
                outlined
                dense
                hide-details="auto"
                :placeholder="__('e.g. Chicken Burger')"
                :rules="[(v) => !!v || __('Required')]"
              ></v-text-field>
            </div>

            <!-- Item Name Arabic -->
            <div class="form-group mt-4">
              <label class="form-label">{{ __("Item Name (Arabic)") }}</label>
              <v-text-field
                v-model="item.item_name_arabic"
                outlined
                dense
                hide-details
                :placeholder="__('e.g. برجر دجاج')"
                dir="rtl"
              ></v-text-field>
            </div>

            <!-- Category -->
            <div class="form-group mt-4">
              <label class="form-label"
                >{{ __("Category") }} <span class="required">*</span></label
              >
              <v-autocomplete
                v-model="item.item_group"
                :items="categories"
                item-text="name"
                item-value="name"
                outlined
                dense
                hide-details="auto"
                :placeholder="__('Select category')"
              ></v-autocomplete>
            </div>

            <!-- Base Price (for simple items) -->
            <div class="form-group mt-4" v-if="item.item_type === 'simple'">
              <label class="form-label"
                >{{ __("Price") }} <span class="required">*</span></label
              >
              <v-text-field
                v-model.number="item.standard_rate"
                type="number"
                outlined
                dense
                hide-details
                min="0"
                suffix="EGP"
              ></v-text-field>
            </div>
          </v-col>

          <v-col cols="12" md="6">
            <!-- Image Upload -->
            <div class="form-group">
              <label class="form-label">{{ __("Item Image") }}</label>
              <div class="image-upload-area" @click="triggerImageUpload">
                <input
                  type="file"
                  ref="imageInput"
                  @change="handleImageUpload"
                  accept="image/*"
                  style="display: none"
                />
                <div v-if="!item.image" class="image-upload-placeholder">
                  <v-icon size="48" color="grey lighten-1"
                    >mdi-image-plus</v-icon
                  >
                  <div class="mt-2 grey--text">
                    {{ __("Click to upload image") }}
                  </div>
                </div>
                <img v-else :src="item.image" class="image-preview" />
              </div>
            </div>

            <!-- Description -->
            <div class="form-group mt-4">
              <label class="form-label">{{ __("Description") }}</label>
              <v-textarea
                v-model="item.description"
                outlined
                dense
                hide-details
                rows="3"
                :placeholder="__('Optional description...')"
              ></v-textarea>
            </div>
          </v-col>
        </v-row>
      </div>

      <!-- Step 3: Sizes/Variants (for sized items) -->
      <div
        v-show="currentStep === 2 && item.item_type === 'sized'"
        class="step-content"
      >
        <div class="step-title">{{ __("Define Sizes & Prices") }}</div>
        <div class="step-subtitle">
          {{ __("Add different sizes with their prices") }}
        </div>

        <div class="sizes-container mt-6">
          <v-row>
            <v-col cols="12" md="8">
              <!-- Size Cards -->
              <div
                v-for="(size, index) in item.sizes"
                :key="index"
                class="size-card mb-3"
              >
                <v-row align="center" no-gutters>
                  <v-col cols="5">
                    <v-text-field
                      v-model="size.name"
                      outlined
                      dense
                      hide-details
                      :placeholder="__('Size name (e.g. Medium)')"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="4" class="pl-3">
                    <v-text-field
                      v-model.number="size.price"
                      type="number"
                      outlined
                      dense
                      hide-details
                      suffix="EGP"
                      :placeholder="__('Price')"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="3" class="pl-3 d-flex justify-end">
                    <v-btn
                      icon
                      color="error"
                      @click="removeSize(index)"
                      :disabled="item.sizes.length <= 1"
                    >
                      <v-icon>mdi-delete</v-icon>
                    </v-btn>
                  </v-col>
                </v-row>
              </div>

              <!-- Add Size Button -->
              <v-btn outlined color="primary" @click="addSize" class="mt-2">
                <v-icon left>mdi-plus</v-icon>
                {{ __("Add Size") }}
              </v-btn>
            </v-col>

            <!-- Quick Templates -->
            <v-col cols="12" md="4">
              <div class="quick-templates">
                <div class="form-label mb-2">{{ __("Quick Templates") }}</div>
                <v-btn
                  v-for="template in sizeTemplates"
                  :key="template.name"
                  outlined
                  small
                  class="mr-2 mb-2"
                  @click="applySizeTemplate(template)"
                >
                  {{ template.name }}
                </v-btn>
              </div>
            </v-col>
          </v-row>
        </div>
      </div>

      <!-- Step 3: Combo Components (for combo items) -->
      <div
        v-show="currentStep === 2 && item.item_type === 'combo'"
        class="step-content"
      >
        <div class="step-title">{{ __("Build Your Combo") }}</div>
        <div class="step-subtitle">
          {{ __("Add sections and options for your combo meal") }}
        </div>

        <div class="combo-builder mt-6">
          <!-- Combo Price -->
          <div class="form-group mb-4" style="max-width: 300px">
            <label class="form-label"
              >{{ __("Combo Price") }} <span class="required">*</span></label
            >
            <v-text-field
              v-model.number="item.standard_rate"
              type="number"
              outlined
              dense
              hide-details
              min="0"
              suffix="EGP"
            ></v-text-field>
          </div>

          <!-- Sections -->
          <div
            v-for="(section, sIndex) in item.sections"
            :key="sIndex"
            class="combo-section mb-4"
          >
            <div class="combo-section__header">
              <v-row align="center" no-gutters>
                <v-col cols="4">
                  <v-text-field
                    v-model="section.name"
                    outlined
                    dense
                    hide-details
                    :placeholder="__('Section name (e.g. Main Dish)')"
                  ></v-text-field>
                </v-col>
                <v-col cols="2" class="pl-2">
                  <v-select
                    v-model="section.selection_type"
                    :items="selectionTypes"
                    item-text="label"
                    item-value="value"
                    outlined
                    dense
                    hide-details
                  ></v-select>
                </v-col>
                <v-col cols="2" class="pl-2">
                  <v-text-field
                    v-model.number="section.max_selections"
                    type="number"
                    outlined
                    dense
                    hide-details
                    :label="__('Max')"
                    min="1"
                  ></v-text-field>
                </v-col>
                <v-col cols="4" class="pl-2 d-flex justify-end">
                  <v-btn
                    icon
                    color="error"
                    @click="removeSection(sIndex)"
                    :disabled="item.sections.length <= 1"
                  >
                    <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </v-col>
              </v-row>
            </div>

            <!-- Section Options -->
            <div class="combo-section__options mt-3">
              <div
                v-for="(option, oIndex) in section.options"
                :key="oIndex"
                class="option-row mb-2"
              >
                <v-row align="center" no-gutters>
                  <v-col cols="6">
                    <v-autocomplete
                      v-model="option.item_code"
                      :items="availableItems"
                      item-text="item_name"
                      item-value="item_code"
                      outlined
                      dense
                      hide-details
                      :placeholder="__('Select item')"
                      @change="onOptionItemChange(option)"
                    ></v-autocomplete>
                  </v-col>
                  <v-col cols="3" class="pl-2">
                    <v-text-field
                      v-model.number="option.extra_price"
                      type="number"
                      outlined
                      dense
                      hide-details
                      :placeholder="__('Extra price')"
                      prefix="+"
                      suffix="EGP"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="3" class="pl-2 d-flex justify-end">
                    <v-btn
                      icon
                      x-small
                      color="error"
                      @click="removeOption(section, oIndex)"
                    >
                      <v-icon small>mdi-close</v-icon>
                    </v-btn>
                  </v-col>
                </v-row>
              </div>

              <v-btn
                text
                small
                color="primary"
                @click="addOption(section)"
                class="mt-2"
              >
                <v-icon left small>mdi-plus</v-icon>
                {{ __("Add Option") }}
              </v-btn>
            </div>
          </div>

          <!-- Add Section Button -->
          <v-btn outlined color="primary" @click="addSection" class="mt-2">
            <v-icon left>mdi-plus</v-icon>
            {{ __("Add Section") }}
          </v-btn>
        </div>
      </div>

      <!-- Step 4: Additional Settings -->
      <div v-show="currentStep === 3" class="step-content">
        <div class="step-title">{{ __("Additional Settings") }}</div>

        <v-row class="mt-6">
          <v-col cols="12" md="6">
            <!-- Availability -->
            <v-card outlined class="settings-card pa-4 mb-4">
              <div class="d-flex align-center justify-space-between">
                <div>
                  <div class="font-weight-medium">
                    {{ __("Available for Sale") }}
                  </div>
                  <div class="text-caption grey--text">
                    {{ __("Show this item in POS") }}
                  </div>
                </div>
                <v-switch
                  v-model="item.disabled"
                  :true-value="0"
                  :false-value="1"
                  color="success"
                  hide-details
                  class="mt-0"
                ></v-switch>
              </div>
            </v-card>

            <!-- Quick Sell -->
            <v-card outlined class="settings-card pa-4 mb-4">
              <div class="d-flex align-center justify-space-between">
                <div>
                  <div class="font-weight-medium">{{ __("Quick Sell") }}</div>
                  <div class="text-caption grey--text">
                    {{ __("Add to cart without opening dialog") }}
                  </div>
                </div>
                <v-switch
                  v-model="item.custom_fast_sell"
                  color="primary"
                  hide-details
                  class="mt-0"
                ></v-switch>
              </div>
            </v-card>

            <!-- Show in POS -->
            <v-card outlined class="settings-card pa-4 mb-4">
              <div class="d-flex align-center justify-space-between">
                <div>
                  <div class="font-weight-medium">{{ __("Show in POS") }}</div>
                  <div class="text-caption grey--text">
                    {{ __("Display in POS item selector") }}
                  </div>
                </div>
                <v-switch
                  v-model="item.custom_is_pos_item"
                  color="primary"
                  hide-details
                  class="mt-0"
                ></v-switch>
              </div>
            </v-card>
          </v-col>

          <v-col cols="12" md="6">
            <!-- Recipe Management -->
            <v-card
              outlined
              class="settings-card pa-4 mb-4"
              v-if="item.item_type !== 'combo'"
            >
              <div class="d-flex align-center justify-space-between">
                <div>
                  <div class="font-weight-medium">{{ __("Recipe / BOM") }}</div>
                  <div class="text-caption grey--text">
                    {{ __("Manage ingredients for this item") }}
                  </div>
                </div>
                <v-btn outlined small color="primary" @click="openRecipeDialog">
                  <v-icon left small>mdi-chef-hat</v-icon>
                  {{ __("Manage") }}
                </v-btn>
              </div>
            </v-card>

            <!-- Tax -->
            <v-card outlined class="settings-card pa-4 mb-4">
              <div class="form-group">
                <label class="form-label">{{ __("Tax Template") }}</label>
                <v-autocomplete
                  v-model="item.item_tax_template"
                  :items="taxTemplates"
                  item-text="name"
                  item-value="name"
                  outlined
                  dense
                  hide-details
                  clearable
                  :placeholder="__('Select tax template')"
                ></v-autocomplete>
              </div>
            </v-card>
          </v-col>
        </v-row>
      </div>
    </div>

    <!-- Footer Actions -->
    <div class="editor-footer">
      <v-btn text @click="goBack" class="mr-2">{{ __("Cancel") }}</v-btn>
      <v-spacer></v-spacer>
      <v-btn outlined @click="previousStep" v-if="currentStep > 0" class="mr-2">
        <v-icon left>mdi-chevron-left</v-icon>
        {{ __("Back") }}
      </v-btn>
      <v-btn
        color="primary"
        @click="nextStep"
        v-if="currentStep < steps.length - 1"
        :disabled="!canProceed"
      >
        {{ __("Next") }}
        <v-icon right>mdi-chevron-right</v-icon>
      </v-btn>
      <v-btn
        color="success"
        @click="saveItem"
        v-else
        :loading="saving"
        :disabled="!canSave"
      >
        <v-icon left>mdi-check</v-icon>
        {{ __("Save Item") }}
      </v-btn>
    </div>
  </v-container>
</template>

<script>
export default {
  name: "RestaurantItemEditor",

  props: {
    itemCode: {
      type: String,
      default: null,
    },
  },

  data() {
    return {
      loading: false,
      saving: false,
      currentStep: 0,

      item: {
        item_type: null,
        item_name: "",
        item_name_arabic: "",
        item_group: "",
        standard_rate: 0,
        description: "",
        image: "",
        disabled: 0,
        custom_fast_sell: false,
        custom_is_pos_item: true,
        item_tax_template: null,
        sizes: [{ name: "", price: 0 }],
        sections: [
          {
            name: "",
            selection_type: "single",
            max_selections: 1,
            options: [],
          },
        ],
      },

      steps: [
        { label: this.__("Type") },
        { label: this.__("Info") },
        { label: this.__("Details") },
        { label: this.__("Settings") },
      ],

      stepDescriptions: [
        this.__("Choose the type of item you want to create"),
        this.__("Enter basic information about your item"),
        this.__("Configure sizes, variants, or combo components"),
        this.__("Set availability and other settings"),
      ],

      itemTypes: [
        {
          value: "simple",
          label: this.__("Simple Item"),
          description: this.__("A single item with fixed price"),
          icon: "mdi-food",
          examples: ["Pepsi", "Water", "Fries"],
        },
        {
          value: "sized",
          label: this.__("Sized Item"),
          description: this.__("Item with different sizes and prices"),
          icon: "mdi-resize",
          examples: ["Fatta M/L", "Pizza S/M/L"],
        },
        {
          value: "combo",
          label: this.__("Combo Meal"),
          description: this.__("Meal with multiple components"),
          icon: "mdi-food-variant",
          examples: ["Burger Meal", "Family Box"],
        },
      ],

      selectionTypes: [
        { value: "single", label: this.__("Single") },
        { value: "multiple", label: this.__("Multiple") },
      ],

      sizeTemplates: [
        {
          name: "S/M/L",
          sizes: [
            { name: "Small", price: 0 },
            { name: "Medium", price: 0 },
            { name: "Large", price: 0 },
          ],
        },
        {
          name: "M/L",
          sizes: [
            { name: "Medium", price: 0 },
            { name: "Large", price: 0 },
          ],
        },
        {
          name: "Regular/Large",
          sizes: [
            { name: "Regular", price: 0 },
            { name: "Large", price: 0 },
          ],
        },
      ],

      categories: [],
      availableItems: [],
      taxTemplates: [],
    };
  },

  computed: {
    isEditing() {
      return !!this.itemCode;
    },

    canProceed() {
      switch (this.currentStep) {
        case 0:
          return !!this.item.item_type;
        case 1:
          return !!this.item.item_name && !!this.item.item_group;
        case 2:
          if (this.item.item_type === "sized") {
            return (
              this.item.sizes.length > 0 &&
              this.item.sizes.every((s) => s.name && s.price >= 0)
            );
          }
          if (this.item.item_type === "combo") {
            return (
              this.item.sections.length > 0 &&
              this.item.sections.every((s) => s.name)
            );
          }
          return true;
        default:
          return true;
      }
    },

    canSave() {
      return this.canProceed;
    },
  },

  methods: {
    __(text) {
      return __(text);
    },

    goBack() {
      this.$emit("close");
    },

    goToStep(index) {
      if (index <= this.currentStep) {
        this.currentStep = index;
      }
    },

    nextStep() {
      if (this.currentStep < this.steps.length - 1 && this.canProceed) {
        this.currentStep++;
      }
    },

    previousStep() {
      if (this.currentStep > 0) {
        this.currentStep--;
      }
    },

    selectItemType(type) {
      this.item.item_type = type;
    },

    triggerImageUpload() {
      this.$refs.imageInput.click();
    },

    handleImageUpload(event) {
      const file = event.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          this.item.image = e.target.result;
        };
        reader.readAsDataURL(file);
      }
    },

    addSize() {
      this.item.sizes.push({ name: "", price: 0 });
    },

    removeSize(index) {
      if (this.item.sizes.length > 1) {
        this.item.sizes.splice(index, 1);
      }
    },

    applySizeTemplate(template) {
      this.item.sizes = JSON.parse(JSON.stringify(template.sizes));
    },

    addSection() {
      this.item.sections.push({
        name: "",
        selection_type: "single",
        max_selections: 1,
        options: [],
      });
    },

    removeSection(index) {
      if (this.item.sections.length > 1) {
        this.item.sections.splice(index, 1);
      }
    },

    addOption(section) {
      section.options.push({
        item_code: "",
        extra_price: 0,
      });
    },

    removeOption(section, index) {
      section.options.splice(index, 1);
    },

    onOptionItemChange(option) {
      // Handle item selection
    },

    openRecipeDialog() {
      // Open recipe dialog
    },

    async loadData() {
      this.loading = true;
      try {
        // Load categories
        const categories = await frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Item Group",
            fields: ["name"],
            limit_page_length: 0,
          },
        });
        this.categories = categories.message || [];

        // Load available items for combo
        const items = await frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Item",
            fields: ["item_code", "item_name"],
            filters: { disabled: 0 },
            limit_page_length: 0,
          },
        });
        this.availableItems = items.message || [];

        // Load tax templates
        const taxes = await frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Item Tax Template",
            fields: ["name"],
            limit_page_length: 0,
          },
        });
        this.taxTemplates = taxes.message || [];

        // Load existing item if editing
        if (this.itemCode) {
          await this.loadItem();
        }
      } catch (error) {
        console.error("Error loading data:", error);
        frappe.show_alert({
          message: this.__("Error loading data"),
          indicator: "red",
        });
      }
      this.loading = false;
    },

    async loadItem() {
      if (!this.itemCode || this.itemCode === "new") return;

      try {
        const response = await frappe.call({
          method: "frappe.client.get",
          args: {
            doctype: "Item",
            name: this.itemCode,
          },
        });

        if (response.message) {
          const doc = response.message;
          this.item.item_name = doc.item_name;
          this.item.item_name_arabic = doc.custom_item_name_arabic || "";
          this.item.item_group = doc.item_group;
          this.item.standard_rate = doc.standard_rate || 0;
          this.item.description = doc.description || "";
          this.item.image = doc.image || "";
          this.item.disabled = doc.disabled;
          this.item.custom_fast_sell = doc.custom_fast_sell || false;
          this.item.custom_is_pos_item = doc.custom_is_pos_item !== 0;
          this.item.item_tax_template = doc.item_tax_template || null;

          // Determine item type
          if (doc.has_variants) {
            this.item.item_type = "sized";
          } else if (doc.enabled_item_bundle) {
            this.item.item_type = "combo";
          } else {
            this.item.item_type = "simple";
          }

          // Skip to step 1 since we already know the type
          this.currentStep = 1;
        }
      } catch (error) {
        console.error("Error loading item:", error);
      }
    },

    async saveItem() {
      this.saving = true;
      try {
        if (this.item.item_type === "simple") {
          await this.saveSimpleItem();
        } else if (this.item.item_type === "sized") {
          await this.saveSizedItem();
        } else if (this.item.item_type === "combo") {
          await this.saveComboItem();
        }

        frappe.show_alert({
          message: this.__("Item saved successfully"),
          indicator: "green",
        });
        this.goBack();
      } catch (error) {
        console.error("Error saving item:", error);
        frappe.show_alert({
          message: error.message || this.__("Error saving item"),
          indicator: "red",
        });
      }
      this.saving = false;
    },

    async saveSimpleItem() {
      const itemData = {
        doctype: "Item",
        item_name: this.item.item_name,
        item_group: this.item.item_group,
        standard_rate: this.item.standard_rate,
        description: this.item.description,
        image: this.item.image,
        disabled: this.item.disabled,
        custom_fast_sell: this.item.custom_fast_sell,
        custom_is_pos_item: this.item.custom_is_pos_item,
        item_tax_template: this.item.item_tax_template,
        is_stock_item: 0,
        include_item_in_manufacturing: 0,
      };

      if (this.item.item_name_arabic) {
        itemData.custom_item_name_arabic = this.item.item_name_arabic;
      }

      await frappe.call({
        method: "frappe.client.insert",
        args: { doc: itemData },
      });
    },

    async saveSizedItem() {
      // Create template item first
      const templateData = {
        doctype: "Item",
        item_name: this.item.item_name,
        item_group: this.item.item_group,
        description: this.item.description,
        image: this.item.image,
        disabled: this.item.disabled,
        custom_fast_sell: this.item.custom_fast_sell,
        custom_is_pos_item: this.item.custom_is_pos_item,
        item_tax_template: this.item.item_tax_template,
        has_variants: 1,
        is_stock_item: 0,
        include_item_in_manufacturing: 0,
        attributes: [{ attribute: "Size" }],
      };

      if (this.item.item_name_arabic) {
        templateData.custom_item_name_arabic = this.item.item_name_arabic;
      }

      // Ensure Size attribute exists with all values
      await this.ensureSizeAttribute();

      const templateResponse = await frappe.call({
        method: "frappe.client.insert",
        args: { doc: templateData },
      });

      const templateCode = templateResponse.message.item_code;

      // Create variants for each size
      for (const size of this.item.sizes) {
        if (!size.name) continue;

        await frappe.call({
          method: "frappe.client.insert",
          args: {
            doc: {
              doctype: "Item",
              item_name: `${this.item.item_name} - ${size.name}`,
              item_group: this.item.item_group,
              variant_of: templateCode,
              standard_rate: size.price,
              disabled: this.item.disabled,
              is_stock_item: 0,
              attributes: [{ attribute: "Size", attribute_value: size.name }],
            },
          },
        });
      }
    },

    async ensureSizeAttribute() {
      // Check if Size attribute exists
      const exists = await frappe.db.exists("Item Attribute", "Size");

      if (!exists) {
        // Create Size attribute
        await frappe.call({
          method: "frappe.client.insert",
          args: {
            doc: {
              doctype: "Item Attribute",
              attribute_name: "Size",
              item_attribute_values: this.item.sizes.map((s) => ({
                attribute_value: s.name,
                abbr: s.name.substring(0, 3).toUpperCase(),
              })),
            },
          },
        });
      } else {
        // Add missing values to existing attribute
        const attr = await frappe.call({
          method: "frappe.client.get",
          args: { doctype: "Item Attribute", name: "Size" },
        });

        const existingValues = (attr.message.item_attribute_values || []).map(
          (v) => v.attribute_value,
        );
        const newValues = this.item.sizes.filter(
          (s) => s.name && !existingValues.includes(s.name),
        );

        if (newValues.length > 0) {
          for (const size of newValues) {
            await frappe.call({
              method: "frappe.client.insert",
              args: {
                doc: {
                  doctype: "Item Attribute Value",
                  parent: "Size",
                  parenttype: "Item Attribute",
                  parentfield: "item_attribute_values",
                  attribute_value: size.name,
                  abbr: size.name.substring(0, 3).toUpperCase(),
                },
              },
            });
          }
        }
      }
    },

    async saveComboItem() {
      // Create combo item
      const comboData = {
        doctype: "Item",
        item_name: this.item.item_name,
        item_group: this.item.item_group,
        standard_rate: this.item.standard_rate,
        description: this.item.description,
        image: this.item.image,
        disabled: this.item.disabled,
        custom_fast_sell: this.item.custom_fast_sell,
        custom_is_pos_item: this.item.custom_is_pos_item,
        item_tax_template: this.item.item_tax_template,
        is_stock_item: 0,
        include_item_in_manufacturing: 0,
        enabled_item_bundle: 1,
        custom_item_options: [],
      };

      if (this.item.item_name_arabic) {
        comboData.custom_item_name_arabic = this.item.item_name_arabic;
      }

      // Add sections and options
      for (const section of this.item.sections) {
        for (const option of section.options) {
          if (!option.item_code) continue;

          comboData.custom_item_options.push({
            item_code: option.item_code,
            item_classification: section.name,
            rate: option.extra_price || 0,
            qty: 1,
            max_required: section.max_selections || 1,
            state:
              section.selection_type === "single"
                ? "Minimum 1 Item is Required In Section"
                : "Optional",
          });
        }
      }

      await frappe.call({
        method: "frappe.client.insert",
        args: { doc: comboData },
      });
    },
  },

  mounted() {
    this.loadData();
  },
};
</script>

<style scoped>
/* ===== Local Theme Tokens ===== */
.restaurant-editor {
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

  min-height: 100vh;
  background: var(--im-bg);
  display: flex;
  flex-direction: column;
}

/* ===== Header ===== */
.editor-header {
  background: var(--im-primary);
  padding: 24px;
  color: white;
}

/* ===== Step Indicators ===== */
.step-indicators {
  display: flex;
  gap: 24px;
}

.step-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.step-indicator--active,
.step-indicator--completed {
  opacity: 1;
}

.step-indicator__number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 13px;
}

.step-indicator--active .step-indicator__number {
  background: var(--im-accent);
}

.step-indicator--completed .step-indicator__number {
  background: #34d399;
}

.step-indicator__label {
  font-size: 13px;
  font-weight: 500;
}

/* ===== Content ===== */
.editor-content {
  flex: 1;
  padding: 32px;
  overflow-y: auto;
}

.step-content {
  max-width: 900px;
  margin: 0 auto;
}

.step-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--im-primary);
  letter-spacing: -0.02em;
}

.step-subtitle {
  font-size: 13px;
  color: var(--im-muted);
  margin-top: 4px;
}

/* ===== Type Cards ===== */
.type-card {
  padding: 24px;
  text-align: center;
  border-radius: var(--im-radius) !important;
  cursor: pointer;
  transition: all 0.2s;
  height: 100%;
  border-color: var(--im-border) !important;
}

.type-card:hover {
  border-color: var(--im-accent) !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.type-card--selected {
  border-color: var(--im-accent) !important;
  border-width: 2px !important;
  background: var(--im-primary-light) !important;
}

.type-card__icon {
  margin-bottom: 16px;
}

.type-card__title {
  font-size: 16px;
  font-weight: 700;
  color: var(--im-primary);
  margin-bottom: 8px;
}

.type-card__description {
  font-size: 13px;
  color: var(--im-text-secondary);
  margin-bottom: 12px;
}

.type-card__examples {
  margin-top: 8px;
}

/* ===== Form ===== */
.form-group {
  margin-bottom: 0;
}

.form-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--im-muted);
  margin-bottom: 6px;
  display: block;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.form-label .required {
  color: #ef4444;
}

/* ===== Image Upload ===== */
.image-upload-area {
  border: 2px dashed var(--im-border);
  border-radius: var(--im-radius);
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s;
  min-height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--im-input-bg);
}

.image-upload-area:hover {
  border-color: var(--im-accent);
}

.image-preview {
  max-width: 100%;
  max-height: 200px;
  border-radius: var(--im-radius-sm);
}

/* ===== Size Card ===== */
.size-card {
  background: var(--im-card);
  padding: 16px;
  border-radius: var(--im-radius-sm);
  border: 1px solid var(--im-border);
  transition: border-color 0.15s ease;
}

.size-card:hover {
  border-color: var(--im-accent);
}

/* ===== Combo Section ===== */
.combo-section {
  background: var(--im-card);
  border-radius: var(--im-radius);
  border: 1px solid var(--im-border);
  overflow: hidden;
}

.combo-section__header {
  background: var(--im-input-bg);
  padding: 16px;
  border-bottom: 1px solid var(--im-border-light);
}

.combo-section__options {
  padding: 16px;
}

/* ===== Option Row ===== */
.option-row {
  background: var(--im-input-bg);
  padding: 12px;
  border-radius: var(--im-radius-sm);
  border: 1px solid var(--im-border);
}

/* ===== Settings Card ===== */
.settings-card {
  border-radius: var(--im-radius) !important;
  border-color: var(--im-border) !important;
}

/* ===== Footer ===== */
.editor-footer {
  background: var(--im-card);
  padding: 16px 32px;
  border-top: 1px solid var(--im-border);
  display: flex;
  align-items: center;
}

/* ===== Quick Templates ===== */
.quick-templates {
  background: var(--im-input-bg);
  padding: 16px;
  border-radius: var(--im-radius-sm);
  border: 1px solid var(--im-border);
}

/* ===== Input Overrides (scoped) ===== */
.restaurant-editor >>> .v-text-field--outlined fieldset,
.restaurant-editor >>> .v-select--outlined fieldset,
.restaurant-editor >>> .v-autocomplete--outlined fieldset,
.restaurant-editor >>> .v-textarea--outlined fieldset {
  border-color: var(--im-input-border) !important;
  border-radius: var(--im-radius-input) !important;
  border-width: 1px !important;
}

.restaurant-editor >>> .v-text-field--outlined .v-input__slot,
.restaurant-editor >>> .v-select--outlined .v-input__slot,
.restaurant-editor >>> .v-autocomplete--outlined .v-input__slot,
.restaurant-editor >>> .v-textarea--outlined .v-input__slot {
  background: var(--im-input-bg) !important;
  min-height: 40px !important;
}

.restaurant-editor >>> .v-text-field--outlined.v-input--is-focused fieldset,
.restaurant-editor >>> .v-select--outlined.v-input--is-focused fieldset,
.restaurant-editor >>> .v-autocomplete--outlined.v-input--is-focused fieldset,
.restaurant-editor >>> .v-textarea--outlined.v-input--is-focused fieldset {
  border-color: var(--im-accent) !important;
  box-shadow: 0 0 0 2px rgba(94, 96, 206, 0.12) !important;
}

.restaurant-editor >>> .v-input__slot input,
.restaurant-editor >>> .v-input__slot textarea,
.restaurant-editor >>> .v-select__selection {
  font-size: 13.5px !important;
  color: var(--im-text) !important;
}

.restaurant-editor >>> .v-label {
  font-size: 13px !important;
  color: var(--im-muted) !important;
}

/* ===== Switches ===== */
.restaurant-editor >>> .v-input--switch .v-input--selection-controls__input {
  transform: scale(0.85);
}
</style>
