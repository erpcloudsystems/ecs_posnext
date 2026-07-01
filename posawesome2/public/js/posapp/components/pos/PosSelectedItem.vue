<template>
  <div>
    <v-card
      class="selection modern-shell mx-auto"
      style="max-height: 80vh; height: 80vh"
    >
      <v-card-title class="selection-header">
        <div class="selection-header__icon">
          <v-icon color="secondary">mdi-format-list-bulleted</v-icon>
        </div>
        <div>
          <span class="selection-header__title">{{ __("Items Selected") }}</span>
          <p class="selection-header__subtitle">
            {{ __("Review bundle components before confirming the order.") }}
          </p>
        </div>
      </v-card-title>
      <div class="my-0 py-0 overflow-y-auto" style="max-height: 75vh">
        <template>
          <v-container>
            <v-data-table
              v-model="expanded"
              :headers="headers"
              :items="item_selected"
              :single-expand="singleExpand"
              :expanded.sync="expanded"
              show-expand
              item-key="posa_row_id"
              class="selected-items-table elevation-0"
              :items-per-page="-1"
              hide-default-footer
            >
              <!-- Main row content -->

              <!-- Expandable row content -->
              <template v-slot:expanded-item="{ headers, item }">
                <td :colspan="headers.length" class="ma-0 pa-0">
                  <v-data-table
                    :headers="subHeaders"
                    :items="item.items"
                    dense
                    :items-per-page="-1"
                    hide-default-footer
                  >
                    <template v-slot:item.item_name="{ item: subItem }">
                      <span v-if="subItem.is_deselected" class="red--text">
                        {{ subItem.item_name || subItem.item_code }}
                      </span>
                      <span v-else-if="subItem.qty === null" class="grey--text">
                        {{ subItem.item_name || subItem.item_code }}
                      </span>
                      <span v-else>
                        <v-icon small color="green" v-if="subItem.qty > 0">mdi-check-circle</v-icon>
                        <v-icon small color="red" v-else>mdi-close-circle</v-icon>
                        {{ subItem.item_name || subItem.item_code }}
                      </span>
                    </template>
                  </v-data-table>
                </td>
              </template>
            </v-data-table>
          </v-container>
        </template>
      </div>
    </v-card>

    <v-card
      flat
      style="max-height: 11vh; height: 11vh"
      class="cards mb-0 mt-3 py-0 action-bar"
    >
      <v-row align="start" no-gutters>
        <v-col cols="12">
          <v-btn
            block
            class="action-button action-button--primary"
            large
            @click="back_to_invoice"
            >{{ __("Back") }}</v-btn
          >
        </v-col>
      </v-row>
    </v-card>
  </div>
</template>

