import assert from 'node:assert/strict';
import { chromium, firefox, webkit } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const engines = { chromium, firefox, webkit };

for (const [name, launcher] of Object.entries(engines)) {
  const browser = await launcher.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 850 } });
    let response = await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    assert.equal(response?.ok(), true, `${name}: Manecillas no cargó correctamente`);
    await page.evaluate(() => document.fonts?.ready);

    assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'manecillas', `${name}: contexto editorial incorrecto`);
    assert.equal(await page.locator('body').getAttribute('data-reading-progress'), null, `${name}: la ficha principal no debe confundirse con Fragmentos`);

    const h1Color = await page.locator('.book-hero h1').evaluate((el) => getComputedStyle(el).color);
    assert.equal(h1Color, 'rgb(29, 79, 150)', `${name}: H1 fuera del azul canónico`);

    const openingFont = await page.locator('.book-hero__copy>.eyebrow').evaluate((el) => getComputedStyle(el).fontFamily);
    assert.match(openingFont.toLowerCase(), /yellowtail/, `${name}: apertura principal no usa Yellowtail`);

    const coverBefore = await page.locator('.book-cover').evaluate((el) => getComputedStyle(el, '::before').backgroundImage);
    const coverAfter = await page.locator('.book-cover').evaluate((el) => getComputedStyle(el, '::after').backgroundImage);
    assert.match(coverBefore, /corner-bracket-blue-gold\.svg/, `${name}: falta bracket superior`);
    assert.match(coverAfter, /corner-bracket-blue-gold\.svg/, `${name}: falta bracket inferior`);

    const noteRail = await page.locator('.book-margin-note').evaluate((el) => {
      const cs = getComputedStyle(el);
      return { image: cs.backgroundImage, size: cs.backgroundSize };
    });
    assert.match(noteRail.image, /linear-gradient/, `${name}: cita sin rail`);
    assert.match(noteRail.size, /2\.5px\s+100%/, `${name}: rail de cita no conserva 2.5px`);

    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(100);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    assert.ok(overflow <= 1, `${name}: overflow horizontal móvil de ${overflow}px`);
    const anchorPosition = await page.locator('.book-anchor-alias').first().evaluate((el) => getComputedStyle(el).position);
    assert.equal(anchorPosition, 'absolute', `${name}: #muestra vuelve al grid en móvil`);

    response = await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/fragmentos/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    assert.equal(response?.ok(), true, `${name}: Fragmentos no cargó correctamente`);
    const fragmentScope = await page.locator('body').evaluate((el) => getComputedStyle(el).getPropertyValue('--man-blue').trim());
    assert.equal(fragmentScope, '', `${name}: V8 de la ficha principal contamina Fragmentos`);
    const fragmentCoverBefore = await page.locator('.book-cover').first().evaluate((el) => getComputedStyle(el, '::before').backgroundImage);
    assert.doesNotMatch(fragmentCoverBefore, /corner-bracket-blue-gold\.svg/, `${name}: brackets de la ficha principal contaminan Fragmentos`);

    console.log(`ok [${name}] Manecillas + aislamiento Fragmentos`);
  } finally {
    await browser.close();
  }
}

console.log('manecillas-cross-engine: PASS');
