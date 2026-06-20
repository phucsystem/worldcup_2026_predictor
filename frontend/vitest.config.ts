import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

// Minimal setup: pure data→view helpers only (no DOM/RTL).
export default defineConfig({
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./", import.meta.url)),
    },
  },
  test: {
    include: ["lib/**/*.test.ts"],
    environment: "node",
  },
});
