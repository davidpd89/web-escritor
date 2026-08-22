import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";

const origin = process.env.QA_ORIGIN || "http://127.0.0.1:4173";
const out = process.env.QA_OUT || "qa-artifacts/assistant";
await fs.mkdir(out, { recursive: true });

const browser = await chromium.launch({ headless: true });
const viewports = [[320,900],[390,900],[768,1000],[1024,900],[1440,1000],[1728,1000],[844,390]];
const shots = new Set(["320x900","390x900","768x1000","1024x900","1440x1000","1728x1000"]);
const failures = [];
const check = (cond, msg) => { if (!cond) failures.push(msg); };

function watchRuntime(page) {
  const state = { pageErrors: [], consoleErrors: [] };
  page.on("pageerror", error => state.pageErrors.push(String(error)));
  page.on("console", msg => {
    if (msg.type() !== "error") return;
    const text = msg.text();
    // The source checkout intentionally has no generated Pagefind bundle;
    // assistant.js catches that import and falls back to the canonical registry.
    if (text.includes("pagefind/pagefind.js") || text.includes("Failed to load resource") && text.includes("404")) return;
    state.consoleErrors.push(text);
  });
  return state;
}

async function waitIdle(page) {
  await page.waitForFunction(() => document.querySelector("[data-assistant-form]")?.getAttribute("aria-busy") !== "true");
}

async function lastAssistantText(page) {
  return page.locator('[data-assistant-log] .assistant-message--assistant .assistant-message__bubble p').last().innerText();
}

for (const [width, height] of viewports) {
  const context = await browser.newContext({ viewport: { width, height }, reducedMotion: "reduce" });
  const page = await context.newPage();
  const runtime = watchRuntime(page);
  let assistantPosts = 0;
  let turnstileRequests = 0;
  const sentinel = "ASSISTANT_LOCAL_QUERY_SENTINEL_582931";
  const leaked = [];

  page.on("request", request => {
    if (request.url().includes("/api/assistant") && request.method() === "POST") assistantPosts += 1;
    if (request.url().includes("challenges.cloudflare.com")) turnstileRequests += 1;
    if ((request.url() + " " + (request.postData() || "")).includes(sentinel)) leaked.push({ url: request.url(), method: request.method() });
  });

  await page.goto(`${origin}/asistente/`, { waitUntil: "networkidle" });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  check(overflow <= 1, `${width}x${height}: horizontal overflow ${overflow}px`);
  check(await page.locator('link[rel="canonical"]').getAttribute("href") === "https://davidportodiaz.com/asistente/", `${width}x${height}: canonical drift`);
  check(await page.locator('meta[name="robots"]').getAttribute("content") === "noindex,nofollow", `${width}x${height}: robots drift`);
  check(await page.locator("[data-assistant-log]").count() === 1, `${width}x${height}: chat log missing`);
  check(await page.locator("[data-assistant-example]").count() === 3, `${width}x${height}: starter count`);
  check(await page.locator('.assistant-message--assistant').count() === 1, `${width}x${height}: welcome message missing`);
  check(await page.locator('.assistant-panel').count() === 0, `${width}x${height}: legacy panel was not upgraded`);

  const textareaFont = await page.locator("[data-assistant-query]").evaluate(el => parseFloat(getComputedStyle(el).fontSize));
  check(textareaFont >= 16, `${width}x${height}: textarea font below 16px (${textareaFont})`);
  const shortTargets = await page.locator("[data-assistant-example], .assistant-composer button").evaluateAll(els => els
    .filter(el => !el.hidden && getComputedStyle(el).display !== "none")
    .filter(el => { const r = el.getBoundingClientRect(); return r.width < 44 || r.height < 44; })
    .map(el => ({ tag: el.tagName, text: el.textContent?.trim(), w: el.getBoundingClientRect().width, h: el.getBoundingClientRect().height })));
  check(shortTargets.length === 0, `${width}x${height}: touch targets below 44px ${JSON.stringify(shortTargets)}`);

  const skipState = await page.locator(".skip-link").evaluate(el => { const r = el.getBoundingClientRect(); return { focused: document.activeElement === el, bottom: r.bottom }; });
  check(!skipState.focused && skipState.bottom <= 0, `${width}x${height}: skip link visible without focus ${JSON.stringify(skipState)}`);
  if (shots.has(`${width}x${height}`)) await page.screenshot({ path: path.join(out, `assistant-${width}x${height}.png`), fullPage: true });

  await page.locator("[data-assistant-query]").fill("x");
  await page.locator("[data-assistant-submit]").click();
  check((await page.locator("[data-assistant-status]").innerText()).includes("concreta"), `${width}x${height}: one-char validation`);

  await page.locator("[data-assistant-query]").evaluate(el => el.removeAttribute("maxlength"));
  await page.locator("[data-assistant-query]").fill("x".repeat(501));
  await page.locator("[data-assistant-submit]").click();
  check((await page.locator("[data-assistant-status]").innerText()).includes("500"), `${width}x${height}: max+1 validation`);

  await page.locator("[data-assistant-query]").fill(sentinel);
  await page.locator("[data-assistant-submit]").click();
  await waitIdle(page);
  check(assistantPosts === 0, `${width}x${height}: remote POST while public kill switch is OFF`);
  check(turnstileRequests === 0, `${width}x${height}: Turnstile loaded while public kill switch is OFF`);
  check(leaked.length === 0, `${width}x${height}: local query leaked to network ${JSON.stringify(leaked)}`);
  check(await page.locator('[data-assistant-log] .assistant-message--user').count() >= 1, `${width}x${height}: user turn not added`);
  check(await page.locator('[data-assistant-log] .assistant-message--assistant').count() >= 2, `${width}x${height}: assistant fallback turn not added`);

  const textResilience = await page.evaluate(() => {
    const el = document.querySelector('[data-assistant-log] .assistant-message__bubble p');
    if (!el) return 999;
    el.textContent = "W".repeat(400);
    return document.documentElement.scrollWidth - document.documentElement.clientWidth;
  });
  check(textResilience <= 1, `${width}x${height}: long-token overflow ${textResilience}px`);
  check(runtime.pageErrors.length === 0, `${width}x${height}: pageerrors ${runtime.pageErrors.join(" | ")}`);
  check(runtime.consoleErrors.length === 0, `${width}x${height}: console errors ${runtime.consoleErrors.join(" | ")}`);
  await context.close();
}

