import frappeUIPreset from "frappe-ui/tailwind"
import colors from "tailwindcss/colors"

export default {
	presets: [frappeUIPreset],
	content: [
		"./index.html",
		"./src/**/*.{vue,js,ts,jsx,tsx}",
		"./node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}",
	],
	theme: {
		extend: {
			// frappe-ui's preset ships a limited palette; restore the standard
			// Tailwind families the KDS / Dispatch screens rely on (emerald/neutral/indigo).
			colors: {
				neutral: colors.neutral,
				emerald: colors.emerald,
				indigo: colors.indigo,
				amber: colors.amber,
			},
		},
	},
	plugins: [],
}
