<template>
  <v-container fluid class="new-product-editor pa-0 rtl-scope" dir="rtl">
    <!-- Header -->
    <div class="editor-header">
      <v-btn icon @click="goBack" class="me-3">
        <v-icon color="white">mdi-arrow-right</v-icon>
      </v-btn>
      <div class="flex-grow-1">
        <div class="text-h5 font-weight-bold white--text">
          {{ isEditing ? product.item_name : __("إضافة صنف جديد") }}
        </div>
        <div class="text-caption white--text" style="opacity: 0.8">
          {{ productTypeLabel }}
        </div>
      </div>
      <v-btn color="white" depressed @click="saveProduct" :loading="saving">
        <v-icon right>mdi-check</v-icon>
        {{ __("حفظ") }}
      </v-btn>
    </div>

    <!-- Loading -->
    <v-progress-linear v-if="loading" indeterminate color="primary"></v-progress-linear>

    <!-- Content -->
    <div class="editor-body" v-if="!loading">
      <v-row no-gutters>
        <!-- right Panel - Basic Info -->
        <v-col cols="12" md="4" class="panel panel--right px-2 py-3">
          <div class="panel-title" style="height: 40px !important">
            {{ __("المعلومات الأساسية") }}
          </div>

          <!-- Product Type -->
          <div class="form-group">
            <label class="form-label">{{ __("نوع الصنف") }}</label>
            <v-btn-toggle v-model="product.product_type" mandatory class="mt-2 d-flex">
              <v-btn value="standard" class="flex-grow-1" :disabled="isEditing">
                <v-icon right small>mdi-food</v-icon>
                {{ __("وجبة عادية") }}
              </v-btn>
              <v-btn value="combo" class="flex-grow-1" :disabled="isEditing">
                <v-icon right small>mdi-food-variant</v-icon>
                {{ __("كومبو") }}
              </v-btn>
            </v-btn-toggle>
          </div>

          <!-- Item Name ar -->
          <div class="form-group">
            <label class="form-label">{{ __("اسم الصنف بالعربي") }} *</label>
            <v-text-field v-model="product.custom_item_name_arabic" outlined dense hide-details="auto"
              :placeholder="__('مثال: برجر دجاج')"></v-text-field>
          </div>
          <!-- Item Name -->
          <div class="form-group">
            <label class="form-label">{{ __("اسم الصنف بالانجليزي") }} *</label>
            <v-text-field v-model="product.item_name" outlined dense hide-details="auto"
              :placeholder="__('ex: checkin Burger')"></v-text-field>
          </div>

          <!-- Item Code -->
          <div class="form-group" v-if="!isEditing">
            <label class="form-label">{{ __("كود الصنف (Item Code)") }} *</label>
            <v-text-field v-model="product.item_code" outlined dense hide-details="auto"
              :placeholder="__('ex: BURGER-001')"></v-text-field>
          </div>

          <!-- Category -->
          <div class="form-group">
            <label class="form-label">{{ __("الفئة") }} *</label>
            <v-autocomplete v-model="product.item_group" :items="categories" item-text="name" item-value="name" outlined
              dense hide-details="auto" :placeholder="__('اختر الفئة')"></v-autocomplete>
          </div>

          <!-- Base Price (for standard without variants) -->
          <!-- <div
            class="form-group"
            v-if="product.product_type === 'standard' && !hasVariants"
          >
            <label class="form-label">{{ __("السعر") }}</label>
            <v-text-field
              v-model.number="product.standard_rate"
              type="number"
              outlined
              dense
              hide-details
              suffix="EGP"
              min="0"
            ></v-text-field>
          </div> -->

          <!-- Combo Price -->
          <!-- <div class="form-group" v-if="product.product_type === 'combo'">
            <label class="form-label">{{ __("سعر الكومبو") }}</label>
            <v-text-field
              v-model.number="product.standard_rate"
              type="number"
              outlined
              dense
              hide-details
              suffix="EGP"
              min="0"
            ></v-text-field>
          </div> -->

          <!-- Image -->
          <!-- <div class="form-group">
            <label class="form-label">{{ __("الصورة") }}</label>
            <v-text-field
              v-model="product.image"
              outlined
              dense
              hide-details
              placeholder="https://..."
            ></v-text-field>
          </div> -->

          <!-- Settings -->
          <div class="form-group" dir="ltr">
            <v-switch v-model="product.custom_is_pos_item" :label="__('إظهار في الـ POS')" hide-details
              color="primary"></v-switch>
            <v-switch v-model="product.custom_fast_sell" :label="__('بيع سريع (بدون dialog)')" hide-details
              color="primary"></v-switch>
          </div>

          <!-- Price Lists Section -->
          <div class="form-group">
            <label class="form-label d-flex align-center justify-space-between">
              <span>{{ __("الأسعار") }}</span>
              <v-btn icon x-small color="primary" @click="addPriceRow">
                <v-icon small>mdi-plus</v-icon>
              </v-btn>
            </label>
            <div v-if="itemPrices.length === 0" class="text-caption grey--text pa-2">
              {{ __("اضغط + لإضافة سعر") }}
            </div>
            <div v-for="(priceItem, idx) in itemPrices" :key="idx" class="d-flex align-center mb-2">
              <v-autocomplete v-model="priceItem.price_list" :items="priceLists" item-text="name" item-value="name"
                outlined dense hide-details :placeholder="__('قائمة الأسعار')" class="me-2"
                style="flex: 1"></v-autocomplete>
              <v-text-field v-model.number="priceItem.price" type="number" outlined dense hide-details suffix="EGP"
                min="0" style="max-width: 120px"></v-text-field>
              <v-btn icon x-small color="error" @click="removePriceRow(idx)" class="ms-1">
                <v-icon small>mdi-close</v-icon>
              </v-btn>
            </div>
          </div>
        </v-col>

        <!-- Middle Panel - Variants (for Standard) -->
        <v-col cols="12" md="4" class="panel panel--middle px-4 py-3" v-if="product.product_type === 'standard'">
          <div class="panel-title d-flex align-center justify-space-between">
            <span>{{ __("الأحجام والأنواع (Variants)") }}</span>
            <div dir="ltr" class="d-inline-flex align-center">
              <v-switch v-model="hasVariants" hide-details class="mt-0" color="primary" />
            </div>
          </div>

          <template v-if="hasVariants">
            <!-- Attributes Section -->
            <div class="section-box mb-4">
              <div class="section-box__header">
                <span>{{ __("الخصائص (Attributes)") }}</span>
                <v-btn icon small color="primary" @click="showAddAttributeDialog = true">
                  <v-icon small>mdi-plus</v-icon>
                </v-btn>
              </div>
              <div class="section-box__body">
                <div v-if="product.attributes.length === 0" class="text-center grey--text pa-4">
                  <div>{{ __("لا توجد خصائص") }}</div>
                  <div class="text-caption mt-2">
                    {{
                      __(
                        'مثال: أضف "Size" بقيم (Double, Single) ثم "Type" بقيم (Spicy, Regular)',
                      )
                    }}
                  </div>
                </div>
                <div v-for="(attr, idx) in product.attributes" :key="attr.attribute" class="attribute-item mb-2">
                  <div class="d-flex align-center">
                    <v-chip color="primary" small class="ms-2 pa-2">{{
                      idx + 1
                      }}</v-chip>
                    <strong>{{ attr.attribute }}</strong>
                    <v-btn icon x-small color="error" @click="removeAttribute(attr)" class="ms-auto">
                      <v-icon x-small>mdi-close</v-icon>
                    </v-btn>
                  </div>
                  <div class="mt-1 ms-8">
                    <v-chip v-for="val in attr.values" :key="val" x-small outlined class="me-1 mb-1">
                      {{ val }}
                    </v-chip>
                  </div>
                </div>
                <v-alert v-if="product.attributes.length >= 2" type="info" dense text class="mt-2 text-caption">
                  {{ __("سيتم توليد") }} {{ expectedVariantsCount }}
                  {{ __("variant من combinations الخصائص") }}
                </v-alert>
              </div>
            </div>

            <!-- Variants Section -->
            <div class="section-box">
              <div class="section-box__header">
                <span>{{ __("المتغيرات (Variants)") }}</span>
                <v-btn text small color="primary" @click="generateAllVariants"
                  :disabled="product.attributes.length === 0">
                  <v-icon right small>mdi-auto-fix</v-icon>
                  {{ __("توليد تلقائي") }}
                </v-btn>
              </div>
              <div class="section-box__body">
                <div v-if="product.variants.length === 0" class="text-center grey--text pa-4">
                  <div>{{ __("لا توجد متغيرات") }}</div>
                  <div class="text-caption mt-2">
                    {{ __('أضف الخصائص أولاً ثم اضغط "توليد تلقائي"') }}
                  </div>
                </div>

                <!-- Grouped view when 2+ attributes -->
                <template v-if="
                  product.attributes.length >= 2 &&
                  product.variants.length > 0
                ">
                  <div v-for="(group, groupName) in groupedVariants" :key="groupName" class="variant-group mb-3">
                    <div class="variant-group__header">
                      <v-icon small color="primary" class="me-1">mdi-folder-outline</v-icon>
                      <strong>{{ groupName }}</strong>
                    </div>
                    <div class="variant-group__items">
                      <div v-for="variant in group" :key="variant.name" class="variant-row variant-row--nested">
                        <v-text-field v-model="variant.name" outlined dense hide-details
                          :placeholder="__('اسم المتغير')" class="variant-row__name flex-grow-1"></v-text-field>
                        <v-text-field v-model="variant.item_code" outlined dense hide-details
                          :placeholder="__('كود الصنف')" class="variant-row__code" style="max-width: 150px"
                          :disabled="variant.isExisting"></v-text-field>
                        <v-text-field v-model.number="variant.price" type="number" outlined dense hide-details
                          suffix="EGP" class="variant-row__price" style="max-width: 100px" min="0"></v-text-field>
                        <v-tooltip bottom>
                          <template v-slot:activator="{ on }">
                            <v-btn icon x-small v-on="on" @click="
                              variant.show_bundle = !variant.show_bundle
                              " :color="variant.show_bundle ? 'orange' : 'grey'">
                              <v-icon x-small>mdi-package-variant</v-icon>
                            </v-btn>
                          </template>
                          <span>{{ __("عرض المكونات في POS") }}</span>
                        </v-tooltip>
                        <v-btn icon x-small color="primary" @click="openRecipeDialog(variant)"
                          :disabled="!variant.item_code">
                          <v-icon x-small>mdi-chef-hat</v-icon>
                        </v-btn>
                        <v-btn icon x-small color="error" @click="removeVariantByName(variant.name)">
                          <v-icon x-small>mdi-delete</v-icon>
                        </v-btn>
                      </div>
                    </div>
                  </div>
                </template>

                <!-- Flat view for single attribute -->
                <template v-else-if="product.variants.length > 0">
                  <div v-for="(variant, index) in product.variants" :key="index" class="variant-row">
                    <v-text-field v-model="variant.name" outlined dense hide-details :placeholder="__('اسم المتغير')"
                      class="variant-row__name flex-grow-1"></v-text-field>
                    <v-text-field v-model="variant.item_code" outlined dense hide-details :placeholder="__('كود الصنف')"
                      class="variant-row__code" style="max-width: 150px" :disabled="variant.isExisting"></v-text-field>
                    <v-text-field v-model.number="variant.price" type="number" outlined dense hide-details suffix="EGP"
                      class="variant-row__price" style="max-width: 120px" min="0"></v-text-field>
                    <v-tooltip bottom>
                      <template v-slot:activator="{ on }">
                        <v-btn icon small v-on="on" @click="variant.show_bundle = !variant.show_bundle"
                          :color="variant.show_bundle ? 'orange' : 'grey'">
                          <v-icon small>mdi-package-variant</v-icon>
                        </v-btn>
                      </template>
                      <span>{{ __("عرض المكونات في POS") }}</span>
                    </v-tooltip>
                    <v-btn icon small color="primary" @click="openRecipeDialog(variant)" :disabled="!variant.item_code">
                      <v-icon small>mdi-chef-hat</v-icon>
                    </v-btn>
                    <v-btn icon small color="error" @click="removeVariant(index)">
                      <v-icon small>mdi-delete</v-icon>
                    </v-btn>
                  </div>
                </template>

                <v-btn text small color="primary" @click="addManualVariant" class="mt-2">
                  <v-icon right small>mdi-plus</v-icon>
                  {{ __("إضافة متغير") }}
                </v-btn>
              </div>
            </div>

            <!-- Add-ons Section for Standard Items -->
            <div class="section-box mt-4">
              <div class="section-box__header">
                <span>{{ __("الإضافات (Add-ons)") }}</span>
                <v-btn icon small color="primary" @click="showAddAddonDialog = true">
                  <v-icon small>mdi-plus</v-icon>
                </v-btn>
              </div>
              <div class="section-box__body">
                <!-- Custom Label for Addons -->
                <v-text-field v-model="product.addons_label" outlined dense hide-details
                  :label="__('عنوان الإضافات في الكاشير')" :placeholder="__('مثال: اختر الصوص')"
                  class="mb-3"></v-text-field>
                <div v-if="product.addons.length === 0" class="text-center grey--text pa-4">
                  {{ __("لا توجد إضافات. أضف إضافات مثل: جبنة إضافية، صوص") }}
                </div>
                <div v-for="(addon, idx) in product.addons" :key="idx" class="addon-row">
                  <span class="addon-row__name">{{
                    addon.item_name || addon.item_code
                    }}</span>
                  <v-text-field v-model.number="addon.price" type="number" outlined dense hide-details suffix="EGP"
                    style="max-width: 80px" min="0"></v-text-field>
                  <v-select v-model="addon.applicable_attribute" :items="product.attributes.map((a) => a.attribute)"
                    outlined dense hide-details clearable :placeholder="__('كل الأحجام')" style="max-width: 100px"
                    class="mx-1"></v-select>
                  <v-select v-if="addon.applicable_attribute" v-model="addon.applicable_value"
                    :items="getAttributeValues(addon.applicable_attribute)" outlined dense hide-details
                    :placeholder="__('القيمة')" style="max-width: 100px"></v-select>
                  <v-btn icon x-small color="error" @click="removeAddon(idx)">
                    <v-icon x-small>mdi-delete</v-icon>
                  </v-btn>
                </div>
              </div>
            </div>
          </template>

          <div v-else class="text-center grey--text pa-6">
            <v-icon size="48" color="grey lighten-2">mdi-tag-multiple-outline</v-icon>
            <div class="mt-2">
              {{ __("فعّل الـ Variants لإضافة أحجام وأنواع مختلفة") }}
            </div>
          </div>
        </v-col>

        <!-- Middle Panel - Components (for Combo) -->
        <v-col cols="12" md="4" class="panel panel--middle px-2 py-3" v-if="product.product_type === 'combo'">
          <div class="panel-title" style="height: 40px !important">
            {{ __("مكونات الكومبو") }}
          </div>

          <!-- Sections -->
          <div v-for="(section, sIndex) in product.sections" :key="sIndex" class="combo-section mb-4">
            <div class="combo-section__header">
              <v-text-field v-model="section.name" outlined dense hide-details
                :placeholder="__('اسم القسم (مثال: Size, Type, Packages)')" class="flex-grow-1"></v-text-field>
              <v-btn icon small color="error" @click="removeSection(sIndex)" class="ms-2">
                <v-icon small>mdi-delete</v-icon>
              </v-btn>
            </div>

            <div class="combo-section__settings">
              <v-select v-model="section.section_type" :items="sectionTypes" item-text="label" item-value="value"
                outlined dense hide-details :label="__('النوع')" style="max-width: 130px" class="me-2"></v-select>
              <v-checkbox v-model="section.is_required" :label="__('إلزامي')" hide-details class="mt-2 me-2"
                dense></v-checkbox>
              <v-text-field v-model.number="section.min_qty" type="number" outlined dense hide-details
                :label="__('الحد الأدنى')" min="0" style="max-width: 80px" class="me-2"></v-text-field>
              <v-text-field v-model.number="section.max_qty" type="number" outlined dense hide-details
                :label="__('الحد الأقصى')" min="1" style="max-width: 80px"></v-text-field>
            </div>

            <!-- Options -->
            <div class="combo-section__options">
              <div v-for="(option, oIndex) in section.options" :key="oIndex" class="option-item">
                <!-- Regular item or Template header -->
                <div class="option-row" :class="{ 'option-row--template': option.has_variants }">
                  <v-checkbox v-model="option.default_selected" hide-details class="mt-0 me-2"
                    :title="__('محدد افتراضياً')" v-if="!option.has_variants"></v-checkbox>
                  <v-icon v-if="option.has_variants" small class="me-2 cursor-pointer" color="primary"
                    @click="toggleOptionExpanded(option)">{{
                      option.expanded === true
                        ? "mdi-chevron-up"
                        : "mdi-chevron-down"
                    }}</v-icon>
                  <v-autocomplete v-model="option.item_code" :items="availableItems" item-text="item_name"
                    item-value="item_code" outlined dense hide-details :placeholder="__('اختر صنف')" class="flex-grow-1"
                    @change="onOptionSelect(option, section)"></v-autocomplete>
                  <v-text-field v-model.number="option.extra_price" type="number" outlined dense hide-details prefix="+"
                    suffix="EGP" class="mx-2" style="max-width: 100px" v-if="!option.has_variants"></v-text-field>
                  <v-text-field v-model.number="option.global_price" type="number" outlined dense hide-details
                    prefix="+" suffix="EGP" class="mx-2" style="max-width: 100px" v-if="option.has_variants"
                    @input="applyGlobalPriceToVariants(option)" :placeholder="__('سعر موحد')"></v-text-field>
                  <!-- Min/Max Qty for Standard templates -->
                  <v-text-field v-model.number="option.min_qty" type="number" outlined dense hide-details
                    :label="__('Min')" min="0" style="max-width: 60px" class="mx-1" 
                    v-if="option.has_variants && isStandardItem(option)"></v-text-field>
                  <v-text-field v-model.number="option.max_qty" type="number" outlined dense hide-details
                    :label="__('Max')" min="1" style="max-width: 60px" class="mx-1"
                    v-if="option.has_variants && isStandardItem(option)"></v-text-field>
                  <v-tooltip bottom v-if="option.item_code && !option.has_variants">
                    <template v-slot:activator="{ on, attrs }">
                      <v-checkbox v-model="option.show_bundle_in_pos" v-bind="attrs" v-on="on" hide-details
                        class="mt-0 mx-1" color="orange" dense></v-checkbox>
                    </template>
                    <span>{{ __("إظهار المكونات في الكاشير") }}</span>
                  </v-tooltip>
                  <v-btn icon x-small :color="optionBundles[option.item_code] ? 'orange' : 'grey'"
                    @click="toggleOptionBundle(option)" :title="__('Product Bundle')"
                    v-if="option.item_code && !option.has_variants">
                    <v-icon small>mdi-package-variant</v-icon>
                  </v-btn>
                  <v-btn icon x-small color="error" @click="removeOption(section, oIndex)">
                    <v-icon small>mdi-close</v-icon>
                  </v-btn>
                </div>

                <!-- Nested variants -->
                <div v-if="
                  option.has_variants &&
                  option.variants &&
                  option.expanded === true
                " class="nested-variants">
                  <div v-for="(variant, vIndex) in option.variants" :key="vIndex" class="option-row option-row--nested">
                    <v-checkbox v-model="variant.default_selected" hide-details class="mt-0 me-2"
                      :title="__('محدد افتراضياً')"></v-checkbox>
                    <span class="variant-name flex-grow-1">{{
                      variant.item_name
                      }}</span>
                    <v-text-field v-model.number="variant.extra_price" type="number" outlined dense hide-details
                      prefix="+" suffix="EGP" class="mx-2" style="max-width: 100px"></v-text-field>
                    <v-tooltip bottom v-if="variant.item_code">
                      <template v-slot:activator="{ on, attrs }">
                        <v-checkbox v-model="variant.show_bundle_in_pos" v-bind="attrs" v-on="on" hide-details
                          class="mt-0 mx-1" color="orange" dense></v-checkbox>
                      </template>
                      <span>{{ __("إظهار المكونات في الكاشير") }}</span>
                    </v-tooltip>
                    <v-btn icon x-small :color="optionBundles[variant.item_code] ? 'orange' : 'grey'
                      " @click="toggleOptionBundle(variant)" :title="__('Product Bundle')" v-if="variant.item_code">
                      <v-icon small>mdi-package-variant</v-icon>
                    </v-btn>
                    <v-btn icon x-small color="error" @click="removeNestedVariant(option, vIndex)">
                      <v-icon small>mdi-close</v-icon>
                    </v-btn>
                  </div>
                  <!-- Add variant button -->
                  <v-btn text x-small color="secondary" @click="openAddVariantDialog(option)" class="mt-1 ms-6">
                    <v-icon right x-small>mdi-plus</v-icon>
                    {{ __("إضافة variant") }}
                  </v-btn>
                </div>
              </div>
              <v-btn text small color="primary" @click="addOption(section)" class="mt-2">
                <v-icon right small>mdi-plus</v-icon>
                {{ __("إضافة صنف") }}
              </v-btn>
            </div>
          </div>

          <v-btn outlined color="primary" @click="addSection" class="mt-2">
            <v-icon right>mdi-plus</v-icon>
            {{ __("إضافة قسم") }}
          </v-btn>
        </v-col>

        <!-- Right Panel - Recipe/Preview -->
        <v-col cols="12" md="4" class="panel panel--right px-2 py-3">
          <!-- Recipe for simple items (no variants) -->
          <div v-if="product.product_type === 'standard' && !hasVariants">
            <div class="panel-title" style="height: 40px !important">
              {{ __("الوصفة / المكونات") }}
            </div>
            <div class="recipe-section">
              <div class="text-center grey--text pa-6" v-if="!isEditing">
                <v-icon size="48" color="grey lighten-2">mdi-chef-hat</v-icon>
                <div class="mt-2">
                  {{ __("احفظ الصنف أولاً لإدارة الوصفة") }}
                </div>
              </div>
              <div v-else>
                <v-btn outlined color="primary" @click="openRecipeDialog()" block>
                  <v-icon right>mdi-chef-hat</v-icon>
                  {{ __("إدارة المكونات") }}
                </v-btn>
              </div>
            </div>
          </div>

          <!-- Info for variants -->
          <div v-if="hasVariants" class="mb-4">
            <div class="panel-title" style="height: 40px !important">
              {{ __("الوصفات") }}
            </div>
            <v-alert type="info" dense text class="text-caption">
              {{
                __("اضغط على أيقونة الوصفة 🍳 بجوار كل variant لإدارة وصفته")
              }}
            </v-alert>
          </div>

          <!-- Packaging Section -->
          <div class="packaging-section">
            <div class="panel-title" style="height: 40px !important">
              {{ __("مواد التغليف (Packaging)") }}
            </div>
            <v-expansion-panels accordion flat>
              <!-- Delivery Packaging -->
              <v-expansion-panel>
                <v-expansion-panel-header>
                  <div class="d-flex align-center">
                    <v-icon small right class="me-2">mdi-truck-delivery</v-icon>
                    {{ __("Delivery") }}
                    <v-chip x-small class="ms-2" v-if="product.packaging_delivery.length">
                      {{ product.packaging_delivery.length }}
                    </v-chip>
                  </div>
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                  <div v-for="(pkg, idx) in product.packaging_delivery" :key="'del-' + idx"
                    class="d-flex align-center mb-2">
                    <v-autocomplete v-model="pkg.item_code" :items="packagingItems" item-text="item_name"
                      item-value="item_code" outlined dense hide-details :placeholder="__('اختر الصنف')"
                      class="flex-grow-1"></v-autocomplete>
                    <v-text-field v-model.number="pkg.qty" type="number" outlined dense hide-details class="mx-2"
                      style="max-width: 80px" min="1"></v-text-field>
                    <v-btn icon small color="error" @click="product.packaging_delivery.splice(idx, 1)">
                      <v-icon small>mdi-delete</v-icon>
                    </v-btn>
                  </div>
                  <v-btn text small color="primary" @click="addPackaging('delivery')">
                    <v-icon right small>mdi-plus</v-icon>
                    {{ __("إضافة") }}
                  </v-btn>
                </v-expansion-panel-content>
              </v-expansion-panel>

              <!-- Dine-in Packaging -->
              <v-expansion-panel>
                <v-expansion-panel-header>
                  <div class="d-flex align-center">
                    <v-icon small right class="me-2">mdi-silverware-fork-knife</v-icon>
                    {{ __("Dine-in") }}
                    <v-chip x-small class="ms-2" v-if="product.packaging_dinein.length">
                      {{ product.packaging_dinein.length }}
                    </v-chip>
                  </div>
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                  <div v-for="(pkg, idx) in product.packaging_dinein" :key="'din-' + idx"
                    class="d-flex align-center mb-2">
                    <v-autocomplete v-model="pkg.item_code" :items="packagingItems" item-text="item_name"
                      item-value="item_code" outlined dense hide-details :placeholder="__('اختر الصنف')"
                      class="flex-grow-1"></v-autocomplete>
                    <v-text-field v-model.number="pkg.qty" type="number" outlined dense hide-details class="mx-2"
                      style="max-width: 80px" min="1"></v-text-field>
                    <v-btn icon small color="error" @click="product.packaging_dinein.splice(idx, 1)">
                      <v-icon small>mdi-delete</v-icon>
                    </v-btn>
                  </div>
                  <v-btn text small color="primary" @click="addPackaging('dinein')">
                    <v-icon right small>mdi-plus</v-icon>
                    {{ __("إضافة") }}
                  </v-btn>
                </v-expansion-panel-content>
              </v-expansion-panel>

              <!-- Takeaway Packaging -->
              <v-expansion-panel>
                <v-expansion-panel-header>
                  <div class="d-flex align-center">
                    <v-icon small right class="me-2">mdi-shopping-outline</v-icon>
                    {{ __("Takeaway") }}
                    <v-chip x-small class="ms-2" v-if="product.packaging_takeaway.length">
                      {{ product.packaging_takeaway.length }}
                    </v-chip>
                  </div>
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                  <div v-for="(pkg, idx) in product.packaging_takeaway" :key="'take-' + idx"
                    class="d-flex align-center mb-2">
                    <v-autocomplete v-model="pkg.item_code" :items="packagingItems" item-text="item_name"
                      item-value="item_code" outlined dense hide-details :placeholder="__('اختر الصنف')"
                      class="flex-grow-1"></v-autocomplete>
                    <v-text-field v-model.number="pkg.qty" type="number" outlined dense hide-details class="mx-2"
                      style="max-width: 80px" min="1"></v-text-field>
                    <v-btn icon small color="error" @click="product.packaging_takeaway.splice(idx, 1)">
                      <v-icon small>mdi-delete</v-icon>
                    </v-btn>
                  </div>
                  <v-btn text small color="primary" @click="addPackaging('takeaway')">
                    <v-icon right small>mdi-plus</v-icon>
                    {{ __("إضافة") }}
                  </v-btn>
                </v-expansion-panel-content>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>

          <!-- Preview -->
          <div class="preview-section mt-6" v-if="product.item_name || product.custom_item_name_arabic">
            <div class="panel-title">{{ __("معاينة") }}</div>
            <v-card outlined class="pa-3">
              <div class="d-flex align-center">
                <v-avatar size="60" color="grey lighten-3" class="me-3">
                  <v-img v-if="product.image" :src="product.image"></v-img>
                  <v-icon v-else>mdi-food</v-icon>
                </v-avatar>
                <div>
                  <div class="font-weight-bold">
                    {{ product.item_name }} |
                    {{ product.custom_item_name_arabic }}
                  </div>
                  <div class="text-caption grey--text">
                    {{ product.item_group }}
                  </div>
                  <div class="primary--text font-weight-bold" v-if="!hasVariants || product.product_type === 'combo'">
                    {{ product.standard_rate || 0 }} EGP
                  </div>
                </div>
              </div>

              <div v-if="hasVariants && product.variants.length > 0" class="mt-3">
                <div class="text-caption grey--text mb-1">
                  {{ __("الأسعار:") }}
                </div>
                <v-chip v-for="v in product.variants" :key="v.name" x-small class="me-1 mb-1" outlined>
                  {{ v.name }}: {{ v.price }} EGP
                </v-chip>
              </div>
            </v-card>
          </div>
        </v-col>
      </v-row>
    </div>

    <!-- Recipe Dialog -->
    <v-dialog v-model="showRecipeDialog" max-width="600px" class="rounded">
      <v-card>
        <v-card-title>
          <v-icon right>mdi-package-variant</v-icon>
          {{ __("المكونات:") }} {{ currentRecipeItem }}
        </v-card-title>
        <v-card-text>
          <div v-for="(ingredient, index) in recipe.ingredients" :key="index" class="d-flex align-center mb-2">
            <v-autocomplete v-model="ingredient.item_code" :items="rawMaterials" item-text="item_name"
              item-value="item_code" outlined dense hide-details :placeholder="__('اختر المكون')" class="flex-grow-1"
              @change="onIngredientSelect(ingredient)"></v-autocomplete>
            <v-text-field v-model.number="ingredient.qty" type="number" outlined dense hide-details
              :label="__('الكمية')" class="mx-2" style="max-width: 100px" min="0.01" step="0.01"></v-text-field>
            <v-select v-model="ingredient.uom" :items="uoms" item-text="name" item-value="name" outlined dense
              hide-details style="max-width: 100px"></v-select>
            <v-checkbox v-model="ingredient.show_in_pos" :label="__('يظهر للكاشير')" hide-details dense
              class="mx-2 mt-0"></v-checkbox>
            <v-btn icon small color="error" @click="removeIngredient(index)" class="ms-2">
              <v-icon small>mdi-delete</v-icon>
            </v-btn>
          </div>
          <v-btn text small color="primary" @click="addIngredient" class="mt-2">
            <v-icon right small>mdi-plus</v-icon>
            {{ __("إضافة مكون") }}
          </v-btn>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="showRecipeDialog = false">{{
            __("إلغاء")
            }}</v-btn>
          <v-btn color="primary" @click="saveRecipe" :loading="savingRecipe">{{
            __("حفظ المكونات")
            }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Add Attribute Dialog -->
    <v-dialog v-model="showAddAttributeDialog" max-width="400px">
      <v-card>
        <v-card-title>{{ __("إضافة خاصية جديدة") }}</v-card-title>
        <v-card-text>
          <div class="form-group">
            <label class="form-label">{{ __("اسم الخاصية") }}</label>
            <v-combobox v-model="newAttribute.name" :items="availableAttributeNames" outlined dense hide-details
              :placeholder="__('مثال: الحجم')" @change="onAttributeNameSelect"></v-combobox>
          </div>
          <div class="form-group mt-4">
            <label class="form-label">{{ __("القيم (مفصولة بفاصلة)") }}</label>
            <v-text-field v-model="newAttribute.values" outlined dense hide-details
              :placeholder="__('مثال: صغير, وسط, كبير')"></v-text-field>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="showAddAttributeDialog = false">{{
            __("إلغاء")
            }}</v-btn>
          <v-btn color="primary" @click="addAttribute">{{ __("إضافة") }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Add Addon Dialog -->
    <v-dialog v-model="showAddAddonDialog" max-width="400px">
      <v-card>
        <v-card-title>{{ __("إضافة إضافة جديدة") }}</v-card-title>
        <v-card-text>
          <v-autocomplete v-model="selectedAddon" :items="availableItems" :search-input.sync="addonSearchQuery"
            item-text="item_name" item-value="item_code" outlined dense :placeholder="__('ابحث عن صنف...')"
            return-object :loading="searchingAddons" @update:search-input="searchAddons"></v-autocomplete>
          <v-text-field v-if="selectedAddon" v-model.number="addonPrice" type="number" outlined dense
            :label="__('السعر الإضافي')" suffix="EGP" min="0" class="mt-3"></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="showAddAddonDialog = false">{{
            __("إلغاء")
            }}</v-btn>
          <v-btn color="primary" @click="addAddon" :disabled="!selectedAddon">{{
            __("إضافة")
            }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Add Variant to Combo Dialog -->
    <v-dialog v-model="showAddVariantDialog" max-width="400px">
      <v-card>
        <v-card-title>{{ __("إضافة variant") }}</v-card-title>
        <v-card-text>
          <v-autocomplete v-model="selectedVariantToAdd" :items="availableVariantsForTemplate" item-text="item_name"
            item-value="item_code" outlined dense :placeholder="__('اختر variant')" return-object></v-autocomplete>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="showAddVariantDialog = false">{{
            __("إلغاء")
            }}</v-btn>
          <v-btn color="primary" @click="confirmAddVariant" :disabled="!selectedVariantToAdd">{{ __("إضافة") }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Product Bundle Dialog -->
    <v-dialog v-model="showBundleDialog" max-width="500px">
      <v-card>
        <v-card-title class="orange white--text">
          <v-icon right color="white">mdi-package-variant</v-icon>
          {{ __("Product Bundle") }} - {{ currentBundleItem }}
        </v-card-title>
        <v-card-text class="pa-4">
          <div class="text-subtitle-2 grey--text mb-3">
            {{ __("المكونات التي ستُخصم من المخزون:") }}
          </div>
          <v-simple-table dense>
            <template v-slot:default>
              <thead>
                <tr>
                  <th>{{ __("الصنف") }}</th>
                  <th class="text-center">{{ __("الكمية") }}</th>
                  <th>{{ __("الوحدة") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in currentBundleItems" :key="index">
                  <td>
                    <v-icon small color="orange" class="me-1">mdi-minus-circle</v-icon>
                    {{ item.item_name || item.item_code }}
                  </td>
                  <td class="text-center">{{ item.qty }}</td>
                  <td>{{ item.uom }}</td>
                </tr>
              </tbody>
            </template>
          </v-simple-table>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="showBundleDialog = false">{{
            __("إغلاق")
            }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.message }}
    </v-snackbar>
  </v-container>
</template>

<script>
export default {
  name: "NewProductEditor",

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
      hasVariants: false,

      product: {
        item_code: null,
        item_name: "",
        item_group: "",
        standard_rate: 0,
        image: "",
        product_type: "standard",
        custom_is_pos_item: true,
        custom_fast_sell: false,
        attributes: [],
        variants: [],
        sections: [],
        addons: [],
        addons_label: "",
        packaging_delivery: [],
        packaging_dinein: [],
        packaging_takeaway: [],
      },

      packagingItems: [],
      showAddAddonDialog: false,
      addonSearchQuery: "",
      addonSearchResults: [],
      selectedAddon: null,
      addonPrice: 0,
      searchingAddons: false,

      sectionTypes: [
        { value: "Component", label: "مكون" },
        { value: "Attribute", label: "خاصية (Size/Type)" },
        { value: "Package", label: "باقة" },
        { value: "Add-On", label: "إضافة" },
      ],

      categories: [],
      availableItems: [],
      availableAttributes: [],

      // Store custom product code for reuse across variants
      customProductCode: null,

      showAddAttributeDialog: false,
      newAttribute: {
        name: "",
        values: "",
      },

      showRecipeDialog: false,
      savingRecipe: false,
      currentRecipeItem: null,
      recipe: {
        bundle_name: null,
        ingredients: [],
      },
      rawMaterials: [],
      uoms: [],

      showAddVariantDialog: false,
      currentTemplateOption: null,
      selectedVariantToAdd: null,
      availableVariantsForTemplate: [],

      sectionStates: [
        {
          value: "Minimum 1 Item is Required In Section",
          label: this.__("مطلوب"),
        },
        { value: "Optional", label: this.__("اختياري") },
      ],

      snackbar: {
        show: false,
        message: "",
        color: "success",
      },

      // Product Bundle display
      optionBundles: {},
      showBundleDialog: false,
      currentBundleItem: null,
      currentBundleItems: [],

      // Price Lists
      priceLists: [],
      itemPrices: [], // { price_list: '', price: 0 }
    };
  },

  computed: {
    productTypeLabel() {
      if (this.product.product_type === "combo") {
        return this.__("وجبة كومبو");
      }
      if (this.hasVariants) {
        return this.__("وجبة عادية مع أحجام/أنواع");
      }
      return this.__("وجبة عادية");
    },

    canSave() {
      return !!(
        (this.product.item_name || this.product.custom_item_name_arabic) &&
        this.product.item_group
      );
    },

    availableAttributeNames() {
      return this.availableAttributes.map((a) => a.name);
    },

    expectedVariantsCount() {
      if (this.product.attributes.length === 0) return 0;
      return this.product.attributes.reduce(
        (total, attr) => total * attr.values.length,
        1,
      );
    },

    groupedVariants() {
      if (
        this.product.attributes.length < 2 ||
        this.product.variants.length === 0
      ) {
        return {};
      }

      // Group by first attribute value
      const groups = {};
      const firstAttr = this.product.attributes[0].attribute;

      this.product.variants.forEach((variant) => {
        // Find the first attribute value in the variant
        let groupKey = "";
        if (variant.attributes && variant.attributes.length > 0) {
          const firstAttrObj = variant.attributes.find(
            (a) => a.attribute === firstAttr,
          );
          groupKey = firstAttrObj
            ? firstAttrObj.value
            : variant.name.split(" - ")[0];
        } else {
          // Fallback: extract from name
          groupKey = variant.name.split(" - ")[0];
        }

        if (!groups[groupKey]) {
          groups[groupKey] = [];
        }
        groups[groupKey].push(variant);
      });

      return groups;
    },
  },

  methods: {
    __(text) {
      return __(text);
    },

    isStandardItem(option) {
      // Check if item_name ends with 'Standard'
      const name = option.item_name || option.item_code || '';
      return name.trim().endsWith('Standard');
    },
    applyGlobalPriceToVariants(option) {
      if (option.variants && option.global_price !== undefined) {
        option.variants.forEach((variant) => {
          variant.extra_price = option.global_price;
        });
      }
    },
    goBack() {
      this.$emit("back");
    },

    showMessage(message, color = "success") {
      this.snackbar = { show: true, message, color };
    },

    // Price List Methods
    addPriceRow() {
      this.itemPrices.push({ price_list: "", price: 0 });
    },

    removePriceRow(idx) {
      this.itemPrices.splice(idx, 1);
    },

    async fetchPriceLists() {
      try {
        const res = await frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Price List",
            fields: ["name"],
            filters: { enabled: 1, selling: 1 },
            limit_page_length: 0,
          },
        });
        this.priceLists = res.message || [];
      } catch (e) {
        console.error("Error fetching price lists:", e);
      }
    },

    async loadItemPrices(itemCode) {
      try {
        const res = await frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Item Price",
            fields: ["name", "price_list", "price_list_rate"],
            filters: { item_code: itemCode, selling: 1 },
            limit_page_length: 0,
          },
        });
        this.itemPrices = (res.message || []).map((p) => ({
          name: p.name,
          price_list: p.price_list,
          price: p.price_list_rate,
        }));
      } catch (e) {
        console.error("Error loading item prices:", e);
      }
    },

    async saveVariantItemPrices(variantCode, variantPrice) {
      let priceEntries = this.itemPrices.filter((p) => p.price_list);
      // If no price list rows, auto-use default selling price list
      if (priceEntries.length === 0 && this.priceLists.length > 0) {
        priceEntries = [{ price_list: this.priceLists[0].name }];
      }
      for (const priceItem of priceEntries) {
        // Check if an Item Price already exists for this variant + price list
        const existing = await frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Item Price",
            filters: { item_code: variantCode, price_list: priceItem.price_list, selling: 1 },
            fields: ["name"],
            limit_page_length: 1,
          },
        });
        if (existing.message && existing.message.length > 0) {
          await frappe.call({
            method: "frappe.client.set_value",
            args: {
              doctype: "Item Price",
              name: existing.message[0].name,
              fieldname: { price_list_rate: variantPrice },
            },
          });
        } else {
          await frappe.call({
            method: "frappe.client.insert",
            args: {
              doc: {
                doctype: "Item Price",
                item_code: variantCode,
                price_list: priceItem.price_list,
                price_list_rate: variantPrice,
                selling: 1,
              },
            },
          });
        }
      }
    },

    async saveItemPrices(itemCode) {
      for (const priceItem of this.itemPrices) {
        if (!priceItem.price_list) continue;

        if (priceItem.name) {
          // Update existing
          await frappe.call({
            method: "frappe.client.set_value",
            args: {
              doctype: "Item Price",
              name: priceItem.name,
              fieldname: { price_list_rate: priceItem.price },
            },
          });
        } else {
          // Create new
          await frappe.call({
            method: "frappe.client.insert",
            args: {
              doc: {
                doctype: "Item Price",
                item_code: itemCode,
                price_list: priceItem.price_list,
                price_list_rate: priceItem.price,
                selling: 1,
              },
            },
          });
        }
      }
    },

    // Attribute Methods
    onAttributeNameSelect(name) {
      const attr = this.availableAttributes.find((a) => a.name === name);
      if (attr && attr.values) {
        this.newAttribute.values = attr.values
          .map((v) => v.value || v.attribute_value)
          .join(", ");
      }
    },

    addAttribute() {
      if (!this.newAttribute.name || !this.newAttribute.values) {
        this.showMessage(this.__("أدخل اسم الخاصية والقيم"), "warning");
        return;
      }

      const values = this.newAttribute.values
        .split(",")
        .map((v) => v.trim())
        .filter((v) => v);

      this.product.attributes.push({
        attribute: this.newAttribute.name,
        values: values,
      });

      this.newAttribute = { name: "", values: "" };
      this.showAddAttributeDialog = false;
    },

    removeAttribute(attr) {
      const index = this.product.attributes.indexOf(attr);
      if (index > -1) {
        this.product.attributes.splice(index, 1);
        this.product.variants = [];
      }
    },

    // Addon methods
    async searchAddons(query) {
      if (!query || query.length < 2) return;

      this.searchingAddons = true;
      try {
        const res = await frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Item",
            fields: ["item_code", "item_name", "standard_rate"],
            filters: {
              item_name: ["like", `%${query}%`],
              disabled: 0,
            },
            limit_page_length: 20,
          },
        });
        this.availableItems = res.message || [];
      } catch (e) {
        console.error("Search addons error:", e);
      }
      this.searchingAddons = false;
    },

    addAddon() {
      if (!this.selectedAddon) return;

      // Check if already added
      if (
        this.product.addons.find(
          (a) => a.item_code === this.selectedAddon.item_code,
        )
      ) {
        this.showMessage(this.__("هذا الصنف مضاف مسبقاً"), "warning");
        return;
      }

      this.product.addons.push({
        item_code: this.selectedAddon.item_code,
        item_name: this.selectedAddon.item_name,
        price: this.addonPrice || 0,
      });

      this.selectedAddon = null;
      this.addonPrice = 0;
      this.showAddAddonDialog = false;
    },

    removeAddon(index) {
      this.product.addons.splice(index, 1);
    },

    getAttributeValues(attributeName) {
      const attr = this.product.attributes.find(
        (a) => a.attribute === attributeName,
      );
      return attr ? attr.values : [];
    },

    generateAllVariants() {
      if (this.product.attributes.length === 0) return;

      const combinations = this.cartesianProduct(
        this.product.attributes.map((a) => a.values),
      );

      this.product.variants = combinations.map((combo) => {
        const attrs = this.product.attributes.map((a, i) => ({
          attribute: a.attribute,
          value: combo[i],
        }));

        return {
          name: combo.join(" - "),
          attributes: attrs,
          price: this.product.standard_rate || 0,
        };
      });
    },

    cartesianProduct(arrays) {
      return arrays.reduce(
        (acc, curr) => {
          const result = [];
          acc.forEach((a) => {
            curr.forEach((b) => {
              result.push([...a, b]);
            });
          });
          return result;
        },
        [[]],
      );
    },

    removeVariant(index) {
      this.product.variants.splice(index, 1);
    },

    removeVariantByName(name) {
      const index = this.product.variants.findIndex((v) => v.name === name);
      if (index > -1) {
        this.product.variants.splice(index, 1);
      }
    },

    addManualVariant() {
      this.product.variants.push({
        name: "",
        price: 0,
        item_code: null,
        isExisting: false,
        attributes: [],
      });
    },

    // Section/Option Methods
    addSection() {
      this.product.sections.push({
        name: "",
        section_type: "Component",
        is_required: false,
        min_qty: 0,
        max_qty: 1,
        options: [],
      });
    },

    removeSection(index) {
      this.product.sections.splice(index, 1);
    },

    addOption(section) {
      section.options.push({
        item_code: "",
        extra_price: 0,
        default_selected: false,
        qty: 1,
        expanded: false,
      });
    },

    toggleOptionExpanded(option) {
      const currentState = option.expanded === true;
      this.$set(option, "expanded", !currentState);
    },

    removeOption(section, index) {
      section.options.splice(index, 1);
    },

    async onOptionSelect(option, section) {
      const item = this.availableItems.find(
        (i) => i.item_code === option.item_code,
      );
      if (item) {
        option.item_name = item.item_name;

        // If template item selected (not a variant itself), load its variants as nested
        if (item.has_variants && !item.variant_of) {
          this.$set(option, "has_variants", true);
          this.$set(option, "expanded", true);
          const variantsRes = await frappe.call({
            method: "frappe.client.get_list",
            args: {
              doctype: "Item",
              fields: ["item_code", "item_name", "standard_rate"],
              filters: { variant_of: item.item_code, disabled: 0 },
              limit_page_length: 0,
            },
          });

          const variants = variantsRes.message || [];
          option.variants = variants.map((v) => ({
            item_code: v.item_code,
            item_name: v.item_name,
            extra_price: 0,
            default_selected: false,
            qty: 1,
          }));
        } else {
          option.has_variants = false;
          option.variants = null;
        }
      }
    },

    removeNestedVariant(option, index) {
      option.variants.splice(index, 1);
      if (option.variants.length === 0) {
        option.has_variants = false;
      }
    },

    async openAddVariantDialog(option) {
      this.currentTemplateOption = option;
      this.selectedVariantToAdd = null;

      // Load all variants for this template
      const res = await frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "Item",
          filters: { variant_of: option.item_code },
          fields: ["item_code", "item_name"],
          limit_page_length: 0,
        },
      });

      // Filter out already added variants
      const existingCodes = (option.variants || []).map((v) => v.item_code);
      this.availableVariantsForTemplate = (res.message || []).filter(
        (v) => !existingCodes.includes(v.item_code),
      );

      this.showAddVariantDialog = true;
    },

    confirmAddVariant() {
      if (!this.selectedVariantToAdd || !this.currentTemplateOption) return;

      if (!this.currentTemplateOption.variants) {
        this.currentTemplateOption.variants = [];
      }

      this.currentTemplateOption.variants.push({
        item_code: this.selectedVariantToAdd.item_code,
        item_name: this.selectedVariantToAdd.item_name,
        extra_price: 0,
        default_selected: false,
        qty: 1,
      });

      this.showAddVariantDialog = false;
      this.selectedVariantToAdd = null;
    },

    async openRecipeDialog(variant = null) {
      this.currentRecipeItem = variant
        ? variant.item_code
        : this.product.item_code;
      await Promise.all([
        this.loadRawMaterials(),
        this.loadUOMs(),
        this.loadExistingBundle(),
      ]);
      this.showRecipeDialog = true;
    },

    async loadRawMaterials() {
      const res = await frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "Item",
          fields: ["item_code", "item_name", "stock_uom"],
          filters: { is_stock_item: 1, disabled: 0 },
          limit_page_length: 0,
        },
      });
      this.rawMaterials = res.message || [];
    },

    async loadUOMs() {
      const res = await frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "UOM",
          fields: ["name"],
          limit_page_length: 0,
        },
      });
      this.uoms = res.message || [];
    },

    async loadExistingBundle() {
      const res = await frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "Product Bundle",
          filters: { new_item_code: this.currentRecipeItem },
          fields: ["name"],
          limit_page_length: 1,
        },
      });

      if (res.message && res.message.length > 0) {
        this.recipe.bundle_name = res.message[0].name;
        const bundle = await frappe.call({
          method: "frappe.client.get",
          args: { doctype: "Product Bundle", name: this.recipe.bundle_name },
        });

        if (bundle.message && bundle.message.items) {
          this.recipe.ingredients = bundle.message.items.map((item) => ({
            item_code: item.item_code,
            item_name: item.description || item.item_code,
            qty: item.qty,
            uom: item.uom || "Unit",
            show_in_pos: item.show_in_pos !== 0,
          }));
        }
      } else {
        this.recipe.bundle_name = null;
        this.recipe.ingredients = [];
      }
    },

    addIngredient() {
      this.recipe.ingredients.push({
        item_code: "",
        item_name: "",
        qty: 1,
        uom: "Unit",
        show_in_pos: true,
      });
    },

    removeIngredient(index) {
      this.recipe.ingredients.splice(index, 1);
    },

    onIngredientSelect(ingredient) {
      const item = this.rawMaterials.find(
        (i) => i.item_code === ingredient.item_code,
      );
      if (item) {
        ingredient.item_name = item.item_name;
        ingredient.uom = item.stock_uom || "Unit";
      }
    },

    // Product Bundle Methods
    async toggleOptionBundle(item) {
      if (!item.item_code) return;

      const itemCode = item.item_code;

      // Toggle visibility
      if (this.optionBundles[itemCode]) {
        this.$set(this.optionBundles, itemCode, null);
        return;
      }

      // Load Product Bundle
      try {
        const res = await frappe.call({
          method:
            "ecs_posnext.ecs_posnext.custom_api.item_manager.get_product_bundle",
          args: { item_code: itemCode },
        });

        if (res.message && res.message.items && res.message.items.length > 0) {
          this.$set(this.optionBundles, itemCode, res.message.items);
          this.currentBundleItem = item.item_name || itemCode;
          this.currentBundleItems = res.message.items;
          this.showBundleDialog = true;
        } else {
          this.showMessage(
            this.__("لا يوجد Product Bundle لهذا الصنف"),
            "warning",
          );
        }
      } catch (e) {
        console.error("Error loading Product Bundle:", e);
        this.showMessage(this.__("خطأ في تحميل Product Bundle"), "error");
      }
    },

    async saveRecipe() {
      if (this.recipe.ingredients.length === 0) {
        this.showMessage(this.__("أضف مكون واحد على الأقل"), "error");
        return;
      }

      this.savingRecipe = true;
      try {
        // Delete existing bundle if any
        if (this.recipe.bundle_name) {
          await frappe.call({
            method: "frappe.client.delete",
            args: { doctype: "Product Bundle", name: this.recipe.bundle_name },
          });
        }

        // Create new Product Bundle
        const bundleData = {
          doctype: "Product Bundle",
          new_item_code: this.currentRecipeItem,
          items: this.recipe.ingredients.map((ing) => ({
            item_code: ing.item_code,
            qty: ing.qty,
            uom: ing.uom,
            description: ing.item_name,
            show_in_pos: ing.show_in_pos ? 1 : 0,
          })),
        };

        const res = await frappe.call({
          method: "frappe.client.insert",
          args: { doc: bundleData },
        });

        this.recipe.bundle_name = res.message.name;
        this.showMessage(this.__("تم حفظ المكونات بنجاح"));
        this.showRecipeDialog = false;
      } catch (e) {
        console.error("Recipe save error:", e);
        this.showMessage(e.message || this.__("خطأ في حفظ المكونات"), "error");
      }
      this.savingRecipe = false;
    },

    // Data Loading
    async loadData() {
      this.loading = true;
      try {
        await Promise.all([
          this.loadCategories(),
          this.loadAvailableItems(),
          this.loadAvailableAttributes(),
          this.loadPackagingItems(),
        ]);

        if (this.itemId && this.itemId !== "new") {
          await this.loadProduct();
        }
      } catch (e) {
        console.error(e);
        this.showMessage(this.__("خطأ في تحميل البيانات"), "error");
      }
      this.loading = false;
    },

    async loadCategories() {
      const res = await frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "Item Group",
          fields: ["name", "custom_item_group_code"],
          limit_page_length: 0,
        },
      });
      this.categories = res.message || [];
    },

    async loadAvailableItems() {
      const res = await frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "Item",
          fields: ["item_code", "item_name", "standard_rate", "has_variants", "variant_of"],
          filters: { disabled: 0 },
          limit_page_length: 0,
        },
      });
      this.availableItems = res.message || [];
    },

    async loadAvailableAttributes() {
      const res = await frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "Item Attribute",
          fields: ["name"],
          limit_page_length: 0,
        },
      });

      const attrs = res.message || [];
      for (const attr of attrs) {
        const valRes = await frappe.call({
          method: "frappe.client.get",
          args: {
            doctype: "Item Attribute",
            name: attr.name,
          },
        });
        if (valRes.message) {
          attr.values = valRes.message.item_attribute_values || [];
        }
      }
      this.availableAttributes = attrs;
    },

    async loadPackagingItems() {
      const res = await frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "Item",
          fields: ["item_code", "item_name"],
          filters: {
            disabled: 0,
            is_stock_item: 1,
          },
          limit_page_length: 0,
        },
      });
      this.packagingItems = res.message || [];
    },

    addPackaging(type) {
      const pkg = { item_code: "", qty: 1, uom: "Unit" };
      if (type === "delivery") {
        this.product.packaging_delivery.push(pkg);
      } else if (type === "dinein") {
        this.product.packaging_dinein.push(pkg);
      } else if (type === "takeaway") {
        this.product.packaging_takeaway.push(pkg);
      }
    },

    async loadProduct() {
      this.isEditing = true;
      const res = await frappe.call({
        method: "frappe.client.get",
        args: {
          doctype: "Item",
          name: this.itemId,
        },
      });

      if (res.message) {
        const item = res.message;
        this.product.item_code = item.item_code;
        this.product.item_name = item.item_name;
        this.product.custom_item_name_arabic = item.custom_item_name_arabic;
        this.product.item_group = item.item_group;
        this.product.standard_rate = item.standard_rate || 0;
        this.product.image = item.image || "";
        this.product.custom_is_pos_item = item.custom_is_pos_item;
        this.product.custom_fast_sell = item.custom_fast_sell;
        this.product.product_type = item.enabled_item_bundle
          ? "combo"
          : "standard";
        this.hasVariants = item.has_variants === 1;

        // Load packaging data
        this.product.packaging_delivery = (item.packaging_delivery || []).map(
          (p) => ({
            item_code: p.item_code,
            qty: p.qty || 1,
            uom: p.uom || "Unit",
          }),
        );
        this.product.packaging_dinein = (item.packaging_dinein || []).map(
          (p) => ({
            item_code: p.item_code,
            qty: p.qty || 1,
            uom: p.uom || "Unit",
          }),
        );
        this.product.packaging_takeaway = (item.packaging_takeaway || []).map(
          (p) => ({
            item_code: p.item_code,
            qty: p.qty || 1,
            uom: p.uom || "Unit",
          }),
        );

        // Load addons
        this.product.addons = (item.custom_addons || []).map((a) => ({
          item_code: a.item_code,
          item_name: a.item_name,
          price: a.price || 0,
          applicable_attribute: a.applicable_attribute || "",
          applicable_value: a.applicable_value || "",
        }));
        this.product.addons_label = item.custom_addons_label || "";

        if (item.enabled_item_bundle && item.combo_components) {
          await this.loadComboSections(item.combo_components);
        }

        if (item.has_variants) {
          await this.loadAttributes();
          await this.loadVariants();
          // Load item prices from first variant (templates can't have Item Prices)
          if (this.product.variants.length > 0 && this.product.variants[0].item_code) {
            await this.loadItemPrices(this.product.variants[0].item_code);
          }
        } else {
          // Load item prices
          await this.loadItemPrices(item.item_code);
        }
      }
    },

    async loadComboSections(components) {
      // Get item details to check for variants
      const itemCodes = components.map((c) => c.item_code);
      const itemsRes = await frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "Item",
          fields: ["item_code", "item_name", "variant_of"],
          filters: { item_code: ["in", itemCodes] },
          limit_page_length: 0,
        },
      });

      const itemsMap = {};
      (itemsRes.message || []).forEach((item) => {
        itemsMap[item.item_code] = item;
      });

      const sectionsMap = {};
      const templateGroups = {}; // Group variants by template

      components.forEach((comp) => {
        const sectionName = comp.section_name || "Default";
        if (!sectionsMap[sectionName]) {
          sectionsMap[sectionName] = {
            name: sectionName,
            section_type: comp.section_type || "Component",
            is_required: comp.is_required === 1,
            min_qty: comp.min_qty || 0,
            max_qty: comp.max_qty || 1,
            options: [],
          };
        }

        const itemInfo = itemsMap[comp.item_code] || {};
        const templateCode = itemInfo.variant_of;
        const isStandalone = comp.is_standalone === 1;

        if (templateCode && !isStandalone) {
          // This is a variant from template - group it
          const key = `${sectionName}__${templateCode}`;
          if (!templateGroups[key]) {
            templateGroups[key] = {
              sectionName,
              templateCode,
              variants: [],
              // Store min/max from first variant
              min_qty: comp.min_qty || 0,
              max_qty: comp.max_qty || 1,
            };
          }
          templateGroups[key].variants.push({
            item_code: comp.item_code,
            item_name: itemInfo.item_name || comp.item_code,
            extra_price: comp.extra_price || 0,
            default_selected: comp.default_selected === 1,
            qty: comp.qty || 1,
            show_bundle_in_pos: comp.show_bundle_in_pos === 1,
          });
        } else {
          // Regular item or standalone variant
          sectionsMap[sectionName].options.push({
            item_code: comp.item_code,
            item_name: itemInfo.item_name || comp.item_code,
            extra_price: comp.extra_price || 0,
            default_selected: comp.default_selected === 1,
            qty: comp.qty || 1,
            has_variants: false,
            show_bundle_in_pos: comp.show_bundle_in_pos === 1,
          });
        }
      });

      // Add grouped variants as nested options
      for (const key in templateGroups) {
        const group = templateGroups[key];
        const template = this.availableItems.find(
          (i) => i.item_code === group.templateCode,
        );
        sectionsMap[group.sectionName].options.push({
          item_code: group.templateCode,
          item_name: template ? template.item_name : group.templateCode,
          has_variants: true,
          expanded: true,
          variants: group.variants,
          // Include min/max from group (for Standard templates)
          min_qty: group.min_qty,
          max_qty: group.max_qty,
        });
      }

      this.product.sections = Object.values(sectionsMap);
    },

    async loadAttributes() {
      // Load attributes from existing variants
      try {
        // Get all variants of this item
        const variantsRes = await frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Item",
            fields: ["item_code", "item_name"],
            filters: { variant_of: this.product.item_code },
            limit_page_length: 0,
          },
        });

        const variants = variantsRes.message || [];
        if (variants.length === 0) {
          this.product.attributes = [];
          return;
        }

        // Get attributes from each variant
        const attrMap = {};
        for (const variant of variants) {
          const variantDoc = await frappe.call({
            method: "frappe.client.get",
            args: {
              doctype: "Item",
              name: variant.item_code,
            },
          });

          if (variantDoc.message && variantDoc.message.attributes) {
            variantDoc.message.attributes.forEach((attr) => {
              if (!attrMap[attr.attribute]) {
                attrMap[attr.attribute] = {
                  attribute: attr.attribute,
                  values: [],
                };
              }
              if (
                attr.attribute_value &&
                !attrMap[attr.attribute].values.includes(attr.attribute_value)
              ) {
                attrMap[attr.attribute].values.push(attr.attribute_value);
              }
            });
          }
        }

        this.product.attributes = Object.values(attrMap);
      } catch (e) {
        console.error("Error loading attributes:", e);
        this.product.attributes = [];
      }
    },

    async loadVariants() {
      const res = await frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "Item",
          fields: [
            "item_code",
            "item_name",
            "standard_rate",
            "custom_show_bundle_in_pos",
          ],
          filters: { variant_of: this.product.item_code },
          limit_page_length: 0,
        },
      });

      this.product.variants = (res.message || []).map((v) => ({
        item_code: v.item_code,
        name: v.item_name.replace(this.product.item_name + " - ", ""),
        price: v.standard_rate || 0,
        show_bundle: v.custom_show_bundle_in_pos === 1,
        isExisting: true,
      }));
    },

    // Save
    async saveProduct() {
      if (!this.product.item_name || !this.product.item_group) {
        this.showMessage(this.__("يجب إدخال اسم الصنف والفئة"), "error");
        return;
      }

      this.saving = true;
      try {
        // Reset custom product code for new save operation
        this.customProductCode = null;

        let savedItemCode = this.product.item_code;

        if (this.product.product_type === "standard") {
          if (this.hasVariants) {
            await this.saveStandardWithVariants();
          } else {
            await this.saveSimpleItem();
          }
        } else {
          await this.saveComboItem();
        }

        // Save item prices
        if (this.hasVariants) {
          // For template items, save item prices per variant
          for (const variant of this.product.variants) {
            if (variant.item_code) {
              await this.saveVariantItemPrices(variant.item_code, variant.price);
            }
          }
        } else {
          const itemCode =
            this.product.item_code ||
            this.generateItemCode(this.product.item_name);
          await this.saveItemPrices(itemCode);
        }

        this.showMessage(this.__("تم الحفظ بنجاح"));
        this.goBack();
      } catch (e) {
        console.error("Save error:", e);
        this.showMessage(e.message || this.__("خطأ في الحفظ"), "error");
      }
      this.saving = false;
    },


    /**
     * Checks if an item code already exists in the system
     * @param {string} itemCode - The item code to check
     * @returns {Promise<boolean>} True if exists, false otherwise
     */
    async checkItemCodeExists(itemCode) {
      try {
        const res = await frappe.call({
          method: "frappe.client.get_value",
          args: {
            doctype: "Item",
            filters: { item_code: itemCode },
            fieldname: "name",
          },
        });
        // frappe.client.get_value returns res.message as object {name: "value"} if found, null if not found
        return res.message && res.message.name ? true : false;
      } catch (e) {
        // If error occurs (e.g., item not found), return false
        return false;
      }
    },







    async saveSimpleItem() {
      const itemCode = this.product.item_code;
      if (!itemCode) {
        throw new Error(this.__("يجب إدخال كود الصنف"));
      }

      // Check if item code already exists (only for new items)
      if (!this.isEditing) {
        const exists = await this.checkItemCodeExists(itemCode);
        if (exists) {
          throw new Error(this.__("كود الصنف موجود بالفعل"));
        }
      }
      const addonsData = this.product.addons
        .filter((a) => a.item_code)
        .map((a) => ({
          item_code: a.item_code,
          item_name: a.item_name,
          price: a.price || 0,
          applicable_attribute: a.applicable_attribute || "",
          applicable_value: a.applicable_value || "",
        }));

      const doc = {
        doctype: "Item",
        item_code: itemCode,
        item_name: this.product.item_name,
        custom_item_name_arabic: this.product.custom_item_name_arabic,
        item_group: this.product.item_group,
        standard_rate: this.product.standard_rate,
        image: this.product.image,
        custom_is_pos_item: this.product.custom_is_pos_item,
        custom_fast_sell: this.product.custom_fast_sell,
        is_stock_item: 0,
        include_item_in_manufacturing: 0,
        packaging_delivery: this.product.packaging_delivery.filter(
          (p) => p.item_code,
        ),
        packaging_dinein: this.product.packaging_dinein.filter(
          (p) => p.item_code,
        ),
        packaging_takeaway: this.product.packaging_takeaway.filter(
          (p) => p.item_code,
        ),
        custom_addons: addonsData,
        custom_addons_label: this.product.addons_label || "",
      };

      if (this.isEditing) {
        await frappe.call({
          method: "frappe.client.set_value",
          args: {
            doctype: "Item",
            name: this.product.item_code,
            fieldname: doc,
          },
        });
      } else {
        await frappe.call({
          method: "frappe.client.insert",
          args: { doc },
        });
      }
    },

    async saveStandardWithVariants() {
      if (!this.isEditing) {
        const templateCode = this.product.item_code;
        if (!templateCode) {
          throw new Error(this.__("يجب إدخال كود الصنف"));
        }

        const pendingVariantCodes = this.product.variants
          .filter((variant) => variant.name && !variant.isExisting)
          .map((variant) => variant.item_code);

        if (pendingVariantCodes.some((code) => !code)) {
          throw new Error(this.__("يجب إدخال كود الصنف لجميع المتغيرات"));
        }

        const allCodes = [templateCode, ...pendingVariantCodes];
        const duplicateCodes = allCodes.filter(
          (code, index) => allCodes.indexOf(code) !== index,
        );

        if (duplicateCodes.length > 0) {
          throw new Error(
            this.__("يوجد تكرار في أكواد الأصناف: ") +
            [...new Set(duplicateCodes)].join(", "),
          );
        }

        const existingChecks = await Promise.all(
          allCodes.map(async (code) => ({
            code,
            exists: await this.checkItemCodeExists(code),
          })),
        );

        const existingCodes = existingChecks
          .filter((check) => check.exists)
          .map((check) => check.code);

        if (existingCodes.length > 0) {
          throw new Error(
            this.__("كود الصنف موجود بالفعل: ") + existingCodes.join(", "),
          );
        }
      }

      // If no attributes defined, create a default "Type" attribute
      if (this.product.attributes.length === 0) {
        const variantNames = this.product.variants
          .map((v) => v.name)
          .filter((n) => n);
        if (variantNames.length > 0) {
          this.product.attributes.push({
            attribute: "Type",
            values: variantNames,
          });
          // Assign attributes to variants
          this.product.variants.forEach((v) => {
            v.attributes = [{ attribute: "Type", value: v.name }];
          });
        }
      }

      // Ensure attributes exist in Item Attribute table
      for (const attr of this.product.attributes) {
        await this.ensureAttributeExists(attr.attribute, attr.values);
      }

      // Prepare addons data
      const addonsData = this.product.addons
        .filter((a) => a.item_code)
        .map((a) => ({
          item_code: a.item_code,
          item_name: a.item_name,
          price: a.price || 0,
          applicable_attribute: a.applicable_attribute || "",
          applicable_value: a.applicable_value || "",
        }));

      if (!this.isEditing) {
        // Create template item
        const templateCode = this.product.item_code;
        const templateDoc = {
          doctype: "Item",
          item_code: templateCode,
          item_name: this.product.item_name,
          custom_item_name_arabic: this.product.custom_item_name_arabic,
          item_group: this.product.item_group,
          image: this.product.image,
          custom_is_pos_item: this.product.custom_is_pos_item,
          custom_fast_sell: this.product.custom_fast_sell,
          has_variants: 1,
          is_stock_item: 0,
          stock_uom: "Unit",
          include_item_in_manufacturing: 0,
          attributes: this.product.attributes.map((a) => ({
            attribute: a.attribute,
          })),
          custom_addons: addonsData,
          custom_addons_label: this.product.addons_label || "",
        };

        const res = await frappe.call({
          method: "frappe.client.insert",
          args: { doc: templateDoc },
        });

        this.product.item_code = res.message.item_code;
      } else {
        // Update template item attributes and addons
        await frappe.call({
          method: "frappe.client.set_value",
          args: {
            doctype: "Item",
            name: this.product.item_code,
            fieldname: {
              attributes: this.product.attributes.map((a) => ({
                attribute: a.attribute,
              })),
              custom_addons: addonsData,
              custom_addons_label: this.product.addons_label || "",
            },
          },
        });
      }

      // Create/update variants
      for (const variant of this.product.variants) {
        if (!variant.name) continue; // Skip empty variants

        if (variant.isExisting) {
          // Update price and show_bundle_in_pos
          await frappe.call({
            method: "frappe.client.set_value",
            args: {
              doctype: "Item",
              name: variant.item_code,
              fieldname: {
                standard_rate: variant.price,
                custom_show_bundle_in_pos: variant.show_bundle ? 1 : 0,
              },
            },
          });
        } else {
          // Ensure variant has attributes
          if (!variant.attributes || variant.attributes.length === 0) {
            variant.attributes = [{ attribute: "Type", value: variant.name }];
          }

          // Create new variant with manual item code
          const variantCode = variant.item_code;
          if (!variantCode) {
            throw new Error(this.__("يجب إدخال كود الصنف لجميع المتغيرات"));
          }

          // Check if variant code already exists
          const variantExists = await this.checkItemCodeExists(variantCode);
          if (variantExists) {
            throw new Error(this.__("كود الصنف موجود بالفعل: ") + variantCode);
          }
          const variantDoc = {
            doctype: "Item",
            item_code: variantCode,
            item_name: `${this.product.item_name} - ${variant.name}`,
            custom_item_name_arabic: `${this.product.custom_item_name_arabic} - ${variant.name}`,
            item_group: this.product.item_group,
            variant_of: this.product.item_code,
            standard_rate: variant.price,
            custom_show_bundle_in_pos: variant.show_bundle ? 1 : 0,
            is_stock_item: 0,
            stock_uom: "Unit",
            attributes: variant.attributes.map((a) => ({
              attribute: a.attribute,
              attribute_value: a.value,
            })),
          };

          const res = await frappe.call({
            method: "frappe.client.insert",
            args: { doc: variantDoc },
          });

          // Store the created item_code
          variant.item_code = res.message.item_code;
          variant.isExisting = true;
        }
      }
    },

    async ensureAttributeExists(attrName, values) {
      const exists = await frappe.db.exists("Item Attribute", attrName);

      if (!exists) {
        await frappe.call({
          method: "frappe.client.insert",
          args: {
            doc: {
              doctype: "Item Attribute",
              attribute_name: attrName,
              item_attribute_values: values.map((v) => ({
                attribute_value: v,
                abbr: v.substring(0, 3).toUpperCase(),
              })),
            },
          },
        });
      } else {
        // Attribute exists, ensure all values exist
        const attrDoc = await frappe.call({
          method: "frappe.client.get",
          args: { doctype: "Item Attribute", name: attrName },
        });

        const existingValues = (
          attrDoc.message.item_attribute_values || []
        ).map((v) => v.attribute_value);
        const newValues = values.filter((v) => !existingValues.includes(v));

        if (newValues.length > 0) {
          const doc = attrDoc.message;
          for (const val of newValues) {
            doc.item_attribute_values.push({
              attribute_value: val,
              abbr: val.substring(0, 3).toUpperCase(),
            });
          }
          await frappe.call({
            method: "frappe.client.save",
            args: { doc },
          });
        }
      }
    },

    async saveComboItem() {
      const components = [];
      for (const section of this.product.sections) {
        for (const option of section.options) {
          // Handle nested variants (from template)
          if (option.has_variants && option.variants) {
            for (const variant of option.variants) {
              if (variant.item_code) {
                components.push({
                  section_name: section.name,
                  section_type: section.section_type || "Component",
                  is_required: section.is_required ? 1 : 0,
                  item_code: variant.item_code,
                  // Use option-level min/max for Standard templates, otherwise section-level
                  min_qty: option.min_qty !== undefined ? option.min_qty : (section.min_qty || 0),
                  max_qty: option.max_qty !== undefined ? option.max_qty : (section.max_qty || 1),
                  default_selected: variant.default_selected ? 1 : 0,
                  extra_price: variant.extra_price || 0,
                  qty: variant.qty || 1,
                  show_bundle_in_pos: variant.show_bundle_in_pos ? 1 : 0,
                  is_standalone: 0,
                });
              }
            }
          } else if (option.item_code) {
            // Regular item or standalone variant
            components.push({
              section_name: section.name,
              section_type: section.section_type || "Component",
              is_required: section.is_required ? 1 : 0,
              item_code: option.item_code,
              min_qty: section.min_qty || 0,
              max_qty: section.max_qty || 1,
              default_selected: option.default_selected ? 1 : 0,
              extra_price: option.extra_price || 0,
              qty: option.qty || 1,
              show_bundle_in_pos: option.show_bundle_in_pos ? 1 : 0,
              is_standalone: 1,
            });
          }
        }
      }

      const itemCode = this.product.item_code;
      if (!itemCode) {
        throw new Error(this.__("يجب إدخال كود الصنف"));
      }

      // Check if item code already exists (only for new items)
      if (!this.isEditing) {
        const exists = await this.checkItemCodeExists(itemCode);
        if (exists) {
          throw new Error(this.__("كود الصنف موجود بالفعل"));
        }
      }
      const doc = {
        doctype: "Item",
        item_code: itemCode,
        item_name: this.product.item_name,
        custom_item_name_arabic: this.product.custom_item_name_arabic,
        item_group: this.product.item_group,
        standard_rate: this.product.standard_rate,
        image: this.product.image,
        custom_is_pos_item: this.product.custom_is_pos_item,
        custom_fast_sell: this.product.custom_fast_sell,
        is_stock_item: 0,
        include_item_in_manufacturing: 0,
        enabled_item_bundle: 1,
        combo_components: components,
        packaging_delivery: this.product.packaging_delivery.filter(
          (p) => p.item_code,
        ),
        packaging_dinein: this.product.packaging_dinein.filter(
          (p) => p.item_code,
        ),
        packaging_takeaway: this.product.packaging_takeaway.filter(
          (p) => p.item_code,
        ),
      };

      if (this.isEditing) {
        await frappe.call({
          method: "frappe.client.set_value",
          args: {
            doctype: "Item",
            name: this.product.item_code,
            fieldname: doc,
          },
        });
      } else {
        await frappe.call({
          method: "frappe.client.insert",
          args: { doc },
        });
      }
    },
  },

  mounted() {
    this.loadData();
    this.fetchPriceLists();
  },
};
</script>

