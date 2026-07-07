import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef4ff",
          100: "#dae6ff",
          500: "#3b6cf6",
          600: "#2f57d6",
          700: "#2545ad",
        },
      },
    },
  },
  plugins: [],
};

export default config;
