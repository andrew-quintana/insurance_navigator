/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom Medicare Navigator Colors
        teal: {
          50: "#f0f9f6",
          100: "#d9f0e8",
          200: "#b3e0d1",
          300: "#8ccfb9",
          400: "#5bb99e",
          500: "#3ca188",
          600: "#2a8270",
          700: "#24695c",
          800: "#1f544a",
          900: "#1b463f",
        },
        sky: {
          50: "#f0f9fb",
          100: "#ddf0f7",
          200: "#bce1ef",
          300: "#8ccce3",
          400: "#5bb0d3",
          500: "#3a94c0",
          600: "#2a77a2",
          700: "#246084",
          800: "#1f4d6b",
          900: "#1b405a",
        },
        cream: {
          50: "#fdfaf2",
          100: "#f9f2e0",
          200: "#f3e4c1",
          300: "#ebd29d",
          400: "#e2ba71",
          500: "#d9a14f",
          600: "#c6833a",
          700: "#a46631",
          800: "#85522e",
          900: "#6e4529",
        },
        terracotta: {
          DEFAULT: "#d9674f",
          50: "#fdf4f2",
          100: "#fae7e2",
          200: "#f5cec3",
          300: "#eeab9a",
          400: "#e47f65",
          500: "#d9674f",
          600: "#c44b3a",
          700: "#a33a30",
          800: "#85322c",
          900: "#6e2c27",
        },
      },
    },
  },
  plugins: [],
}

