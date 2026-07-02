import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#7c5c2e",
        surface: "#f8fafc"
      }
    }
  },
  plugins: []
};

export default config;
