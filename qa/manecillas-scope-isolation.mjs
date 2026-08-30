import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const GOLD = 'rgb(184, 134, 11)';
const PALE_HIGHLIGHT = 'rgb(247, 251, 254)';

async function assertGoldOpening(locator, label) {
  const state = await locator.evaluate((el) => {
    const cs = getComputedStyle(el);
    return {
      color: cs.color,
      fontSize: parseFloat(cs.fontSize),
      backgroundImage: cs.backgroundImage,
    };
  });
  assert.equal(state.color, GOLD, `${label}: se perdió el dorado canónico`);
  assert.ok(state.fontSize >= 24, `${label}: texto dorado por debajo de 24px (${state.fontSize}px)`);
  assert.ok(state.backgroundImage.includes(PALE_HIGHLIGHT), `${label}: el resaltado no conserva el fondo pálido con contraste controlado (${state.backgroundImage})`);
}

async function assertHeaderAssistant(page, label) {
  const button = page.locator('.header-search');
  await button.waitFor({ state: 'visible', timeout: 4000 });
  const box = await button.boundingBox();
  assert.ok(box && box.width >= 44 && box.height >= 44, `${label}: acceso Asistente del header por debajo de 44x44`);
  assert.equal(await button.getAttribute('aria-label'), 'Abrir asistente', `${label}: acceso Asistente sin nombre accesible esperado`);
}

const browser = await chromium.launch({ headless: true });
try {
  for (const viewport of [{ width: 1280, height: 800 }, { width: 390, height: 844 }]) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    try {
      let response = await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      assert.ok(response?.ok(), 'Ficha principal no carga');
      assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'manecillas');
      assert.equal(await page.locator('body').getAttribute('data-reading-progress'), null);

      const mainTokens = await page.locator('body').evaluate((body) => {
        const cs = getComputedStyle(body);
        return {
          man: cs.getPropertyValue('--man-blue').trim(),
          frag: cs.getPropertyValue('--frag-blue').trim(),
        };
      });
      assert.equal(mainTokens.man, '#1d4f96', `Main scope perdido: --man-blue=${mainTokens.man}`);
      assert.equal(mainTokens.frag, '', `Leak Fragmentos -> main: --frag-blue=${mainTokens.frag}`);
      await assertGoldOpening(page.locator('.book-hero__copy>.eyebrow'), `Main ${viewport.width}px`);
      await assertHeaderAssistant(page, `Main ${viewport.width}px`);

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

      const goldOpenings = [
        ['.book-hero__copy>.eyebrow', 'hero'],
        ['.book-hero + .v1-section>.eyebrow', 'intro'],
        ['.excerpt-section .book-section__label>.eyebrow', 'fragmento'],
        ['#cta-final>.eyebrow', 'cta'],
      ];
      for (const [selector, name] of goldOpenings) {
        await assertGoldOpening(page.locator(selector).first(), `Fragmentos ${name} ${viewport.width}px`);
      }
      await assertHeaderAssistant(page, `Fragmentos ${viewport.width}px`);

      console.log(`ok scope + contrast + assistant access Main/Fragmentos ${viewport.width}x${viewport.height}`);
    } finally {
      await context.close();
    }
  }
  console.log('manecillas-scope-isolation: PASS');
} finally {
  await browser.close();
}
