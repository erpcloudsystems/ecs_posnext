/**
 * Frappe's client-side template engine, ported for the POS.
 *
 * Report Print Formats are stored with `print_format_type = "JS"`: their HTML is
 * a template for THIS engine, not for server-side Jinja. Rendering one therefore
 * has to happen in the browser, and it has to use the same compiler the desk
 * uses, or a format that works in the desk would break here.
 *
 * Adapted from frappe/public/js/frappe/microtemplate.js, itself adapted from
 * John Resig's Simple JavaScript Templating (MIT licensed).
 */

import { logger } from "@/utils/logger"

const log = logger.create("microtemplate")

const compiled = new Map()

let sequence = 0
/** Loop variable names must not collide with anything in the template's scope. */
function uniqueName(prefix) {
	sequence += 1
	return `${prefix}${sequence}`
}

function compile(source) {
	if (compiled.has(source)) return compiled.get(source)

	let str = source

	// Jinja-style output tags
	str = str.replace(/{{/g, "{%=").replace(/}}/g, "%}")

	// {% if not test %} --> {% if (!test) { %}
	str = str.replace(/{%\s?if\s?\s?not\s?([^(][^%{]+)\s?%}/g, "{% if (! $1) { %}")

	// {% if test %} --> {% if (test) { %}
	str = str.replace(/{%\s?if\s?([^(][^%{]+)\s?%}/g, "{% if ($1) { %}")

	// {% for item in list %} --> a counted for loop, exposing item._index
	str = str.replace(/{%\s?for\s([a-z._]+)\sin\s([a-z._]+)\s?%}/gi, (match, item, list) => {
		const i = uniqueName("__i")
		const len = uniqueName("__len")
		return `{% for (var ${i}=0, ${len}=${list}.length; ${i}<${len}; ${i}++) { var ${item} = ${list}[${i}]; ${item}._index = ${i}; %}`
	})

	str = str.replace(/{%\s?endif\s?%}/g, "{% }; %}")
	str = str.replace(/{%\s?else\s?%}/g, "{% } else { %}")
	str = str.replace(/{%\s?endfor\s?%}/g, "{% }; %}")

	const body =
		"var _p=[],print=function(){_p.push.apply(_p,arguments)};" +
		"with(obj){\n_p.push('" +
		str
			.replace(/[\r\t\n]/g, " ")
			.split("{%")
			.join("\t")
			.replace(/((^|%})[^\t]*)'/g, "$1\r")
			.replace(/\t=(.*?)%}/g, "',$1,'")
			.split("\t")
			.join("');\n")
			.split("%}")
			.join("\n_p.push('")
			.split("\r")
			.join("\\'") +
		"');}return _p.join('');"

	// biome-ignore lint/security/noGlobalEval: the template engine compiles to a function by design
	const fn = new Function("obj", body)
	compiled.set(source, fn)
	return fn
}

/**
 * Render a Frappe JS template.
 *
 * @param {string} template
 * @param {Object} context - becomes the template's scope via with(){}
 * @returns {string} rendered HTML
 * @throws when the template does not compile or references something absent
 *         from the context — callers are expected to fall back to a plain layout
 */
export function renderTemplate(template, context) {
	try {
		return compile(template)(context)
	} catch (error) {
		log.error("Template render failed:", error)
		throw error
	}
}
