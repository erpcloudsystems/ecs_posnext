import { i as ref, j as onMounted, p as onBeforeUnmount, a as _export_sfc, l as computed, o as openBlock, c as createElementBlock, x as unref, u as normalizeClass, g as renderSlot, h as createCommentVNode, f as createBaseVNode } from "./index-jY-oWqoI.js";
function useLazyLoad(options = {}) {
  const {
    rootMargin = "50px",
    // Start loading 50px before element enters viewport
    threshold = 0.01
    // Trigger when 1% of element is visible
  } = options;
  const targetRef = ref(null);
  const isVisible = ref(false);
  const isLoaded = ref(false);
  const error = ref(null);
  let observer = null;
  onMounted(() => {
    if (!targetRef.value) return;
    if (!("IntersectionObserver" in window)) {
      isVisible.value = true;
      return;
    }
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !isVisible.value) {
            isVisible.value = true;
            observer == null ? void 0 : observer.disconnect();
          }
        });
      },
      {
        rootMargin,
        threshold
      }
    );
    observer.observe(targetRef.value);
  });
  onBeforeUnmount(() => {
    if (observer) {
      observer.disconnect();
      observer = null;
    }
  });
  return {
    targetRef,
    isVisible,
    isLoaded,
    error
  };
}
const _hoisted_1 = ["src", "alt", "loading"];
const baseContainerClass = "relative overflow-hidden";
const _sfc_main = {
  __name: "LazyImage",
  props: {
    src: {
      type: String,
      required: true
    },
    alt: {
      type: String,
      default: ""
    },
    containerClass: {
      type: String,
      default: ""
    },
    imgClass: {
      type: String,
      default: "w-full h-full object-cover"
    },
    placeholderClass: {
      type: String,
      default: ""
    },
    errorClass: {
      type: String,
      default: ""
    },
    rootMargin: {
      type: String,
      default: "50px"
    },
    threshold: {
      type: Number,
      default: 0.01
    },
    // Use native loading="lazy" as fallback for browsers without Intersection Observer
    nativeLazy: {
      type: Boolean,
      default: true
    }
  },
  emits: ["load", "error"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const containerClasses = computed(() => {
      var _a;
      const userClasses = (_a = props.containerClass) == null ? void 0 : _a.trim();
      return userClasses ? `${baseContainerClass} ${userClasses}` : baseContainerClass;
    });
    const { targetRef, isVisible, isLoaded, error } = useLazyLoad({
      rootMargin: props.rootMargin,
      threshold: props.threshold
    });
    function handleLoad(event) {
      error.value = null;
      isLoaded.value = true;
      emit("load", event);
    }
    function handleError(event) {
      error.value = event;
      isLoaded.value = true;
      emit("error", event);
    }
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", {
        ref_key: "targetRef",
        ref: targetRef,
        class: normalizeClass(containerClasses.value)
      }, [
        !unref(isLoaded) ? (openBlock(), createElementBlock("div", {
          key: 0,
          class: normalizeClass([
            "absolute inset-0 bg-gray-100 flex items-center justify-center",
            __props.placeholderClass
          ])
        }, [
          renderSlot(_ctx.$slots, "placeholder", {}, () => [
            _cache[0] || (_cache[0] = createBaseVNode("div", { class: "absolute inset-0 bg-gradient-to-r from-gray-100 via-gray-200 to-gray-100 animate-pulse" }, null, -1))
          ], true)
        ], 2)) : createCommentVNode("", true),
        unref(isVisible) ? (openBlock(), createElementBlock("img", {
          key: 1,
          src: __props.src,
          alt: __props.alt,
          class: normalizeClass([
            "transition-opacity duration-300",
            unref(isLoaded) ? "opacity-100" : "opacity-0",
            __props.imgClass
          ]),
          onLoad: handleLoad,
          onError: handleError,
          loading: __props.nativeLazy ? "lazy" : "eager"
        }, null, 42, _hoisted_1)) : createCommentVNode("", true),
        unref(error) ? (openBlock(), createElementBlock("div", {
          key: 2,
          class: normalizeClass(["absolute inset-0 bg-gray-100 flex items-center justify-center", __props.errorClass])
        }, [
          renderSlot(_ctx.$slots, "error", {}, () => [
            _cache[1] || (_cache[1] = createBaseVNode("svg", {
              class: "w-8 h-8 text-gray-400",
              fill: "none",
              stroke: "currentColor",
              viewBox: "0 0 24 24"
            }, [
              createBaseVNode("path", {
                "stroke-linecap": "round",
                "stroke-linejoin": "round",
                "stroke-width": "2",
                d: "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              })
            ], -1))
          ], true)
        ], 2)) : createCommentVNode("", true)
      ], 2);
    };
  }
};
const LazyImage = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-c257926e"]]);
export {
  LazyImage as L
};
