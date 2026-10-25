import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const routes = ['/', '/las-manecillas-del-recuerdo/'];
const browser = await chromium.launch({headless:true});
try {
  const page = await browser.newPage();
  for (const route of routes) {
    const response = await page.goto(BASE + route, {waitUntil:'domcontentloaded'});
    assert.equal(response?.status(), 200, `${route}: HTTP ${response?.status()}`);
    const result = await page.evaluate(() => {
      const bad = [];
      let inspected = 0;
      for (const link of document.querySelectorAll('a[href]')) {
        if (!link.querySelector('img, picture, video')) continue;
        const destination = new URL(link.href, location.href);
        if (destination.origin === location.origin) continue;
        if (link.target.toLowerCase() !== '_blank') continue;
        inspected++;
        const rel = new Set(link.rel.toLowerCase().split(/\s+/));
        if (!rel.has('noopener') && !rel.has('noreferrer')) {
          bad.push({href:link.href, rel:link.rel});
        }
      }
      return {bad, inspected};
    });
    assert.deepEqual(result.bad, [], `${route}: enlaces multimedia externos sin aislamiento explícito: ${JSON.stringify(result.bad)}`);
    console.log(`${route}: ${result.inspected} enlaces multimedia externos inspeccionados`);
  }
} finally {
  await browser.close();
}
console.log('PASS editorial media external link isolation');