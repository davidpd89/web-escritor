import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/cuaderno';
fs.mkdirSync(OUT, { recursive: true });

const BLUE = 'rgb(29, 79, 150)';
const GOLD = 'rgb(184, 134, 11)';
const PALE = 'rgb(238, 250, 255)';
const NEUTRAL = 'rgb(111, 106, 100)';
const TRANSPARENT = 'rgba(0, 0, 0, 0)';

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

async function style(locator, pseudo = null) {
  return locator.evaluate((el, p) => {
    const s = getComputedStyle(el, p || null);
    return {
      display: s.display,
      gridTemplateColumns: s.gridTemplateColumns,
      position: s.position,
      color: s.color,
      backgroundColor: s.backgroundColor,
      backgroundImage: s.backgroundImage,
      borderTopColor: s.borderTopColor,
      borderTopWidth: s.borderTopWidth,
      borderBottomColor: s.borderBottomColor,
      borderBottomWidth: s.borderBottomWidth,
      borderLeftColor: s.borderLeftColor,
      borderLeftWidth: s.borderLeftWidth,
      boxShadow: s.boxShadow,
      fontFamily: s.fontFamily,
      fontSize: s.fontSize,
      minHeight: s.minHeight,
    };
  }, pseudo);
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
      assert.equal(await page.locator('link[href="/assets/cuaderno-index.css"]').count(), 1, `${name}: capa visual exclusiva no cargada`);
      assert.equal(await page.locator('main#contenido.editorial-page').count(), 1, `${name}: main editorial ausente`);
      assert.equal(await page.locator('h1').count(), 1, `${name}: H1 no único`);
      assert.equal(await page.locator('.section-context [aria-current="page"]').getAttribute('href'), '/cuaderno/', `${name}: contexto no marca Archivo`);
      assert.notEqual((await style(page.locator('.header-search'))).display, 'none', `${name}: Asistente del header no disponible`);

      const token = await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--cuaderno-blue').trim());
      assert.equal(token, '#1d4f96', `${name}: tokens Cuaderno no aplicados`);
      const currentContext = await style(page.locator('.section-context [aria-current="page"]'));
      assert.equal(currentContext.color, BLUE, `${name}: navegación contextual activa no azul`);
      assert.equal(currentContext.backgroundColor, PALE, `${name}: navegación contextual activa no pálida`);
      assert.match(currentContext.boxShadow, /rgb\(184, 134, 11\)/, `${name}: navegación contextual sin cierre dorado`);

      const masthead = page.locator('.cuaderno-masthead');
      const opening = await style(masthead.locator('.eyebrow'));
      assert.equal(opening.color, GOLD, `${name}: apertura Cuaderno no dorada`);
      assert.match(opening.fontFamily.toLowerCase(), /yellowtail/, `${name}: apertura Cuaderno sin Yellowtail`);
      assert.match(opening.backgroundImage, /highlight-8-blue-rect\.png/, `${name}: apertura Cuaderno sin highlight azul`);
      assert.equal((await style(masthead.locator('h1'))).color, BLUE, `${name}: H1 no azul editorial`);
      assert.match((await style(masthead)).backgroundImage, /linear-gradient/, `${name}: masthead sin doble regla azul/dorada`);

      const folio = page.locator('.cuaderno-masthead__folio');
      assert.equal((await folio.locator('strong').innerText()).trim(), '05', `${name}: folio no conserva 05 piezas`);
      assert.equal((await style(folio.locator('strong'))).color, BLUE, `${name}: folio no azul`);
      assert.equal((await style(folio.locator('span'))).color, NEUTRAL, `${name}: folio pierde neutral documental`);

      const themesAction = await style(masthead.locator('.text-action'));
      assert.equal(themesAction.color, BLUE, `${name}: acción de colecciones no azul`);
      assert.match(themesAction.fontFamily.toLowerCase(), /yellowtail/, `${name}: acción de colecciones sin Yellowtail`);
      assert.equal(themesAction.minHeight, '0px', `${name}: acción conserva altura de control genérico`);
      assert.equal(themesAction.backgroundColor, TRANSPARENT, `${name}: acción conserva fondo de botón`);

      assert.equal(await page.locator('.cuaderno-feature').count(), 1, `${name}: destacada ausente`);
      const feature = page.locator('.cuaderno-feature');
      assert.match((await style(feature)).backgroundImage, /linear-gradient/, `${name}: destacada sin cierre editorial`);
      assert.equal((await style(feature.locator('.cuaderno-feature__index'))).color, GOLD, `${name}: índice destacado no dorado`);
      assert.equal((await style(feature.locator('h2'))).color, BLUE, `${name}: titular destacado no azul`);
      const featureBody = await style(feature.locator('.cuaderno-feature__body'));
      if (width > 900) {
        assert.equal(featureBody.borderLeftColor, BLUE, `${name}: destacada pierde rail azul >900`);
        assert.ok(parseFloat(featureBody.borderLeftWidth) >= 2, `${name}: rail destacado demasiado débil`);
      } else {
        assert.equal(featureBody.borderLeftWidth, '0px', `${name}: rail destacado no se limpia <=900`);
      }

      assert.equal(await page.locator('.cuaderno-ledger > .cuaderno-entry').count(), 4, `${name}: archivo no conserva cuatro entradas`);
      assert.deepEqual(await page.locator('.cuaderno-entry__index').allInnerTexts(), ['02', '03', '04', '05'], `${name}: índices del archivo alterados`);
      const ledger = await style(page.locator('.cuaderno-ledger'));
      assert.equal(ledger.borderTopColor, BLUE, `${name}: ledger sin apertura azul`);
      assert.equal(ledger.borderBottomColor, GOLD, `${name}: ledger sin cierre dorado`);
      assert.equal((await style(page.locator('.cuaderno-entry__index').first())).color, GOLD, `${name}: índice ledger no dorado`);
      assert.equal((await style(page.locator('.cuaderno-entry__body h3 a').first())).color, BLUE, `${name}: titular ledger no azul`);
      assert.equal((await style(page.locator('.cuaderno-entry__meta').first())).color, NEUTRAL, `${name}: metadata ledger pierde neutral`);

      assert.equal(await page.locator('.editorial-continuity__links a').count(), 4, `${name}: continuidad editorial alterada`);
      const continuity = page.locator('.editorial-continuity');
      assert.match((await style(continuity)).backgroundImage, /linear-gradient/, `${name}: continuidad sin doble regla`);
      assert.equal((await style(continuity.locator('h2'))).color, BLUE, `${name}: continuidad H2 no azul`);
      assert.equal((await style(continuity.locator('.eyebrow'))).color, GOLD, `${name}: continuidad sin apertura dorada`);

      assert.equal(await page.locator('.editorial-newsletter form').count(), 1, `${name}: newsletter editorial ausente`);
      const newsletter = page.locator('.editorial-newsletter');
      assert.match((await style(newsletter)).backgroundImage, /linear-gradient/, `${name}: newsletter sin doble regla`);
      assert.equal((await style(newsletter.locator('h2'))).color, BLUE, `${name}: newsletter H2 no azul`);
      assert.equal((await style(newsletter.locator('.eyebrow'))).color, GOLD, `${name}: newsletter sin apertura dorada`);
      assert.equal((await style(newsletter.locator('.form-submit'))).backgroundColor, BLUE, `${name}: submit newsletter no azul`);

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 1, `${name}: overflow horizontal ${overflow}px`);

      const mastheadCols = cols((await style(masthead)).gridTemplateColumns);
      const featureCols = cols((await style(feature)).gridTemplateColumns);
      const entryCols = cols((await style(page.locator('.cuaderno-entry').first())).gridTemplateColumns);
      const continuityCols = cols((await style(continuity)).gridTemplateColumns);
      const newsletterCols = cols((await style(newsletter)).gridTemplateColumns);

      if (width > 900) {
        assert.equal(mastheadCols, 2, `${name}: masthead debe usar dos columnas >900`);
        assert.equal(featureCols, 2, `${name}: destacada debe usar dos columnas >900`);
        assert.equal(entryCols, 3, `${name}: ledger debe usar tres columnas >900`);
        assert.equal(continuityCols, 2, `${name}: continuidad debe usar dos columnas >900`);
        assert.equal(newsletterCols, 2, `${name}: newsletter debe usar dos columnas >900`);
        assert.equal((await style(folio)).borderLeftColor, BLUE, `${name}: folio desktop pierde rail azul`);
      } else {
        assert.equal(mastheadCols, 1, `${name}: masthead debe apilar <=900`);
        assert.equal(featureCols, 1, `${name}: destacada debe apilar <=900`);
        assert.equal(entryCols, 2, `${name}: ledger debe conservar índice + cuerpo <=900`);
        assert.equal(continuityCols, 1, `${name}: continuidad debe apilar <=900`);
        assert.equal(newsletterCols, 1, `${name}: newsletter debe apilar <=900`);
        assert.equal((await style(folio)).borderTopColor, BLUE, `${name}: folio móvil pierde regla azul`);
      }

      const footerBefore = await style(page.locator('.site-footer'), '::before');
      assert.match(footerBefore.backgroundImage, /linear-gradient/, `${name}: footer sin doble regla Cuaderno`);
      assert.equal((await style(page.locator('.site-footer .brand__name'))).color, BLUE, `${name}: firma footer no azul`);

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

  const isolation = await browser.newContext({ viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce' });
  await isolation.addInitScript(() => {
    try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {}
  });
  const article = await isolation.newPage();
  try {
    const response = await article.goto(`${ORIGIN}/cuaderno/que-es-el-portal-fantasy/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    assert.ok(response?.ok(), 'isolation: artículo no carga');
    await article.evaluate(() => document.fonts?.ready);
    assert.equal(await article.locator('link[href="/assets/cuaderno-index.css"]').count(), 0, 'isolation: hoja del índice se filtra al artículo');
    const articleToken = await article.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--cuaderno-blue').trim());
    assert.equal(articleToken, '', 'isolation: tokens del índice se filtran al artículo');
  } catch (error) {
    failures.push({ viewport: 'article-isolation', width: 1280, height: 800, error: error instanceof Error ? error.message : String(error) });
  } finally {
    await isolation.close();
  }
} finally {
  await browser.close();
}

fs.writeFileSync(path.join(OUT, 'cuaderno-index-design-report.json'), `${JSON.stringify({ route: '/cuaderno/', viewports, measurements, failures }, null, 2)}\n`);
assert.deepEqual(failures, [], `Cuaderno index design failures:\n${JSON.stringify(failures, null, 2)}`);
console.log(`cuaderno-index-design-browser: PASS (${viewports.length} viewports + article isolation)`);
