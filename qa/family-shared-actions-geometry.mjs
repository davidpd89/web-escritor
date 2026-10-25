import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN;
assert.ok(origin, 'QA_ORIGIN obligatorio');
const browser = await chromium.launch({ headless: true });
const routes = ['/', '/libros/', '/404.html'];
try {
  for (const width of [320, 390, 768, 1280]) {
    const context = await browser.newContext({ viewport: { width, height: 850 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    try {
      let total = 0;
      for (const route of routes) {
        const response = await page.goto(new URL(route, origin).href, { waitUntil: 'domcontentloaded' });
        assert.equal(response?.status(), 200, `${route}: HTTP inesperado`);
        await page.locator('body').waitFor({ state: 'visible' });
        const samples = await page.locator('.primary-action, .form-submit, .button').evaluateAll(nodes => nodes.filter(el => {
          const s = getComputedStyle(el);
          return s.display !== 'none' && s.visibility === 'visible' && el.getClientRects().length && el.getBoundingClientRect().width > 0;
        }).map(el => {
          const r = el.getBoundingClientRect(), s = getComputedStyle(el);
          return { kind: ['primary-action','form-submit','button'].find(c => el.classList.contains(c)), label: el.textContent.trim(), width: r.width, height: r.height, left: r.left, right: r.right, display: s.display, radius: s.borderRadius };
        }));
        total += samples.length;
        for (const item of samples) {
          assert.ok(item.height >= 43.5, `${route} @${width}: ${item.kind} '${item.label}' mide ${item.height}px de alto`);
          assert.ok(item.left >= -1 && item.right <= width + 1, `${route} @${width}: ${item.kind} '${item.label}' desborda: [${item.left},${item.right}]`);
          assert.notEqual(item.display, 'inline', `${route} @${width}: ${item.kind} '${item.label}' carece de caja de control estable`);
        }
      }
      assert.ok(total > 0, `@${width}: ninguna acción compartida encontrada; revisar selectores y rutas`);
    } finally { await context.close(); }
  }
} finally { await browser.close(); }
