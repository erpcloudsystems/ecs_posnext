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
import { _ as __vitePreload } from "./index-jY-oWqoI.js";
function registerSW(options = {}) {
  const {
    immediate = false,
    onNeedReload,
    onNeedRefresh,
    onOfflineReady,
    onRegistered,
    onRegisteredSW,
    onRegisterError
  } = options;
  let wb;
  let registerPromise;
  const updateServiceWorker = (_reloadPage = true) => __async(this, null, function* () {
    yield registerPromise;
  });
  function register() {
    return __async(this, null, function* () {
      if ("serviceWorker" in navigator) {
        wb = yield __vitePreload(() => __async(this, null, function* () {
          const { Workbox } = yield import("./workbox-window.prod.es5-ZA_CIrj6.js");
          return { Workbox };
        }), true ? [] : void 0).then(({ Workbox }) => {
          return new Workbox("/assets/ecs_posnext/pos/sw.js", { scope: "/assets/ecs_posnext/pos/", type: "classic" });
        }).catch((e) => {
          onRegisterError == null ? void 0 : onRegisterError(e);
          return void 0;
        });
        if (!wb)
          return;
        {
          {
            wb.addEventListener("activated", (event) => {
              if (event.isUpdate || event.isExternal) {
                if (onNeedReload)
                  onNeedReload();
                else
                  window.location.reload();
              }
            });
            wb.addEventListener("installed", (event) => {
              if (!event.isUpdate) {
                onOfflineReady == null ? void 0 : onOfflineReady();
              }
            });
          }
        }
        wb.register({ immediate }).then((r) => {
          if (onRegisteredSW)
            onRegisteredSW("/assets/ecs_posnext/pos/sw.js", r);
          else
            onRegistered == null ? void 0 : onRegistered(r);
        }).catch((e) => {
          onRegisterError == null ? void 0 : onRegisterError(e);
        });
      }
    });
  }
  registerPromise = register();
  return updateServiceWorker;
}
export {
  registerSW
};