<style scoped>
/* ===== Local Theme Tokens ===== */
.new-product-editor {
  --im-bg: #f4f6fb;
  --im-card: #ffffff;
  --im-border: #e0e6f0;
  --im-border-light: #f0f2f8;
  --im-muted: #8a94a6;
  --im-primary: #17223b;
  --im-primary-light: #e8eeff;
  --im-accent: #5e60ce;
  --im-radius: 12px;
  --im-radius-sm: 8px;
  --im-radius-input: 10px;
  --im-input-bg: #f7f8fa;
  --im-input-border: #e0e6f0;
  --im-text: #2d3348;
  --im-text-secondary: #6b7280;

  min-height: 100vh;
  background: var(--im-bg);
}

/* ===== Header ===== */
.editor-header {
  background: var(--im-primary);
  padding: 18px 28px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

/* ===== Body / Panels ===== */
.editor-body {
  height: calc(100vh - 72px);
  overflow-y: auto;
}

.panel {
  background: var(--im-card);
  padding: 28px;
  border-left: 1px solid var(--im-border);
  height: calc(100vh - 72px);
  overflow-y: auto;
}

.panel--right {
  background: var(--im-bg);
  border-left: none;
}

.panel--middle {
  background: var(--im-card);
}

.panel-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--im-primary);
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--im-border);
  letter-spacing: -0.01em;
}

