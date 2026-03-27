import { defineConfig, devices } from "@playwright/test";

const port = Number(process.env.PLAYWRIGHT_FRONTEND_PORT || "3003");
const backendUrl =
  process.env.PLAYWRIGHT_BACKEND_URL || process.env.BACKEND_API_URL || "http://127.0.0.1:8000";
const baseURL = process.env.PLAYWRIGHT_BASE_URL || `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 120_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: `npm run dev:clean -- --port ${port}`,
    url: baseURL,
    reuseExistingServer: true,
    timeout: 120_000,
    env: {
      BACKEND_API_URL: backendUrl,
    },
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
