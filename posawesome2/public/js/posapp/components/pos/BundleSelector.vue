<template>
  <v-dialog v-model="dialog" max-width="full-width" persistent scrollable>
    <v-card class="bundle-selector">
      <!-- Header -->
      <v-card-title class="bundle-selector__header">
        <div class="d-flex align-center justify-space-between w-100">
          <div class="d-flex align-center">
            <!-- Back button for nested bundles -->
            <v-btn
              v-if="nestedBundleStack.length > 0"
              icon
              small
              class="mr-2"
              @click="closeNestedBundle"
            >
              <v-icon>mdi-arrow-right</v-icon>
            </v-btn>
            <div>
              <span class="text-h6">{{ item.item_name }}</span>
              <div class="text-caption grey--text">
                <span v-if="nestedBundleStack.length > 0">
                  {{ __("Customize") }} - {{ nestedBundleStack.length }}
                  {{ __("level") }}
                </span>
                <span v-else>
                  {{ __("Customize your order") }}
                </span>
              </div>
            </div>
          </div>
          <v-btn icon @click="forceClose">
            <v-icon dark>mdi-close</v-icon>
          </v-btn>
        </div>
      </v-card-title>

      <v-divider></v-divider>

      <div
        style="
          display: flex;
          justify-content: space-between;
          align-items: start;
        "
      >
        <v-card-text class="bundle-selector__body pa-0" style="flex-grow: 1">
          <!-- Sections -->
          <div
            v-for="(section, sectionIndex) in groupedOptions"
            :key="sectionIndex"
            class="bundle-section"
          >
            <!-- Section Header -->
            <div
              class="bundle-section__header"
              :class="
                'bundle-section__header--' + section.section_type.toLowerCase()
              "
            >
              <div class="d-flex align-center justify-space-between">
                <div>
                  <span class="bundle-section__title">{{ section.name }}</span>
                  <span
                    v-if="section.required"
                    class="bundle-section__badge bundle-section__badge--required"
                  >
                    {{ __("Required") }}
                  </span>
                  <span
                    v-else
                    class="bundle-section__badge bundle-section__badge--optional"
                  >
                    {{ __("Optional") }}
                  </span>
                </div>
                <v-icon v-if="isSectionComplete(section)" color="success"
                  >mdi-check-circle</v-icon
                >
              </div>
              <div class="bundle-section__subtitle">
                {{ getSectionSubtitle(section) }}
              </div>
            </div>

            <!-- Section Options - Card View -->
            <v-row class="bundle-section__options pa-2" dense>
              <v-col
                v-for="(option, optionIndex) in section.options"
                :key="optionIndex"
                cols="6"
                sm="4"
              >
                <!-- Option Card -->
                <v-card
                  class="bundle-card"
                  :class="{
                    'bundle-card--selected': isOptionSelected(section, option),
                  }"
                  @click="toggleOption(section, option)"
                  outlined
                  hover
                >
                  <!-- Selection Indicator -->
                  <div class="bundle-card__selector">
                    <v-icon
                      v-if="isOptionSelected(section, option)"
                      color="primary"
                      >mdi-checkbox-marked-circle</v-icon
                    >
                    <v-icon v-else color="grey lighten-1"
                      >mdi-checkbox-blank-circle-outline</v-icon
                    >
                  </div>

                  <!-- Card Content -->
                  <v-card-text class="bundle-card__content pa-3">
                    <div class="d-flex align-center justify-space-between">
                      <div class="bundle-card__name">
                        {{ option.item_name }}
                      </div>
                      <v-btn
                        v-if="shouldShowBundleIcon(option)"
                        icon
                        x-small
                        @click.stop="toggleItemBundle(option)"
                        :color="
                          expandedBundles[option.item_code] ? 'orange' : 'grey'
                        "
                      >
                        <v-icon x-small>mdi-package-variant</v-icon>
                      </v-btn>
                    </div>
                    <div
                      v-if="(option.rate || option.standard_rate) > 0"
                      class="bundle-card__price"
                    >
                      +
                      {{ formatCurrency(option.rate || option.standard_rate) }}
                    </div>

                    <!-- Quantity Controls for multi-selection -->
                    <div
                      v-if="
                        section.max > 1 && isOptionSelected(section, option)
                      "
                      class="bundle-card__qty-controls mt-2 d-flex align-center justify-center"
                      @click.stop
                    >
                      <v-btn
                        icon
                        x-small
                        color="error"
                        @click="decreaseOptionQty(section, option)"
                      >
                        <v-icon small>mdi-minus</v-icon>
                      </v-btn>
                      <span class="mx-2 font-weight-bold">
                        {{ getOptionQty(option) }}
                      </span>
                      <v-btn
                        icon
                        x-small
                        color="primary"
                        @click="increaseOptionQty(section, option)"
                      >
                        <v-icon small>mdi-plus</v-icon>
                      </v-btn>
                    </div>

                    <!-- Nested Attributes for Template Items -->
                    <div
                      v-if="
                        option.is_template &&
                        option.let_customer_choose &&
                        isOptionSelected(section, option)
                      "
                      class="bundle-card__nested mt-3"
                      @click.stop
                    >
                      <div
                        v-for="attr in option.template_attributes"
                        :key="attr.attribute"
                        class="bundle-card__attr-section"
                      >
                        <div class="bundle-card__attr-header">
                          <span class="bundle-card__attr-title">{{
                            attr.attribute
                          }}</span>
                        </div>
                        <div class="bundle-card__attr-options">
                          <v-chip-group
                            v-model="
                              nestedSelections[
                                option.item_code + '_' + attr.attribute
                              ]
                            "
                            active-class="bundle-chip--active"
                            mandatory
                            column
                            @change="onNestedChange(option)"
                          >
                            <v-chip
                              v-for="val in attr.values"
                              :key="val.attribute_value"
                              :value="val.attribute_value"
                              class="bundle-chip"
                              outlined
                              label
                            >
                              {{ val.attribute_value }}
                            </v-chip>
                          </v-chip-group>
                        </div>
                      </div>
                    </div>

                    <!-- Show Product Bundle (Stock Items to be deducted) when enabled -->
                    <div
                      v-if="
                        shouldShowBundleIcon(option) &&
                        isItemBundleExpanded(option)
                      "
                      class="bundle-card__components mt-2"
                      @click.stop
                    >
                      <v-divider class="my-1"></v-divider>
                      <div class="text-caption grey--text mb-1">
                        <v-icon x-small color="orange"
                          >mdi-package-variant</v-icon
                        >
                        {{ __("Stock Deduction") }}:
                      </div>
                      <div v-if="getOptionComponents(option).length">
                        <v-chip
                          v-for="comp in getOptionComponents(option)"
                          :key="comp.item_code"
                          x-small
                          class="mr-1 mb-1"
                          color="orange lighten-4"
                        >
                          <v-icon x-small left>mdi-minus-circle</v-icon>
                          {{ comp.item_name || comp.item_code }} x{{ comp.qty }}
                        </v-chip>
                      </div>
                      <div v-else class="text-caption grey--text font-italic">
                        {{ __("No stock items") }}
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </div>
        </v-card-text>

        <!-- Footer with Qty, Notes, and Actions -->
        <div class="bundle-selector__footer pa-4">
          <v-row dense align="center">
            <!-- Quantity for entire meal -->
            <v-col cols="6">
              <div class="d-flex align-center">
                <span class="text-caption mr-2">{{ __("Qty") }}</span>
                <v-btn icon small @click="decreaseMealQty">
                  <v-icon>mdi-minus</v-icon>
                </v-btn>
                <span class="mx-2 text-h6 font-weight-bold">{{ mealQty }}</span>
                <v-btn icon small color="primary" @click="increaseMealQty">
                  <v-icon>mdi-plus</v-icon>
                </v-btn>
              </div>
            </v-col>

            <!-- Total -->
            <v-col cols="6" class="ml-auto">
              <div class="bundle-selector__total text-right">
                <span class="text-caption grey--text">{{ __("Total") }}</span>
                <span class="text-h6 primary--text ml-2">{{
                  formatCurrency(totalPrice * mealQty)
                }}</span>
              </div>
            </v-col>

            <!-- Actions -->
            <v-col cols="12" style="">
              <v-btn text @click="close" class="mr-2">{{ __("Cancel") }}</v-btn>
              <v-btn color="primary" @click="confirm" :disabled="!isValid">
                {{ __("Add to Order") }}
              </v-btn>
            </v-col>
          </v-row>

          <!-- Notes for entire meal - dedicated full-width row -->
          <v-divider class="my-3"></v-divider>
          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="mealNotes"
                :placeholder="__('Add notes for meal...')"
                outlined
                hide-details
                class="bundle-selector__notes-field"
                prepend-inner-icon="mdi-note-text-outline"
              ></v-text-field>
            </v-col>
          </v-row>
        </div>
      </div>
    </v-card>
  </v-dialog>
