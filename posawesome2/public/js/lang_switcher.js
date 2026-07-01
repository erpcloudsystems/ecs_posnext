/**
 * POS Awesome — Language Switcher Utility
 * Manages AR ↔ EN toggle with User-document persistence.
 *
 * Strategy:
 *  1. Toggle calls frappe.client.set_value to persist language in the User doc.
 *  2. Page is reloaded so Frappe serves the correct translation bundle & direction.
 *  3. localStorage is used only as a fast cache for the toggle-button label before
 *     frappe.boot is ready, and to survive the brief instant between the call and reload.
 */

frappe.provide('posawesome');

posawesome.lang = (function () {
    var LANG_KEY  = 'posa_ui_lang';
    var RTL_LANGS = ['ar'];

    /** Return the active language (server-authoritative after boot, else localStorage). */
    function getCurrentLang() {
        if (frappe && frappe.boot && frappe.boot.lang) {
            return frappe.boot.lang;
        }
        return localStorage.getItem(LANG_KEY) || 'en';
    }

    /** True when the current language is RTL. */
    function isRTL() {
        return RTL_LANGS.indexOf(getCurrentLang()) !== -1;
    }

    /** Returns the language we should switch TO. */
    function getNextLang() {
        return getCurrentLang() === 'ar' ? 'en' : 'ar';
    }

    /**
     * Persist the chosen language in the User document and reload.
     * localStorage is written first so the toggle label is correct
     * immediately if anything reads it before the reload completes.
     */
    function setLanguage(lang) {
        localStorage.setItem(LANG_KEY, lang);

        // Apply direction to <html> immediately so the page doesn't flicker
        // during the (short) time between the call and the reload.
        var dir = RTL_LANGS.indexOf(lang) !== -1 ? 'rtl' : 'ltr';
        document.documentElement.setAttribute('dir', dir);
        document.documentElement.setAttribute('lang', lang);

        frappe.call({
            method: 'frappe.client.set_value',
            args: {
                doctype:   'User',
                name:      frappe.session.user,
                fieldname: 'language',
                value:     lang,
            },
            callback: function () {
                location.reload();
            },
        });
    }

    /** Toggle between AR and EN. */
    function toggleLanguage() {
        setLanguage(getNextLang());
    }

    // Sync localStorage cache with the server-authoritative value on every load.
    // This keeps the cache fresh even when the language was changed from
    // the User profile form directly.
    if (frappe && frappe.boot && frappe.boot.lang) {
        localStorage.setItem(LANG_KEY, frappe.boot.lang);
    }

    return {
        getCurrentLang: getCurrentLang,
        isRTL:          isRTL,
        getNextLang:    getNextLang,
        setLanguage:    setLanguage,
        toggleLanguage: toggleLanguage,
    };
}());