// Local knowledge must answer conversationally without remote network access.
{
  const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
  const page = await context.newPage();
  const runtime = watchRuntime(page);
  let posts = 0;
  page.on("request", request => { if (request.url().includes("/api/assistant") && request.method() === "POST") posts += 1; });
  await page.goto(`${origin}/asistente/`, { waitUntil: "networkidle" });
  await page.locator('[data-assistant-query]').fill('¿De qué trata Las manecillas del recuerdo?');
  await page.locator('[data-assistant-submit]').click();
  await waitIdle(page);
  const text = await lastAssistantText(page);
  check(/reloj|Manuel|memoria|vidas/i.test(text), `local knowledge: unexpected Manecillas answer: ${text}`);
  check(await page.locator('[data-assistant-log] .assistant-message__sources a').count() >= 1, 'local knowledge: canonical source missing');
  check(posts === 0, 'local knowledge: should not POST remotely');
  check(runtime.pageErrors.length === 0, `local knowledge: pageerrors ${runtime.pageErrors.join(" | ")}`);
  await context.close();
}

// Remote mock: explicit public opt-in + server opt-in + Turnstile. Validate
// literal rendering of hostile HTML and strict source validation.
{
  const context = await browser.newContext({ viewport: { width: 390, height: 900 }, reducedMotion: "reduce" });
  const page = await context.newPage();
  const runtime = watchRuntime(page);
  const remoteQuery = "ASSISTANT_REMOTE_QUERY_SENTINEL_482731";
  let posts = 0;
  let invalidMode = false;
  const leaked = [];

  await page.route("**/assets/assistant-config.js", route => route.fulfill({
    status: 200,
    contentType: "application/javascript",
    body: 'export const ASSISTANT_PUBLIC_CONFIG=Object.freeze({protocolVersion:1,remoteEnabled:true,assistantUrl:"/api/assistant",configUrl:"/api/assistant/config",turnstileSiteKey:"",queryMinLength:2,queryMaxLength:500});',
  }));
  await page.route("**/api/assistant/config", route => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ protocol_version: 1, ok: true, enabled: true, turnstile_site_key: "qa-site-key" }) }));
  await page.route("https://challenges.cloudflare.com/turnstile/v0/api.js*", route => route.fulfill({
    status: 200,
    contentType: "application/javascript",
    body: 'globalThis.turnstile={render(_el,opts){globalThis.__assistantTurnstileOpts=opts;return "qa-widget"},execute(){queueMicrotask(()=>globalThis.__assistantTurnstileOpts.callback("qa-token"))},reset(){}};',
  }));
  await page.route("**/api/assistant", async route => {
    if (route.request().method() !== "POST") return route.continue();
    posts += 1;
    const body = route.request().postDataJSON();
    check(body?.protocol_version === 1, "remote mock: protocol mismatch");
    check(body?.turnstile_token === "qa-token", "remote mock: Turnstile token missing");
    if (invalidMode) {
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ protocol_version: 1, ok: true, answer: "Dato [spoof]", abstained: false, sources: [{ id: "author", url: "/autor.html", title: "David Porto Díaz" }] }) });
    }
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ protocol_version: 1, ok: true, answer: '<img src=x onerror="alert(1)"> David es escritor. [author]', abstained: false, sources: [{ id: "author", url: "/autor.html", title: "David Porto Díaz" }] }) });
  });
  page.on("request", request => {
    const combined = request.url() + " " + (request.postData() || "");
    if (combined.includes(remoteQuery) && !(request.url().endsWith("/api/assistant") && request.method() === "POST")) leaked.push({ url: request.url(), method: request.method() });
  });

  await page.goto(`${origin}/asistente/`, { waitUntil: "networkidle" });
  await page.locator("[data-assistant-query]").fill(remoteQuery);
  await page.locator("[data-assistant-submit]").click();
  await waitIdle(page);
  const answerText = await lastAssistantText(page);
  check(answerText.includes('<img src=x onerror="alert(1)">'), "remote mock: HTML payload not rendered as literal text");
  check(await page.locator('[data-assistant-log] img').count() === 0, "remote mock: XSS created an element");
  check(answerText.includes("[1]"), "remote mock: citation marker not numbered");
  check(await page.locator('[data-assistant-log] .assistant-message__sources a').last().getAttribute("href") === "/autor.html", "remote mock: source href drift");
  check(posts === 1, `remote mock: expected exactly one POST, got ${posts}`);
  check(leaked.length === 0, `remote mock: query leaked outside assistant POST ${JSON.stringify(leaked)}`);

  invalidMode = true;
  await page.locator("[data-assistant-query]").fill("respuesta con cita suplantada");
  await page.locator("[data-assistant-submit]").click();
  await waitIdle(page);
  const transcript = await page.locator('[data-assistant-log]').innerText();
  check(!transcript.includes("Dato [spoof]"), "remote invalid payload: spoofed answer rendered");
  check(await page.locator('[data-assistant-log] img').count() === 0, "remote invalid payload: created element");
  check(posts === 2, `remote invalid payload: expected second POST, got ${posts}`);
  check(runtime.pageErrors.length === 0, `remote mock: pageerrors ${runtime.pageErrors.join(" | ")}`);
  check(runtime.consoleErrors.length === 0, `remote mock: console errors ${runtime.consoleErrors.join(" | ")}`);
  await context.close();
}

