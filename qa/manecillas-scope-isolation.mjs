import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const GOLD = 'rgb(184, 134, 11)';
const PALE_HIGHLIGHT = 'rgb(247, 251, 254)';
const browser = await chromium.launch({ headless: true });
try {
  for (const viewport of [{ width: 1280, height: 800 }, { width: 390, height: 844 }]) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    try {
      let response = await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      assert.ok(response?.ok(), 'Ficha principal no carga');
      assert.equal(await page.locator('body').getAttribute('data-reading-progress'), null);

      const mainOpening = await page.locator('.book-hero__copy>.eyebrow').evaluate((el) => {
        const cs = getComputedStyle(el);
        return { color: cs.color, fontSize: parseFloat(cs.fontSize), backgroundImage: cs.backgroundImage };
      });
      assert.equal(mainOpening.color, GOLD, 'La apertura principal debe conservar el dorado canónico');
      assert.ok(mainOpening.fontSize >= 24, `Apertura dorada por debajo de texto grande: ${mainOpening.fontSize}px`);
      assert.match(mainOpening.backgroundImage, new RegExp(PALE_HIGHLIGHT.replace(/[()]/g, '\\$&')), 'La apertura principal debe usar el resaltado pálido con contraste controlado');

      response = await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/fragmentos/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      assert.ok(response?.ok(), 'Fragmentos no carga');
      assert.equal(await page.locator('body').getAttribute('data-reading-progress'), '');

      const leakedToken = await page.locator('body').evaluate((body) => getComputedStyle(body).getPropertyValue('--man-blue').trim());
      assert.equal(leakedToken, '', `V8 leak: --man-blue=${leakedToken}`);

      const coverBefore = await page.locator('.book-cover').first().evaluate((el) => getComputedStyle(el, '::before').backgroundImage);
      assert.doesNotMatch(coverBefore, /corner-bracket-blue-gold\.svg/, 'V8 leak: Fragmentos recibió brackets de la ficha principal');

      console.log(`ok scope isolation + main gold contrast ${viewport.width}x${viewport.height}`);
    } finally {
      await context.close();
    }
  }
  console.log('manecillas-scope-isolation: PASS');
} finally {
  await browser.close();
}
