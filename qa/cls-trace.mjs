import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

// Diagnostico del CLS intermitente de autor/prensa. Nunca hace fallar el job:
// solo registra, para cada carga, cada layout-shift con su momento, el
// elemento afectado (selector corto + rectangulos antes/despues) y el estado
// de las fuentes en ese instante. Si una carga supera CLS_TRACE_MIN se guarda
// ademas la traza de Playwright (capturas + DOM) para verla en trace.playwright.dev.
const BASE = process.env.IDENTITY_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.CLS_TRACE_DIR || 'artifacts/cls-trace';
const RUNS = Number.parseInt(process.env.CLS_TRACE_RUNS || '5', 10);
const MIN = Number.parseFloat(process.env.CLS_TRACE_MIN || '0.001');
const routes = ['/autor.html', '/prensa.html'];
// Mismas condiciones que Lighthouse movil: 412x823, CPU x4, 4G lenta.
const profiles = [
  { name: 'lh-mobile', width: 412, height: 823, cpu: 4, latency: 150, down: 1.6 * 1024 * 1024 / 8 },
  { name: 'desktop', width: 1350, height: 940, cpu: 1, latency: 40, down: 10 * 1024 * 1024 / 8 },
];

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch();
const report = [];

for (const route of routes) {
  for (const profile of profiles) {
    for (let run = 0; run < RUNS; run += 1) {
      const context = await browser.newContext({ viewport: { width: profile.width, height: profile.height } });
      await context.tracing.start({ screenshots: true, snapshots: true });
      const page = await context.newPage();
      const cdp = await context.newCDPSession(page);
      await cdp.send('Emulation.setCPUThrottlingRate', { rate: profile.cpu });
      await cdp.send('Network.enable');
      await cdp.send('Network.emulateNetworkConditions', {
        offline: false,
        latency: profile.latency,
        downloadThroughput: profile.down,
        uploadThroughput: profile.down / 2,
      });
      await page.addInitScript(() => {
        const short = (node) => {
          if (!node || !node.nodeName) return '?';
          const el = node.nodeType === 1 ? node : node.parentElement;
          if (!el) return node.nodeName;
          const id = el.id ? `#${el.id}` : '';
          const cls = typeof el.className === 'string' && el.className.trim() ? `.${el.className.trim().split(/\s+/).slice(0, 2).join('.')}` : '';
          return `${el.nodeName.toLowerCase()}${id}${cls}`;
        };
        const rect = (r) => r && [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
        window.__clsTrace = { total: 0, shifts: [] };
        let sessionStart = 0;
        let sessionLast = 0;
        let sessionValue = 0;
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.hadRecentInput) continue;
            if (sessionStart === 0 || entry.startTime - sessionLast >= 1000 || entry.startTime - sessionStart >= 5000) {
              sessionStart = entry.startTime;
              sessionValue = entry.value;
            } else {
              sessionValue += entry.value;
            }
            sessionLast = entry.startTime;
            window.__clsTrace.total = Math.max(window.__clsTrace.total, sessionValue);
            window.__clsTrace.shifts.push({
              at: Math.round(entry.startTime),
              value: Number(entry.value.toFixed(5)),
              fontsStatus: document.fonts ? document.fonts.status : 'n/a',
              fontsLoaded: document.fonts ? [...document.fonts].filter((f) => f.status === 'loaded').map((f) => `${f.family} ${f.weight} ${f.style}`) : [],
              sources: entry.sources.map((s) => ({ node: short(s.node), from: rect(s.previousRect), to: rect(s.currentRect) })),
            });
          }
        }).observe({ type: 'layout-shift', buffered: true });
      });
      let result;
      try {
        await page.goto(`${BASE}${route}`, { waitUntil: 'load' });
        await page.evaluate(() => document.fonts && document.fonts.ready);
        await page.waitForTimeout(2500);
        result = await page.evaluate(() => ({
          ...window.__clsTrace,
          total: Number(window.__clsTrace.total.toFixed(5)),
          fontsFinal: document.fonts ? document.fonts.status : 'n/a',
          fcp: Math.round(performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0),
        }));
      } catch (error) {
        result = { error: String(error?.message || error), shifts: [] };
      }
      const entry = { route, profile: profile.name, run, ...result };
      if (!result.error && result.total >= MIN) {
        entry.trace = `${route.replace(/\W+/g, '_')}-${profile.name}-${run}.zip`;
        await context.tracing.stop({ path: path.join(OUT, entry.trace) });
      } else {
        await context.tracing.stop();
      }
      report.push(entry);
      await context.close();
    }
  }
}
await browser.close();

await fs.writeFile(path.join(OUT, 'cls-trace.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8');
const lines = ['| ruta | perfil | cargas | errores | con shift | CLS max |', '|---|---|---|---|---|---|'];
for (const route of routes) {
  for (const profile of profiles) {
    const rows = report.filter((r) => r.route === route && r.profile === profile.name);
    const ok = rows.filter((r) => !r.error);
    const bad = ok.filter((r) => r.total >= MIN);
    lines.push(`| ${route} | ${profile.name} | ${ok.length} | ${rows.length - ok.length} | ${bad.length} | ${Math.max(0, ...ok.map((r) => r.total))} |`);
  }
}
const summary = lines.join('\n');
console.log(summary);
if (process.env.GITHUB_STEP_SUMMARY) {
  await fs.appendFile(process.env.GITHUB_STEP_SUMMARY, `### Traza de CLS (autor/prensa)\n\n${summary}\n`);
}