// Keyboard path and focus: skip link, starter sends directly, then composer focus returns.
{
  const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
  const page = await context.newPage();
  await page.goto(`${origin}/asistente/`);
  await page.keyboard.press("Tab");
  check(await page.locator(".skip-link").evaluate(el => el === document.activeElement), "keyboard: first Tab must focus skip link");
  await page.locator(".skip-link").evaluate(el => new Promise(resolve => {
    const done = () => { el.removeEventListener("transitionend", done); resolve(); };
    el.addEventListener("transitionend", done);
    setTimeout(done, 600);
  }));
  check(await page.locator(".skip-link").evaluate(el => el.getBoundingClientRect().bottom > 0), "keyboard: focused skip link must become visible");
  const starter = page.locator("[data-assistant-example]").first();
  await starter.focus();
  await page.keyboard.press("Enter");
  await waitIdle(page);
  check(await page.locator('[data-assistant-log] .assistant-message--user').count() === 1, "keyboard: starter must send one user turn");
  check(await page.locator("[data-assistant-query]").evaluate(el => el === document.activeElement), "keyboard: focus must return to query");
  await context.close();
}

// 200% zoom-like viewport pressure + WCAG text spacing.
{
  const context = await browser.newContext({ viewport: { width: 640, height: 900 } });
  const page = await context.newPage();
  await page.goto(`${origin}/asistente/`);
  await page.addStyleTag({ content: "*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}" });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  check(overflow <= 1, `text-spacing/200%: overflow ${overflow}px`);
  await context.close();
}

// No-JS keeps the authored fallback, navigation and explicit site-map route.
{
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 900 } });
  const page = await context.newPage();
  await page.goto(`${origin}/asistente/`);
  check(await page.locator('a[href="/mapa-del-sitio/"]').count() > 0, "no-JS: site-map fallback missing");
  check(await page.locator('nav[aria-label="Navegación principal"] a').count() >= 3, "no-JS: primary navigation missing");
  check(await page.locator('[data-assistant-form]').count() === 1, "no-JS: authored search form missing");
  await context.close();
}

await browser.close();
if (failures.length) {
  console.error("Assistant browser QA FAILED:\n- " + failures.join("\n- "));
  process.exit(1);
}
console.log(`assistant-browser: OK (${viewports.length} viewports, 6 screenshots, local knowledge, remote mock, XSS, privacy sentinel, keyboard, no-JS, reduced-motion, text-spacing)`);
