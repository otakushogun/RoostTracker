import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "RoostTracker Kerr Lake Alpha",
        short_name: "RoostTracker",
        description: "Explore the Kerr Lake KRAX radar alpha test hour.",
        theme_color: "#082f49",
        background_color: "#f0f9ff",
        display: "standalone",
        start_url: "/",
        icons: [
          {
            src: "/roost-icon.svg",
            sizes: "512x512",
            type: "image/svg+xml",
            purpose: "any",
          },
        ],
      },
      workbox: {
        navigateFallback: "/index.html",
        globPatterns: ["**/*.{html,js,css,svg,woff2}"],
      },
    }),
  ],
  server: {
    host: "0.0.0.0",
  },
});
