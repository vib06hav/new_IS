import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "var(--surface-border)",
        input: "rgba(255, 255, 255, 0.9)",
        ring: "rgba(29, 78, 216, 0.28)",
        background: "rgba(255, 255, 255, 0.94)",
        foreground: "var(--ink)",
        primary: {
          DEFAULT: "var(--accent)",
          foreground: "#ffffff",
        },
        secondary: {
          DEFAULT: "rgba(239, 246, 255, 0.96)",
          foreground: "var(--brand-deep)",
        },
        popover: {
          DEFAULT: "rgba(255, 255, 255, 0.98)",
          foreground: "var(--ink)",
        },
        accent: {
          DEFAULT: "rgba(219, 234, 254, 0.92)",
          foreground: "var(--brand-deep)",
        },
        muted: {
          DEFAULT: "rgba(241, 245, 249, 0.96)",
          foreground: "var(--muted)",
        },
        destructive: {
          DEFAULT: "#dc2626",
          foreground: "#ffffff",
        },
        surface: "#f5f5f4",
        ink: "#1c1917",
        line: "#d6d3d1",
        mutedInk: "#78716c",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "var(--radius-md)",
      },
    },
  },
  plugins: []
};

export default config;