</template>

<script>
import { evntBus } from "../../bus";

export default {
  name: "BundleSelector",

  data() {
    return {
      dialog: false,
      item: {},
      options: [],
      selections: {},
      multiSelections: {},
      optionQuantities: {}, // Track qty for each option: {item_code: qty}
      nestedSelections: {},
      ingredientsCache: {},
      mealQty: 1,
      mealNotes: "",
      expandedBundles: {},
      componentsCache: {},
      // Nested bundle support
      nestedBundleStack: [], // Stack of parent states for nested bundles
      nestedBundleSelections: {}, // Store selections from nested bundles: {parent_item_code: [{selectedItems}]}
    };
  },

  computed: {
    groupedOptions() {
      const groups = {};

      this.options.forEach((opt) => {
        const classification = opt.item_classification || "Other";
        if (!groups[classification]) {
          groups[classification] = {
            name: classification,
            section_type: opt.section_type || "Component",
            options: [],
            min: opt.min_required || 0,
            max: opt.max_required || 999,
            required:
              opt.is_required ||
              (opt.min_required || 0) > 0 ||
              opt.state === "Item Must Be Selected",
          };
        }
        groups[classification].options.push(opt);
      });

      // Sort sections by type: Attribute first, then Component, Package, Add-On
      const typeOrder = { Attribute: 0, Component: 1, Package: 2, "Add-On": 3 };
      return Object.values(groups).sort(
        (a, b) =>
          (typeOrder[a.section_type] || 99) - (typeOrder[b.section_type] || 99),
      );
    },

    totalPrice() {
      let total = parseFloat(this.item.rate || this.item.standard_rate || 0);
      console.log(
        "totalPrice - item.rate:",
        this.item.rate,
        "total start:",
        total,
      );

      // Add selected options prices
      Object.entries(this.selections).forEach(([section, itemCode]) => {
        const option = this.findOption(itemCode);
        if (option) {
          const optionRate = parseFloat(
            option.rate || option.standard_rate || 0,
          );
          console.log(
            "Selection option:",
            section,
            option.item_code,
            "rate:",
            optionRate,
          );
          total += optionRate;

          // Add variant price if selected
          if (option.is_template) {
            const variant = this.getSelectedVariant(option);
            if (variant) {
              const variantRate = parseFloat(
                variant.rate || variant.standard_rate || 0,
              );
              console.log("Variant:", variant.item_code, "rate:", variantRate);
              total += variantRate;
            }
          }
        }
      });

      // Add multi-selections prices (with quantity)
      Object.entries(this.multiSelections).forEach(([section, itemCodes]) => {
        (itemCodes || []).forEach((itemCode) => {
          const option = this.findOption(itemCode);
          if (option) {
            const optionRate = parseFloat(
              option.rate || option.standard_rate || 0,
            );
            const qty = this.optionQuantities[itemCode] || 1;
            console.log(
              "Multi-selection option:",
              option.item_code,
              "rate:",
              optionRate,
              "qty:",
              qty,
            );
            total += optionRate * qty;
          }
        });
      });

      console.log("totalPrice final:", total);
      return total;
    },

    isValid() {
      return this.groupedOptions.every((section) => {
        if (!section.required) return true;

        if (section.max === 1) {
          return !!this.selections[section.name];
        } else {
          // Check total quantity instead of item count
          const selected = this.multiSelections[section.name] || [];
          let totalQty = 0;
          selected.forEach((itemCode) => {
            totalQty += this.optionQuantities[itemCode] || 1;
          });
          return totalQty >= section.min;
        }
      });
    },
  },

  methods: {
    __(text) {
      return __(text);
    },

    formatCurrency(value) {
      if (!value) return "0.00 EGP";
      return parseFloat(value).toFixed(2) + " EGP";
    },

    findOption(itemCode) {
      for (const section of this.groupedOptions) {
        const found = section.options.find((o) => o.item_code === itemCode);
        if (found) return found;
      }
      return null;
    },

    getSectionSubtitle(section) {
      if (section.max === 1) {
        return this.__("Choose 1 choice");
      } else if (section.min > 0) {
        return this.__("Choose up to {0} choices").replace("{0}", section.max);
      }
      return this.__("Optional");
    },

    isSectionComplete(section) {
      if (section.max === 1) {
        return !!this.selections[section.name];
      } else {
        const selected = this.multiSelections[section.name] || [];
        return selected.length >= section.min;
      }
    },

    isOptionSelected(section, option) {
      if (section.max === 1) {
        return this.selections[section.name] === option.item_code;
      } else {
        return (this.multiSelections[section.name] || []).includes(
          option.item_code,
        );
      }
    },

    async toggleOption(section, option) {
      // Check if this option has its own bundle options (nested bundle)
      const nestedOptions = await this.checkForNestedBundle(option);

      if (nestedOptions && nestedOptions.length > 0) {
        // Open nested bundle selector
        this.openNestedBundle(option, nestedOptions, section);
        return;
      }

      // Normal selection logic
      if (section.max === 1) {
        this.$set(this.selections, section.name, option.item_code);
      } else {
        const current = this.multiSelections[section.name] || [];
        const index = current.indexOf(option.item_code);

        if (index === -1) {
          // Check total qty before adding new item
          const totalQty = this.getTotalSectionQty(section);
          if (totalQty < section.max) {
            current.push(option.item_code);
            this.$set(this.optionQuantities, option.item_code, 1);
          }
        } else {
          current.splice(index, 1);
          // Remove qty when deselected
          this.$delete(this.optionQuantities, option.item_code);
        }

        this.$set(this.multiSelections, section.name, current);
      }
    },

    getOptionQty(option) {
      return this.optionQuantities[option.item_code] || 1;
    },

    getTotalSectionQty(section) {
      // Calculate total quantity across all selected options in this section
      const selectedItems = this.multiSelections[section.name] || [];
      let total = 0;
      selectedItems.forEach((itemCode) => {
        total += this.optionQuantities[itemCode] || 1;
      });
      return total;
    },

    increaseOptionQty(section, option) {
      const totalQty = this.getTotalSectionQty(section);
      // Check if we can add more (total must be < section.max)
      if (totalQty >= section.max) {
        return; // Can't add more
      }
      const currentQty = this.getOptionQty(option);
      this.$set(this.optionQuantities, option.item_code, currentQty + 1);
    },

    decreaseOptionQty(section, option) {
      const currentQty = this.getOptionQty(option);
      if (currentQty > 1) {
        this.$set(this.optionQuantities, option.item_code, currentQty - 1);
      } else {
        // Remove from selection when qty goes to 0
        const current = this.multiSelections[section.name] || [];
        const index = current.indexOf(option.item_code);
        if (index !== -1) {
          current.splice(index, 1);
          this.$set(this.multiSelections, section.name, current);
          this.$delete(this.optionQuantities, option.item_code);
        }
      }
    },

    async checkForNestedBundle(option) {
      // Check if this option has bundle options
      try {
        const res = await frappe.call({
          method:
            "posawesome.posawesome.custom_api.product_bundle.checkIsProdBundle",
          args: { item_code: option.item_code },
        });
        return res && res.message ? res.message : [];
      } catch (e) {
        console.error("Error checking nested bundle:", e);
        return [];
      }
    },

    openNestedBundle(option, nestedOptions, parentSection) {
      // Save current state to stack
      this.nestedBundleStack.push({
        item: { ...this.item },
        options: [...this.options],
        selections: { ...this.selections },
        multiSelections: { ...this.multiSelections },
        nestedSelections: { ...this.nestedSelections },
        mealQty: this.mealQty,
        mealNotes: this.mealNotes,
        parentSection: parentSection,
        parentOption: option,
      });

      // Load nested bundle
      this.item = option;
      this.options = nestedOptions;
      this.selections = {};
      this.multiSelections = {};
      this.nestedSelections = {};
      this.mealQty = 1;
      this.mealNotes = "";

      // Auto-select defaults for nested bundle
      this.initializeDefaultSelections();
    },

    getEffectiveItemCode(option) {
      // For template items with selected variant, use variant's item_code
      if (option.is_template) {
        const variant = this.getSelectedVariant(option);
        if (variant) {
          return variant.item_code;
        }
      }
      return option.item_code;
    },

    shouldShowBundleIcon(option) {
      // For template items, check selected variant's show_bundle_in_pos
      if (option.is_template) {
        const variant = this.getSelectedVariant(option);
        if (variant) {
          return variant.show_bundle_in_pos;
        }
        // Check if any variant has show_bundle_in_pos enabled
        if (option.template_variants) {
          return option.template_variants.some((v) => v.show_bundle_in_pos);
        }
        return false;
      }
      // For regular items, check directly
      return option.show_bundle_in_pos;
    },

    isItemBundleExpanded(option) {
      const effectiveCode = this.getEffectiveItemCode(option);
      return (
        this.expandedBundles[effectiveCode] ||
        this.expandedBundles[option.item_code]
      );
    },

    toggleItemBundle(option) {
      const effectiveCode = this.getEffectiveItemCode(option);
      const isExpanded = this.expandedBundles[effectiveCode];

      if (!isExpanded) {
        // Load components when expanding
        this.loadComponents(effectiveCode);
        console.log("Toggle bundle for:", effectiveCode);
      }

      this.$set(this.expandedBundles, effectiveCode, !isExpanded);
    },

    getOptionComponents(option) {
      const effectiveCode = this.getEffectiveItemCode(option);

      // Check effective item code first (variant for templates)
      if (
        this.componentsCache[effectiveCode] &&
        this.componentsCache[effectiveCode].length
      ) {
        return this.componentsCache[effectiveCode];
      }

      // Fallback to direct item_code
      if (
        this.componentsCache[option.item_code] &&
        this.componentsCache[option.item_code].length
      ) {
        return this.componentsCache[option.item_code];
      }

      return [];
    },

    async loadComponents(itemCode) {
      if (this.componentsCache[itemCode]) return;

      try {
        console.log("Loading Product Bundle for:", itemCode);
        const res = await frappe.call({
          method:
            "posawesome.posawesome.custom_api.item_manager.get_product_bundle",
          args: { item_code: itemCode },
        });

        console.log("Product Bundle response:", res);

        if (res.message && res.message.items && res.message.items.length > 0) {
          this.$set(this.componentsCache, itemCode, res.message.items);
          console.log("Loaded items:", res.message.items);
          // Force UI update
          this.$forceUpdate();
        } else {
          this.$set(this.componentsCache, itemCode, []);
          console.log("No items found for:", itemCode);
        }
      } catch (e) {
        console.error("Error loading Product Bundle:", e);
        this.$set(this.componentsCache, itemCode, []);
      }
    },

    increaseMealQty() {
      this.mealQty++;
    },

    decreaseMealQty() {
      if (this.mealQty > 1) {
        this.mealQty--;
      }
    },

    onNestedChange(option) {
      // Find matching variant
      const variant = this.getSelectedVariant(option);
      if (variant) {
        // Load ingredients for this variant
        this.loadIngredients(variant.item_code);
      }
    },

    getSelectedVariant(option) {
      if (!option.template_variants || !option.template_attributes) return null;

      const selectedAttrs = {};
      option.template_attributes.forEach((attr) => {
        const key = option.item_code + "_" + attr.attribute;
        if (this.nestedSelections[key]) {
          selectedAttrs[attr.attribute] = this.nestedSelections[key];
        }
      });

      if (
        Object.keys(selectedAttrs).length !== option.template_attributes.length
      ) {
        return null;
      }

      return option.template_variants.find((v) => {
        return v.attributes.every((attr) => {
          return selectedAttrs[attr.attribute] === attr.attribute_value;
        });
      });
    },

    getVariantIngredients(option) {
      const variant = this.getSelectedVariant(option);
      if (!variant) return [];
      return this.ingredientsCache[variant.item_code] || [];
    },

    async loadIngredients(itemCode) {
      if (this.ingredientsCache[itemCode]) return;

      try {
        const res = await frappe.call({
          method:
            "posawesome.posawesome.custom_api.item_manager.get_product_bundle",
          args: { item_code: itemCode },
        });

        if (res.message && res.message.items) {
          // Filter ingredients to show only those with show_in_pos = 1
          const filteredItems = res.message.items.filter(
            (item) => item.show_in_pos !== 0,
          );
          this.$set(this.ingredientsCache, itemCode, filteredItems);
        }
      } catch (e) {
        console.error("Error loading ingredients:", e);
      }
    },

    close() {
      // If we're in a nested bundle, go back to parent
      if (this.nestedBundleStack.length > 0) {
        this.closeNestedBundle();
        return;
      }

      this.dialog = false;
      this.reset();
    },

    forceClose() {
      // Force close everything (X button)
      this.dialog = false;
      this.reset();
    },

    closeNestedBundle() {
      // Restore parent state from stack
      const parentState = this.nestedBundleStack.pop();
      if (parentState) {
        this.item = parentState.item;
        this.options = parentState.options;
        this.selections = parentState.selections;
        this.multiSelections = parentState.multiSelections;
        this.nestedSelections = parentState.nestedSelections;
        this.mealQty = parentState.mealQty;
        this.mealNotes = parentState.mealNotes;
      }
    },

    reset() {
      this.item = {};
      this.options = [];
      this.selections = {};
      this.multiSelections = {};
      this.optionQuantities = {};
      this.nestedSelections = {};
      this.mealQty = 1;
      this.mealNotes = "";
      this.expandedBundles = {};
      this.componentsCache = {};
      this.nestedBundleStack = [];
      this.nestedBundleSelections = {};
    },

    initializeDefaultSelections() {
      // Group options by classification first
      const groups = {};
      this.options.forEach((opt) => {
        const classification = opt.item_classification || "Other";
        if (!groups[classification]) {
          groups[classification] = {
            name: classification,
            options: [],
            max: opt.max_required || 999,
          };
        }
        groups[classification].options.push(opt);
      });

      // Auto-select default items
      Object.values(groups).forEach((section) => {
        section.options.forEach((option) => {
          if (option.default_selected) {
            if (section.max === 1) {
              // Single selection - set directly
              this.$set(this.selections, section.name, option.item_code);

              // If template, auto-select first variant's attributes
              if (
                option.is_template &&
                option.template_variants &&
                option.template_variants.length > 0
              ) {
                const defaultVariant =
                  option.template_variants.find((v) => v.default_selected) ||
                  option.template_variants[0];
                if (defaultVariant && defaultVariant.attributes) {
                  defaultVariant.attributes.forEach((attr) => {
                    const key = option.item_code + "_" + attr.attribute;
                    this.$set(this.nestedSelections, key, attr.attribute_value);
                  });
                }
              }
            } else {
              // Multi selection - add to array
              if (!this.multiSelections[section.name]) {
                this.$set(this.multiSelections, section.name, []);
              }
              if (this.multiSelections[section.name].length < section.max) {
                this.multiSelections[section.name].push(option.item_code);
              }
            }
          }
        });
      });
    },

    confirm() {
      // If we're in a nested bundle, save selections and go back to parent
      if (this.nestedBundleStack.length > 0) {
        this.confirmNestedBundle();
        return;
      }

      const selectedItems = [];

      // Collect single selections
      Object.entries(this.selections).forEach(([section, itemCode]) => {
        const option = this.findOption(itemCode);
        if (option) {
          if (option.is_template) {
            const variant = this.getSelectedVariant(option);
            if (variant) {
              selectedItems.push({
                ...variant,
                section,
                parent_item_code: this.item.item_code,
                is_variant: true,
              });
            }
          } else {
            selectedItems.push({
              ...option,
              section,
              parent_item_code: this.item.item_code,
            });
          }

          // Add nested bundle selections if any
          const nestedItems = this.nestedBundleSelections[itemCode];
          if (nestedItems && nestedItems.length) {
            nestedItems.forEach((nestedItem) => {
              selectedItems.push({
                ...nestedItem,
                parent_item_code: itemCode,
                is_nested_bundle_item: true,
              });
            });
          }
        }
      });

      // Collect multi-selections (with quantity)
      Object.entries(this.multiSelections).forEach(([section, itemCodes]) => {
        (itemCodes || []).forEach((itemCode) => {
          const option = this.findOption(itemCode);
          if (option) {
            const qty = this.optionQuantities[itemCode] || 1;
            selectedItems.push({
              ...option,
              section,
              parent_item_code: this.item.item_code,
              qty: qty,
            });

            // Add nested bundle selections if any
            const nestedItems = this.nestedBundleSelections[itemCode];
            if (nestedItems && nestedItems.length) {
              nestedItems.forEach((nestedItem) => {
                selectedItems.push({
                  ...nestedItem,
                  parent_item_code: itemCode,
                  is_nested_bundle_item: true,
                });
              });
            }
          }
        });
      });

      evntBus.$emit("bundle_selection_confirmed", {
        item: this.item,
        selectedItems,
        totalPrice: this.totalPrice * this.mealQty,
        qty: this.mealQty,
        notes: this.mealNotes,
      });

      this.close();
    },

    confirmNestedBundle() {
      // Collect nested selections
      const nestedSelectedItems = [];

      Object.entries(this.selections).forEach(([section, itemCode]) => {
        const option = this.findOption(itemCode);
        if (option) {
          nestedSelectedItems.push({
            ...option,
            section,
          });
        }
      });

      Object.entries(this.multiSelections).forEach(([section, itemCodes]) => {
        (itemCodes || []).forEach((itemCode) => {
          const option = this.findOption(itemCode);
          if (option) {
            nestedSelectedItems.push({
              ...option,
              section,
            });
          }
        });
      });

      // Get parent state
      const parentState =
        this.nestedBundleStack[this.nestedBundleStack.length - 1];
      const parentOption = parentState.parentOption;

      // Store nested selections
      this.$set(
        this.nestedBundleSelections,
        parentOption.item_code,
        nestedSelectedItems,
      );

      // Restore parent state
      this.closeNestedBundle();

      // Mark the parent option as selected
      const parentSection = parentState.parentSection;
      if (parentSection.max === 1) {
        this.$set(this.selections, parentSection.name, parentOption.item_code);
      } else {
        const current = this.multiSelections[parentSection.name] || [];
        if (!current.includes(parentOption.item_code)) {
          current.push(parentOption.item_code);
          this.$set(this.multiSelections, parentSection.name, current);
        }
      }
    },
  },

  created() {
    evntBus.$on("open_bundle_selector", (item, options, posProfile) => {
      this.item = item;
      this.options = options;
      this.selections = {};
      this.multiSelections = {};
      this.nestedSelections = {};
      this.ingredientsCache = {};
      this.mealQty = 1;
      this.mealNotes = "";
      this.expandedBundles = {};
      this.componentsCache = {};

      // Auto-select default items
      this.initializeDefaultSelections();

      this.dialog = true;
    });
  },

  beforeDestroy() {
    evntBus.$off("open_bundle_selector");
  },
};
</script>

