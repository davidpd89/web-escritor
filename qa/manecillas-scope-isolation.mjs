import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  for (const viewport of [{ width: 1280, height: 800 }, { width: 390, height: 844 }]) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    try {
      let response = await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      assert.ok(response?.ok(), 'Ficha principal no carga');
      const mainTokens = await page.locator('body').evaluate((body) => {
        const cs = getComputedStyle(body);
        return {
          man: cs.getPropertyValue('--man-blue').trim(),
          frag: cs.getPropertyValue('--frag-blue').trim(),
        };
      });
      assert.equal(mainTokens.man, '#1d4f96', `Main scope perdido: --man-blue=${mainTokens.man}`);
      assert.equal(mainTokens.frag, '', `Leak Fragmentos -> main: --frag-blue=${mainTokens.frag}`);

      response = await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/fragmentos/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      assert.ok(response?.ok(), 'Fragmentos no carga');
      assert.equal(await page.locator('body').getAttribute('data-reading-progress'), '');

      const fragmentTokens = await page.locator('body').evaluate((body) => {
        const cs = getComputedStyle(body);
        return {
          man: cs.getPropertyValue('--man-blue').trim(),
          frag: cs.getPropertyValue('--frag-blue').trim(),
        };
      });
      assert.equal(fragmentTokens.man, '', `Leak main -> Fragmentos: --man-blue=${fragmentTokens.man}`);
      assert.equal(fragmentTokens.frag, '#1d4f96', `Fragmentos scope perdido: --frag-blue=${fragmentTokens.frag}`);

      const coverBefore = await page.locator('.book-cover').first().evaluate((el) => getComputedStyle(el, '::before').backgroundImage);
      assert.match(coverBefore, /corner-bracket-blue-gold\.svg/, 'Fragmentos debe recibir sus brackets propios');

      console.log(`ok scope isolation Main/Fragmentos ${viewport.width}x${viewport.height}`);
    } finally {
      await context.close();
    }
  }
  console.log('manecillas-scope-isolation: PASS');
} finally {
  await browser.close();
}
