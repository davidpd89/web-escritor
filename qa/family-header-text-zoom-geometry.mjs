import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN;
assert.ok(origin, 'QA_ORIGIN es obligatorio');
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [320, 390, 768]) {
    const context = await browser.newContext({ viewport: { width, height: 850 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    try {
      for (const route of ['/', '/libros/', '/404.html']) {
        const response = await page.goto(new URL(route, origin).href, { waitUntil: 'domcontentloaded' });
        assert.equal(response?.status(), 200, `${route}: HTTP inesperado`);
        await page.locator('.site-header').waitFor({ state: 'visible' });
        await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
        for (const scroll of [0, 450]) {
          await page.evaluate(y => window.scrollTo(0, y), scroll);
          await page.waitForFunction(() => {
            const h = document.querySelector('.site-header');
            return h && getComputedStyle(h).position === 'sticky';
          });
          const result = await page.evaluate(() => {
            const nodes = [...document.querySelectorAll('.site-header__inner a, .site-header__inner button')].filter(el => {
              const s = getComputedStyle(el);
              return s.display !== 'none' && s.visibility !== 'hidden' && el.getClientRects().length;
            });
            const boxes = nodes.map(el => ({ name: el.getAttribute('aria-label') || el.textContent.trim(), r: el.getBoundingClientRect() }));
            const collisions = [];
            for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
              const a = boxes[i].r, b = boxes[j].r;
              if (Math.min(a.right,b.right)-Math.max(a.left,b.left)>2 && Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>2) collisions.push([boxes[i].name,boxes[j].name]);
            }
            return { collisions, overflow: boxes.filter(x => x.r.left < -1 || x.r.right > innerWidth + 1).map(x => x.name), count: boxes.length };
          });
          assert.ok(result.count >= 3, `${route} @${width}, scroll ${scroll}: cabecera sin controles`);
          assert.deepEqual(result.collisions, [], `${route} @${width}, scroll ${scroll}: controles solapados`);
          assert.deepEqual(result.overflow, [], `${route} @${width}, scroll ${scroll}: controles fuera de pantalla`);
        }
      }
    } finally { await context.close(); }
  }
} finally { await browser.close(); }
