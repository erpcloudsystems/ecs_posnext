var __async = (__this, __arguments, generator) => {
  return new Promise((resolve, reject) => {
    var fulfilled = (value) => {
      try {
        step(generator.next(value));
      } catch (e) {
        reject(e);
      }
    };
    var rejected = (value) => {
      try {
        step(generator.throw(value));
      } catch (e) {
        reject(e);
      }
    };
    var step = (x) => x.done ? resolve(x.value) : Promise.resolve(x.value).then(fulfilled, rejected);
    step((generator = generator.apply(__this, __arguments)).next());
  });
};
import { i as ref, l as computed, A as watch, a4 as __, j as onMounted, c as createElementBlock, f as createBaseVNode, x as unref, t as toDisplayString, d as createVNode, w as withCtx, I as _sfc_main$1, m as createBlock, F as Fragment, B as renderList, h as createCommentVNode, e as createTextVNode, J as withDirectives, K as vModelText, v as call, ad as useRouter, ae as useRoute, o as openBlock, C as h } from "./index-jY-oWqoI.js";
import { A as AutocompleteSelect } from "./AutocompleteSelect-B093H_UT.js";
import { L as LazyImage } from "./LazyImage-CrISaA0D.js";
import { u as useBuildReservationStore, _ as _sfc_main$2 } from "./ReservationCartBar-Cfh0Qix2.js";
import { formatCurrencyCode } from "./currency-KPLDlCCc.js";
const _hoisted_1 = {
  class: "flex flex-col bg-gray-50",
  style: { "height": "100vh", "max-height": "100vh" }
};
const _hoisted_2 = { class: "flex items-center gap-3 px-3 sm:px-4 py-2.5 sm:py-3 bg-white border-b border-gray-200" };
const _hoisted_3 = ["aria-label"];
const _hoisted_4 = { class: "text-sm sm:text-base font-semibold text-gray-900 truncate" };
const _hoisted_5 = { class: "flex-1 overflow-y-auto px-3 sm:px-4 py-4 pb-20" };
const _hoisted_6 = {
  key: 0,
  class: "flex items-center justify-center h-full text-gray-400 text-sm"
};
const _hoisted_7 = {
  key: 1,
  class: "flex flex-col items-center justify-center h-full text-gray-400 text-sm gap-2"
};
const _hoisted_8 = {
  key: 2,
  class: "max-w-3xl mx-auto grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6"
};
const _hoisted_9 = { class: "bg-white rounded-lg border border-gray-200 aspect-square overflow-hidden" };
const _hoisted_10 = {
  key: 1,
  class: "w-full h-full flex items-center justify-center"
};
const _hoisted_11 = {
  key: 0,
  class: "bg-white rounded-lg border border-gray-200 mt-3 p-3"
};
const _hoisted_12 = { class: "text-xs font-semibold text-gray-500 uppercase mb-2" };
const _hoisted_13 = { class: "text-sm text-gray-700 divide-y divide-gray-100" };
const _hoisted_14 = { class: "text-gray-500" };
const _hoisted_15 = { class: "flex flex-col gap-3" };
const _hoisted_16 = { class: "text-xs text-gray-500" };
const _hoisted_17 = { class: "text-lg sm:text-xl font-semibold text-gray-900" };
const _hoisted_18 = {
  key: 0,
  class: "text-xs text-gray-500 mt-0.5"
};
const _hoisted_19 = { class: "text-xl sm:text-2xl font-bold text-gray-900" };
const _hoisted_20 = {
  key: 0,
  class: "text-sm font-normal text-gray-500"
};
const _hoisted_21 = {
  key: 0,
  class: "text-xs font-medium text-amber-600 bg-amber-50 rounded px-2 py-1 w-fit"
};
const _hoisted_22 = {
  key: 1,
  class: "text-sm text-gray-600"
};
const _hoisted_23 = ["innerHTML"];
const _hoisted_24 = { class: "bg-white rounded-lg border border-gray-200 p-3 sm:p-4 flex flex-col gap-3 mt-2" };
const _hoisted_25 = { class: "text-sm font-semibold text-gray-900" };
const _hoisted_26 = { class: "block text-xs font-medium text-gray-600 mb-1" };
const _hoisted_27 = {
  key: 0,
  class: "text-gray-400 font-normal"
};
const _hoisted_28 = { class: "flex items-center gap-2" };
const _hoisted_29 = ["min"];
const _hoisted_30 = { class: "block text-xs font-medium text-gray-600 mb-1" };
const _hoisted_31 = { key: 0 };
const _hoisted_32 = { class: "block text-xs font-medium text-gray-600 mb-1" };
const _hoisted_33 = { class: "block text-xs font-medium text-gray-600 mb-1" };
const _hoisted_34 = ["min"];
const _hoisted_35 = { key: 1 };
const _hoisted_36 = { class: "block text-xs font-medium text-gray-600 mb-1" };
const _hoisted_37 = {
  key: 0,
  class: "text-gray-400 font-normal"
};
const _hoisted_38 = { key: 2 };
const _hoisted_39 = { class: "block text-xs font-medium text-gray-600 mb-1" };
const _hoisted_40 = { class: "text-sm text-gray-700" };
const _hoisted_41 = { class: "font-semibold text-gray-900" };
const _hoisted_42 = {
  key: 1,
  class: "text-xs text-red-600 bg-red-50 rounded px-2 py-1.5"
};
const _hoisted_43 = {
  key: 2,
  class: "text-xs text-green-700 bg-green-50 rounded px-2 py-1.5"
};
const _sfc_main = {
  __name: "BuildProductDetail",
  setup(__props) {
    const route = useRoute();
    const router = useRouter();
    const store = useBuildReservationStore();
    const product = ref(null);
    const bookingOptions = ref(null);
    const currency = ref("SAR");
    const loading = ref(false);
    const error = ref(null);
    const qty = ref(1);
    const selectedUom = ref(null);
    const rooms = ref([]);
    const roomsLoading = ref(false);
    const slot = ref(null);
    const slots = ref([]);
    const slotsLoading = ref(false);
    const addError = ref(null);
    const added = ref(false);
    const todayStr = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
    const minQty = computed(() => {
      var _a;
      return ((_a = bookingOptions.value) == null ? void 0 : _a.minimum_sales_quantity) || 1;
    });
    const selectedRate = computed(() => {
      var _a, _b, _c;
      const match = (_b = (_a = bookingOptions.value) == null ? void 0 : _a.uoms) == null ? void 0 : _b.find((u) => u.uom === selectedUom.value);
      return match ? match.rate : ((_c = product.value) == null ? void 0 : _c.price_list_rate) || 0;
    });
    const isWeekend = computed(() => {
      if (!store.visitDate) return false;
      const day = (/* @__PURE__ */ new Date(`${store.visitDate}T00:00:00`)).getDay();
      return day === 4 || day === 5;
    });
    const filteredUoms = computed(() => {
      var _a;
      const uoms = ((_a = bookingOptions.value) == null ? void 0 : _a.uoms) || [];
      if (!store.visitDate) return uoms;
      const wantWord = isWeekend.value ? "weekend" : "weekday";
      const matches = uoms.filter((u) => u.uom.toLowerCase().includes(wantWord));
      return matches.length ? matches : uoms;
    });
    watch(filteredUoms, (uoms) => {
      var _a;
      if (!uoms.some((u) => u.uom === selectedUom.value)) {
        selectedUom.value = ((_a = uoms[0]) == null ? void 0 : _a.uom) || null;
      }
    });
    const parentBranchOptions = computed(
      () => {
        var _a;
        return (((_a = bookingOptions.value) == null ? void 0 : _a.parent_branches) || []).map((b) => ({ value: b, label: b }));
      }
    );
    const roomOptions = computed(
      () => rooms.value.map((r) => ({ value: r.name, label: r.is_group ? __("Whole Branch") : r.name }))
    );
    const uomOptions = computed(
      () => filteredUoms.value.map((u) => ({
        value: u.uom,
        label: __(u.uom),
        subtitle: formatCurrencyCode(u.rate, currency.value)
      }))
    );
    const slotOptions = computed(() => slots.value.map((s) => ({ value: s.id, label: s.Name })));
    const PlaceholderIcon = () => h(
      "svg",
      {
        class: "h-16 w-16 text-gray-300",
        fill: "none",
        stroke: "currentColor",
        viewBox: "0 0 24 24"
      },
      [
        h("path", {
          "stroke-linecap": "round",
          "stroke-linejoin": "round",
          "stroke-width": "2",
          d: "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
        })
      ]
    );
    function fetchProduct() {
      return __async(this, null, function* () {
        var _a, _b, _c, _d, _e, _f, _g, _h;
        loading.value = true;
        error.value = null;
        product.value = null;
        bookingOptions.value = null;
        added.value = false;
        addError.value = null;
        try {
          const [productResponse, optionsResponse] = yield Promise.all([
            call("ecs_posnext.api.items.get_product_detail", { item_code: route.params.item_code }),
            call("ecs_posnext.api.build_booking.get_booking_options", { item_code: route.params.item_code })
          ]);
          product.value = (productResponse == null ? void 0 : productResponse.message) || productResponse;
          bookingOptions.value = (optionsResponse == null ? void 0 : optionsResponse.message) || optionsResponse;
          currency.value = ((_a = product.value) == null ? void 0 : _a.currency) || ((_b = bookingOptions.value) == null ? void 0 : _b.currency) || "SAR";
          selectedUom.value = ((_e = (_d = (_c = bookingOptions.value) == null ? void 0 : _c.uoms) == null ? void 0 : _d[0]) == null ? void 0 : _e.uom) || null;
          qty.value = minQty.value;
          if ((_f = bookingOptions.value) == null ? void 0 : _f.requires_booking) {
            const parentBranches = ((_g = bookingOptions.value) == null ? void 0 : _g.parent_branches) || [];
            if (!store.parentBranch || !parentBranches.includes(store.parentBranch)) {
              store.parentBranch = parentBranches.length === 1 ? parentBranches[0] : null;
              store.room = null;
            }
            if (store.parentBranch) {
              yield fetchRooms();
            } else {
              rooms.value = [];
            }
          }
        } catch (err) {
          error.value = ((_h = err == null ? void 0 : err.messages) == null ? void 0 : _h[0]) || (err == null ? void 0 : err.message) || __("Product not found");
        } finally {
          loading.value = false;
        }
      });
    }
    function onParentBranchChange() {
      return __async(this, null, function* () {
        store.room = null;
        yield fetchRooms();
      });
    }
    function fetchRooms() {
      return __async(this, null, function* () {
        if (!store.parentBranch) {
          rooms.value = [];
          return;
        }
        roomsLoading.value = true;
        try {
          const response = yield call("ecs_posnext.api.build_booking.get_rooms", {
            item_code: route.params.item_code,
            parent_branch: store.parentBranch
          });
          rooms.value = (response == null ? void 0 : response.message) || response || [];
          if (store.room && !rooms.value.some((r) => r.name === store.room)) {
            store.room = rooms.value.length === 1 ? rooms.value[0].name : null;
          }
        } finally {
          roomsLoading.value = false;
        }
      });
    }
    function fetchSlots() {
      return __async(this, null, function* () {
        var _a;
        if (!((_a = bookingOptions.value) == null ? void 0 : _a.non_sharable_slot) || !store.visitDate || !store.room) {
          slots.value = [];
          return;
        }
        slotsLoading.value = true;
        slot.value = null;
        try {
          const response = yield call("ecs_posnext.api.build_booking.get_slots", {
            item_code: route.params.item_code,
            visit_date: store.visitDate,
            branch: store.room
          });
          slots.value = (response == null ? void 0 : response.message) || response || [];
        } finally {
          slotsLoading.value = false;
        }
      });
    }
    function addToCart() {
      var _a, _b, _c;
      addError.value = null;
      added.value = false;
      if ((_a = bookingOptions.value) == null ? void 0 : _a.requires_booking) {
        if (!store.room) {
          addError.value = __("Select a branch and room first");
          return;
        }
        if (!store.visitDate) {
          addError.value = __("Select a visit date first");
          return;
        }
        if (((_b = bookingOptions.value) == null ? void 0 : _b.non_sharable_slot) && !slot.value) {
          addError.value = __("Select a slot first");
          return;
        }
      }
      store.addItem({
        item_code: route.params.item_code,
        item_name: product.value.web_item_name || product.value.item_name,
        qty: Math.max(minQty.value, qty.value),
        uom: selectedUom.value,
        rate: selectedRate.value,
        slot: ((_c = bookingOptions.value) == null ? void 0 : _c.non_sharable_slot) ? slot.value : null
      });
      added.value = true;
      qty.value = minQty.value;
    }
    watch(() => store.room, fetchSlots);
    watch(() => store.visitDate, fetchSlots);
    watch(() => route.params.item_code, fetchProduct);
    onMounted(fetchProduct);
    return (_ctx, _cache) => {
      var _a, _b, _c, _d;
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          createBaseVNode("button", {
            onClick: _cache[0] || (_cache[0] = ($event) => unref(router).push({ name: "Build" })),
            class: "flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs sm:text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 active:bg-blue-200 touch-manipulation",
            "aria-label": unref(__)("Back to catalog")
          }, [
            _cache[11] || (_cache[11] = createBaseVNode("svg", {
              class: "w-4 h-4",
              fill: "none",
              stroke: "currentColor",
              viewBox: "0 0 24 24"
            }, [
              createBaseVNode("path", {
                "stroke-linecap": "round",
                "stroke-linejoin": "round",
                "stroke-width": "2",
                d: "M15 19l-7-7 7-7"
              })
            ], -1)),
            createBaseVNode("span", null, toDisplayString(unref(__)("Back")), 1)
          ], 8, _hoisted_3),
          createBaseVNode("h1", _hoisted_4, toDisplayString(unref(__)("Product Details")), 1)
        ]),
        createBaseVNode("div", _hoisted_5, [
          loading.value ? (openBlock(), createElementBlock("div", _hoisted_6, toDisplayString(unref(__)("Loading product...")), 1)) : error.value ? (openBlock(), createElementBlock("div", _hoisted_7, [
            createBaseVNode("span", null, toDisplayString(error.value), 1),
            createVNode(unref(_sfc_main$1), {
              variant: "outline",
              onClick: _cache[1] || (_cache[1] = ($event) => unref(router).push({ name: "Build" }))
            }, {
              default: withCtx(() => [
                createTextVNode(toDisplayString(unref(__)("Back to catalog")), 1)
              ]),
              _: 1
            })
          ])) : product.value ? (openBlock(), createElementBlock("div", _hoisted_8, [
            createBaseVNode("div", null, [
              createBaseVNode("div", _hoisted_9, [
                product.value.image ? (openBlock(), createBlock(LazyImage, {
                  key: 0,
                  src: product.value.image,
                  alt: product.value.item_name,
                  "container-class": "relative w-full h-full",
                  "img-class": "w-full h-full object-cover"
                }, {
                  error: withCtx(() => [
                    createVNode(PlaceholderIcon)
                  ]),
                  _: 1
                }, 8, ["src", "alt"])) : (openBlock(), createElementBlock("div", _hoisted_10, [
                  createVNode(PlaceholderIcon)
                ]))
              ]),
              ((_b = (_a = bookingOptions.value) == null ? void 0 : _a.bundle_items) == null ? void 0 : _b.length) ? (openBlock(), createElementBlock("div", _hoisted_11, [
                createBaseVNode("div", _hoisted_12, toDisplayString(unref(__)("Included Items")), 1),
                createBaseVNode("ul", _hoisted_13, [
                  (openBlock(true), createElementBlock(Fragment, null, renderList(bookingOptions.value.bundle_items, (bundleItem) => {
                    return openBlock(), createElementBlock("li", {
                      key: bundleItem.item_code,
                      class: "flex justify-between py-1.5"
                    }, [
                      createBaseVNode("span", null, toDisplayString(bundleItem.item_name || bundleItem.item_code), 1),
                      createBaseVNode("span", _hoisted_14, toDisplayString(bundleItem.qty) + " " + toDisplayString(bundleItem.uom), 1)
                    ]);
                  }), 128))
                ])
              ])) : createCommentVNode("", true)
            ]),
            createBaseVNode("div", _hoisted_15, [
              createBaseVNode("div", null, [
                createBaseVNode("div", _hoisted_16, toDisplayString(unref(__)(product.value.item_group)), 1),
                createBaseVNode("h2", _hoisted_17, toDisplayString(product.value.web_item_name || product.value.item_name), 1),
                product.value.brand ? (openBlock(), createElementBlock("div", _hoisted_18, toDisplayString(unref(__)(product.value.brand)), 1)) : createCommentVNode("", true)
              ]),
              createBaseVNode("div", _hoisted_19, [
                createTextVNode(toDisplayString(unref(formatCurrencyCode)(selectedRate.value, currency.value)) + " ", 1),
                selectedUom.value ? (openBlock(), createElementBlock("span", _hoisted_20, "/ " + toDisplayString(unref(__)(selectedUom.value)), 1)) : createCommentVNode("", true)
              ]),
              product.value.on_backorder ? (openBlock(), createElementBlock("div", _hoisted_21, toDisplayString(unref(__)("On Backorder")), 1)) : createCommentVNode("", true),
              product.value.short_description ? (openBlock(), createElementBlock("p", _hoisted_22, toDisplayString(product.value.short_description), 1)) : createCommentVNode("", true),
              product.value.web_long_description ? (openBlock(), createElementBlock("div", {
                key: 2,
                class: "text-sm text-gray-700 prose prose-sm max-w-none",
                innerHTML: product.value.web_long_description
              }, null, 8, _hoisted_23)) : createCommentVNode("", true),
              createBaseVNode("div", _hoisted_24, [
                createBaseVNode("div", _hoisted_25, toDisplayString(unref(__)("Book This")), 1),
                createBaseVNode("div", null, [
                  createBaseVNode("label", _hoisted_26, [
                    createTextVNode(toDisplayString(unref(__)("Quantity")) + " ", 1),
                    minQty.value > 1 ? (openBlock(), createElementBlock("span", _hoisted_27, "(" + toDisplayString(unref(__)("min {0}", [minQty.value])) + ")", 1)) : createCommentVNode("", true)
                  ]),
                  createBaseVNode("div", _hoisted_28, [
                    createBaseVNode("button", {
                      type: "button",
                      onClick: _cache[2] || (_cache[2] = ($event) => qty.value = Math.max(minQty.value, qty.value - 1)),
                      class: "w-8 h-8 flex items-center justify-center rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-100 touch-manipulation"
                    }, "−"),
                    withDirectives(createBaseVNode("input", {
                      "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => qty.value = $event),
                      type: "number",
                      min: minQty.value,
                      onChange: _cache[4] || (_cache[4] = ($event) => qty.value = Math.max(minQty.value, qty.value)),
                      class: "w-20 text-center text-sm border border-gray-300 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    }, null, 40, _hoisted_29), [
                      [
                        vModelText,
                        qty.value,
                        void 0,
                        { number: true }
                      ]
                    ]),
                    createBaseVNode("button", {
                      type: "button",
                      onClick: _cache[5] || (_cache[5] = ($event) => qty.value = qty.value + 1),
                      class: "w-8 h-8 flex items-center justify-center rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-100 touch-manipulation"
                    }, "+")
                  ])
                ]),
                ((_c = bookingOptions.value) == null ? void 0 : _c.requires_booking) ? (openBlock(), createElementBlock(Fragment, { key: 0 }, [
                  createBaseVNode("div", null, [
                    createBaseVNode("label", _hoisted_30, toDisplayString(unref(__)("Branch")), 1),
                    createVNode(AutocompleteSelect, {
                      modelValue: unref(store).parentBranch,
                      "onUpdate:modelValue": [
                        _cache[6] || (_cache[6] = ($event) => unref(store).parentBranch = $event),
                        onParentBranchChange
                      ],
                      options: parentBranchOptions.value,
                      placeholder: unref(__)("Search branch...")
                    }, null, 8, ["modelValue", "options", "placeholder"])
                  ]),
                  unref(store).parentBranch ? (openBlock(), createElementBlock("div", _hoisted_31, [
                    createBaseVNode("label", _hoisted_32, toDisplayString(unref(__)("Room")), 1),
                    createVNode(AutocompleteSelect, {
                      modelValue: unref(store).room,
                      "onUpdate:modelValue": _cache[7] || (_cache[7] = ($event) => unref(store).room = $event),
                      options: roomOptions.value,
                      loading: roomsLoading.value,
                      placeholder: unref(__)("Search room...")
                    }, null, 8, ["modelValue", "options", "loading", "placeholder"])
                  ])) : createCommentVNode("", true),
                  createBaseVNode("div", null, [
                    createBaseVNode("label", _hoisted_33, toDisplayString(unref(__)("Visit Date")), 1),
                    withDirectives(createBaseVNode("input", {
                      "onUpdate:modelValue": _cache[8] || (_cache[8] = ($event) => unref(store).visitDate = $event),
                      type: "date",
                      min: unref(todayStr),
                      class: "w-full text-sm border border-gray-300 rounded-lg px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    }, null, 8, _hoisted_34), [
                      [vModelText, unref(store).visitDate]
                    ])
                  ]),
                  filteredUoms.value.length > 1 ? (openBlock(), createElementBlock("div", _hoisted_35, [
                    createBaseVNode("label", _hoisted_36, [
                      createTextVNode(toDisplayString(unref(__)("Weekday / Weekend")) + " ", 1),
                      unref(store).visitDate ? (openBlock(), createElementBlock("span", _hoisted_37, "(" + toDisplayString(isWeekend.value ? unref(__)("Weekend") : unref(__)("Weekday")) + ")", 1)) : createCommentVNode("", true)
                    ]),
                    createVNode(AutocompleteSelect, {
                      modelValue: selectedUom.value,
                      "onUpdate:modelValue": _cache[9] || (_cache[9] = ($event) => selectedUom.value = $event),
                      options: uomOptions.value,
                      placeholder: unref(__)("Search pricing option...")
                    }, null, 8, ["modelValue", "options", "placeholder"])
                  ])) : createCommentVNode("", true),
                  ((_d = bookingOptions.value) == null ? void 0 : _d.non_sharable_slot) ? (openBlock(), createElementBlock("div", _hoisted_38, [
                    createBaseVNode("label", _hoisted_39, toDisplayString(unref(__)("Slot")), 1),
                    createVNode(AutocompleteSelect, {
                      modelValue: slot.value,
                      "onUpdate:modelValue": _cache[10] || (_cache[10] = ($event) => slot.value = $event),
                      options: slotOptions.value,
                      loading: slotsLoading.value,
                      placeholder: slots.value.length ? unref(__)("Search slot...") : unref(__)("Select room and date first")
                    }, null, 8, ["modelValue", "options", "loading", "placeholder"])
                  ])) : createCommentVNode("", true)
                ], 64)) : createCommentVNode("", true),
                createBaseVNode("div", _hoisted_40, [
                  createTextVNode(toDisplayString(unref(__)("Total")) + ": ", 1),
                  createBaseVNode("span", _hoisted_41, toDisplayString(unref(formatCurrencyCode)(qty.value * selectedRate.value, currency.value)), 1)
                ]),
                addError.value ? (openBlock(), createElementBlock("div", _hoisted_42, toDisplayString(addError.value), 1)) : createCommentVNode("", true),
                added.value ? (openBlock(), createElementBlock("div", _hoisted_43, toDisplayString(unref(__)("Added to reservation")), 1)) : createCommentVNode("", true),
                createVNode(unref(_sfc_main$1), {
                  variant: "solid",
                  onClick: addToCart
                }, {
                  default: withCtx(() => [
                    createTextVNode(toDisplayString(unref(__)("Add to Cart")), 1)
                  ]),
                  _: 1
                })
              ])
            ])
          ])) : createCommentVNode("", true)
        ]),
        createVNode(_sfc_main$2, { currency: currency.value }, null, 8, ["currency"])
      ]);
    };
  }
};
export {
  _sfc_main as default
};
