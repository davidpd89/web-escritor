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
    const covers = await page.locator('img[src*="portada-las-manecillas-del-recuerdo-"]').evaluateAll(images => images.map(img => ({src:img.getAttribute('src'), alt:img.getAttribute('alt')})));
    assert.ok(covers.length > 0, `${route}: no se encuentra la portada editorial esperada`);
    for (const cover of covers) {
      const alt = (cover.alt || '').trim();
      assert.ok(/manecillas del recuerdo/i.test(alt), `${route}: ${cover.src}: texto alternativo incorrecto: ${JSON.stringify(alt)}`);
      assert.doesNotMatch(alt, /lorem ipsum|placeholder|todo|pendiente|imagen de prueba|sin descripción/i, `${route}: ${cover.src}: texto alternativo provisional: ${alt}`);
    }
  }
} finally {
  await browser.close();
}
console.log('PASS editorial image alt content integrity');