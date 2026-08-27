import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        sea: {
          50: "var(--sea-50)",
          100: "var(--sea-100)",
          200: "var(--sea-200)",
          300: "var(--sea-300)",
          400: "var(--sea-400)",
          500: "var(--sea-500)",
          600: "var(--sea-600)",
          700: "var(--sea-700)",
          800: "var(--sea-800)",
          900: "var(--sea-900)",
        },
        sand: {
          50: "var(--sand-50)",
          100: "var(--sand-100)",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      keyframes: {
        drift: {
          "0%, 100%": { transform: "translateX(0)" },
          "50%": { transform: "translateX(-24px)" },
        },
        bob: {
          "0%, 100%": { transform: "translateY(0) rotate(-0.4deg)" },
          "50%": { transform: "translateY(-4px) rotate(0.4deg)" },
        },
      },
      animation: {
        "drift-slow": "drift 18s ease-in-out infinite",
        "drift-slower": "drift 26s ease-in-out infinite",
        bob: "bob 7s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
export default config;