/* ===== Form Groups & Labels ===== */
.form-group {
  margin-bottom: 16px;
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

/* ===== Global Input Overrides (scoped) ===== */
.new-product-editor > > > .v-text-field--outlined fieldset,
.new-product-editor > > > .v-select--outlined fieldset,
.new-product-editor > > > .v-autocomplete--outlined fieldset,
.new-product-editor > > > .v-textarea--outlined fieldset,
.new-product-editor > > > .v-combobox--outlined fieldset {
  border-color: var(--im-input-border) !important;
  border-radius: var(--im-radius-input) !important;
  border-width: 1px !important;
}

.new-product-editor > > > .v-text-field--outlined .v-input__slot,
.new-product-editor > > > .v-select--outlined .v-input__slot,
.new-product-editor > > > .v-autocomplete--outlined .v-input__slot,
.new-product-editor > > > .v-textarea--outlined .v-input__slot,
.new-product-editor > > > .v-combobox--outlined .v-input__slot {
  background: var(--im-input-bg) !important;
  min-height: 40px !important;
}

.new-product-editor > > > .v-text-field--outlined.v-input--is-focused fieldset,
.new-product-editor > > > .v-select--outlined.v-input--is-focused fieldset,
.new-product-editor > > > .v-autocomplete--outlined.v-input--is-focused fieldset,
.new-product-editor > > > .v-textarea--outlined.v-input--is-focused fieldset,
.new-product-editor > > > .v-combobox--outlined.v-input--is-focused fieldset {
  border-color: var(--im-accent) !important;
  box-shadow: 0 0 0 2px rgba(94, 96, 206, 0.12) !important;
}

.new-product-editor > > > .v-input__slot input,
.new-product-editor > > > .v-input__slot textarea,
.new-product-editor > > > .v-select__selection {
  font-size: 13.5px !important;
  color: var(--im-text) !important;
}

.new-product-editor > > > .v-label {
  font-size: 13px !important;
  color: var(--im-muted) !important;
}

/* ===== Switches ===== */
.new-product-editor > > > .v-input--switch .v-input--selection-controls__input {
  transform: scale(0.85);
}

/* ===== Button Toggle (Product Type) ===== */
.new-product-editor > > > .v-btn-toggle {
  border-radius: var(--im-radius-sm) !important;
  border: 1px solid var(--im-border) !important;
  overflow: hidden;
}

.new-product-editor > > > .v-btn-toggle .v-btn {
  border: none !important;
  text-transform: none !important;
  font-weight: 500 !important;
  letter-spacing: 0 !important;
  font-size: 13px !important;
}

.new-product-editor > > > .v-btn-toggle .v-btn--active {
  background: var(--im-primary-light) !important;
  color: var(--im-primary) !important;
}

/* ===== Section Boxes ===== */
.section-box {
  background: var(--im-card);
  border-radius: var(--im-radius);
  border: 1px solid var(--im-border);
}

.section-box__header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--im-border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  font-size: 13px;
  color: var(--im-primary);
}

