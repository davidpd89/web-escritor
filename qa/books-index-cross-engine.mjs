import assert from 'node:assert/strict';
import { chromium, firefox, webkit } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const engines = { chromium, firefox, webkit };

for (const [name, launcher] of Object.entries(engines)) {
  const browser = await launcher.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    const response = await page.goto(`${ORIGIN}/libros/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    assert.equal(response?.ok(), true, `${name}: /libros/ no cargó correctamente`);

    const rootContext = await page.locator('html').getAttribute('data-editorial-context');
    assert.equal(rootContext, 'obras', `${name}: contexto editorial incorrecto`);

    const stageCount = await page.locator('.books-stage, .books-stage-anthology').count();
    assert.equal(stageCount, 3, `${name}: se esperaban tres bloques de obra`);

    const h1Color = await page.locator('.v1-masthead h1').evaluate((el) => getComputedStyle(el).color);
    assert.equal(h1Color, 'rgb(29, 79, 150)', `${name}: H1 fuera del azul canónico`);

    const actionFont = await page.locator('.books-stage__actions a').first().evaluate((el) => getComputedStyle(el).fontFamily);
    assert.match(actionFont.toLowerCase(), /yellowtail/, `${name}: CTA principal no usa Yellowtail`);

    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(80);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    assert.ok(overflow <= 1, `${name}: overflow horizontal móvil de ${overflow}px`);

    const railWidth = await page.locator('.books-stage').first().evaluate((el) => getComputedStyle(el, '::before').width);
    assert.equal(railWidth, '2.5px', `${name}: rail móvil no mantiene 2.5px`);

    console.log(`ok [${name}] /libros/`);
  } finally {
    await browser.close();
  }
}

console.log('books-index-cross-engine: PASS');
