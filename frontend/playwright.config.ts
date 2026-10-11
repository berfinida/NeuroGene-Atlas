import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: process.env.E2E_CORE === "1" ? "./e2e-core" : "./e2e", timeout: 45000, fullyParallel: false, workers: 1,
  reporter: [["list"], ["json", { outputFile: "test-results/results.json" }]],
  use: { baseURL: process.env.E2E_BASE_URL || "http://127.0.0.1:3000", trace: "retain-on-failure", screenshot: "only-on-failure" },
  projects: [
    { name: "desktop", use: { viewport: { width: 1440, height: 1000 } } },
    { name: "mobile", use: { viewport: { width: 390, height: 844 }, isMobile: true } },
  ],
});