.section-box__body {
  padding: 14px;
}

/* ===== Variant Rows ===== */
.variant-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--im-input-bg);
  border-radius: var(--im-radius-sm);
  margin-bottom: 8px;
  border: 1px solid var(--im-border);
  transition: border-color 0.15s ease;
}

.variant-row:hover {
  border-color: var(--im-accent);
}

.variant-row__name {
  flex: 1;
  font-weight: 500;
  color: var(--im-text);
}

.variant-row__price {
  max-width: 120px;
}

.variant-row--nested {
  padding: 8px 10px;
  margin-bottom: 4px;
  background: var(--im-card);
}

/* ===== Variant Groups ===== */
.variant-group {
  background: var(--im-primary-light);
  border-radius: var(--im-radius);
  border: 1px solid #c8d0e8;
  overflow: hidden;
}

.variant-group__header {
  padding: 10px 14px;
  background: rgba(94, 96, 206, 0.06);
  border-bottom: 1px solid #c8d0e8;
  font-size: 13px;
  font-weight: 600;
  color: var(--im-primary);
}

.variant-group__items {
  padding: 8px;
}

/* ===== Addon Rows ===== */
.addon-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--im-input-bg);
  border-radius: var(--im-radius-sm);
  margin-bottom: 8px;
  border: 1px solid var(--im-border);
  transition: border-color 0.15s ease;
}

