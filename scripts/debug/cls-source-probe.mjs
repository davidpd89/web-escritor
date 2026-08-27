// TEMPORARY diagnostic, not part of the QA suite. Captures the exact DOM
// node + before/after rects for every non-input-driven layout-shift on a
// page, under CPU + network throttling matching lhci's collect settings, so
// the specific shifting element can be identified instead of guessing from
// Lighthouse's "cause" heuristic (which lists any resource that finished
// loading in the shift's time window, not necessarily the true cause).
// Deleted once the Cuaderno CLS regression is closed.
import { chromium } from 'playwright';

const url = process.argv[2] || 'http://127.0.0.1:4173/cuaderno/que-es-el-portal-fantasy/';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 412, height: 823 }, deviceScaleFactor: 2.625, isMobile: true, hasTouch: true });
const client = await page.context().newCDPSession(page);
await client.send('Network.enable');
await client.send('Network.emulateNetworkConditions', {
  offline: false,
  latency: 150,
  downloadThroughput: (1.6 * 1024 * 1024) / 8,
  uploadThroughput: (750 * 1024) / 8,
});
await client.send('Emulation.setCPUThrottlingRate', { rate: 4 });

await page.evaluateOnNewDocument?.(() => {}); // no-op, keep API surface explicit
await page.addInitScript(() => {
  window.__shifts = [];
  new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      if (entry.hadRecentInput) continue;
      window.__shifts.push({
        value: entry.value,
        startTime: entry.startTime,
        sources: (entry.sources || []).map((s) => ({
          desc: s.node ? `${s.node.tagName}.${(s.node.className || '').toString().slice(0, 60)}` : null,
          prev: s.previousRect,
          curr: s.currentRect,
        })),
      });
    }
  }).observe({ type: 'layout-shift', buffered: true });
});

await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(1500);
const shifts = await page.evaluate(() => window.__shifts);
console.log(JSON.stringify(shifts, null, 2));
await browser.close();
