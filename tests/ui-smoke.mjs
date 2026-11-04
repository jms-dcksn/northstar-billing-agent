import { chromium, expect } from "../ui/node_modules/@playwright/test/index.mjs";

const browser = await chromium.launch({ headless: true });
try {
  for (const scenario of ["eligible", "over_limit", "ambiguous", "timeout_recovered", "timeout_exhausted"]) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const errors = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(`http://127.0.0.1:3000/?scenario=${scenario}&hideToolCalls=true`);
    await page.getByRole("textbox").fill("I was charged twice. Please check the charges.");
    await page.getByRole("button", { name: "Send", exact: true }).click();
    await page.getByRole("button", { name: "Yes, these charges" }).click({ timeout: 30000 });
    if (!["over_limit", "ambiguous"].includes(scenario)) {
      await expect(page.getByRole("button", { name: "Approve refund" })).toBeVisible();
      if (scenario === "eligible") {
        await page.screenshot({ path: "/private/tmp/northstar-refund-card.png", fullPage: true });
      }
      await page.getByRole("button", { name: "Approve refund" }).click();
    }
    const handoff = ["over_limit", "ambiguous", "timeout_exhausted"].includes(scenario);
    await expect(page.getByRole("status").filter({ hasText: handoff ? "Specialist review requested" : "Refund verified" })).toBeVisible();
    if (scenario === "timeout_exhausted") {
      await expect(page.getByRole("status").filter({ hasText: "Refund submission could not be confirmed" })).toBeVisible();
    }
    await page.getByRole("button", { name: "Rate 5 out of 5" }).click();
    await expect(page.getByText("Thanks for your feedback.", { exact: true })).toBeVisible();
    expect(errors).toEqual([]);
    console.log(`${scenario}: charge confirmation, outcome and feedback passed`);
    await page.close();
  }
  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await mobile.goto("http://127.0.0.1:3000");
  expect(await mobile.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  console.log("Mobile: no horizontal overflow");
} finally {
  await browser.close();
}
