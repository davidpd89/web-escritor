import { chromium } from "playwright";

const origin = process.env.QA_ORIGIN || "http://127.0.0.1:4173";
const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}),
});

const failures = [];
const check = (condition, message) => { if (!condition) failures.push(message); };

try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  const pageErrors = [];
  page.on("pageerror", error => pageErrors.push(String(error)));

  await page.goto(`${origin}/autor.html`, { waitUntil: "networkidle" });
  await page.locator("[data-assistant-search-open]").click();
  const iframe = page.locator(".assistant-widget__frame");
  await iframe.waitFor({ state: "visible" });

  const assistant = page.frameLocator(".assistant-widget__frame");
  await assistant.locator("[data-assistant-query]").fill("¿De qué trata Las manecillas del recuerdo?");
  await assistant.locator("[data-assistant-submit]").click();
  await assistant.locator(".assistant-message__sources a").first().waitFor({ state: "visible" });

  const sourceHref = await assistant.locator(".assistant-message__sources a").first().getAttribute("href");
  check(Boolean(sourceHref), "assistant source href missing");

  await Promise.all([
    page.waitForURL(url => url.pathname !== "/autor.html" && !url.pathname.startsWith("/asistente/embed"), { timeout: 5000 }),
    assistant.locator(".assistant-message__sources a").first().click(),
  ]);

  const finalUrl = new URL(page.url());
  check(!finalUrl.pathname.startsWith("/asistente/embed"), `source remained trapped in iframe: ${finalUrl.pathname}`);
  check(finalUrl.pathname.includes("las-manecillas-del-recuerdo"), `unexpected source destination: ${finalUrl.pathname}`);
  check(pageErrors.length === 0, `page errors: ${pageErrors.join(" | ")}`);

  await context.close();
} finally {
  await browser.close();
}

if (failures.length) {
  console.error("Assistant widget navigation QA FAILED:\n- " + failures.join("\n- "));
  process.exit(1);
}
console.log("assistant-widget-navigation: OK (source link escapes iframe to top-level page)");
