import { chromium, expect } from "../ui/node_modules/@playwright/test/index.mjs";
import { mkdir, writeFile } from "node:fs/promises";

// Requires the live backend and frontend; uses Anthropic API credit.
const output = new URL("../.runtime/demo/", import.meta.url);
await mkdir(output, { recursive: true });
const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1280, height: 900 },
  deviceScaleFactor: 1,
  colorScheme: "light",
  recordVideo: { dir: output.pathname, size: { width: 1280, height: 900 } },
});
const page = await context.newPage();
const errors = [];
page.on("pageerror", error => errors.push(error.message));
const pause = () => page.waitForTimeout(2500);
try {
  await page.goto("http://127.0.0.1:3000/?scenario=eligible&hideToolCalls=true");
  await expect(page.getByRole("textbox")).toBeVisible();
  await pause();
  await page.getByRole("textbox").pressSequentially(
    "Hi, I was charged twice for my subscription. Can you help?",
    { delay: 55 },
  );
  await pause();
  await page.getByRole("button", { name: "Send", exact: true }).click();
  const confirm = page.getByRole("button", { name: "Yes, these charges" });
  await expect(confirm).toBeVisible({ timeout: 120000 });
  await page.screenshot({ path: new URL("charges.png", output).pathname });
  await pause();
  await confirm.click();
  const approve = page.getByRole("button", { name: "Approve refund" });
  await expect(approve).toBeVisible({ timeout: 120000 });
  await page.screenshot({ path: new URL("approval.png", output).pathname });
  await pause();
  await approve.click();
  await expect(page.getByRole("status").filter({ hasText: "Refund verified" }))
    .toBeVisible({ timeout: 120000 });
  await page.screenshot({ path: new URL("verified.png", output).pathname });
  const rating = page.getByRole("button", { name: "Rate 5 out of 5" });
  await expect(rating).toBeVisible({ timeout: 120000 });
  await pause();
  await rating.click();
  await expect(rating).toBeHidden({ timeout: 120000 });
  await expect(page.getByRole("textbox")).toBeEnabled({ timeout: 120000 });
  await pause();
  await page.screenshot({ path: new URL("complete.png", output).pathname });
  expect(errors).toEqual([]);
  await writeFile(new URL("result.json", output), JSON.stringify({
    url: page.url(), errors, flow: "live Claude: confirmed, approved, verified, rated",
  }, null, 2));
  console.log("Happy path passed:", page.url());
} finally {
  await context.close();
  console.log("Recording:", await page.video().path());
  await browser.close();
}
