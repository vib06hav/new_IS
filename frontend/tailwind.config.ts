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
        surface: "#f5f5f4",
        ink: "#1c1917",
        line: "#d6d3d1",
        muted: "#78716c",
        accent: "#1d4ed8"
      }
    }
  },
  plugins: []
};

export default config;
