<template>
  <v-dialog v-model="varaintsDialog" max-width="700px" persistent scrollable>
    <v-card class="variants-selector">
      <!-- Header -->
      <v-card-title class="variants-selector__header">
        <div class="d-flex align-center justify-space-between w-100">
          <div>
            <span class="text-h6">{{ parentItem ? parentItem.item_name : '' }}</span>
            <div class="text-caption" style="color: rgba(255,255,255,0.7)">{{ __('Customize your order') }}</div>
          </div>
          <v-btn icon dark @click="close_dialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </div>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="variants-selector__body pa-0">
        <!-- Attribute Sections -->
        <div v-for="(attr, attrIndex) in (parentItem ? parentItem.attributes : [])" :key="attr.attribute" class="variant-section">
          <!-- Section Header -->
          <div class="variant-section__header">
            <div class="d-flex align-center justify-space-between">
              <div>
                <span class="variant-section__title">{{ attr.attribute }}</span>
                <span class="variant-section__badge variant-section__badge--optional">
                  {{ __('Optional') }}
                </span>
              </div>
              <v-icon v-if="selections[attr.attribute]" color="success">mdi-check-circle</v-icon>
            </div>
            <div class="variant-section__subtitle">
              {{ __('Choose 1 choice') }}
            </div>
          </div>

          <!-- Section Options -->
          <v-row class="variant-section__options pa-2" dense>
            <v-col v-for="value in attr.values" :key="value.attribute_value" cols="6" sm="4">
              <v-card 
                class="variant-card" 
                :class="{ 'variant-card--selected': selections[attr.attribute] === value.attribute_value }"
                @click="selectAttribute(attr.attribute, value.attribute_value)"
                outlined
                hover
              >
                <!-- Selection Indicator -->
                <div class="variant-card__selector">
                  <v-icon v-if="selections[attr.attribute] === value.attribute_value" color="primary">mdi-checkbox-marked-circle</v-icon>
                  <v-icon v-else color="grey lighten-1">mdi-checkbox-blank-circle-outline</v-icon>
                </div>
                <!-- Card Content -->
                <v-card-text class="variant-card__content pa-3">
                  <div class="variant-card__name">{{ value.attribute_value }}</div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </div>

        <!-- Ingredients Section (Product Bundle items) -->
        <div v-if="ingredients.length > 0" class="variant-section">
          <div class="variant-section__header variant-section__header--ingredients">
            <div class="d-flex align-center justify-space-between">
              <div>
                <span class="variant-section__title">{{ __('المكونات') }}</span>
                <span class="variant-section__badge variant-section__badge--info">
                  {{ __('Ingredients') }}
                </span>
              </div>
              <v-icon color="orange darken-2">mdi-food-variant</v-icon>
            </div>
            <div class="variant-section__subtitle">
              {{ __('اضغط على المكون لإلغائه') }}
            </div>
          </div>

          <div class="ingredients-list pa-3">
            <v-chip
              v-for="ing in ingredients"
              v-if="ing.show_in_pos"
              :key="ing.item_code"
              class="ma-1 ingredient-chip"
              :class="{ 'ingredient-chip--removed': isIngredientRemoved(ing.item_code) }"
              small
              :outlined="!isIngredientRemoved(ing.item_code)"
              :color="isIngredientRemoved(ing.item_code) ? 'grey lighten-1' : 'orange darken-1'"
              @click="toggleIngredient(ing)"
            >
              <v-icon left small>{{ isIngredientRemoved(ing.item_code) ? 'mdi-close-circle' : 'mdi-check-circle' }}</v-icon>
              <span :class="{ 'text-decoration-line-through': isIngredientRemoved(ing.item_code) }">
                {{ ing.item_name }}
              </span>
              <span class="grey--text ml-1">({{ ing.qty }})</span>
            </v-chip>
          </div>
        </div>

        <!-- Add-ons Section -->
        <div v-if="availableAddons.length > 0" class="variant-section">
          <div class="variant-section__header variant-section__header--addon">
            <div class="d-flex align-center justify-space-between">
              <div>
                <span class="variant-section__title">{{ addonsLabel }}</span>
                <span class="variant-section__badge variant-section__badge--optional">
                  {{ __('Optional') }}
                </span>
              </div>
            </div>
            <div class="variant-section__subtitle">
              {{ __('اختر إضافات إن أردت') }}
            </div>
          </div>

          <v-row class="variant-section__options pa-2" dense>
            <v-col v-for="addon in availableAddons" :key="addon.item_code" cols="6" sm="4">
              <v-card 
                class="variant-card" 
                :class="{ 'variant-card--selected': isAddonSelected(addon.item_code) }"
                @click="toggleAddon(addon)"
                outlined
                hover
              >
                <div class="variant-card__selector">
                  <v-icon v-if="isAddonSelected(addon.item_code)" color="primary">mdi-checkbox-marked-circle</v-icon>
                  <v-icon v-else color="grey lighten-1">mdi-checkbox-blank-circle-outline</v-icon>
                </div>
                <v-card-text class="variant-card__content pa-3">
                  <div class="variant-card__name">{{ addon.item_name }}</div>
                  <div v-if="addon.price > 0" class="variant-card__price">+ {{ formatCurrency(addon.price) }}</div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </div>
      </v-card-text>

      <v-divider></v-divider>

      <!-- Footer with Qty, Notes, and Actions -->
      <v-card-actions class="variants-selector__footer pa-4">
        <v-row dense align="center">
          <!-- Quantity -->
          <v-col cols="auto">
            <div class="d-flex align-center">
              <span class="text-caption mr-2">{{ __('Qty') }}</span>
              <v-btn icon small @click="decreaseQty">
                <v-icon>mdi-minus</v-icon>
              </v-btn>
              <span class="mx-2 text-h6 font-weight-bold">{{ qty }}</span>
              <v-btn icon small color="primary" @click="increaseQty">
                <v-icon>mdi-plus</v-icon>
              </v-btn>
            </div>
          </v-col>
          
          <!-- Notes -->
          <v-col cols="4">
            <v-text-field
              v-model="notes"
              :placeholder="__('Add notes for meal...')"
              dense
              outlined
              hide-details
              class="variants-selector__notes"
            ></v-text-field>
          </v-col>
          
          <!-- Total -->
          <v-col cols="auto" class="ml-auto">
            <div class="variants-selector__total text-right">
              <span class="text-caption grey--text">{{ __('Total') }}</span>
              <span class="text-h6 primary--text ml-2">{{ formatCurrency(totalPrice * qty) }}</span>
            </div>
          </v-col>
          
          <!-- Actions -->
          <v-col cols="auto">
            <v-btn text @click="close_dialog" class="mr-2">{{ __('CANCEL') }}</v-btn>
            <v-btn color="primary" @click="confirmSelection" :disabled="!isSelectionComplete">
              {{ __('ADD TO ORDER') }}
            </v-btn>
          </v-col>
        </v-row>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { evntBus } from '../../bus';
