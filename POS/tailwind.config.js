import frappeUIPreset from "frappe-ui/tailwind"
import {
	backgroundColor,
	borderColor,
	pageColor,
	surfaceColor,
	surfaceColorPlain,
	textColor,
} from "./tailwind.theme.js"

export default {
	presets: [frappeUIPreset],
	content: [
		"./index.html",
		"./src/**/*.{vue,js,ts,jsx,tsx}",
		"./node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}",
	],
	theme: {
		extend: {
			// The palette utilities the app already uses (bg-gray-100,
			// text-gray-900, border-gray-200, ...) are re-pointed at the CSS
			// variables in src/theme.css. In light mode those variables hold the
			// exact values frappe-ui shipped, so light mode is unchanged; the
			// [data-theme="dark"] block swaps them.
			//
			// Background, text and border are themed as separate scales because
			// one shade name carries two different roles: `bg-blue-600` is a
			// solid button that must stay saturated under `text-white`, while
			// `text-blue-600` is a label that must brighten on a dark surface.
			backgroundColor: {
				...backgroundColor,
				// `bg-white` is a card/panel surface, so it goes dark. `text-white`
				// is deliberately not overridden - it sits on solid coloured
				// buttons and stays white.
				white: surfaceColor,
				// Page/app background, so a root element can opt out of being
				// treated as a raised surface.
				page: pageColor,
			},
			textColor,
			placeholderColor: textColor,
			borderColor,
			divideColor: borderColor,
			ringColor: borderColor,
			// Focus rings punch a hole in the surface behind them, so the offset
			// has to follow the surface rather than stay white.
			ringOffsetColor: {
				DEFAULT: surfaceColorPlain,
				white: surfaceColorPlain,
			},
			// Gradients are used for solid buttons (from-blue-500 to-blue-600),
			// so they follow the background scale.
			gradientColorStops: backgroundColor,
		},
	},
	plugins: [],
}
