import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#0f1419",
        surface: "#1a2332",
        border: "#2d3a4f",
        muted: "#8b949e",
        accent: "#58a6ff",
        success: "#3fb950",
        warning: "#d29922",
        error: "#f85149",
      },
    },
  },
  plugins: [],
};
export default config;
