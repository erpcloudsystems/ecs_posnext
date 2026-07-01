/**
 * POS Awesome — Frappe Desk Language Toggle
 *
 * Injects a floating AR/EN button on the Frappe desk.
 * Uses posawesome.lang (from lang_switcher.js) if available,
 * otherwise falls back to an inline frappe.call.
 *
 * Runs on initial load and re-injects after Frappe SPA navigation
 * (the button is appended to <body>, which survives route changes).
 */

(function () {
    'use strict';

    var FAB_ID    = 'posa-lang-fab';
    var LANG_KEY  = 'posa_ui_lang';
    var RTL_LANGS = ['ar'];

    function getActiveLang() {
        if (frappe && frappe.boot && frappe.boot.lang) {
            return frappe.boot.lang;
        }
        return localStorage.getItem(LANG_KEY) || 'en';
    }

    function doToggle() {
        if (window.posawesome && posawesome.lang) {
            posawesome.lang.toggleLanguage();
            return;
        }
        // Inline fallback (posawesome.lang not yet ready)
        var current = getActiveLang();
        var next    = current === 'ar' ? 'en' : 'ar';
        localStorage.setItem(LANG_KEY, next);
        frappe.call({
            method: 'frappe.client.set_value',
            args: {
                doctype:   'User',
                name:      frappe.session.user,
                fieldname: 'language',
                value:     next,
            },
            callback: function () { location.reload(); },
        });
    }

    function injectFAB() {
        // Don't double-inject
        if (document.getElementById(FAB_ID)) return;

        // Don't inject on login page
        if (!frappe || !frappe.session || !frappe.session.user || frappe.session.user === 'Guest') return;

        var lang  = getActiveLang();
        var isRTL = RTL_LANGS.indexOf(lang) !== -1;
        var label = isRTL ? 'EN' : 'AR';
        var tip   = isRTL ? 'Switch to English' : 'التبديل إلى العربية';

        var fab       = document.createElement('button');
        fab.id        = FAB_ID;
        fab.type      = 'button';
        fab.title     = tip;
        fab.innerText = label;
        fab.setAttribute('aria-label', tip);

        // Position: bottom-right for LTR, bottom-left for RTL
        var sideKey = isRTL ? 'left' : 'right';
        fab.style.cssText =
            'position:fixed;' +
            'bottom:72px;' +
            sideKey + ':18px;' +
            'z-index:9999;' +
            'background:#17223B;' +
            'color:#fff;' +
            'border:none;' +
            'border-radius:50%;' +
            'width:44px;' +
            'height:44px;' +
            'display:flex;' +
            'align-items:center;' +
            'justify-content:center;' +
            'cursor:pointer;' +
            'font-weight:700;' +
            'font-size:12px;' +
            'letter-spacing:0.5px;' +
            'box-shadow:0 2px 10px rgba(0,0,0,0.35);' +
            'transition:background 0.2s,transform 0.15s;' +
            'user-select:none;' +
            'outline:none;';

        fab.addEventListener('mouseenter', function () {
            fab.style.background  = '#2CC8C2';
            fab.style.transform   = 'scale(1.08)';
        });
        fab.addEventListener('mouseleave', function () {
            fab.style.background  = '#17223B';
            fab.style.transform   = 'scale(1)';
        });
        fab.addEventListener('click', function (e) {
            e.preventDefault();
            doToggle();
        });

        document.body.appendChild(fab);
    }

    // ── Injection triggers ──────────────────────────────────────────────────

    // 1. DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectFAB);
    } else {
        injectFAB();
    }

    // 2. After Frappe SPA navigation (page-change, page-load events)
    $(document).on('page-load page-change', function () {
        // Small delay so frappe.session is populated
        setTimeout(injectFAB, 300);
    });

    // 3. After full window load (catches deferred renders)
    window.addEventListener('load', injectFAB);

}());