<style scoped>
.bundle-selector {
  border-radius: 12px !important;
}

.bundle-selector__header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.bundle-selector__body {
  max-height: 60vh;
  overflow-y: auto;
}

.bundle-section {
  border-bottom: 1px solid #eee;
}

.bundle-section__header {
  padding: 16px 20px;
  background: #fafafa;
}

.bundle-section__title {
  font-weight: 600;
  font-size: 16px;
}

.bundle-section__badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  margin-left: 8px;
}

.bundle-section__badge--required {
  background: #e3f2fd;
  color: #1976d2;
}

.bundle-section__badge--optional {
  background: #f5f5f5;
  color: #757575;
}

.bundle-section__header--attribute {
  background: linear-gradient(90deg, #f3e5f5 0%, #fafafa 100%);
}

.bundle-section__header--package {
  background: linear-gradient(90deg, #fff3e0 0%, #fafafa 100%);
}

.bundle-section__header--add-on {
  background: linear-gradient(90deg, #e8f5e9 0%, #fafafa 100%);
}

.bundle-section__subtitle {
  font-size: 13px;
  color: #666;
  margin-top: 4px;
}

.bundle-section__options {
  padding: 8px 20px 16px;
}

.bundle-option {
  display: flex;
  align-items: flex-start;
  padding: 12px 16px;
  margin-bottom: 8px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.bundle-option:hover {
  border-color: #1976d2;
}

.bundle-option--selected {
  border-color: #1976d2;
  background: #e3f2fd;
}

.bundle-option--expandable {
  flex-direction: column;
}

.bundle-option__main {
  display: flex;
  align-items: center;
  width: 100%;
}

.bundle-option__info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-left: 8px;
}

.bundle-option__name {
  font-weight: 500;
}

.bundle-option__price {
  color: #1976d2;
  font-weight: 600;
}

.bundle-option__nested {
  width: 100%;
  padding: 16px 0 0 32px;
  border-top: 1px dashed #e0e0e0;
  margin-top: 12px;
}

.bundle-option__attribute {
  margin-bottom: 12px;
}

.bundle-option__attribute-label {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.bundle-option__ingredients {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e0e0e0;
}

.bundle-selector__footer {
  padding: 16px 20px;
}

.bundle-selector__total {
  display: flex;
  flex-direction: column;
}

.bundle-card__attr-section {
  margin-bottom: 16px;
}

.bundle-card__attr-header {
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f0f0f0;
}

.bundle-card__attr-title {
  font-weight: 700;
  font-size: 14px;
  color: #333;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: inline-block;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.bundle-card__attr-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.bundle-chip {
  font-weight: 500 !important;
  border-radius: 16px !important;
  border-width: 2px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  cursor: pointer !important;
  min-height: 36px !important;
  font-size: 13px !important;
  padding: 0 16px !important;
  background-color: #ffffff !important;
  border-color: #e0e0e0 !important;
  color: #666 !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04) !important;
}

.bundle-chip:hover {
  border-color: #667eea !important;
  color: #667eea !important;
  background-color: #f8f9ff !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.15) !important;
}

.bundle-chip:focus {
  outline: 2px solid #667eea !important;
  outline-offset: 2px !important;
}

.bundle-chip--active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border-color: transparent !important;
  color: white !important;
  font-weight: 600 !important;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
  transform: translateY(-1px) !important;
}

.bundle-chip--active:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%) !important;
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4) !important;
}

.bundle-selector__notes-field {
  margin-bottom: 0;
}

.bundle-selector__notes-field .v-input__slot {
  border-radius: 12px !important;
  min-height: 48px !important;
}

.bundle-selector__notes-field .v-input__prepend-inner {
  margin-top: 12px !important;
  margin-right: 8px !important;
}

.bundle-selector__notes-field .v-text-field__slot input {
  font-size: 14px !important;
  padding: 8px 0 !important;
}

.bundle-selector__notes-field .v-label {
  font-size: 14px !important;
}

.w-100 {
  width: 100%;
}
</style>
