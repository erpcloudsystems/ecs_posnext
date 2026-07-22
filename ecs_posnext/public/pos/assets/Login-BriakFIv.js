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
import { $ as useShift, a1 as reactive, i as ref, j as onMounted, ac as session, A as watch, c as createElementBlock, f as createBaseVNode, t as toDisplayString, q as withModifiers, x as unref, h as createCommentVNode, d as createVNode, J as withDirectives, af as vModelDynamic, y as _sfc_main$1, w as withCtx, r as resolveComponent, ad as useRouter, o as openBlock, e as createTextVNode, ag as ensureCSRFToken, V as offlineWorker } from "./index-jY-oWqoI.js";
import { a as usePOSCartStore, o as usePOSUIStore, q as _sfc_main$2 } from "./posUI-_bFY4ZW7.js";
import "./currency-KPLDlCCc.js";
const _hoisted_1 = { class: "min-h-screen flex flex-col items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8" };
const _hoisted_2 = { class: "max-w-md w-full space-y-8" };
const _hoisted_3 = { class: "text-center" };
const _hoisted_4 = { class: "mt-6 text-3xl font-extrabold text-gray-900" };
const _hoisted_5 = { class: "mt-2 text-sm text-gray-600" };
const _hoisted_6 = { class: "bg-white py-8 px-6 shadow rounded-lg" };
const _hoisted_7 = {
  key: 0,
  class: "rounded-md bg-red-50 p-4"
};
const _hoisted_8 = { class: "flex" };
const _hoisted_9 = { class: "ml-3" };
const _hoisted_10 = { class: "text-sm font-medium text-red-800" };
const _hoisted_11 = { class: "mt-2 text-sm text-red-700" };
const _hoisted_12 = { class: "block" };
const _hoisted_13 = { class: "mb-2 block text-sm leading-4 text-gray-700" };
const _hoisted_14 = { class: "relative" };
const _hoisted_15 = ["type", "placeholder", "disabled"];
const _hoisted_16 = ["disabled", "aria-label"];
const _sfc_main = {
  __name: "Login",
  setup(__props) {
    const router = useRouter();
    const { shiftState } = useShift();
    const cartStore = usePOSCartStore();
    const uiStore = usePOSUIStore();
    const loginForm = reactive({
      email: "",
      password: ""
    });
    const showShiftDialog = ref(false);
    const showPassword = ref(false);
    onMounted(() => {
      loginForm.email = "";
      loginForm.password = "";
      showPassword.value = false;
      if (session.login.error) {
        session.login.reset();
      }
      if (!session.isLoggedIn) {
        showShiftDialog.value = false;
        cartStore.clearCart();
        uiStore.resetAllDialogs();
        shiftState.value = {
          pos_opening_shift: null,
          pos_profile: null,
          company: null,
          isOpen: false
        };
        localStorage.removeItem("pos_shift_data");
      }
    });
    function submit() {
      if (!loginForm.email || !loginForm.password) {
        return;
      }
      session.login.submit({
        email: loginForm.email.trim(),
        password: loginForm.password
      });
    }
    watch(
      () => session.isLoggedIn,
      (isLoggedIn) => __async(this, null, function* () {
        if (isLoggedIn) {
          try {
            console.log("User logged in, initializing CSRF token...");
            yield ensureCSRFToken();
            if (window.csrf_token) {
              yield offlineWorker.setCSRFToken(window.csrf_token);
            }
          } catch (error) {
            console.error("Failed to initialize CSRF token after login:", error);
          }
          showShiftDialog.value = true;
        }
      })
    );
    watch(showShiftDialog, (isOpen, wasOpen) => {
      if (wasOpen === true && isOpen === false && session.isLoggedIn) {
        router.push({ name: "POSSale" });
      }
    });
    function handleShiftOpened() {
      router.push({ name: "POSSale" });
    }
    function handleDialogClosed({ reason }) {
      if (reason === "cancelled" || reason === "resumed") {
        router.push({ name: "POSSale" });
      }
    }
    watch([() => loginForm.email, () => loginForm.password], () => {
      if (session.login.error) {
        session.login.reset();
      }
    });
    return (_ctx, _cache) => {
      const _component_Input = resolveComponent("Input");
      const _component_Button = resolveComponent("Button");
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          createBaseVNode("div", _hoisted_3, [
            createBaseVNode("h2", _hoisted_4, toDisplayString(_ctx.__("Sign in to POS Next")), 1),
            createBaseVNode("p", _hoisted_5, toDisplayString(_ctx.__("Access your point of sale system")), 1)
          ]),
          createBaseVNode("div", _hoisted_6, [
            createBaseVNode("form", {
              class: "space-y-6",
              onSubmit: withModifiers(submit, ["prevent"])
            }, [
              unref(session).login.error ? (openBlock(), createElementBlock("div", _hoisted_7, [
                createBaseVNode("div", _hoisted_8, [
                  _cache[4] || (_cache[4] = createBaseVNode("div", { class: "flex-shrink-0" }, [
                    createBaseVNode("svg", {
                      class: "h-5 w-5 text-red-400",
                      viewBox: "0 0 20 20",
                      fill: "currentColor"
                    }, [
                      createBaseVNode("path", {
                        "fill-rule": "evenodd",
                        d: "M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z",
                        "clip-rule": "evenodd"
                      })
                    ])
                  ], -1)),
                  createBaseVNode("div", _hoisted_9, [
                    createBaseVNode("h3", _hoisted_10, toDisplayString(_ctx.__("Login Failed")), 1),
                    createBaseVNode("div", _hoisted_11, [
                      createBaseVNode("p", null, toDisplayString(unref(session).login.error.messages.join("\n")), 1)
                    ])
                  ])
                ])
              ])) : createCommentVNode("", true),
              createBaseVNode("div", null, [
                createVNode(_component_Input, {
                  modelValue: loginForm.email,
                  "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => loginForm.email = $event),
                  required: "",
                  name: "email",
                  type: "text",
                  placeholder: _ctx.__("Enter your username or email"),
                  label: _ctx.__("User ID / Email"),
                  disabled: unref(session).login.loading
                }, null, 8, ["modelValue", "placeholder", "label", "disabled"])
              ]),
              createBaseVNode("div", null, [
                createBaseVNode("label", _hoisted_12, [
                  createBaseVNode("span", _hoisted_13, toDisplayString(_ctx.__("Password")), 1),
                  createBaseVNode("div", _hoisted_14, [
                    withDirectives(createBaseVNode("input", {
                      "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => loginForm.password = $event),
                      required: "",
                      name: "password",
                      type: showPassword.value ? "text" : "password",
                      placeholder: _ctx.__("Enter your password"),
                      disabled: unref(session).login.loading,
                      class: "form-input block w-full border-gray-400 placeholder-gray-500 pe-10"
                    }, null, 8, _hoisted_15), [
                      [vModelDynamic, loginForm.password]
                    ]),
                    createBaseVNode("button", {
                      type: "button",
                      onClick: _cache[2] || (_cache[2] = ($event) => showPassword.value = !showPassword.value),
                      class: "absolute inset-y-0 end-0 flex items-center pe-3 text-gray-600 hover:text-gray-800 transition-colors focus:outline-none",
                      disabled: unref(session).login.loading,
                      tabindex: "-1",
                      "aria-label": showPassword.value ? _ctx.__("Hide password") : _ctx.__("Show password")
                    }, [
                      createVNode(unref(_sfc_main$1), {
                        name: showPassword.value ? "eye-off" : "eye",
                        class: "h-5 w-5",
                        "stroke-width": 2
                      }, null, 8, ["name"])
                    ], 8, _hoisted_16)
                  ])
                ])
              ]),
              createBaseVNode("div", null, [
                createVNode(_component_Button, {
                  loading: unref(session).login.loading,
                  variant: "solid",
                  class: "w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50",
                  type: "submit"
                }, {
                  default: withCtx(() => [
                    createTextVNode(toDisplayString(unref(session).login.loading ? _ctx.__("Signing in...") : _ctx.__("Sign in")), 1)
                  ]),
                  _: 1
                }, 8, ["loading"])
              ])
            ], 32)
          ])
        ]),
        createVNode(_sfc_main$2, {
          modelValue: showShiftDialog.value,
          "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => showShiftDialog.value = $event),
          onShiftOpened: handleShiftOpened,
          onDialogClosed: handleDialogClosed
        }, null, 8, ["modelValue"])
      ]);
    };
  }
};
export {
  _sfc_main as default
};
