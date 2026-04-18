/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{html,js,svelte,ts}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        surface: {
          page: "var(--color-page)",
          container: "var(--color-container)",
          content: "var(--color-content)",
          card: "var(--color-card)",
          "card-hover": "var(--color-card-hover)",
          elevated: "var(--color-elevated)",
          overlay: "var(--color-overlay)",
          input: "var(--color-input)",
          disabled: "var(--color-disabled)",
          track: "var(--color-track)",
        },
        themed: {
          primary: "var(--color-text-primary)",
          secondary: "var(--color-text-secondary)",
          tertiary: "var(--color-text-tertiary)",
          muted: "var(--color-text-muted)",
          faint: "var(--color-text-faint)",
          hover: "var(--color-text-hover)",
          "on-accent": "var(--color-text-on-accent)",
        },
        accent: {
          DEFAULT: "var(--color-accent)",
          hover: "var(--color-accent-hover)",
          text: "var(--color-accent-text)",
          light: "var(--color-accent-light)",
          focus: "var(--color-accent-focus)",
        },
        border: {
          DEFAULT: "var(--color-border)",
          light: "var(--color-border-light)",
        },
        icon: "var(--color-icon)",
        "cancel-hover": "var(--color-cancel-hover)",
        "search-icon": "var(--color-search-icon)",
        tooltip: {
          bg: "var(--color-tooltip-bg)",
          text: "var(--color-tooltip-text)",
        },
      },
      ringOffsetColor: {
        DEFAULT: "var(--color-ring-offset)",
      },
      keyframes: {
        flicker: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.65" },
        },
      },
      animation: {
        flicker: "flicker 0.4s ease-in-out 6",
      },
    },
  },
  plugins: [],
};
