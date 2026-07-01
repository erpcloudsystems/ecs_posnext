<template>
  <v-dialog v-model="dialog" max-width="500px" persistent>
    <v-card>
      <v-card-title class="primary white--text">
        <span>{{ __('Select Variant') }}</span>
        <v-spacer></v-spacer>
        <span class="text-subtitle-2">{{ optionItem.item_name }}</span>
      </v-card-title>
      
      <v-card-text class="pa-4">
        <!-- Attribute Selection -->
        <div v-if="attributes.length > 0">
          <div v-for="attr in attributes" :key="attr.attribute" class="mb-4">
            <div class="text-subtitle-2 mb-2 font-weight-bold">{{ attr.attribute }}</div>
            <v-chip-group
              v-model="selectedAttributes[attr.attribute]"
              active-class="primary white--text"
              mandatory
            >
              <v-chip
                v-for="value in attr.values"
                :key="value.attribute_value"
                :value="value.attribute_value"
                outlined
                label
                @click="updateFilteredVariants"
              >
                {{ value.attribute_value }}
              </v-chip>
            </v-chip-group>
          </div>
        </div>

        <!-- Filtered Variants -->
        <v-divider class="my-3" v-if="attributes.length > 0"></v-divider>
        
        <div class="text-subtitle-2 mb-2 font-weight-bold">{{ __('Available Options') }}</div>
        <v-row dense>
          <v-col
            v-for="variant in filteredVariants"
            :key="variant.item_code"
            cols="6"
            sm="4"
          >
            <v-card
              :class="['variant-option', { 'selected': selectedVariant && selectedVariant.item_code === variant.item_code }]"
              @click="selectVariant(variant)"
              outlined
              hover
            >
              <v-card-text class="text-center pa-3">
                <div class="font-weight-medium text-body-2">{{ getVariantDisplayName(variant) }}</div>
                <div class="primary--text font-weight-bold mt-1">
                  {{ formatCurrency(variant.standard_rate) }}
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <div v-if="filteredVariants.length === 0" class="text-center grey--text pa-4">
          {{ __('No variants match your selection') }}
        </div>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text @click="cancel">{{ __('Cancel') }}</v-btn>
        <v-btn 
          color="primary" 
          @click="confirm"
          :disabled="!selectedVariant"
        >
          {{ __('Select') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { evntBus } from '../../bus';

export default {
  name: 'OptionVariantSelector',
  
  data() {
    return {
      dialog: false,
      optionItem: {},
      attributes: [],
      variants: [],
      selectedAttributes: {},
      filteredVariants: [],
      selectedVariant: null,
      callback: null
    };
  },

  methods: {
    __(text) {
      return __(text);
    },

    formatCurrency(value) {
      if (!value) return '0.00';
      return parseFloat(value).toFixed(2);
    },

    getVariantDisplayName(variant) {
      if (variant.attributes && variant.attributes.length > 0) {
        return variant.attributes.map(a => a.attribute_value).join(' - ');
      }
      return variant.item_name;
    },

    updateFilteredVariants() {
      this.$nextTick(() => {
        if (Object.keys(this.selectedAttributes).length === 0) {
          this.filteredVariants = this.variants;
          return;
        }

        this.filteredVariants = this.variants.filter(variant => {
          return variant.attributes.every(attr => {
            const selected = this.selectedAttributes[attr.attribute];
            return !selected || selected === attr.attribute_value;
          });
        });

        // Auto-select if only one variant matches
        if (this.filteredVariants.length === 1) {
          this.selectedVariant = this.filteredVariants[0];
        } else {
          this.selectedVariant = null;
        }
      });
    },

    selectVariant(variant) {
      this.selectedVariant = variant;
    },

    confirm() {
      if (this.selectedVariant && this.callback) {
        this.callback(this.selectedVariant);
      }
      this.dialog = false;
      this.reset();
    },

    cancel() {
      this.dialog = false;
      this.reset();
    },

    reset() {
      this.optionItem = {};
      this.attributes = [];
      this.variants = [];
      this.selectedAttributes = {};
      this.filteredVariants = [];
      this.selectedVariant = null;
      this.callback = null;
    }
  },

  created() {
    evntBus.$on('open_option_variant_selector', (optionItem, callback) => {
      this.optionItem = optionItem;
      this.attributes = optionItem.template_attributes || [];
      this.variants = optionItem.template_variants || [];
      this.selectedAttributes = {};
      this.filteredVariants = this.variants;
      this.selectedVariant = null;
      this.callback = callback;
      this.dialog = true;
    });
  },

  beforeDestroy() {
    evntBus.$off('open_option_variant_selector');
  }
};
</script>

<style scoped>
.variant-option {
  cursor: pointer;
  transition: all 0.2s;
}

.variant-option:hover {
  border-color: var(--v-primary-base) !important;
}

.variant-option.selected {
  border-color: var(--v-primary-base) !important;
  background-color: var(--v-primary-lighten5) !important;
}
</style>