export default {
  data: () => ({
    varaintsDialog: false,
    parentItem: null,
    items: null,
    selections: {},
    selectedAddons: [],
    qty: 1,
    notes: '',
    ingredients: [],
    loadingIngredients: false,
    removedIngredients: []
  }),

  computed: {
    variantsItems() {
      if (!this.parentItem) {
        return [];
      } else {
        return this.items.filter(
          (item) => item.variant_of == this.parentItem.item_code
        );
      }
    },

    isSelectionComplete() {
      if (!this.parentItem || !this.parentItem.attributes) return false;
      return this.parentItem.attributes.every(attr => this.selections[attr.attribute]);
    },

    matchedVariant() {
      if (!this.isSelectionComplete) return null;
      
      return this.variantsItems.find(item => {
        return item.item_attributes.every(attr => {
          return this.selections[attr.attribute] === attr.attribute_value;
        });
      });
    },

    availableAddons() {
      if (!this.parentItem || !this.parentItem.addons) return [];
      
      // Filter addons based on selected attribute values
      return this.parentItem.addons.filter(addon => {
        // If no applicable_attribute, show for all
        if (!addon.applicable_attribute || !addon.applicable_value) {
          return true;
        }
        // Check if the selected value matches
        const selectedValue = this.selections[addon.applicable_attribute];
        return selectedValue === addon.applicable_value;
      });
    },

    totalPrice() {
      let total = 0;
      
      // Add matched variant price
      if (this.matchedVariant) {
        total += this.matchedVariant.rate || 0;
      } else if (this.parentItem) {
        total += this.parentItem.rate || 0;
      }
      
      // Add selected addons prices
      this.selectedAddons.forEach(addon => {
        total += addon.price || 0;
      });
      
      return total;
    },

    addonsLabel() {
      if (this.parentItem && this.parentItem.addons_label) {
        return this.parentItem.addons_label;
      }
      return this.__('الإضافات');
    }
  },

  watch: {
    matchedVariant: {
      handler(newVariant) {
        if (newVariant) {
          this.fetchIngredients(newVariant.item_code);
        } else {
          this.ingredients = [];
        }
      },
      immediate: true
    }
  },

  methods: {
    __: (text) => __(text),

    close_dialog() {
      this.varaintsDialog = false;
      this.selections = {};
      this.selectedAddons = [];
      this.removedIngredients = [];
      this.qty = 1;
      this.notes = '';
    },

    formatCurrency(value) {
      value = parseFloat(value || 0);
      return value.toFixed(2) + ' EGP';
    },

    selectAttribute(attrName, value) {
      this.$set(this.selections, attrName, value);
    },

    increaseQty() {
      this.qty++;
    },

    decreaseQty() {
      if (this.qty > 1) {
        this.qty--;
      }
    },

    confirmSelection() {
      if (this.matchedVariant) {
        const itemToAdd = { ...this.matchedVariant };
        itemToAdd.qty = this.qty;
        itemToAdd.from_variants = true; // Flag to skip BundleSelector check
        if (this.notes) {
          itemToAdd.posa_notes = this.notes;
        }
        if (this.selectedAddons.length > 0) {
          itemToAdd.selected_addons = this.selectedAddons;
        }
        // Add selected ingredients (not removed ones)
        const selectedIngredients = this.ingredients.filter(
          ing => !this.removedIngredients.includes(ing.item_code)
        );
        if (selectedIngredients.length > 0) {
          itemToAdd.selected_ingredients = selectedIngredients;
        }
        // Track removed ingredients for notes
        if (this.removedIngredients.length > 0) {
          const removedNames = this.ingredients
            .filter(ing => this.removedIngredients.includes(ing.item_code))
            .map(ing => ing.item_name);
          itemToAdd.removed_ingredients = removedNames;
        }
        evntBus.$emit('add_item', itemToAdd);
        this.close_dialog();
      }
    },

    isAddonSelected(itemCode) {
      return this.selectedAddons.some(a => a.item_code === itemCode);
    },

    toggleAddon(addon) {
      const idx = this.selectedAddons.findIndex(a => a.item_code === addon.item_code);
      if (idx >= 0) {
        this.selectedAddons.splice(idx, 1);
      } else {
        this.selectedAddons.push({
          item_code: addon.item_code,
          item_name: addon.item_name,
          price: addon.price || 0
        });
      }
    },

    async fetchIngredients(itemCode) {
      if (!itemCode) {
        this.ingredients = [];
        return;
      }
      
      this.loadingIngredients = true;
      this.removedIngredients = []; // Reset removed when fetching new ingredients
      try {
        const res = await frappe.call({
          method: 'posawesome.posawesome.api.posapp.get_product_bundle_items_for_pos',
          args: {
            item_codes: JSON.stringify([{ item_code: itemCode, qty: 1 }])
          }
        });
        
        if (res.message && res.message.length) {
          this.ingredients = res.message;
        } else {
          this.ingredients = [];
        }
      } catch (e) {
        console.error('Error fetching ingredients:', e);
        this.ingredients = [];
      }
      this.loadingIngredients = false;
    },

    isIngredientRemoved(itemCode) {
      return this.removedIngredients.includes(itemCode);
    },

    toggleIngredient(ingredient) {
      const idx = this.removedIngredients.indexOf(ingredient.item_code);
      if (idx >= 0) {
        this.removedIngredients.splice(idx, 1);
      } else {
        this.removedIngredients.push(ingredient.item_code);
      }
    }
  },

  created: function () {
    evntBus.$on('open_variants_model', (item, items) => {
      this.varaintsDialog = true;
      this.parentItem = item || null;
      this.items = items;
      this.selections = {};
      this.selectedAddons = [];
      this.removedIngredients = [];
      this.qty = 1;
      this.notes = '';
    });
  },
};
</script>

