import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/cuaderno';
fs.mkdirSync(OUT, { recursive: true });

const viewports = [
  ['wide-1728', 1728, 1000],
  ['desktop-1440', 1440, 1000],
  ['desktop-1280', 1280, 800],
  ['tablet-1024', 1024, 768],
  ['layout-901', 901, 800],
  ['layout-900', 900, 800],
  ['tablet-768', 768, 1024],
  ['tablet-767', 767, 900],
  ['mid-640', 640, 900],
  ['mobile-390', 390, 844],
  ['mobile-389', 389, 844],
  ['mobile-360', 360, 800],
  ['mobile-320', 320, 900],
];

async function style(locator) {
  return locator.evaluate(el => {
    const s = getComputedStyle(el);
    return {
      display: s.display,
      gridTemplateColumns: s.gridTemplateColumns,
      position: s.position,
      color: s.color,
      backgroundColor: s.backgroundColor,
      borderTopWidth: s.borderTopWidth,
      borderBottomWidth: s.borderBottomWidth,
    };
  });
}

function cols(value) {
  return value === 'none' ? 0 : value.split(' ').filter(Boolean).length;
}

const browser = await chromium.launch({ headless: true });
const failures = [];
const measurements = [];

try {
  for (const [name, width, height] of viewports) {
    const context = await browser.newContext({ viewport: { width, height }, reducedMotion: 'reduce' });
    await context.addInitScript(() => {
      try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {}
    });
    const page = await context.newPage();
    try {
      const response = await page.goto(`${ORIGIN}/cuaderno/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      assert.ok(response?.ok(), `${name}: /cuaderno/ no carga`);
      await page.evaluate(() => document.fonts?.ready);

      assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'cuaderno', `${name}: contexto Cuaderno perdido`);
      assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'), 'https://davidportodiaz.com/cuaderno/', `${name}: canonical alterado`);
      assert.equal(await page.locator('main#contenido.editorial-page').count(), 1, `${name}: main editorial ausente`);
      assert.equal(await page.locator('h1').count(), 1, `${name}: H1 no único`);
      assert.equal(await page.locator('.section-context [aria-current="page"]').getAttribute('href'), '/cuaderno/', `${name}: contexto no marca Archivo`);
      assert.notEqual((await style(page.locator('.header-search'))).display, 'none', `${name}: Asistente del header no disponible`);

      const folio = page.locator('.cuaderno-masthead__folio');
      assert.equal((await folio.locator('strong').innerText()).trim(), '05', `${name}: folio no conserva 05 piezas`);
      assert.equal(await page.locator('.cuaderno-feature').count(), 1, `${name}: destacada ausente`);
      assert.equal(await page.locator('.cuaderno-ledger > .cuaderno-entry').count(), 4, `${name}: archivo no conserva cuatro entradas`);
      assert.deepEqual(await page.locator('.cuaderno-entry__index').allInnerTexts(), ['02', '03', '04', '05'], `${name}: índices del archivo alterados`);
      assert.equal(await page.locator('.editorial-continuity__links a').count(), 4, `${name}: continuidad editorial alterada`);
      assert.equal(await page.locator('.editorial-newsletter form').count(), 1, `${name}: newsletter editorial ausente`);

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 1, `${name}: overflow horizontal ${overflow}px`);

      const mastheadCols = cols((await style(page.locator('.cuaderno-masthead'))).gridTemplateColumns);
      const featureCols = cols((await style(page.locator('.cuaderno-feature'))).gridTemplateColumns);
      const entryCols = cols((await style(page.locator('.cuaderno-entry').first())).gridTemplateColumns);
      const continuityCols = cols((await style(page.locator('.editorial-continuity'))).gridTemplateColumns);
      const newsletterCols = cols((await style(page.locator('.editorial-newsletter'))).gridTemplateColumns);

      if (width > 900) {
        assert.equal(mastheadCols, 2, `${name}: masthead debe usar dos columnas >900`);
        assert.equal(featureCols, 2, `${name}: destacada debe usar dos columnas >900`);
        assert.equal(entryCols, 3, `${name}: ledger debe usar tres columnas >900`);
        assert.equal(continuityCols, 2, `${name}: continuidad debe usar dos columnas >900`);
        assert.equal(newsletterCols, 2, `${name}: newsletter debe usar dos columnas >900`);
      } else {
        assert.equal(mastheadCols, 1, `${name}: masthead debe apilar <=900`);
        assert.equal(featureCols, 1, `${name}: destacada debe apilar <=900`);
        assert.equal(entryCols, 2, `${name}: ledger debe conservar índice + cuerpo <=900`);
        assert.equal(continuityCols, 1, `${name}: continuidad debe apilar <=900`);
        assert.equal(newsletterCols, 1, `${name}: newsletter debe apilar <=900`);
      }

      measurements.push({ name, width, height, mastheadCols, featureCols, entryCols, continuityCols, newsletterCols, overflow });

      await page.evaluate(() => {
        if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
        window.scrollTo(0, 0);
      });
      await page.waitForTimeout(50);
      await page.screenshot({ path: path.join(OUT, `cuaderno-index-${name}.png`), fullPage: true });
    } catch (error) {
      failures.push({ viewport: name, width, height, error: error instanceof Error ? error.message : String(error) });
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}

fs.writeFileSync(path.join(OUT, 'cuaderno-index-design-report.json'), `${JSON.stringify({ route: '/cuaderno/', viewports, measurements, failures }, null, 2)}\n`);
assert.deepEqual(failures, [], `Cuaderno index design baseline failures:\n${JSON.stringify(failures, null, 2)}`);
console.log(`cuaderno-index-design-browser: PASS (${viewports.length} viewports)`);
