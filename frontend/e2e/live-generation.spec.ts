import fs from "fs";
import path from "path";
import { expect, test, type Page } from "@playwright/test";

const ADMIN_EMAIL = process.env.PLAYWRIGHT_ADMIN_EMAIL || "you@example.com";
const ADMIN_PASSWORD = process.env.PLAYWRIGHT_ADMIN_PASSWORD || "StrongPassword123!";
const SOURCE_PDF = path.resolve(__dirname, "..", "..", "tests", "pdfs", "Dummy App (1)_v8_filled.pdf");

test.setTimeout(900_000);

async function login(page: Page) {
  await page.goto("/admin/login");
  await page.getByLabel("Email").fill(ADMIN_EMAIL);
  await page.getByLabel("Password").fill(ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL("**/admin/reports");
}

test("live upload and report generation completes through the browser", async ({ page }) => {
  const runId = Date.now();
  const displayId = `Live Generation ${runId}`;
  const uploadName = `${displayId}.pdf`;

  async function fetchApplication() {
    const response = await page.request.get("/api/applications");
    expect(response.ok()).toBeTruthy();
    const applications = (await response.json()) as Array<{
      id: string;
      display_id: string;
      status: string;
    }>;
    return applications.find((item) => item.display_id === displayId) ?? null;
  }

  await login(page);
  await page.goto("/admin/upload");

  await page.locator('input[type="file"]').setInputFiles({
    name: uploadName,
    mimeType: "application/pdf",
    buffer: fs.readFileSync(SOURCE_PDF),
  });
  await page.getByRole("button", { name: "Add to Batch" }).click();

  await expect(page.getByText("1 PDF added to the upload queue.")).toBeVisible();

  await expect
    .poll(
      async () => (await fetchApplication())?.status ?? null,
      {
        timeout: 300_000,
        message: "Expected uploaded PDF to reach PROCESSED, READY, or FAILED.",
      },
    )
    .toMatch(/^(PROCESSED|READY|FAILED)$/);

  const processedApplication = await fetchApplication();
  expect(processedApplication).not.toBeNull();
  expect(processedApplication?.status).not.toBe("FAILED");
  expect(["PROCESSED", "READY"]).toContain(processedApplication?.status ?? "");

  if (processedApplication?.status === "PROCESSED") {
    await page.goto("/admin/reports");
    const reportCard = page.locator("article").filter({ hasText: displayId }).first();
    await expect(reportCard).toBeVisible({ timeout: 60_000 });
    await reportCard.getByRole("button", { name: "Generate report" }).click();
    await expect
      .poll(
        async () => (await fetchApplication())?.status ?? null,
        {
          timeout: 600_000,
          message: "Expected Generate report to move the application to READY or FAILED.",
        },
      )
      .toMatch(/^(READY|FAILED)$/);
  }

  await expect
    .poll(
      async () => (await fetchApplication())?.status ?? null,
      {
        timeout: 300_000,
        message: "Expected generated application to reach READY.",
      },
    )
    .toBe("READY");

  const readyApplication = await fetchApplication();
  expect(readyApplication).not.toBeNull();
  await page.goto(`/admin/applications/${readyApplication!.id}`);
  await expect(page.getByText(displayId)).toBeVisible();
  await expect(page.getByRole("button", { name: /Focus Areas/i })).toBeVisible({ timeout: 60_000 });
  await expect(page.getByRole("button", { name: /Questions/i })).toBeVisible({ timeout: 60_000 });
});
