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
import { i as ref, l as computed, A as watch, j as onMounted, c as createElementBlock, f as createBaseVNode, x as unref, t as toDisplayString, J as withDirectives, K as vModelText, R as vModelSelect, F as Fragment, B as renderList, d as createVNode, w as withCtx, I as _sfc_main$1, h as createCommentVNode, v as call, ad as useRouter, o as openBlock, m as createBlock, e as createTextVNode, C as h } from "./index-jY-oWqoI.js";
import { L as LazyImage } from "./LazyImage-CrISaA0D.js";
import { _ as _sfc_main$2 } from "./ReservationCartBar-Cfh0Qix2.js";
import { formatCurrencyCode } from "./currency-KPLDlCCc.js";
const _hoisted_1 = {
  class: "flex flex-col bg-gray-50",
  style: { "height": "100vh", "max-height": "100vh" }
};
const _hoisted_2 = { class: "flex items-center gap-3 px-3 sm:px-4 py-2.5 sm:py-3 bg-white border-b border-gray-200" };
const _hoisted_3 = ["aria-label"];
const _hoisted_4 = { class: "text-sm sm:text-base font-semibold text-gray-900 truncate" };
const _hoisted_5 = { class: "text-xs text-gray-500 hidden sm:inline" };
const _hoisted_6 = { class: "px-3 sm:px-4 py-2 sm:py-3 bg-white border-b border-gray-200 flex items-center gap-2" };
const _hoisted_7 = { class: "flex-1 relative min-w-0" };
const _hoisted_8 = ["placeholder", "aria-label"];
const _hoisted_9 = ["aria-label"];
const _hoisted_10 = { value: null };
const _hoisted_11 = ["value"];
const _hoisted_12 = { class: "flex-1 overflow-y-auto px-3 sm:px-4 py-3 sm:py-4 pb-20" };
const _hoisted_13 = {
  key: 0,
  class: "flex items-center justify-center h-full text-gray-400 text-sm"
};
const _hoisted_14 = {
  key: 1,
  class: "flex items-center justify-center h-full text-gray-400 text-sm"
};
const _hoisted_15 = {
  key: 2,
  class: "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2 sm:gap-3"
};
const _hoisted_16 = ["onClick"];
const _hoisted_17 = { class: "relative w-full aspect-square bg-gray-100 rounded-md mb-2 overflow-hidden" };
const _hoisted_18 = {
  key: 1,
  class: "w-full h-full flex items-center justify-center"
};
const _hoisted_19 = ["title"];
const _hoisted_20 = { class: "text-[10px] sm:text-xs text-gray-500 truncate" };
const _hoisted_21 = { class: "mt-1 text-xs sm:text-sm font-semibold text-gray-900" };
const _hoisted_22 = {
  key: 3,
  class: "flex justify-center mt-4"
};
const PAGE_SIZE = 40;
const _sfc_main = {
  __name: "Build",
  setup(__props) {
    const router = useRouter();
    const products = ref([]);
    const itemGroups = ref([]);
    const searchTerm = ref("");
    const selectedGroup = ref(null);
    const start = ref(0);
    const totalCount = ref(0);
    const loading = ref(false);
    const loadingMore = ref(false);
    const currency = ref("SAR");
    const hasMore = computed(() => products.value.length < totalCount.value);
    const PlaceholderIcon = () => h(
      "svg",
      {
        class: "h-8 w-8 text-gray-300",
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
    function fetchProducts() {
      return __async(this, arguments, function* ({ append = false } = {}) {
        if (append) {
          loadingMore.value = true;
        } else {
          loading.value = true;
          start.value = 0;
        }
        try {
          const response = yield call("ecs_posnext.api.items.get_all_products", {
            search_term: searchTerm.value || null,
            item_group: selectedGroup.value,
            start: start.value,
            limit: PAGE_SIZE
          });
          const data = (response == null ? void 0 : response.message) || response;
          products.value = append ? [...products.value, ...data.items || []] : data.items || [];
          totalCount.value = data.total_count || 0;
          currency.value = data.currency || currency.value;
        } finally {
          loading.value = false;
          loadingMore.value = false;
        }
      });
    }
    function loadMore() {
      start.value += PAGE_SIZE;
      fetchProducts({ append: true });
    }
    function openProduct(item) {
      router.push({ name: "BuildProductDetail", params: { item_code: item.item_code } });
    }
    function loadItemGroups() {
      return __async(this, null, function* () {
        const response = yield call("ecs_posnext.api.items.get_build_catalog_item_groups");
        itemGroups.value = (response == null ? void 0 : response.message) || response || [];
      });
    }
    let searchDebounce = null;
    watch([searchTerm, selectedGroup], () => {
      clearTimeout(searchDebounce);
      searchDebounce = setTimeout(() => fetchProducts(), 300);
    });
    onMounted(() => {
      fetchProducts();
      loadItemGroups();
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          createBaseVNode("button", {
            onClick: _cache[0] || (_cache[0] = ($event) => unref(router).push({ name: "POSSale" })),
            class: "flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs sm:text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 active:bg-blue-200 touch-manipulation",
            "aria-label": _ctx.__("Back to POS")
          }, [
            _cache[3] || (_cache[3] = createBaseVNode("svg", {
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
            createBaseVNode("span", null, toDisplayString(_ctx.__("Back")), 1)
          ], 8, _hoisted_3),
          createBaseVNode("h1", _hoisted_4, toDisplayString(_ctx.__("Build")), 1),
          createBaseVNode("span", _hoisted_5, toDisplayString(_ctx.__("All products")), 1)
        ]),
        createBaseVNode("div", _hoisted_6, [
          createBaseVNode("div", _hoisted_7, [
            _cache[4] || (_cache[4] = createBaseVNode("div", { class: "absolute inset-y-0 start-0 ps-3 flex items-center pointer-events-none" }, [
              createBaseVNode("svg", {
                class: "h-4 w-4 text-gray-400",
                fill: "none",
                stroke: "currentColor",
                viewBox: "0 0 24 24"
              }, [
                createBaseVNode("path", {
                  "stroke-linecap": "round",
                  "stroke-linejoin": "round",
                  "stroke-width": "2",
                  d: "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                })
              ])
            ], -1)),
            withDirectives(createBaseVNode("input", {
              "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => searchTerm.value = $event),
              type: "text",
              placeholder: _ctx.__("Search products..."),
              class: "w-full text-sm border border-gray-300 rounded-lg px-3 py-2 ps-9 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
              "aria-label": _ctx.__("Search products")
            }, null, 8, _hoisted_8), [
              [vModelText, searchTerm.value]
            ])
          ]),
          withDirectives(createBaseVNode("select", {
            "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => selectedGroup.value = $event),
            class: "text-sm border border-gray-300 rounded-lg px-2 py-2 max-w-[10rem] sm:max-w-xs focus:outline-none focus:ring-2 focus:ring-blue-500",
            "aria-label": _ctx.__("Filter by item group")
          }, [
            createBaseVNode("option", _hoisted_10, toDisplayString(_ctx.__("All groups")), 1),
            (openBlock(true), createElementBlock(Fragment, null, renderList(itemGroups.value, (group) => {
              return openBlock(), createElementBlock("option", {
                key: group,
                value: group
              }, toDisplayString(_ctx.__(group)), 9, _hoisted_11);
            }), 128))
          ], 8, _hoisted_9), [
            [vModelSelect, selectedGroup.value]
          ])
        ]),
        createBaseVNode("div", _hoisted_12, [
          loading.value && !products.value.length ? (openBlock(), createElementBlock("div", _hoisted_13, toDisplayString(_ctx.__("Loading products...")), 1)) : !products.value.length ? (openBlock(), createElementBlock("div", _hoisted_14, toDisplayString(_ctx.__("No products found")), 1)) : (openBlock(), createElementBlock("div", _hoisted_15, [
            (openBlock(true), createElementBlock(Fragment, null, renderList(products.value, (item) => {
              return openBlock(), createElementBlock("div", {
                key: item.item_code,
                onClick: ($event) => openProduct(item),
                class: "bg-white rounded-lg border border-gray-200 p-2 sm:p-3 flex flex-col cursor-pointer hover:shadow-md hover:border-blue-300 transition-shadow touch-manipulation"
              }, [
                createBaseVNode("div", _hoisted_17, [
                  item.image ? (openBlock(), createBlock(LazyImage, {
                    key: 0,
                    src: item.image,
                    alt: item.item_name,
                    "container-class": "relative w-full h-full",
                    "img-class": "w-full h-full object-cover",
                    "root-margin": "150px"
                  }, {
                    error: withCtx(() => [
                      createVNode(PlaceholderIcon)
                    ]),
                    _: 2
                  }, 1032, ["src", "alt"])) : (openBlock(), createElementBlock("div", _hoisted_18, [
                    createVNode(PlaceholderIcon)
                  ]))
                ]),
                createBaseVNode("div", {
                  class: "text-xs sm:text-sm font-medium text-gray-900 truncate",
                  title: item.item_name
                }, toDisplayString(item.item_name), 9, _hoisted_19),
                createBaseVNode("div", _hoisted_20, toDisplayString(_ctx.__(item.item_group)), 1),
                createBaseVNode("div", _hoisted_21, toDisplayString(unref(formatCurrencyCode)(item.price_list_rate, currency.value)), 1)
              ], 8, _hoisted_16);
            }), 128))
          ])),
          hasMore.value ? (openBlock(), createElementBlock("div", _hoisted_22, [
            createVNode(unref(_sfc_main$1), {
              variant: "outline",
              loading: loadingMore.value,
              onClick: loadMore
            }, {
              default: withCtx(() => [
                createTextVNode(toDisplayString(_ctx.__("Load more")), 1)
              ]),
              _: 1
            }, 8, ["loading"])
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