<script>
import { evntBus } from "../../bus";
import format from "../../format";
export default {
  mixins: [format],
  data: () => ({
    expanded: [],
    headers: [
      { text: __("Item"), value: "parent_item_name" },
      { text: __("Qty"), value: "qty" },
      { text: __("Notes"), value: "posa_notes" },
    ],
    subHeaders: [
      { text: __("الصنف"), value: "item_name" },
      { text: __("الكمية"), value: "qty" },
    ],
    loading: false,
    pos_profile: "",
    item_selected: [],
    allItems: [],
    discount_percentage_offer_name: null,
    itemsPerPage: 1000,
    singleExpand: true,
    items_headers: [
      { text: __("Name"), value: "item_code", align: "start" },
      { text: __("QTY"), value: "qty", align: "start" },
    ],
  }),

  computed: {
    offersCount() {
      return this.pos_offers.length;
    },
    appliedOffersCount() {
      return this.pos_offers.filter((el) => !!el.offer_applied).length;
    },
  },

  methods: {
    back_to_invoice() {
      evntBus.$emit("show_item_selected", "false");
    },
  },

  watch: {},

  created: function () {
    this.$nextTick(function () {
      evntBus.$on("register_pos_profile", (data) => {
        this.pos_profile = data.pos_profile;
      });
    });
    evntBus.$on("update_customer", (customer) => {
      if (this.customer != customer) {
        this.offers = [];
      }
    });
    evntBus.$on("update_item_selected", (data) => {
      console.log("update_item_selected", data);
      
      // Filter items: show user selections (variants, addons - not default selected, not ingredients)
      let newData = data.picked_list_for_item_bundel.filter(item => {
        if (item.hide) return false;
        // Skip product bundle ingredients (these are for stock deduction only)
        if (item.is_product_bundle_item) return false;
        // Show variants (user selected different from default)
        if (item.is_variant && item.qty > 0) return true;
        // Skip default selected items from Combo Component
        if (item.default_selected) return false;
        // Show addons with qty > 0
        if (item.addons && item.qty > 0) return true;
        return false;
      });
      
      console.log("picked_list_for_item_bundel", data.picked_list_for_item_bundel);
      console.log("filtered newData", newData);
      
      console.log("filtered_items", newData);
      const transformed = newData.reduce((acc, curr) => {
        let group = acc.find(
          (g) =>
            g.parent_item_code === curr.parent_item_code &&
            g.posa_row_id === curr.posa_row_id
        );
        if (!group) {
          group = {
            parent_item_code: curr.parent_item_code,
            parent_item_name: curr.parent_item_name || curr.parent_item_code,
            posa_row_id: curr.posa_row_id,
            items: [],
          };
          acc.push(group);
        }
        group.items.push({ item_code: curr.item_code, item_name: curr.item_name || curr.item_code, qty: curr.qty });
        return acc;
      }, []);
      console.log("transformed", transformed);
      this.item_selected = transformed;
      const result = data.items_data.reduce((acc, item) => {
        acc[item.posa_row_id] = item;
        return acc;
      }, {});
      this.item_selected.forEach((i) => {
        if (result[i.posa_row_id]) {
          const cartItem = result[i.posa_row_id];
          i.qty = cartItem.qty;
          
          if (cartItem.posa_notes) {
            i.posa_notes = cartItem.posa_notes;
            
            // Extract deselected ingredients from notes (format: "بدون: صوص، خس")
            const deselectedMatch = cartItem.posa_notes.match(/بدون:\s*([^|]+)/);
            if (deselectedMatch) {
              const deselectedItems = deselectedMatch[1].split('،').map(s => s.trim());
              deselectedItems.forEach(itemName => {
                i.items.push({
                  item_code: '❌ ' + itemName,
                  qty: 0,
                  is_deselected: true
                });
              });
            }
            
            // Show other notes (not deselected)
            const otherNotes = cartItem.posa_notes.replace(/بدون:\s*[^|]+\s*\|?\s*/, '').trim();
            if (otherNotes) {
              i.items.push({
                item_code: '📝 ' + otherNotes,
                qty: null
              });
            }
          }
        }
      });
      console.log("this.item_selected", this.item_selected);
    });
  },
};
</script>

<style scoped>
.modern-shell {
  background: linear-gradient(145deg, #ffffff 0%, #f4f6fb 100%);
  border-radius: 24px;
  box-shadow: 0 24px 48px rgba(23, 34, 59, 0.12);
  padding: 24px;
}

.selection-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 8px;
}

.selection-header__icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(44, 200, 194, 0.16);
}

.selection-header__title {
  font-size: 1.3rem;
  font-weight: 700;
  color: #17223b;
  display: block;
}

.selection-header__subtitle {
  margin: 2px 0 0;
  font-size: 0.85rem;
  color: var(--v-muted-base, #8a94a6);
}

.selected-items-table {
  border-radius: 18px;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid rgba(23, 34, 59, 0.08);
}

::v-deep .selected-items-table .v-data-table-header th {
  background: rgba(23, 34, 59, 0.04) !important;
  color: #17223b !important;
  font-weight: 600;
  font-size: 0.82rem;
}

::v-deep .selected-items-table .v-data-table__wrapper tr {
  transition: background 0.2s ease;
}

::v-deep .selected-items-table .v-data-table__wrapper tr:hover {
  background: rgba(44, 200, 194, 0.08);
}

::v-deep .selected-items-table .v-data-table__expand-content {
  background: #f4f6fb;
}

.action-bar {
  background: linear-gradient(135deg, rgba(44, 200, 194, 0.12), rgba(23, 34, 59, 0.08));
  border-radius: 18px;
  border: 1px solid rgba(23, 34, 59, 0.06);
  padding: 14px 18px !important;
}

.action-button {
  border-radius: 14px !important;
  font-weight: 600;
  text-transform: none !important;
  padding: 12px 18px !important;
  letter-spacing: 0.02em;
  box-shadow: 0 16px 32px rgba(23, 34, 59, 0.14);
}

.action-button--primary {
  background: #17223b !important;
  color: #ffffff !important;
}
</style>
