import fs from "fs";
import path from "path";
import { expect, test, type Page } from "@playwright/test";

const ADMIN_EMAIL = process.env.PLAYWRIGHT_ADMIN_EMAIL || "you@example.com";
const ADMIN_PASSWORD = process.env.PLAYWRIGHT_ADMIN_PASSWORD || "StrongPassword123!";
const SOURCE_PDFS = [
  path.resolve(__dirname, "..", "..", "tests", "pdfs", "Dummy App (1)_v8_filled.pdf"),
  path.resolve(__dirname, "..", "..", "tests", "pdfs", "Dummy App (2)_v8_filled.pdf"),
  path.resolve(__dirname, "..", "..", "tests", "pdfs", "Dummy App (3)_v8_filled.pdf"),
];

async function login(page: Page) {
  await page.goto("/admin/login");
  await page.getByLabel("Email").fill(ADMIN_EMAIL);
  await page.getByLabel("Password").fill(ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL("**/admin/reports");
}

test("upload queue advances across multiple pdfs", async ({ page }) => {
  const runId = Date.now();
  const displayIds = SOURCE_PDFS.map((_, index) => `Queue Monitor ${runId}-${index + 1}`);
  const files = SOURCE_PDFS.map((filePath, index) => ({
    name: `${displayIds[index]}.pdf`,
    mimeType: "application/pdf",
    buffer: fs.readFileSync(filePath),
  }));

  await login(page);
  await page.goto("/admin/upload");

  await page.locator('input[type="file"]').setInputFiles(files);
  await page.getByRole("button", { name: "Add to Batch" }).click();

  await expect(page.getByText("3 PDFs added to the upload queue.")).toBeVisible();

  await expect
    .poll(
      async () => {
        const readyResponse = await page.request.get("/api/applications?status=READY");
        expect(readyResponse.ok()).toBeTruthy();
        const readyItems = (await readyResponse.json()) as Array<{ display_id: string }>;
        const readyNames = new Set(readyItems.map((item) => item.display_id));
        return displayIds.filter((displayId) => readyNames.has(displayId)).length;
      },
      {
        timeout: 180_000,
        message: "Expected the multi-PDF upload queue to advance all files into READY.",
      },
    )
    .toBe(displayIds.length);
});
