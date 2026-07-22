import { a as _export_sfc, i as ref, l as computed, A as watch, j as onMounted, k as onUnmounted, o as openBlock, c as createElementBlock, f as createBaseVNode, h as createCommentVNode, J as withDirectives, K as vModelText, u as normalizeClass, d as createVNode, w as withCtx, t as toDisplayString, F as Fragment, B as renderList, T as Transition } from "./index-jY-oWqoI.js";
const _hoisted_1 = { class: "select-input-wrapper" };
const _hoisted_2 = {
  key: 0,
  class: "input-icon",
  fill: "none",
  stroke: "currentColor",
  viewBox: "0 0 24 24"
};
const _hoisted_3 = ["d"];
const _hoisted_4 = ["placeholder"];
const _hoisted_5 = { class: "input-actions" };
const _hoisted_6 = {
  key: 0,
  class: "dropdown-menu"
};
const _hoisted_7 = {
  key: 0,
  class: "dropdown-loading"
};
const _hoisted_8 = {
  key: 1,
  class: "dropdown-empty"
};
const _hoisted_9 = {
  key: 2,
  class: "dropdown-list"
};
const _hoisted_10 = ["onClick"];
const _hoisted_11 = {
  key: 0,
  class: "item-icon check-icon",
  fill: "none",
  stroke: "currentColor",
  viewBox: "0 0 24 24"
};
const _hoisted_12 = { class: "item-content" };
const _hoisted_13 = ["innerHTML"];
const _hoisted_14 = {
  key: 0,
  class: "item-subtitle"
};
const _sfc_main = {
  __name: "AutocompleteSelect",
  props: {
    modelValue: {
      type: [String, Number],
      default: ""
    },
    options: {
      type: Array,
      default: () => []
    },
    placeholder: {
      type: String,
      default: __("Search...")
    },
    icon: {
      type: String,
      default: ""
    },
    required: {
      type: Boolean,
      default: false
    },
    loading: {
      type: Boolean,
      default: false
    },
    // For async search
    searchable: {
      type: Boolean,
      default: true
    },
    minSearchLength: {
      type: Number,
      default: 0
    }
  },
  emits: ["update:modelValue", "search"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const containerRef = ref(null);
    const inputRef = ref(null);
    const searchQuery = ref("");
    const showDropdown = ref(false);
    const highlightedIndex = ref(-1);
    const displayLimit = ref(50);
    const selectedOption = computed(() => {
      return props.options.find((opt) => opt.value === props.modelValue);
    });
    watch(
      () => props.modelValue,
      (newValue) => {
        if (newValue && selectedOption.value) {
          searchQuery.value = selectedOption.value.label;
        } else if (!newValue) {
          searchQuery.value = "";
        }
      },
      { immediate: true }
    );
    const filteredOptions = computed(() => {
      var _a;
      if (!searchQuery.value || searchQuery.value === ((_a = selectedOption.value) == null ? void 0 : _a.label)) {
        return props.options;
      }
      const query = searchQuery.value.toLowerCase();
      return props.options.filter((option) => {
        var _a2;
        const label = option.label.toLowerCase();
        const subtitle = ((_a2 = option.subtitle) == null ? void 0 : _a2.toLowerCase()) || "";
        return label.includes(query) || subtitle.includes(query);
      });
    });
    const paginatedOptions = computed(() => {
      return filteredOptions.value.slice(0, displayLimit.value);
    });
    const hasMore = computed(() => {
      return filteredOptions.value.length > displayLimit.value;
    });
    function handleFocus() {
      var _a;
      showDropdown.value = true;
      highlightedIndex.value = -1;
      if (searchQuery.value) {
        (_a = inputRef.value) == null ? void 0 : _a.select();
      }
    }
    function handleInput() {
      showDropdown.value = true;
      highlightedIndex.value = -1;
      displayLimit.value = 50;
      if (props.searchable && searchQuery.value.length >= props.minSearchLength) {
        emit("search", searchQuery.value);
      }
    }
    function handleKeydown(e) {
      if (!showDropdown.value) {
        if (e.key === "ArrowDown" || e.key === "ArrowUp") {
          showDropdown.value = true;
          e.preventDefault();
          return;
        }
      }
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          highlightedIndex.value = Math.min(
            highlightedIndex.value + 1,
            paginatedOptions.value.length - 1
          );
          scrollToHighlighted();
          break;
        case "ArrowUp":
          e.preventDefault();
          highlightedIndex.value = Math.max(highlightedIndex.value - 1, -1);
          scrollToHighlighted();
          break;
        case "Enter":
          e.preventDefault();
          if (highlightedIndex.value >= 0) {
            selectOption(paginatedOptions.value[highlightedIndex.value]);
          }
          break;
        case "Escape":
          e.preventDefault();
          closeDropdown();
          break;
        case "Tab":
          closeDropdown();
          break;
      }
    }
    function toggleDropdown() {
      var _a;
      showDropdown.value = !showDropdown.value;
      if (showDropdown.value) {
        (_a = inputRef.value) == null ? void 0 : _a.focus();
      }
    }
    function selectOption(option) {
      var _a;
      emit("update:modelValue", option.value);
      searchQuery.value = option.label;
      closeDropdown();
      (_a = inputRef.value) == null ? void 0 : _a.blur();
    }
    function clearSelection() {
      var _a;
      emit("update:modelValue", "");
      searchQuery.value = "";
      showDropdown.value = false;
      (_a = inputRef.value) == null ? void 0 : _a.focus();
    }
    function closeDropdown() {
      showDropdown.value = false;
      highlightedIndex.value = -1;
      if (selectedOption.value) {
        searchQuery.value = selectedOption.value.label;
      }
    }
    function loadMore() {
      displayLimit.value += 50;
    }
    function scrollToHighlighted() {
      var _a, _b;
      const dropdown = (_a = containerRef.value) == null ? void 0 : _a.querySelector(".dropdown-list");
      const items = dropdown == null ? void 0 : dropdown.querySelectorAll(
        ".dropdown-item:not(.clear-item):not(.load-more)"
      );
      if (items && highlightedIndex.value >= 0) {
        (_b = items[highlightedIndex.value]) == null ? void 0 : _b.scrollIntoView({
          block: "nearest",
          behavior: "smooth"
        });
      }
    }
    function highlightMatch(text) {
      var _a;
      if (!searchQuery.value || searchQuery.value === ((_a = selectedOption.value) == null ? void 0 : _a.label)) {
        return text;
      }
      const query = searchQuery.value;
      const regex = new RegExp(`(${query})`, "gi");
      return text.replace(regex, "<mark>$1</mark>");
    }
    function handleClickOutside(event) {
      if (containerRef.value && !containerRef.value.contains(event.target)) {
        closeDropdown();
      }
    }
    onMounted(() => {
      document.addEventListener("click", handleClickOutside);
    });
    onUnmounted(() => {
      document.removeEventListener("click", handleClickOutside);
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", {
        class: "autocomplete-select",
        ref_key: "containerRef",
        ref: containerRef
      }, [
        createBaseVNode("div", _hoisted_1, [
          __props.icon ? (openBlock(), createElementBlock("svg", _hoisted_2, [
            createBaseVNode("path", {
              "stroke-linecap": "round",
              "stroke-linejoin": "round",
              "stroke-width": "2",
              d: __props.icon
            }, null, 8, _hoisted_3)
          ])) : createCommentVNode("", true),
          withDirectives(createBaseVNode("input", {
            ref_key: "inputRef",
            ref: inputRef,
            "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => searchQuery.value = $event),
            type: "text",
            class: normalizeClass(["select-input", { "has-icon": __props.icon, "has-value": __props.modelValue }]),
            placeholder: __props.placeholder,
            onFocus: handleFocus,
            onInput: handleInput,
            onKeydown: handleKeydown
          }, null, 42, _hoisted_4), [
            [vModelText, searchQuery.value]
          ]),
          createBaseVNode("div", _hoisted_5, [
            __props.modelValue ? (openBlock(), createElementBlock("button", {
              key: 0,
              onClick: clearSelection,
              class: "clear-btn",
              type: "button"
            }, _cache[1] || (_cache[1] = [
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
            ]))) : createCommentVNode("", true),
            createBaseVNode("button", {
              onClick: toggleDropdown,
              class: "dropdown-toggle",
              type: "button"
            }, [
              (openBlock(), createElementBlock("svg", {
                class: normalizeClass(["w-4 h-4", { "rotate-180": showDropdown.value }]),
                fill: "none",
                stroke: "currentColor",
                viewBox: "0 0 24 24"
              }, _cache[2] || (_cache[2] = [
                createBaseVNode("path", {
                  "stroke-linecap": "round",
                  "stroke-linejoin": "round",
                  "stroke-width": "2",
                  d: "M19 9l-7 7-7-7"
                }, null, -1)
              ]), 2))
            ])
          ])
        ]),
        createVNode(Transition, { name: "dropdown" }, {
          default: withCtx(() => [
            showDropdown.value ? (openBlock(), createElementBlock("div", _hoisted_6, [
              __props.loading ? (openBlock(), createElementBlock("div", _hoisted_7, [
                _cache[3] || (_cache[3] = createBaseVNode("div", { class: "loading-spinner" }, null, -1)),
                createBaseVNode("span", null, toDisplayString(_ctx.__("Searching...")), 1)
              ])) : filteredOptions.value.length === 0 ? (openBlock(), createElementBlock("div", _hoisted_8, [
                _cache[4] || (_cache[4] = createBaseVNode("svg", {
                  class: "empty-icon",
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
                ], -1)),
                createBaseVNode("span", null, toDisplayString(searchQuery.value ? _ctx.__("No results found") : _ctx.__("No options available")), 1)
              ])) : (openBlock(), createElementBlock("div", _hoisted_9, [
                !__props.required && __props.modelValue ? (openBlock(), createElementBlock("button", {
                  key: 0,
                  onClick: clearSelection,
                  class: "dropdown-item clear-item",
                  type: "button"
                }, [
                  _cache[5] || (_cache[5] = createBaseVNode("svg", {
                    class: "item-icon",
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
                  ], -1)),
                  createBaseVNode("span", null, toDisplayString(_ctx.__("Clear selection")), 1)
                ])) : createCommentVNode("", true),
                (openBlock(true), createElementBlock(Fragment, null, renderList(paginatedOptions.value, (option, index) => {
                  return openBlock(), createElementBlock("button", {
                    key: option.value,
                    onClick: ($event) => selectOption(option),
                    class: normalizeClass(["dropdown-item", {
                      active: option.value === __props.modelValue,
                      highlighted: index === highlightedIndex.value
                    }]),
                    type: "button"
                  }, [
                    option.value === __props.modelValue ? (openBlock(), createElementBlock("svg", _hoisted_11, _cache[6] || (_cache[6] = [
                      createBaseVNode("path", {
                        "stroke-linecap": "round",
                        "stroke-linejoin": "round",
                        "stroke-width": "2",
                        d: "M5 13l4 4L19 7"
                      }, null, -1)
                    ]))) : createCommentVNode("", true),
                    createBaseVNode("div", _hoisted_12, [
                      createBaseVNode("span", {
                        class: "item-label",
                        innerHTML: highlightMatch(option.label)
                      }, null, 8, _hoisted_13),
                      option.subtitle ? (openBlock(), createElementBlock("span", _hoisted_14, toDisplayString(option.subtitle), 1)) : createCommentVNode("", true)
                    ])
                  ], 10, _hoisted_10);
                }), 128)),
                hasMore.value ? (openBlock(), createElementBlock("button", {
                  key: 1,
                  onClick: loadMore,
                  class: "dropdown-item load-more",
                  type: "button"
                }, [
                  _cache[7] || (_cache[7] = createBaseVNode("svg", {
                    class: "item-icon",
                    fill: "none",
                    stroke: "currentColor",
                    viewBox: "0 0 24 24"
                  }, [
                    createBaseVNode("path", {
                      "stroke-linecap": "round",
                      "stroke-linejoin": "round",
                      "stroke-width": "2",
                      d: "M19 9l-7 7-7-7"
                    })
                  ], -1)),
                  createBaseVNode("span", null, toDisplayString(_ctx.__("Load more ({0} remaining)", [filteredOptions.value.length - displayLimit.value])), 1)
                ])) : createCommentVNode("", true)
              ]))
            ])) : createCommentVNode("", true)
          ]),
          _: 1
        })
      ], 512);
    };
  }
};
const AutocompleteSelect = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-e8ee12e1"]]);
export {
  AutocompleteSelect as A
};