.addon-row:hover {
  border-color: var(--im-accent);
}

.addon-row__name {
  flex: 1;
  font-weight: 500;
  color: var(--im-text);
  font-size: 13px;
}

/* ===== Attribute Items ===== */
.attribute-item {
  background: var(--im-input-bg);
  padding: 10px 14px;
  border-radius: var(--im-radius-sm);
  border: 1px solid var(--im-border);
}

/* ===== Combo Sections ===== */
.combo-section {
  background: var(--im-card);
  border-radius: var(--im-radius);
  border: 1px solid var(--im-border);
  padding: 18px;
}

.combo-section__header {
  display: flex;
  align-items: center;
  margin-bottom: 14px;
}

.combo-section__settings {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.combo-section__options {
  padding-top: 14px;
  border-top: 1px solid var(--im-border-light);
}

/* ===== Option Items ===== */
.option-item {
  margin-bottom: 8px;
}

.option-row {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.option-row--template {
  background: var(--im-primary-light);
  padding: 10px;
  border-radius: var(--im-radius-sm);
  border: 1px solid #c8d0e8;
}

.nested-variants {
  margin-right: 28px;
  padding: 10px;
  background: var(--im-input-bg);
  border-radius: var(--im-radius-sm);
  border: 1px dashed var(--im-border);
}

.option-row--nested {
  background: var(--im-card);
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid var(--im-border-light);
}

.variant-name {
  font-size: 13px;
  color: var(--im-text-secondary);
}

/* ===== Recipe Section ===== */
.recipe-section {
  background: var(--im-input-bg);
  border-radius: var(--im-radius);
  padding: 18px;
  border: 1px solid var(--im-border);
}

/* ===== Sub-Dialogs ===== */
.new-product-editor > > > .v-dialog > .v-card {
  border-radius: var(--im-radius) !important;
}

.new-product-editor > > > .v-dialog .v-card__title {
  font-size: 16px !important;
  font-weight: 700 !important;
  color: var(--im-primary) !important;
  padding: 18px 24px !important;
  border-bottom: 1px solid var(--im-border) !important;
  background: var(--im-card) !important;
}

.new-product-editor > > > .v-dialog .v-card__text {
  padding: 20px 24px !important;
}

.new-product-editor > > > .v-dialog .v-card__actions {
  padding: 14px 24px !important;
  border-top: 1px solid var(--im-border-light) !important;
}

/* ===== Expansion Panels (Packaging) ===== */
.new-product-editor > > > .v-expansion-panel {
  border: 1px solid var(--im-border) !important;
  border-radius: var(--im-radius-sm) !important;
  margin-bottom: 8px;
}

.new-product-editor > > > .v-expansion-panel::before {
  box-shadow: none !important;
}

.new-product-editor > > > .v-expansion-panel-header {
  font-size: 13px;
  font-weight: 600;
  min-height: 44px !important;
  padding: 10px 16px !important;
}

/* ===== Preview Card ===== */
.preview-section > > > .v-card--outlined {
  border-color: var(--im-border) !important;
  border-radius: var(--im-radius) !important;
}

/* ===== RTL Support (Component-scoped only) ===== */
.rtl-scope {
  direction: rtl;
  text-align: right;
}

/* Inputs and textareas */
.rtl-scope :deep(input),
.rtl-scope :deep(textarea) {
  direction: rtl;
  text-align: right;
}

/* Labels, hints, validation messages */
.rtl-scope :deep(.v-label),
.rtl-scope :deep(.v-messages),
.rtl-scope :deep(.v-messages__message) {
  text-align: right;
}

/* Select and Autocomplete selections */
.rtl-scope :deep(.v-select__selection),
.rtl-scope :deep(.v-autocomplete__selection) {
  text-align: right;
}

/* Dropdown menu items */
.rtl-scope :deep(.v-list-item__title),
.rtl-scope :deep(.v-list-item__subtitle),
.rtl-scope :deep(.v-list-item__content) {
  text-align: right;
}

/* Menu positioning and padding */
.rtl-scope :deep(.v-menu__content) {
  text-align: right;
}

.rtl-scope :deep(.v-list-item) {
  padding-right: 16px;
  padding-left: 16px;
}

/* Chips alignment */
.rtl-scope :deep(.v-chip__content) {
  text-align: right;
}

/* Button with icon spacing - icons on right side in RTL */
.rtl-scope :deep(.v-btn .v-icon--right) {
  margin-left: 0;
  margin-right: 8px;
}

.rtl-scope :deep(.v-btn .v-icon--left) {
  margin-right: 0;
  margin-left: 8px;
}

/* Expansion panel headers */
.rtl-scope :deep(.v-expansion-panel-header) {
  text-align: right;
}

/* Data table cells */
.rtl-scope :deep(.v-data-table td),
.rtl-scope :deep(.v-data-table th) {
  text-align: right;
}

/* Card titles and text */
.rtl-scope :deep(.v-card__title),
.rtl-scope :deep(.v-card__text) {
  text-align: right;
}

/* Dialog content */
.rtl-scope :deep(.v-dialog .v-card__title),
.rtl-scope :deep(.v-dialog .v-card__text) {
  text-align: right;
}

/* Autocomplete/Select prepend/append icons positioning */
.rtl-scope :deep(.v-input__prepend-inner) {
  margin-right: 0;
  margin-left: 4px;
}

.rtl-scope :deep(.v-input__append-inner) {
  margin-left: 0;
  margin-right: 4px;
}

/* Select dropdown icon */
.rtl-scope :deep(.v-select__slot .v-input__append-inner) {
  margin-left: 0;
  margin-right: 4px;
}

/* Checkbox and switch labels */
.rtl-scope :deep(.v-input--selection-controls__input) {
  margin-right: 0;
  margin-left: 8px;
}

/* Alert text */
.rtl-scope :deep(.v-alert__content) {
  text-align: right;
}

/* Snackbar */
.rtl-scope :deep(.v-snack__content) {
  text-align: right;
}

/* ===== Fix Vuetify label position in RTL (outlined) ===== */
.rtl-scope :deep(.v-text-field--outlined .v-label),
.rtl-scope :deep(.v-select--outlined .v-label),
.rtl-scope :deep(.v-autocomplete--outlined .v-label),
.rtl-scope :deep(.v-combobox--outlined .v-label) {
  left: auto !important;
  right: 12px !important;
  /* عدّلها حسب padding بتاعك */
  transform-origin: top right !important;
  text-align: right !important;
}

/* لما الـ label يبقى active (فوق) */
.rtl-scope :deep(.v-text-field--outlined.v-input--is-label-active .v-label),
.rtl-scope :deep(.v-text-field--outlined.v-input--is-focused .v-label) {
  left: auto !important;
  right: 12px !important;
  transform-origin: top right !important;
}

/* أحيانًا الـ legend بتاع الـ outline بيبوّظ شكل القص */
.rtl-scope :deep(.v-text-field--outlined legend) {
  text-align: right !important;
}
</style>
