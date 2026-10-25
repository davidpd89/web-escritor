import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN;
assert.ok(origin, 'QA_ORIGIN obligatorio');
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [320, 390, 900, 1280]) {
    const context = await browser.newContext({ viewport: { width, height: 850 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    let reference;
    try {
      for (const route of ['/libros/', '/404.html', '/']) {
        const response = await page.goto(new URL(route, origin).href, { waitUntil: 'domcontentloaded' });
        assert.equal(response?.status(), 200, `${route}: HTTP inesperado`);
        const trigger = page.locator('.site-header .explore-trigger');
        await trigger.waitFor({ state: 'visible' });
        const style = await trigger.evaluate(el => {
          const s = getComputedStyle(el), r = el.getBoundingClientRect();
          return { width: r.width, height: r.height, display: s.display, alignItems: s.alignItems, justifyContent: s.justifyContent, borderRadius: s.borderRadius, borderWidth: s.borderTopWidth };
        });
        assert.ok(style.width >= 44 && style.height >= 44, `${route} @${width}: Explorar mide ${style.width}x${style.height}`);
        if (!reference) reference = style;
        else {
          for (const key of Object.keys(reference)) assert.equal(style[key], reference[key], `${route} @${width}: Explorar.${key}=${style[key]}, referencia=${reference[key]}`);
        }
      }
    } finally { await context.close(); }
  }
} finally { await browser.close(); }
