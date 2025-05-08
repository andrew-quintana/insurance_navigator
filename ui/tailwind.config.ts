import type { Config } from "tailwindcss"

const config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
    "*.{js,ts,jsx,tsx,mdx}",
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Custom watercolor-inspired palette based on the banner image
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
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config

export default config