<style scoped>
.variants-selector {
  border-radius: 12px !important;
}

.variants-selector__header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.variants-selector__body {
  max-height: 60vh;
  overflow-y: auto;
}

.variant-section {
  border-bottom: 1px solid #eee;
}

.variant-section__header {
  padding: 16px 20px;
  background: #fafafa;
}

.variant-section__header--addon {
  background: linear-gradient(90deg, #e8f5e9 0%, #fafafa 100%);
}

.variant-section__header--ingredients {
  background: linear-gradient(90deg, #fff3e0 0%, #fafafa 100%);
}

.variant-section__badge--info {
  background: #fff3e0;
  color: #e65100;
}

.ingredients-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.ingredient-chip {
  cursor: pointer;
  transition: all 0.2s ease;
}

.ingredient-chip:hover {
  transform: scale(1.05);
}

.ingredient-chip--removed {
  opacity: 0.6;
}

.text-decoration-line-through {
  text-decoration: line-through;
}

.variant-section__title {
  font-weight: 600;
  font-size: 16px;
}

.variant-section__badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  margin-left: 8px;
}

.variant-section__badge--required {
  background: #e3f2fd;
  color: #1976d2;
}

.variant-section__badge--optional {
  background: #f5f5f5;
  color: #757575;
}

.variant-section__subtitle {
  font-size: 13px;
  color: #666;
  margin-top: 4px;
}

.variant-section__options {
  padding: 8px 20px 16px;
}

.variant-card {
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  height: 100%;
}

.variant-card:hover {
  border-color: #1976d2 !important;
}

.variant-card--selected {
  border-color: #1976d2 !important;
  background: #e3f2fd;
}

.variant-card__selector {
  top: 10px;
  left: 10px;
}

.variant-card__content {
  padding-left: 40px !important;
  min-height: 50px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.variant-card__name {
  font-weight: 500;
  font-size: 14px;
}

.variant-card__price {
  color: #1976d2;
  font-weight: 600;
  font-size: 13px;
  margin-top: 4px;
}

.variants-selector__footer {
  padding: 16px 20px;
}

.variants-selector__total {
  display: flex;
  flex-direction: column;
}

.w-100 {
  width: 100%;
}
</style>
