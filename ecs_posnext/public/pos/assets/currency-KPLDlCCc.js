var __defProp = Object.defineProperty;
var __getOwnPropSymbols = Object.getOwnPropertySymbols;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __propIsEnum = Object.prototype.propertyIsEnumerable;
var __pow = Math.pow;
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
let settings = {
  currency: 2,
  float: 3,
  rounding_method: "Banker's Rounding",
  number_format: "#,###.##"
};
function initPrecision(data) {
  var _a, _b;
  if (!data) return;
  settings = {
    currency: (_a = data.currency) != null ? _a : 2,
    float: (_b = data.float) != null ? _b : 3,
    rounding_method: data.rounding_method || "Banker's Rounding",
    number_format: data.number_format || "#,###.##"
  };
  _formatterCache.clear();
}
function getPrecision() {
  return __spreadValues({}, settings);
}
const DEFAULT_CURRENCY = "USD";
const DEFAULT_LOCALE = "en-US";
const SYMBOLS = {
  USD: "$",
  EUR: "€",
  GBP: "£",
  JPY: "¥",
  CNY: "¥",
  INR: "₹",
  EGP: "E£",
  SAR: "ê",
  AED: "د.إ"
};
const _symbolCache = /* @__PURE__ */ new Map();
function getSymbol(currency) {
  var _a;
  if (!currency) return SYMBOLS[DEFAULT_CURRENCY];
  if (SYMBOLS[currency]) return SYMBOLS[currency];
  if (_symbolCache.has(currency)) return _symbolCache.get(currency);
  try {
    const parts = new Intl.NumberFormat(DEFAULT_LOCALE, {
      style: "currency",
      currency,
      currencyDisplay: "narrowSymbol"
    }).formatToParts(0);
    const symbol = ((_a = parts.find((p) => p.type === "currency")) == null ? void 0 : _a.value) || currency;
    _symbolCache.set(currency, symbol);
    return symbol;
  } catch (e) {
    _symbolCache.set(currency, currency);
    return currency;
  }
}
const _formatterCache = /* @__PURE__ */ new Map();
function getFormatter(precision, locale = DEFAULT_LOCALE) {
  const key = `${locale}:${precision}`;
  if (!_formatterCache.has(key)) {
    _formatterCache.set(
      key,
      new Intl.NumberFormat(locale, {
        minimumFractionDigits: precision,
        maximumFractionDigits: precision
      })
    );
  }
  return _formatterCache.get(key);
}
function formatCurrency(value, currency = DEFAULT_CURRENCY, locale = DEFAULT_LOCALE) {
  if (typeof value !== "number" || Number.isNaN(value)) return "";
  const abs = Math.abs(value);
  const formatted = `${getSymbol(currency)} ${getFormatter(settings.currency, locale).format(abs)}`;
  return value < 0 ? `-${formatted}` : formatted;
}
function formatCurrencyNumber(value, locale = DEFAULT_LOCALE) {
  if (typeof value !== "number" || Number.isNaN(value)) return "0.00";
  return getFormatter(settings.currency, locale).format(value);
}
function formatCurrencyCode(value, currencyCode = DEFAULT_CURRENCY, locale = DEFAULT_LOCALE) {
  if (typeof value !== "number" || Number.isNaN(value)) return "";
  const abs = Math.abs(value);
  const formatted = `${currencyCode} ${getFormatter(settings.currency, locale).format(abs)}`;
  return value < 0 ? `-${formatted}` : formatted;
}
function getCurrencyClass(value) {
  return value < 0 ? "text-red-600" : "text-gray-900";
}
function bankersRound(num, precision) {
  const multiplier = __pow(10, precision);
  let shifted = Number((num * multiplier).toFixed(12));
  if (shifted === 0) return 0;
  const floor = Math.floor(shifted);
  const decimal = shifted - floor;
  const epsilon = __pow(2, Math.log2(Math.abs(shifted)) - 52);
  if (Math.abs(decimal - 0.5) < epsilon) {
    shifted = floor % 2 === 0 ? floor : floor + 1;
  } else {
    shifted = Math.round(shifted);
  }
  return shifted / multiplier;
}
function commercialRound(num, precision) {
  if (num === 0) return 0;
  const epsilon = __pow(2, Math.log2(Math.abs(num)) - 52);
  const adjusted = num + Math.sign(num) * epsilon;
  return Number(adjusted.toFixed(precision));
}
function round(value, precision) {
  if (typeof value !== "number" || Number.isNaN(value)) return 0;
  if (typeof window !== "undefined" && typeof window.flt === "function") {
    return window.flt(value, precision);
  }
  if (settings.rounding_method === "Commercial Rounding") {
    return commercialRound(value, precision);
  }
  return bankersRound(value, precision);
}
function round2(value) {
  return round(value, 2);
}
function round3(value) {
  return round(value, 3);
}
function roundCurrency(value) {
  return round(value, settings.currency);
}
function roundFloat(value) {
  return round(value, settings.float);
}
export {
  DEFAULT_CURRENCY,
  DEFAULT_LOCALE,
  formatCurrency,
  formatCurrencyCode,
  formatCurrencyNumber,
  getCurrencyClass,
  getSymbol as getCurrencySymbol,
  getPrecision,
  initPrecision,
  round2,
  round3,
  roundCurrency,
  roundFloat
};
