import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";

const origin = process.env.QA_ORIGIN || "http://127.0.0.1:4173";
const out = process.env.QA_OUT || "qa-artifacts/assistant";
const mode = String(process.env.RECOMMENDATION_BENCHMARK_MODE || "report").toLowerCase();
await fs.mkdir(out, { recursive: true });

const CASES = [
  { id: "generic-1", group: "generic", query: "¿Qué me recomiendas leer?", accepted: ["/recomendaciones/"] },
  { id: "generic-2", group: "generic", query: "Quiero ver recomendaciones de lectura", accepted: ["/recomendaciones/"] },
  { id: "generic-3", group: "generic", query: "¿Tienes libros recomendados de fantasía?", accepted: ["/recomendaciones/"] },
  { id: "generic-4", group: "generic", query: "Busco lecturas parecidas a la fantasía juvenil", accepted: ["/recomendaciones/"] },

  { id: "portal-1", group: "portal", query: "Recomiéndame portal fantasy juvenil en español", accepted: ["/recomendaciones/portal-fantasy-espanol/"] },
  { id: "portal-2", group: "portal", query: "¿Qué puedo leer si busco fantasía de portales en español?", accepted: ["/recomendaciones/portal-fantasy-espanol/"] },
  { id: "portal-3", group: "portal", query: "Quiero libros parecidos a Samuel por lo de cruzar a otro mundo", accepted: ["/recomendaciones/portal-fantasy-espanol/"] },
  { id: "portal-4", group: "portal", query: "Dame lecturas de portal fantasy", accepted: ["/recomendaciones/portal-fantasy-espanol/"] },

  { id: "cost-1", group: "magic-cost", query: "Recomiéndame fantasía donde la magia tenga un coste", accepted: ["/recomendaciones/magia-con-coste/"] },
  { id: "cost-2", group: "magic-cost", query: "¿Qué libros tienen magia con consecuencias o precio?", accepted: ["/recomendaciones/magia-con-coste/"] },
  { id: "cost-3", group: "magic-cost", query: "Busco libros donde usar magia cueste algo", accepted: ["/recomendaciones/magia-con-coste/"] },
  { id: "cost-4", group: "magic-cost", query: "Quiero leer fantasía con magia que exige un precio real", accepted: ["/recomendaciones/magia-con-coste/"] },
];

async function waitIdle(page) {
  await page.waitForFunction(() => document.querySelector("[data-assistant-form]")?.getAttribute("aria-busy") !== "true");
}

function normalizeHref(value) {
  if (!value) return "";
  try {
    const url = new URL(value, origin);
    return `${url.pathname}${url.search}${url.hash}`;
  } catch {
    return String(value);
  }
}

const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
const results = [];

for (const item of CASES) {
  const context = await browser.newContext({ viewport: { width: 390, height: 900 }, reducedMotion: "reduce" });
  const page = await context.newPage();
  const assistantPosts = [];
  page.on("request", request => {
    if (request.url().includes("/api/assistant") && request.method() === "POST") assistantPosts.push(request.url());
  });

  await page.goto(`${origin}/asistente/`, { waitUntil: "networkidle" });
  await page.locator("[data-assistant-query]").fill(item.query);
  await page.locator("[data-assistant-submit]").click();
  await waitIdle(page);

  const last = page.locator('[data-assistant-log] .assistant-message--assistant').last();
  const answer = (await last.locator(".assistant-message__bubble p").innerText()).trim();
  const hrefs = (await last.locator(".assistant-message__sources a").evaluateAll(links => links.map(link => link.getAttribute("href")))).map(normalizeHref);
  // Exact-set match, not "one of the accepted hrefs is present": a reply
  // that also drags in an unrelated or wrongly-specialized extra source
  // (e.g. a generic query's answer also citing a specific sub-topic page)
  // must fail here, not slip through because the right link was merely
  // among several returned.
  const uniqueHrefs = [...new Set(hrefs)];
  const matched = uniqueHrefs.length === item.accepted.length
    && item.accepted.every(expected => uniqueHrefs.includes(expected));

  results.push({
    id: item.id,
    group: item.group,
    query: item.query,
    accepted: item.accepted,
    hrefs,
    answer,
    matched,
    remotePosts: assistantPosts.length,
  });
  await context.close();
}

await browser.close();

const groups = Object.fromEntries([...new Set(CASES.map(item => item.group))].map(group => {
  const subset = results.filter(item => item.group === group);
  const matched = subset.filter(item => item.matched).length;
  return [group, { matched, total: subset.length, rate: subset.length ? matched / subset.length : 0 }];
}));
const matched = results.filter(item => item.matched).length;
const remotePosts = results.reduce((total, item) => total + item.remotePosts, 0);
const report = {
  schemaVersion: 1,
  mode,
  total: results.length,
  matched,
  rate: results.length ? matched / results.length : 0,
  remotePosts,
  groups,
  results,
};

const output = path.join(out, "assistant-recommendation-benchmark.json");
await fs.writeFile(output, `${JSON.stringify(report, null, 2)}\n`, "utf8");
console.log(JSON.stringify(report, null, 2));

if (remotePosts !== 0) {
  console.error(`G.1 benchmark leaked ${remotePosts} query/queries to the remote assistant while the public kill switch should be off.`);
  process.exit(1);
}

if (mode === "enforce") {
  const failures = results.filter(item => !item.matched);
  if (failures.length) {
    console.error(`G.1 recommendation benchmark: ${failures.length}/${results.length} routing failures.`);
    process.exit(1);
  }
}
