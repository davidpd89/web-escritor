import assert from 'node:assert/strict';
import {chromium, firefox, webkit} from 'playwright';
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const routes = ['/las-manecillas-del-recuerdo/fragmentos/', '/cuaderno/'];
for (const [name, engine] of Object.entries({chromium, firefox, webkit})) {
  const browser = await engine.launch();
  try {
    for (const route of routes) {
      const page = await browser.newPage({viewport: {width: 800, height: 600}, reducedMotion: 'reduce'});
      await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, r => r.abort());
      try {
        await page.goto(origin + route, {waitUntil: 'domcontentloaded'});
        if (!await page.locator('body[data-reading-progress]').count()) continue;
        assert.equal(await page.locator('.reading-progress').count(), 1, `${name} ${route}`);
        const values = [];
        for (const fraction of [0, 0.5, 1, 0]) {
          await page.evaluate(f => {const max = document.documentElement.scrollHeight - innerHeight; window.scrollTo(0, max * f);}, fraction);
          await page.waitForFunction(f => {const max = document.documentElement.scrollHeight - innerHeight; return Math.abs(scrollY - max * f) < 3;}, fraction);
          await page.waitForTimeout(120);
          values.push(await page.locator('.reading-progress').evaluate(el => parseFloat(el.style.width)));
        }
        assert.ok(values.every(v => Number.isFinite(v) && v >= 0 && v <= 100.1), `${name} ${route}: ${values}`);
        assert.ok(values[0] <= values[1] && values[1] <= values[2], `${name} ${route}: progreso no monótono`);
        assert.ok(values[3] <= 1, `${name} ${route}: progreso no reiniciado`);
      } finally {await page.close();}
    }
  } finally {await browser.close();}
}
console.log('PASS reading progress boundaries');