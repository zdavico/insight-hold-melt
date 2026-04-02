import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // For local dev, the base is "/". If deploying to GitHub Pages under a
  // subpath like /insight-hold-melt/, change this to that path.
  base: "/insight-hold-melt/",

  server: {
    // Opens the browser automatically when you run `npm run dev`
    open: true,
    port: 5173,
  },
});
