import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import Pages from "vite-plugin-pages";
import { resolve } from "path";
import tailwindcss from "@tailwindcss/vite";
// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd());
  const apiTarget = env.VITE_BACKEND_URL || "http://localhost:8000";

  return {
    base: "/znkfzs/",
    plugins: [
      tailwindcss(),
      react(),
      Pages({
        dirs: [{ dir: "src/pages", baseRoute: "" }],
        extensions: ["tsx", "jsx"],
        importMode: "sync",
      }),
    ],

    resolve: {
      alias: {
        "@": resolve(__dirname, "src"),
      },
    },
    server: {
      hmr: true,
      watch: {
        usePolling: true,
      },
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
        "/v1": {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/v1/, "/v1"),
        },
      },
    },
  };
});
