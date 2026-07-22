var __defProp = Object.defineProperty;
var __defProps = Object.defineProperties;
var __getOwnPropDescs = Object.getOwnPropertyDescriptors;
var __getOwnPropNames = Object.getOwnPropertyNames;
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
var __commonJS = (cb, mod) => function __require() {
  return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
};
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
var require_offline_worker_001 = __commonJS({
  "assets/offline.worker-COSYx7UK.js"(exports) {
    const LOG_LEVELS = {
      DEBUG: 0,
      INFO: 1,
      WARN: 2,
      ERROR: 3,
      NONE: 4
    };
    const COLORS = {
      DEBUG: "\x1B[36m",
      // Cyan
      INFO: "\x1B[34m",
      // Blue
      WARN: "\x1B[33m",
      // Yellow
      ERROR: "\x1B[31m",
      // Red
      SUCCESS: "\x1B[32m",
      // Green
      RESET: "\x1B[0m",
      BOLD: "\x1B[1m",
      DIM: "\x1B[2m"
    };
    class LoggerConfig {
      constructor() {
        this.isDev = false;
        if (typeof window !== "undefined" && typeof localStorage !== "undefined") {
          const manualLevel = localStorage.getItem("POS_LOG_LEVEL");
          const manualEnabled = localStorage.getItem("POS_LOGGING_ENABLED");
          this.currentLevel = manualLevel ? LOG_LEVELS[manualLevel.toUpperCase()] : this.getDefaultLevel();
          this.enabled = manualEnabled !== null ? manualEnabled === "true" : this.isDev;
        } else {
          this.currentLevel = this.getDefaultLevel();
          this.enabled = this.isDev;
        }
        this.enabledNamespaces = /* @__PURE__ */ new Set();
        this.disabledNamespaces = /* @__PURE__ */ new Set();
        this.loadNamespaceConfig();
      }
      getDefaultLevel() {
        return this.isDev ? LOG_LEVELS.DEBUG : LOG_LEVELS.WARN;
      }
      loadNamespaceConfig() {
        if (typeof window === "undefined" || typeof localStorage === "undefined") return;
        try {
          const enabled = localStorage.getItem("POS_LOG_NAMESPACES_ENABLED");
          const disabled = localStorage.getItem("POS_LOG_NAMESPACES_DISABLED");
          if (enabled) {
            enabled.split(",").forEach((ns) => this.enabledNamespaces.add(ns.trim()));
          }
          if (disabled) {
            disabled.split(",").forEach((ns) => this.disabledNamespaces.add(ns.trim()));
          }
        } catch (error) {
        }
      }
      setLevel(level) {
        const levelValue = typeof level === "string" ? LOG_LEVELS[level.toUpperCase()] : level;
        if (levelValue !== void 0) {
          this.currentLevel = levelValue;
          if (typeof localStorage !== "undefined") {
            localStorage.setItem("POS_LOG_LEVEL", Object.keys(LOG_LEVELS)[levelValue]);
          }
        }
      }
      setEnabled(enabled) {
        this.enabled = enabled;
        if (typeof localStorage !== "undefined") {
          localStorage.setItem("POS_LOGGING_ENABLED", enabled.toString());
        }
      }
      enableNamespace(namespace) {
        this.enabledNamespaces.add(namespace);
        this.disabledNamespaces.delete(namespace);
        this.saveNamespaceConfig();
      }
      disableNamespace(namespace) {
        this.disabledNamespaces.add(namespace);
        this.enabledNamespaces.delete(namespace);
        this.saveNamespaceConfig();
      }
      saveNamespaceConfig() {
        if (typeof localStorage === "undefined") return;
        if (this.enabledNamespaces.size > 0) {
          localStorage.setItem("POS_LOG_NAMESPACES_ENABLED", Array.from(this.enabledNamespaces).join(","));
        } else {
          localStorage.removeItem("POS_LOG_NAMESPACES_ENABLED");
        }
        if (this.disabledNamespaces.size > 0) {
          localStorage.setItem("POS_LOG_NAMESPACES_DISABLED", Array.from(this.disabledNamespaces).join(","));
        } else {
          localStorage.removeItem("POS_LOG_NAMESPACES_DISABLED");
        }
      }
      shouldLog(namespace, level) {
        if (!this.enabled) return false;
        if (level < this.currentLevel) return false;
        if (this.enabledNamespaces.size > 0) {
          return this.enabledNamespaces.has(namespace);
        }
        if (this.disabledNamespaces.has(namespace)) {
          return false;
        }
        return true;
      }
    }
    class Logger {
      constructor(namespace, config) {
        this.namespace = namespace;
        this.config = config;
        this.timers = /* @__PURE__ */ new Map();
      }
      /**
       * Format log message with timestamp and namespace
       */
      format(level, message, ...args) {
        const timestamp = (/* @__PURE__ */ new Date()).toISOString().split("T")[1].split(".")[0];
        const levelName = Object.keys(LOG_LEVELS)[level];
        const color = COLORS[levelName] || COLORS.RESET;
        if (typeof window !== "undefined") {
          return [
            `%c[${timestamp}] %c${levelName}%c [${this.namespace}]%c ${message}`,
            "color: gray; font-size: 0.9em",
            `${color}; font-weight: bold`,
            "color: blue; font-weight: bold",
            "color: inherit",
            ...args
          ];
        } else {
          return [
            `${COLORS.DIM}[${timestamp}]${COLORS.RESET} ${color}${COLORS.BOLD}${levelName}${COLORS.RESET} ${COLORS.BOLD}[${this.namespace}]${COLORS.RESET} ${message}`,
            ...args
          ];
        }
      }
      debug(message, ...args) {
        if (this.config.shouldLog(this.namespace, LOG_LEVELS.DEBUG)) {
          console.log(...this.format(LOG_LEVELS.DEBUG, message, ...args));
        }
      }
      info(message, ...args) {
        if (this.config.shouldLog(this.namespace, LOG_LEVELS.INFO)) {
          console.log(...this.format(LOG_LEVELS.INFO, message, ...args));
        }
      }
      warn(message, ...args) {
        if (this.config.shouldLog(this.namespace, LOG_LEVELS.WARN)) {
          console.warn(...this.format(LOG_LEVELS.WARN, message, ...args));
        }
      }
      error(message, ...args) {
        if (this.config.shouldLog(this.namespace, LOG_LEVELS.ERROR)) {
          console.error(...this.format(LOG_LEVELS.ERROR, message, ...args));
        }
      }
      /**
       * Success message (always shown as INFO level)
       */
      success(message, ...args) {
        if (this.config.shouldLog(this.namespace, LOG_LEVELS.INFO)) {
          const formatted = this.format(LOG_LEVELS.INFO, message, ...args);
          if (typeof window !== "undefined") {
            formatted[1] = formatted[1].replace("INFO", "✓ SUCCESS");
            formatted[2] = `${COLORS.SUCCESS}; font-weight: bold`;
          } else {
            formatted[0] = formatted[0].replace("INFO", "✓ SUCCESS");
          }
          console.log(...formatted);
        }
      }
      /**
       * Group related logs
       */
      group(label) {
        if (this.config.shouldLog(this.namespace, LOG_LEVELS.DEBUG)) {
          console.group(`[${this.namespace}] ${label}`);
        }
      }
      groupEnd() {
        if (this.config.shouldLog(this.namespace, LOG_LEVELS.DEBUG)) {
          console.groupEnd();
        }
      }
      /**
       * Table output
       */
      table(data, columns) {
        if (this.config.shouldLog(this.namespace, LOG_LEVELS.DEBUG)) {
          console.table(data, columns);
        }
      }
      /**
       * Performance timing
       */
      time(label) {
        if (this.config.shouldLog(this.namespace, LOG_LEVELS.DEBUG)) {
          this.timers.set(label, performance.now());
        }
      }
      timeEnd(label) {
        if (this.config.shouldLog(this.namespace, LOG_LEVELS.DEBUG)) {
          const startTime = this.timers.get(label);
          if (startTime !== void 0) {
            const duration = performance.now() - startTime;
            this.debug(`⏱️  ${label}: ${duration.toFixed(2)}ms`);
            this.timers.delete(label);
          }
        }
      }
      /**
       * Log with custom color/style
       */
      custom(level, color, message, ...args) {
        if (this.config.shouldLog(this.namespace, level)) {
          const formatted = this.format(level, message, ...args);
          formatted[2] = `color: ${color}; font-weight: bold`;
          console.log(...formatted);
        }
      }
    }
    class LoggerManager {
      constructor() {
        this.config = new LoggerConfig();
        this.loggers = /* @__PURE__ */ new Map();
      }
      /**
       * Create or get a namespaced logger
       */
      create(namespace) {
        if (!this.loggers.has(namespace)) {
          this.loggers.set(namespace, new Logger(namespace, this.config));
        }
        return this.loggers.get(namespace);
      }
      /**
       * Set global log level
       */
      setLevel(level) {
        this.config.setLevel(level);
      }
      /**
       * Enable/disable logging globally
       */
      setEnabled(enabled) {
        this.config.setEnabled(enabled);
      }
      /**
       * Enable specific namespace
       */
      enableNamespace(namespace) {
        this.config.enableNamespace(namespace);
      }
      /**
       * Disable specific namespace
       */
      disableNamespace(namespace) {
        this.config.disableNamespace(namespace);
      }
      /**
       * Get current config
       */
      getConfig() {
        return {
          enabled: this.config.enabled,
          level: Object.keys(LOG_LEVELS)[this.config.currentLevel],
          isDev: this.config.isDev,
          enabledNamespaces: Array.from(this.config.enabledNamespaces),
          disabledNamespaces: Array.from(this.config.disabledNamespaces)
        };
      }
      /**
       * Show help in console
       */
      help() {
        console.log(
          `
%c🔍 POS Logging System Help

%cControl logging globally:%c
  logger.setLevel('DEBUG')    - Set log level (DEBUG, INFO, WARN, ERROR, NONE)
  logger.setEnabled(true)     - Enable/disable all logging
  logger.getConfig()          - View current configuration

%cControl specific modules:%c
  logger.enableNamespace('ItemSearch')   - Only log from ItemSearch
  logger.disableNamespace('Worker')      - Disable Worker logs

%cExamples:%c
  // Create module logger
  const log = logger.create('MyModule')

  // Log at different levels
  log.debug('Detailed info', { data })
  log.info('General info')
  log.warn('Warning message')
  log.error('Error occurred', error)
  log.success('Operation successful!')

  // Performance timing
  log.time('operation')
  // ... do work ...
  log.timeEnd('operation')  // Logs: ⏱️  operation: 42.35ms

  // Group logs
  log.group('Processing items')
  log.info('Item 1')
  log.info('Item 2')
  log.groupEnd()

%cPersistence:%c
  Settings are saved to localStorage and persist across sessions.

%cCurrent Config:%c
  ${JSON.stringify(this.getConfig(), null, 2)}
		`,
          "font-size: 16px; font-weight: bold",
          "font-weight: bold; color: #2196F3",
          "font-weight: normal",
          "font-weight: bold; color: #4CAF50",
          "font-weight: normal",
          "font-weight: bold; color: #FF9800",
          "font-weight: normal",
          "font-weight: bold; color: #9C27B0",
          "font-weight: normal",
          "font-weight: bold; color: #607D8B",
          "font-weight: normal"
        );
      }
    }
    const logger = new LoggerManager();
    if (typeof window !== "undefined") {
      window.posLogger = logger;
    }
    if (logger.config.isDev) {
      const initLog = logger.create("Logger");
      initLog.info("Logger initialized", logger.getConfig());
      initLog.debug("Type posLogger.help() in console for usage guide");
    }
    const generateUUID = () => {
      if (typeof crypto !== "undefined" && crypto.randomUUID) {
        return crypto.randomUUID();
      }
      return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
        const r = Math.random() * 16 | 0;
        const v = c === "x" ? r : r & 3 | 8;
        return v.toString(16);
      });
    };
    const generateOfflineId = () => `pos_offline_${generateUUID()}`;
    const log = logger.create("OfflineWorker");
    const CONFIG = {
      DB_NAME: "ecs_posnext_offline",
      BATCH_SIZE: 500,
      // Optimal for IndexedDB performance
      MAX_RETRY_ATTEMPTS: 3,
      RETRY_DELAY_MS: 1e3,
      QUERY_CACHE_SIZE: 100,
      QUERY_CACHE_TTL_MS: 5 * 60 * 1e3
      // 5 minutes
    };
    let db = null;
    let dbInitialized = false;
    let dbInitPromise = null;
    const queryCache = /* @__PURE__ */ new Map();
    const metrics = /* @__PURE__ */ new Map();
    let circuitBreakerFailures = 0;
    let circuitBreakerOpen = false;
    function initDB() {
      return __async(this, null, function* () {
        if (db && dbInitialized) {
          return db;
        }
        if (dbInitPromise) {
          return dbInitPromise;
        }
        if (circuitBreakerOpen) {
          throw new Error("Circuit breaker open - database unavailable");
        }
        dbInitPromise = (() => __async(this, null, function* () {
          const startTime = performance.now();
          let lastError = null;
          for (let attempt = 1; attempt <= CONFIG.MAX_RETRY_ATTEMPTS; attempt++) {
            try {
              const dexieModule = yield import("./import-wrapper-prod-PyP-HOM1.js");
              const Dexie = dexieModule.default || dexieModule;
              db = new Dexie(CONFIG.DB_NAME);
              yield db.open();
              const tables = db.tables.map((t) => t.name);
              if (tables.length === 0) {
                throw new Error("No tables found in database");
              }
              dbInitialized = true;
              circuitBreakerFailures = 0;
              const duration = Math.round(performance.now() - startTime);
              log.success(`DB initialized in ${duration}ms (attempt ${attempt})`, {
                tables: tables.length
              });
              return db;
            } catch (error) {
              lastError = error;
              log.error(
                `DB init failed (attempt ${attempt}/${CONFIG.MAX_RETRY_ATTEMPTS})`,
                {
                  error: error.message
                }
              );
              if (db) {
                try {
                  yield db.close();
                } catch (closeError) {
                }
                db = null;
                dbInitialized = false;
              }
              if (attempt >= CONFIG.MAX_RETRY_ATTEMPTS) {
                circuitBreakerFailures++;
                if (circuitBreakerFailures >= 5) {
                  circuitBreakerOpen = true;
                  log.error("Circuit breaker opened - DB permanently unavailable");
                }
                throw new Error(
                  `DB init failed after ${attempt} attempts: ${lastError.message}`
                );
              }
              yield new Promise(
                (resolve) => setTimeout(resolve, CONFIG.RETRY_DELAY_MS * Math.pow(2, attempt - 1))
              );
            }
          }
          throw lastError;
        }))();
        try {
          return yield dbInitPromise;
        } finally {
          dbInitPromise = null;
        }
      });
    }
    let serverOnline = true;
    let manualOffline = false;
    let csrfToken = null;
    let stockSyncInterval = null;
    let stockSyncEnabled = false;
    let stockSyncIntervalMs = 6e4;
    let currentWarehouse = null;
    let trackedItemCodes = /* @__PURE__ */ new Set();
    let lastStockSyncTime = null;
    let stockSyncRunning = false;
    function recordMetric(operation, duration, isError = false) {
      if (!metrics.has(operation)) {
        metrics.set(operation, {
          count: 0,
          totalTime: 0,
          errors: 0,
          avgTime: 0,
          minTime: Number.POSITIVE_INFINITY,
          maxTime: 0
        });
      }
      const metric = metrics.get(operation);
      metric.count++;
      metric.totalTime += duration;
      metric.avgTime = Math.round(metric.totalTime / metric.count);
      metric.minTime = Math.min(metric.minTime, duration);
      metric.maxTime = Math.max(metric.maxTime, duration);
      if (isError) {
        metric.errors++;
      }
    }
    function extractBarcodes(item) {
      if (Array.isArray(item.barcodes)) return item.barcodes;
      if (item.barcode) return [item.barcode];
      if (item.item_barcode) {
        if (Array.isArray(item.item_barcode)) {
          return item.item_barcode.map((b) => typeof b === "object" ? b.barcode : b).filter(Boolean);
        }
        return [item.item_barcode];
      }
      return [];
    }
    function chunkArray(array, size) {
      const chunks = [];
      for (let i = 0; i < array.length; i += size) {
        chunks.push(array.slice(i, i + size));
      }
      return chunks;
    }
    function cacheQueryResult(key, value) {
      if (queryCache.size >= CONFIG.QUERY_CACHE_SIZE) {
        const firstKey = queryCache.keys().next().value;
        queryCache.delete(firstKey);
      }
      queryCache.set(key, {
        value,
        timestamp: Date.now()
      });
    }
    function getCachedQuery(key) {
      const entry = queryCache.get(key);
      if (!entry) return null;
      if (Date.now() - entry.timestamp > CONFIG.QUERY_CACHE_TTL_MS) {
        queryCache.delete(key);
        return null;
      }
      return entry.value;
    }
    function invalidateCache(prefix) {
      if (!prefix) {
        queryCache.clear();
        return;
      }
      for (const key of queryCache.keys()) {
        if (key.startsWith(prefix)) {
          queryCache.delete(key);
        }
      }
    }
    function getMetrics() {
      return {
        operations: Object.fromEntries(metrics),
        cache: {
          size: queryCache.size,
          maxSize: CONFIG.QUERY_CACHE_SIZE,
          entries: Array.from(queryCache.keys()).slice(0, 10)
          // Sample
        },
        circuit: {
          open: circuitBreakerOpen,
          failures: circuitBreakerFailures
        },
        db: {
          initialized: dbInitialized
        }
      };
    }
    function pingServer() {
      return __async(this, null, function* () {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 3e3);
          const response = yield fetch("/api/method/ecs_posnext.api.ping", {
            method: "GET",
            signal: controller.signal
          });
          clearTimeout(timeoutId);
          serverOnline = response.ok;
          return serverOnline;
        } catch (error) {
          serverOnline = false;
          return false;
        }
      });
    }
    function isOffline(browserOnline) {
      if (manualOffline) return true;
      return !browserOnline || !serverOnline;
    }
    function getOfflineInvoiceCount() {
      return __async(this, null, function* () {
        try {
          const db2 = yield initDB();
          const tableExists = db2.tables.some(
            (table) => table.name === "invoice_queue"
          );
          if (!tableExists) {
            log.debug("invoice_queue table does not exist yet, returning 0");
            return 0;
          }
          const count = yield db2.table("invoice_queue").filter((invoice) => invoice.synced === false).count();
          return count;
        } catch (error) {
          if (error.name === "NotFoundError" || error.name === "DatabaseClosedError") {
            log.debug("Invoice queue not accessible yet, returning 0");
            return 0;
          }
          log.error("Error getting offline invoice count", error);
          return 0;
        }
      });
    }
    function getOfflineInvoices() {
      return __async(this, null, function* () {
        try {
          const db2 = yield initDB();
          const tableExists = db2.tables.some(
            (table) => table.name === "invoice_queue"
          );
          if (!tableExists) {
            log.debug("invoice_queue table does not exist yet, returning empty array");
            return [];
          }
          const invoices = yield db2.table("invoice_queue").filter((invoice) => invoice.synced === false).toArray();
          return invoices;
        } catch (error) {
          log.error("Error getting offline invoices", error);
          return [];
        }
      });
    }
    function saveOfflineInvoice(invoiceData) {
      return __async(this, null, function* () {
        try {
          const db2 = yield initDB();
          if (!invoiceData.items || invoiceData.items.length === 0) {
            throw new Error("Cannot save empty invoice");
          }
          const offlineId = generateOfflineId();
          invoiceData.offline_id = offlineId;
          const id = yield db2.table("invoice_queue").add({
            offline_id: offlineId,
            data: invoiceData,
            timestamp: Date.now(),
            synced: false,
            retry_count: 0
          });
          log.info(`Invoice saved to offline queue with offline_id: ${offlineId}`);
          return { success: true, id, offline_id: offlineId };
        } catch (error) {
          log.error("Error saving offline invoice", error);
          throw error;
        }
      });
    }
    function searchCachedItems(searchTerm = "", limit = 50, offset = 0) {
      return __async(this, null, function* () {
        const startTime = performance.now();
        const cacheKey = `search:${searchTerm}:${limit}:${offset}`;
        const cached = getCachedQuery(cacheKey);
        if (cached) {
          log.debug("Cache hit for search", { searchTerm });
          return cached;
        }
        try {
          const db2 = yield initDB();
          if (!searchTerm || searchTerm.trim().length === 0) {
            const results2 = yield db2.table("items").orderBy("item_name").filter((item) => !item.disabled && !item.variant_of).offset(offset).limit(limit).toArray();
            cacheQueryResult(cacheKey, results2);
            return results2;
          }
          const term = searchTerm.toLowerCase().trim();
          const searchWords = term.split(/\s+/).filter(Boolean);
          if (searchWords.length === 1) {
            const barcodeResults = yield db2.table("items").where("barcodes").equals(term).filter((item) => !item.disabled).limit(limit).toArray();
            if (barcodeResults.length > 0) {
              cacheQueryResult(cacheKey, barcodeResults);
              recordMetric("searchCachedItems", performance.now() - startTime, false);
              return barcodeResults;
            }
            const codeResults = yield db2.table("items").where("item_code").startsWithIgnoreCase(term).filter((item) => !item.disabled).limit(limit).toArray();
            if (codeResults.length > 0) {
              cacheQueryResult(cacheKey, codeResults);
              recordMetric("searchCachedItems", performance.now() - startTime, false);
              return codeResults;
            }
            const nameResults = yield db2.table("items").where("item_name").startsWithIgnoreCase(term).filter((item) => !item.disabled).limit(limit).toArray();
            if (nameResults.length > 0) {
              cacheQueryResult(cacheKey, nameResults);
              recordMetric("searchCachedItems", performance.now() - startTime, false);
              return nameResults;
            }
          }
          const allItems = yield db2.table("items").filter((item) => !item.disabled).limit(limit * 10).toArray();
          const results = allItems.map((item) => {
            var _a, _b, _c, _d;
            const searchable = `${item.item_code || ""} ${item.item_name || ""} ${item.description || ""}`.toLowerCase();
            if (!searchWords.every((word) => searchable.includes(word))) {
              return null;
            }
            let score = 100;
            if (((_a = item.item_name) == null ? void 0 : _a.toLowerCase()) === term) score = 1e3;
            else if (((_b = item.item_code) == null ? void 0 : _b.toLowerCase()) === term) score = 900;
            else if ((_c = item.item_name) == null ? void 0 : _c.toLowerCase().startsWith(term)) score = 500;
            else if ((_d = item.item_code) == null ? void 0 : _d.toLowerCase().startsWith(term)) score = 400;
            return { item, score };
          }).filter(Boolean).sort((a, b) => b.score - a.score).slice(0, limit).map(({ item }) => item);
          const duration = Math.round(performance.now() - startTime);
          recordMetric("searchCachedItems", duration, false);
          cacheQueryResult(cacheKey, results);
          return results;
        } catch (error) {
          recordMetric("searchCachedItems", performance.now() - startTime, true);
          log.error("Error searching cached items", error);
          return [];
        }
      });
    }
    function searchCachedItemsByGroup() {
      return __async(this, arguments, function* (itemGroups = [], limit = 50, offset = 0) {
        const startTime = performance.now();
        if (!itemGroups || itemGroups.length === 0) {
          return searchCachedItems("", limit, offset);
        }
        const cacheKey = `group:${itemGroups.sort().join(",")}:${limit}:${offset}`;
        const cached = getCachedQuery(cacheKey);
        if (cached) {
          log.debug("Cache hit for group search", { itemGroups });
          return cached;
        }
        try {
          const db2 = yield initDB();
          const allResults = [];
          for (const group of itemGroups) {
            const items = yield db2.table("items").where("item_group").equals(group).filter((item) => !item.disabled && !item.variant_of).toArray();
            allResults.push(...items);
          }
          allResults.sort(
            (a, b) => (a.item_name || "").localeCompare(b.item_name || "")
          );
          const paginated = allResults.slice(offset, offset + limit);
          const duration = Math.round(performance.now() - startTime);
          recordMetric("searchCachedItemsByGroup", duration, false);
          log.debug(
            `Group search: ${paginated.length} items from ${itemGroups.length} groups in ${duration}ms`
          );
          cacheQueryResult(cacheKey, paginated);
          return paginated;
        } catch (error) {
          recordMetric(
            "searchCachedItemsByGroup",
            performance.now() - startTime,
            true
          );
          log.error("Error searching cached items by group", error);
          return [];
        }
      });
    }
    function countCachedItemsByGroup() {
      return __async(this, arguments, function* (itemGroups = []) {
        try {
          const db2 = yield initDB();
          if (!itemGroups || itemGroups.length === 0) {
            return yield db2.table("items").filter((item) => !item.disabled && !item.variant_of).count();
          }
          let total = 0;
          for (const group of itemGroups) {
            total += yield db2.table("items").where("item_group").equals(group).filter((item) => !item.disabled && !item.variant_of).count();
          }
          return total;
        } catch (error) {
          log.error("Error counting cached items by group", error);
          return 0;
        }
      });
    }
    function searchCachedCustomers(searchTerm = "", limit = 20) {
      return __async(this, null, function* () {
        try {
          const db2 = yield initDB();
          const term = searchTerm.toLowerCase();
          if (!term) {
            return limit > 0 ? yield db2.table("customers").limit(limit).toArray() : yield db2.table("customers").toArray();
          }
          const cap = limit && limit > 0 ? limit : 50;
          const table = db2.table("customers");
          const [byName, byMobile, byId] = yield Promise.all([
            table.where("customer_name").startsWithIgnoreCase(term).limit(cap).toArray(),
            table.where("mobile_no").startsWith(term).limit(cap).toArray(),
            table.where("name").startsWithIgnoreCase(term).limit(cap).toArray()
          ]);
          const seen = /* @__PURE__ */ new Set();
          const results = [];
          for (const cust of [...byName, ...byMobile, ...byId]) {
            if (seen.has(cust.name)) continue;
            seen.add(cust.name);
            results.push(cust);
            if (results.length >= cap) break;
          }
          return results;
        } catch (error) {
          log.error("Error searching cached customers", error);
          return [];
        }
      });
    }
    function deleteCustomers(customerNames) {
      return __async(this, null, function* () {
        if (!customerNames || customerNames.length === 0) return true;
        try {
          const db2 = yield initDB();
          yield db2.table("customers").bulkDelete(customerNames);
          log.success(`Deleted ${customerNames.length} customers from cache`);
          return true;
        } catch (error) {
          log.error("Error deleting customers from cache", error);
          throw error;
        }
      });
    }
    function cacheItemsFromServer(items, batchSize) {
      return __async(this, null, function* () {
        if (!items || items.length === 0) {
          return { success: true, count: 0, duration: 0 };
        }
        const startTime = performance.now();
        try {
          const db2 = yield initDB();
          const effectiveBatchSize = batchSize || CONFIG.BATCH_SIZE;
          const batches = chunkArray(items, effectiveBatchSize);
          let totalProcessed = 0;
          yield db2.transaction("rw", "items", "item_prices", "settings", () => __async(this, null, function* () {
            for (const batch of batches) {
              const processedItems = batch.map((item) => __spreadProps(__spreadValues({}, item), {
                barcodes: extractBarcodes(item)
              }));
              yield db2.table("items").bulkPut(processedItems);
              const prices = batch.filter((item) => {
                if (!item.item_code) return false;
                return item.rate || item.price_list_rate;
              }).map((item) => {
                const priceList = item.selling_price_list || item.price_list || "Standard";
                return {
                  price_list: priceList,
                  item_code: item.item_code,
                  rate: item.rate || item.price_list_rate || 0,
                  timestamp: Date.now()
                };
              });
              if (prices.length > 0) {
                try {
                  yield db2.table("item_prices").bulkPut(prices);
                } catch (priceError) {
                  log.error("Failed to cache item prices", {
                    error: priceError.message,
                    batchSize: prices.length,
                    samplePrices: prices.slice(0, 3)
                    // Log first 3 for debugging
                  });
                  let successCount = 0;
                  for (const price of prices) {
                    try {
                      yield db2.table("item_prices").put(price);
                      successCount++;
                    } catch (individualError) {
                      log.warn("Skipping invalid price record", {
                        item_code: price.item_code,
                        price_list: price.price_list,
                        error: individualError.message
                      });
                    }
                  }
                  if (successCount > 0) {
                    log.info(
                      `Recovered ${successCount}/${prices.length} price records`
                    );
                  }
                }
              }
              totalProcessed += batch.length;
            }
            yield db2.table("settings").put({
              key: "items_last_sync",
              value: Date.now()
            });
          }));
          const duration = Math.round(performance.now() - startTime);
          recordMetric("cacheItems", duration, false);
          invalidateCache("search:");
          invalidateCache("items:");
          log.success(`Cached ${totalProcessed} items in ${duration}ms`, {
            batches: batches.length,
            throughput: Math.round(totalProcessed / (duration / 1e3)) + " items/s"
          });
          return { success: true, count: totalProcessed, duration };
        } catch (error) {
          const duration = Math.round(performance.now() - startTime);
          recordMetric("cacheItems", duration, true);
          log.error("Error caching items", {
            error: error.message,
            count: items.length
          });
          throw error;
        }
      });
    }
    function cacheCustomersFromServer(customers) {
      return __async(this, null, function* () {
        if (!customers || customers.length === 0) {
          return { success: true, count: 0, duration: 0 };
        }
        const startTime = performance.now();
        try {
          const db2 = yield initDB();
          yield db2.transaction("rw", "customers", "settings", () => __async(this, null, function* () {
            const batches = chunkArray(customers, CONFIG.BATCH_SIZE);
            for (const batch of batches) {
              yield db2.table("customers").bulkPut(batch);
            }
            yield db2.table("settings").put({
              key: "customers_last_sync",
              value: Date.now()
            });
          }));
          const duration = Math.round(performance.now() - startTime);
          recordMetric("cacheCustomers", duration, false);
          invalidateCache("customers:");
          log.success(`Cached ${customers.length} customers in ${duration}ms`);
          return { success: true, count: customers.length, duration };
        } catch (error) {
          recordMetric("cacheCustomers", performance.now() - startTime, true);
          log.error("Error caching customers", error);
          throw error;
        }
      });
    }
    function clearItemsCache() {
      return __async(this, null, function* () {
        try {
          const db2 = yield initDB();
          yield db2.transaction("rw", "items", "item_prices", "settings", () => __async(this, null, function* () {
            yield db2.table("items").clear();
            yield db2.table("item_prices").clear();
            yield db2.table("settings").put({ key: "items_last_sync", value: null });
          }));
          invalidateCache("items");
          invalidateCache("search");
          log.info("Items cache cleared");
          return { success: true };
        } catch (error) {
          log.error("Error clearing items cache", error);
          throw error;
        }
      });
    }
    function clearCustomersCache() {
      return __async(this, null, function* () {
        try {
          const db2 = yield initDB();
          yield db2.transaction("rw", "customers", "settings", () => __async(this, null, function* () {
            yield db2.table("customers").clear();
            yield db2.table("settings").put({ key: "customers_last_sync", value: null });
          }));
          invalidateCache("customers");
          log.info("Customers cache cleared");
          return { success: true };
        } catch (error) {
          log.error("Error clearing customers cache", error);
          throw error;
        }
      });
    }
    function removeItemsByGroups(itemGroups) {
      return __async(this, null, function* () {
        if (!itemGroups || itemGroups.length === 0) {
          return { success: true, removed: 0, pricesRemoved: 0 };
        }
        const startTime = performance.now();
        try {
          const db2 = yield initDB();
          let totalRemoved = 0;
          let totalPricesRemoved = 0;
          yield db2.transaction("rw", "items", "item_prices", () => __async(this, null, function* () {
            const itemCodesToRemove = [];
            for (const group of itemGroups) {
              const items = yield db2.table("items").where("item_group").equals(group).primaryKeys();
              itemCodesToRemove.push(...items);
              const deleted = yield db2.table("items").where("item_group").equals(group).delete();
              totalRemoved += deleted;
            }
            if (itemCodesToRemove.length > 0) {
              const chunks = chunkArray(itemCodesToRemove, 500);
              for (const chunk of chunks) {
                const pricesDeleted = yield db2.table("item_prices").where("item_code").anyOf(chunk).delete();
                totalPricesRemoved += pricesDeleted;
              }
            }
          }));
          const duration = Math.round(performance.now() - startTime);
          recordMetric("removeItemsByGroups", duration, false);
          invalidateCache("items");
          invalidateCache("search");
          log.success(
            `Removed ${totalRemoved} items, ${totalPricesRemoved} prices in ${duration}ms`,
            {
              groups: itemGroups.length
            }
          );
          return {
            success: true,
            removed: totalRemoved,
            pricesRemoved: totalPricesRemoved,
            duration
          };
        } catch (error) {
          recordMetric("removeItemsByGroups", performance.now() - startTime, true);
          log.error("Error removing items by groups", {
            error: error.message,
            groups: itemGroups
          });
          throw error;
        }
      });
    }
    function cachePaymentMethodsFromServer(paymentMethods) {
      return __async(this, null, function* () {
        try {
          const db2 = yield initDB();
          yield db2.table("payment_methods").bulkPut(paymentMethods);
          yield db2.table("settings").put({
            key: "payment_methods_last_sync",
            value: Date.now()
          });
          return { success: true, count: paymentMethods.length };
        } catch (error) {
          log.error("Error caching payment methods", error);
          throw error;
        }
      });
    }
    function getCachedPaymentMethods(posProfile) {
      return __async(this, null, function* () {
        try {
          const db2 = yield initDB();
          if (!posProfile) {
            return yield db2.table("payment_methods").toArray();
          }
          const methods = yield db2.table("payment_methods").where("pos_profile").equals(posProfile).toArray();
          return methods;
        } catch (error) {
          log.error("Error getting cached payment methods", error);
          return [];
        }
      });
    }
    function cacheOffers(offers, posProfile) {
      return __async(this, null, function* () {
        try {
          if (!Array.isArray(offers) || !posProfile) {
            return { success: false, count: 0 };
          }
          const db2 = yield initDB();
          const offersWithProfile = offers.map((offer) => __spreadProps(__spreadValues({}, offer), {
            pos_profile: posProfile,
            _cached_at: Date.now()
          }));
          yield db2.transaction("rw", db2.table("offers"), () => __async(this, null, function* () {
            yield db2.table("offers").where("pos_profile").equals(posProfile).delete();
            if (offersWithProfile.length > 0) {
              yield db2.table("offers").bulkPut(offersWithProfile);
            }
          }));
          yield db2.table("settings").put({
            key: `offers_last_sync_${posProfile}`,
            value: Date.now()
          });
          log.success(`Cached ${offers.length} offers for profile ${posProfile}`);
          return { success: true, count: offers.length };
        } catch (error) {
          log.error("Error caching offers", error);
          return { success: false, count: 0, error: error.message };
        }
      });
    }
    function getCachedOffers(posProfile) {
      return __async(this, null, function* () {
        try {
          if (!posProfile) {
            return [];
          }
          const db2 = yield initDB();
          const today = (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
          const allOffers = yield db2.table("offers").where("pos_profile").equals(posProfile).toArray();
          const validOffers = allOffers.filter((offer) => {
            if (!offer.valid_upto) return true;
            return offer.valid_upto >= today;
          });
          log.info(
            `Retrieved ${validOffers.length} cached offers for profile ${posProfile}`
          );
          return validOffers;
        } catch (error) {
          log.error("Error getting cached offers", error);
          return [];
        }
      });
    }
    function clearOffersCache(posProfile = null) {
      return __async(this, null, function* () {
        try {
          const db2 = yield initDB();
          if (posProfile) {
            yield db2.table("offers").where("pos_profile").equals(posProfile).delete();
          } else {
            yield db2.table("offers").clear();
          }
          return { success: true };
        } catch (error) {
          log.error("Error clearing offers cache", error);
          return { success: false, error: error.message };
        }
      });
    }
    function isCacheReady() {
      return __async(this, null, function* () {
        try {
          const db2 = yield initDB();
          const itemCount = yield db2.table("items").count();
          return itemCount > 0;
        } catch (error) {
          return false;
        }
      });
    }
    function getCacheStats() {
      return __async(this, null, function* () {
        try {
          const db2 = yield initDB();
          const [
            totalCount,
            variantCount,
            customerCount,
            queuedInvoices,
            lastSyncSetting
          ] = yield Promise.all([
            db2.table("items").count(),
            // Count variant items (have non-empty variant_of field)
            db2.table("items").where("variant_of").notEqual("").count(),
            db2.table("customers").count(),
            getOfflineInvoiceCount(),
            db2.table("settings").get("items_last_sync")
          ]);
          const itemCount = totalCount - variantCount;
          return {
            items: itemCount,
            customers: customerCount,
            queuedInvoices,
            cacheReady: itemCount > 0,
            lastSync: (lastSyncSetting == null ? void 0 : lastSyncSetting.value) || null
          };
        } catch (error) {
          log.error("Error getting cache stats", error);
          return {
            items: 0,
            customers: 0,
            queuedInvoices: 0,
            cacheReady: false,
            lastSync: null
          };
        }
      });
    }
    function deleteOfflineInvoice(id) {
      return __async(this, null, function* () {
        try {
          const db2 = yield initDB();
          yield db2.table("invoice_queue").delete(id);
          return { success: true };
        } catch (error) {
          log.error("Error deleting offline invoice", error);
          throw error;
        }
      });
    }
    function updateStockQuantities(stockUpdates) {
      return __async(this, null, function* () {
        try {
          const db2 = yield initDB();
          if (!stockUpdates || stockUpdates.length === 0) {
            return { success: true, updated: 0 };
          }
          let updatedCount = 0;
          for (const update of stockUpdates) {
            const { item_code, warehouse, actual_qty, stock_qty } = update;
            if (!item_code) {
              continue;
            }
            const item = yield db2.table("items").get(item_code);
            if (!item) {
              continue;
            }
            item.actual_qty = actual_qty !== void 0 ? actual_qty : stock_qty;
            item.stock_qty = stock_qty !== void 0 ? stock_qty : actual_qty;
            item.warehouse = warehouse || item.warehouse;
            yield db2.table("items").put(item);
            updatedCount++;
          }
          if (updatedCount > 0) {
            try {
              yield db2.table("settings").put({
                key: "items_last_sync",
                value: Date.now()
              });
            } catch (error) {
              log.error("Error updating items_last_sync timestamp", error);
            }
          }
          return { success: true, updated: updatedCount };
        } catch (error) {
          log.error("Error updating stock quantities", error);
          throw error;
        }
      });
    }
    function fetchStockFromServer() {
      return __async(this, null, function* () {
        if (!currentWarehouse || trackedItemCodes.size === 0) {
          log.debug("Stock sync skipped: No warehouse or items tracked");
          return [];
        }
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 5e3);
          const itemCodes = Array.from(trackedItemCodes);
          const headers = {
            "Content-Type": "application/json",
            Accept: "application/json"
          };
          if (csrfToken) {
            headers["X-Frappe-CSRF-Token"] = csrfToken;
          }
          const response = yield fetch(
            "/api/method/ecs_posnext.api.items.get_stock_quantities",
            {
              method: "POST",
              headers,
              body: JSON.stringify({
                item_codes: JSON.stringify(itemCodes),
                warehouse: currentWarehouse
              }),
              signal: controller.signal
            }
          );
          clearTimeout(timeoutId);
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
          const data = yield response.json();
          return (data == null ? void 0 : data.message) || data || [];
        } catch (error) {
          if (error.name === "AbortError") {
            log.warn("Stock fetch timeout");
          } else {
            log.error("Error fetching stock from server", error);
          }
          return [];
        }
      });
    }
    function performStockSync() {
      return __async(this, null, function* () {
        if (stockSyncRunning) {
          log.debug("Stock sync already running, skipping");
          return;
        }
        if (!serverOnline || manualOffline) {
          log.debug("Stock sync skipped: Server offline");
          return;
        }
        try {
          stockSyncRunning = true;
          const startTime = Date.now();
          const stockUpdates = yield fetchStockFromServer();
          if (stockUpdates.length > 0) {
            const result = yield updateStockQuantities(stockUpdates);
            lastStockSyncTime = Date.now();
            const duration = lastStockSyncTime - startTime;
            log.success(
              `Stock sync completed: ${result.updated}/${stockUpdates.length} items updated in ${duration}ms`
            );
            self.postMessage({
              type: "STOCK_SYNC_COMPLETE",
              payload: {
                updated: result.updated,
                total: stockUpdates.length,
                duration,
                timestamp: lastStockSyncTime
              }
            });
          } else {
            log.debug("Stock sync: No updates received");
          }
        } catch (error) {
          log.error("Stock sync failed", error);
          self.postMessage({
            type: "STOCK_SYNC_ERROR",
            payload: {
              message: error.message,
              timestamp: Date.now()
            }
          });
        } finally {
          stockSyncRunning = false;
        }
      });
    }
    function startPeriodicStockSync() {
      if (stockSyncInterval) {
        log.debug("Stock sync already running");
        return;
      }
      stockSyncEnabled = true;
      performStockSync().catch((err) => {
        log.error("Initial stock sync failed", err);
      });
      stockSyncInterval = setInterval(() => {
        performStockSync().catch((err) => {
          log.error("Periodic stock sync failed", err);
        });
      }, stockSyncIntervalMs);
      log.success(
        `Periodic stock sync started (interval: ${stockSyncIntervalMs}ms)`
      );
    }
    function stopPeriodicStockSync() {
      if (stockSyncInterval) {
        clearInterval(stockSyncInterval);
        stockSyncInterval = null;
        stockSyncEnabled = false;
        log.info("Periodic stock sync stopped");
      }
    }
    function configureStockSync({ warehouse, itemCodes, intervalMs }) {
      let restartNeeded = false;
      if (warehouse !== void 0) {
        currentWarehouse = warehouse;
        log.debug(`Stock sync warehouse set: ${warehouse}`);
        restartNeeded = true;
      }
      if (itemCodes !== void 0 && Array.isArray(itemCodes)) {
        trackedItemCodes = new Set(itemCodes);
        log.debug(`Stock sync tracking ${itemCodes.length} items`);
        restartNeeded = true;
      }
      if (intervalMs !== void 0 && intervalMs >= 1e4) {
        stockSyncIntervalMs = intervalMs;
        log.debug(`Stock sync interval set: ${intervalMs}ms`);
        restartNeeded = true;
      }
      if (restartNeeded && stockSyncEnabled) {
        stopPeriodicStockSync();
        startPeriodicStockSync();
      }
      return {
        warehouse: currentWarehouse,
        itemCount: trackedItemCodes.size,
        intervalMs: stockSyncIntervalMs,
        enabled: stockSyncEnabled,
        lastSync: lastStockSyncTime
      };
    }
    function getStockSyncStatus() {
      return {
        enabled: stockSyncEnabled,
        warehouse: currentWarehouse,
        itemCount: trackedItemCodes.size,
        intervalMs: stockSyncIntervalMs,
        lastSync: lastStockSyncTime,
        running: stockSyncRunning
      };
    }
    self.onmessage = (event) => __async(exports, null, function* () {
      const { type, payload, id } = event.data;
      try {
        let result;
        switch (type) {
          case "SET_CSRF_TOKEN":
            csrfToken = payload.token;
            result = { success: true };
            break;
          case "PING_SERVER":
            result = yield pingServer();
            break;
          case "CHECK_OFFLINE":
            result = isOffline(payload.browserOnline);
            break;
          case "GET_INVOICE_COUNT":
            result = yield getOfflineInvoiceCount();
            break;
          case "GET_INVOICES":
            result = yield getOfflineInvoices();
            break;
          case "SAVE_INVOICE":
            result = yield saveOfflineInvoice(payload.invoiceData);
            break;
          case "SEARCH_ITEMS":
            result = yield searchCachedItems(
              payload.searchTerm,
              payload.limit,
              payload.offset || 0
            );
            break;
          case "SEARCH_ITEMS_BY_GROUP":
            result = yield searchCachedItemsByGroup(
              payload.itemGroups,
              payload.limit,
              payload.offset || 0
            );
            break;
          case "COUNT_ITEMS_BY_GROUP":
            result = yield countCachedItemsByGroup(payload.itemGroups);
            break;
          case "SEARCH_CUSTOMERS":
            result = yield searchCachedCustomers(payload.searchTerm, payload.limit);
            break;
          case "CACHE_ITEMS":
            result = yield cacheItemsFromServer(payload.items, payload.batchSize);
            break;
          case "CACHE_CUSTOMERS":
            result = yield cacheCustomersFromServer(payload.customers);
            break;
          case "DELETE_CUSTOMERS":
            result = yield deleteCustomers(payload.customerNames);
            break;
          case "CLEAR_ITEMS_CACHE":
            result = yield clearItemsCache();
            break;
          case "CLEAR_CUSTOMERS_CACHE":
            result = yield clearCustomersCache();
            break;
          case "REMOVE_ITEMS_BY_GROUPS":
            result = yield removeItemsByGroups(payload.itemGroups);
            break;
          case "GET_METRICS":
            result = getMetrics();
            break;
          case "CACHE_PAYMENT_METHODS":
            result = yield cachePaymentMethodsFromServer(payload.paymentMethods);
            break;
          case "GET_PAYMENT_METHODS":
            result = yield getCachedPaymentMethods(payload.posProfile);
            break;
          case "IS_CACHE_READY":
            result = yield isCacheReady();
            break;
          case "GET_CACHE_STATS":
            result = yield getCacheStats();
            break;
          case "DELETE_INVOICE":
            result = yield deleteOfflineInvoice(payload.id);
            break;
          case "SET_MANUAL_OFFLINE":
            manualOffline = payload.value;
            self.postMessage({
              type: "SERVER_STATUS_CHANGE",
              payload: {
                serverOnline: serverOnline && !manualOffline,
                manualOffline
              }
            });
            result = { success: true, manualOffline };
            break;
          case "UPDATE_STOCK_QUANTITIES":
            result = yield updateStockQuantities(payload.stockUpdates);
            break;
          case "START_STOCK_SYNC":
            startPeriodicStockSync();
            result = { success: true, status: getStockSyncStatus() };
            break;
          case "STOP_STOCK_SYNC":
            stopPeriodicStockSync();
            result = { success: true, status: getStockSyncStatus() };
            break;
          case "CONFIGURE_STOCK_SYNC":
            result = configureStockSync(payload);
            break;
          case "GET_STOCK_SYNC_STATUS":
            result = getStockSyncStatus();
            break;
          case "TRIGGER_STOCK_SYNC":
            yield performStockSync();
            result = { success: true, status: getStockSyncStatus() };
            break;
          case "CACHE_OFFERS":
            result = yield cacheOffers(payload.offers, payload.posProfile);
            break;
          case "GET_CACHED_OFFERS":
            result = yield getCachedOffers(payload.posProfile);
            break;
          case "CLEAR_OFFERS_CACHE":
            result = yield clearOffersCache(payload.posProfile);
            break;
          default:
            throw new Error(`Unknown message type: ${type}`);
        }
        self.postMessage({
          type: "SUCCESS",
          id,
          payload: result
        });
      } catch (error) {
        self.postMessage({
          type: "ERROR",
          id,
          payload: {
            message: error.message,
            stack: error.stack
          }
        });
      }
    });
    function initialize() {
      return __async(this, null, function* () {
        try {
          yield initDB();
          log.info("Database ready");
          setInterval(() => __async(this, null, function* () {
            const isOnline2 = yield pingServer();
            self.postMessage({
              type: "SERVER_STATUS_CHANGE",
              payload: { serverOnline: isOnline2, manualOffline }
            });
          }), 3e4);
          const isOnline = yield pingServer();
          self.postMessage({
            type: "WORKER_READY",
            payload: { serverOnline: isOnline, manualOffline }
          });
          log.success("Offline worker initialized and ready");
        } catch (error) {
          log.error("Offline worker initialization failed", error);
          self.postMessage({
            type: "ERROR",
            payload: {
              message: `Worker initialization failed: ${error.message}`,
              stack: error.stack
            }
          });
        }
      });
    }
    initialize();
  }
});
export default require_offline_worker_001();
