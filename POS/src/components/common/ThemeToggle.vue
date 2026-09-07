<template>
	<!-- Compact icon button, for the header toolbar -->
	<button
		v-if="variant === 'icon'"
		type="button"
		@click="toggleTheme"
		class="p-1.5 sm:p-2 hover:bg-gray-100 active:bg-gray-200 rounded-lg transition-colors touch-manipulation"
		:title="isDark ? __('Switch to light mode') : __('Switch to dark mode')"
		:aria-label="isDark ? __('Switch to light mode') : __('Switch to dark mode')"
		:aria-pressed="isDark"
	>
		<svg
			v-if="isDark"
			class="w-4 h-4 sm:w-5 sm:h-5 text-amber-500"
			fill="currentColor"
			viewBox="0 0 24 24"
			aria-hidden="true"
		>
			<path
				d="M12 7a5 5 0 100 10 5 5 0 000-10zm0-5a1 1 0 011 1v2a1 1 0 01-2 0V3a1 1 0 011-1zm0 17a1 1 0 011 1v2a1 1 0 01-2 0v-2a1 1 0 011-1zM3 11h2a1 1 0 010 2H3a1 1 0 010-2zm16 0h2a1 1 0 010 2h-2a1 1 0 010-2zM5.64 4.22l1.42 1.42a1 1 0 01-1.42 1.42L4.22 5.64a1 1 0 011.42-1.42zm11.3 11.3l1.42 1.42a1 1 0 01-1.42 1.42l-1.42-1.42a1 1 0 011.42-1.42zm1.42-11.3a1 1 0 010 1.42l-1.42 1.42a1 1 0 01-1.42-1.42l1.42-1.42a1 1 0 011.42 0zM7.06 16.94a1 1 0 010 1.42l-1.42 1.42a1 1 0 01-1.42-1.42l1.42-1.42a1 1 0 011.42 0z"
			/>
		</svg>
		<svg
			v-else
			class="w-4 h-4 sm:w-5 sm:h-5 text-gray-600"
			fill="currentColor"
			viewBox="0 0 24 24"
			aria-hidden="true"
		>
			<path
				d="M12.3 2.04a1 1 0 01.32 1.5A7 7 0 0020.46 14.4a1 1 0 011.5.32 1 1 0 01-.06 1.05A9 9 0 118.23 2.1a1 1 0 011.05-.06z"
			/>
		</svg>
	</button>

	<!-- Full-width row, for the user dropdown on mobile -->
	<button
		v-else
		type="button"
		@click.stop="toggleTheme"
		class="w-full text-start px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3 transition-colors"
		:aria-pressed="isDark"
	>
		<svg
			v-if="isDark"
			class="w-5 h-5 text-amber-500"
			fill="currentColor"
			viewBox="0 0 24 24"
			aria-hidden="true"
		>
			<path
				d="M12 7a5 5 0 100 10 5 5 0 000-10zm0-5a1 1 0 011 1v2a1 1 0 01-2 0V3a1 1 0 011-1zm0 17a1 1 0 011 1v2a1 1 0 01-2 0v-2a1 1 0 011-1zM3 11h2a1 1 0 010 2H3a1 1 0 010-2zm16 0h2a1 1 0 010 2h-2a1 1 0 010-2zM5.64 4.22l1.42 1.42a1 1 0 01-1.42 1.42L4.22 5.64a1 1 0 011.42-1.42zm11.3 11.3l1.42 1.42a1 1 0 01-1.42 1.42l-1.42-1.42a1 1 0 011.42-1.42zm1.42-11.3a1 1 0 010 1.42l-1.42 1.42a1 1 0 01-1.42-1.42l1.42-1.42a1 1 0 011.42 0zM7.06 16.94a1 1 0 010 1.42l-1.42 1.42a1 1 0 01-1.42-1.42l1.42-1.42a1 1 0 011.42 0z"
			/>
		</svg>
		<svg
			v-else
			class="w-5 h-5 text-gray-500"
			fill="currentColor"
			viewBox="0 0 24 24"
			aria-hidden="true"
		>
			<path
				d="M12.3 2.04a1 1 0 01.32 1.5A7 7 0 0020.46 14.4a1 1 0 011.5.32 1 1 0 01-.06 1.05A9 9 0 118.23 2.1a1 1 0 011.05-.06z"
			/>
		</svg>
		<span class="flex-1">{{ __('Dark Mode') }}</span>
		<!-- Switch, so the row reads as a state rather than a navigation item -->
		<span
			class="relative inline-flex h-5 w-9 flex-shrink-0 rounded-full transition-colors"
			:class="isDark ? 'bg-blue-600' : 'bg-gray-300'"
		>
			<span
				class="absolute top-0.5 h-4 w-4 rounded-full bg-[#ffffff] shadow transition-all"
				:class="isDark ? 'start-[1.125rem]' : 'start-0.5'"
			></span>
		</span>
	</button>
</template>

<script setup>
/**
 * @component ThemeToggle
 * @description Switches the POS between light and dark mode.
 *
 * @example
 * <ThemeToggle />              <!-- header icon button -->
 * <ThemeToggle variant="menu" /><!-- row inside the user dropdown -->
 */
import { useTheme } from "@/composables/useTheme"

defineProps({
	variant: {
		type: String,
		default: "icon",
		validator: (value) => ["icon", "menu"].includes(value),
	},
})

const { isDark, toggleTheme } = useTheme()
</script>
