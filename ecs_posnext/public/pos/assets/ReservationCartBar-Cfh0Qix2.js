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
import { P as defineStore, i as ref, l as computed, A as watch, o as openBlock, m as createBlock, w as withCtx, f as createBaseVNode, t as toDisplayString, x as unref, a4 as __, e as createTextVNode, c as createElementBlock, F as Fragment, B as renderList, h as createCommentVNode, J as withDirectives, K as vModelText, u as normalizeClass, d as createVNode, I as _sfc_main$2, L as Dialog, v as call } from "./index-jY-oWqoI.js";
import { formatCurrencyCode } from "./currency-KPLDlCCc.js";
const useBuildReservationStore = defineStore("buildReservation", () => {
  const parentBranch = ref(null);
  const room = ref(null);
  const visitDate = ref(null);
  const phone = ref("");
  const customerName = ref("");
  const customerLookup = ref({ checked: false, found: false, customerName: "" });
  const items = ref([]);
  const itemCount = computed(() => items.value.reduce((sum, i) => sum + i.qty, 0));
  const total = computed(() => items.value.reduce((sum, i) => sum + i.qty * i.rate, 0));
  function addItem(item) {
    const existing = items.value.find(
      (i) => i.item_code === item.item_code && i.uom === item.uom && i.slot === item.slot
    );
    if (existing) {
      existing.qty += item.qty;
    } else {
      items.value.push(item);
    }
  }
  function removeItem(index) {
    items.value.splice(index, 1);
  }
  function updateQty(index, qty) {
    if (qty <= 0) {
      removeItem(index);
      return;
    }
    items.value[index].qty = qty;
  }
  function clear() {
    items.value = [];
    parentBranch.value = null;
    room.value = null;
    visitDate.value = null;
    phone.value = "";
    customerName.value = "";
    customerLookup.value = { checked: false, found: false, customerName: "" };
  }
  return {
    parentBranch,
    room,
    visitDate,
    phone,
    customerName,
    customerLookup,
    items,
    itemCount,
    total,
    addItem,
    removeItem,
    updateQty,
    clear
  };
});
const _hoisted_1$1 = { class: "flex flex-col gap-4" };
const _hoisted_2$1 = { class: "bg-gray-50 rounded-lg p-3 text-sm text-gray-700 flex flex-col gap-1" };
const _hoisted_3$1 = { class: "text-gray-500" };
const _hoisted_4$1 = { class: "text-gray-500" };
const _hoisted_5 = { class: "flex flex-col divide-y divide-gray-100 border border-gray-200 rounded-lg" };
const _hoisted_6 = { class: "min-w-0" };
const _hoisted_7 = { class: "text-sm font-medium text-gray-900 truncate" };
const _hoisted_8 = { class: "text-xs text-gray-500 truncate" };
const _hoisted_9 = { key: 0 };
const _hoisted_10 = { class: "flex items-center gap-2 flex-shrink-0" };
const _hoisted_11 = ["value", "onChange"];
const _hoisted_12 = { class: "text-sm font-semibold text-gray-900 w-20 text-end" };
const _hoisted_13 = ["onClick", "aria-label"];
const _hoisted_14 = { class: "flex justify-between text-sm font-semibold text-gray-900 px-1" };
const _hoisted_15 = { class: "block text-xs font-medium text-gray-600 mb-1" };
const _hoisted_16 = ["placeholder"];
const _hoisted_17 = {
  key: 0,
  class: "mt-1 text-xs"
};
const _hoisted_18 = {
  key: 0,
  class: "text-green-600"
};
const _hoisted_19 = {
  key: 1,
  class: "text-amber-600"
};
const _hoisted_20 = { key: 0 };
const _hoisted_21 = { class: "block text-xs font-medium text-gray-600 mb-1" };
const _hoisted_22 = ["placeholder"];
const _hoisted_23 = {
  key: 1,
  class: "text-xs text-red-600 bg-red-50 rounded px-2 py-1.5"
};
const _sfc_main$1 = {
  __name: "ReservationCheckoutDialog",
  props: {
    modelValue: { type: Boolean, default: false },
    currency: { type: String, default: "SAR" }
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const store = useBuildReservationStore();
    const show = computed({
      get: () => props.modelValue,
      set: (value) => emit("update:modelValue", value)
    });
    const booking = ref(false);
    const bookingError = ref(null);
    const bookingResult = ref(null);
    const canBook = computed(() => {
      if (booking.value || !store.items.length || !store.room || !store.visitDate || !store.phone) return false;
      if (store.customerLookup.checked && !store.customerLookup.found && !store.customerName) return false;
      return true;
    });
    function lookupCustomer() {
      return __async(this, null, function* () {
        if (!store.phone) {
          store.customerLookup = { checked: false, found: false, customerName: "" };
          return;
        }
        const response = yield call("ecs_posnext.api.build_booking.lookup_customer_by_phone", { phone: store.phone });
        const data = (response == null ? void 0 : response.message) || response;
        store.customerLookup = { checked: true, found: !!data, customerName: (data == null ? void 0 : data.customer_name) || "" };
      });
    }
    function confirmBooking() {
      return __async(this, null, function* () {
        var _a, _b;
        booking.value = true;
        bookingError.value = null;
        bookingResult.value = null;
        try {
          const response = yield call("ecs_posnext.api.build_booking.create_booking", {
            items: store.items.map((item) => ({
              item_code: item.item_code,
              qty: item.qty,
              uom: item.uom,
              slot: item.slot
            })),
            branch: store.room,
            visit_date: store.visitDate,
            phone: store.phone,
            customer_name: store.customerLookup.found ? null : store.customerName
          });
          bookingResult.value = (response == null ? void 0 : response.message) || response;
          if ((_a = bookingResult.value) == null ? void 0 : _a.sales_order) {
            store.clear();
            window.location.href = `/app/sales-order/${bookingResult.value.sales_order}`;
          }
        } catch (err) {
          bookingError.value = ((_b = err == null ? void 0 : err.messages) == null ? void 0 : _b[0]) || (err == null ? void 0 : err.message) || __("Could not create the booking");
        } finally {
          booking.value = false;
        }
      });
    }
    watch(show, (value) => {
      if (!value) {
        bookingError.value = null;
      }
    });
    return (_ctx, _cache) => {
      return openBlock(), createBlock(unref(Dialog), {
        modelValue: show.value,
        "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => show.value = $event),
        options: { title: unref(__)("Review Reservation"), size: "lg" }
      }, {
        "body-content": withCtx(() => [
          createBaseVNode("div", _hoisted_1$1, [
            createBaseVNode("div", _hoisted_2$1, [
              createBaseVNode("div", null, [
                createBaseVNode("span", _hoisted_3$1, toDisplayString(unref(__)("Branch")) + ":", 1),
                createTextVNode(" " + toDisplayString(unref(store).room || "-"), 1)
              ]),
              createBaseVNode("div", null, [
                createBaseVNode("span", _hoisted_4$1, toDisplayString(unref(__)("Visit Date")) + ":", 1),
                createTextVNode(" " + toDisplayString(unref(store).visitDate || "-"), 1)
              ])
            ]),
            createBaseVNode("div", _hoisted_5, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(unref(store).items, (item, index) => {
                return openBlock(), createElementBlock("div", {
                  key: index,
                  class: "flex items-center justify-between gap-2 px-3 py-2"
                }, [
                  createBaseVNode("div", _hoisted_6, [
                    createBaseVNode("div", _hoisted_7, toDisplayString(item.item_name), 1),
                    createBaseVNode("div", _hoisted_8, [
                      createTextVNode(toDisplayString(item.uom) + " ", 1),
                      item.slot ? (openBlock(), createElementBlock("span", _hoisted_9, " · " + toDisplayString(item.slot), 1)) : createCommentVNode("", true)
                    ])
                  ]),
                  createBaseVNode("div", _hoisted_10, [
                    createBaseVNode("input", {
                      type: "number",
                      min: "1",
                      value: item.qty,
                      onChange: ($event) => unref(store).updateQty(index, Number($event.target.value)),
                      class: "w-14 text-center text-sm border border-gray-300 rounded-lg px-1 py-1"
                    }, null, 40, _hoisted_11),
                    createBaseVNode("div", _hoisted_12, toDisplayString(unref(formatCurrencyCode)(item.qty * item.rate, __props.currency)), 1),
                    createBaseVNode("button", {
                      type: "button",
                      onClick: ($event) => unref(store).removeItem(index),
                      class: "text-gray-400 hover:text-red-600 p-1",
                      "aria-label": unref(__)("Remove item")
                    }, _cache[3] || (_cache[3] = [
                      createBaseVNode("svg", {
                        class: "w-4 h-4",
                        fill: "none",
                        stroke: "currentColor",
                        viewBox: "0 0 24 24"
                      }, [
                        createBaseVNode("path", {
                          "stroke-linecap": "round",
                          "stroke-linejoin": "round",
                          "stroke-width": "2",
                          d: "M6 18L18 6M6 6l12 12"
                        })
                      ], -1)
                    ]), 8, _hoisted_13)
                  ])
                ]);
              }), 128))
            ]),
            createBaseVNode("div", _hoisted_14, [
              createBaseVNode("span", null, toDisplayString(unref(__)("Total")), 1),
              createBaseVNode("span", null, toDisplayString(unref(formatCurrencyCode)(unref(store).total, __props.currency)), 1)
            ]),
            createBaseVNode("div", null, [
              createBaseVNode("label", _hoisted_15, toDisplayString(unref(__)("Customer Phone Number")), 1),
              withDirectives(createBaseVNode("input", {
                "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => unref(store).phone = $event),
                onBlur: lookupCustomer,
                type: "tel",
                placeholder: unref(__)("Customer Phone Number"),
                class: "w-full text-sm border border-gray-300 rounded-lg px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              }, null, 40, _hoisted_16), [
                [vModelText, unref(store).phone]
              ]),
              unref(store).customerLookup.checked ? (openBlock(), createElementBlock("div", _hoisted_17, [
                unref(store).customerLookup.found ? (openBlock(), createElementBlock("span", _hoisted_18, toDisplayString(unref(__)("Customer")) + ": " + toDisplayString(unref(store).customerLookup.customerName), 1)) : (openBlock(), createElementBlock("span", _hoisted_19, toDisplayString(unref(__)("New customer — enter a name below")), 1))
              ])) : createCommentVNode("", true)
            ]),
            unref(store).customerLookup.checked && !unref(store).customerLookup.found ? (openBlock(), createElementBlock("div", _hoisted_20, [
              createBaseVNode("label", _hoisted_21, toDisplayString(unref(__)("Customer Name")), 1),
              withDirectives(createBaseVNode("input", {
                "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => unref(store).customerName = $event),
                type: "text",
                placeholder: unref(__)("Full name"),
                class: "w-full text-sm border border-gray-300 rounded-lg px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              }, null, 8, _hoisted_22), [
                [vModelText, unref(store).customerName]
              ])
            ])) : createCommentVNode("", true),
            bookingError.value ? (openBlock(), createElementBlock("div", _hoisted_23, toDisplayString(bookingError.value), 1)) : createCommentVNode("", true),
            bookingResult.value ? (openBlock(), createElementBlock("div", {
              key: 2,
              class: normalizeClass(["text-xs rounded px-2 py-1.5", bookingResult.value.submitted ? "text-green-700 bg-green-50" : "text-amber-700 bg-amber-50"])
            }, [
              bookingResult.value.submitted ? (openBlock(), createElementBlock(Fragment, { key: 0 }, [
                createTextVNode(toDisplayString(unref(__)("Booked")) + ": " + toDisplayString(bookingResult.value.sales_order), 1)
              ], 64)) : (openBlock(), createElementBlock(Fragment, { key: 1 }, [
                createTextVNode(toDisplayString(unref(__)("Reservation {0} created — pending branch manager approval before it can be closed at the register.", [bookingResult.value.sales_order])), 1)
              ], 64))
            ], 2)) : createCommentVNode("", true),
            createVNode(unref(_sfc_main$2), {
              variant: "solid",
              loading: booking.value,
              disabled: !canBook.value,
              onClick: confirmBooking
            }, {
              default: withCtx(() => [
                createTextVNode(toDisplayString(unref(__)("Confirm Booking")), 1)
              ]),
              _: 1
            }, 8, ["loading", "disabled"])
          ])
        ]),
        _: 1
      }, 8, ["modelValue", "options"]);
    };
  }
};
const _hoisted_1 = {
  key: 0,
  class: "fixed bottom-0 inset-x-0 bg-white border-t border-gray-200 shadow-lg px-3 sm:px-4 py-2.5 sm:py-3 flex items-center justify-between gap-3 z-40"
};
const _hoisted_2 = { class: "text-sm text-gray-700" };
const _hoisted_3 = { class: "font-semibold text-gray-900" };
const _hoisted_4 = { class: "font-semibold text-gray-900" };
const _sfc_main = {
  __name: "ReservationCartBar",
  props: {
    currency: { type: String, default: "SAR" }
  },
  setup(__props) {
    const store = useBuildReservationStore();
    const showCheckout = ref(false);
    return (_ctx, _cache) => {
      return unref(store).items.length ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          createBaseVNode("span", _hoisted_3, toDisplayString(unref(store).itemCount), 1),
          createTextVNode(" " + toDisplayString(unref(__)("item(s)")) + " ", 1),
          _cache[2] || (_cache[2] = createBaseVNode("span", { class: "mx-1 text-gray-300" }, "|", -1)),
          createBaseVNode("span", _hoisted_4, toDisplayString(unref(formatCurrencyCode)(unref(store).total, __props.currency)), 1)
        ]),
        createVNode(unref(_sfc_main$2), {
          variant: "solid",
          onClick: _cache[0] || (_cache[0] = ($event) => showCheckout.value = true)
        }, {
          default: withCtx(() => [
            createTextVNode(toDisplayString(unref(__)("Review & Book")), 1)
          ]),
          _: 1
        }),
        createVNode(_sfc_main$1, {
          modelValue: showCheckout.value,
          "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => showCheckout.value = $event),
          currency: __props.currency
        }, null, 8, ["modelValue", "currency"])
      ])) : createCommentVNode("", true);
    };
  }
};
export {
  _sfc_main as _,
  useBuildReservationStore as u
};
