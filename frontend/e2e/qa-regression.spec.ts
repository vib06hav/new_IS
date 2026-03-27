import path from "path";
import { expect, test, type Page } from "@playwright/test";

const ADMIN_EMAIL = process.env.PLAYWRIGHT_ADMIN_EMAIL || "admin@example.com";
const ADMIN_PASSWORD = process.env.PLAYWRIGHT_ADMIN_PASSWORD || "Admin12345!";
const VALID_PDF_PATH = path.resolve(__dirname, "..", "..", "tests", "pdfs", "Dummy App (1)_v8_filled.pdf");

async function login(page: Page, role: "admin" | "interviewer", email: string, password: string) {
  await page.goto(`/${role}/login`);
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
}

async function latestApplicationId(page: Page, status = "READY") {
  const response = await page.request.get(`/api/applications?status=${status}`);
  expect(response.ok()).toBeTruthy();

  const items = (await response.json()) as Array<{ id: string; created_at: string }>;
  expect(items.length).toBeGreaterThan(0);
  items.sort((left, right) => right.created_at.localeCompare(left.created_at));
  return items[0].id;
}

test.describe.serial("QA regression suite", () => {
  const runId = `${Date.now()}`;
  const interviewerName = `QA Browser ${runId}`;
  const interviewerEmail = `qa.browser.${runId}@example.com`;
  const interviewerPassword = `Password!${runId}`;
  let applicationId = "";

  test("admin can create interviewer and duplicate create shows only the latest error", async ({ page }) => {
    const health = await page.request.get("/api/health");
    expect(health.ok()).toBeTruthy();

    await login(page, "admin", ADMIN_EMAIL, ADMIN_PASSWORD);
    await page.waitForURL("**/admin/reports");
    expect(await page.evaluate(() => window.localStorage.length)).toBe(0);

    await page.goto("/admin/interviewers");
    await page.getByLabel("Name").fill(interviewerName);
    await page.getByLabel("Email").fill(interviewerEmail);
    await page.getByLabel("Password").fill(interviewerPassword);
    await page.getByRole("button", { name: "Create" }).click();

    await expect(page.getByText("Interviewer created.")).toBeVisible();

    await page.getByLabel("Name").fill(interviewerName);
    await page.getByLabel("Email").fill(interviewerEmail);
    await page.getByLabel("Password").fill(interviewerPassword);
    await page.getByRole("button", { name: "Create" }).click();

    await expect(page.getByText("Email already registered")).toBeVisible();
    await expect(page.getByText("Interviewer created.")).toHaveCount(0);
  });

  test("role guards reject wrong-portal logins", async ({ page }) => {
    await login(page, "admin", interviewerEmail, interviewerPassword);
    await expect(page.getByText("This account does not belong in the admin portal.")).toBeVisible();
    expect(await page.evaluate(() => window.localStorage.length)).toBe(0);

    await login(page, "interviewer", ADMIN_EMAIL, ADMIN_PASSWORD);
    await expect(page.getByText("This account does not belong in the interviewer portal.")).toBeVisible();
    expect(await page.evaluate(() => window.localStorage.length)).toBe(0);
  });

  test("invalid upload shows a controlled validation error", async ({ page }) => {
    await login(page, "admin", ADMIN_EMAIL, ADMIN_PASSWORD);
    await page.waitForURL("**/admin/reports");

    await page.goto("/admin/upload");
    await page.locator('input[type="file"]').setInputFiles({
      name: "fake.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("this is not a valid pdf"),
    });
    await page.getByRole("button", { name: "Upload" }).click();

    await expect(page.getByText("Uploaded file is not a valid PDF")).toBeVisible();
  });

  test("admin and interviewer can open the source pdf through the authenticated browser flow", async ({ page }) => {
    await login(page, "admin", ADMIN_EMAIL, ADMIN_PASSWORD);
    await page.waitForURL("**/admin/reports");

    await page.goto("/admin/upload");
    await page.locator('input[type="file"]').setInputFiles(VALID_PDF_PATH);
    await page.getByRole("button", { name: "Upload" }).click();
    await expect(page.getByText(/Upload completed with status/)).toBeVisible({ timeout: 60_000 });

    applicationId = await latestApplicationId(page, "READY");

    await page.goto("/admin/reports");
    const applicationCard = page.locator("section").filter({ hasText: applicationId }).first();
    await applicationCard.getByLabel("Assign interviewer").selectOption({ label: `${interviewerName} (0)` });
    await applicationCard.getByRole("button", { name: "Assign" }).click();
    await expect(page.getByText("Application assigned.")).toBeVisible();

    await page.goto(`/admin/applications/${applicationId}`);
    const adminPdfResponse = page.waitForResponse(
      (response) =>
        response.url().includes(`/api/applications/${applicationId}/source-pdf`) && response.status() === 200,
    );
    await page.getByRole("button", { name: "Open source PDF" }).click();
    const adminPdf = await adminPdfResponse;
    expect(adminPdf.headers()["content-type"] || "").toContain("application/pdf");
    await expect(page.getByText("Failed to open source PDF.")).toHaveCount(0);
    await expect(page.getByText("Not authenticated")).toHaveCount(0);

    await login(page, "interviewer", interviewerEmail, interviewerPassword);
    await page.waitForURL("**/interviewer/dashboard");
    await expect(page.getByText(applicationId)).toBeVisible({ timeout: 20_000 });
    await page.getByRole("link", { name: "Open application" }).first().click();
    await page.waitForURL(`**/interviewer/applications/${applicationId}`);

    const interviewerPdfResponse = page.waitForResponse(
      (response) =>
        response.url().includes(`/api/applications/${applicationId}/source-pdf`) && response.status() === 200,
    );
    await page.getByRole("button", { name: "Open source PDF" }).click();
    const interviewerPdf = await interviewerPdfResponse;
    expect(interviewerPdf.headers()["content-type"] || "").toContain("application/pdf");
    await expect(page.getByText("Failed to open source PDF.")).toHaveCount(0);
    await expect(page.getByText("Not authenticated")).toHaveCount(0);
  });

  test("assigned interviewer deletion is blocked in the ui", async ({ page }) => {
    test.skip(!applicationId, "Assignment flow must run before deletion check.");

    await login(page, "admin", ADMIN_EMAIL, ADMIN_PASSWORD);
    await page.waitForURL("**/admin/reports");
    await page.goto("/admin/interviewers");

    page.once("dialog", (dialog) => dialog.accept());
    const interviewerCard = page.locator("section").filter({ hasText: interviewerEmail }).first();
    await interviewerCard.getByRole("button", { name: "Remove" }).click();

    await expect(page.getByText("Cannot remove interviewer while they still have active assignments")).toBeVisible();
  });
});
