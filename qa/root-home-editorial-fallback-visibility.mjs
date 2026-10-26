import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.BASE_URL || process.env.TEST_BASE_URL || 'http://127.0.0.1:8000';
const browser = await chromium.launch({ headless: true });
try {
  for (const enabled of [false, true]) {
    const context = await browser.newContext({ javaScriptEnabled: enabled });
    const page = await context.newPage();
    const response = await page.goto(new URL('/', base).href, { waitUntil: 'load' });
    assert.equal(response.status(), 200, '/: respuesta HTTP inesperada');
    if (enabled) {
      await page.waitForFunction(() => document.documentElement.dataset.homeEditorialV3 === 'true');
    }
    const state = await page.evaluate(() => {
      const visible = el => {
        const style = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
      };
      const fallback = [...document.querySelectorAll('.river-grid,.promo-band,#faq,#newsletter')];
      const links = [...document.querySelectorAll('main a[href],#faq a[href]')].filter(visible);
      return {
        fallbackVisible: fallback.filter(visible).length,
        links: links.length,
        hydrated: document.documentElement.dataset.homeEditorialV3 === 'true'
      };
    });
    assert.ok(state.links > 0, `/: sin enlaces editoriales visibles con JavaScript ${enabled ? 'activado' : 'desactivado'}`);
    if (!enabled) assert.ok(state.fallbackVisible > 0, '/: contenido editorial de respaldo invisible sin JavaScript');
    if (enabled) assert.ok(state.hydrated, '/: hidratación editorial incompleta');
    await context.close();
  }
  console.log('PASS home editorial fallback');
} finally {
  await browser.close();
}