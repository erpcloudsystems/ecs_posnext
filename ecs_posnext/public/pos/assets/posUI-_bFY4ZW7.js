var __defProp = Object.defineProperty;
var __defProps = Object.defineProperties;
var __getOwnPropDescs = Object.getOwnPropertyDescriptors;
var __getOwnPropSymbols = Object.getOwnPropertySymbols;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __propIsEnum = Object.prototype.propertyIsEnumerable;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues = (a, b) => {
  for (var prop in b || (b = {}))
    if (__hasOwnProp.call(b, prop))
      __defNormalProp(a, prop, b[prop]);
  if (__getOwnPropSymbols)
    for (var prop of __getOwnPropSymbols(b)) {
      if (__propIsEnum.call(b, prop))
        __defNormalProp(a, prop, b[prop]);
    }
  return a;
};
var __spreadProps = (a, b) => __defProps(a, __getOwnPropDescs(b));
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
import { P as defineStore, i as ref, l as computed, G as createResource, ah as useBootstrapStore, j as onMounted, o as openBlock, m as createBlock, ai as mergeProps, aj as resolveDynamicComponent, $ as useShift, W as storeToRefs, A as watch, a1 as reactive, w as withCtx, f as createBaseVNode, d as createVNode, x as unref, I as _sfc_main$3, e as createTextVNode, t as toDisplayString, c as createElementBlock, h as createCommentVNode, u as normalizeClass, J as withDirectives, F as Fragment, B as renderList, ak as vShow, M as Input, L as Dialog, v as call, Q as logger, D as db, a2 as offlineState, al as getSetting, E as setSetting, H as isOffline$1, am as toRaw, V as offlineWorker, a5 as call$1, S as nextTick, O as useToast, U as readonly } from "./index-jY-oWqoI.js";
import { roundCurrency } from "./currency-KPLDlCCc.js";
/*! @license DOMPurify 3.4.10 | (c) Cure53 and other contributors | Released under the Apache license 2.0 and Mozilla Public License 2.0 | github.com/cure53/DOMPurify/blob/3.4.10/LICENSE */
function _arrayLikeToArray(r, a) {
  (null == a || a > r.length) && (a = r.length);
  for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e];
  return n;
}
function _arrayWithHoles(r) {
  if (Array.isArray(r)) return r;
}
function _iterableToArrayLimit(r, l) {
  var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"];
  if (null != t) {
    var e, n, i, u, a = [], f = true, o = false;
    try {
      if (i = (t = t.call(r)).next, 0 === l) ;
      else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = true) ;
    } catch (r2) {
      o = true, n = r2;
    } finally {
      try {
        if (!f && null != t.return && (u = t.return(), Object(u) !== u)) return;
      } finally {
        if (o) throw n;
      }
    }
    return a;
  }
}
function _nonIterableRest() {
  throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function _slicedToArray(r, e) {
  return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest();
}
function _unsupportedIterableToArray(r, a) {
  if (r) {
    if ("string" == typeof r) return _arrayLikeToArray(r, a);
    var t = {}.toString.call(r).slice(8, -1);
    return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0;
  }
}
const entries = Object.entries, setPrototypeOf = Object.setPrototypeOf, isFrozen = Object.isFrozen, getPrototypeOf = Object.getPrototypeOf, getOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
let freeze = Object.freeze, seal = Object.seal, create = Object.create;
let _ref = typeof Reflect !== "undefined" && Reflect, apply = _ref.apply, construct = _ref.construct;
if (!freeze) {
  freeze = function freeze2(x) {
    return x;
  };
}
if (!seal) {
  seal = function seal2(x) {
    return x;
  };
}
if (!apply) {
  apply = function apply2(func, thisArg) {
    for (var _len = arguments.length, args = new Array(_len > 2 ? _len - 2 : 0), _key = 2; _key < _len; _key++) {
      args[_key - 2] = arguments[_key];
    }
    return func.apply(thisArg, args);
  };
}
if (!construct) {
  construct = function construct2(Func) {
    for (var _len2 = arguments.length, args = new Array(_len2 > 1 ? _len2 - 1 : 0), _key2 = 1; _key2 < _len2; _key2++) {
      args[_key2 - 1] = arguments[_key2];
    }
    return new Func(...args);
  };
}
const arrayForEach = unapply(Array.prototype.forEach);
const arrayLastIndexOf = unapply(Array.prototype.lastIndexOf);
const arrayPop = unapply(Array.prototype.pop);
const arrayPush = unapply(Array.prototype.push);
const arraySplice = unapply(Array.prototype.splice);
const arrayIsArray = Array.isArray;
const stringToLowerCase = unapply(String.prototype.toLowerCase);
const stringToString = unapply(String.prototype.toString);
const stringMatch = unapply(String.prototype.match);
const stringReplace = unapply(String.prototype.replace);
const stringIndexOf = unapply(String.prototype.indexOf);
const stringTrim = unapply(String.prototype.trim);
const numberToString = unapply(Number.prototype.toString);
const booleanToString = unapply(Boolean.prototype.toString);
const bigintToString = typeof BigInt === "undefined" ? null : unapply(BigInt.prototype.toString);
const symbolToString = typeof Symbol === "undefined" ? null : unapply(Symbol.prototype.toString);
const objectHasOwnProperty = unapply(Object.prototype.hasOwnProperty);
const objectToString = unapply(Object.prototype.toString);
const regExpTest = unapply(RegExp.prototype.test);
const typeErrorCreate = unconstruct(TypeError);
function unapply(func) {
  return function(thisArg) {
    if (thisArg instanceof RegExp) {
      thisArg.lastIndex = 0;
    }
    for (var _len3 = arguments.length, args = new Array(_len3 > 1 ? _len3 - 1 : 0), _key3 = 1; _key3 < _len3; _key3++) {
      args[_key3 - 1] = arguments[_key3];
    }
    return apply(func, thisArg, args);
  };
}
function unconstruct(Func) {
  return function() {
    for (var _len4 = arguments.length, args = new Array(_len4), _key4 = 0; _key4 < _len4; _key4++) {
      args[_key4] = arguments[_key4];
    }
    return construct(Func, args);
  };
}
function addToSet(set, array) {
  let transformCaseFunc = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : stringToLowerCase;
  if (setPrototypeOf) {
    setPrototypeOf(set, null);
  }
  if (!arrayIsArray(array)) {
    return set;
  }
  let l = array.length;
  while (l--) {
    let element = array[l];
    if (typeof element === "string") {
      const lcElement = transformCaseFunc(element);
      if (lcElement !== element) {
        if (!isFrozen(array)) {
          array[l] = lcElement;
        }
        element = lcElement;
      }
    }
    set[element] = true;
  }
  return set;
}
function cleanArray(array) {
  for (let index = 0; index < array.length; index++) {
    const isPropertyExist = objectHasOwnProperty(array, index);
    if (!isPropertyExist) {
      array[index] = null;
    }
  }
  return array;
}
function clone(object) {
  const newObject = create(null);
  for (const _ref2 of entries(object)) {
    var _ref3 = _slicedToArray(_ref2, 2);
    const property = _ref3[0];
    const value = _ref3[1];
    const isPropertyExist = objectHasOwnProperty(object, property);
    if (isPropertyExist) {
      if (arrayIsArray(value)) {
        newObject[property] = cleanArray(value);
      } else if (value && typeof value === "object" && value.constructor === Object) {
        newObject[property] = clone(value);
      } else {
        newObject[property] = value;
      }
    }
  }
  return newObject;
}
function stringifyValue(value) {
  switch (typeof value) {
    case "string": {
      return value;
    }
    case "number": {
      return numberToString(value);
    }
    case "boolean": {
      return booleanToString(value);
    }
    case "bigint": {
      return bigintToString ? bigintToString(value) : "0";
    }
    case "symbol": {
      return symbolToString ? symbolToString(value) : "Symbol()";
    }
    case "undefined": {
      return objectToString(value);
    }
    case "function":
    case "object": {
      if (value === null) {
        return objectToString(value);
      }
      const valueAsRecord = value;
      const valueToString = lookupGetter(valueAsRecord, "toString");
      if (typeof valueToString === "function") {
        const stringified = valueToString(valueAsRecord);
        return typeof stringified === "string" ? stringified : objectToString(stringified);
      }
      return objectToString(value);
    }
    default: {
      return objectToString(value);
    }
  }
}
function lookupGetter(object, prop) {
  while (object !== null) {
    const desc = getOwnPropertyDescriptor(object, prop);
    if (desc) {
      if (desc.get) {
        return unapply(desc.get);
      }
      if (typeof desc.value === "function") {
        return unapply(desc.value);
      }
    }
    object = getPrototypeOf(object);
  }
  function fallbackValue() {
    return null;
  }
  return fallbackValue;
}
function isRegex(value) {
  try {
    regExpTest(value, "");
    return true;
  } catch (_unused) {
    return false;
  }
}
const html$1 = freeze(["a", "abbr", "acronym", "address", "area", "article", "aside", "audio", "b", "bdi", "bdo", "big", "blink", "blockquote", "body", "br", "button", "canvas", "caption", "center", "cite", "code", "col", "colgroup", "content", "data", "datalist", "dd", "decorator", "del", "details", "dfn", "dialog", "dir", "div", "dl", "dt", "element", "em", "fieldset", "figcaption", "figure", "font", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "head", "header", "hgroup", "hr", "html", "i", "img", "input", "ins", "kbd", "label", "legend", "li", "main", "map", "mark", "marquee", "menu", "menuitem", "meter", "nav", "nobr", "ol", "optgroup", "option", "output", "p", "picture", "pre", "progress", "q", "rp", "rt", "ruby", "s", "samp", "search", "section", "select", "shadow", "slot", "small", "source", "spacer", "span", "strike", "strong", "style", "sub", "summary", "sup", "table", "tbody", "td", "template", "textarea", "tfoot", "th", "thead", "time", "tr", "track", "tt", "u", "ul", "var", "video", "wbr"]);
const svg$1 = freeze(["svg", "a", "altglyph", "altglyphdef", "altglyphitem", "animatecolor", "animatemotion", "animatetransform", "circle", "clippath", "defs", "desc", "ellipse", "enterkeyhint", "exportparts", "filter", "font", "g", "glyph", "glyphref", "hkern", "image", "inputmode", "line", "lineargradient", "marker", "mask", "metadata", "mpath", "part", "path", "pattern", "polygon", "polyline", "radialgradient", "rect", "stop", "style", "switch", "symbol", "text", "textpath", "title", "tref", "tspan", "view", "vkern"]);
const svgFilters = freeze(["feBlend", "feColorMatrix", "feComponentTransfer", "feComposite", "feConvolveMatrix", "feDiffuseLighting", "feDisplacementMap", "feDistantLight", "feDropShadow", "feFlood", "feFuncA", "feFuncB", "feFuncG", "feFuncR", "feGaussianBlur", "feImage", "feMerge", "feMergeNode", "feMorphology", "feOffset", "fePointLight", "feSpecularLighting", "feSpotLight", "feTile", "feTurbulence"]);
const svgDisallowed = freeze(["animate", "color-profile", "cursor", "discard", "font-face", "font-face-format", "font-face-name", "font-face-src", "font-face-uri", "foreignobject", "hatch", "hatchpath", "mesh", "meshgradient", "meshpatch", "meshrow", "missing-glyph", "script", "set", "solidcolor", "unknown", "use"]);
const mathMl$1 = freeze(["math", "menclose", "merror", "mfenced", "mfrac", "mglyph", "mi", "mlabeledtr", "mmultiscripts", "mn", "mo", "mover", "mpadded", "mphantom", "mroot", "mrow", "ms", "mspace", "msqrt", "mstyle", "msub", "msup", "msubsup", "mtable", "mtd", "mtext", "mtr", "munder", "munderover", "mprescripts"]);
const mathMlDisallowed = freeze(["maction", "maligngroup", "malignmark", "mlongdiv", "mscarries", "mscarry", "msgroup", "mstack", "msline", "msrow", "semantics", "annotation", "annotation-xml", "mprescripts", "none"]);
const text = freeze(["#text"]);
const html = freeze(["accept", "action", "align", "alt", "autocapitalize", "autocomplete", "autopictureinpicture", "autoplay", "background", "bgcolor", "border", "capture", "cellpadding", "cellspacing", "checked", "cite", "class", "clear", "color", "cols", "colspan", "command", "commandfor", "controls", "controlslist", "coords", "crossorigin", "datetime", "decoding", "default", "dir", "disabled", "disablepictureinpicture", "disableremoteplayback", "download", "draggable", "enctype", "enterkeyhint", "exportparts", "face", "for", "headers", "height", "hidden", "high", "href", "hreflang", "id", "inert", "inputmode", "integrity", "ismap", "kind", "label", "lang", "list", "loading", "loop", "low", "max", "maxlength", "media", "method", "min", "minlength", "multiple", "muted", "name", "nonce", "noshade", "novalidate", "nowrap", "open", "optimum", "part", "pattern", "placeholder", "playsinline", "popover", "popovertarget", "popovertargetaction", "poster", "preload", "pubdate", "radiogroup", "readonly", "rel", "required", "rev", "reversed", "role", "rows", "rowspan", "spellcheck", "scope", "selected", "shape", "size", "sizes", "slot", "span", "srclang", "start", "src", "srcset", "step", "style", "summary", "tabindex", "title", "translate", "type", "usemap", "valign", "value", "width", "wrap", "xmlns"]);
const svg = freeze(["accent-height", "accumulate", "additive", "alignment-baseline", "amplitude", "ascent", "attributename", "attributetype", "azimuth", "basefrequency", "baseline-shift", "begin", "bias", "by", "class", "clip", "clippathunits", "clip-path", "clip-rule", "color", "color-interpolation", "color-interpolation-filters", "color-profile", "color-rendering", "cx", "cy", "d", "dx", "dy", "diffuseconstant", "direction", "display", "divisor", "dur", "edgemode", "elevation", "end", "exponent", "fill", "fill-opacity", "fill-rule", "filter", "filterunits", "flood-color", "flood-opacity", "font-family", "font-size", "font-size-adjust", "font-stretch", "font-style", "font-variant", "font-weight", "fx", "fy", "g1", "g2", "glyph-name", "glyphref", "gradientunits", "gradienttransform", "height", "href", "id", "image-rendering", "in", "in2", "intercept", "k", "k1", "k2", "k3", "k4", "kerning", "keypoints", "keysplines", "keytimes", "lang", "lengthadjust", "letter-spacing", "kernelmatrix", "kernelunitlength", "lighting-color", "local", "marker-end", "marker-mid", "marker-start", "markerheight", "markerunits", "markerwidth", "maskcontentunits", "maskunits", "max", "mask", "mask-type", "media", "method", "mode", "min", "name", "numoctaves", "offset", "operator", "opacity", "order", "orient", "orientation", "origin", "overflow", "paint-order", "path", "pathlength", "patterncontentunits", "patterntransform", "patternunits", "points", "preservealpha", "preserveaspectratio", "primitiveunits", "r", "rx", "ry", "radius", "refx", "refy", "repeatcount", "repeatdur", "restart", "result", "rotate", "scale", "seed", "shape-rendering", "slope", "specularconstant", "specularexponent", "spreadmethod", "startoffset", "stddeviation", "stitchtiles", "stop-color", "stop-opacity", "stroke-dasharray", "stroke-dashoffset", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-opacity", "stroke", "stroke-width", "style", "surfacescale", "systemlanguage", "tabindex", "tablevalues", "targetx", "targety", "transform", "transform-origin", "text-anchor", "text-decoration", "text-rendering", "textlength", "type", "u1", "u2", "unicode", "values", "viewbox", "visibility", "version", "vert-adv-y", "vert-origin-x", "vert-origin-y", "width", "word-spacing", "wrap", "writing-mode", "xchannelselector", "ychannelselector", "x", "x1", "x2", "xmlns", "y", "y1", "y2", "z", "zoomandpan"]);
const mathMl = freeze(["accent", "accentunder", "align", "bevelled", "close", "columnalign", "columnlines", "columnspacing", "columnspan", "denomalign", "depth", "dir", "display", "displaystyle", "encoding", "fence", "frame", "height", "href", "id", "largeop", "length", "linethickness", "lquote", "lspace", "mathbackground", "mathcolor", "mathsize", "mathvariant", "maxsize", "minsize", "movablelimits", "notation", "numalign", "open", "rowalign", "rowlines", "rowspacing", "rowspan", "rspace", "rquote", "scriptlevel", "scriptminsize", "scriptsizemultiplier", "selection", "separator", "separators", "stretchy", "subscriptshift", "supscriptshift", "symmetric", "voffset", "width", "xmlns"]);
const xml = freeze(["xlink:href", "xml:id", "xlink:title", "xml:space", "xmlns:xlink"]);
const MUSTACHE_EXPR = seal(/{{[\w\W]*|^[\w\W]*}}/g);
const ERB_EXPR = seal(/<%[\w\W]*|^[\w\W]*%>/g);
const TMPLIT_EXPR = seal(/\${[\w\W]*/g);
const DATA_ATTR = seal(/^data-[\-\w.\u00B7-\uFFFF]+$/);
const ARIA_ATTR = seal(/^aria-[\-\w]+$/);
const IS_ALLOWED_URI = seal(
  /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp|matrix):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i
  // eslint-disable-line no-useless-escape
);
const IS_SCRIPT_OR_DATA = seal(/^(?:\w+script|data):/i);
const ATTR_WHITESPACE = seal(
  /[\u0000-\u0020\u00A0\u1680\u180E\u2000-\u2029\u205F\u3000]/g
  // eslint-disable-line no-control-regex
);
const DOCTYPE_NAME = seal(/^html$/i);
const CUSTOM_ELEMENT = seal(/^[a-z][.\w]*(-[.\w]+)+$/i);
const ELEMENT_MARKUP_PROBE = seal(/<[/\w!]/g);
const COMMENT_MARKUP_PROBE = seal(/<[/\w]/g);
const FALLBACK_TAG_CLOSE = seal(/<\/no(script|embed|frames)/i);
const SELF_CLOSING_TAG = seal(/\/>/i);
const NODE_TYPE = {
  element: 1,
  attribute: 2,
  text: 3,
  cdataSection: 4,
  entityReference: 5,
  // Deprecated
  entityNode: 6,
  // Deprecated
  processingInstruction: 7,
  comment: 8,
  document: 9,
  documentType: 10,
  documentFragment: 11,
  notation: 12
  // Deprecated
};
const getGlobal = function getGlobal2() {
  return typeof window === "undefined" ? null : window;
};
const _createTrustedTypesPolicy = function _createTrustedTypesPolicy2(trustedTypes, purifyHostElement) {
  if (typeof trustedTypes !== "object" || typeof trustedTypes.createPolicy !== "function") {
    return null;
  }
  let suffix = null;
  const ATTR_NAME = "data-tt-policy-suffix";
  if (purifyHostElement && purifyHostElement.hasAttribute(ATTR_NAME)) {
    suffix = purifyHostElement.getAttribute(ATTR_NAME);
  }
  const policyName = "dompurify" + (suffix ? "#" + suffix : "");
  try {
    return trustedTypes.createPolicy(policyName, {
      createHTML(html2) {
        return html2;
      },
      createScriptURL(scriptUrl) {
        return scriptUrl;
      }
    });
  } catch (_) {
    console.warn("TrustedTypes policy " + policyName + " could not be created.");
    return null;
  }
};
const _createHooksMap = function _createHooksMap2() {
  return {
    afterSanitizeAttributes: [],
    afterSanitizeElements: [],
    afterSanitizeShadowDOM: [],
    beforeSanitizeAttributes: [],
    beforeSanitizeElements: [],
    beforeSanitizeShadowDOM: [],
    uponSanitizeAttribute: [],
    uponSanitizeElement: [],
    uponSanitizeShadowNode: []
  };
};
const _resolveSetOption = function _resolveSetOption2(cfg, key, fallback, options) {
  return objectHasOwnProperty(cfg, key) && arrayIsArray(cfg[key]) ? addToSet(options.base ? clone(options.base) : {}, cfg[key], options.transform) : fallback;
};
function createDOMPurify() {
  let window2 = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : getGlobal();
  const DOMPurify = (root) => createDOMPurify(root);
  DOMPurify.version = "3.4.10";
  DOMPurify.removed = [];
  if (!window2 || !window2.document || window2.document.nodeType !== NODE_TYPE.document || !window2.Element) {
    DOMPurify.isSupported = false;
    return DOMPurify;
  }
  let document2 = window2.document;
  const originalDocument = document2;
  const currentScript = originalDocument.currentScript;
  window2.DocumentFragment;
  const HTMLTemplateElement = window2.HTMLTemplateElement, Node = window2.Node, Element = window2.Element, NodeFilter = window2.NodeFilter, _window$NamedNodeMap = window2.NamedNodeMap;
  _window$NamedNodeMap === void 0 ? window2.NamedNodeMap || window2.MozNamedAttrMap : _window$NamedNodeMap;
  window2.HTMLFormElement;
  const DOMParser = window2.DOMParser, trustedTypes = window2.trustedTypes;
  const ElementPrototype = Element.prototype;
  const cloneNode = lookupGetter(ElementPrototype, "cloneNode");
  const remove = lookupGetter(ElementPrototype, "remove");
  const getNextSibling = lookupGetter(ElementPrototype, "nextSibling");
  const getChildNodes = lookupGetter(ElementPrototype, "childNodes");
  const getParentNode = lookupGetter(ElementPrototype, "parentNode");
  const getShadowRoot = lookupGetter(ElementPrototype, "shadowRoot");
  const getAttributes = lookupGetter(ElementPrototype, "attributes");
  const getNodeType = Node && Node.prototype ? lookupGetter(Node.prototype, "nodeType") : null;
  const getNodeName = Node && Node.prototype ? lookupGetter(Node.prototype, "nodeName") : null;
  if (typeof HTMLTemplateElement === "function") {
    const template = document2.createElement("template");
    if (template.content && template.content.ownerDocument) {
      document2 = template.content.ownerDocument;
    }
  }
  let trustedTypesPolicy;
  let emptyHTML = "";
  let defaultTrustedTypesPolicy;
  let defaultTrustedTypesPolicyResolved = false;
  let IN_TRUSTED_TYPES_POLICY = 0;
  const _assertNotInTrustedTypesPolicy = function _assertNotInTrustedTypesPolicy2() {
    if (IN_TRUSTED_TYPES_POLICY > 0) {
      throw typeErrorCreate('A configured TRUSTED_TYPES_POLICY callback (createHTML or createScriptURL) must not call DOMPurify.sanitize, as that causes infinite recursion. Do not pass a policy whose callbacks wrap DOMPurify as TRUSTED_TYPES_POLICY; see the "DOMPurify and Trusted Types" section of the README.');
    }
  };
  const _createTrustedHTML = function _createTrustedHTML2(html2) {
    _assertNotInTrustedTypesPolicy();
    IN_TRUSTED_TYPES_POLICY++;
    try {
      return trustedTypesPolicy.createHTML(html2);
    } finally {
      IN_TRUSTED_TYPES_POLICY--;
    }
  };
  const _createTrustedScriptURL = function _createTrustedScriptURL2(scriptUrl) {
    _assertNotInTrustedTypesPolicy();
    IN_TRUSTED_TYPES_POLICY++;
    try {
      return trustedTypesPolicy.createScriptURL(scriptUrl);
    } finally {
      IN_TRUSTED_TYPES_POLICY--;
    }
  };
  const _getDefaultTrustedTypesPolicy = function _getDefaultTrustedTypesPolicy2() {
    if (!defaultTrustedTypesPolicyResolved) {
      defaultTrustedTypesPolicy = _createTrustedTypesPolicy(trustedTypes, currentScript);
      defaultTrustedTypesPolicyResolved = true;
    }
    return defaultTrustedTypesPolicy;
  };
  const _document = document2, implementation = _document.implementation, createNodeIterator = _document.createNodeIterator, createDocumentFragment = _document.createDocumentFragment, getElementsByTagName = _document.getElementsByTagName;
  const importNode = originalDocument.importNode;
  let hooks = _createHooksMap();
  DOMPurify.isSupported = typeof entries === "function" && typeof getParentNode === "function" && implementation && implementation.createHTMLDocument !== void 0;
  const MUSTACHE_EXPR$1 = MUSTACHE_EXPR, ERB_EXPR$1 = ERB_EXPR, TMPLIT_EXPR$1 = TMPLIT_EXPR, DATA_ATTR$1 = DATA_ATTR, ARIA_ATTR$1 = ARIA_ATTR, IS_SCRIPT_OR_DATA$1 = IS_SCRIPT_OR_DATA, ATTR_WHITESPACE$1 = ATTR_WHITESPACE, CUSTOM_ELEMENT$1 = CUSTOM_ELEMENT;
  let IS_ALLOWED_URI$1 = IS_ALLOWED_URI;
  let ALLOWED_TAGS = null;
  const DEFAULT_ALLOWED_TAGS = addToSet({}, [...html$1, ...svg$1, ...svgFilters, ...mathMl$1, ...text]);
  let ALLOWED_ATTR = null;
  const DEFAULT_ALLOWED_ATTR = addToSet({}, [...html, ...svg, ...mathMl, ...xml]);
  let CUSTOM_ELEMENT_HANDLING = Object.seal(create(null, {
    tagNameCheck: {
      writable: true,
      configurable: false,
      enumerable: true,
      value: null
    },
    attributeNameCheck: {
      writable: true,
      configurable: false,
      enumerable: true,
      value: null
    },
    allowCustomizedBuiltInElements: {
      writable: true,
      configurable: false,
      enumerable: true,
      value: false
    }
  }));
  let FORBID_TAGS = null;
  let FORBID_ATTR = null;
  const EXTRA_ELEMENT_HANDLING = Object.seal(create(null, {
    tagCheck: {
      writable: true,
      configurable: false,
      enumerable: true,
      value: null
    },
    attributeCheck: {
      writable: true,
      configurable: false,
      enumerable: true,
      value: null
    }
  }));
  let ALLOW_ARIA_ATTR = true;
  let ALLOW_DATA_ATTR = true;
  let ALLOW_UNKNOWN_PROTOCOLS = false;
  let ALLOW_SELF_CLOSE_IN_ATTR = true;
  let SAFE_FOR_TEMPLATES = false;
  let SAFE_FOR_XML = true;
  let WHOLE_DOCUMENT = false;
  let SET_CONFIG = false;
  let FORCE_BODY = false;
  let RETURN_DOM = false;
  let RETURN_DOM_FRAGMENT = false;
  let RETURN_TRUSTED_TYPE = false;
  let SANITIZE_DOM = true;
  let SANITIZE_NAMED_PROPS = false;
  const SANITIZE_NAMED_PROPS_PREFIX = "user-content-";
  let KEEP_CONTENT = true;
  let IN_PLACE = false;
  let USE_PROFILES = {};
  let FORBID_CONTENTS = null;
  const DEFAULT_FORBID_CONTENTS = addToSet({}, [
    "annotation-xml",
    "audio",
    "colgroup",
    "desc",
    "foreignobject",
    "head",
    "iframe",
    "math",
    "mi",
    "mn",
    "mo",
    "ms",
    "mtext",
    "noembed",
    "noframes",
    "noscript",
    "plaintext",
    "script",
    // <selectedcontent> mirrors the selected <option>'s subtree, cloned by
    // the UA (customizable <select>) — including any on* handlers — and the
    // engine re-mirrors synchronously whenever a removal changes which
    // option/selectedcontent is current, even inside DOMPurify's inert
    // DOMParser document. Hoisting its children on removal re-inserts a fresh
    // mirror target ahead of the walk, which the engine refills, looping
    // forever (DoS) and amplifying output. Dropping its content on removal
    // (rather than hoisting) breaks that cascade; the content is a duplicate
    // of the option, which is sanitized on its own. See campaign-3 F1/F6.
    "selectedcontent",
    "style",
    "svg",
    "template",
    "thead",
    "title",
    "video",
    "xmp"
  ]);
  let DATA_URI_TAGS = null;
  const DEFAULT_DATA_URI_TAGS = addToSet({}, ["audio", "video", "img", "source", "image", "track"]);
  let URI_SAFE_ATTRIBUTES = null;
  const DEFAULT_URI_SAFE_ATTRIBUTES = addToSet({}, ["alt", "class", "for", "id", "label", "name", "pattern", "placeholder", "role", "summary", "title", "value", "style", "xmlns"]);
  const MATHML_NAMESPACE = "http://www.w3.org/1998/Math/MathML";
  const SVG_NAMESPACE = "http://www.w3.org/2000/svg";
  const HTML_NAMESPACE = "http://www.w3.org/1999/xhtml";
  let NAMESPACE = HTML_NAMESPACE;
  let IS_EMPTY_INPUT = false;
  let ALLOWED_NAMESPACES = null;
  const DEFAULT_ALLOWED_NAMESPACES = addToSet({}, [MATHML_NAMESPACE, SVG_NAMESPACE, HTML_NAMESPACE], stringToString);
  const DEFAULT_MATHML_TEXT_INTEGRATION_POINTS = freeze(["mi", "mo", "mn", "ms", "mtext"]);
  let MATHML_TEXT_INTEGRATION_POINTS = addToSet({}, DEFAULT_MATHML_TEXT_INTEGRATION_POINTS);
  const DEFAULT_HTML_INTEGRATION_POINTS = freeze(["annotation-xml"]);
  let HTML_INTEGRATION_POINTS = addToSet({}, DEFAULT_HTML_INTEGRATION_POINTS);
  const COMMON_SVG_AND_HTML_ELEMENTS = addToSet({}, ["title", "style", "font", "a", "script"]);
  let PARSER_MEDIA_TYPE = null;
  const SUPPORTED_PARSER_MEDIA_TYPES = ["application/xhtml+xml", "text/html"];
  const DEFAULT_PARSER_MEDIA_TYPE = "text/html";
  let transformCaseFunc = null;
  let CONFIG = null;
  const formElement = document2.createElement("form");
  const isRegexOrFunction = function isRegexOrFunction2(testValue) {
    return testValue instanceof RegExp || testValue instanceof Function;
  };
  const _parseConfig = function _parseConfig2() {
    let cfg = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : {};
    if (CONFIG && CONFIG === cfg) {
      return;
    }
    if (!cfg || typeof cfg !== "object") {
      cfg = {};
    }
    cfg = clone(cfg);
    PARSER_MEDIA_TYPE = // eslint-disable-next-line unicorn/prefer-includes
    SUPPORTED_PARSER_MEDIA_TYPES.indexOf(cfg.PARSER_MEDIA_TYPE) === -1 ? DEFAULT_PARSER_MEDIA_TYPE : cfg.PARSER_MEDIA_TYPE;
    transformCaseFunc = PARSER_MEDIA_TYPE === "application/xhtml+xml" ? stringToString : stringToLowerCase;
    ALLOWED_TAGS = _resolveSetOption(cfg, "ALLOWED_TAGS", DEFAULT_ALLOWED_TAGS, {
      transform: transformCaseFunc
    });
    ALLOWED_ATTR = _resolveSetOption(cfg, "ALLOWED_ATTR", DEFAULT_ALLOWED_ATTR, {
      transform: transformCaseFunc
    });
    ALLOWED_NAMESPACES = _resolveSetOption(cfg, "ALLOWED_NAMESPACES", DEFAULT_ALLOWED_NAMESPACES, {
      transform: stringToString
    });
    URI_SAFE_ATTRIBUTES = _resolveSetOption(cfg, "ADD_URI_SAFE_ATTR", DEFAULT_URI_SAFE_ATTRIBUTES, {
      transform: transformCaseFunc,
      base: DEFAULT_URI_SAFE_ATTRIBUTES
    });
    DATA_URI_TAGS = _resolveSetOption(cfg, "ADD_DATA_URI_TAGS", DEFAULT_DATA_URI_TAGS, {
      transform: transformCaseFunc,
      base: DEFAULT_DATA_URI_TAGS
    });
    FORBID_CONTENTS = _resolveSetOption(cfg, "FORBID_CONTENTS", DEFAULT_FORBID_CONTENTS, {
      transform: transformCaseFunc
    });
    FORBID_TAGS = _resolveSetOption(cfg, "FORBID_TAGS", clone({}), {
      transform: transformCaseFunc
    });
    FORBID_ATTR = _resolveSetOption(cfg, "FORBID_ATTR", clone({}), {
      transform: transformCaseFunc
    });
    USE_PROFILES = objectHasOwnProperty(cfg, "USE_PROFILES") ? cfg.USE_PROFILES && typeof cfg.USE_PROFILES === "object" ? clone(cfg.USE_PROFILES) : cfg.USE_PROFILES : false;
    ALLOW_ARIA_ATTR = cfg.ALLOW_ARIA_ATTR !== false;
    ALLOW_DATA_ATTR = cfg.ALLOW_DATA_ATTR !== false;
    ALLOW_UNKNOWN_PROTOCOLS = cfg.ALLOW_UNKNOWN_PROTOCOLS || false;
    ALLOW_SELF_CLOSE_IN_ATTR = cfg.ALLOW_SELF_CLOSE_IN_ATTR !== false;
    SAFE_FOR_TEMPLATES = cfg.SAFE_FOR_TEMPLATES || false;
    SAFE_FOR_XML = cfg.SAFE_FOR_XML !== false;
    WHOLE_DOCUMENT = cfg.WHOLE_DOCUMENT || false;
    RETURN_DOM = cfg.RETURN_DOM || false;
    RETURN_DOM_FRAGMENT = cfg.RETURN_DOM_FRAGMENT || false;
    RETURN_TRUSTED_TYPE = cfg.RETURN_TRUSTED_TYPE || false;
    FORCE_BODY = cfg.FORCE_BODY || false;
    SANITIZE_DOM = cfg.SANITIZE_DOM !== false;
    SANITIZE_NAMED_PROPS = cfg.SANITIZE_NAMED_PROPS || false;
    KEEP_CONTENT = cfg.KEEP_CONTENT !== false;
    IN_PLACE = cfg.IN_PLACE || false;
    IS_ALLOWED_URI$1 = isRegex(cfg.ALLOWED_URI_REGEXP) ? cfg.ALLOWED_URI_REGEXP : IS_ALLOWED_URI;
    NAMESPACE = typeof cfg.NAMESPACE === "string" ? cfg.NAMESPACE : HTML_NAMESPACE;
    MATHML_TEXT_INTEGRATION_POINTS = objectHasOwnProperty(cfg, "MATHML_TEXT_INTEGRATION_POINTS") && cfg.MATHML_TEXT_INTEGRATION_POINTS && typeof cfg.MATHML_TEXT_INTEGRATION_POINTS === "object" ? clone(cfg.MATHML_TEXT_INTEGRATION_POINTS) : addToSet({}, DEFAULT_MATHML_TEXT_INTEGRATION_POINTS);
    HTML_INTEGRATION_POINTS = objectHasOwnProperty(cfg, "HTML_INTEGRATION_POINTS") && cfg.HTML_INTEGRATION_POINTS && typeof cfg.HTML_INTEGRATION_POINTS === "object" ? clone(cfg.HTML_INTEGRATION_POINTS) : addToSet({}, DEFAULT_HTML_INTEGRATION_POINTS);
    const customElementHandling = objectHasOwnProperty(cfg, "CUSTOM_ELEMENT_HANDLING") && cfg.CUSTOM_ELEMENT_HANDLING && typeof cfg.CUSTOM_ELEMENT_HANDLING === "object" ? clone(cfg.CUSTOM_ELEMENT_HANDLING) : create(null);
    CUSTOM_ELEMENT_HANDLING = create(null);
    if (objectHasOwnProperty(customElementHandling, "tagNameCheck") && isRegexOrFunction(customElementHandling.tagNameCheck)) {
      CUSTOM_ELEMENT_HANDLING.tagNameCheck = customElementHandling.tagNameCheck;
    }
    if (objectHasOwnProperty(customElementHandling, "attributeNameCheck") && isRegexOrFunction(customElementHandling.attributeNameCheck)) {
      CUSTOM_ELEMENT_HANDLING.attributeNameCheck = customElementHandling.attributeNameCheck;
    }
    if (objectHasOwnProperty(customElementHandling, "allowCustomizedBuiltInElements") && typeof customElementHandling.allowCustomizedBuiltInElements === "boolean") {
      CUSTOM_ELEMENT_HANDLING.allowCustomizedBuiltInElements = customElementHandling.allowCustomizedBuiltInElements;
    }
    seal(CUSTOM_ELEMENT_HANDLING);
    if (SAFE_FOR_TEMPLATES) {
      ALLOW_DATA_ATTR = false;
    }
    if (RETURN_DOM_FRAGMENT) {
      RETURN_DOM = true;
    }
    if (USE_PROFILES) {
      ALLOWED_TAGS = addToSet({}, text);
      ALLOWED_ATTR = create(null);
      if (USE_PROFILES.html === true) {
        addToSet(ALLOWED_TAGS, html$1);
        addToSet(ALLOWED_ATTR, html);
      }
      if (USE_PROFILES.svg === true) {
        addToSet(ALLOWED_TAGS, svg$1);
        addToSet(ALLOWED_ATTR, svg);
        addToSet(ALLOWED_ATTR, xml);
      }
      if (USE_PROFILES.svgFilters === true) {
        addToSet(ALLOWED_TAGS, svgFilters);
        addToSet(ALLOWED_ATTR, svg);
        addToSet(ALLOWED_ATTR, xml);
      }
      if (USE_PROFILES.mathMl === true) {
        addToSet(ALLOWED_TAGS, mathMl$1);
        addToSet(ALLOWED_ATTR, mathMl);
        addToSet(ALLOWED_ATTR, xml);
      }
    }
    EXTRA_ELEMENT_HANDLING.tagCheck = null;
    EXTRA_ELEMENT_HANDLING.attributeCheck = null;
    if (objectHasOwnProperty(cfg, "ADD_TAGS")) {
      if (typeof cfg.ADD_TAGS === "function") {
        EXTRA_ELEMENT_HANDLING.tagCheck = cfg.ADD_TAGS;
      } else if (arrayIsArray(cfg.ADD_TAGS)) {
        if (ALLOWED_TAGS === DEFAULT_ALLOWED_TAGS) {
          ALLOWED_TAGS = clone(ALLOWED_TAGS);
        }
        addToSet(ALLOWED_TAGS, cfg.ADD_TAGS, transformCaseFunc);
      }
    }
    if (objectHasOwnProperty(cfg, "ADD_ATTR")) {
      if (typeof cfg.ADD_ATTR === "function") {
        EXTRA_ELEMENT_HANDLING.attributeCheck = cfg.ADD_ATTR;
      } else if (arrayIsArray(cfg.ADD_ATTR)) {
        if (ALLOWED_ATTR === DEFAULT_ALLOWED_ATTR) {
          ALLOWED_ATTR = clone(ALLOWED_ATTR);
        }
        addToSet(ALLOWED_ATTR, cfg.ADD_ATTR, transformCaseFunc);
      }
    }
    if (objectHasOwnProperty(cfg, "ADD_URI_SAFE_ATTR") && arrayIsArray(cfg.ADD_URI_SAFE_ATTR)) {
      addToSet(URI_SAFE_ATTRIBUTES, cfg.ADD_URI_SAFE_ATTR, transformCaseFunc);
    }
    if (objectHasOwnProperty(cfg, "FORBID_CONTENTS") && arrayIsArray(cfg.FORBID_CONTENTS)) {
      if (FORBID_CONTENTS === DEFAULT_FORBID_CONTENTS) {
        FORBID_CONTENTS = clone(FORBID_CONTENTS);
      }
      addToSet(FORBID_CONTENTS, cfg.FORBID_CONTENTS, transformCaseFunc);
    }
    if (objectHasOwnProperty(cfg, "ADD_FORBID_CONTENTS") && arrayIsArray(cfg.ADD_FORBID_CONTENTS)) {
      if (FORBID_CONTENTS === DEFAULT_FORBID_CONTENTS) {
        FORBID_CONTENTS = clone(FORBID_CONTENTS);
      }
      addToSet(FORBID_CONTENTS, cfg.ADD_FORBID_CONTENTS, transformCaseFunc);
    }
    if (KEEP_CONTENT) {
      ALLOWED_TAGS["#text"] = true;
    }
    if (WHOLE_DOCUMENT) {
      addToSet(ALLOWED_TAGS, ["html", "head", "body"]);
    }
    if (ALLOWED_TAGS.table) {
      addToSet(ALLOWED_TAGS, ["tbody"]);
      delete FORBID_TAGS.tbody;
    }
    if (cfg.TRUSTED_TYPES_POLICY) {
      if (typeof cfg.TRUSTED_TYPES_POLICY.createHTML !== "function") {
        throw typeErrorCreate('TRUSTED_TYPES_POLICY configuration option must provide a "createHTML" hook.');
      }
      if (typeof cfg.TRUSTED_TYPES_POLICY.createScriptURL !== "function") {
        throw typeErrorCreate('TRUSTED_TYPES_POLICY configuration option must provide a "createScriptURL" hook.');
      }
      const previousTrustedTypesPolicy = trustedTypesPolicy;
      trustedTypesPolicy = cfg.TRUSTED_TYPES_POLICY;
      try {
        emptyHTML = _createTrustedHTML("");
      } catch (error) {
        trustedTypesPolicy = previousTrustedTypesPolicy;
        throw error;
      }
    } else if (cfg.TRUSTED_TYPES_POLICY === null) {
      trustedTypesPolicy = void 0;
      emptyHTML = "";
    } else {
      if (trustedTypesPolicy === void 0) {
        trustedTypesPolicy = _getDefaultTrustedTypesPolicy();
      }
      if (trustedTypesPolicy && typeof emptyHTML === "string") {
        emptyHTML = _createTrustedHTML("");
      }
    }
    if ((hooks.uponSanitizeElement.length > 0 || hooks.uponSanitizeAttribute.length > 0) && ALLOWED_TAGS === DEFAULT_ALLOWED_TAGS) {
      ALLOWED_TAGS = clone(ALLOWED_TAGS);
    }
    if (hooks.uponSanitizeAttribute.length > 0 && ALLOWED_ATTR === DEFAULT_ALLOWED_ATTR) {
      ALLOWED_ATTR = clone(ALLOWED_ATTR);
    }
    if (freeze) {
      freeze(cfg);
    }
    CONFIG = cfg;
  };
  const ALL_SVG_TAGS = addToSet({}, [...svg$1, ...svgFilters, ...svgDisallowed]);
  const ALL_MATHML_TAGS = addToSet({}, [...mathMl$1, ...mathMlDisallowed]);
  const _checkSvgNamespace = function _checkSvgNamespace2(tagName, parent, parentTagName) {
    if (parent.namespaceURI === HTML_NAMESPACE) {
      return tagName === "svg";
    }
    if (parent.namespaceURI === MATHML_NAMESPACE) {
      return tagName === "svg" && (parentTagName === "annotation-xml" || MATHML_TEXT_INTEGRATION_POINTS[parentTagName]);
    }
    return Boolean(ALL_SVG_TAGS[tagName]);
  };
  const _checkMathMlNamespace = function _checkMathMlNamespace2(tagName, parent, parentTagName) {
    if (parent.namespaceURI === HTML_NAMESPACE) {
      return tagName === "math";
    }
    if (parent.namespaceURI === SVG_NAMESPACE) {
      return tagName === "math" && HTML_INTEGRATION_POINTS[parentTagName];
    }
    return Boolean(ALL_MATHML_TAGS[tagName]);
  };
  const _checkHtmlNamespace = function _checkHtmlNamespace2(tagName, parent, parentTagName) {
    if (parent.namespaceURI === SVG_NAMESPACE && !HTML_INTEGRATION_POINTS[parentTagName]) {
      return false;
    }
    if (parent.namespaceURI === MATHML_NAMESPACE && !MATHML_TEXT_INTEGRATION_POINTS[parentTagName]) {
      return false;
    }
    return !ALL_MATHML_TAGS[tagName] && (COMMON_SVG_AND_HTML_ELEMENTS[tagName] || !ALL_SVG_TAGS[tagName]);
  };
  const _checkValidNamespace = function _checkValidNamespace2(element) {
    let parent = getParentNode(element);
    if (!parent || !parent.tagName) {
      parent = {
        namespaceURI: NAMESPACE,
        tagName: "template"
      };
    }
    const tagName = stringToLowerCase(element.tagName);
    const parentTagName = stringToLowerCase(parent.tagName);
    if (!ALLOWED_NAMESPACES[element.namespaceURI]) {
      return false;
    }
    if (element.namespaceURI === SVG_NAMESPACE) {
      return _checkSvgNamespace(tagName, parent, parentTagName);
    }
    if (element.namespaceURI === MATHML_NAMESPACE) {
      return _checkMathMlNamespace(tagName, parent, parentTagName);
    }
    if (element.namespaceURI === HTML_NAMESPACE) {
      return _checkHtmlNamespace(tagName, parent, parentTagName);
    }
    if (PARSER_MEDIA_TYPE === "application/xhtml+xml" && ALLOWED_NAMESPACES[element.namespaceURI]) {
      return true;
    }
    return false;
  };
  const _forceRemove = function _forceRemove2(node) {
    arrayPush(DOMPurify.removed, {
      element: node
    });
    try {
      getParentNode(node).removeChild(node);
    } catch (_) {
      remove(node);
      if (!getParentNode(node)) {
        throw typeErrorCreate("a node selected for removal could not be detached from its tree and cannot be safely returned; refusing to sanitize in place");
      }
    }
  };
  const _neutralizeRoot = function _neutralizeRoot2(root) {
    const childNodes = getChildNodes(root);
    if (childNodes) {
      const snapshot = [];
      arrayForEach(childNodes, (child) => {
        arrayPush(snapshot, child);
      });
      arrayForEach(snapshot, (child) => {
        try {
          remove(child);
        } catch (_) {
        }
      });
    }
    const attributes = getAttributes(root);
    if (attributes) {
      for (let i = attributes.length - 1; i >= 0; --i) {
        const attribute = attributes[i];
        const name = attribute && attribute.name;
        if (typeof name === "string") {
          try {
            root.removeAttribute(name);
          } catch (_) {
          }
        }
      }
    }
  };
  const _removeAttribute = function _removeAttribute2(name, element) {
    try {
      arrayPush(DOMPurify.removed, {
        attribute: element.getAttributeNode(name),
        from: element
      });
    } catch (_) {
      arrayPush(DOMPurify.removed, {
        attribute: null,
        from: element
      });
    }
    element.removeAttribute(name);
    if (name === "is") {
      if (RETURN_DOM || RETURN_DOM_FRAGMENT) {
        try {
          _forceRemove(element);
        } catch (_) {
        }
      } else {
        try {
          element.setAttribute(name, "");
        } catch (_) {
        }
      }
    }
  };
  const _stripDisallowedAttributes = function _stripDisallowedAttributes2(element) {
    const attributes = getAttributes(element);
    if (!attributes) {
      return;
    }
    for (let i = attributes.length - 1; i >= 0; --i) {
      const attribute = attributes[i];
      const name = attribute && attribute.name;
      if (typeof name !== "string" || ALLOWED_ATTR[transformCaseFunc(name)]) {
        continue;
      }
      try {
        element.removeAttribute(name);
      } catch (_) {
      }
    }
  };
  const _neutralizeSubtree = function _neutralizeSubtree2(root) {
    const stack = [root];
    while (stack.length > 0) {
      const node = stack.pop();
      const nodeType = getNodeType ? getNodeType(node) : node.nodeType;
      if (nodeType === NODE_TYPE.element) {
        _stripDisallowedAttributes(node);
      }
      const childNodes = getChildNodes(node);
      if (childNodes) {
        for (let i = childNodes.length - 1; i >= 0; --i) {
          stack.push(childNodes[i]);
        }
      }
    }
  };
  const _initDocument = function _initDocument2(dirty) {
    let doc = null;
    let leadingWhitespace = null;
    if (FORCE_BODY) {
      dirty = "<remove></remove>" + dirty;
    } else {
      const matches = stringMatch(dirty, /^[\r\n\t ]+/);
      leadingWhitespace = matches && matches[0];
    }
    if (PARSER_MEDIA_TYPE === "application/xhtml+xml" && NAMESPACE === HTML_NAMESPACE) {
      dirty = '<html xmlns="http://www.w3.org/1999/xhtml"><head></head><body>' + dirty + "</body></html>";
    }
    const dirtyPayload = trustedTypesPolicy ? _createTrustedHTML(dirty) : dirty;
    if (NAMESPACE === HTML_NAMESPACE) {
      try {
        doc = new DOMParser().parseFromString(dirtyPayload, PARSER_MEDIA_TYPE);
      } catch (_) {
      }
    }
    if (!doc || !doc.documentElement) {
      doc = implementation.createDocument(NAMESPACE, "template", null);
      try {
        doc.documentElement.innerHTML = IS_EMPTY_INPUT ? emptyHTML : dirtyPayload;
      } catch (_) {
      }
    }
    const body = doc.body || doc.documentElement;
    if (dirty && leadingWhitespace) {
      body.insertBefore(document2.createTextNode(leadingWhitespace), body.childNodes[0] || null);
    }
    if (NAMESPACE === HTML_NAMESPACE) {
      return getElementsByTagName.call(doc, WHOLE_DOCUMENT ? "html" : "body")[0];
    }
    return WHOLE_DOCUMENT ? doc.documentElement : body;
  };
  const _createNodeIterator = function _createNodeIterator2(root) {
    return createNodeIterator.call(
      root.ownerDocument || root,
      root,
      // eslint-disable-next-line no-bitwise
      NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_COMMENT | NodeFilter.SHOW_TEXT | NodeFilter.SHOW_PROCESSING_INSTRUCTION | NodeFilter.SHOW_CDATA_SECTION,
      null
    );
  };
  const _stripTemplateExpressions = function _stripTemplateExpressions2(value) {
    value = stringReplace(value, MUSTACHE_EXPR$1, " ");
    value = stringReplace(value, ERB_EXPR$1, " ");
    value = stringReplace(value, TMPLIT_EXPR$1, " ");
    return value;
  };
  const _scrubTemplateExpressions2 = function _scrubTemplateExpressions(node) {
    var _node$querySelectorAl;
    node.normalize();
    const walker = createNodeIterator.call(
      node.ownerDocument || node,
      node,
      // eslint-disable-next-line no-bitwise
      NodeFilter.SHOW_TEXT | NodeFilter.SHOW_COMMENT | NodeFilter.SHOW_CDATA_SECTION | NodeFilter.SHOW_PROCESSING_INSTRUCTION,
      null
    );
    let currentNode = walker.nextNode();
    while (currentNode) {
      currentNode.data = _stripTemplateExpressions(currentNode.data);
      currentNode = walker.nextNode();
    }
    const templates = (_node$querySelectorAl = node.querySelectorAll) === null || _node$querySelectorAl === void 0 ? void 0 : _node$querySelectorAl.call(node, "template");
    if (templates) {
      arrayForEach(templates, (tmpl) => {
        if (_isDocumentFragment(tmpl.content)) {
          _scrubTemplateExpressions2(tmpl.content);
        }
      });
    }
  };
  const _isClobbered = function _isClobbered2(element) {
    const realTagName = getNodeName ? getNodeName(element) : null;
    if (typeof realTagName !== "string") {
      return false;
    }
    if (transformCaseFunc(realTagName) !== "form") {
      return false;
    }
    return typeof element.nodeName !== "string" || typeof element.textContent !== "string" || typeof element.removeChild !== "function" || // Realm-safe NamedNodeMap detection: equality against the cached
    // prototype getter. Clobbered .attributes (e.g. <input name="attributes">)
    // makes the direct read diverge from the cached read; a clean form
    // (same-realm OR foreign-realm) has both reads pointing at the same
    // canonical NamedNodeMap.
    element.attributes !== getAttributes(element) || typeof element.removeAttribute !== "function" || typeof element.setAttribute !== "function" || typeof element.namespaceURI !== "string" || typeof element.insertBefore !== "function" || typeof element.hasChildNodes !== "function" || // NodeType clobbering probe. Cached Node.prototype.nodeType getter
    // returns the integer 1 for any Element regardless of realm; direct
    // read on a clobbered form (e.g. <input name="nodeType">) returns
    // the named child element. Cheap addition — nodeType is read from
    // an internal slot, no serialization cost — and removes a residual
    // clobbering surface used by several mXSS / PI / comment branches
    // in _sanitizeElements that compare currentNode.nodeType directly.
    element.nodeType !== getNodeType(element) || // HTMLFormElement has [LegacyOverrideBuiltIns]: a descendant named
    // "childNodes" shadows the prototype getter. Direct reads of
    // form.childNodes from a clobbered form return the named child
    // instead of the real NodeList, so any walk that reads it directly
    // skips the form's real children. Compare the direct read to the
    // cached Node.prototype getter — when the form's named-property
    // getter intercepts the read, the two values differ and we flag
    // the form. This catches every clobbering child type (input,
    // select, etc.) regardless of whether the named child happens to
    // carry a numeric .length, which a typeof-based probe would miss
    // (e.g. HTMLSelectElement.length is a defined unsigned-long).
    element.childNodes !== getChildNodes(element);
  };
  const _isDocumentFragment = function _isDocumentFragment2(value) {
    if (!getNodeType || typeof value !== "object" || value === null) {
      return false;
    }
    try {
      return getNodeType(value) === NODE_TYPE.documentFragment;
    } catch (_) {
      return false;
    }
  };
  const _isNode = function _isNode2(value) {
    if (!getNodeType || typeof value !== "object" || value === null) {
      return false;
    }
    try {
      return typeof getNodeType(value) === "number";
    } catch (_) {
      return false;
    }
  };
  function _executeHooks(hooks2, currentNode, data) {
    if (hooks2.length === 0) {
      return;
    }
    arrayForEach(hooks2, (hook) => {
      hook.call(DOMPurify, currentNode, data, CONFIG);
    });
  }
  const _isUnsafeNode = function _isUnsafeNode2(currentNode, tagName) {
    if (SAFE_FOR_XML && currentNode.hasChildNodes() && !_isNode(currentNode.firstElementChild) && regExpTest(ELEMENT_MARKUP_PROBE, currentNode.textContent) && regExpTest(ELEMENT_MARKUP_PROBE, currentNode.innerHTML)) {
      return true;
    }
    if (SAFE_FOR_XML && currentNode.namespaceURI === HTML_NAMESPACE && tagName === "style" && _isNode(currentNode.firstElementChild)) {
      return true;
    }
    if (currentNode.nodeType === NODE_TYPE.processingInstruction) {
      return true;
    }
    if (SAFE_FOR_XML && currentNode.nodeType === NODE_TYPE.comment && regExpTest(COMMENT_MARKUP_PROBE, currentNode.data)) {
      return true;
    }
    return false;
  };
  const _sanitizeDisallowedNode = function _sanitizeDisallowedNode2(currentNode, tagName) {
    if (!FORBID_TAGS[tagName] && _isBasicCustomElement(tagName)) {
      if (CUSTOM_ELEMENT_HANDLING.tagNameCheck instanceof RegExp && regExpTest(CUSTOM_ELEMENT_HANDLING.tagNameCheck, tagName)) {
        return false;
      }
      if (CUSTOM_ELEMENT_HANDLING.tagNameCheck instanceof Function && CUSTOM_ELEMENT_HANDLING.tagNameCheck(tagName)) {
        return false;
      }
    }
    if (KEEP_CONTENT && !FORBID_CONTENTS[tagName]) {
      const parentNode = getParentNode(currentNode);
      const childNodes = getChildNodes(currentNode);
      if (childNodes && parentNode) {
        const childCount = childNodes.length;
        for (let i = childCount - 1; i >= 0; --i) {
          const hoisted = IN_PLACE ? childNodes[i] : cloneNode(childNodes[i], true);
          parentNode.insertBefore(hoisted, getNextSibling(currentNode));
        }
      }
    }
    _forceRemove(currentNode);
    return true;
  };
  const _sanitizeElements = function _sanitizeElements2(currentNode) {
    _executeHooks(hooks.beforeSanitizeElements, currentNode, null);
    if (_isClobbered(currentNode)) {
      _forceRemove(currentNode);
      return true;
    }
    const tagName = transformCaseFunc(getNodeName ? getNodeName(currentNode) : currentNode.nodeName);
    _executeHooks(hooks.uponSanitizeElement, currentNode, {
      tagName,
      allowedTags: ALLOWED_TAGS
    });
    if (_isUnsafeNode(currentNode, tagName)) {
      _forceRemove(currentNode);
      return true;
    }
    if (FORBID_TAGS[tagName] || !(EXTRA_ELEMENT_HANDLING.tagCheck instanceof Function && EXTRA_ELEMENT_HANDLING.tagCheck(tagName)) && !ALLOWED_TAGS[tagName]) {
      return _sanitizeDisallowedNode(currentNode, tagName);
    }
    const nt = getNodeType ? getNodeType(currentNode) : currentNode.nodeType;
    if (nt === NODE_TYPE.element && !_checkValidNamespace(currentNode)) {
      _forceRemove(currentNode);
      return true;
    }
    if ((tagName === "noscript" || tagName === "noembed" || tagName === "noframes") && regExpTest(FALLBACK_TAG_CLOSE, currentNode.innerHTML)) {
      _forceRemove(currentNode);
      return true;
    }
    if (SAFE_FOR_TEMPLATES && currentNode.nodeType === NODE_TYPE.text) {
      const content = _stripTemplateExpressions(currentNode.textContent);
      if (currentNode.textContent !== content) {
        arrayPush(DOMPurify.removed, {
          element: currentNode.cloneNode()
        });
        currentNode.textContent = content;
      }
    }
    _executeHooks(hooks.afterSanitizeElements, currentNode, null);
    return false;
  };
  const _isValidAttribute = function _isValidAttribute2(lcTag, lcName, value) {
    if (FORBID_ATTR[lcName]) {
      return false;
    }
    if (SANITIZE_DOM && (lcName === "id" || lcName === "name") && (value in document2 || value in formElement)) {
      return false;
    }
    const nameIsPermitted = ALLOWED_ATTR[lcName] || EXTRA_ELEMENT_HANDLING.attributeCheck instanceof Function && EXTRA_ELEMENT_HANDLING.attributeCheck(lcName, lcTag);
    if (ALLOW_DATA_ATTR && regExpTest(DATA_ATTR$1, lcName)) ;
    else if (ALLOW_ARIA_ATTR && regExpTest(ARIA_ATTR$1, lcName)) ;
    else if (!nameIsPermitted) {
      if (
        // First condition does a very basic check if a) it's basically a valid custom element tagname AND
        // b) if the tagName passes whatever the user has configured for CUSTOM_ELEMENT_HANDLING.tagNameCheck
        // and c) if the attribute name passes whatever the user has configured for CUSTOM_ELEMENT_HANDLING.attributeNameCheck
        _isBasicCustomElement(lcTag) && (CUSTOM_ELEMENT_HANDLING.tagNameCheck instanceof RegExp && regExpTest(CUSTOM_ELEMENT_HANDLING.tagNameCheck, lcTag) || CUSTOM_ELEMENT_HANDLING.tagNameCheck instanceof Function && CUSTOM_ELEMENT_HANDLING.tagNameCheck(lcTag)) && (CUSTOM_ELEMENT_HANDLING.attributeNameCheck instanceof RegExp && regExpTest(CUSTOM_ELEMENT_HANDLING.attributeNameCheck, lcName) || CUSTOM_ELEMENT_HANDLING.attributeNameCheck instanceof Function && CUSTOM_ELEMENT_HANDLING.attributeNameCheck(lcName, lcTag)) || // Alternative, second condition checks if it's an `is`-attribute, AND
        // the value passes whatever the user has configured for CUSTOM_ELEMENT_HANDLING.tagNameCheck
        lcName === "is" && CUSTOM_ELEMENT_HANDLING.allowCustomizedBuiltInElements && (CUSTOM_ELEMENT_HANDLING.tagNameCheck instanceof RegExp && regExpTest(CUSTOM_ELEMENT_HANDLING.tagNameCheck, value) || CUSTOM_ELEMENT_HANDLING.tagNameCheck instanceof Function && CUSTOM_ELEMENT_HANDLING.tagNameCheck(value))
      ) ;
      else {
        return false;
      }
    } else if (URI_SAFE_ATTRIBUTES[lcName]) ;
    else if (regExpTest(IS_ALLOWED_URI$1, stringReplace(value, ATTR_WHITESPACE$1, ""))) ;
    else if ((lcName === "src" || lcName === "xlink:href" || lcName === "href") && lcTag !== "script" && stringIndexOf(value, "data:") === 0 && DATA_URI_TAGS[lcTag]) ;
    else if (ALLOW_UNKNOWN_PROTOCOLS && !regExpTest(IS_SCRIPT_OR_DATA$1, stringReplace(value, ATTR_WHITESPACE$1, ""))) ;
    else if (value) {
      return false;
    } else ;
    return true;
  };
  const RESERVED_CUSTOM_ELEMENT_NAMES = addToSet({}, ["annotation-xml", "color-profile", "font-face", "font-face-format", "font-face-name", "font-face-src", "font-face-uri", "missing-glyph"]);
  const _isBasicCustomElement = function _isBasicCustomElement2(tagName) {
    return !RESERVED_CUSTOM_ELEMENT_NAMES[stringToLowerCase(tagName)] && regExpTest(CUSTOM_ELEMENT$1, tagName);
  };
  const _applyTrustedTypesToAttribute = function _applyTrustedTypesToAttribute2(lcTag, lcName, namespaceURI, value) {
    if (trustedTypesPolicy && typeof trustedTypes === "object" && typeof trustedTypes.getAttributeType === "function" && !namespaceURI) {
      switch (trustedTypes.getAttributeType(lcTag, lcName)) {
        case "TrustedHTML": {
          return _createTrustedHTML(value);
        }
        case "TrustedScriptURL": {
          return _createTrustedScriptURL(value);
        }
      }
    }
    return value;
  };
  const _setAttributeValue = function _setAttributeValue2(currentNode, name, namespaceURI, value) {
    try {
      if (namespaceURI) {
        currentNode.setAttributeNS(namespaceURI, name, value);
      } else {
        currentNode.setAttribute(name, value);
      }
      if (_isClobbered(currentNode)) {
        _forceRemove(currentNode);
      } else {
        arrayPop(DOMPurify.removed);
      }
    } catch (_) {
      _removeAttribute(name, currentNode);
    }
  };
  const _sanitizeAttributes = function _sanitizeAttributes2(currentNode) {
    _executeHooks(hooks.beforeSanitizeAttributes, currentNode, null);
    const attributes = currentNode.attributes;
    if (!attributes || _isClobbered(currentNode)) {
      return;
    }
    const hookEvent = {
      attrName: "",
      attrValue: "",
      keepAttr: true,
      allowedAttributes: ALLOWED_ATTR,
      forceKeepAttr: void 0
    };
    let l = attributes.length;
    const lcTag = transformCaseFunc(currentNode.nodeName);
    while (l--) {
      const attr = attributes[l];
      const name = attr.name, namespaceURI = attr.namespaceURI, attrValue = attr.value;
      const lcName = transformCaseFunc(name);
      const initValue = attrValue;
      let value = name === "value" ? initValue : stringTrim(initValue);
      hookEvent.attrName = lcName;
      hookEvent.attrValue = value;
      hookEvent.keepAttr = true;
      hookEvent.forceKeepAttr = void 0;
      _executeHooks(hooks.uponSanitizeAttribute, currentNode, hookEvent);
      value = hookEvent.attrValue;
      if (SANITIZE_NAMED_PROPS && (lcName === "id" || lcName === "name") && stringIndexOf(value, SANITIZE_NAMED_PROPS_PREFIX) !== 0) {
        _removeAttribute(name, currentNode);
        value = SANITIZE_NAMED_PROPS_PREFIX + value;
      }
      if (SAFE_FOR_XML && regExpTest(/((--!?|])>)|<\/(style|script|title|xmp|textarea|noscript|iframe|noembed|noframes)/i, value)) {
        _removeAttribute(name, currentNode);
        continue;
      }
      if (lcName === "attributename" && stringMatch(value, "href")) {
        _removeAttribute(name, currentNode);
        continue;
      }
      if (hookEvent.forceKeepAttr) {
        continue;
      }
      if (!hookEvent.keepAttr) {
        _removeAttribute(name, currentNode);
        continue;
      }
      if (!ALLOW_SELF_CLOSE_IN_ATTR && regExpTest(SELF_CLOSING_TAG, value)) {
        _removeAttribute(name, currentNode);
        continue;
      }
      if (SAFE_FOR_TEMPLATES) {
        value = _stripTemplateExpressions(value);
      }
      if (!_isValidAttribute(lcTag, lcName, value)) {
        _removeAttribute(name, currentNode);
        continue;
      }
      value = _applyTrustedTypesToAttribute(lcTag, lcName, namespaceURI, value);
      if (value !== initValue) {
        _setAttributeValue(currentNode, name, namespaceURI, value);
      }
    }
    _executeHooks(hooks.afterSanitizeAttributes, currentNode, null);
  };
  const _sanitizeShadowDOM2 = function _sanitizeShadowDOM(fragment) {
    let shadowNode = null;
    const shadowIterator = _createNodeIterator(fragment);
    _executeHooks(hooks.beforeSanitizeShadowDOM, fragment, null);
    while (shadowNode = shadowIterator.nextNode()) {
      _executeHooks(hooks.uponSanitizeShadowNode, shadowNode, null);
      _sanitizeElements(shadowNode);
      _sanitizeAttributes(shadowNode);
      if (_isDocumentFragment(shadowNode.content)) {
        _sanitizeShadowDOM2(shadowNode.content);
      }
      const shadowNodeType = getNodeType ? getNodeType(shadowNode) : shadowNode.nodeType;
      if (shadowNodeType === NODE_TYPE.element) {
        const innerSr = getShadowRoot(shadowNode);
        if (_isDocumentFragment(innerSr)) {
          _sanitizeAttachedShadowRoots(innerSr);
          _sanitizeShadowDOM2(innerSr);
        }
      }
    }
    _executeHooks(hooks.afterSanitizeShadowDOM, fragment, null);
  };
  const _sanitizeAttachedShadowRoots = function _sanitizeAttachedShadowRoots2(root) {
    const stack = [{
      node: root,
      shadow: null
    }];
    while (stack.length > 0) {
      const item = stack.pop();
      if (item.shadow) {
        _sanitizeShadowDOM2(item.shadow);
        continue;
      }
      const node = item.node;
      const nodeType = getNodeType ? getNodeType(node) : node.nodeType;
      const isElement = nodeType === NODE_TYPE.element;
      const childNodes = getChildNodes(node);
      if (childNodes) {
        for (let i = childNodes.length - 1; i >= 0; --i) {
          stack.push({
            node: childNodes[i],
            shadow: null
          });
        }
      }
      if (isElement) {
        const rootName = getNodeName ? getNodeName(node) : null;
        if (typeof rootName === "string" && transformCaseFunc(rootName) === "template") {
          const content = node.content;
          if (_isDocumentFragment(content)) {
            stack.push({
              node: content,
              shadow: null
            });
          }
        }
      }
      if (isElement) {
        const sr = getShadowRoot(node);
        if (_isDocumentFragment(sr)) {
          stack.push({
            node: null,
            shadow: sr
          }, {
            node: sr,
            shadow: null
          });
        }
      }
    }
  };
  DOMPurify.sanitize = function(dirty) {
    let cfg = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : {};
    let body = null;
    let importedNode = null;
    let currentNode = null;
    let returnNode = null;
    IS_EMPTY_INPUT = !dirty;
    if (IS_EMPTY_INPUT) {
      dirty = "<!-->";
    }
    if (typeof dirty !== "string" && !_isNode(dirty)) {
      dirty = stringifyValue(dirty);
      if (typeof dirty !== "string") {
        throw typeErrorCreate("dirty is not a string, aborting");
      }
    }
    if (!DOMPurify.isSupported) {
      return dirty;
    }
    if (!SET_CONFIG) {
      _parseConfig(cfg);
    }
    DOMPurify.removed = [];
    const inPlace = IN_PLACE && typeof dirty !== "string" && _isNode(dirty);
    if (inPlace) {
      const nn = getNodeName ? getNodeName(dirty) : dirty.nodeName;
      if (typeof nn === "string") {
        const tagName = transformCaseFunc(nn);
        if (!ALLOWED_TAGS[tagName] || FORBID_TAGS[tagName]) {
          throw typeErrorCreate("root node is forbidden and cannot be sanitized in-place");
        }
      }
      if (_isClobbered(dirty)) {
        throw typeErrorCreate("root node is clobbered and cannot be sanitized in-place");
      }
      try {
        _sanitizeAttachedShadowRoots(dirty);
      } catch (error) {
        _neutralizeRoot(dirty);
        throw error;
      }
    } else if (_isNode(dirty)) {
      body = _initDocument("<!---->");
      importedNode = body.ownerDocument.importNode(dirty, true);
      if (importedNode.nodeType === NODE_TYPE.element && importedNode.nodeName === "BODY") {
        body = importedNode;
      } else if (importedNode.nodeName === "HTML") {
        body = importedNode;
      } else {
        body.appendChild(importedNode);
      }
      _sanitizeAttachedShadowRoots(importedNode);
    } else {
      if (!RETURN_DOM && !SAFE_FOR_TEMPLATES && !WHOLE_DOCUMENT && // eslint-disable-next-line unicorn/prefer-includes
      dirty.indexOf("<") === -1) {
        return trustedTypesPolicy && RETURN_TRUSTED_TYPE ? _createTrustedHTML(dirty) : dirty;
      }
      body = _initDocument(dirty);
      if (!body) {
        return RETURN_DOM ? null : RETURN_TRUSTED_TYPE ? emptyHTML : "";
      }
    }
    if (body && FORCE_BODY) {
      _forceRemove(body.firstChild);
    }
    const nodeIterator = _createNodeIterator(inPlace ? dirty : body);
    try {
      while (currentNode = nodeIterator.nextNode()) {
        _sanitizeElements(currentNode);
        _sanitizeAttributes(currentNode);
        if (_isDocumentFragment(currentNode.content)) {
          _sanitizeShadowDOM2(currentNode.content);
        }
      }
    } catch (error) {
      if (inPlace) {
        _neutralizeRoot(dirty);
      }
      throw error;
    }
    if (inPlace) {
      arrayForEach(DOMPurify.removed, (entry) => {
        if (entry.element) {
          _neutralizeSubtree(entry.element);
        }
      });
      if (SAFE_FOR_TEMPLATES) {
        _scrubTemplateExpressions2(dirty);
      }
      return dirty;
    }
    if (RETURN_DOM) {
      if (SAFE_FOR_TEMPLATES) {
        _scrubTemplateExpressions2(body);
      }
      if (RETURN_DOM_FRAGMENT) {
        returnNode = createDocumentFragment.call(body.ownerDocument);
        while (body.firstChild) {
          returnNode.appendChild(body.firstChild);
        }
      } else {
        returnNode = body;
      }
      if (ALLOWED_ATTR.shadowroot || ALLOWED_ATTR.shadowrootmode) {
        returnNode = importNode.call(originalDocument, returnNode, true);
      }
      return returnNode;
    }
    let serializedHTML = WHOLE_DOCUMENT ? body.outerHTML : body.innerHTML;
    if (WHOLE_DOCUMENT && ALLOWED_TAGS["!doctype"] && body.ownerDocument && body.ownerDocument.doctype && body.ownerDocument.doctype.name && regExpTest(DOCTYPE_NAME, body.ownerDocument.doctype.name)) {
      serializedHTML = "<!DOCTYPE " + body.ownerDocument.doctype.name + ">\n" + serializedHTML;
    }
    if (SAFE_FOR_TEMPLATES) {
      serializedHTML = _stripTemplateExpressions(serializedHTML);
    }
    return trustedTypesPolicy && RETURN_TRUSTED_TYPE ? _createTrustedHTML(serializedHTML) : serializedHTML;
  };
  DOMPurify.setConfig = function() {
    let cfg = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : {};
    _parseConfig(cfg);
    SET_CONFIG = true;
  };
  DOMPurify.clearConfig = function() {
    CONFIG = null;
    SET_CONFIG = false;
    trustedTypesPolicy = defaultTrustedTypesPolicy;
    emptyHTML = "";
  };
  DOMPurify.isValidAttribute = function(tag, attr, value) {
    if (!CONFIG) {
      _parseConfig({});
    }
    const lcTag = transformCaseFunc(tag);
    const lcName = transformCaseFunc(attr);
    return _isValidAttribute(lcTag, lcName, value);
  };
  DOMPurify.addHook = function(entryPoint, hookFunction) {
    if (typeof hookFunction !== "function") {
      return;
    }
    arrayPush(hooks[entryPoint], hookFunction);
  };
  DOMPurify.removeHook = function(entryPoint, hookFunction) {
    if (hookFunction !== void 0) {
      const index = arrayLastIndexOf(hooks[entryPoint], hookFunction);
      return index === -1 ? void 0 : arraySplice(hooks[entryPoint], index, 1)[0];
    }
    return arrayPop(hooks[entryPoint]);
  };
  DOMPurify.removeHooks = function(entryPoint) {
    hooks[entryPoint] = [];
  };
  DOMPurify.removeAllHooks = function() {
    hooks = _createHooksMap();
  };
  return DOMPurify;
}
var purify = createDOMPurify();
function formatCurrency(amount) {
  if (amount === null || amount === void 0) return "0.00";
  return Number.parseFloat(amount).toFixed(2);
}
function formatQuantity(quantity) {
  if (quantity === null || quantity === void 0) return "0";
  const num = Number.parseFloat(quantity);
  if (isNaN(num)) return "0";
  return num.toFixed(4).replace(/\.?0+$/, "");
}
function formatDateTime(datetime) {
  if (!datetime) return "";
  return new Date(datetime).toLocaleString();
}
function formatTime(time) {
  if (!time) return "";
  if (typeof time === "string" && time.includes(":")) {
    const parts = time.split(":");
    if (parts.length >= 2) {
      return `${parts[0]}:${parts[1]}`;
    }
    return time;
  }
  return new Date(time).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit"
  });
}
function formatDate(date) {
  if (!date) return "";
  return new Date(date).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit"
  });
}
function formatPercentage(value, decimals = 2) {
  if (value === null || value === void 0) return "0%";
  return `${Number.parseFloat(value).toFixed(decimals).replace(/\.?0+$/, "")}%`;
}
function useFormatters() {
  return {
    formatCurrency,
    formatQuantity,
    formatDateTime,
    formatTime,
    formatDate,
    formatPercentage
  };
}
const usePOSSettingsStore = defineStore("posSettings", () => {
  const settings = ref({
    pos_profile: "",
    enabled: 0,
    // Wallet & Loyalty Settings
    enable_loyalty_program: 0,
    default_loyalty_program: "",
    wallet_account: "",
    auto_create_wallet: 1,
    loyalty_to_wallet: 1,
    // General Settings
    max_discount_allowed: 0,
    use_percentage_discount: 0,
    allow_user_to_edit_additional_discount: 0,
    allow_user_to_edit_item_discount: 1,
    // Allow item-level discounts
    allow_user_to_edit_rate: 0,
    // Allow rate editing in edit dialog
    disable_rounded_total: 1,
    // Disable rounding for accurate totals
    allow_credit_sale: 0,
    allow_customer_credit_payment: 0,
    allow_return: 0,
    allow_write_off_change: 0,
    allow_partial_payment: 0,
    use_exact_amount: 0,
    // Display Settings
    default_card_view: 0,
    display_item_code: 0,
    show_customer_balance: 0,
    hide_expected_amount: 0,
    display_discount_percentage: 0,
    display_discount_amount: 0,
    // Operations
    allow_sales_order: 0,
    allow_select_sales_order: 0,
    create_only_sales_order: 0,
    allow_return_without_invoice: 0,
    allow_free_batch_return: 0,
    allow_print_draft_invoices: 0,
    // Pricing & Display
    decimal_precision: "2",
    // Customer Settings
    allow_customer_purchase_order: 0,
    allow_duplicate_customer_names: 0,
    fetch_coupon: 0,
    // Printing
    allow_print_last_invoice: 0,
    silent_print: 0,
    // Delivery
    use_delivery_charges: 0,
    auto_set_delivery_charges: 0,
    // Advanced Settings
    use_limit_search: 0,
    search_limit: 1e3,
    allow_submissions_in_background_job: 0,
    allow_delete_offline_invoice: 0,
    allow_change_posting_date: 0,
    // Miscellaneous
    input_qty: 0,
    allow_negative_stock: 0,
    // Sales Persons
    enable_sales_persons: "Disabled"
  });
  const isLoading = ref(false);
  const isLoaded = ref(false);
  const enableLoyaltyProgram = computed(
    () => Boolean(settings.value.enable_loyalty_program)
  );
  const defaultLoyaltyProgram = computed(
    () => settings.value.default_loyalty_program || ""
  );
  const walletAccount = computed(
    () => settings.value.wallet_account || ""
  );
  const autoCreateWallet = computed(
    () => Boolean(settings.value.auto_create_wallet)
  );
  const loyaltyToWallet = computed(
    () => Boolean(settings.value.loyalty_to_wallet)
  );
  const isEnabled = computed(() => Boolean(settings.value.enabled));
  const maxDiscountAllowed = computed(
    () => Number.parseFloat(settings.value.max_discount_allowed) || 0
  );
  const usePercentageDiscount = computed(
    () => Boolean(settings.value.use_percentage_discount)
  );
  const allowAdditionalDiscount = computed(
    () => Boolean(settings.value.allow_user_to_edit_additional_discount)
  );
  const allowItemDiscount = computed(
    () => Boolean(settings.value.allow_user_to_edit_item_discount)
  );
  const allowUserToEditRate = computed(
    () => Boolean(settings.value.allow_user_to_edit_rate)
  );
  const disableRoundedTotal = computed(
    () => Boolean(settings.value.disable_rounded_total)
  );
  const allowCreditSale = computed(
    () => Boolean(settings.value.allow_credit_sale)
  );
  const allowCustomerCreditPayment = computed(
    () => Boolean(settings.value.allow_customer_credit_payment)
  );
  const allowReturn = computed(() => Boolean(settings.value.allow_return));
  const allowWriteOffChange = computed(
    () => Boolean(settings.value.allow_write_off_change)
  );
  const allowPartialPayment = computed(
    () => Boolean(settings.value.allow_partial_payment)
  );
  const useExactAmount = computed(
    () => Boolean(settings.value.use_exact_amount)
  );
  const defaultCardView = computed(
    () => Boolean(settings.value.default_card_view)
  );
  const displayItemCode = computed(
    () => Boolean(settings.value.display_item_code)
  );
  const showCustomerBalance = computed(
    () => Boolean(settings.value.show_customer_balance)
  );
  const hideExpectedAmount = computed(
    () => Boolean(settings.value.hide_expected_amount)
  );
  const displayDiscountPercentage = computed(
    () => Boolean(settings.value.display_discount_percentage)
  );
  const displayDiscountAmount = computed(
    () => Boolean(settings.value.display_discount_amount)
  );
  const allowSalesOrder = computed(
    () => Boolean(settings.value.allow_sales_order)
  );
  const allowSelectSalesOrder = computed(
    () => Boolean(settings.value.allow_select_sales_order)
  );
  const createOnlySalesOrder = computed(
    () => Boolean(settings.value.create_only_sales_order)
  );
  const allowReturnWithoutInvoice = computed(
    () => Boolean(settings.value.allow_return_without_invoice)
  );
  const allowFreeBatchReturn = computed(
    () => Boolean(settings.value.allow_free_batch_return)
  );
  const allowPrintDraftInvoices = computed(
    () => Boolean(settings.value.allow_print_draft_invoices)
  );
  const decimalPrecision = computed(
    () => Number.parseInt(settings.value.decimal_precision) || 2
  );
  const allowCustomerPurchaseOrder = computed(
    () => Boolean(settings.value.allow_customer_purchase_order)
  );
  const allowDuplicateCustomerNames = computed(
    () => Boolean(settings.value.allow_duplicate_customer_names)
  );
  const fetchCoupon = computed(() => Boolean(settings.value.fetch_coupon));
  const allowPrintLastInvoice = computed(
    () => Boolean(settings.value.allow_print_last_invoice)
  );
  const silentPrint = computed(() => Boolean(settings.value.silent_print));
  const useDeliveryCharges = computed(
    () => Boolean(settings.value.use_delivery_charges)
  );
  const autoSetDeliveryCharges = computed(
    () => Boolean(settings.value.auto_set_delivery_charges)
  );
  const useLimitSearch = computed(
    () => Boolean(settings.value.use_limit_search)
  );
  const searchLimit = computed(
    () => Number.parseInt(settings.value.search_limit) || 1e3
  );
  const allowSubmissionsInBackgroundJob = computed(
    () => Boolean(settings.value.allow_submissions_in_background_job)
  );
  const allowDeleteOfflineInvoice = computed(
    () => Boolean(settings.value.allow_delete_offline_invoice)
  );
  const allowChangePostingDate = computed(
    () => Boolean(settings.value.allow_change_posting_date)
  );
  const inputQty = computed(() => Boolean(settings.value.input_qty));
  const allowNegativeStock = computed(
    () => Boolean(settings.value.allow_negative_stock)
  );
  const enableSalesPersons = computed(
    () => settings.value.enable_sales_persons === "Single" || settings.value.enable_sales_persons === "Multiple"
  );
  const salesPersonsMode = computed(
    () => settings.value.enable_sales_persons || "Disabled"
  );
  const isSingleSalesPerson = computed(
    () => settings.value.enable_sales_persons === "Single"
  );
  const isMultipleSalesPersons = computed(
    () => settings.value.enable_sales_persons === "Multiple"
  );
  const settingsResource = createResource({
    url: "ecs_posnext.pos_next.doctype.pos_settings.pos_settings.get_pos_settings",
    onSuccess(data) {
      if (data) {
        Object.assign(settings.value, data);
        isLoaded.value = true;
      }
      isLoading.value = false;
    },
    onError(error) {
      isLoading.value = false;
    }
  });
  function loadSettings(posProfile) {
    return __async(this, null, function* () {
      if (!posProfile) {
        return false;
      }
      isLoading.value = true;
      settings.value.pos_profile = posProfile;
      try {
        const bootstrapStore = useBootstrapStore();
        const preloadedSettings = bootstrapStore.getPreloadedPOSSettings();
        if (preloadedSettings && Object.keys(preloadedSettings).length > 0) {
          Object.assign(settings.value, preloadedSettings);
          isLoaded.value = true;
          isLoading.value = false;
          return true;
        }
      } catch (e) {
      }
      try {
        yield settingsResource.submit({ pos_profile: posProfile });
        return true;
      } catch (e) {
        return false;
      }
    });
  }
  function resetSettings() {
    settings.value = {
      pos_profile: "",
      enabled: 0,
      // Wallet & Loyalty Settings
      enable_loyalty_program: 0,
      default_loyalty_program: "",
      wallet_account: "",
      auto_create_wallet: 1,
      loyalty_to_wallet: 1,
      // General Settings
      max_discount_allowed: 0,
      use_percentage_discount: 0,
      allow_user_to_edit_additional_discount: 0,
      allow_user_to_edit_item_discount: 1,
      allow_user_to_edit_rate: 0,
      disable_rounded_total: 1,
      allow_credit_sale: 0,
      allow_customer_credit_payment: 0,
      allow_return: 0,
      allow_write_off_change: 0,
      allow_partial_payment: 0,
      use_exact_amount: 0,
      default_card_view: 0,
      display_item_code: 0,
      show_customer_balance: 0,
      hide_expected_amount: 0,
      display_discount_percentage: 0,
      display_discount_amount: 0,
      allow_sales_order: 0,
      allow_select_sales_order: 0,
      create_only_sales_order: 0,
      allow_return_without_invoice: 0,
      allow_free_batch_return: 0,
      allow_print_draft_invoices: 0,
      decimal_precision: "2",
      allow_customer_purchase_order: 0,
      allow_duplicate_customer_names: 0,
      fetch_coupon: 0,
      allow_print_last_invoice: 0,
      silent_print: 0,
      use_delivery_charges: 0,
      auto_set_delivery_charges: 0,
      use_limit_search: 0,
      search_limit: 1e3,
      allow_submissions_in_background_job: 0,
      allow_delete_offline_invoice: 0,
      allow_change_posting_date: 0,
      input_qty: 0,
      allow_negative_stock: 0,
      enable_sales_persons: "Disabled"
    };
    isLoaded.value = false;
  }
  function validateDiscount(discountPercentage) {
    if (!isEnabled.value || maxDiscountAllowed.value === 0) {
      return true;
    }
    return discountPercentage <= maxDiscountAllowed.value;
  }
  function isNegativeStockAllowed() {
    return isEnabled.value && Boolean(settings.value.allow_negative_stock);
  }
  function shouldEnforceStockValidation() {
    return isEnabled.value && !Boolean(settings.value.allow_negative_stock);
  }
  function reloadSettings() {
    return __async(this, null, function* () {
      if (!settings.value.pos_profile) {
        return false;
      }
      isLoading.value = true;
      try {
        yield settingsResource.submit({ pos_profile: settings.value.pos_profile });
        return true;
      } catch (e) {
        return false;
      }
    });
  }
  return {
    // State
    settings,
    isLoading,
    isLoaded,
    // Computed - Wallet & Loyalty Settings
    enableLoyaltyProgram,
    defaultLoyaltyProgram,
    walletAccount,
    autoCreateWallet,
    loyaltyToWallet,
    // Computed - General Settings
    isEnabled,
    maxDiscountAllowed,
    usePercentageDiscount,
    allowAdditionalDiscount,
    allowItemDiscount,
    allowUserToEditRate,
    disableRoundedTotal,
    allowCreditSale,
    allowCustomerCreditPayment,
    allowReturn,
    allowWriteOffChange,
    allowPartialPayment,
    useExactAmount,
    // Computed - Display Settings
    defaultCardView,
    displayItemCode,
    showCustomerBalance,
    hideExpectedAmount,
    displayDiscountPercentage,
    displayDiscountAmount,
    // Computed - Operations
    allowSalesOrder,
    allowSelectSalesOrder,
    createOnlySalesOrder,
    allowReturnWithoutInvoice,
    allowFreeBatchReturn,
    allowPrintDraftInvoices,
    // Computed - Pricing & Display
    decimalPrecision,
    // Computed - Customer Settings
    allowCustomerPurchaseOrder,
    allowDuplicateCustomerNames,
    fetchCoupon,
    // Computed - Printing
    allowPrintLastInvoice,
    silentPrint,
    // Computed - Delivery
    useDeliveryCharges,
    autoSetDeliveryCharges,
    // Computed - Advanced Settings
    useLimitSearch,
    searchLimit,
    allowSubmissionsInBackgroundJob,
    allowDeleteOfflineInvoice,
    allowChangePostingDate,
    // Computed - Miscellaneous
    inputQty,
    allowNegativeStock,
    // Computed - Sales Persons
    enableSalesPersons,
    salesPersonsMode,
    isSingleSalesPerson,
    isMultipleSalesPersons,
    // Actions
    loadSettings,
    reloadSettings,
    resetSettings,
    validateDiscount,
    isNegativeStockAllowed,
    shouldEnforceStockValidation
  };
});
const _sfc_main$2 = {
  __name: "TranslatedHTML",
  props: {
    tag: {
      type: String,
      required: false,
      default: "span"
    },
    inner: {
      type: String,
      required: true
    }
  },
  setup(__props) {
    const props = __props;
    const containerRef = ref(null);
    onMounted(() => {
      const sanitized = purify.sanitize(props.inner);
      containerRef.value.innerHTML = sanitized;
    });
    return (_ctx, _cache) => {
      return openBlock(), createBlock(resolveDynamicComponent(__props.tag), mergeProps(_ctx.$attrs, {
        ref_key: "containerRef",
        ref: containerRef
      }), null, 16);
    };
  }
};
const _hoisted_1$1 = { class: "flex flex-col gap-3 md:gap-6" };
const _hoisted_2$1 = {
  key: 0,
  class: "text-center py-8 md:py-12"
};
const _hoisted_3$1 = { class: "mt-3 md:mt-4 text-base md:text-lg font-medium text-gray-600" };
const _hoisted_4$1 = { class: "text-xs md:text-sm text-gray-500" };
const _hoisted_5$1 = {
  key: 1,
  class: "flex flex-col gap-3 md:gap-6"
};
const _hoisted_6$1 = {
  key: 0,
  class: "bg-white border border-gray-200 rounded-lg p-3 md:p-6 shadow-sm"
};
const _hoisted_7$1 = { class: "flex flex-col sm:flex-row justify-start items-start gap-3 mb-3 md:mb-6" };
const _hoisted_8$1 = { class: "flex-1" };
const _hoisted_9$1 = { class: "text-start text-sm md:text-base font-medium text-gray-900" };
const _hoisted_10$1 = { class: "text-start text-xs md:text-sm text-gray-500 mt-1" };
const _hoisted_11$1 = { class: "text-start sm:text-end" };
const _hoisted_12$1 = { class: "text-start text-xs text-gray-500 uppercase" };
const _hoisted_13$1 = { class: "text-base md:text-lg font-semibold text-gray-900" };
const _hoisted_14$1 = { class: "grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-4" };
const _hoisted_15$1 = { class: "text-start bg-blue-50 border border-blue-200 rounded-lg p-3 md:p-4" };
const _hoisted_16$1 = { class: "text-blue-600 text-xs uppercase font-medium mb-1" };
const _hoisted_17$1 = { class: "text-lg md:text-2xl font-bold text-blue-900 mb-0.5 md:mb-1 truncate" };
const _hoisted_18$1 = { class: "text-blue-600 text-xs" };
const _hoisted_19$1 = {
  key: 0,
  class: "text-start bg-red-50 border border-red-200 rounded-lg p-3 md:p-4"
};
const _hoisted_20$1 = { class: "text-red-600 text-xs uppercase font-medium mb-1" };
const _hoisted_21$1 = { class: "text-lg md:text-2xl font-bold text-red-700 mb-0.5 md:mb-1 truncate" };
const _hoisted_22$1 = { class: "text-red-600 text-xs" };
const _hoisted_23$1 = { class: "text-start bg-green-50 border border-green-200 rounded-lg p-3 md:p-4" };
const _hoisted_24$1 = { class: "text-green-600 text-xs uppercase font-medium mb-1" };
const _hoisted_25$1 = { class: "text-lg md:text-2xl font-bold text-green-900 mb-0.5 md:mb-1 truncate" };
const _hoisted_26$1 = { class: "text-green-600 text-xs" };
const _hoisted_27$1 = { class: "text-start bg-gray-50 border border-gray-200 rounded-lg p-3 md:p-4" };
const _hoisted_28$1 = { class: "text-gray-600 text-xs uppercase font-medium mb-1" };
const _hoisted_29$1 = { class: "text-lg md:text-2xl font-bold text-gray-900 mb-0.5 md:mb-1 truncate" };
const _hoisted_30$1 = { class: "text-gray-600 text-xs" };
const _hoisted_31$1 = {
  key: 1,
  class: "bg-yellow-50 border border-yellow-200 rounded-lg p-3 md:p-4"
};
const _hoisted_32$1 = { class: "flex items-start gap-2 md:gap-3" };
const _hoisted_33$1 = { class: "text-xs md:text-sm font-medium text-yellow-900" };
const _hoisted_34$1 = { class: "text-xs md:text-sm text-yellow-700 mt-1 md:mt-2" };
const _hoisted_35$1 = {
  key: 2,
  class: "bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm"
};
const _hoisted_36$1 = ["aria-label", "aria-expanded"];
const _hoisted_37$1 = { class: "text-start" };
const _hoisted_38$1 = { class: "text-sm md:text-lg font-medium text-gray-900" };
const _hoisted_39$1 = { class: "text-xs md:text-sm text-gray-500" };
const _hoisted_40$1 = { class: "border-t border-gray-200" };
const _hoisted_41$1 = { class: "md:hidden divide-y divide-gray-200" };
const _hoisted_42$1 = { class: "flex justify-between items-start mb-2" };
const _hoisted_43 = { class: "flex items-center gap-2" };
const _hoisted_44 = {
  key: 0,
  class: "px-1.5 py-0.5 text-xs font-medium bg-red-200 text-red-800 rounded"
};
const _hoisted_45 = { class: "flex justify-between items-center text-xs text-gray-600" };
const _hoisted_46 = { class: "text-gray-500" };
const _hoisted_47 = { class: "bg-gray-50 p-3" };
const _hoisted_48 = { class: "flex justify-between items-center" };
const _hoisted_49 = { class: "text-xs font-semibold text-gray-700" };
const _hoisted_50 = { class: "text-sm font-bold text-gray-900" };
const _hoisted_51 = { class: "hidden md:block overflow-x-auto" };
const _hoisted_52 = { class: "min-w-full divide-y divide-gray-200" };
const _hoisted_53 = { class: "bg-gray-50" };
const _hoisted_54 = { class: "px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase" };
const _hoisted_55 = { class: "px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase" };
const _hoisted_56 = { class: "px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase" };
const _hoisted_57 = { class: "px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase" };
const _hoisted_58 = { class: "px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase" };
const _hoisted_59 = { class: "bg-white divide-y divide-gray-200" };
const _hoisted_60 = { class: "text-start px-6 py-4 whitespace-nowrap" };
const _hoisted_61 = { class: "text-start px-6 py-4 whitespace-nowrap" };
const _hoisted_62 = {
  key: 0,
  class: "px-2 py-1 text-xs font-medium bg-red-200 text-red-800 rounded"
};
const _hoisted_63 = {
  key: 1,
  class: "px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded"
};
const _hoisted_64 = { class: "text-start px-6 py-4 whitespace-nowrap text-sm text-gray-600" };
const _hoisted_65 = { class: "text-start px-6 py-4 whitespace-nowrap text-sm text-gray-500" };
const _hoisted_66 = { class: "text-start px-6 py-4 whitespace-nowrap" };
const _hoisted_67 = { class: "bg-gray-50" };
const _hoisted_68 = {
  colspan: "4",
  class: "px-6 py-4 text-start text-sm font-semibold text-gray-700"
};
const _hoisted_69 = { class: "px-6 py-4 whitespace-nowrap text-start" };
const _hoisted_70 = { class: "text-base font-bold text-gray-900" };
const _hoisted_71 = { class: "bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm" };
const _hoisted_72 = { class: "flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2" };
const _hoisted_73 = { class: "text-start flex items-center gap-2" };
const _hoisted_74 = { class: "text-sm md:text-lg font-semibold text-gray-900" };
const _hoisted_75 = {
  key: 0,
  class: "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
};
const _hoisted_76 = { class: "text-xs md:text-sm text-gray-600" };
const _hoisted_77 = {
  key: 0,
  class: "text-start sm:text-end"
};
const _hoisted_78 = { class: "text-xs mb-1 text-gray-500 uppercase" };
const _hoisted_79 = { class: "p-3 md:p-6" };
const _hoisted_80 = {
  key: 0,
  class: "flex flex-col gap-3 md:gap-4"
};
const _hoisted_81 = { class: "flex items-center justify-between gap-3" };
const _hoisted_82 = { class: "flex items-center gap-2 md:gap-3 flex-1" };
const _hoisted_83 = { class: "text-base md:text-xl" };
const _hoisted_84 = ["for"];
const _hoisted_85 = { class: "w-40 md:w-48" };
const _hoisted_86 = {
  key: 1,
  class: "flex flex-col gap-4 md:gap-5"
};
const _hoisted_87 = { class: "flex items-start justify-between mb-3 md:mb-4 gap-2" };
const _hoisted_88 = { class: "flex items-center gap-2 md:gap-3" };
const _hoisted_89 = { class: "text-base md:text-xl" };
const _hoisted_90 = { class: "text-start text-sm md:text-base font-semibold text-gray-900" };
const _hoisted_91 = {
  key: 0,
  class: "flex-shrink-0"
};
const _hoisted_92 = {
  key: 0,
  class: "inline-flex items-center px-2 md:px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
};
const _hoisted_93 = {
  key: 1,
  class: "inline-flex items-center px-2 md:px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
};
const _hoisted_94 = {
  key: 2,
  class: "inline-flex items-center px-2 md:px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
};
const _hoisted_95 = { class: "grid grid-cols-1 sm:grid-cols-3 gap-2 md:gap-3" };
const _hoisted_96 = { class: "text-start bg-white rounded-lg p-2 md:p-3 border border-gray-200" };
const _hoisted_97 = { class: "block text-xs font-medium text-gray-500 uppercase mb-0.5 md:mb-1" };
const _hoisted_98 = { class: "text-base md:text-lg font-semibold text-gray-900" };
const _hoisted_99 = { class: "text-xs text-gray-500 mt-0.5 md:mt-1 hidden sm:block" };
const _hoisted_100 = { class: "text-start bg-white rounded-lg p-2 md:p-3 border border-gray-200" };
const _hoisted_101 = { class: "block text-xs font-medium text-gray-500 uppercase mb-0.5 md:mb-1" };
const _hoisted_102 = { class: "text-base md:text-lg font-semibold text-gray-900" };
const _hoisted_103 = { class: "text-xs text-gray-500 mt-0.5 md:mt-1 hidden sm:block" };
const _hoisted_104 = { key: 0 };
const _hoisted_105 = { key: 1 };
const _hoisted_106 = { class: "text-start bg-white rounded-lg p-2 md:p-3 border border-gray-300" };
const _hoisted_107 = { class: "block text-xs font-medium text-gray-700 uppercase mb-0.5 md:mb-1" };
const _hoisted_108 = { class: "text-xs text-gray-500 mt-0.5 md:mt-1 hidden sm:block" };
const _hoisted_109 = { class: "flex items-center justify-between gap-2" };
const _hoisted_110 = { class: "flex-1" };
const _hoisted_111 = {
  key: 0,
  class: "text-start bg-gray-50 px-3 py-3 md:px-6 md:py-4 border-t border-gray-200"
};
const _hoisted_112 = { class: "grid grid-cols-3 gap-2 md:gap-4" };
const _hoisted_113 = { class: "text-xs md:text-sm text-gray-600" };
const _hoisted_114 = { class: "text-base md:text-xl font-semibold text-gray-900" };
const _hoisted_115 = { class: "text-xs md:text-sm text-gray-600" };
const _hoisted_116 = { class: "text-base md:text-xl font-semibold text-gray-900" };
const _hoisted_117 = { class: "text-xs md:text-sm text-gray-600" };
const _hoisted_118 = {
  key: 3,
  class: "bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm"
};
const _hoisted_119 = { class: "px-3 py-3 md:px-6 md:py-4 bg-gray-50 border-b border-gray-200" };
const _hoisted_120 = { class: "text-sm md:text-lg font-medium text-gray-900" };
const _hoisted_121 = { class: "p-3 md:p-6" };
const _hoisted_122 = { class: "flex flex-col gap-2 md:gap-3" };
const _hoisted_123 = { class: "text-xs md:text-sm font-medium text-gray-900" };
const _hoisted_124 = { class: "text-xs text-gray-500" };
const _hoisted_125 = { class: "text-end" };
const _hoisted_126 = { class: "text-sm md:text-base font-semibold text-gray-900" };
const _hoisted_127 = { class: "mt-3 md:mt-4 pt-3 md:pt-4 border-t border-gray-200" };
const _hoisted_128 = { class: "flex items-center justify-between" };
const _hoisted_129 = { class: "text-xs md:text-sm font-medium text-gray-700" };
const _hoisted_130 = { class: "text-base md:text-lg font-bold text-gray-900" };
const _hoisted_131 = {
  key: 4,
  class: "rounded-lg bg-red-50 border border-red-200 p-3 md:p-4"
};
const _hoisted_132 = { class: "flex gap-2 md:gap-3" };
const _hoisted_133 = { class: "flex-1" };
const _hoisted_134 = { class: "text-xs md:text-sm font-medium text-red-800" };
const _hoisted_135 = { class: "text-xs md:text-sm text-red-700 mt-1" };
const _hoisted_136 = {
  key: 5,
  class: "rounded-lg bg-red-50 border border-red-200 p-3 md:p-4"
};
const _hoisted_137 = { class: "flex gap-2 md:gap-3" };
const _hoisted_138 = { class: "flex-1" };
const _hoisted_139 = { class: "text-xs md:text-sm font-medium text-red-800" };
const _hoisted_140 = { class: "text-xs md:text-sm text-red-700 mt-1" };
const _hoisted_141 = {
  key: 2,
  class: "rounded-lg bg-red-50 border border-red-200 p-3 md:p-4"
};
const _hoisted_142 = { class: "flex gap-2 md:gap-3" };
const _hoisted_143 = { class: "text-xs md:text-sm font-medium text-red-800" };
const _hoisted_144 = { class: "text-xs md:text-sm text-red-700 mt-1" };
const _hoisted_145 = { class: "flex flex-col sm:flex-row justify-between w-full items-stretch sm:items-center gap-2 sm:gap-0" };
const _hoisted_146 = { class: "flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3 order-1 sm:order-2" };
const _hoisted_147 = {
  key: 0,
  class: "text-xs md:text-sm text-yellow-600 font-medium text-center sm:text-end"
};
const _hoisted_148 = {
  key: 1,
  class: "text-xs md:text-sm text-green-600 font-medium text-center sm:text-end"
};
const _sfc_main$1 = {
  __name: "ShiftClosingDialog",
  props: {
    modelValue: {
      type: Boolean,
      required: true
    },
    openingShift: {
      type: String,
      required: true,
      validator: (value) => value && value.length > 0
    }
  },
  emits: ["update:modelValue", "shift-closed"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const open = computed({
      get: () => props.modelValue,
      set: (value) => emit("update:modelValue", value)
    });
    const { getClosingShiftData, submitClosingShift } = useShift();
    const { formatCurrency: formatCurrency2, formatQuantity: formatQuantity2, formatDateTime: formatDateTime2, formatTime: formatTime2 } = useFormatters();
    const posSettingsStore = usePOSSettingsStore();
    const { hideExpectedAmount } = storeToRefs(posSettingsStore);
    const closingData = ref(null);
    const closingDataResource = getClosingShiftData;
    const submitResource = submitClosingShift;
    const showInvoiceDetails = ref(false);
    const showSuccessReport = ref(false);
    const errorMessage = ref("");
    const pendingStockCount = ref(0);
    function loadPendingStockCount() {
      return __async(this, null, function* () {
        var _a, _b;
        try {
          const res = yield call(
            "ecs_posnext.api.pending_stock.count_pending_stock_invoices",
            { pos_opening_shift: props.openingShift }
          );
          pendingStockCount.value = Number((_b = (_a = res == null ? void 0 : res.message) != null ? _a : res) != null ? _b : 0);
        } catch (e) {
          console.error("Pending-stock count failed", e);
          pendingStockCount.value = 0;
        }
      });
    }
    watch(open, (isOpen) => __async(this, null, function* () {
      if (isOpen && props.openingShift) {
        yield posSettingsStore.reloadSettings();
        loadClosingData();
        loadPendingStockCount();
      }
    }));
    function loadClosingData() {
      return __async(this, null, function* () {
        try {
          errorMessage.value = "";
          const data = yield closingDataResource.submit({
            opening_shift: props.openingShift
          });
          if (data.payment_reconciliation) {
            data.payment_reconciliation = data.payment_reconciliation.map(
              (payment) => {
                var _a, _b;
                return reactive(__spreadProps(__spreadValues({}, payment), {
                  closing_amount: (_b = (_a = payment.closing_amount) != null ? _a : payment.expected_amount) != null ? _b : 0,
                  difference: 0
                }));
              }
            );
            data.payment_reconciliation.forEach((payment) => {
              calculateDifference(payment);
            });
          }
          closingData.value = data;
          if (invoiceCount.value > 0 && invoiceCount.value <= 10) {
            showInvoiceDetails.value = true;
          }
        } catch (error) {
          console.error("Error loading closing data:", error);
          errorMessage.value = "Unable to load shift data. Please check your connection and try again.";
        }
      });
    }
    function calculateDifference(payment) {
      const closing = Number.parseFloat(payment.closing_amount) || 0;
      const expected = Number.parseFloat(payment.expected_amount) || 0;
      payment.difference = closing - expected;
    }
    function updateClosingAmount(payment, value) {
      payment.closing_amount = value;
      calculateDifference(payment);
    }
    const canSubmit = computed(() => {
      if (!closingData.value || !closingData.value.payment_reconciliation)
        return false;
      if (pendingStockCount.value > 0) return false;
      return closingData.value.payment_reconciliation.every(
        (payment) => payment.closing_amount !== null && payment.closing_amount !== void 0 && payment.closing_amount !== ""
      );
    });
    function submitClosing() {
      return __async(this, null, function* () {
        if (!closingData.value) return;
        try {
          errorMessage.value = "";
          if (closingData.value.payment_reconciliation) {
            closingData.value.payment_reconciliation.forEach((payment) => {
              calculateDifference(payment);
            });
          }
          const result = yield submitResource.submit({
            closing_shift: closingData.value
          });
          if (result && result.name) {
            printClosingShift(result.name);
          }
          if (hideExpectedAmount.value) {
            showSuccessReport.value = true;
            if (invoiceCount.value > 0 && invoiceCount.value <= 10) {
              showInvoiceDetails.value = true;
            }
          } else {
            emit("shift-closed");
            closeDialog();
          }
        } catch (error) {
          console.error("Error submitting closing shift:", error);
          errorMessage.value = "Failed to close shift. Please verify all amounts and try again.";
        }
      });
    }
    function printClosingShift(name) {
      const params = new URLSearchParams({
        doctype: "POS Closing Shift",
        name,
        format: "POS Closing Shift",
        no_letterhead: 1,
        _lang: "en",
        trigger_print: 1,
        _t: Date.now()
      });
      window.open(
        `/printview?${params.toString()}`,
        "_blank",
        "width=800,height=600"
      );
    }
    function closeDialog() {
      if (showSuccessReport.value) {
        emit("shift-closed");
      }
      open.value = false;
      closingData.value = null;
      showInvoiceDetails.value = false;
      showSuccessReport.value = false;
      errorMessage.value = "";
    }
    const shouldShowSummary = computed(
      () => !hideExpectedAmount.value || showSuccessReport.value
    );
    const isInEntryMode = computed(
      () => hideExpectedAmount.value && !showSuccessReport.value
    );
    const reconciliationMessage = computed(() => {
      if (isInEntryMode.value) {
        return "Enter the actual counted amounts for each payment method";
      }
      if (showSuccessReport.value && hideExpectedAmount.value) {
        return "Shift closed successfully - Review the final reconciliation below";
      }
      return "Count your cash and enter actual amounts below";
    });
    const invoiceCount = computed(() => {
      if (!closingData.value) return 0;
      const transactions = closingData.value.pos_transactions || [];
      return transactions.length;
    });
    const hasReturns = computed(() => {
      if (!closingData.value) return false;
      return (closingData.value.returns_count || 0) > 0;
    });
    const salesInvoiceCount = computed(() => {
      if (!closingData.value) return 0;
      const transactions = closingData.value.pos_transactions || [];
      return transactions.filter((t) => !t.is_return).length;
    });
    const totalTax = computed(() => {
      if (!closingData.value || !closingData.value.taxes) return 0;
      return closingData.value.taxes.reduce(
        (sum, tax) => sum + Number.parseFloat(tax.amount || 0),
        0
      );
    });
    const grossSales = computed(() => {
      var _a, _b;
      if (!closingData.value) return 0;
      return (_b = (_a = closingData.value.sales_total) != null ? _a : closingData.value.grand_total) != null ? _b : 0;
    });
    const getTotalExpected = computed(() => {
      if (!closingData.value || !closingData.value.payment_reconciliation) return 0;
      return closingData.value.payment_reconciliation.reduce(
        (sum, payment) => sum + Number.parseFloat(payment.expected_amount || 0),
        0
      );
    });
    const getTotalActual = computed(() => {
      if (!closingData.value || !closingData.value.payment_reconciliation) return 0;
      return closingData.value.payment_reconciliation.reduce(
        (sum, payment) => sum + Number.parseFloat(payment.closing_amount || 0),
        0
      );
    });
    const getTotalDifference = computed(() => {
      return getTotalActual.value - getTotalExpected.value;
    });
    function getSalesForPayment(payment) {
      return Number.parseFloat(payment.expected_amount || 0) - Number.parseFloat(payment.opening_amount || 0);
    }
    function getShiftDuration() {
      if (!closingData.value || !closingData.value.period_start_date)
        return __("N/A");
      const start = new Date(closingData.value.period_start_date);
      const end = /* @__PURE__ */ new Date();
      const diff = end - start;
      const hours = Math.floor(diff / (1e3 * 60 * 60));
      const minutes = Math.floor(diff % (1e3 * 60 * 60) / (1e3 * 60));
      if (hours > 0) {
        return __("{0}h {1}m", [hours, minutes]);
      }
      return __("{0}m", [minutes]);
    }
    function getPaymentIcon(method) {
      const methodLower = method.toLowerCase();
      if (methodLower.includes("cash")) {
        return { icon: "💵", color: "bg-green-500" };
      } else if (methodLower.includes("card") || methodLower.includes("credit") || methodLower.includes("debit")) {
        return { icon: "💳", color: "bg-blue-500" };
      } else if (methodLower.includes("mobile") || methodLower.includes("wallet") || methodLower.includes("upi") || methodLower.includes("phone")) {
        return { icon: "📱", color: "bg-purple-500" };
      } else if (methodLower.includes("bank") || methodLower.includes("transfer")) {
        return { icon: "🏦", color: "bg-indigo-500" };
      } else if (methodLower.includes("cheque") || methodLower.includes("check")) {
        return { icon: "📝", color: "bg-yellow-500" };
      } else {
        return { icon: "💰", color: "bg-gray-500" };
      }
    }
    return (_ctx, _cache) => {
      return openBlock(), createBlock(unref(Dialog), {
        modelValue: open.value,
        "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => open.value = $event),
        options: { title: _ctx.__("Close POS Shift mahmoud"), size: "4xl" }
      }, {
        "body-content": withCtx(() => [
          createBaseVNode("div", _hoisted_1$1, [
            unref(closingDataResource).loading ? (openBlock(), createElementBlock("div", _hoisted_2$1, [
              _cache[3] || (_cache[3] = createBaseVNode("div", { class: "inline-block animate-spin rounded-full h-12 w-12 md:h-16 md:w-16 border-b-4 border-blue-600" }, null, -1)),
              createBaseVNode("p", _hoisted_3$1, toDisplayString(_ctx.__("Loading shift data...")), 1),
              createBaseVNode("p", _hoisted_4$1, toDisplayString(_ctx.__("Calculating totals and reconciliation...")), 1)
            ])) : closingData.value ? (openBlock(), createElementBlock("div", _hoisted_5$1, [
              shouldShowSummary.value ? (openBlock(), createElementBlock("div", _hoisted_6$1, [
                createBaseVNode("div", _hoisted_7$1, [
                  createBaseVNode("div", _hoisted_8$1, [
                    createBaseVNode("h3", _hoisted_9$1, toDisplayString(closingData.value.pos_profile), 1),
                    createBaseVNode("p", _hoisted_10$1, toDisplayString(unref(formatDateTime2)(closingData.value.period_start_date)), 1)
                  ]),
                  createBaseVNode("div", _hoisted_11$1, [
                    createBaseVNode("div", _hoisted_12$1, toDisplayString(_ctx.__("Duration")), 1),
                    createBaseVNode("div", _hoisted_13$1, toDisplayString(getShiftDuration()), 1)
                  ])
                ]),
                createBaseVNode("div", _hoisted_14$1, [
                  createBaseVNode("div", _hoisted_15$1, [
                    createBaseVNode("div", _hoisted_16$1, toDisplayString(_ctx.__("Gross Sales")), 1),
                    createBaseVNode("div", _hoisted_17$1, toDisplayString(unref(formatCurrency2)(grossSales.value)), 1),
                    createBaseVNode("div", _hoisted_18$1, toDisplayString(_ctx.__("{0} invoices", [closingData.value.sales_count || salesInvoiceCount.value])), 1)
                  ]),
                  hasReturns.value ? (openBlock(), createElementBlock("div", _hoisted_19$1, [
                    createBaseVNode("div", _hoisted_20$1, toDisplayString(_ctx.__("Returns")), 1),
                    createBaseVNode("div", _hoisted_21$1, "-" + toDisplayString(unref(formatCurrency2)(closingData.value.returns_total)), 1),
                    createBaseVNode("div", _hoisted_22$1, toDisplayString(_ctx.__("{0} returns", [closingData.value.returns_count])), 1)
                  ])) : createCommentVNode("", true),
                  createBaseVNode("div", _hoisted_23$1, [
                    createBaseVNode("div", _hoisted_24$1, toDisplayString(_ctx.__("Net Sales")), 1),
                    createBaseVNode("div", _hoisted_25$1, toDisplayString(unref(formatCurrency2)(closingData.value.grand_total)), 1),
                    createBaseVNode("div", _hoisted_26$1, toDisplayString(_ctx.__("After returns")), 1)
                  ]),
                  createBaseVNode("div", _hoisted_27$1, [
                    createBaseVNode("div", _hoisted_28$1, toDisplayString(_ctx.__("Tax Collected")), 1),
                    createBaseVNode("div", _hoisted_29$1, toDisplayString(unref(formatCurrency2)(totalTax.value)), 1),
                    createBaseVNode("div", _hoisted_30$1, toDisplayString(_ctx.__("Net tax")), 1)
                  ])
                ])
              ])) : createCommentVNode("", true),
              shouldShowSummary.value && invoiceCount.value === 0 ? (openBlock(), createElementBlock("div", _hoisted_31$1, [
                createBaseVNode("div", _hoisted_32$1, [
                  _cache[4] || (_cache[4] = createBaseVNode("div", { class: "flex-shrink-0" }, [
                    createBaseVNode("svg", {
                      class: "h-4 w-4 md:h-5 md:w-5 text-yellow-600",
                      fill: "currentColor",
                      viewBox: "0 0 20 20"
                    }, [
                      createBaseVNode("path", {
                        "fill-rule": "evenodd",
                        d: "M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z",
                        "clip-rule": "evenodd"
                      })
                    ])
                  ], -1)),
                  createBaseVNode("div", null, [
                    createBaseVNode("h3", _hoisted_33$1, toDisplayString(_ctx.__("No Sales During This Shift")), 1),
                    createBaseVNode("p", _hoisted_34$1, toDisplayString(_ctx.__("No invoices were created. Closing amounts should match opening amounts.")), 1)
                  ])
                ])
              ])) : createCommentVNode("", true),
              shouldShowSummary.value && invoiceCount.value > 0 ? (openBlock(), createElementBlock("div", _hoisted_35$1, [
                createBaseVNode("button", {
                  onClick: _cache[0] || (_cache[0] = ($event) => showInvoiceDetails.value = !showInvoiceDetails.value),
                  "aria-label": `${showInvoiceDetails.value ? "Hide" : "Show"} invoice details for ${invoiceCount.value} transactions`,
                  "aria-expanded": showInvoiceDetails.value,
                  class: "w-full px-3 py-3 md:px-6 md:py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                }, [
                  createBaseVNode("div", _hoisted_37$1, [
                    createBaseVNode("h3", _hoisted_38$1, toDisplayString(_ctx.__("Invoice Details")), 1),
                    createBaseVNode("p", _hoisted_39$1, toDisplayString(_ctx.__("{0} transactions • {1}", [
                      invoiceCount.value,
                      unref(formatCurrency2)(closingData.value.grand_total)
                    ])), 1)
                  ]),
                  (openBlock(), createElementBlock("svg", {
                    class: normalizeClass(["h-4 w-4 md:h-5 md:w-5 text-gray-400 transition-transform", showInvoiceDetails.value ? "transform rotate-180" : ""]),
                    fill: "none",
                    stroke: "currentColor",
                    viewBox: "0 0 24 24"
                  }, _cache[5] || (_cache[5] = [
                    createBaseVNode("path", {
                      "stroke-linecap": "round",
                      "stroke-linejoin": "round",
                      "stroke-width": "2",
                      d: "M19 9l-7 7-7-7"
                    }, null, -1)
                  ]), 2))
                ], 8, _hoisted_36$1),
                withDirectives(createBaseVNode("div", _hoisted_40$1, [
                  createBaseVNode("div", _hoisted_41$1, [
                    (openBlock(true), createElementBlock(Fragment, null, renderList(closingData.value.pos_transactions, (invoice, idx) => {
                      return openBlock(), createElementBlock("div", {
                        key: idx,
                        class: normalizeClass(["p-3", invoice.is_return ? "bg-red-50 hover:bg-red-100" : "hover:bg-gray-50"])
                      }, [
                        createBaseVNode("div", _hoisted_42$1, [
                          createBaseVNode("div", _hoisted_43, [
                            createBaseVNode("span", {
                              class: normalizeClass(["text-xs font-medium", invoice.is_return ? "text-red-700" : "text-gray-900"])
                            }, toDisplayString(invoice.pos_invoice || invoice.sales_invoice || _ctx.__("N/A")), 3),
                            invoice.is_return ? (openBlock(), createElementBlock("span", _hoisted_44, toDisplayString(_ctx.__("Return")), 1)) : createCommentVNode("", true)
                          ]),
                          createBaseVNode("span", {
                            class: normalizeClass(["text-sm font-semibold", invoice.is_return ? "text-red-700" : "text-gray-900"])
                          }, toDisplayString(unref(formatCurrency2)(invoice.grand_total)), 3)
                        ]),
                        createBaseVNode("div", _hoisted_45, [
                          createBaseVNode("span", null, toDisplayString(invoice.customer), 1),
                          createBaseVNode("span", _hoisted_46, toDisplayString(unref(formatTime2)(invoice.posting_date)), 1)
                        ])
                      ], 2);
                    }), 128)),
                    createBaseVNode("div", _hoisted_47, [
                      createBaseVNode("div", _hoisted_48, [
                        createBaseVNode("span", _hoisted_49, toDisplayString(_ctx.__("Net Total:")), 1),
                        createBaseVNode("span", _hoisted_50, toDisplayString(unref(formatCurrency2)(closingData.value.grand_total)), 1)
                      ])
                    ])
                  ]),
                  createBaseVNode("div", _hoisted_51, [
                    createBaseVNode("table", _hoisted_52, [
                      createBaseVNode("thead", _hoisted_53, [
                        createBaseVNode("tr", null, [
                          createBaseVNode("th", _hoisted_54, toDisplayString(_ctx.__("Invoice")), 1),
                          createBaseVNode("th", _hoisted_55, toDisplayString(_ctx.__("Type")), 1),
                          createBaseVNode("th", _hoisted_56, toDisplayString(_ctx.__("Customer")), 1),
                          createBaseVNode("th", _hoisted_57, toDisplayString(_ctx.__("Time")), 1),
                          createBaseVNode("th", _hoisted_58, toDisplayString(_ctx.__("Amount")), 1)
                        ])
                      ]),
                      createBaseVNode("tbody", _hoisted_59, [
                        (openBlock(true), createElementBlock(Fragment, null, renderList(closingData.value.pos_transactions, (invoice, idx) => {
                          return openBlock(), createElementBlock("tr", {
                            key: idx,
                            class: normalizeClass(invoice.is_return ? "bg-red-50 hover:bg-red-100" : "hover:bg-gray-50")
                          }, [
                            createBaseVNode("td", _hoisted_60, [
                              createBaseVNode("span", {
                                class: normalizeClass(["text-sm font-medium", invoice.is_return ? "text-red-700" : "text-gray-900"])
                              }, toDisplayString(invoice.pos_invoice || invoice.sales_invoice || _ctx.__("N/A")), 3)
                            ]),
                            createBaseVNode("td", _hoisted_61, [
                              invoice.is_return ? (openBlock(), createElementBlock("span", _hoisted_62, toDisplayString(_ctx.__("Return")), 1)) : (openBlock(), createElementBlock("span", _hoisted_63, toDisplayString(_ctx.__("Sale")), 1))
                            ]),
                            createBaseVNode("td", _hoisted_64, toDisplayString(invoice.customer), 1),
                            createBaseVNode("td", _hoisted_65, toDisplayString(unref(formatTime2)(invoice.posting_date)), 1),
                            createBaseVNode("td", _hoisted_66, [
                              createBaseVNode("span", {
                                class: normalizeClass(["text-sm font-semibold", invoice.is_return ? "text-red-700" : "text-gray-900"])
                              }, toDisplayString(unref(formatCurrency2)(invoice.grand_total)), 3)
                            ])
                          ], 2);
                        }), 128))
                      ]),
                      createBaseVNode("tfoot", _hoisted_67, [
                        createBaseVNode("tr", null, [
                          createBaseVNode("td", _hoisted_68, toDisplayString(_ctx.__("Net Total:")), 1),
                          createBaseVNode("td", _hoisted_69, [
                            createBaseVNode("span", _hoisted_70, toDisplayString(unref(formatCurrency2)(closingData.value.grand_total)), 1)
                          ])
                        ])
                      ])
                    ])
                  ])
                ], 512), [
                  [vShow, showInvoiceDetails.value]
                ])
              ])) : createCommentVNode("", true),
              createBaseVNode("div", _hoisted_71, [
                createBaseVNode("div", {
                  class: normalizeClass([
                    "px-3 py-3 md:px-6 md:py-4 border-b border-gray-200",
                    unref(hideExpectedAmount) && showSuccessReport.value ? "bg-green-50 border-green-200" : "bg-gray-50"
                  ])
                }, [
                  createBaseVNode("div", _hoisted_72, [
                    createBaseVNode("div", null, [
                      createBaseVNode("div", _hoisted_73, [
                        createBaseVNode("h3", _hoisted_74, toDisplayString(_ctx.__("Payment Reconciliation")), 1),
                        unref(hideExpectedAmount) && showSuccessReport.value ? (openBlock(), createElementBlock("span", _hoisted_75, toDisplayString(_ctx.__("✓ Shift Closed")), 1)) : createCommentVNode("", true)
                      ]),
                      createBaseVNode("p", _hoisted_76, toDisplayString(reconciliationMessage.value), 1)
                    ]),
                    shouldShowSummary.value && getTotalDifference.value !== 0 ? (openBlock(), createElementBlock("div", _hoisted_77, [
                      createBaseVNode("div", _hoisted_78, toDisplayString(_ctx.__("Total Variance")), 1),
                      createBaseVNode("div", {
                        class: normalizeClass([
                          "text-lg md:text-xl font-bold",
                          getTotalDifference.value > 0 ? "text-blue-600" : "text-red-600"
                        ])
                      }, toDisplayString(getTotalDifference.value > 0 ? "+" : "") + toDisplayString(unref(formatCurrency2)(Math.abs(getTotalDifference.value))), 3)
                    ])) : createCommentVNode("", true)
                  ])
                ], 2),
                createBaseVNode("div", _hoisted_79, [
                  isInEntryMode.value ? (openBlock(), createElementBlock("div", _hoisted_80, [
                    (openBlock(true), createElementBlock(Fragment, null, renderList(closingData.value.payment_reconciliation, (payment, idx) => {
                      return openBlock(), createElementBlock("div", {
                        key: idx,
                        class: "border border-gray-200 rounded-lg p-3 md:p-4 bg-white hover:border-gray-300 transition-colors"
                      }, [
                        createBaseVNode("div", _hoisted_81, [
                          createBaseVNode("div", _hoisted_82, [
                            createBaseVNode("div", {
                              class: normalizeClass(["rounded-lg p-1.5 md:p-2 flex-shrink-0", getPaymentIcon(payment.mode_of_payment).color])
                            }, [
                              createBaseVNode("span", _hoisted_83, toDisplayString(getPaymentIcon(payment.mode_of_payment).icon), 1)
                            ], 2),
                            createBaseVNode("label", {
                              for: `payment-${idx}`,
                              class: "text-start text-sm md:text-base font-semibold text-gray-900 cursor-pointer"
                            }, toDisplayString(payment.mode_of_payment), 9, _hoisted_84)
                          ]),
                          createBaseVNode("div", _hoisted_85, [
                            createVNode(unref(Input), {
                              id: `payment-${idx}`,
                              modelValue: payment.closing_amount,
                              "onUpdate:modelValue": (value) => updateClosingAmount(payment, value),
                              type: "number",
                              step: "10",
                              min: "0",
                              placeholder: "0.00",
                              disabled: unref(submitResource).loading,
                              "aria-label": _ctx.__("Enter actual amount for {0}", [payment.mode_of_payment]),
                              class: "text-base md:text-lg text-center font-semibold"
                            }, null, 8, ["id", "modelValue", "onUpdate:modelValue", "disabled", "aria-label"])
                          ])
                        ])
                      ]);
                    }), 128))
                  ])) : (openBlock(), createElementBlock("div", _hoisted_86, [
                    (openBlock(true), createElementBlock(Fragment, null, renderList(closingData.value.payment_reconciliation, (payment, idx) => {
                      return openBlock(), createElementBlock("div", {
                        key: idx,
                        class: normalizeClass([
                          "border rounded-lg p-3 md:p-5 transition-all",
                          payment.difference === 0 ? "border-green-200 bg-green-50" : payment.difference > 0 ? "border-blue-200 bg-blue-50" : "border-red-200 bg-red-50"
                        ])
                      }, [
                        createBaseVNode("div", _hoisted_87, [
                          createBaseVNode("div", _hoisted_88, [
                            createBaseVNode("div", {
                              class: normalizeClass(["rounded-lg p-1.5 md:p-2", getPaymentIcon(payment.mode_of_payment).color])
                            }, [
                              createBaseVNode("span", _hoisted_89, toDisplayString(getPaymentIcon(payment.mode_of_payment).icon), 1)
                            ], 2),
                            createBaseVNode("div", null, [
                              createBaseVNode("h4", _hoisted_90, toDisplayString(payment.mode_of_payment), 1),
                              createVNode(_sfc_main$2, {
                                tag: "p",
                                class: "text-xs md:text-sm text-gray-600",
                                inner: _ctx.__('Expected: <span class="font-medium">{0}</span>', [unref(formatCurrency2)(payment.expected_amount)])
                              }, null, 8, ["inner"])
                            ])
                          ]),
                          payment.closing_amount !== null && payment.closing_amount !== void 0 ? (openBlock(), createElementBlock("div", _hoisted_91, [
                            payment.difference === 0 ? (openBlock(), createElementBlock("span", _hoisted_92, toDisplayString(_ctx.__("✓ Balanced")), 1)) : payment.difference > 0 ? (openBlock(), createElementBlock("span", _hoisted_93, toDisplayString(_ctx.__("Over {0}", [unref(formatCurrency2)(payment.difference)])), 1)) : (openBlock(), createElementBlock("span", _hoisted_94, toDisplayString(_ctx.__("Short {0}", [unref(formatCurrency2)(Math.abs(payment.difference))])), 1))
                          ])) : createCommentVNode("", true)
                        ]),
                        createBaseVNode("div", _hoisted_95, [
                          createBaseVNode("div", _hoisted_96, [
                            createBaseVNode("label", _hoisted_97, toDisplayString(_ctx.__("Opening")), 1),
                            createBaseVNode("div", _hoisted_98, toDisplayString(unref(formatCurrency2)(payment.opening_amount)), 1),
                            createBaseVNode("div", _hoisted_99, toDisplayString(_ctx.__("Shift start")), 1)
                          ]),
                          createBaseVNode("div", _hoisted_100, [
                            createBaseVNode("label", _hoisted_101, toDisplayString(_ctx.__("Expected")), 1),
                            createBaseVNode("div", _hoisted_102, toDisplayString(unref(formatCurrency2)(payment.expected_amount)), 1),
                            createBaseVNode("div", _hoisted_103, [
                              getSalesForPayment(payment) > 0 ? (openBlock(), createElementBlock("span", _hoisted_104, " +" + toDisplayString(unref(formatCurrency2)(getSalesForPayment(payment))), 1)) : (openBlock(), createElementBlock("span", _hoisted_105, toDisplayString(_ctx.__("No sales")), 1))
                            ])
                          ]),
                          createBaseVNode("div", _hoisted_106, [
                            createBaseVNode("label", _hoisted_107, toDisplayString(_ctx.__("Actual Amount *")), 1),
                            createVNode(unref(Input), {
                              modelValue: payment.closing_amount,
                              "onUpdate:modelValue": (value) => updateClosingAmount(payment, value),
                              type: "number",
                              step: "0.01",
                              min: "0",
                              placeholder: "0.00",
                              disabled: showSuccessReport.value || unref(submitResource).loading,
                              "aria-label": `Enter actual amount for ${payment.mode_of_payment}`,
                              class: "text-base md:text-lg"
                            }, null, 8, ["modelValue", "onUpdate:modelValue", "disabled", "aria-label"]),
                            createBaseVNode("div", _hoisted_108, toDisplayString(showSuccessReport.value ? _ctx.__("Final Amount") : _ctx.__("Count & enter")), 1)
                          ])
                        ]),
                        payment.closing_amount !== null && payment.closing_amount !== void 0 && payment.difference !== 0 ? (openBlock(), createElementBlock("div", {
                          key: 0,
                          class: normalizeClass(["text-start mt-2 md:mt-3 p-2 md:p-3 rounded-lg", [
                            payment.difference > 0 ? "bg-blue-50 border border-blue-200" : "bg-red-50 border border-red-200"
                          ]])
                        }, [
                          createBaseVNode("div", _hoisted_109, [
                            createBaseVNode("div", _hoisted_110, [
                              createBaseVNode("p", {
                                class: normalizeClass(["text-xs md:text-sm font-medium", payment.difference > 0 ? "text-blue-900" : "text-red-900"])
                              }, toDisplayString(payment.difference > 0 ? _ctx.__("Cash Over") : _ctx.__("Cash Short")), 3),
                              createBaseVNode("p", {
                                class: normalizeClass(["text-xs", payment.difference > 0 ? "text-blue-700" : "text-red-700"])
                              }, toDisplayString(payment.difference > 0 ? _ctx.__("You have more than expected.") : _ctx.__("You have less than expected.")), 3)
                            ]),
                            createBaseVNode("div", {
                              class: normalizeClass(["text-base md:text-xl font-bold", payment.difference > 0 ? "text-blue-700" : "text-red-700"])
                            }, toDisplayString(payment.difference > 0 ? "+" : "") + toDisplayString(unref(formatCurrency2)(payment.difference)), 3)
                          ])
                        ], 2)) : createCommentVNode("", true)
                      ], 2);
                    }), 128))
                  ]))
                ]),
                shouldShowSummary.value ? (openBlock(), createElementBlock("div", _hoisted_111, [
                  createBaseVNode("div", _hoisted_112, [
                    createBaseVNode("div", null, [
                      createBaseVNode("p", _hoisted_113, toDisplayString(_ctx.__("Total Expected")), 1),
                      createBaseVNode("p", _hoisted_114, toDisplayString(unref(formatCurrency2)(getTotalExpected.value)), 1)
                    ]),
                    createBaseVNode("div", null, [
                      createBaseVNode("p", _hoisted_115, toDisplayString(_ctx.__("Total Actual")), 1),
                      createBaseVNode("p", _hoisted_116, toDisplayString(unref(formatCurrency2)(getTotalActual.value)), 1)
                    ]),
                    createBaseVNode("div", null, [
                      createBaseVNode("p", _hoisted_117, toDisplayString(_ctx.__("Net Variance")), 1),
                      createBaseVNode("p", {
                        class: normalizeClass([
                          "text-base md:text-xl font-bold",
                          getTotalDifference.value === 0 ? "text-green-600" : getTotalDifference.value > 0 ? "text-blue-600" : "text-red-600"
                        ])
                      }, toDisplayString(getTotalDifference.value === 0 ? "✓ " : getTotalDifference.value > 0 ? "+" : "") + toDisplayString(unref(formatCurrency2)(Math.abs(getTotalDifference.value))), 3)
                    ])
                  ])
                ])) : createCommentVNode("", true)
              ]),
              shouldShowSummary.value && closingData.value.taxes && closingData.value.taxes.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_118, [
                createBaseVNode("div", _hoisted_119, [
                  createBaseVNode("h3", _hoisted_120, toDisplayString(_ctx.__("Tax Summary")), 1)
                ]),
                createBaseVNode("div", _hoisted_121, [
                  createBaseVNode("div", _hoisted_122, [
                    (openBlock(true), createElementBlock(Fragment, null, renderList(closingData.value.taxes, (tax, idx) => {
                      return openBlock(), createElementBlock("div", {
                        key: idx,
                        class: "flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
                      }, [
                        createBaseVNode("div", null, [
                          createBaseVNode("p", _hoisted_123, toDisplayString(tax.account_head), 1),
                          createBaseVNode("p", _hoisted_124, toDisplayString(unref(formatQuantity2)(tax.rate)) + "%", 1)
                        ]),
                        createBaseVNode("div", _hoisted_125, [
                          createBaseVNode("p", _hoisted_126, toDisplayString(unref(formatCurrency2)(tax.amount)), 1)
                        ])
                      ]);
                    }), 128))
                  ]),
                  createBaseVNode("div", _hoisted_127, [
                    createBaseVNode("div", _hoisted_128, [
                      createBaseVNode("span", _hoisted_129, toDisplayString(_ctx.__("Total Tax Collected")), 1),
                      createBaseVNode("span", _hoisted_130, toDisplayString(unref(formatCurrency2)(totalTax.value)), 1)
                    ])
                  ])
                ])
              ])) : createCommentVNode("", true),
              pendingStockCount.value > 0 ? (openBlock(), createElementBlock("div", _hoisted_131, [
                createBaseVNode("div", _hoisted_132, [
                  _cache[6] || (_cache[6] = createBaseVNode("svg", {
                    class: "h-4 w-4 md:h-5 md:w-5 text-red-600 flex-shrink-0",
                    fill: "currentColor",
                    viewBox: "0 0 20 20"
                  }, [
                    createBaseVNode("path", {
                      "fill-rule": "evenodd",
                      d: "M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z",
                      "clip-rule": "evenodd"
                    })
                  ], -1)),
                  createBaseVNode("div", _hoisted_133, [
                    createBaseVNode("h4", _hoisted_134, toDisplayString(_ctx.__("Pending Stock Invoices")), 1),
                    createBaseVNode("p", _hoisted_135, toDisplayString(_ctx.__("{0} invoice(s) are held pending stock. Finalize them from the Pending Stock page before closing the shift.", [pendingStockCount.value])), 1)
                  ])
                ])
              ])) : createCommentVNode("", true),
              unref(submitResource).error || errorMessage.value && !unref(closingDataResource).error ? (openBlock(), createElementBlock("div", _hoisted_136, [
                createBaseVNode("div", _hoisted_137, [
                  _cache[7] || (_cache[7] = createBaseVNode("svg", {
                    class: "h-4 w-4 md:h-5 md:w-5 text-red-600 flex-shrink-0",
                    fill: "currentColor",
                    viewBox: "0 0 20 20"
                  }, [
                    createBaseVNode("path", {
                      "fill-rule": "evenodd",
                      d: "M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z",
                      "clip-rule": "evenodd"
                    })
                  ], -1)),
                  createBaseVNode("div", _hoisted_138, [
                    createBaseVNode("h4", _hoisted_139, toDisplayString(_ctx.__("Error Closing Shift")), 1),
                    createBaseVNode("p", _hoisted_140, toDisplayString(errorMessage.value || unref(submitResource).error), 1),
                    errorMessage.value ? (openBlock(), createElementBlock("button", {
                      key: 0,
                      onClick: _cache[1] || (_cache[1] = ($event) => errorMessage.value = ""),
                      class: "mt-2 text-xs text-red-600 hover:text-red-800 underline"
                    }, toDisplayString(_ctx.__("Dismiss")), 1)) : createCommentVNode("", true)
                  ])
                ])
              ])) : createCommentVNode("", true)
            ])) : unref(closingDataResource).error || errorMessage.value ? (openBlock(), createElementBlock("div", _hoisted_141, [
              createBaseVNode("div", _hoisted_142, [
                _cache[8] || (_cache[8] = createBaseVNode("svg", {
                  class: "h-4 w-4 md:h-5 md:w-5 text-red-600 flex-shrink-0",
                  fill: "currentColor",
                  viewBox: "0 0 20 20"
                }, [
                  createBaseVNode("path", {
                    "fill-rule": "evenodd",
                    d: "M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z",
                    "clip-rule": "evenodd"
                  })
                ], -1)),
                createBaseVNode("div", null, [
                  createBaseVNode("h3", _hoisted_143, toDisplayString(_ctx.__("Failed to Load Shift Data")), 1),
                  createBaseVNode("p", _hoisted_144, toDisplayString(errorMessage.value || unref(closingDataResource).error), 1)
                ])
              ])
            ])) : createCommentVNode("", true)
          ])
        ]),
        actions: withCtx(() => [
          createBaseVNode("div", _hoisted_145, [
            createVNode(unref(_sfc_main$3), {
              variant: "subtle",
              onClick: closeDialog,
              disabled: unref(submitResource).loading,
              class: "order-2 sm:order-1"
            }, {
              default: withCtx(() => [
                createTextVNode(toDisplayString(showSuccessReport.value ? _ctx.__("Close") : _ctx.__("Cancel")), 1)
              ]),
              _: 1
            }, 8, ["disabled"]),
            createBaseVNode("div", _hoisted_146, [
              !canSubmit.value && closingData.value && !showSuccessReport.value ? (openBlock(), createElementBlock("div", _hoisted_147, toDisplayString(_ctx.__("Please enter all closing amounts")), 1)) : createCommentVNode("", true),
              showSuccessReport.value ? (openBlock(), createElementBlock("div", _hoisted_148, toDisplayString(_ctx.__("✓ Shift closed successfully")), 1)) : createCommentVNode("", true),
              !showSuccessReport.value ? (openBlock(), createBlock(unref(_sfc_main$3), {
                key: 2,
                variant: "solid",
                theme: "blue",
                onClick: submitClosing,
                loading: unref(submitResource).loading,
                disabled: !canSubmit.value
              }, {
                default: withCtx(() => [
                  createTextVNode(toDisplayString(unref(submitResource).loading ? _ctx.__("Closing Shift...") : _ctx.__("Close Shift")), 1)
                ]),
                _: 1
              }, 8, ["loading", "disabled"])) : createCommentVNode("", true)
            ])
          ])
        ]),
        _: 1
      }, 8, ["modelValue", "options"]);
    };
  }
};
const _hoisted_1 = { class: "flex flex-col gap-6" };
const _hoisted_2 = {
  key: 0,
  class: "flex flex-col gap-4"
};
const _hoisted_3 = { class: "block text-sm font-medium text-gray-700 mb-2 text-start" };
const _hoisted_4 = {
  key: 0,
  class: "text-center py-4"
};
const _hoisted_5 = {
  key: 1,
  class: "grid grid-cols-1 gap-3"
};
const _hoisted_6 = ["onClick"];
const _hoisted_7 = { class: "flex justify-between items-start" };
const _hoisted_8 = { class: "text-start" };
const _hoisted_9 = { class: "font-medium text-gray-900" };
const _hoisted_10 = { class: "text-sm text-gray-500 mt-1" };
const _hoisted_11 = { class: "text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded" };
const _hoisted_12 = {
  key: 2,
  class: "text-center py-8 text-gray-500"
};
const _hoisted_13 = {
  key: 0,
  class: "rounded-md bg-red-50 p-4"
};
const _hoisted_14 = { class: "text-sm text-red-800" };
const _hoisted_15 = {
  key: 1,
  class: "flex flex-col gap-4"
};
const _hoisted_16 = { class: "mb-4" };
const _hoisted_17 = { class: "flex items-center justify-between" };
const _hoisted_18 = { class: "text-start" };
const _hoisted_19 = { class: "font-medium text-gray-900" };
const _hoisted_20 = { class: "text-sm text-gray-500" };
const _hoisted_21 = { class: "block text-sm font-medium text-gray-700 mb-3 text-start" };
const _hoisted_22 = {
  key: 0,
  class: "text-center py-4"
};
const _hoisted_23 = {
  key: 1,
  class: "flex flex-col gap-3"
};
const _hoisted_24 = { class: "flex-1 text-start" };
const _hoisted_25 = { class: "text-sm font-medium text-gray-700" };
const _hoisted_26 = { class: "w-32" };
const _hoisted_27 = {
  key: 2,
  class: "text-center py-4 text-gray-500"
};
const _hoisted_28 = { class: "text-sm" };
const _hoisted_29 = {
  key: 0,
  class: "rounded-md bg-red-50 p-4"
};
const _hoisted_30 = { class: "text-sm text-red-800" };
const _hoisted_31 = {
  key: 1,
  class: "rounded-md bg-red-50 p-4"
};
const _hoisted_32 = { class: "text-sm text-red-800" };
const _hoisted_33 = {
  key: 2,
  class: "flex flex-col gap-4"
};
const _hoisted_34 = { class: "text-center" };
const _hoisted_35 = { class: "text-lg font-medium text-gray-900 mb-2" };
const _hoisted_36 = { class: "text-sm text-gray-500 mb-6" };
const _hoisted_37 = {
  key: 0,
  class: "bg-gray-50 rounded-lg p-4 mb-6"
};
const _hoisted_38 = { class: "text-sm text-gray-600" };
const _hoisted_39 = { class: "flex gap-3 justify-center" };
const _hoisted_40 = { class: "flex justify-between w-full" };
const _hoisted_41 = { key: 1 };
const _hoisted_42 = { class: "flex gap-2" };
const _sfc_main = {
  __name: "ShiftOpeningDialog",
  props: {
    modelValue: Boolean
  },
  emits: ["update:modelValue", "shift-opened", "dialog-closed"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const open = computed({
      get: () => props.modelValue,
      set: (value) => emit("update:modelValue", value)
    });
    const { createOpeningShift, checkOpeningShift } = useShift();
    const { formatDateTime: formatDateTime2 } = useFormatters();
    const step = ref(1);
    const selectedProfile = ref(null);
    const openingBalances = ref({});
    const existingShift = ref(null);
    const showClosingDialog = ref(false);
    const closingExistingShift = ref(false);
    const restartProfileName = ref(null);
    const profilesResource = createResource({
      url: "ecs_posnext.api.pos_profile.get_pos_profiles",
      auto: false
    });
    const dialogDataResource = createResource({
      url: "ecs_posnext.api.shifts.get_opening_dialog_data",
      auto: false
    });
    const createShiftResource = createOpeningShift;
    const paymentMethods = computed(() => {
      if (!dialogDataResource.data || !selectedProfile.value) return [];
      return (dialogDataResource.data.payments_method || []).filter(
        (method) => method.parent === selectedProfile.value.name
      );
    });
    watch(
      open,
      (isOpen) => {
        if (isOpen) {
          initDialog();
        } else {
          resetDialog();
        }
      },
      { immediate: true }
    );
    watch(showClosingDialog, (isOpen) => {
      closingExistingShift.value = isOpen;
      if (!isOpen && existingShift.value) {
        restartProfileName.value = null;
      }
    });
    function initDialog() {
      return __async(this, null, function* () {
        step.value = 1;
        selectedProfile.value = null;
        existingShift.value = null;
        openingBalances.value = {};
        dialogDataResource.reset();
        try {
          yield profilesResource.fetch();
          const checkResult = yield checkOpeningShift.fetch();
          if (checkResult) {
            existingShift.value = checkResult;
            step.value = 3;
          }
        } catch (error) {
          console.error("Error initializing shift dialog:", error);
        }
      });
    }
    function resetDialog() {
      step.value = 1;
      selectedProfile.value = null;
      openingBalances.value = {};
      existingShift.value = null;
      profilesResource.reset();
      dialogDataResource.reset();
      createShiftResource.reset();
    }
    function selectPosProfile(profile) {
      selectedProfile.value = profile;
    }
    function nextStep() {
      return __async(this, null, function* () {
        if (step.value === 1 && selectedProfile.value) {
          yield dialogDataResource.fetch();
          step.value = 2;
        }
      });
    }
    function openShift() {
      return __async(this, null, function* () {
        if (!selectedProfile.value) return;
        const balance_details = paymentMethods.value.map((method) => ({
          mode_of_payment: method.mode_of_payment,
          opening_amount: Number.parseFloat(
            openingBalances.value[method.mode_of_payment] || 0
          )
        }));
        try {
          yield createShiftResource.submit({
            pos_profile: selectedProfile.value.name,
            company: selectedProfile.value.company,
            balance_details
          });
          emit("shift-opened");
          closeDialog("shift-opened");
        } catch (error) {
          console.error("Error opening shift:", error);
        }
      });
    }
    function resumeShift() {
      emit("shift-opened");
      closeDialog("resumed");
    }
    function closeAndOpenNew() {
      var _a, _b, _c;
      if (!((_b = (_a = existingShift.value) == null ? void 0 : _a.pos_opening_shift) == null ? void 0 : _b.name)) {
        return;
      }
      restartProfileName.value = ((_c = existingShift.value.pos_profile) == null ? void 0 : _c.name) || null;
      showClosingDialog.value = true;
    }
    function closeDialog(reason) {
      open.value = false;
      emit("dialog-closed", { reason });
    }
    function handleExistingShiftClosed() {
      return __async(this, null, function* () {
        var _a;
        showClosingDialog.value = false;
        const profileToRestore = restartProfileName.value;
        restartProfileName.value = null;
        existingShift.value = null;
        step.value = 1;
        openingBalances.value = {};
        yield checkOpeningShift.fetch();
        if (!profilesResource.data || profilesResource.data.length === 0) {
          yield profilesResource.fetch();
        }
        if (profileToRestore) {
          const matchedProfile = (_a = profilesResource.data) == null ? void 0 : _a.find(
            (profile) => profile.name === profileToRestore
          );
          if (matchedProfile) {
            selectedProfile.value = matchedProfile;
            yield dialogDataResource.fetch();
            step.value = 2;
          }
        }
      });
    }
    return (_ctx, _cache) => {
      var _a, _b;
      return openBlock(), createElementBlock(Fragment, null, [
        createVNode(unref(Dialog), {
          modelValue: open.value,
          "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => open.value = $event),
          options: { title: _ctx.__("Open POS Shift"), size: "xl" }
        }, {
          "body-content": withCtx(() => {
            var _a2, _b2, _c, _d;
            return [
              createBaseVNode("div", _hoisted_1, [
                step.value === 1 ? (openBlock(), createElementBlock("div", _hoisted_2, [
                  createBaseVNode("div", null, [
                    createBaseVNode("label", _hoisted_3, toDisplayString(_ctx.__("Select POS Profile")), 1),
                    unref(profilesResource).loading ? (openBlock(), createElementBlock("div", _hoisted_4, _cache[5] || (_cache[5] = [
                      createBaseVNode("div", { class: "inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" }, null, -1)
                    ]))) : unref(profilesResource).data && unref(profilesResource).data.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_5, [
                      (openBlock(true), createElementBlock(Fragment, null, renderList(unref(profilesResource).data, (profile) => {
                        var _a3;
                        return openBlock(), createElementBlock("div", {
                          key: profile.name,
                          onClick: ($event) => selectPosProfile(profile),
                          class: normalizeClass([
                            "p-4 border rounded-lg cursor-pointer transition-all",
                            ((_a3 = selectedProfile.value) == null ? void 0 : _a3.name) === profile.name ? "border-blue-500 bg-blue-50 ring-2 ring-blue-500" : "border-gray-200 hover:border-blue-300 hover:bg-gray-50"
                          ])
                        }, [
                          createBaseVNode("div", _hoisted_7, [
                            createBaseVNode("div", _hoisted_8, [
                              createBaseVNode("h3", _hoisted_9, toDisplayString(profile.name), 1),
                              createBaseVNode("p", _hoisted_10, toDisplayString(profile.company), 1)
                            ]),
                            createBaseVNode("span", _hoisted_11, toDisplayString(profile.currency), 1)
                          ])
                        ], 10, _hoisted_6);
                      }), 128))
                    ])) : (openBlock(), createElementBlock("div", _hoisted_12, [
                      createBaseVNode("p", null, toDisplayString(_ctx.__("No POS Profiles available. Please contact your administrator.")), 1)
                    ]))
                  ]),
                  unref(profilesResource).error ? (openBlock(), createElementBlock("div", _hoisted_13, [
                    createBaseVNode("p", _hoisted_14, toDisplayString(unref(profilesResource).error), 1)
                  ])) : createCommentVNode("", true)
                ])) : createCommentVNode("", true),
                step.value === 2 ? (openBlock(), createElementBlock("div", _hoisted_15, [
                  createBaseVNode("div", _hoisted_16, [
                    createBaseVNode("div", _hoisted_17, [
                      createBaseVNode("div", _hoisted_18, [
                        createBaseVNode("h3", _hoisted_19, toDisplayString((_a2 = selectedProfile.value) == null ? void 0 : _a2.name), 1),
                        createBaseVNode("p", _hoisted_20, toDisplayString((_b2 = selectedProfile.value) == null ? void 0 : _b2.company), 1)
                      ]),
                      createVNode(unref(_sfc_main$3), {
                        variant: "subtle",
                        onClick: _cache[0] || (_cache[0] = ($event) => step.value = 1)
                      }, {
                        default: withCtx(() => [
                          createTextVNode(toDisplayString(_ctx.__("Change Profile")), 1)
                        ]),
                        _: 1
                      })
                    ])
                  ]),
                  createBaseVNode("div", null, [
                    createBaseVNode("label", _hoisted_21, toDisplayString(_ctx.__("Opening Balance (Optional)")), 1),
                    unref(dialogDataResource).loading ? (openBlock(), createElementBlock("div", _hoisted_22, _cache[6] || (_cache[6] = [
                      createBaseVNode("div", { class: "inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" }, null, -1)
                    ]))) : paymentMethods.value.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_23, [
                      (openBlock(true), createElementBlock(Fragment, null, renderList(paymentMethods.value, (method) => {
                        return openBlock(), createElementBlock("div", {
                          key: method.name,
                          class: "flex items-center gap-3 p-3 border rounded-lg"
                        }, [
                          createBaseVNode("div", _hoisted_24, [
                            createBaseVNode("label", _hoisted_25, toDisplayString(method.mode_of_payment), 1)
                          ]),
                          createBaseVNode("div", _hoisted_26, [
                            createVNode(unref(Input), {
                              modelValue: openingBalances.value[method.mode_of_payment],
                              "onUpdate:modelValue": ($event) => openingBalances.value[method.mode_of_payment] = $event,
                              type: "number",
                              placeholder: "0.00",
                              step: "0.01",
                              min: "0"
                            }, null, 8, ["modelValue", "onUpdate:modelValue"])
                          ])
                        ]);
                      }), 128))
                    ])) : (openBlock(), createElementBlock("div", _hoisted_27, [
                      createBaseVNode("p", _hoisted_28, toDisplayString(_ctx.__("No payment methods configured for this POS Profile")), 1)
                    ]))
                  ]),
                  unref(dialogDataResource).error ? (openBlock(), createElementBlock("div", _hoisted_29, [
                    createBaseVNode("p", _hoisted_30, toDisplayString(unref(dialogDataResource).error), 1)
                  ])) : createCommentVNode("", true),
                  unref(createShiftResource).error ? (openBlock(), createElementBlock("div", _hoisted_31, [
                    createBaseVNode("p", _hoisted_32, toDisplayString(unref(createShiftResource).error), 1)
                  ])) : createCommentVNode("", true)
                ])) : createCommentVNode("", true),
                step.value === 3 ? (openBlock(), createElementBlock("div", _hoisted_33, [
                  createBaseVNode("div", _hoisted_34, [
                    _cache[8] || (_cache[8] = createBaseVNode("div", { class: "mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 mb-4" }, [
                      createBaseVNode("svg", {
                        class: "h-6 w-6 text-blue-600",
                        fill: "none",
                        stroke: "currentColor",
                        viewBox: "0 0 24 24"
                      }, [
                        createBaseVNode("path", {
                          "stroke-linecap": "round",
                          "stroke-linejoin": "round",
                          "stroke-width": "2",
                          d: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        })
                      ])
                    ], -1)),
                    createBaseVNode("h3", _hoisted_35, toDisplayString(_ctx.__("Existing Shift Found")), 1),
                    createBaseVNode("p", _hoisted_36, toDisplayString(_ctx.__("You have an open shift. Would you like to resume it or close it and open a new one?")), 1),
                    existingShift.value ? (openBlock(), createElementBlock("div", _hoisted_37, [
                      createBaseVNode("div", _hoisted_38, [
                        createVNode(_sfc_main$2, {
                          tag: "p",
                          inner: _ctx.__("<strong>POS Profile:</strong> {0}", [(_c = existingShift.value.pos_profile) == null ? void 0 : _c.name])
                        }, null, 8, ["inner"]),
                        _cache[7] || (_cache[7] = createBaseVNode("div", { class: "h-2" }, null, -1)),
                        createVNode(_sfc_main$2, {
                          tag: "p",
                          inner: _ctx.__("<strong>Opened:</strong> {0}", [unref(formatDateTime2)((_d = existingShift.value.pos_opening_shift) == null ? void 0 : _d.period_start_date)])
                        }, null, 8, ["inner"])
                      ])
                    ])) : createCommentVNode("", true),
                    createBaseVNode("div", _hoisted_39, [
                      createVNode(unref(_sfc_main$3), {
                        variant: "solid",
                        theme: "blue",
                        onClick: resumeShift
                      }, {
                        default: withCtx(() => [
                          createTextVNode(toDisplayString(_ctx.__("Resume Shift")), 1)
                        ]),
                        _: 1
                      }),
                      createVNode(unref(_sfc_main$3), {
                        variant: "subtle",
                        theme: "gray",
                        onClick: closeAndOpenNew,
                        disabled: closingExistingShift.value
                      }, {
                        default: withCtx(() => [
                          createTextVNode(toDisplayString(_ctx.__("Close & Open New")), 1)
                        ]),
                        _: 1
                      }, 8, ["disabled"])
                    ])
                  ])
                ])) : createCommentVNode("", true)
              ])
            ];
          }),
          actions: withCtx(() => [
            createBaseVNode("div", _hoisted_40, [
              step.value > 1 && step.value !== 3 ? (openBlock(), createBlock(unref(_sfc_main$3), {
                key: 0,
                variant: "subtle",
                onClick: _cache[1] || (_cache[1] = ($event) => step.value--)
              }, {
                default: withCtx(() => [
                  createTextVNode(toDisplayString(_ctx.__("Back")), 1)
                ]),
                _: 1
              })) : (openBlock(), createElementBlock("div", _hoisted_41)),
              createBaseVNode("div", _hoisted_42, [
                createVNode(unref(_sfc_main$3), {
                  variant: "subtle",
                  onClick: _cache[2] || (_cache[2] = ($event) => closeDialog("cancelled")),
                  disabled: unref(createShiftResource).loading
                }, {
                  default: withCtx(() => [
                    createTextVNode(toDisplayString(_ctx.__("Cancel")), 1)
                  ]),
                  _: 1
                }, 8, ["disabled"]),
                step.value === 1 ? (openBlock(), createBlock(unref(_sfc_main$3), {
                  key: 0,
                  variant: "solid",
                  theme: "blue",
                  onClick: nextStep,
                  disabled: !selectedProfile.value
                }, {
                  default: withCtx(() => [
                    createTextVNode(toDisplayString(_ctx.__("Next")), 1)
                  ]),
                  _: 1
                }, 8, ["disabled"])) : createCommentVNode("", true),
                step.value === 2 ? (openBlock(), createBlock(unref(_sfc_main$3), {
                  key: 1,
                  variant: "solid",
                  theme: "blue",
                  onClick: openShift,
                  loading: unref(createShiftResource).loading
                }, {
                  default: withCtx(() => [
                    createTextVNode(toDisplayString(_ctx.__("Open Shift")), 1)
                  ]),
                  _: 1
                }, 8, ["loading"])) : createCommentVNode("", true)
              ])
            ])
          ]),
          _: 1
        }, 8, ["modelValue", "options"]),
        existingShift.value ? (openBlock(), createBlock(_sfc_main$1, {
          key: 0,
          modelValue: showClosingDialog.value,
          "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => showClosingDialog.value = $event),
          "opening-shift": (_b = (_a = existingShift.value) == null ? void 0 : _a.pos_opening_shift) == null ? void 0 : _b.name,
          onShiftClosed: handleExistingShiftClosed
        }, null, 8, ["modelValue", "opening-shift"])) : createCommentVNode("", true)
      ], 64);
    };
  }
};
const log$2 = logger.create("SerialNumber");
const useSerialNumberStore = defineStore("serialNumber", () => {
  const cache = ref(/* @__PURE__ */ new Map());
  const loading = ref(false);
  const currentWarehouse = ref(null);
  const CACHE_TTL = 5 * 60 * 1e3;
  const getSerials = (itemCode) => {
    const cached = cache.value.get(itemCode);
    if (!cached) return [];
    return cached.serials;
  };
  const isCacheValid = (itemCode) => {
    const cached = cache.value.get(itemCode);
    if (!cached) return false;
    if (cached.warehouse !== currentWarehouse.value) return false;
    if (Date.now() - cached.timestamp > CACHE_TTL) return false;
    return true;
  };
  const setWarehouse = (warehouse) => {
    if (currentWarehouse.value !== warehouse) {
      currentWarehouse.value = warehouse;
      cache.value.clear();
      log$2.info(`Warehouse changed to ${warehouse}, cache cleared`);
    }
  };
  const fetchSerials = (itemCode, forceRefresh = false) => __async(void 0, null, function* () {
    if (!itemCode || !currentWarehouse.value) {
      log$2.warn("Missing itemCode or warehouse");
      return [];
    }
    if (!forceRefresh && isCacheValid(itemCode)) {
      log$2.info(`Using cached serials for ${itemCode}`);
      return getSerials(itemCode);
    }
    loading.value = true;
    try {
      const response = yield call("frappe.client.get_list", {
        doctype: "Serial No",
        filters: {
          item_code: itemCode,
          warehouse: currentWarehouse.value,
          status: "Active"
        },
        fields: ["name as serial_no", "warehouse"],
        limit_page_length: 500
      });
      const serials = response || [];
      cache.value.set(itemCode, {
        serials,
        warehouse: currentWarehouse.value,
        timestamp: Date.now()
      });
      log$2.success(`Loaded ${serials.length} serials for ${itemCode}`);
      return serials;
    } catch (error) {
      log$2.error(`Failed to fetch serials for ${itemCode}`, error);
      return [];
    } finally {
      loading.value = false;
    }
  });
  const consumeSerials = (itemCode, serialNumbers) => {
    const cached = cache.value.get(itemCode);
    if (!cached) return;
    const serialsToRemove = new Set(
      Array.isArray(serialNumbers) ? serialNumbers : serialNumbers.split("\n").map((s) => s.trim()).filter(Boolean)
    );
    cached.serials = cached.serials.filter(
      (s) => !serialsToRemove.has(s.serial_no)
    );
    log$2.info(`Consumed ${serialsToRemove.size} serials for ${itemCode}`);
  };
  const returnSerials = (itemCode, serialNumbers) => {
    const cached = cache.value.get(itemCode);
    if (!cached) return;
    const serialsToReturn = Array.isArray(serialNumbers) ? serialNumbers : serialNumbers.split("\n").map((s) => s.trim()).filter(Boolean);
    const existingSerialNos = new Set(cached.serials.map((s) => s.serial_no));
    for (const serialNo of serialsToReturn) {
      if (!existingSerialNos.has(serialNo)) {
        cached.serials.push({
          serial_no: serialNo,
          warehouse: currentWarehouse.value
        });
      }
    }
    cached.serials.sort((a, b) => a.serial_no.localeCompare(b.serial_no, void 0, { numeric: true }));
    log$2.info(`Returned ${serialsToReturn.length} serials for ${itemCode}`);
  };
  const clearCache = (itemCode = null) => {
    if (itemCode) {
      cache.value.delete(itemCode);
      log$2.info(`Cache cleared for ${itemCode}`);
    } else {
      cache.value.clear();
      log$2.info("All cache cleared");
    }
  };
  const prefetchSerials = (itemCodes) => __async(void 0, null, function* () {
    const codesToFetch = itemCodes.filter((code) => !isCacheValid(code));
    if (codesToFetch.length === 0) return;
    log$2.info(`Prefetching serials for ${codesToFetch.length} items`);
    const batchSize = 3;
    for (let i = 0; i < codesToFetch.length; i += batchSize) {
      const batch = codesToFetch.slice(i, i + batchSize);
      yield Promise.all(batch.map((code) => fetchSerials(code)));
    }
  });
  return {
    // State
    cache,
    loading,
    currentWarehouse,
    // Getters
    getSerials,
    isCacheValid,
    // Actions
    setWarehouse,
    fetchSerials,
    consumeSerials,
    returnSerials,
    clearCache,
    prefetchSerials
  };
});
class CoalescingMutex {
  /**
   * @param {Object} options - Configuration options
   * @param {number} options.timeout - Timeout in milliseconds (default: 60000)
   * @param {string} options.name - Optional name for debugging
   */
  constructor(options = {}) {
    var _a;
    this._activePromise = null;
    this._timeout = (_a = options.timeout) != null ? _a : 6e4;
    this._name = options.name || "Mutex";
  }
  /**
   * Check if the mutex is currently locked
   * @returns {boolean}
   */
  get isLocked() {
    return this._activePromise !== null;
  }
  /**
   * Execute function with exclusive access.
   * If locked, waits for completion then re-executes to catch any new work.
   *
   * @param {Function} fn - Async function to execute
   * @param {Function} logFn - Optional logging function for debug output
   * @returns {Promise} Result of the function execution
   */
  withLock(fn, logFn = null) {
    return __async(this, null, function* () {
      if (this._activePromise) {
        logFn == null ? void 0 : logFn(`${this._name}: Waiting for ongoing operation to complete...`);
        try {
          yield this._activePromise;
        } catch (e) {
        }
        return this.withLock(fn, logFn);
      }
      this._activePromise = this._executeWithTimeout(fn);
      try {
        return yield this._activePromise;
      } finally {
        this._activePromise = null;
      }
    });
  }
  /**
   * Execute function with timeout protection
   * @private
   */
  _executeWithTimeout(fn) {
    return __async(this, null, function* () {
      return new Promise((resolve, reject) => {
        const timeoutId = setTimeout(() => {
          reject(new Error(`${this._name}: Operation timed out after ${this._timeout}ms`));
        }, this._timeout);
        fn().then((result) => {
          clearTimeout(timeoutId);
          resolve(result);
        }).catch((error) => {
          clearTimeout(timeoutId);
          reject(error);
        });
      });
    });
  }
}
class QueuedMutex {
  /**
   * @param {Object} options - Configuration options
   * @param {number} options.timeout - Timeout in milliseconds (default: 60000)
   * @param {string} options.name - Optional name for debugging
   */
  constructor(options = {}) {
    var _a;
    this._queue = Promise.resolve();
    this._timeout = (_a = options.timeout) != null ? _a : 6e4;
    this._name = options.name || "QueuedMutex";
    this._pendingCount = 0;
  }
  /**
   * Check if the mutex has pending operations
   * @returns {boolean}
   */
  get isLocked() {
    return this._pendingCount > 0;
  }
  /**
   * Number of operations waiting in queue
   * @returns {number}
   */
  get pendingCount() {
    return this._pendingCount;
  }
  /**
   * Execute function in queue order.
   * Each caller waits for previous callers to complete.
   *
   * @param {Function} fn - Async function to execute
   * @param {Function} logFn - Optional logging function
   * @returns {Promise} Result of the function execution
   */
  withLock(fn, logFn = null) {
    return __async(this, null, function* () {
      this._pendingCount++;
      if (this._pendingCount > 1) {
        logFn == null ? void 0 : logFn(`${this._name}: Queued (${this._pendingCount - 1} ahead)`);
      }
      const result = this._queue.then(() => __async(this, null, function* () {
        try {
          return yield this._executeWithTimeout(fn);
        } finally {
          this._pendingCount--;
        }
      }));
      this._queue = result.catch(() => {
      });
      return result;
    });
  }
  /**
   * Execute function with timeout protection
   * @private
   */
  _executeWithTimeout(fn) {
    return __async(this, null, function* () {
      return new Promise((resolve, reject) => {
        const timeoutId = setTimeout(() => {
          reject(new Error(`${this._name}: Operation timed out after ${this._timeout}ms`));
        }, this._timeout);
        fn().then((result) => {
          clearTimeout(timeoutId);
          resolve(result);
        }).catch((error) => {
          clearTimeout(timeoutId);
          reject(error);
        });
      });
    });
  }
}
const log$1 = logger.create("Sync");
const syncMutex = new CoalescingMutex({ timeout: 6e4, name: "InvoiceSync" });
const SYNC_CONFIG = {
  MAX_RETRY_COUNT: 3,
  CLEANUP_AGE_DAYS: 7
};
const DUPLICATE_ERROR_PATTERNS = [
  "DUPLICATE_OFFLINE_INVOICE",
  "already been synced"
];
const SYNC_IN_PROGRESS_PATTERNS = [
  "SYNC_IN_PROGRESS",
  "currently being processed"
];
const isOffline = () => {
  if (typeof window === "undefined") return false;
  return offlineState.isOffline;
};
const getOfflineInvoices = () => __async(void 0, null, function* () {
  try {
    return yield db.invoice_queue.filter((inv) => !inv.synced).toArray();
  } catch (error) {
    log$1.error("Failed to get offline invoices", error);
    return [];
  }
});
const checkOfflineIdSynced = (offlineId) => __async(void 0, null, function* () {
  if (!offlineId) return { synced: false };
  try {
    const response = yield call(
      "ecs_posnext.api.invoices.check_offline_invoice_synced",
      { offline_id: offlineId }
    );
    return response || { synced: false };
  } catch (error) {
    log$1.warn("Failed to check sync status", { offline_id: offlineId, error });
    return { synced: false };
  }
});
const checkDuplicateError = (error) => {
  const errorMessage = (error == null ? void 0 : error.message) || (error == null ? void 0 : error.exc) || (error == null ? void 0 : error.title) || String(error);
  const isDuplicate = DUPLICATE_ERROR_PATTERNS.some(
    (pattern) => errorMessage.includes(pattern)
  );
  if (!isDuplicate) return { isDuplicate: false, invoiceName: null };
  const match = errorMessage.match(/Sales Invoice: (\S+)/);
  return { isDuplicate: true, invoiceName: (match == null ? void 0 : match[1]) || null };
};
const isSyncInProgressError = (error) => {
  const errorMessage = (error == null ? void 0 : error.message) || (error == null ? void 0 : error.exc) || (error == null ? void 0 : error.title) || String(error);
  return SYNC_IN_PROGRESS_PATTERNS.some(
    (pattern) => errorMessage.includes(pattern)
  );
};
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const markInvoiceSynced = (id, serverInvoice) => __async(void 0, null, function* () {
  yield db.invoice_queue.update(id, {
    synced: true,
    server_invoice: serverInvoice
  });
});
const handleSyncFailure = (invoice, errorMessage) => __async(void 0, null, function* () {
  const newRetryCount = (invoice.retry_count || 0) + 1;
  const updates = { retry_count: newRetryCount };
  if (newRetryCount >= SYNC_CONFIG.MAX_RETRY_COUNT) {
    updates.sync_failed = true;
    updates.error = errorMessage;
  }
  yield db.invoice_queue.update(invoice.id, updates);
});
const stringifyPricingRules = (value) => {
  if (!value) return "";
  if (Array.isArray(value)) return value.filter(Boolean).join(",");
  if (typeof value !== "string") return "";
  const stripped = value.trim();
  if (!stripped.startsWith("[")) return stripped;
  try {
    const parsed = JSON.parse(stripped);
    if (Array.isArray(parsed)) return parsed.filter(Boolean).join(",");
  } catch (e) {
    log$1.warn("Invalid pricing_rules JSON, clearing value", { value: stripped.slice(0, 100) });
    return "";
  }
  return "";
};
const normalizeInvoiceForSync = (invoiceData, offlineId) => {
  var _a;
  return __spreadProps(__spreadValues({}, invoiceData), {
    offline_id: offlineId || invoiceData.offline_id,
    items: (_a = invoiceData.items) == null ? void 0 : _a.map((item) => __spreadProps(__spreadValues({}, item), {
      qty: item.qty || item.quantity || 1,
      pricing_rules: stringifyPricingRules(item.pricing_rules)
    }))
  });
};
const syncInvoiceToServer = (invoice, retryCount = 0) => __async(void 0, null, function* () {
  var _a;
  const MAX_IN_PROGRESS_RETRIES = 3;
  const IN_PROGRESS_WAIT_MS = 2e3;
  const offlineId = invoice.offline_id || ((_a = invoice.data) == null ? void 0 : _a.offline_id);
  if (offlineId) {
    const syncStatus = yield checkOfflineIdSynced(offlineId);
    if (syncStatus.synced) {
      yield markInvoiceSynced(invoice.id, syncStatus.sales_invoice);
      log$1.debug("Invoice already synced, skipping", {
        id: invoice.id,
        offline_id: offlineId,
        sales_invoice: syncStatus.sales_invoice
      });
      return { status: "skipped" };
    }
  }
  const invoiceData = normalizeInvoiceForSync(invoice.data, offlineId);
  try {
    const response = yield call("ecs_posnext.api.invoices.submit_invoice", {
      data: JSON.stringify({ invoice: invoiceData, data: {} })
    });
    if (response.message || response.name) {
      const serverName = response.name || response.message;
      yield markInvoiceSynced(invoice.id, serverName);
      log$1.success("Invoice synced", {
        id: invoice.id,
        offline_id: offlineId,
        sales_invoice: serverName
      });
      return { status: "success" };
    }
    throw new Error("Invalid server response");
  } catch (error) {
    if (isSyncInProgressError(error) && retryCount < MAX_IN_PROGRESS_RETRIES) {
      log$1.debug("Invoice being processed by another request, waiting...", {
        id: invoice.id,
        retry: retryCount + 1
      });
      yield sleep(IN_PROGRESS_WAIT_MS);
      return syncInvoiceToServer(invoice, retryCount + 1);
    }
    throw error;
  }
});
const syncOfflineInvoices = () => __async(void 0, null, function* () {
  if (isOffline()) {
    log$1.debug("Cannot sync while offline");
    return { success: 0, failed: 0, skipped: 0, errors: [] };
  }
  return yield syncMutex.withLock(() => __async(void 0, null, function* () {
    var _a;
    const pendingInvoices = yield getOfflineInvoices();
    if (!pendingInvoices.length) {
      return { success: 0, failed: 0, skipped: 0, errors: [] };
    }
    log$1.info(`Starting sync of ${pendingInvoices.length} invoice(s)`);
    const result = { success: 0, failed: 0, skipped: 0, errors: [] };
    for (const invoice of pendingInvoices) {
      try {
        const syncResult = yield syncInvoiceToServer(invoice);
        if (syncResult.status === "success") {
          result.success++;
        } else if (syncResult.status === "skipped") {
          result.skipped++;
        }
      } catch (error) {
        log$1.error("Failed to sync invoice", { id: invoice.id, error });
        const { isDuplicate, invoiceName } = checkDuplicateError(error);
        if (isDuplicate) {
          yield markInvoiceSynced(invoice.id, invoiceName);
          log$1.debug("Invoice is duplicate, marked as synced", { id: invoice.id });
          result.skipped++;
          continue;
        }
        result.errors.push({
          invoiceId: invoice.id,
          offlineId: invoice.offline_id,
          customer: ((_a = invoice.data) == null ? void 0 : _a.customer) || "Walk-in Customer",
          error
        });
        yield handleSyncFailure(invoice, error.message);
        result.failed++;
      }
    }
    yield cleanupSyncedInvoices();
    log$1.info("Sync completed", {
      success: result.success,
      skipped: result.skipped,
      failed: result.failed
    });
    return result;
  }), log$1.debug.bind(log$1));
});
const cleanupSyncedInvoices = () => __async(void 0, null, function* () {
  const cutoff = Date.now() - SYNC_CONFIG.CLEANUP_AGE_DAYS * 24 * 60 * 60 * 1e3;
  yield db.invoice_queue.filter((inv) => inv.synced && inv.timestamp < cutoff).delete();
});
const cacheInvoiceHistory = (invoices, posProfile) => __async(void 0, null, function* () {
  if (!invoices || invoices.length === 0) return false;
  try {
    const invoicesToCache = invoices.map((invoice) => __spreadProps(__spreadValues({}, JSON.parse(JSON.stringify(invoice))), {
      pos_profile: posProfile,
      cached_at: Date.now()
    }));
    yield db.invoice_history.bulkPut(invoicesToCache);
    log$1.info(`Cached ${invoices.length} invoices for offline viewing`);
    return true;
  } catch (error) {
    log$1.error("Failed to cache invoice history", error);
    return false;
  }
});
const getCachedInvoiceHistory = (_0, ..._1) => __async(void 0, [_0, ..._1], function* (posProfile, options = {}) {
  try {
    const { limit = 100, customer, fromDate, toDate } = options;
    let query = db.invoice_history;
    if (posProfile) {
      query = query.where("pos_profile").equals(posProfile);
    }
    let invoices = yield query.toArray();
    if (customer) {
      invoices = invoices.filter(
        (inv) => {
          var _a;
          return (_a = inv.customer) == null ? void 0 : _a.toLowerCase().includes(customer.toLowerCase());
        }
      );
    }
    if (fromDate) {
      invoices = invoices.filter((inv) => inv.posting_date >= fromDate);
    }
    if (toDate) {
      invoices = invoices.filter((inv) => inv.posting_date <= toDate);
    }
    invoices.sort((a, b) => {
      const dateA = /* @__PURE__ */ new Date(b.posting_date + " " + (b.posting_time || "00:00:00"));
      const dateB = /* @__PURE__ */ new Date(a.posting_date + " " + (a.posting_time || "00:00:00"));
      return dateA - dateB;
    });
    return invoices.slice(0, limit);
  } catch (error) {
    log$1.error("Failed to get cached invoice history", error);
    return [];
  }
});
const cacheUnpaidInvoices = (invoices, posProfile) => __async(void 0, null, function* () {
  if (!invoices || invoices.length === 0) {
    try {
      yield db.unpaid_invoices.where("pos_profile").equals(posProfile).delete();
    } catch (e) {
    }
    return true;
  }
  try {
    const invoicesToCache = invoices.map((invoice) => __spreadProps(__spreadValues({}, JSON.parse(JSON.stringify(invoice))), {
      pos_profile: posProfile,
      cached_at: Date.now()
    }));
    yield db.unpaid_invoices.where("pos_profile").equals(posProfile).delete();
    yield db.unpaid_invoices.bulkPut(invoicesToCache);
    log$1.info(`Cached ${invoices.length} unpaid invoices for offline viewing`);
    return true;
  } catch (error) {
    log$1.error("Failed to cache unpaid invoices", error);
    return false;
  }
});
const getCachedUnpaidInvoices = (_0, ..._1) => __async(void 0, [_0, ..._1], function* (posProfile, options = {}) {
  try {
    const { limit = 100 } = options;
    if (!posProfile) {
      return [];
    }
    let invoices = yield db.unpaid_invoices.where("pos_profile").equals(posProfile).toArray();
    invoices.sort((a, b) => {
      const amountA = parseFloat(b.outstanding_amount || 0);
      const amountB = parseFloat(a.outstanding_amount || 0);
      return amountA - amountB;
    });
    return invoices.slice(0, limit);
  } catch (error) {
    log$1.error("Failed to get cached unpaid invoices", error);
    return [];
  }
});
const cacheUnpaidSummary = (summary, posProfile) => __async(void 0, null, function* () {
  try {
    yield db.settings.put({
      key: `unpaid_summary_${posProfile}`,
      value: __spreadProps(__spreadValues({}, summary), {
        cached_at: Date.now()
      })
    });
    log$1.debug("Cached unpaid invoice summary");
    return true;
  } catch (error) {
    log$1.error("Failed to cache unpaid summary", error);
    return false;
  }
});
const getCachedUnpaidSummary = (posProfile) => __async(void 0, null, function* () {
  try {
    const result = yield db.settings.get(`unpaid_summary_${posProfile}`);
    return (result == null ? void 0 : result.value) || { count: 0, total_outstanding: 0, total_paid: 0 };
  } catch (error) {
    log$1.error("Failed to get cached unpaid summary", error);
    return { count: 0, total_outstanding: 0, total_paid: 0 };
  }
});
const CACHE_STRUCTURE = {
  // Define what gets cached
  items: ["item_code", "item_name", "item_group", "barcodes", "price", "stock", "custom_allow_rate_edit"],
  customers: ["name", "customer_name", "mobile_no", "email_id"],
  item_prices: ["price_list", "item_code", "price"],
  local_stock: ["item_code", "warehouse", "actual_qty"],
  payment_methods: [
    "mode_of_payment",
    "pos_profile",
    "default",
    "allow_in_returns",
    "type"
  ]
};
function getCacheStructureHash(structure) {
  const structureString = JSON.stringify(structure);
  let hash = 0;
  for (let i = 0; i < structureString.length; i++) {
    const char = structureString.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash;
  }
  return Math.abs(hash);
}
function getCacheVersion() {
  const structureHash = getCacheStructureHash(CACHE_STRUCTURE);
  const storedHash = localStorage.getItem("ecs_posnext_cache_structure_hash");
  const storedVersion = Number.parseInt(
    localStorage.getItem("ecs_posnext_cache_version") || "1"
  );
  if (storedHash !== structureHash.toString()) {
    const newVersion = storedVersion + 1;
    console.log(
      `Cache structure changed. Upgrading from v${storedVersion} to v${newVersion}`
    );
    localStorage.setItem(
      "ecs_posnext_cache_structure_hash",
      structureHash.toString()
    );
    localStorage.setItem("ecs_posnext_cache_version", newVersion.toString());
    return newVersion;
  }
  return storedVersion;
}
const CACHE_VERSION = getCacheVersion();
const memory = {
  // Offline queues
  offline_invoices: [],
  offline_customers: [],
  offline_payments: [],
  // Cached data
  items: [],
  customers: [],
  item_prices: {},
  local_stock: {},
  payment_methods: [],
  // Metadata
  items_last_sync: null,
  customers_last_sync: null,
  payment_methods_last_sync: null,
  cache_ready: false,
  stock_cache_ready: false,
  manual_offline: false,
  // Cache version
  cache_version: CACHE_VERSION
};
const initMemoryCache = () => __async(void 0, null, function* () {
  try {
    console.log("Initializing memory cache...");
    const storedVersion = yield getSetting("cache_version", CACHE_VERSION);
    if (storedVersion !== CACHE_VERSION) {
      console.log("Cache version mismatch, clearing cache...");
      yield clearAllCache();
      yield setSetting("cache_version", CACHE_VERSION);
      memory.cache_version = CACHE_VERSION;
    }
    memory.items_last_sync = yield getSetting("items_last_sync", null);
    memory.customers_last_sync = yield getSetting("customers_last_sync", null);
    memory.cache_ready = yield getSetting("cache_ready", false);
    memory.stock_cache_ready = yield getSetting("stock_cache_ready", false);
    memory.manual_offline = yield getSetting("manual_offline", false);
    if (memory.manual_offline) {
      offlineState.setManualOffline(true, { silent: true });
    }
    const itemsCount = yield db.items.count();
    const customersCount = yield db.customers.count();
    console.log(
      `Cache initialized: ${itemsCount} items, ${customersCount} customers`
    );
    console.log(
      `Cache ready: ${memory.cache_ready}, Stock ready: ${memory.stock_cache_ready}`
    );
    return true;
  } catch (error) {
    console.error("Failed to initialize memory cache:", error);
    return false;
  }
});
const cacheCustomersFromServer = (posProfile) => __async(void 0, null, function* () {
  try {
    console.log("Fetching customers from server...");
    const response = yield call("ecs_posnext.api.customers.get_customers", {
      pos_profile: posProfile,
      start: 0,
      limit: 0
      // Get all customers
    });
    if (response.message && Array.isArray(response.message)) {
      const customers = response.message;
      console.log(`Fetched ${customers.length} customers from server`);
      return { customers };
    }
    return { customers: [] };
  } catch (error) {
    console.error("Error fetching customers from server:", error);
    throw error;
  }
});
const getCachedItem = (itemCode) => __async(void 0, null, function* () {
  try {
    return yield db.items.get(itemCode);
  } catch (error) {
    console.error("Error getting cached item:", error);
    return null;
  }
});
const clearAllCache = () => __async(void 0, null, function* () {
  try {
    console.log("Clearing all cache...");
    yield db.items.clear();
    yield db.customers.clear();
    yield db.item_prices.clear();
    yield db.stock.clear();
    memory.items = [];
    memory.customers = [];
    memory.item_prices = {};
    memory.local_stock = {};
    memory.items_last_sync = null;
    memory.customers_last_sync = null;
    memory.cache_ready = false;
    memory.stock_cache_ready = false;
    yield setSetting("items_last_sync", null);
    yield setSetting("customers_last_sync", null);
    yield setSetting("cache_ready", false);
    yield setSetting("stock_cache_ready", false);
    console.log("Cache cleared successfully");
    return true;
  } catch (error) {
    console.error("Error clearing cache:", error);
    return false;
  }
});
function cachePaymentMethodsFromServer(posProfile) {
  return __async(this, null, function* () {
    try {
      const result = yield call("ecs_posnext.api.pos_profile.get_payment_methods", {
        pos_profile: posProfile
      });
      const paymentMethods = (result == null ? void 0 : result.message) || result || [];
      const methodsWithProfile = paymentMethods.map((method) => __spreadProps(__spreadValues({}, method), {
        pos_profile: posProfile
      }));
      yield db.payment_methods.bulkPut(methodsWithProfile);
      const timestamp = Date.now();
      yield setSetting("payment_methods_last_sync", timestamp);
      memory.payment_methods_last_sync = timestamp;
      console.log(
        `Cached ${paymentMethods.length} payment methods for ${posProfile}`
      );
      return { payment_methods: paymentMethods };
    } catch (error) {
      console.error("Error caching payment methods:", error);
      throw error;
    }
  });
}
initMemoryCache();
const log = logger.create("Invoice");
const submitMutex = new CoalescingMutex({
  timeout: 6e4,
  name: "InvoiceSubmit"
});
function useInvoice() {
  const serialStore = useSerialNumberStore();
  const settingsStore = usePOSSettingsStore();
  const allowAdditionalDiscount = computed(
    () => settingsStore.allowAdditionalDiscount
  );
  const invoiceItems = ref([]);
  const customer = ref(null);
  const payments = ref([]);
  const salesTeam = ref([]);
  const posProfile = ref(null);
  const posOpeningShift = ref(null);
  const additionalDiscount = ref(0);
  const couponCode = ref(null);
  const taxRules = ref([]);
  const taxInclusive = ref(false);
  const loyaltyPointsToRedeem = ref(0);
  const loyaltyCashbackToUse = ref(0);
  const activePriceList = ref(null);
  const cardApprovalCodes = ref([]);
  const isTabbyPayment = ref(false);
  const bundleSelections = ref({});
  function setBundleSelection(bundleItemCode, componentCodes) {
    if (!bundleItemCode) return;
    bundleSelections.value = __spreadProps(__spreadValues({}, bundleSelections.value), {
      [bundleItemCode]: componentCodes || []
    });
  }
  const isSubmitting = ref(false);
  const _cachedSubtotal = ref(0);
  const _cachedTotalTax = ref(0);
  const _cachedTotalDiscount = ref(0);
  const _cachedTotalPaid = ref(0);
  const updateInvoiceResource = createResource({
    url: "ecs_posnext.api.invoices.update_invoice",
    makeParams(params) {
      return { data: JSON.stringify(params.data) };
    },
    auto: false
  });
  const submitInvoiceResource = createResource({
    url: "ecs_posnext.api.invoices.submit_invoice",
    makeParams(params) {
      return {
        invoice: JSON.stringify(params.invoice),
        data: JSON.stringify(params.data || {})
      };
    },
    auto: false,
    onError(error) {
      console.error("submitInvoiceResource onError:", error);
      if (submitInvoiceResource.error) {
        error.resourceError = submitInvoiceResource.error;
      }
    }
  });
  const closeReservationResource = createResource({
    url: "ecs_posnext.api.reservations.close_party_reservation",
    makeParams(params) {
      return {
        sales_order: params.sales_order,
        invoice_data: JSON.stringify(params.invoice_data),
        data: JSON.stringify(params.data || {}),
        pos_profile: params.pos_profile
      };
    },
    auto: false
  });
  const validateCartItemsResource = createResource({
    url: "ecs_posnext.api.invoices.validate_cart_items",
    makeParams({ items, pos_profile }) {
      return {
        items: JSON.stringify(items),
        pos_profile
      };
    },
    auto: false
  });
  const applyOffersResource = createResource({
    url: "ecs_posnext.api.invoices.apply_offers",
    makeParams({ invoice_data, selected_offers }) {
      const params = {
        invoice_data: JSON.stringify(invoice_data)
      };
      if (selected_offers && selected_offers.length) {
        params.selected_offers = JSON.stringify(selected_offers);
      }
      return params;
    },
    auto: false
  });
  const getItemDetailsResource = createResource({
    url: "ecs_posnext.api.items.get_item_details",
    auto: false
  });
  function resolveUomPricing(item, uom, conversionFactor, qty) {
    return __async(this, null, function* () {
      var _a, _b;
      if (!isOffline$1()) {
        try {
          const itemDetails = yield getItemDetailsResource.submit({
            item_code: item.item_code,
            pos_profile: posProfile.value,
            customer: ((_a = customer.value) == null ? void 0 : _a.name) || customer.value,
            qty,
            uom
          });
          return {
            rate: itemDetails.price_list_rate || itemDetails.rate,
            price_list_rate: itemDetails.price_list_rate
          };
        } catch (err) {
          log.warn(
            "Server UOM pricing unavailable, resolving from IndexedDB",
            err
          );
        }
      }
      const cachedItem = yield getCachedItem(item.item_code);
      const source = cachedItem || item;
      let rate;
      if ((_b = source.uom_prices) == null ? void 0 : _b[uom]) {
        rate = source.uom_prices[uom];
      } else {
        const baseRate = source.price_list_rate || source.rate || 0;
        const currentConversion = source.conversion_factor || 1;
        rate = baseRate / currentConversion * conversionFactor;
      }
      return { rate, price_list_rate: rate };
    });
  }
  const getTaxesResource = createResource({
    url: "ecs_posnext.api.pos_profile.get_taxes",
    auto: false
  });
  const getDefaultCustomerResource = createResource({
    url: "ecs_posnext.api.pos_profile.get_default_customer",
    makeParams({ pos_profile }) {
      return { pos_profile };
    },
    auto: false
  });
  const resolveDefaultCustomerResource = createResource({
    url: "ecs_posnext.api.pos_profile.resolve_default_customer",
    makeParams({ pos_profile, price_list, item_code }) {
      return { pos_profile, price_list, item_code };
    },
    auto: false
  });
  const cleanupDraftsResource = createResource({
    url: "ecs_posnext.api.invoices.cleanup_old_drafts",
    auto: false
  });
  const notIncludedTotal = computed(() => {
    if (!allowAdditionalDiscount.value) {
      return 0;
    }
    let total = 0;
    for (const item of invoiceItems.value) {
      if (!item.custom_not_included) continue;
      const isManuallyEdited = item.is_rate_manually_edited === 1;
      const effectiveRate = isManuallyEdited ? item.rate : item.price_list_rate || item.rate;
      total += roundCurrency(item.quantity * roundCurrency(effectiveRate));
    }
    return roundCurrency(total);
  });
  const subtotal = computed(() => {
    if (allowAdditionalDiscount.value) {
      return roundCurrency(_cachedSubtotal.value - notIncludedTotal.value);
    }
    return roundCurrency(_cachedSubtotal.value);
  });
  const discountEligibleSubtotal = computed(() => {
    let total = 0;
    for (const item of invoiceItems.value) {
      if (item.custom_not_included) continue;
      const isManuallyEdited = item.is_rate_manually_edited === 1;
      const effectiveRate = isManuallyEdited ? item.rate : item.price_list_rate || item.rate;
      total += roundCurrency(item.quantity * roundCurrency(effectiveRate));
    }
    return roundCurrency(total);
  });
  const totalTax = computed(() => roundCurrency(_cachedTotalTax.value));
  const totalDiscount = computed(
    () => roundCurrency(_cachedTotalDiscount.value + (additionalDiscount.value || 0))
  );
  const grandTotal = computed(() => {
    const discount = _cachedTotalDiscount.value + (additionalDiscount.value || 0);
    if (allowAdditionalDiscount.value) {
      const eligibleBase = _cachedSubtotal.value - notIncludedTotal.value;
      if (taxInclusive.value) {
        return roundCurrency(eligibleBase - discount + notIncludedTotal.value);
      } else {
        return roundCurrency(
          eligibleBase + _cachedTotalTax.value - discount + notIncludedTotal.value
        );
      }
    }
    if (taxInclusive.value) {
      return roundCurrency(_cachedSubtotal.value - discount);
    } else {
      return roundCurrency(
        _cachedSubtotal.value + _cachedTotalTax.value - discount
      );
    }
  });
  const totalPaid = computed(() => _cachedTotalPaid.value);
  const remainingAmount = computed(() => {
    return grandTotal.value - totalPaid.value;
  });
  const canSubmit = computed(() => {
    return invoiceItems.value.length > 0 && remainingAmount.value <= 0.01;
  });
  function addItem(item, quantity = 1) {
    const itemUom = item.uom || item.stock_uom;
    const existingItem = invoiceItems.value.find(
      (i) => i.item_code === item.item_code && i.uom === itemUom
    );
    if (existingItem) {
      const oldPriceListRate = existingItem.price_list_rate || existingItem.rate;
      const oldAmount = roundCurrency(
        existingItem.quantity * roundCurrency(oldPriceListRate)
      );
      const oldTax = existingItem.tax_amount || 0;
      const oldDiscount = existingItem.discount_amount || 0;
      if (existingItem.has_serial_no && item.serial_no) {
        const existingSerials = existingItem.serial_no ? existingItem.serial_no.split("\n").filter((s) => s.trim()) : [];
        const newSerials = item.serial_no.split("\n").filter((s) => s.trim());
        const allSerials = [.../* @__PURE__ */ new Set([...existingSerials, ...newSerials])];
        existingItem.serial_no = allSerials.join("\n");
        existingItem.quantity = allSerials.length;
      } else {
        existingItem.quantity += quantity;
      }
      recalculateItem(existingItem);
      const priceListRate = existingItem.price_list_rate || existingItem.rate;
      _cachedSubtotal.value += roundCurrency(existingItem.quantity * roundCurrency(priceListRate)) - oldAmount;
      _cachedTotalTax.value += (existingItem.tax_amount || 0) - oldTax;
      _cachedTotalDiscount.value += (existingItem.discount_amount || 0) - oldDiscount;
    } else {
      const newItem = {
        item_code: item.item_code,
        item_name: item.item_name,
        rate: item.rate || item.price_list_rate || 0,
        price_list_rate: item.price_list_rate || item.rate || 0,
        quantity,
        discount_amount: 0,
        discount_percentage: 0,
        tax_amount: 0,
        amount: quantity * (item.rate || item.price_list_rate || 0),
        stock_qty: item.stock_qty || 0,
        image: item.image,
        uom: item.uom || item.stock_uom,
        stock_uom: item.stock_uom,
        conversion_factor: item.conversion_factor || 1,
        warehouse: item.warehouse,
        actual_batch_qty: item.actual_batch_qty || 0,
        has_batch_no: item.has_batch_no || 0,
        has_serial_no: item.has_serial_no || 0,
        batch_no: item.batch_no,
        serial_no: item.serial_no,
        item_uoms: item.item_uoms || [],
        // Available UOMs for this item
        // Add item_group and brand for offer eligibility checking
        item_group: item.item_group,
        brand: item.brand,
        // Resolved barcode flag - prevents editing qty/uom/rate for weighted/priced barcodes
        is_resolved_barcode: item.is_resolved_barcode || false,
        // Per-item rate edit control
        custom_allow_rate_edit: item.custom_allow_rate_edit || 0,
        // Exclude from additional discount
        custom_not_included: item.custom_not_included || 0
      };
      console.log(
        "[DEBUG addItem]",
        item.item_code,
        "source custom_not_included:",
        item.custom_not_included,
        "→ cart custom_not_included:",
        newItem.custom_not_included,
        "| allowAdditionalDiscount:",
        allowAdditionalDiscount.value
      );
      invoiceItems.value.push(newItem);
      recalculateItem(newItem);
      const priceListRate = newItem.price_list_rate || newItem.rate;
      _cachedSubtotal.value += roundCurrency(
        newItem.quantity * roundCurrency(priceListRate)
      );
      _cachedTotalTax.value += newItem.tax_amount || 0;
      _cachedTotalDiscount.value += newItem.discount_amount || 0;
    }
  }
  function removeItem(itemCode, uom = null) {
    let itemToRemove;
    if (uom) {
      itemToRemove = invoiceItems.value.find(
        (i) => i.item_code === itemCode && i.uom === uom
      );
    } else {
      itemToRemove = invoiceItems.value.find((i) => i.item_code === itemCode);
    }
    if (itemToRemove) {
      const isManuallyEdited = itemToRemove.is_rate_manually_edited === 1;
      const effectiveRate = isManuallyEdited ? itemToRemove.rate : itemToRemove.price_list_rate || itemToRemove.rate;
      _cachedSubtotal.value -= roundCurrency(
        itemToRemove.quantity * roundCurrency(effectiveRate)
      );
      _cachedTotalTax.value -= itemToRemove.tax_amount || 0;
      _cachedTotalDiscount.value -= itemToRemove.discount_amount || 0;
      if (itemToRemove.serial_no && itemToRemove.has_serial_no) {
        serialStore.returnSerials(itemCode, itemToRemove.serial_no);
      }
    }
    if (uom) {
      invoiceItems.value = invoiceItems.value.filter(
        (i) => !(i.item_code === itemCode && i.uom === uom)
      );
    } else {
      invoiceItems.value = invoiceItems.value.filter(
        (i) => i.item_code !== itemCode
      );
    }
  }
  function updateItemQuantity(itemCode, quantity, uom = null) {
    let item;
    if (uom) {
      item = invoiceItems.value.find(
        (i) => i.item_code === itemCode && i.uom === uom
      );
    } else {
      item = invoiceItems.value.find((i) => i.item_code === itemCode);
    }
    if (item) {
      const isManuallyEdited = item.is_rate_manually_edited === 1;
      const effectiveRate = isManuallyEdited ? item.rate : item.price_list_rate || item.rate;
      const oldAmount = roundCurrency(
        item.quantity * roundCurrency(effectiveRate)
      );
      const oldTax = item.tax_amount || 0;
      const oldDiscount = item.discount_amount || 0;
      const oldQuantity = item.quantity;
      const newQuantity = Number.parseFloat(quantity) || 1;
      if (item.has_serial_no && item.serial_no) {
        const serialList = item.serial_no.split("\n").filter((s) => s.trim());
        if (newQuantity < oldQuantity) {
          const serialsToReturn = serialList.slice(newQuantity);
          const serialsToKeep = serialList.slice(0, newQuantity);
          if (serialsToReturn.length > 0) {
            serialStore.returnSerials(itemCode, serialsToReturn);
            item.serial_no = serialsToKeep.join("\n");
          }
        }
      }
      item.quantity = newQuantity;
      recalculateItem(item);
      _cachedSubtotal.value += roundCurrency(item.quantity * roundCurrency(effectiveRate)) - oldAmount;
      _cachedTotalTax.value += (item.tax_amount || 0) - oldTax;
      _cachedTotalDiscount.value += (item.discount_amount || 0) - oldDiscount;
    }
  }
  function updateItemRate(itemCode, rate, isManualEdit = false) {
    const item = invoiceItems.value.find((i) => i.item_code === itemCode);
    if (item) {
      const wasManuallyEdited = item.is_rate_manually_edited === 1;
      const oldEffectiveRate = wasManuallyEdited ? item.rate : item.price_list_rate || item.rate;
      const oldAmount = roundCurrency(
        item.quantity * roundCurrency(oldEffectiveRate)
      );
      const oldTax = item.tax_amount || 0;
      const oldDiscount = item.discount_amount || 0;
      const newRate = Number.parseFloat(rate) || 0;
      item.rate = newRate;
      const originalPriceListRate = item.price_list_rate || oldEffectiveRate;
      if (isManualEdit && newRate !== originalPriceListRate) {
        item.is_rate_manually_edited = 1;
        item.original_rate = originalPriceListRate;
      }
      recalculateItem(item);
      const isNowManuallyEdited = item.is_rate_manually_edited === 1;
      const newEffectiveRate = isNowManuallyEdited ? item.rate : item.price_list_rate || item.rate;
      _cachedSubtotal.value += roundCurrency(item.quantity * roundCurrency(newEffectiveRate)) - oldAmount;
      _cachedTotalTax.value += (item.tax_amount || 0) - oldTax;
      _cachedTotalDiscount.value += (item.discount_amount || 0) - oldDiscount;
    }
  }
  function updateItemDiscount(itemCode, discountPercentage) {
    const item = invoiceItems.value.find((i) => i.item_code === itemCode);
    if (item) {
      let validDiscount = Number.parseFloat(discountPercentage) || 0;
      if (validDiscount < 0) validDiscount = 0;
      if (validDiscount > 100) validDiscount = 100;
      const isManuallyEdited = item.is_rate_manually_edited === 1;
      const effectiveRate = isManuallyEdited ? item.rate : item.price_list_rate || item.rate;
      const oldAmount = roundCurrency(
        item.quantity * roundCurrency(effectiveRate)
      );
      const oldTax = item.tax_amount || 0;
      const oldDiscount = item.discount_amount || 0;
      item.discount_percentage = validDiscount;
      item.discount_amount = 0;
      recalculateItem(item);
      _cachedSubtotal.value += roundCurrency(item.quantity * roundCurrency(effectiveRate)) - oldAmount;
      _cachedTotalTax.value += (item.tax_amount || 0) - oldTax;
      _cachedTotalDiscount.value += (item.discount_amount || 0) - oldDiscount;
    }
  }
  function calculateDiscountAmount(discount, baseAmount = null) {
    if (!discount) return 0;
    const base = baseAmount !== null ? baseAmount : subtotal.value;
    if (discount.percentage > 0) {
      return roundCurrency(base * discount.percentage / 100);
    } else if (discount.amount > 0) {
      return roundCurrency(discount.amount);
    }
    return 0;
  }
  function applyDiscount(discount) {
    if (!discount) return;
    couponCode.value = discount.code || discount.name;
    let discountAmount = calculateDiscountAmount(discount, subtotal.value);
    if (discountAmount > subtotal.value) {
      discountAmount = subtotal.value;
    }
    if (discountAmount < 0) {
      discountAmount = 0;
    }
    additionalDiscount.value = discountAmount;
    rebuildIncrementalCache();
  }
  function removeDiscount() {
    additionalDiscount.value = 0;
    couponCode.value = null;
    rebuildIncrementalCache();
  }
  let cachedTaxRate = 0;
  let taxRulesCacheKey = "";
  function calculateTotalTaxRate() {
    const currentKey = JSON.stringify(taxRules.value);
    if (currentKey === taxRulesCacheKey && cachedTaxRate !== 0) {
      return cachedTaxRate;
    }
    let totalRate = 0;
    if (taxRules.value && taxRules.value.length > 0) {
      for (const taxRule of taxRules.value) {
        if (taxRule.charge_type === "On Net Total" || taxRule.charge_type === "On Previous Row Total") {
          totalRate += taxRule.rate || 0;
        }
      }
    }
    cachedTaxRate = totalRate;
    taxRulesCacheKey = currentKey;
    return totalRate;
  }
  function rebuildIncrementalCache() {
    _cachedSubtotal.value = 0;
    _cachedTotalTax.value = 0;
    _cachedTotalDiscount.value = 0;
    for (const item of invoiceItems.value) {
      const isManuallyEdited = item.is_rate_manually_edited === 1;
      const effectiveRate = isManuallyEdited ? item.rate : item.price_list_rate || item.rate;
      _cachedSubtotal.value += roundCurrency(
        item.quantity * roundCurrency(effectiveRate)
      );
      _cachedTotalTax.value += item.tax_amount || 0;
      _cachedTotalDiscount.value += item.discount_amount || 0;
    }
    _cachedTotalPaid.value = 0;
    for (const payment of payments.value) {
      _cachedTotalPaid.value += payment.amount || 0;
    }
  }
  function recalculateItem(item) {
    const isManuallyEdited = item.is_rate_manually_edited === 1;
    const effectiveRate = isManuallyEdited ? item.rate : item.price_list_rate || item.rate;
    const roundedRate = roundCurrency(effectiveRate);
    const baseAmount = roundCurrency(item.quantity * roundedRate);
    let discountAmount = 0;
    if (item.discount_percentage > 0) {
      discountAmount = roundCurrency(
        baseAmount * item.discount_percentage / 100
      );
    } else if (item.discount_amount > 0) {
      discountAmount = roundCurrency(item.discount_amount);
      item.discount_percentage = baseAmount > 0 ? discountAmount / baseAmount * 100 : 0;
    }
    item.discount_amount = discountAmount;
    const totalTaxRate = calculateTotalTaxRate();
    let netAmount = 0;
    let taxAmount = 0;
    if (taxInclusive.value && totalTaxRate > 0) {
      const grossAmount = roundCurrency(baseAmount - discountAmount);
      netAmount = roundCurrency(grossAmount / (1 + totalTaxRate / 100));
      taxAmount = roundCurrency(grossAmount - netAmount);
    } else {
      netAmount = roundCurrency(baseAmount - discountAmount);
      taxAmount = roundCurrency(netAmount * totalTaxRate / 100);
    }
    item.tax_amount = taxAmount;
    if (!isManuallyEdited) {
      item.rate = effectiveRate;
    }
    item.amount = netAmount;
  }
  function computeBackendRate(item) {
    var _a, _b, _c, _d;
    const qty = item.quantity || item.qty || 1;
    const isManuallyEdited = item.is_rate_manually_edited === 1;
    const effectiveRate = isManuallyEdited ? item.rate : (_b = (_a = item.price_list_rate) != null ? _a : item.rate) != null ? _b : 0;
    const discountAmount = item.discount_amount || 0;
    if (taxInclusive.value) {
      return roundCurrency(effectiveRate - discountAmount / qty);
    }
    return qty > 0 ? roundCurrency(((_c = item.amount) != null ? _c : 0) / qty) : (_d = item.rate) != null ? _d : 0;
  }
  function stringifyPricingRules2(pricingRules) {
    if (!pricingRules) return "";
    if (Array.isArray(pricingRules)) return pricingRules.join(",");
    return String(pricingRules);
  }
  function formatItemsForSubmission(items) {
    return items.map((item) => ({
      item_code: item.item_code,
      item_name: item.item_name,
      qty: item.quantity || item.qty || 1,
      rate: computeBackendRate(item),
      price_list_rate: roundCurrency(item.price_list_rate || item.rate),
      uom: item.uom,
      warehouse: item.warehouse,
      batch_no: item.batch_no,
      serial_no: item.serial_no,
      conversion_factor: item.conversion_factor || 1,
      discount_percentage: roundCurrency(item.discount_percentage || 0),
      discount_amount: roundCurrency(item.discount_amount || 0),
      pricing_rules: stringifyPricingRules2(item.pricing_rules),
      // Manual rate edit tracking for audit logging
      is_rate_manually_edited: item.is_rate_manually_edited || 0,
      original_rate: item.original_rate || null
    }));
  }
  function addPayment(payment) {
    const amount = Number.parseFloat(payment.amount) || 0;
    payments.value.push({
      mode_of_payment: payment.mode_of_payment,
      amount,
      type: payment.type
    });
    _cachedTotalPaid.value += amount;
  }
  function removePayment(index) {
    if (payments.value[index]) {
      _cachedTotalPaid.value -= payments.value[index].amount || 0;
    }
    payments.value.splice(index, 1);
  }
  function updatePayment(index, amount) {
    if (payments.value[index]) {
      const oldAmount = payments.value[index].amount || 0;
      const newAmount = Number.parseFloat(amount) || 0;
      payments.value[index].amount = newAmount;
      _cachedTotalPaid.value += newAmount - oldAmount;
    }
  }
  function validateStock() {
    return __async(this, null, function* () {
      const rawItems = toRaw(invoiceItems.value);
      const items = rawItems.map((item) => ({
        item_code: item.item_code,
        qty: item.quantity,
        warehouse: item.warehouse,
        conversion_factor: item.conversion_factor || 1,
        stock_qty: item.quantity * (item.conversion_factor || 1),
        is_stock_item: item.is_stock_item !== false
        // default to true
      }));
      try {
        const result = yield validateCartItemsResource.submit({
          items,
          pos_profile: posProfile.value
        });
        return result || [];
      } catch (error) {
        console.error("Stock validation error:", error);
        return [];
      }
    });
  }
  function saveDraft(targetDoctype = "Sales Invoice") {
    return __async(this, null, function* () {
      var _a;
      const rawItems = toRaw(invoiceItems.value);
      const rawPayments = toRaw(payments.value);
      const invoiceData = {
        doctype: targetDoctype,
        pos_profile: posProfile.value,
        posa_pos_opening_shift: posOpeningShift.value,
        customer: ((_a = customer.value) == null ? void 0 : _a.name) || customer.value,
        items: formatItemsForSubmission(rawItems),
        payments: rawPayments.map((p) => ({
          mode_of_payment: p.mode_of_payment,
          amount: p.amount,
          type: p.type
        })),
        discount_amount: additionalDiscount.value || 0,
        coupon_code: couponCode.value,
        custom_loyalty_points_to_redeem: loyaltyPointsToRedeem.value || 0,
        custom_cashback_to_use: loyaltyCashbackToUse.value || 0,
        selling_price_list: activePriceList.value || void 0,
        posa_bundle_selections: Object.keys(bundleSelections.value).length ? JSON.stringify(bundleSelections.value) : void 0,
        is_pos: 1,
        update_stock: 1
      };
      if (targetDoctype === "Sales Order") {
        const today = (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
        invoiceData.delivery_date = today;
        invoiceData.transaction_date = today;
      }
      const result = yield updateInvoiceResource.submit({ data: invoiceData });
      return (result == null ? void 0 : result.data) || result;
    });
  }
  function submitInvoice(targetDoctype = "Sales Invoice", deliveryDate = null, writeOffAmount = 0, onDraftCreated = null) {
    return __async(this, null, function* () {
      return yield submitMutex.withLock(() => __async(this, null, function* () {
        var _a;
        if (isSubmitting.value) {
          log.warn(
            "Invoice submission already in progress, skipping duplicate request"
          );
          return null;
        }
        isSubmitting.value = true;
        try {
          const rawItems = toRaw(invoiceItems.value);
          const rawPayments = toRaw(payments.value);
          const rawSalesTeam = toRaw(salesTeam.value);
          const invoiceData = {
            doctype: targetDoctype,
            pos_profile: posProfile.value,
            posa_pos_opening_shift: posOpeningShift.value,
            customer: ((_a = customer.value) == null ? void 0 : _a.name) || customer.value,
            items: formatItemsForSubmission(rawItems),
            payments: rawPayments.map((p) => ({
              mode_of_payment: p.mode_of_payment,
              amount: p.amount,
              type: p.type
            })),
            discount_amount: additionalDiscount.value || 0,
            coupon_code: couponCode.value,
            custom_loyalty_points_to_redeem: loyaltyPointsToRedeem.value || 0,
            custom_cashback_to_use: loyaltyCashbackToUse.value || 0,
            selling_price_list: activePriceList.value || void 0,
            posa_bundle_selections: Object.keys(bundleSelections.value).length ? JSON.stringify(bundleSelections.value) : void 0,
            custom_approval_code: cardApprovalCodes.value.length ? cardApprovalCodes.value.join(", ") : void 0,
            custom_approval_codes: cardApprovalCodes.value.length ? cardApprovalCodes.value.map((c) => ({ approval_code: c })) : void 0,
            is_pos: 1,
            update_stock: 1
            // Critical: Ensures stock is updated
          };
          if (targetDoctype === "Sales Order" && deliveryDate) {
            invoiceData.delivery_date = deliveryDate;
          }
          if (rawSalesTeam && rawSalesTeam.length > 0) {
            invoiceData.sales_team = rawSalesTeam.map((member) => ({
              sales_person: member.sales_person,
              allocated_percentage: member.allocated_percentage || 0
            }));
          }
          const draftInvoice = yield updateInvoiceResource.submit({
            data: invoiceData
          });
          let invoiceDoc = draftInvoice;
          if (draftInvoice && typeof draftInvoice === "object" && "data" in draftInvoice) {
            invoiceDoc = draftInvoice.data;
          }
          if (!invoiceDoc || !invoiceDoc.name) {
            throw new Error(
              "Failed to create draft invoice - no invoice name returned"
            );
          }
          if (onDraftCreated) {
            try {
              onDraftCreated(invoiceDoc);
            } catch (callbackError) {
              log.error("onDraftCreated callback failed:", callbackError);
            }
          }
          const submitData = {
            change_amount: remainingAmount.value < 0 ? Math.abs(remainingAmount.value) : 0,
            write_off_amount: writeOffAmount || 0,
            is_tabby: isTabbyPayment.value ? 1 : 0
          };
          try {
            const result = yield submitInvoiceResource.submit({
              invoice: invoiceDoc,
              data: submitData
            });
            if (submitInvoiceResource.error) {
              const resourceError = submitInvoiceResource.error;
              console.error("Submit invoice resource error:", resourceError);
              const detailedError = new Error(
                resourceError.message || "Invoice submission failed"
              );
              detailedError.exc_type = resourceError.exc_type;
              detailedError._server_messages = resourceError._server_messages;
              detailedError.httpStatus = resourceError.httpStatus;
              detailedError.messages = resourceError.messages;
              throw detailedError;
            }
            resetInvoice();
            return result;
          } catch (error) {
            console.error("Submit invoice error:", error);
            if (submitInvoiceResource.error) {
              const resourceError = submitInvoiceResource.error;
              error.exc_type = resourceError.exc_type || error.exc_type;
              error._server_messages = resourceError._server_messages;
              error.httpStatus = resourceError.httpStatus;
              error.messages = resourceError.messages;
              error.exception = resourceError.exception;
              error.data = resourceError.data;
            }
            throw error;
          }
        } catch (error) {
          console.error("Submit invoice outer error:", error);
          throw error;
        } finally {
          isSubmitting.value = false;
        }
      }));
    });
  }
  function closeReservation(salesOrder, writeOffAmount = 0) {
    return __async(this, null, function* () {
      return yield submitMutex.withLock(() => __async(this, null, function* () {
        var _a;
        if (isSubmitting.value) {
          log.warn("Submission already in progress, skipping duplicate close");
          return null;
        }
        isSubmitting.value = true;
        try {
          const rawItems = toRaw(invoiceItems.value);
          const rawPayments = toRaw(payments.value);
          const invoiceData = {
            doctype: "Sales Invoice",
            pos_profile: posProfile.value,
            posa_pos_opening_shift: posOpeningShift.value,
            customer: ((_a = customer.value) == null ? void 0 : _a.name) || customer.value,
            items: formatItemsForSubmission(rawItems),
            payments: rawPayments.map((p) => ({
              mode_of_payment: p.mode_of_payment,
              amount: p.amount,
              type: p.type
            })),
            discount_amount: additionalDiscount.value || 0,
            coupon_code: couponCode.value,
            custom_loyalty_points_to_redeem: loyaltyPointsToRedeem.value || 0,
            custom_cashback_to_use: loyaltyCashbackToUse.value || 0,
            selling_price_list: activePriceList.value || void 0,
            posa_bundle_selections: Object.keys(bundleSelections.value).length ? JSON.stringify(bundleSelections.value) : void 0,
            is_pos: 1,
            update_stock: 1
          };
          const submitData = {
            change_amount: remainingAmount.value < 0 ? Math.abs(remainingAmount.value) : 0,
            write_off_amount: writeOffAmount || 0,
            is_tabby: isTabbyPayment.value ? 1 : 0
          };
          const result = yield closeReservationResource.submit({
            sales_order: salesOrder,
            invoice_data: invoiceData,
            data: submitData,
            pos_profile: posProfile.value
          });
          if (closeReservationResource.error) {
            throw new Error(
              closeReservationResource.error.message || "Failed to close party reservation"
            );
          }
          resetInvoice();
          return result;
        } finally {
          isSubmitting.value = false;
        }
      }));
    });
  }
  function setDefaultCustomer() {
    return __async(this, null, function* () {
      customer.value = null;
      if (!posProfile.value) {
        return;
      }
      try {
        const result = yield getDefaultCustomerResource.submit({
          pos_profile: posProfile.value
        });
        if (result && result.customer) {
          customer.value = {
            name: result.customer,
            customer_name: result.customer_name || result.customer,
            customer_group: result.customer_group
          };
        }
      } catch (error) {
        console.log("No default customer set in POS Profile");
      }
    });
  }
  function ensureDefaultCustomer(priceList = null, itemCode = null) {
    return __async(this, null, function* () {
      if (!posProfile.value) return null;
      try {
        const result = yield resolveDefaultCustomerResource.submit({
          pos_profile: posProfile.value,
          price_list: priceList || activePriceList.value || null,
          item_code: itemCode || null
        });
        const data = (result == null ? void 0 : result.message) || result;
        const itemDriven = !!(data == null ? void 0 : data.make_sales_order);
        if ((data == null ? void 0 : data.customer) && (itemDriven || !customer.value)) {
          customer.value = {
            name: data.customer,
            customer_name: data.customer_name || data.customer,
            customer_group: data.customer_group
          };
        }
        return data;
      } catch (error) {
        return null;
      }
    });
  }
  function repriceCart() {
    return __async(this, null, function* () {
      var _a, _b;
      if (!invoiceItems.value.length || !posProfile.value) return;
      for (const item of invoiceItems.value) {
        try {
          const res = yield getItemDetailsResource.submit({
            item_code: item.item_code,
            pos_profile: posProfile.value,
            customer: ((_a = customer.value) == null ? void 0 : _a.name) || customer.value,
            qty: item.quantity,
            uom: item.uom,
            price_list: activePriceList.value
          });
          const d = (res == null ? void 0 : res.message) || res;
          const rate = (_b = d == null ? void 0 : d.price_list_rate) != null ? _b : d == null ? void 0 : d.rate;
          if (rate != null) {
            item.price_list_rate = rate;
            item.rate = rate;
          }
          recalculateItem(item);
        } catch (e) {
        }
      }
      rebuildIncrementalCache();
    });
  }
  function setActivePriceList(priceList) {
    return __async(this, null, function* () {
      activePriceList.value = priceList || null;
      yield repriceCart();
    });
  }
  function resetInvoice() {
    invoiceItems.value = [];
    payments.value = [];
    additionalDiscount.value = 0;
    couponCode.value = null;
    loyaltyPointsToRedeem.value = 0;
    loyaltyCashbackToUse.value = 0;
    cardApprovalCodes.value = [];
    isTabbyPayment.value = false;
    bundleSelections.value = {};
    _cachedSubtotal.value = 0;
    _cachedTotalTax.value = 0;
    _cachedTotalDiscount.value = 0;
    _cachedTotalPaid.value = 0;
    setDefaultCustomer();
  }
  function clearCart() {
    return __async(this, null, function* () {
      for (const item of invoiceItems.value) {
        if (item.has_serial_no && item.serial_no) {
          serialStore.returnSerials(item.item_code, item.serial_no);
        }
      }
      invoiceItems.value = [];
      payments.value = [];
      additionalDiscount.value = 0;
      couponCode.value = null;
      loyaltyPointsToRedeem.value = 0;
      loyaltyCashbackToUse.value = 0;
      _cachedSubtotal.value = 0;
      _cachedTotalTax.value = 0;
      _cachedTotalDiscount.value = 0;
      _cachedTotalPaid.value = 0;
      setDefaultCustomer();
      if (!isOffline$1()) {
        try {
          yield cleanupDraftsResource.submit({
            pos_profile: posProfile.value,
            max_age_hours: 1
          });
        } catch (error) {
          console.warn("Failed to cleanup old drafts:", error);
        }
      }
    });
  }
  function loadTaxRules(profileName, posSettings = null) {
    return __async(this, null, function* () {
      try {
        const result = yield getTaxesResource.submit({ pos_profile: profileName });
        taxRules.value = (result == null ? void 0 : result.data) || result || [];
        if (posSettings && posSettings.tax_inclusive !== void 0) {
          taxInclusive.value = posSettings.tax_inclusive || false;
        }
        invoiceItems.value.forEach((item) => recalculateItem(item));
        rebuildIncrementalCache();
        return taxRules.value;
      } catch (error) {
        console.error("Error loading tax rules:", error);
        taxRules.value = [];
        return [];
      }
    });
  }
  function setTaxInclusive(value) {
    taxInclusive.value = value;
    invoiceItems.value.forEach((item) => recalculateItem(item));
    rebuildIncrementalCache();
  }
  return {
    // State
    invoiceItems,
    customer,
    payments,
    salesTeam,
    posProfile,
    posOpeningShift,
    additionalDiscount,
    couponCode,
    loyaltyPointsToRedeem,
    loyaltyCashbackToUse,
    cardApprovalCodes,
    isTabbyPayment,
    bundleSelections,
    setBundleSelection,
    taxRules,
    taxInclusive,
    isSubmitting,
    // Computed
    subtotal,
    notIncludedTotal,
    discountEligibleSubtotal,
    totalTax,
    totalDiscount,
    grandTotal,
    totalPaid,
    remainingAmount,
    canSubmit,
    // Actions
    addItem,
    removeItem,
    updateItemQuantity,
    updateItemRate,
    updateItemDiscount,
    calculateDiscountAmount,
    applyDiscount,
    removeDiscount,
    addPayment,
    removePayment,
    updatePayment,
    validateStock,
    saveDraft,
    submitInvoice,
    closeReservation,
    ensureDefaultCustomer,
    activePriceList,
    setActivePriceList,
    resetInvoice,
    clearCart,
    setDefaultCustomer,
    loadTaxRules,
    setTaxInclusive,
    recalculateItem,
    rebuildIncrementalCache,
    formatItemsForSubmission,
    resolveUomPricing,
    // Resources
    updateInvoiceResource,
    submitInvoiceResource,
    validateCartItemsResource,
    applyOffersResource,
    getItemDetailsResource,
    getTaxesResource
  };
}
const defaultSnapshot = () => ({
  subtotal: 0,
  itemCount: 0,
  itemCodes: [],
  itemGroups: [],
  brands: [],
  // Quantity maps for accurate min_qty/max_qty validation
  itemQuantities: {},
  // { item_code: qty }
  itemGroupQuantities: {},
  // { item_group: qty }
  brandQuantities: {}
  // { brand: qty }
});
function getDiscountSortValue(offer) {
  const percentage = Number.parseFloat(offer == null ? void 0 : offer.discount_percentage) || 0;
  if (percentage) {
    return percentage;
  }
  return Number.parseFloat(offer == null ? void 0 : offer.discount_amount) || 0;
}
const usePOSOffersStore = defineStore("posOffers", () => {
  const availableOffers = ref([]);
  const cartSnapshot = ref(defaultSnapshot());
  const hasFetched = ref(false);
  function updateCartSnapshot(snapshot = {}) {
    const subtotal = Number.parseFloat(snapshot.subtotal) || 0;
    const itemCount = Number.isFinite(snapshot.itemCount) ? snapshot.itemCount : 0;
    const itemCodes = Array.isArray(snapshot.itemCodes) ? snapshot.itemCodes : [];
    const itemGroups = Array.isArray(snapshot.itemGroups) ? snapshot.itemGroups : [];
    const brands = Array.isArray(snapshot.brands) ? snapshot.brands : [];
    const itemQuantities = snapshot.itemQuantities && typeof snapshot.itemQuantities === "object" ? snapshot.itemQuantities : {};
    const itemGroupQuantities = snapshot.itemGroupQuantities && typeof snapshot.itemGroupQuantities === "object" ? snapshot.itemGroupQuantities : {};
    const brandQuantities = snapshot.brandQuantities && typeof snapshot.brandQuantities === "object" ? snapshot.brandQuantities : {};
    cartSnapshot.value = {
      subtotal,
      itemCount,
      itemCodes,
      itemGroups,
      brands,
      itemQuantities,
      itemGroupQuantities,
      brandQuantities
    };
  }
  function resetCartSnapshot() {
    cartSnapshot.value = defaultSnapshot();
  }
  function setAvailableOffers(offers = []) {
    if (!Array.isArray(offers)) {
      availableOffers.value = [];
    } else {
      availableOffers.value = offers;
    }
    hasFetched.value = true;
  }
  function clearOffers() {
    availableOffers.value = [];
    hasFetched.value = false;
  }
  function getEligibleItemQuantity(offer) {
    const itemQuantities = cartSnapshot.value.itemQuantities || {};
    const itemGroupQuantities = cartSnapshot.value.itemGroupQuantities || {};
    const brandQuantities = cartSnapshot.value.brandQuantities || {};
    if ((offer == null ? void 0 : offer.apply_on) === "Item Code") {
      const eligibleItems = offer.eligible_items || [];
      if (eligibleItems.length > 0) {
        return eligibleItems.reduce((sum, itemCode) => {
          return sum + (itemQuantities[itemCode] || 0);
        }, 0);
      }
    } else if ((offer == null ? void 0 : offer.apply_on) === "Item Group") {
      const eligibleGroups = offer.eligible_item_groups || [];
      if (eligibleGroups.length > 0) {
        return eligibleGroups.reduce((sum, group) => {
          return sum + (itemGroupQuantities[group] || 0);
        }, 0);
      }
    } else if ((offer == null ? void 0 : offer.apply_on) === "Brand") {
      const eligibleBrands = offer.eligible_brands || [];
      if (eligibleBrands.length > 0) {
        return eligibleBrands.reduce((sum, brand) => {
          return sum + (brandQuantities[brand] || 0);
        }, 0);
      }
    }
    return cartSnapshot.value.itemCount || 0;
  }
  function checkOfferEligibility(offer) {
    const subtotal = cartSnapshot.value.subtotal || 0;
    const itemCount = cartSnapshot.value.itemCount || 0;
    const cartItemCodes = cartSnapshot.value.itemCodes || [];
    const cartItemGroups = cartSnapshot.value.itemGroups || [];
    const cartBrands = cartSnapshot.value.brands || [];
    if (itemCount === 0) {
      return {
        eligible: false,
        reason: "Cart is empty"
      };
    }
    let eligibleItemQty = itemCount;
    if ((offer == null ? void 0 : offer.apply_on) === "Item Code") {
      const eligibleItems = offer.eligible_items || [];
      if (eligibleItems.length > 0) {
        const hasEligibleItem = eligibleItems.some(
          (item) => cartItemCodes.includes(item)
        );
        if (!hasEligibleItem) {
          return {
            eligible: false,
            reason: __("Cart does not contain eligible items for this offer")
          };
        }
        eligibleItemQty = getEligibleItemQuantity(offer);
      }
    } else if ((offer == null ? void 0 : offer.apply_on) === "Item Group") {
      const eligibleGroups = offer.eligible_item_groups || [];
      if (eligibleGroups.length > 0) {
        const hasEligibleGroup = eligibleGroups.some(
          (group) => cartItemGroups.includes(group)
        );
        if (!hasEligibleGroup) {
          return {
            eligible: false,
            reason: __("Cart does not contain items from eligible groups")
          };
        }
        eligibleItemQty = getEligibleItemQuantity(offer);
      }
    } else if ((offer == null ? void 0 : offer.apply_on) === "Brand") {
      const eligibleBrands = offer.eligible_brands || [];
      if (eligibleBrands.length > 0) {
        const hasEligibleBrand = eligibleBrands.some(
          (brand) => cartBrands.includes(brand)
        );
        if (!hasEligibleBrand) {
          return {
            eligible: false,
            reason: __("Cart does not contain items from eligible brands")
          };
        }
        eligibleItemQty = getEligibleItemQuantity(offer);
      }
    }
    if ((offer == null ? void 0 : offer.min_qty) && eligibleItemQty < offer.min_qty) {
      return {
        eligible: false,
        reason: __("At least {0} eligible items required", [offer.min_qty])
      };
    }
    if ((offer == null ? void 0 : offer.max_qty) && eligibleItemQty > offer.max_qty) {
      return {
        eligible: false,
        reason: __("Maximum {0} eligible items allowed for this offer", [offer.max_qty])
      };
    }
    if ((offer == null ? void 0 : offer.min_amt) && subtotal < offer.min_amt) {
      return {
        eligible: false,
        reason: __("Minimum cart value of {0} required", [offer.min_amt])
      };
    }
    if ((offer == null ? void 0 : offer.max_amt) && subtotal > offer.max_amt) {
      return {
        eligible: false,
        reason: __("Maximum cart value exceeded ({0})", [offer.max_amt])
      };
    }
    return { eligible: true, reason: null };
  }
  const allEligibleOffers = computed(() => {
    return availableOffers.value.filter((offer) => {
      if (offer == null ? void 0 : offer.coupon_based) {
        return false;
      }
      const eligibility = checkOfferEligibility(offer);
      return eligibility.eligible;
    });
  });
  const allEligibleOffersSorted = computed(() => {
    return [...allEligibleOffers.value].sort((a, b) => {
      return getDiscountSortValue(b) - getDiscountSortValue(a);
    });
  });
  const autoEligibleOffers = computed(() => {
    return availableOffers.value.filter((offer) => {
      if (!(offer == null ? void 0 : offer.auto) || (offer == null ? void 0 : offer.coupon_based)) {
        return false;
      }
      const eligibility = checkOfferEligibility(offer);
      return eligibility.eligible;
    });
  });
  const autoEligibleCount = computed(() => autoEligibleOffers.value.length);
  function getUnlockAmount(offer) {
    const subtotal = cartSnapshot.value.subtotal || 0;
    if ((offer == null ? void 0 : offer.min_amt) && subtotal < offer.min_amt) {
      return offer.min_amt - subtotal;
    }
    return 0;
  }
  let fetchPromise = null;
  function ensureOffersFetched(posProfile) {
    return __async(this, null, function* () {
      if (hasFetched.value) {
        return true;
      }
      if (fetchPromise) {
        return fetchPromise;
      }
      if (!posProfile) {
        return false;
      }
      fetchPromise = (() => __async(this, null, function* () {
        try {
          if (isOffline$1()) {
            const cachedOffers = yield offlineWorker.getCachedOffers(posProfile);
            if (cachedOffers && cachedOffers.length > 0) {
              setAvailableOffers(cachedOffers);
              return true;
            }
            hasFetched.value = true;
            return false;
          }
          const response = yield call("ecs_posnext.api.offers.get_offers", {
            pos_profile: posProfile
          });
          const offers = (response == null ? void 0 : response.message) || response || [];
          setAvailableOffers(offers);
          if (offers.length > 0) {
            offlineWorker.cacheOffers(offers, posProfile).catch(() => {
            });
          }
          return true;
        } catch (error) {
          console.error("Error fetching offers:", error);
          hasFetched.value = true;
          return false;
        } finally {
          fetchPromise = null;
        }
      }))();
      return fetchPromise;
    });
  }
  return {
    // State
    availableOffers,
    cartSnapshot,
    hasFetched,
    // Computed
    allEligibleOffers,
    allEligibleOffersSorted,
    autoEligibleOffers,
    autoEligibleCount,
    // Actions
    updateCartSnapshot,
    resetCartSnapshot,
    setAvailableOffers,
    clearOffers,
    checkOfferEligibility,
    getUnlockAmount,
    ensureOffersFetched
  };
});
function cleanErrorMessage(rawMessage) {
  if (!rawMessage) return "";
  if (Array.isArray(rawMessage)) {
    return cleanErrorMessage(rawMessage[0]);
  }
  if (typeof rawMessage === "object" && rawMessage !== null) {
    return cleanErrorMessage(
      rawMessage.message || rawMessage.title || rawMessage.value
    );
  }
  let text2 = typeof rawMessage === "string" ? rawMessage : String(rawMessage);
  if (typeof window !== "undefined" && typeof document !== "undefined") {
    const container = document.createElement("div");
    container.innerHTML = text2;
    text2 = container.textContent || container.innerText || "";
  } else {
    text2 = text2.replace(/<[^>]*>/g, " ");
  }
  return text2.replace(/\s+/g, " ").trim();
}
function parseError(error) {
  const context = {
    title: __("Error"),
    message: __("An unexpected error occurred"),
    type: "error",
    // error, warning, validation
    retryable: false,
    technicalDetails: null
  };
  const detailsParts = [];
  if (error.exc_type) detailsParts.push(__("Type: {0}", [error.exc_type]));
  if (error.httpStatus || error.status)
    detailsParts.push(__("Status: {0}", [error.httpStatus || error.status]));
  if (error.exception) detailsParts.push(__("Exception: {0}", [error.exception], "Error"));
  context.technicalDetails = detailsParts.length > 0 ? detailsParts.join(" | ") : null;
  if (error.httpStatus === 417 || error.status === 417) {
    context.type = "validation";
    context.title = __("Validation Error");
  } else if (error.httpStatus === 403 || error.status === 403) {
    context.type = "error";
    context.title = __("Permission Denied");
  } else if (error.httpStatus === 404 || error.status === 404) {
    context.type = "warning";
    context.title = __("Not Found");
  } else if (error.httpStatus >= 500 || error.status >= 500) {
    context.type = "error";
    context.title = __("Server Error");
  }
  if (error.messages && Array.isArray(error.messages) && error.messages.length > 0) {
    context.message = cleanErrorMessage(error.messages[0]);
  } else if (error._server_messages) {
    try {
      const serverMessages = JSON.parse(error._server_messages);
      if (serverMessages && serverMessages.length > 0) {
        const firstMessage = JSON.parse(serverMessages[0]);
        context.message = cleanErrorMessage(
          firstMessage.message || firstMessage.title
        );
        if (firstMessage.title) context.title = firstMessage.title;
      }
    } catch (parseError2) {
      console.error("Error parsing _server_messages:", parseError2);
    }
  } else if (error.message) {
    context.message = cleanErrorMessage(error.message);
  }
  const normalizedMessage = (context.message || "").toLowerCase();
  const excType = (error.exc_type || "").toLowerCase();
  if (excType === "negativestockerror" || normalizedMessage.includes("needed in") || normalizedMessage.includes("insufficient stock") || normalizedMessage.includes("negative stock")) {
    context.type = "warning";
    context.title = __("Insufficient Stock");
    const match = context.message.match(
      /(\d+\.?\d*)\s+units?\s+of\s+(?:Item\s+)?(.+?)\s+needed\s+in\s+(?:Warehouse\s+)?(.+?)(?:\s+to complete|$)/i
    );
    if (match) {
      const [, quantity, itemName, warehouse] = match;
      const qty = Number.parseFloat(quantity);
      const unit = qty === 1 ? "unit" : "units";
      context.message = `Not enough stock for "${itemName}".

You need ${qty} ${unit} but the warehouse "${warehouse}" doesn't have enough available.

Please reduce the quantity or check another warehouse.`;
    } else if (!context.message || context.message === "An unexpected error occurred") {
      context.message = __("Not enough stock available in the warehouse.\n\nPlease reduce the quantity or check stock availability.");
    }
    context.retryable = true;
  } else if (excType === "validationerror" || context.type === "validation") {
    context.type = "validation";
    context.title = __("Validation Error");
    context.retryable = true;
  } else if (normalizedMessage.includes("price list") || normalizedMessage.includes("price not found")) {
    context.type = "warning";
    context.title = __("Pricing Error");
    context.retryable = true;
  } else if (normalizedMessage.includes("customer") || normalizedMessage.includes("party")) {
    context.type = "validation";
    context.title = __("Customer Error");
    context.retryable = true;
  } else if (normalizedMessage.includes("tax") || normalizedMessage.includes("account")) {
    context.type = "warning";
    context.title = __("Tax Configuration Error");
    context.retryable = false;
  } else if (normalizedMessage.includes("payment") || normalizedMessage.includes("mode of payment")) {
    context.type = "validation";
    context.title = __("Payment Error");
    context.retryable = true;
  } else if (normalizedMessage.includes("series") || normalizedMessage.includes("naming")) {
    context.type = "error";
    context.title = __("Naming Series Error");
    context.retryable = false;
  } else if (normalizedMessage.includes("permission") || normalizedMessage.includes("not allowed")) {
    context.type = "error";
    context.title = __("Permission Denied");
    context.retryable = false;
  } else if (normalizedMessage.includes("network") || normalizedMessage.includes("timeout") || normalizedMessage.includes("connection") || normalizedMessage.includes("fetch")) {
    context.type = "warning";
    context.title = __("Connection Error");
    context.message = __("Unable to connect to server. Check your internet connection.");
    context.retryable = true;
  } else if (normalizedMessage.includes("duplicate") || normalizedMessage.includes("already exists")) {
    context.type = "validation";
    context.title = __("Duplicate Entry");
    context.retryable = false;
  }
  return context;
}
function checkStockAvailability({
  itemCode,
  qty,
  warehouse,
  actualQty = null
}) {
  if (actualQty !== null && actualQty !== void 0) {
    const available = actualQty >= qty;
    return {
      available,
      actualQty
    };
  }
  return {
    available: true,
    actualQty: qty
  };
}
function getItemStock(itemCode, warehouse) {
  return __async(this, null, function* () {
    try {
      const result = yield call$1("frappe.client.get_value", {
        doctype: "Bin",
        filters: {
          item_code: itemCode,
          warehouse
        },
        fieldname: "actual_qty"
      });
      return Number.parseFloat((result == null ? void 0 : result.actual_qty) || 0);
    } catch (error) {
      console.warn("Failed to fetch stock:", error);
      return 0;
    }
  });
}
function formatStockError(itemName, requested, available, warehouse) {
  const unit = requested === 1 ? "unit" : "units";
  const availableUnit = available === 1 ? "unit" : "units";
  if (available === 0) {
    return `"${itemName}" is out of stock in warehouse "${warehouse}".

Please check another warehouse or restock this item.`;
  }
  return `Not enough stock for "${itemName}".

You requested ${requested} ${unit}, but only ${available} ${availableUnit} available in "${warehouse}".

Please reduce the quantity or check another warehouse.`;
}
function createAsyncQueue() {
  let isProcessing = false;
  let pendingTask = null;
  let currentAbortController = null;
  return {
    /**
     * Enqueue a task. If already processing, replaces any pending task.
     * @param {Function} taskFn - Async function to execute
     * @returns {Promise} Resolves when task completes or is superseded
     */
    enqueue(taskFn) {
      return __async(this, null, function* () {
        if (isProcessing) {
          pendingTask = taskFn;
          return;
        }
        isProcessing = true;
        currentAbortController = new AbortController();
        try {
          yield taskFn(currentAbortController.signal);
        } finally {
          isProcessing = false;
          currentAbortController = null;
          if (pendingTask) {
            const next = pendingTask;
            pendingTask = null;
            yield this.enqueue(next);
          }
        }
      });
    },
    /**
     * Cancel current operation and clear pending tasks
     */
    cancel() {
      if (currentAbortController) {
        currentAbortController.abort();
      }
      pendingTask = null;
    },
    /**
     * Check if queue is currently processing
     */
    get isProcessing() {
      return isProcessing;
    },
    /**
     * Check if there's a pending task
     */
    get hasPending() {
      return pendingTask !== null;
    }
  };
}
const usePOSCartStore = defineStore("posCart", () => {
  const {
    invoiceItems,
    customer,
    subtotal,
    notIncludedTotal,
    discountEligibleSubtotal,
    totalTax,
    totalDiscount,
    grandTotal,
    posProfile,
    posOpeningShift,
    payments,
    salesTeam,
    additionalDiscount,
    taxInclusive,
    loyaltyPointsToRedeem,
    loyaltyCashbackToUse,
    cardApprovalCodes,
    isTabbyPayment,
    bundleSelections,
    setBundleSelection,
    isSubmitting,
    addItem: addItemToInvoice,
    removeItem,
    updateItemQuantity,
    submitInvoice: baseSubmitInvoice,
    closeReservation: baseCloseReservation,
    ensureDefaultCustomer,
    activePriceList,
    setActivePriceList,
    clearCart: clearInvoiceCart,
    loadTaxRules,
    setTaxInclusive,
    setDefaultCustomer,
    applyDiscount,
    removeDiscount,
    applyOffersResource,
    getItemDetailsResource,
    resolveUomPricing,
    recalculateItem,
    rebuildIncrementalCache,
    formatItemsForSubmission
  } = useInvoice();
  const offersStore = usePOSOffersStore();
  const settingsStore = usePOSSettingsStore();
  const pendingItem = ref(null);
  const pendingItemQty = ref(1);
  const appliedOffers = ref([]);
  const appliedCoupon = ref(null);
  const selectionMode = ref("uom");
  const suppressOfferReapply = ref(false);
  const currentDraftId = ref(null);
  const targetDoctype = ref("Sales Invoice");
  const offerProcessingState = ref({
    isProcessing: false,
    // True while any offer operation is running
    isAutoProcessing: false,
    // True during automatic offer processing
    lastProcessedAt: 0,
    // Timestamp of last successful processing
    lastCartHash: "",
    // Hash of cart state when last processed
    error: null,
    // Last error if any
    retryCount: 0
    // Number of consecutive failures
  });
  let cartGeneration = 0;
  const offerQueue = createAsyncQueue();
  const isProcessingOffers = computed(
    () => offerProcessingState.value.isProcessing
  );
  function generateCartHash() {
    var _a;
    const items = invoiceItems.value;
    const parts = [
      // Item details: code, quantity, uom, discount
      items.map(
        (i) => `${i.item_code}:${i.quantity}:${i.uom || ""}:${i.discount_percentage || 0}`
      ).join("|"),
      // Total item count
      items.length.toString(),
      // Subtotal (rounded to avoid floating point issues)
      Math.round((subtotal.value || 0) * 100).toString(),
      // Customer
      ((_a = customer.value) == null ? void 0 : _a.name) || customer.value || "none",
      // Applied offers count
      appliedOffers.value.length.toString()
    ];
    return parts.join("::");
  }
  const { showSuccess, showError, showWarning } = useToast();
  const itemCount = computed(() => invoiceItems.value.length);
  const isEmpty = computed(() => invoiceItems.value.length === 0);
  const hasCustomer = computed(() => !!customer.value);
  function addItem(item, qty = 1, autoAdd = false, currentProfile = null) {
    const isNonStockItem = item.is_stock_item === 0 || item.is_stock_item === false;
    const hasActualQty = item.actual_qty !== void 0 || item.stock_qty !== void 0;
    const shouldValidateStock = !isNonStockItem && (item.is_stock_item || item.is_bundle || hasActualQty);
    if (currentProfile && !autoAdd && settingsStore.shouldEnforceStockValidation() && shouldValidateStock && !item.has_serial_no && !item.has_batch_no) {
      const warehouse = item.warehouse || currentProfile.warehouse;
      const actualQty = item.actual_qty !== void 0 ? item.actual_qty : item.stock_qty || 0;
      if (warehouse && actualQty !== void 0 && actualQty !== null) {
        const stockCheck = checkStockAvailability({
          itemCode: item.item_code,
          qty,
          warehouse,
          actualQty
        });
        if (!stockCheck.available) {
          const itemType = item.is_bundle ? "Bundle" : "Item";
          const errorMsg = formatStockError(
            item.item_name,
            qty,
            stockCheck.actualQty,
            warehouse
          );
          throw new Error(errorMsg.replace("Item", itemType));
        }
      }
    }
    ensureDefaultCustomer(activePriceList.value, item.item_code).then((res) => {
      if (res == null ? void 0 : res.make_sales_order) {
        setTargetDoctype("Sales Order");
      }
    });
    addItemToInvoice(item, qty);
  }
  function clearCart() {
    debouncedProcessOffers.cancel();
    offerQueue.cancel();
    clearInvoiceCart();
    customer.value = null;
    appliedOffers.value = [];
    appliedCoupon.value = null;
    currentDraftId.value = null;
    targetDoctype.value = "Sales Invoice";
    reservationSalesOrder.value = null;
    reservationDeposit.value = 0;
    suppressOfferReapply.value = false;
    offerProcessingState.value.lastCartHash = "";
    offerProcessingState.value.error = null;
    offerProcessingState.value.retryCount = 0;
    syncOfferSnapshot();
  }
  function setTargetDoctype(doctype) {
    targetDoctype.value = doctype;
  }
  const deliveryDate = ref("");
  const writeOffAmount = ref(0);
  function setDeliveryDate(date) {
    deliveryDate.value = date;
  }
  function setWriteOffAmount(amount) {
    writeOffAmount.value = amount || 0;
  }
  function submitInvoice(onDraftCreated) {
    return __async(this, null, function* () {
      if (invoiceItems.value.length === 0) {
        showWarning(__("Cart is empty"));
        return;
      }
      if (!customer.value) {
        showWarning(__("Please select a customer"));
        return;
      }
      if (reservationSalesOrder.value) {
        return yield closeReservation();
      }
      const result = yield baseSubmitInvoice(
        targetDoctype.value,
        deliveryDate.value,
        writeOffAmount.value,
        onDraftCreated
      );
      if (result) {
        writeOffAmount.value = 0;
      }
      return result;
    });
  }
  function createSalesOrder() {
    return __async(this, null, function* () {
      return yield submitInvoice();
    });
  }
  const reservationSalesOrder = ref(null);
  const reservationDeposit = ref(0);
  function loadReservationOrder(order) {
    clearCart();
    if (order.customer) {
      setCustomer({
        name: order.customer,
        customer_name: order.customer_name || order.customer
      });
    }
    for (const it of order.items || []) {
      addItemToInvoice(
        {
          item_code: it.item_code,
          item_name: it.item_name,
          rate: it.rate,
          price_list_rate: it.rate,
          uom: it.uom,
          warehouse: it.warehouse,
          sales_order: it.sales_order || order.name || order.sales_order
        },
        it.qty || 1
      );
    }
    if (order.delivery_date) {
      setDeliveryDate(order.delivery_date);
    }
    reservationSalesOrder.value = order.name || order.sales_order;
    reservationDeposit.value = order.total_deposit || 0;
  }
  function closeReservation() {
    return __async(this, null, function* () {
      if (!reservationSalesOrder.value) {
        return yield submitInvoice();
      }
      if (invoiceItems.value.length === 0) {
        showWarning(__("Cart is empty"));
        return;
      }
      if (!customer.value) {
        showWarning(__("Please select a customer"));
        return;
      }
      const result = yield baseCloseReservation(
        reservationSalesOrder.value,
        writeOffAmount.value
      );
      if (result) {
        reservationSalesOrder.value = null;
        writeOffAmount.value = 0;
      }
      return result;
    });
  }
  function setCustomer(selectedCustomer) {
    customer.value = selectedCustomer;
  }
  function setPendingItem(item, qty = 1, mode = "uom") {
    pendingItem.value = item;
    pendingItemQty.value = qty;
    selectionMode.value = mode;
  }
  function clearPendingItem() {
    pendingItem.value = null;
    pendingItemQty.value = 1;
    selectionMode.value = "uom";
  }
  function applyDiscountToCart(discount) {
    applyDiscount(discount);
    appliedCoupon.value = discount;
    showSuccess(__("{0} applied successfully", [discount.name]));
  }
  function removeDiscountFromCart() {
    suppressOfferReapply.value = true;
    appliedOffers.value = [];
    removeDiscount();
    appliedCoupon.value = null;
    showSuccess(__("Discount has been removed from cart"));
  }
  function buildOfferEvaluationPayload(currentProfile) {
    var _a, _b;
    const rawItems = toRaw(invoiceItems.value);
    return {
      doctype: "Sales Invoice",
      pos_profile: posProfile.value,
      customer: ((_a = customer.value) == null ? void 0 : _a.name) || customer.value || (currentProfile == null ? void 0 : currentProfile.customer),
      company: currentProfile == null ? void 0 : currentProfile.company,
      selling_price_list: currentProfile == null ? void 0 : currentProfile.selling_price_list,
      currency: currentProfile == null ? void 0 : currentProfile.currency,
      discount_amount: additionalDiscount.value || 0,
      coupon_code: ((_b = appliedCoupon.value) == null ? void 0 : _b.name) || "",
      items: rawItems.map((item) => ({
        item_code: item.item_code,
        item_name: item.item_name,
        qty: item.quantity,
        rate: item.rate,
        uom: item.uom,
        warehouse: item.warehouse,
        conversion_factor: item.conversion_factor || 1,
        price_list_rate: item.price_list_rate || item.rate,
        discount_percentage: item.discount_percentage || 0,
        discount_amount: item.discount_amount || 0
      }))
    };
  }
  function hasPricingRules(value) {
    if (!value) return false;
    if (Array.isArray(value)) return value.length > 0;
    return typeof value === "string" && value.trim().length > 0;
  }
  function applyDiscountsFromServer(serverItems) {
    if (!Array.isArray(serverItems)) return false;
    let hasDiscounts = false;
    invoiceItems.value.forEach((item, index) => {
      const serverItem = serverItems[index] || {};
      const discountPct = Number.parseFloat(serverItem.discount_percentage) || 0;
      const discountAmt = Number.parseFloat(serverItem.discount_amount) || 0;
      if (hasPricingRules(serverItem.pricing_rules) || discountPct > 0 || discountAmt > 0) {
        item.discount_percentage = discountPct;
        item.discount_amount = discountAmt;
        item.pricing_rules = serverItem.pricing_rules;
        hasDiscounts = discountPct > 0 || discountAmt > 0;
      }
      recalculateItem(item);
    });
    rebuildIncrementalCache();
    return hasDiscounts;
  }
  function processFreeItems(freeItems) {
    invoiceItems.value.forEach((item) => {
      item.free_qty = 0;
    });
    if (!Array.isArray(freeItems) || freeItems.length === 0) {
      return;
    }
    for (const freeItem of freeItems) {
      const freeQty = Number.parseFloat(freeItem.qty) || 0;
      if (freeQty <= 0) continue;
      const cartItem = invoiceItems.value.find(
        (item) => item.item_code === freeItem.item_code && (item.uom || item.stock_uom) === (freeItem.uom || freeItem.stock_uom)
      );
      if (cartItem) {
        cartItem.free_qty = freeQty;
      }
    }
  }
  function parseOfferResponse(response) {
    const payload = (response == null ? void 0 : response.message) || response || {};
    return {
      items: Array.isArray(payload.items) ? payload.items : [],
      freeItems: Array.isArray(payload.free_items) ? payload.free_items : [],
      // CRITICAL: Only trust explicitly returned rules - NO FALLBACK
      // If backend doesn't return applied_pricing_rules, NO offers were applied
      appliedRules: Array.isArray(payload.applied_pricing_rules) ? payload.applied_pricing_rules : []
    };
  }
  function getAppliedOfferCodes() {
    return appliedOffers.value.map((entry) => entry.code);
  }
  function filterActiveOffers(appliedRuleNames = []) {
    if (!Array.isArray(appliedRuleNames) || appliedRuleNames.length === 0) {
      appliedOffers.value = [];
      return;
    }
    appliedOffers.value = appliedOffers.value.filter(
      (entry) => appliedRuleNames.includes(entry.code)
    );
  }
  function applyOffer(offer, currentProfile, offersDialogRef = null) {
    return __async(this, null, function* () {
      if (!offer) {
        console.error("No offer provided");
        offersDialogRef == null ? void 0 : offersDialogRef.resetApplyingState();
        return false;
      }
      const offerCode = offer.name;
      const existingCodes = getAppliedOfferCodes();
      const alreadyApplied = existingCodes.includes(offerCode);
      if (alreadyApplied) {
        return yield removeOffer(offerCode, currentProfile, offersDialogRef);
      }
      if (!posProfile.value || invoiceItems.value.length === 0) {
        showWarning(__("Add items to the cart before applying an offer."));
        offersDialogRef == null ? void 0 : offersDialogRef.resetApplyingState();
        return false;
      }
      debouncedProcessOffers.cancel();
      offerQueue.cancel();
      let result = false;
      yield offerQueue.enqueue((signal) => __async(this, null, function* () {
        if (signal == null ? void 0 : signal.aborted) return;
        try {
          offerProcessingState.value.isProcessing = true;
          offerProcessingState.value.error = null;
          const invoiceData = buildOfferEvaluationPayload(currentProfile);
          const offerNames = [.../* @__PURE__ */ new Set([...existingCodes, offerCode])];
          const response = yield applyOffersResource.submit({
            invoice_data: invoiceData,
            selected_offers: offerNames
          });
          if (signal == null ? void 0 : signal.aborted) return;
          const {
            items: responseItems,
            freeItems,
            appliedRules
          } = parseOfferResponse(response);
          suppressOfferReapply.value = true;
          applyDiscountsFromServer(responseItems);
          processFreeItems(freeItems);
          filterActiveOffers(appliedRules);
          const offerApplied = appliedRules.includes(offerCode);
          if (!offerApplied) {
            if (existingCodes.length) {
              try {
                const rollbackResponse = yield applyOffersResource.submit({
                  invoice_data: invoiceData,
                  selected_offers: existingCodes
                });
                const {
                  items: rollbackItems,
                  freeItems: rollbackFreeItems,
                  appliedRules: rollbackRules
                } = parseOfferResponse(rollbackResponse);
                applyDiscountsFromServer(rollbackItems);
                processFreeItems(rollbackFreeItems);
                filterActiveOffers(rollbackRules);
              } catch (rollbackError) {
                console.error("Error rolling back offers:", rollbackError);
              }
            }
            showWarning(
              __("Your cart doesn't meet the requirements for this offer.")
            );
            offersDialogRef == null ? void 0 : offersDialogRef.resetApplyingState();
            result = false;
            return;
          }
          const offerRuleCodes = appliedRules.includes(offerCode) ? appliedRules.filter((ruleName) => ruleName === offerCode) : [offerCode];
          const updatedEntries = appliedOffers.value.filter(
            (entry) => entry.code !== offerCode
          );
          updatedEntries.push({
            name: offer.title || offer.name,
            code: offerCode,
            offer,
            // Store full offer object for validation
            source: "manual",
            applied: true,
            rules: offerRuleCodes,
            // Store constraints for quick validation
            min_qty: offer.min_qty,
            max_qty: offer.max_qty,
            min_amt: offer.min_amt,
            max_amt: offer.max_amt
          });
          appliedOffers.value = updatedEntries;
          offerProcessingState.value.lastProcessedAt = Date.now();
          yield nextTick();
          showSuccess(__("{0} applied successfully", [offer.title || offer.name]));
          result = true;
        } catch (error) {
          if (signal == null ? void 0 : signal.aborted) return;
          console.error("Error applying offer:", error);
          offerProcessingState.value.error = error.message;
          showError(__("Failed to apply offer. Please try again."));
          offersDialogRef == null ? void 0 : offersDialogRef.resetApplyingState();
          result = false;
        } finally {
          offerProcessingState.value.isProcessing = false;
        }
      }));
      return result;
    });
  }
  function removeOffer(offer, currentProfile = null, offersDialogRef = null) {
    return __async(this, null, function* () {
      const offerCode = typeof offer === "string" ? offer : (offer == null ? void 0 : offer.name) || (offer == null ? void 0 : offer.code);
      debouncedProcessOffers.cancel();
      if (!offerCode) {
        offerQueue.cancel();
        suppressOfferReapply.value = true;
        appliedOffers.value = [];
        processFreeItems([]);
        removeDiscount();
        yield nextTick();
        showSuccess(__("Offer has been removed from cart"));
        offersDialogRef == null ? void 0 : offersDialogRef.resetApplyingState();
        return true;
      }
      const remainingOffers = appliedOffers.value.filter(
        (entry) => entry.code !== offerCode
      );
      const remainingCodes = remainingOffers.map((entry) => entry.code);
      if (remainingCodes.length === 0) {
        offerQueue.cancel();
        suppressOfferReapply.value = true;
        appliedOffers.value = [];
        processFreeItems([]);
        removeDiscount();
        yield nextTick();
        showSuccess(__("Offer has been removed from cart"));
        offersDialogRef == null ? void 0 : offersDialogRef.resetApplyingState();
        return true;
      }
      let result = false;
      yield offerQueue.enqueue((signal) => __async(this, null, function* () {
        if (signal == null ? void 0 : signal.aborted) return;
        try {
          offerProcessingState.value.isProcessing = true;
          offerProcessingState.value.error = null;
          const invoiceData = buildOfferEvaluationPayload(currentProfile);
          const response = yield applyOffersResource.submit({
            invoice_data: invoiceData,
            selected_offers: remainingCodes
          });
          if (signal == null ? void 0 : signal.aborted) return;
          const {
            items: responseItems,
            freeItems,
            appliedRules
          } = parseOfferResponse(response);
          suppressOfferReapply.value = true;
          applyDiscountsFromServer(responseItems);
          processFreeItems(freeItems);
          filterActiveOffers(appliedRules);
          appliedOffers.value = appliedOffers.value.filter(
            (entry) => remainingCodes.includes(entry.code)
          );
          offerProcessingState.value.lastProcessedAt = Date.now();
          yield nextTick();
          showSuccess(__("Offer has been removed from cart"));
          offersDialogRef == null ? void 0 : offersDialogRef.resetApplyingState();
          result = true;
        } catch (error) {
          if (signal == null ? void 0 : signal.aborted) return;
          console.error("Error removing offer:", error);
          offerProcessingState.value.error = error.message;
          showError(__("Failed to update cart after removing offer."));
          offersDialogRef == null ? void 0 : offersDialogRef.resetApplyingState();
          result = false;
        } finally {
          offerProcessingState.value.isProcessing = false;
        }
      }));
      return result;
    });
  }
  function reapplyOffer(currentProfile, signal = null) {
    return __async(this, null, function* () {
      if (invoiceItems.value.length === 0 && appliedOffers.value.length) {
        appliedOffers.value = [];
        processFreeItems([]);
        return true;
      }
      if (appliedOffers.value.length === 0 || invoiceItems.value.length === 0) {
        return false;
      }
      if (signal == null ? void 0 : signal.aborted) return false;
      try {
        const cartSnapshot = buildCartSnapshot();
        const invalidOffers = [];
        for (const appliedOffer of appliedOffers.value) {
          const offer = appliedOffer.offer;
          if (!offer) continue;
          offersStore.updateCartSnapshot(cartSnapshot);
          const { eligible, reason } = offersStore.checkOfferEligibility(offer);
          if (!eligible) {
            invalidOffers.push(__spreadProps(__spreadValues({}, appliedOffer), {
              reason
            }));
          }
        }
        if (signal == null ? void 0 : signal.aborted) return false;
        if (invalidOffers.length > 0) {
          const validOfferCodes = appliedOffers.value.filter((o) => !invalidOffers.find((inv) => inv.code === o.code)).map((o) => o.code);
          if (validOfferCodes.length === 0) {
            appliedOffers.value = [];
            processFreeItems([]);
            invoiceItems.value.forEach((item) => {
              if (item.pricing_rules && item.pricing_rules.length > 0) {
                item.discount_percentage = 0;
                item.discount_amount = 0;
                item.pricing_rules = [];
                recalculateItem(item);
              }
            });
            rebuildIncrementalCache();
          } else {
            const invoiceData = buildOfferEvaluationPayload(currentProfile);
            const response = yield applyOffersResource.submit({
              invoice_data: invoiceData,
              selected_offers: validOfferCodes
            });
            if (signal == null ? void 0 : signal.aborted) return false;
            const {
              items: responseItems,
              freeItems,
              appliedRules
            } = parseOfferResponse(response);
            applyDiscountsFromServer(responseItems);
            processFreeItems(freeItems);
            filterActiveOffers(appliedRules);
            appliedOffers.value = appliedOffers.value.filter(
              (entry) => appliedRules.includes(entry.code)
            );
          }
          yield nextTick();
          const offerNames = invalidOffers.map((o) => o.name).join(", ");
          showWarning(
            __("Offer removed: {0}. Cart no longer meets requirements.", [
              offerNames
            ])
          );
          return true;
        }
        return false;
      } catch (error) {
        if (signal == null ? void 0 : signal.aborted) return false;
        console.error("Error validating offers:", error);
        offerProcessingState.value.error = error.message;
        return false;
      }
    });
  }
  function autoApplyEligibleOffers(currentProfile, signal = null) {
    return __async(this, null, function* () {
      if (invoiceItems.value.length === 0 || !offersStore.hasFetched) {
        return;
      }
      if (signal == null ? void 0 : signal.aborted) return;
      try {
        const cartSnapshot = buildCartSnapshot();
        offersStore.updateCartSnapshot(cartSnapshot);
        const allEligibleOffers = offersStore.allEligibleOffers;
        if (allEligibleOffers.length === 0) {
          return;
        }
        const appliedOfferCodes = new Set(appliedOffers.value.map((o) => o.code));
        const newOffers = allEligibleOffers.filter(
          (offer) => !appliedOfferCodes.has(offer.name)
        );
        if (newOffers.length === 0) {
          return;
        }
        if (signal == null ? void 0 : signal.aborted) return;
        const existingCodes = appliedOffers.value.map((entry) => entry.code);
        const newOfferCodes = newOffers.map((offer) => offer.name);
        const allCodes = [...existingCodes, ...newOfferCodes];
        const invoiceData = buildOfferEvaluationPayload(currentProfile);
        const response = yield applyOffersResource.submit({
          invoice_data: invoiceData,
          selected_offers: allCodes
        });
        if (signal == null ? void 0 : signal.aborted) return;
        const {
          items: responseItems,
          freeItems,
          appliedRules
        } = parseOfferResponse(response);
        applyDiscountsFromServer(responseItems);
        processFreeItems(freeItems);
        filterActiveOffers(appliedRules);
        const newlyAppliedOffers = [];
        for (const offer of newOffers) {
          const offerCode = offer.name;
          if (!appliedRules.includes(offerCode)) {
            continue;
          }
          const offerRuleCodes = appliedRules.filter(
            (ruleName) => ruleName === offerCode
          );
          appliedOffers.value.push({
            name: offer.title || offer.name,
            code: offerCode,
            offer,
            // Store full offer object for validation
            source: "auto",
            applied: true,
            rules: offerRuleCodes,
            min_qty: offer.min_qty,
            max_qty: offer.max_qty,
            min_amt: offer.min_amt,
            max_amt: offer.max_amt
          });
          newlyAppliedOffers.push(offer.title || offer.name);
        }
        offerProcessingState.value.lastProcessedAt = Date.now();
        yield nextTick();
        if (newlyAppliedOffers.length > 0) {
          if (newlyAppliedOffers.length === 1) {
            showSuccess(__("Offer applied: {0}", [newlyAppliedOffers[0]]));
          } else {
            showSuccess(
              __("Offers applied: {0}", [newlyAppliedOffers.join(", ")])
            );
          }
        }
      } catch (error) {
        if (signal == null ? void 0 : signal.aborted) return;
        console.error("Error auto-applying offers:", error);
        offerProcessingState.value.error = error.message;
      }
    });
  }
  function applyOffersOffline() {
    if (invoiceItems.value.length === 0 || !offersStore.hasFetched) {
      return;
    }
    if (!offlineState.isOffline) {
      return;
    }
    try {
      const cartSnapshot = buildCartSnapshot();
      offersStore.updateCartSnapshot(cartSnapshot);
      const eligibleOffers = offersStore.autoEligibleOffers;
      if (eligibleOffers.length === 0) {
        return;
      }
      const appliedOfferCodes = new Set(appliedOffers.value.map((o) => o.code));
      const newOffers = eligibleOffers.filter(
        (offer) => !appliedOfferCodes.has(offer.name)
      );
      if (newOffers.length === 0) {
        return;
      }
      const newlyAppliedOffers = [];
      for (const offer of newOffers) {
        const isProductDiscount = offer.offer === "Give Product";
        let eligibleItems = [];
        if (offer.apply_on === "Item Code") {
          const eligibleCodes = offer.eligible_items || [];
          eligibleItems = invoiceItems.value.filter(
            (item) => eligibleCodes.includes(item.item_code)
          );
        } else if (offer.apply_on === "Item Group") {
          const eligibleGroups = offer.eligible_item_groups || [];
          eligibleItems = invoiceItems.value.filter(
            (item) => eligibleGroups.includes(item.item_group)
          );
        } else if (offer.apply_on === "Brand") {
          const eligibleBrands = offer.eligible_brands || [];
          eligibleItems = invoiceItems.value.filter(
            (item) => eligibleBrands.includes(item.brand)
          );
        } else if (offer.apply_on === "Transaction") {
          eligibleItems = invoiceItems.value;
        }
        if (eligibleItems.length === 0) continue;
        let offerApplied = false;
        if (isProductDiscount) {
          offerApplied = applyOfflineFreeItem(offer, eligibleItems);
        } else {
          offerApplied = applyOfflinePriceDiscount(offer, eligibleItems);
        }
        if (offerApplied) {
          appliedOffers.value.push({
            name: offer.title || offer.name,
            code: offer.name,
            offer,
            source: "offline",
            applied: true,
            rules: [offer.name],
            min_qty: offer.min_qty,
            max_qty: offer.max_qty,
            min_amt: offer.min_amt,
            max_amt: offer.max_amt
          });
          newlyAppliedOffers.push(offer.title || offer.name);
        }
      }
      if (newlyAppliedOffers.length > 0) {
        rebuildIncrementalCache();
        showSuccess(__("Offline: {0} applied", [newlyAppliedOffers.join(", ")]));
      }
    } catch (error) {
      console.error("Error applying offers offline:", error);
    }
  }
  function applyOfflinePriceDiscount(offer, eligibleItems) {
    const discountType = offer.discount_type || offer.rate_or_discount;
    const discountPercentage = Number.parseFloat(offer.discount_percentage) || 0;
    const discountAmount = Number.parseFloat(offer.discount_amount) || 0;
    const rate = Number.parseFloat(offer.rate) || 0;
    let applied = false;
    for (const item of eligibleItems) {
      if (item.pricing_rules && item.pricing_rules.length > 0) continue;
      if (discountType === "Discount Percentage" && discountPercentage > 0) {
        item.discount_percentage = discountPercentage;
        item.pricing_rules = [offer.name];
        recalculateItem(item);
        applied = true;
      } else if (discountType === "Discount Amount" && discountAmount > 0) {
        item.discount_amount = discountAmount;
        item.pricing_rules = [offer.name];
        recalculateItem(item);
        applied = true;
      } else if (discountType === "Rate" && rate > 0) {
        item.rate = rate;
        item.pricing_rules = [offer.name];
        recalculateItem(item);
        applied = true;
      }
    }
    return applied;
  }
  function applyOfflineFreeItem(offer, eligibleItems) {
    const freeQty = Number.parseFloat(offer.free_qty) || 0;
    const sameItem = offer.same_item === 1;
    const isRecursive = offer.is_recursive === 1;
    const recurseFor = Number.parseFloat(offer.recurse_for) || 0;
    const applyRecursionOver = Number.parseFloat(offer.apply_recursion_over) || 0;
    const freeItemCode = offer.free_item;
    if (freeQty <= 0) return false;
    let applied = false;
    if (sameItem) {
      for (const item of eligibleItems) {
        let freeItemsToGive = freeQty;
        if (isRecursive && recurseFor > 0) {
          const effectiveQty = Math.max(0, item.quantity - applyRecursionOver);
          const multiplier = Math.floor(effectiveQty / recurseFor);
          freeItemsToGive = multiplier * freeQty;
        } else if (!isRecursive && offer.min_qty > 0) {
          if (item.quantity >= offer.min_qty) {
            freeItemsToGive = freeQty;
          } else {
            freeItemsToGive = 0;
          }
        }
        if (freeItemsToGive > 0 && (!item.free_qty || item.free_qty === 0)) {
          item.free_qty = freeItemsToGive;
          item.pricing_rules = item.pricing_rules || [];
          if (!item.pricing_rules.includes(offer.name)) {
            item.pricing_rules.push(offer.name);
          }
          applied = true;
        }
      }
    } else if (freeItemCode) {
      const freeItemInCart = invoiceItems.value.find(
        (item) => item.item_code === freeItemCode
      );
      if (freeItemInCart) {
        let freeItemsToGive = freeQty;
        if (isRecursive && recurseFor > 0) {
          const totalEligibleQty = eligibleItems.reduce(
            (sum, item) => sum + (item.quantity || 0),
            0
          );
          const effectiveQty = Math.max(
            0,
            totalEligibleQty - applyRecursionOver
          );
          const multiplier = Math.floor(effectiveQty / recurseFor);
          freeItemsToGive = multiplier * freeQty;
        }
        if (freeItemsToGive > 0 && (!freeItemInCart.free_qty || freeItemInCart.free_qty === 0)) {
          freeItemInCart.free_qty = freeItemsToGive;
          freeItemInCart.pricing_rules = freeItemInCart.pricing_rules || [];
          if (!freeItemInCart.pricing_rules.includes(offer.name)) {
            freeItemInCart.pricing_rules.push(offer.name);
          }
          applied = true;
        }
      }
    }
    return applied;
  }
  function buildCartSnapshot() {
    const items = invoiceItems.value;
    const totalQty = items.reduce((sum, item) => sum + (item.quantity || 0), 0);
    const itemCodes = items.map((item) => item.item_code);
    const itemGroups = items.map((item) => item.item_group).filter(Boolean);
    const brands = items.map((item) => item.brand).filter(Boolean);
    const itemQuantities = {};
    const itemGroupQuantities = {};
    const brandQuantities = {};
    for (const item of items) {
      const qty = item.quantity || 0;
      if (item.item_code) {
        itemQuantities[item.item_code] = (itemQuantities[item.item_code] || 0) + qty;
      }
      if (item.item_group) {
        itemGroupQuantities[item.item_group] = (itemGroupQuantities[item.item_group] || 0) + qty;
      }
      if (item.brand) {
        brandQuantities[item.brand] = (brandQuantities[item.brand] || 0) + qty;
      }
    }
    return {
      subtotal: subtotal.value,
      itemCount: totalQty,
      itemCodes: [...new Set(itemCodes)],
      itemGroups: [...new Set(itemGroups)],
      brands: [...new Set(brands)],
      // New: quantity maps for accurate min_qty/max_qty validation
      itemQuantities,
      itemGroupQuantities,
      brandQuantities
    };
  }
  function findCartItem(itemCode, uom = null) {
    return invoiceItems.value.find(
      (item) => item.item_code === itemCode && (!uom || item.uom === uom)
    );
  }
  function findItemWithUom(itemCode, targetUom, excludeItem = null) {
    return invoiceItems.value.find(
      (item) => item.item_code === itemCode && item.uom === targetUom && item !== excludeItem
    );
  }
  function removeCartItem(cartItem) {
    const index = invoiceItems.value.indexOf(cartItem);
    if (index > -1) {
      invoiceItems.value.splice(index, 1);
    }
  }
  function mergeItems(sourceItem, targetItem, quantity) {
    targetItem.quantity += quantity;
    recalculateItem(targetItem);
    removeCartItem(sourceItem);
    rebuildIncrementalCache();
    return targetItem.quantity;
  }
  function applyUomChange(cartItem, newUom, qty) {
    return __async(this, null, function* () {
      var _a;
      const uomData = (_a = cartItem.item_uoms) == null ? void 0 : _a.find((u) => u.uom === newUom);
      const conversionFactor = (uomData == null ? void 0 : uomData.conversion_factor) || 1;
      const pricing = yield resolveUomPricing(
        cartItem,
        newUom,
        conversionFactor,
        qty
      );
      cartItem.uom = newUom;
      cartItem.conversion_factor = conversionFactor;
      cartItem.rate = pricing.rate;
      cartItem.price_list_rate = pricing.price_list_rate;
    });
  }
  function changeItemUOM(itemCode, newUom, currentUom = null) {
    return __async(this, null, function* () {
      try {
        const cartItem = findCartItem(itemCode, currentUom);
        if (!cartItem || cartItem.uom === newUom) return;
        const existingItem = findItemWithUom(itemCode, newUom, cartItem);
        if (existingItem) {
          const totalQty = mergeItems(cartItem, existingItem, cartItem.quantity);
          showSuccess(__("Merged into {0} (Total: {1})", [newUom, totalQty]));
          return;
        }
        yield applyUomChange(cartItem, newUom, cartItem.quantity);
        recalculateItem(cartItem);
        rebuildIncrementalCache();
        showSuccess(__("Unit changed to {0}", [newUom]));
      } catch (error) {
        console.error("Error changing UOM:", error);
        showError(__("Failed to update UOM. Please try again."));
      }
    });
  }
  function updateItemDetails(itemCode, updates, currentUom = null) {
    return __async(this, null, function* () {
      var _a, _b;
      try {
        const cartItem = findCartItem(itemCode, currentUom);
        if (!cartItem) {
          throw new Error("Item not found in cart");
        }
        if (updates.uom && updates.uom !== cartItem.uom) {
          const existingItem = findItemWithUom(itemCode, updates.uom, cartItem);
          if (existingItem) {
            const qtyToMerge = (_a = updates.quantity) != null ? _a : cartItem.quantity;
            const totalQty = mergeItems(cartItem, existingItem, qtyToMerge);
            showSuccess(
              __("Merged into {0} (Total: {1})", [updates.uom, totalQty])
            );
            return true;
          }
          try {
            yield applyUomChange(
              cartItem,
              updates.uom,
              (_b = updates.quantity) != null ? _b : cartItem.quantity
            );
          } catch (e) {
            cartItem.uom = updates.uom;
          }
        }
        if (updates.quantity !== void 0) cartItem.quantity = updates.quantity;
        if (updates.warehouse !== void 0)
          cartItem.warehouse = updates.warehouse;
        if (updates.discount_percentage !== void 0)
          cartItem.discount_percentage = updates.discount_percentage;
        if (updates.discount_amount !== void 0)
          cartItem.discount_amount = updates.discount_amount;
        if (updates.rate !== void 0) cartItem.rate = updates.rate;
        if (updates.price_list_rate !== void 0)
          cartItem.price_list_rate = updates.price_list_rate;
        if (updates.serial_no !== void 0)
          cartItem.serial_no = updates.serial_no;
        if (updates.is_rate_manually_edited !== void 0)
          cartItem.is_rate_manually_edited = updates.is_rate_manually_edited;
        if (updates.original_rate !== void 0)
          cartItem.original_rate = updates.original_rate;
        recalculateItem(cartItem);
        rebuildIncrementalCache();
        showSuccess(__("{0} updated", [cartItem.item_name]));
        return true;
      } catch (error) {
        console.error("Error updating item:", error);
        showError(parseError(error) || __("Failed to update item."));
        return false;
      }
    });
  }
  let previousItemCodesHash = "";
  let cachedItemCodes = [];
  let cachedItemGroups = [];
  let cachedBrands = [];
  let cachedItemQuantities = {};
  let cachedItemGroupQuantities = {};
  let cachedBrandQuantities = {};
  function syncOfferSnapshot() {
    if (subtotal.value !== void 0 && invoiceItems.value) {
      const currentHash = invoiceItems.value.map((item) => `${item.item_code}:${item.quantity}`).join(",");
      if (currentHash !== previousItemCodesHash) {
        cachedItemCodes = invoiceItems.value.map((item) => item.item_code);
        cachedItemGroups = [
          ...new Set(
            invoiceItems.value.map((item) => item.item_group).filter(Boolean)
          )
        ];
        cachedBrands = [
          ...new Set(
            invoiceItems.value.map((item) => item.brand).filter(Boolean)
          )
        ];
        cachedItemQuantities = {};
        cachedItemGroupQuantities = {};
        cachedBrandQuantities = {};
        for (const item of invoiceItems.value) {
          const qty = item.quantity || 0;
          if (item.item_code) {
            cachedItemQuantities[item.item_code] = (cachedItemQuantities[item.item_code] || 0) + qty;
          }
          if (item.item_group) {
            cachedItemGroupQuantities[item.item_group] = (cachedItemGroupQuantities[item.item_group] || 0) + qty;
          }
          if (item.brand) {
            cachedBrandQuantities[item.brand] = (cachedBrandQuantities[item.brand] || 0) + qty;
          }
        }
        previousItemCodesHash = currentHash;
      }
      const totalQty = invoiceItems.value.reduce((sum, item) => {
        return sum + (item.quantity || 0);
      }, 0);
      offersStore.updateCartSnapshot({
        subtotal: subtotal.value,
        itemCount: totalQty,
        // Total quantity, not number of line items
        itemCodes: cachedItemCodes,
        itemGroups: cachedItemGroups,
        brands: cachedBrands,
        itemQuantities: cachedItemQuantities,
        itemGroupQuantities: cachedItemGroupQuantities,
        brandQuantities: cachedBrandQuantities
      });
    }
  }
  function processOffersInternal(signal = null, generation = 0, force = false) {
    return __async(this, null, function* () {
      var _a;
      suppressOfferReapply.value = false;
      if (signal == null ? void 0 : signal.aborted) return;
      if (generation > 0 && generation < cartGeneration) {
        return;
      }
      if (!posProfile.value) {
        return;
      }
      const wasFetched = offersStore.hasFetched;
      const profileName = posProfile.value;
      yield offersStore.ensureOffersFetched(profileName);
      if (signal == null ? void 0 : signal.aborted) return;
      const currentHash = generateCartHash();
      const justFetched = !wasFetched && offersStore.hasFetched;
      if (!force && !justFetched && currentHash === offerProcessingState.value.lastCartHash) {
        return;
      }
      syncOfferSnapshot();
      if (offlineState.isOffline) {
        applyOffersOffline();
        offerProcessingState.value.lastCartHash = generateCartHash();
        offerProcessingState.value.lastProcessedAt = Date.now();
        return;
      }
      const currentProfile = {
        customer: ((_a = customer.value) == null ? void 0 : _a.name) || customer.value,
        company: posProfile.value.company,
        selling_price_list: posProfile.value.selling_price_list,
        currency: posProfile.value.currency
      };
      if (appliedOffers.value.length > 0) {
        yield reapplyOffer(currentProfile, signal);
      }
      if (signal == null ? void 0 : signal.aborted) return;
      if (generation > 0 && generation < cartGeneration) {
        return;
      }
      yield autoApplyEligibleOffers(currentProfile, signal);
      offerProcessingState.value.lastCartHash = generateCartHash();
      offerProcessingState.value.lastProcessedAt = Date.now();
      offerProcessingState.value.retryCount = 0;
    });
  }
  function triggerOfferProcessing(force = false) {
    const currentGen = ++cartGeneration;
    offerQueue.enqueue((signal) => __async(this, null, function* () {
      try {
        offerProcessingState.value.isProcessing = true;
        offerProcessingState.value.isAutoProcessing = true;
        offerProcessingState.value.error = null;
        yield processOffersInternal(signal, currentGen, force);
      } catch (error) {
        if (!(signal == null ? void 0 : signal.aborted)) {
          console.error("Error in offer processing:", error);
          offerProcessingState.value.error = error.message;
          offerProcessingState.value.retryCount++;
          if (offerProcessingState.value.retryCount < 3) {
            setTimeout(() => {
              triggerOfferProcessing(true);
            }, 500 * offerProcessingState.value.retryCount);
          }
        }
      } finally {
        offerProcessingState.value.isProcessing = false;
        offerProcessingState.value.isAutoProcessing = false;
      }
    }));
  }
  function forceRefreshOffers() {
    debouncedProcessOffers.cancel();
    offerQueue.cancel();
    offerProcessingState.value.lastCartHash = "";
    offerProcessingState.value.error = null;
    offerProcessingState.value.retryCount = 0;
    suppressOfferReapply.value = false;
    triggerOfferProcessing(true);
  }
  function getDynamicDebounceDelay() {
    const itemCount2 = invoiceItems.value.length;
    if (itemCount2 <= 3) return 100;
    if (itemCount2 <= 10) return 200;
    return 300;
  }
  let debounceTimeoutId = null;
  function debouncedProcessOffers() {
    if (debounceTimeoutId) {
      clearTimeout(debounceTimeoutId);
    }
    debounceTimeoutId = setTimeout(() => {
      debounceTimeoutId = null;
      triggerOfferProcessing(false);
    }, getDynamicDebounceDelay());
  }
  debouncedProcessOffers.cancel = () => {
    if (debounceTimeoutId) {
      clearTimeout(debounceTimeoutId);
      debounceTimeoutId = null;
    }
  };
  debouncedProcessOffers.flush = () => {
    if (debounceTimeoutId) {
      clearTimeout(debounceTimeoutId);
      debounceTimeoutId = null;
      triggerOfferProcessing(false);
    }
  };
  watch(
    [
      // Watch item count (additions/removals)
      () => invoiceItems.value.length,
      // Watch item details (quantity, code, uom changes)
      () => invoiceItems.value.map(
        (item) => `${item.item_code}:${item.quantity}:${item.uom || ""}:${item.discount_percentage || 0}`
      ).join(","),
      // Watch subtotal changes
      subtotal,
      // Watch customer changes (some offers are customer-specific)
      () => {
        var _a;
        return ((_a = customer.value) == null ? void 0 : _a.name) || customer.value;
      }
    ],
    (_newVals, oldVals) => {
      if (!oldVals && invoiceItems.value.length === 0) {
        return;
      }
      debouncedProcessOffers();
    },
    { immediate: true, flush: "post" }
  );
  watch(
    () => appliedOffers.value.length,
    (newLen, oldLen) => {
      if (newLen < oldLen) {
        syncOfferSnapshot();
      }
    }
  );
  return {
    // State
    invoiceItems,
    customer,
    subtotal,
    notIncludedTotal,
    discountEligibleSubtotal,
    totalTax,
    totalDiscount,
    grandTotal,
    posProfile,
    posOpeningShift,
    payments,
    salesTeam,
    additionalDiscount,
    taxInclusive,
    pendingItem,
    pendingItemQty,
    appliedOffers,
    appliedCoupon,
    selectionMode,
    suppressOfferReapply,
    currentDraftId,
    offerProcessingState,
    // Offer processing state for UI feedback
    // Computed
    itemCount,
    isEmpty,
    hasCustomer,
    isProcessingOffers,
    // True when any offer operation is in progress
    isSubmitting,
    // True when invoice submission is in progress (mutex protected)
    // Actions
    addItem,
    removeItem,
    updateItemQuantity,
    clearCart,
    setCustomer,
    setDefaultCustomer,
    setPendingItem,
    clearPendingItem,
    loadTaxRules,
    setTaxInclusive,
    submitInvoice,
    applyDiscountToCart,
    removeDiscountFromCart,
    applyOffer,
    removeOffer,
    reapplyOffer,
    autoApplyEligibleOffers,
    changeItemUOM,
    updateItemDetails,
    getItemDetailsResource,
    resolveUomPricing,
    recalculateItem,
    rebuildIncrementalCache,
    applyOffersResource,
    buildOfferEvaluationPayload,
    formatItemsForSubmission,
    // Sales Order feature
    targetDoctype,
    setTargetDoctype,
    createSalesOrder,
    deliveryDate,
    setDeliveryDate,
    // Party reservation closing
    reservationSalesOrder,
    reservationDeposit,
    loadReservationOrder,
    closeReservation,
    // Loyalty redemption (loyalty_engine)
    loyaltyPointsToRedeem,
    loyaltyCashbackToUse,
    // Card approval codes (Span/DigitalPay) + Tabby payment flag
    cardApprovalCodes,
    isTabbyPayment,
    // Configurable Product Bundle component selections
    bundleSelections,
    setBundleSelection,
    // Active price list + repricing
    activePriceList,
    setActivePriceList,
    ensureDefaultCustomer,
    // Write-off feature
    writeOffAmount,
    setWriteOffAmount,
    // Utilities
    cancelPendingOfferProcessing: () => {
      debouncedProcessOffers.cancel();
      offerQueue.cancel();
    },
    forceRefreshOffers
    // Force reprocess offers from scratch
  };
});
const activeDialogs = ref(/* @__PURE__ */ new Set());
const dialogCounter = ref(0);
function useDialog(dialogId) {
  if (!dialogId) {
    throw new Error("useDialog requires a unique dialogId");
  }
  const isOpen = ref(false);
  const setOpen = (value) => {
    if (value && !isOpen.value) {
      activeDialogs.value.add(dialogId);
      dialogCounter.value++;
    } else if (!value && isOpen.value) {
      activeDialogs.value.delete(dialogId);
      dialogCounter.value--;
    }
    isOpen.value = value;
  };
  const isAnyDialogOpen = computed(() => dialogCounter.value > 0);
  const cleanup = () => {
    if (isOpen.value) {
      activeDialogs.value.delete(dialogId);
      dialogCounter.value--;
    }
  };
  return {
    isOpen: computed({
      get: () => isOpen.value,
      set: setOpen
    }),
    isAnyDialogOpen: readonly(isAnyDialogOpen),
    cleanup,
    // Helper methods
    open: () => setOpen(true),
    close: () => setOpen(false),
    toggle: () => setOpen(!isOpen.value)
  };
}
function useDialogState() {
  const isAnyDialogOpen = computed(() => dialogCounter.value > 0);
  const activeCount = computed(() => activeDialogs.value.size);
  return {
    isAnyDialogOpen: readonly(isAnyDialogOpen),
    activeCount: readonly(activeCount),
    activeDialogIds: readonly(computed(() => Array.from(activeDialogs.value)))
  };
}
const LEFT_PANEL_MIN = 320;
const RIGHT_PANEL_MIN = 360;
const usePOSUIStore = defineStore("posUI", () => {
  const isLoading = ref(true);
  const { isOpen: showPaymentDialog } = useDialog("payment");
  const { isOpen: showCustomerDialog } = useDialog("customer");
  const { isOpen: showSuccessDialog } = useDialog("success");
  const { isOpen: showOpenShiftDialog } = useDialog("openShift");
  const { isOpen: showCloseShiftDialog } = useDialog("closeShift");
  const { isOpen: showDraftDialog } = useDialog("draft");
  const { isOpen: showReturnDialog } = useDialog("return");
  const { isOpen: showCouponDialog } = useDialog("coupon");
  const { isOpen: showOffersDialog } = useDialog("offers");
  const { isOpen: showBatchSerialDialog } = useDialog("batchSerial");
  const { isOpen: showHistoryDialog } = useDialog("history");
  const { isOpen: showOfflineInvoicesDialog } = useDialog("offlineInvoices");
  const { isOpen: showCreateCustomerDialog } = useDialog("createCustomer");
  const { isOpen: showClearCartDialog } = useDialog("clearCart");
  const { isOpen: showLogoutDialog } = useDialog("logout");
  const { isOpen: showItemSelectionDialog } = useDialog("itemSelection");
  const { isOpen: showErrorDialog } = useDialog("invoiceError");
  const { isAnyDialogOpen } = useDialogState();
  const errorDialogTitle = ref("");
  const errorDialogMessage = ref("");
  const errorDetails = ref("");
  const errorType = ref("error");
  const errorRetryAction = ref(null);
  const errorRetryActionData = ref(null);
  const lastInvoiceName = ref("");
  const lastInvoiceTotal = ref(0);
  const lastPaidAmount = ref(0);
  const initialCustomerName = ref("");
  const mobileActiveTab = ref("items");
  const windowWidth = ref(
    typeof window !== "undefined" ? window.innerWidth : 1024
  );
  const leftPanelWidth = ref(800);
  const isResizing = ref(false);
  const isDesktop = computed(() => windowWidth.value >= 1024);
  function setLoading(loading) {
    isLoading.value = loading;
  }
  function setWindowWidth(width) {
    windowWidth.value = width;
  }
  function setMobileTab(tab) {
    mobileActiveTab.value = tab;
  }
  function showError(title, message, details = "", retryAction = null, retryData = null) {
    errorDialogTitle.value = title;
    errorDialogMessage.value = message;
    errorDetails.value = details;
    errorRetryAction.value = retryAction;
    errorRetryActionData.value = retryData;
    showErrorDialog.value = true;
  }
  function clearError() {
    errorDialogTitle.value = "";
    errorDialogMessage.value = "";
    errorDetails.value = "";
    errorRetryAction.value = null;
    errorRetryActionData.value = null;
    showErrorDialog.value = false;
  }
  function showSuccess(invoiceName, total, paidAmount = null) {
    lastInvoiceName.value = invoiceName;
    lastInvoiceTotal.value = total;
    lastPaidAmount.value = paidAmount !== null ? paidAmount : total;
    showSuccessDialog.value = true;
  }
  function setInitialCustomerName(name) {
    initialCustomerName.value = name;
  }
  function clampLeftPanelWidth(width, containerWidth) {
    const safeContainerWidth = Number.isFinite(containerWidth) && containerWidth > 0 ? containerWidth : LEFT_PANEL_MIN + RIGHT_PANEL_MIN;
    const maxWidth = Math.max(
      LEFT_PANEL_MIN,
      safeContainerWidth - RIGHT_PANEL_MIN
    );
    const clampedWidth = Math.min(Math.max(width, LEFT_PANEL_MIN), maxWidth);
    return Number.isFinite(clampedWidth) ? clampedWidth : LEFT_PANEL_MIN;
  }
  function setLeftPanelWidth(width, containerWidth = null) {
    if (containerWidth !== null) {
      const clamped = clampLeftPanelWidth(width, containerWidth);
      leftPanelWidth.value = clamped;
    } else {
      leftPanelWidth.value = width;
    }
  }
  function setResizing(resizing) {
    isResizing.value = resizing;
  }
  function updateLayoutBounds(containerWidth) {
    if (containerWidth) {
      leftPanelWidth.value = clampLeftPanelWidth(
        leftPanelWidth.value,
        containerWidth
      );
    }
  }
  function resetAllDialogs() {
    showPaymentDialog.value = false;
    showCustomerDialog.value = false;
    showSuccessDialog.value = false;
    showOpenShiftDialog.value = false;
    showCloseShiftDialog.value = false;
    showDraftDialog.value = false;
    showReturnDialog.value = false;
    showCouponDialog.value = false;
    showOffersDialog.value = false;
    showBatchSerialDialog.value = false;
    showHistoryDialog.value = false;
    showOfflineInvoicesDialog.value = false;
    showCreateCustomerDialog.value = false;
    showClearCartDialog.value = false;
    showLogoutDialog.value = false;
    showItemSelectionDialog.value = false;
    showErrorDialog.value = false;
    clearError();
  }
  return {
    // State
    isLoading,
    showPaymentDialog,
    showCustomerDialog,
    showSuccessDialog,
    showOpenShiftDialog,
    showCloseShiftDialog,
    showDraftDialog,
    showReturnDialog,
    showCouponDialog,
    showOffersDialog,
    showBatchSerialDialog,
    showHistoryDialog,
    showOfflineInvoicesDialog,
    showCreateCustomerDialog,
    showClearCartDialog,
    showLogoutDialog,
    showItemSelectionDialog,
    showErrorDialog,
    isAnyDialogOpen,
    errorDialogTitle,
    errorDialogMessage,
    errorDetails,
    errorType,
    errorRetryAction,
    errorRetryActionData,
    lastInvoiceName,
    lastInvoiceTotal,
    lastPaidAmount,
    initialCustomerName,
    mobileActiveTab,
    windowWidth,
    leftPanelWidth,
    isResizing,
    // Computed
    isDesktop,
    // Actions
    setLoading,
    setWindowWidth,
    setMobileTab,
    showError,
    clearError,
    showSuccess,
    setInitialCustomerName,
    setLeftPanelWidth,
    setResizing,
    updateLayoutBounds,
    clampLeftPanelWidth,
    resetAllDialogs
  };
});
export {
  QueuedMutex as Q,
  _sfc_main$2 as _,
  usePOSCartStore as a,
  useInvoice as b,
  usePOSSettingsStore as c,
  usePOSOffersStore as d,
  useFormatters as e,
  useDialogState as f,
  getItemStock as g,
  getCachedUnpaidInvoices as h,
  cacheUnpaidInvoices as i,
  getCachedUnpaidSummary as j,
  cacheUnpaidSummary as k,
  cachePaymentMethodsFromServer as l,
  cacheCustomersFromServer as m,
  cacheInvoiceHistory as n,
  usePOSUIStore as o,
  parseError as p,
  _sfc_main as q,
  _sfc_main$1 as r,
  syncOfflineInvoices as s,
  getCachedInvoiceHistory as t,
  useSerialNumberStore as u
};
