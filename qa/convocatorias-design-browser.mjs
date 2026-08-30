import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/convocatorias';
const FIXED_TODAY = '2026-08-21';
fs.mkdirSync(OUT, { recursive: true });

const viewports = [
  ['wide-1728', 1728, 1000],
  ['desktop-1440', 1440, 1000],
  ['desktop-1280', 1280, 800],
  ['tablet-1024', 1024, 768],
  ['layout-901', 901, 800],
  ['layout-900', 900, 800],
  ['ledger-861', 861, 850],
  ['ledger-860', 860, 850],
  ['tablet-768', 768, 1024],
  ['layout-641', 641, 900],
  ['layout-640', 640, 900],
  ['record-521', 521, 900],
  ['record-520', 520, 900],
  ['mobile-390', 390, 844],
  ['mobile-389', 389, 844],
  ['mobile-360', 360, 800],
  ['mobile-320', 320, 900],
];

function columnCount(value) {
  if (!value || value === 'none') return 0;
  return value.trim().split(/\s+/).length;
}

async function snapshot(locator) {
  return locator.evaluate(el => {
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return {
      display: s.display,
      gridTemplateColumns: s.gridTemplateColumns,
      color: s.color,
      backgroundColor: s.backgroundColor,
      backgroundImage: s.backgroundImage,
      borderTopWidth: s.borderTopWidth,
      borderBottomWidth: s.borderBottomWidth,
      borderLeftWidth: s.borderLeftWidth,
      borderRadius: s.borderRadius,
      boxShadow: s.boxShadow,
      fontFamily: s.fontFamily,
      fontSize: s.fontSize,
      lineHeight: s.lineHeight,
      maxWidth: s.maxWidth,
      position: s.position,
      width: r.width,
      height: r.height,
      left: r.left,
      top: r.top,
    };
  });
}

async function prepareContext(browser, viewport, javaScriptEnabled = true) {
  const context = await browser.newContext({ viewport, javaScriptEnabled, reducedMotion: 'reduce' });
  if (javaScriptEnabled) {
    await context.addInitScript(fixedToday => {
      window.__DP_RADAR_TODAY__ = fixedToday;
      try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {}
    }, FIXED_TODAY);
  }
  return context;
}

const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}),
});

const failures = [];
const measurements = [];

try {
  for (const [name, width, height] of viewports) {
    const context = await prepareContext(browser, { width, height });
    const page = await context.newPage();
    try {
      const response = await page.goto(`${ORIGIN}/convocatorias-escritores/`, { waitUntil: 'networkidle', timeout: 20000 });
      assert.ok(response?.ok(), `${name}: /convocatorias-escritores/ no carga`);
      await page.evaluate(() => document.fonts?.ready);
      await page.waitForTimeout(120);

      assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'herramientas', `${name}: contexto Herramientas perdido`);
      assert.equal(await page.locator('main#contenido').getAttribute('data-family'), 'tool', `${name}: familia tool alterada`);
      assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'), 'https://davidportodiaz.com/convocatorias-escritores/', `${name}: canonical alterado`);
      assert.equal(await page.locator('h1').count(), 1, `${name}: H1 no único`);
      assert.equal((await page.locator('h1').textContent()).trim(), 'Convocatorias que todavía están a tiempo.', `${name}: H1 alterado`);
      assert.equal(await page.locator('.section-context [aria-current="page"]').getAttribute('href'), '/convocatorias-escritores/', `${name}: contexto no marca Convocatorias`);

      const items = page.locator('[data-radar-item]');
      assert.equal(await items.count(), 2, `${name}: el radar ya no conserva dos oportunidades activas en la fecha fija`);
      assert.deepEqual(await items.evaluateAll(nodes => nodes.map(node => ({
        title: node.getAttribute('data-title'),
        organizer: node.getAttribute('data-organizer'),
        deadline: node.getAttribute('data-deadline'),
        type: node.getAttribute('data-type'),
      }))), [
        { title: 'premios literarios kutxa fundazioa 2027', organizer: 'kutxa fundazioa', deadline: '2026-09-21', type: 'concurso' },
        { title: 'x premio internacional de poesía jorge manrique', organizer: 'diputación de palencia y ayuntamiento de paredes de nava', deadline: '2026-10-09', type: 'concurso' },
      ], `${name}: oportunidades activas o su orden cambiaron`);

      assert.equal(await page.locator('[data-radar-search]').count(), 1, `${name}: buscador ausente`);
      assert.equal(await page.locator('[data-radar-type]').count(), 1, `${name}: filtro de tipo ausente`);
      assert.equal(await page.locator('[data-radar-genre]').count(), 1, `${name}: filtro de género ausente`);
      assert.equal(await page.locator('[data-radar-soon]').count(), 1, `${name}: filtro de cierre próximo ausente`);
      assert.equal(await page.locator('[data-radar-count]').count(), 1, `${name}: contador ausente`);
      assert.equal(await page.locator('[data-radar-calendar]').getAttribute('href'), '/convocatorias-escritores/deadlines.ics', `${name}: enlace ICS alterado`);
      assert.equal(await page.locator('.tool-findings-block h2').textContent(), 'Cómo se mantiene este radar', `${name}: bloque metodológico alterado`);

      const statuses = await page.locator('[data-radar-status]').allTextContents();
      assert.deepEqual(statuses.map(value => value.trim()), ['En plazo', 'En plazo'], `${name}: estados dinámicos inesperados con fecha fija`);
      const relatives = await page.locator('[data-radar-relative]').allTextContents();
      assert.ok(relatives.every(value => value.includes('faltan')), `${name}: fechas relativas no calculadas`);

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 1, `${name}: overflow horizontal ${overflow}px`);

      const hero = await snapshot(page.locator('.tool-hero'));
      const heroTitle = await snapshot(page.locator('.tool-hero h1'));
      const heroEyebrow = await snapshot(page.locator('.tool-hero .eyebrow'));
      const heroNote = await snapshot(page.locator('.tool-hero > .tool-note'));
      const heroActions = await snapshot(page.locator('.tool-hero__actions'));
      const calendar = await snapshot(page.locator('[data-radar-calendar]'));
      const finder = await snapshot(page.locator('.tool-finder'));
      const options = await snapshot(page.locator('.tool-options'));
      const grid = await snapshot(page.locator('.radar-grid'));
      const firstCard = await snapshot(items.first());
      const firstTop = await snapshot(items.first().locator('.radar-card__top'));
      const firstTitle = await snapshot(items.first().locator('h2'));
      const firstBadge = await snapshot(items.first().locator('.radar-badge'));
      const firstLedger = await snapshot(items.first().locator('dl'));
      const firstSource = await snapshot(items.first().locator('[data-radar-source]'));
      const method = await snapshot(page.locator('.tool-findings-block'));
      const activeContext = await snapshot(page.locator('.section-context [aria-current="page"]'));
      const footer = await snapshot(page.locator('.site-footer'));

      // Capture the inherited responsive grammar before any production redesign.
      assert.equal(columnCount(firstLedger.gridTemplateColumns), width > 860 ? 4 : width > 520 ? 2 : 1, `${name}: seam heredado 861/860/520 del ledger cambió`);
      assert.equal(firstTop.display, width > 520 ? 'flex' : 'grid', `${name}: seam heredado 521/520 del encabezado cambió`);

      measurements.push({
        name, width, height, overflow,
        hero, heroTitle, heroEyebrow, heroNote, heroActions, calendar,
        finder, options, grid, firstCard, firstTop, firstTitle, firstBadge,
        firstLedger, firstSource, method, activeContext, footer,
      });

      await page.evaluate(() => {
        if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
        window.scrollTo(0, 0);
      });
      await page.waitForTimeout(50);
      await page.screenshot({ path: path.join(OUT, `convocatorias-${name}.png`), fullPage: true });
    } catch (error) {
      failures.push({ viewport: name, width, height, error: error instanceof Error ? error.message : String(error) });
    } finally {
      await context.close();
    }
  }

  const interactionContext = await prepareContext(browser, { width: 390, height: 844 });
  const interactionPage = await interactionContext.newPage();
  try {
    const response = await interactionPage.goto(`${ORIGIN}/convocatorias-escritores/`, { waitUntil: 'networkidle', timeout: 20000 });
    assert.ok(response?.ok(), 'interaction: radar no carga');

    await interactionPage.locator('[data-radar-search]').fill('KUTXA');
    assert.equal(await interactionPage.locator('[data-radar-item]:visible').count(), 1, 'interaction: búsqueda Kutxa no devuelve una oportunidad');
    assert.equal((await interactionPage.locator('[data-radar-count]').textContent()).trim(), '1 convocatoria visible', 'interaction: contador de búsqueda incorrecto');
    await interactionPage.evaluate(() => { if (document.activeElement instanceof HTMLElement) document.activeElement.blur(); window.scrollTo(0, 0); });
    await interactionPage.waitForTimeout(50);
    await interactionPage.screenshot({ path: path.join(OUT, 'convocatorias-filtered-390.png'), fullPage: true });

    await interactionPage.locator('[data-radar-clear]').click();
    await interactionPage.locator('[data-radar-genre]').selectOption('novela');
    assert.equal(await interactionPage.locator('[data-radar-item]:visible').count(), 1, 'interaction: género novela no devuelve solo Kutxa');

    await interactionPage.locator('[data-radar-clear]').click();
    await interactionPage.locator('[data-radar-soon]').check();
    assert.equal(await interactionPage.locator('[data-radar-item]:visible').count(), 0, 'interaction: cierre en 7 días debería quedar vacío en fecha fija');
    assert.equal(await interactionPage.locator('[data-radar-filter-empty]').isVisible(), true, 'interaction: estado vacío no aparece');
    await interactionPage.evaluate(() => { if (document.activeElement instanceof HTMLElement) document.activeElement.blur(); window.scrollTo(0, 0); });
    await interactionPage.waitForTimeout(50);
    await interactionPage.screenshot({ path: path.join(OUT, 'convocatorias-empty-390.png'), fullPage: true });

    await interactionPage.locator('[data-radar-empty-clear]').click();
    assert.equal(await interactionPage.locator('[data-radar-item]:visible').count(), 2, 'interaction: limpiar desde vacío no restaura las dos oportunidades');
  } catch (error) {
    failures.push({ viewport: 'interaction-mobile-390', width: 390, height: 844, error: error instanceof Error ? error.message : String(error) });
  } finally {
    await interactionContext.close();
  }

  const noJsContext = await prepareContext(browser, { width: 390, height: 844 }, false);
  const noJsPage = await noJsContext.newPage();
  try {
    const response = await noJsPage.goto(`${ORIGIN}/convocatorias-escritores/`, { waitUntil: 'load', timeout: 20000 });
    assert.ok(response?.ok(), 'no-js: radar no carga');
    assert.equal(await noJsPage.locator('[data-radar-item]').count(), 2, 'no-js: las dos oportunidades dejan de estar en HTML');
    assert.equal(await noJsPage.locator('noscript .tool-note').count(), 1, 'no-js: aviso explicativo ausente');
    assert.equal(await noJsPage.locator('[data-radar-calendar]').getAttribute('href'), '/convocatorias-escritores/deadlines.ics', 'no-js: enlace ICS perdido');
    const dates = await noJsPage.locator('[data-radar-item] time').allTextContents();
    assert.ok(dates.includes('21/09/2026') && dates.includes('09/10/2026'), 'no-js: fechas activas no visibles');
    await noJsPage.screenshot({ path: path.join(OUT, 'convocatorias-no-js-390.png'), fullPage: true });
  } catch (error) {
    failures.push({ viewport: 'no-js-mobile-390', width: 390, height: 844, error: error instanceof Error ? error.message : String(error) });
  } finally {
    await noJsContext.close();
  }
} finally {
  await browser.close();
}

fs.writeFileSync(
  path.join(OUT, 'convocatorias-design-report.json'),
  JSON.stringify({ route: '/convocatorias-escritores/', phase: 'inherited-baseline', fixedToday: FIXED_TODAY, viewports: viewports.length, measurements, failures }, null, 2),
);

assert.deepEqual(failures, [], `Convocatorias inherited-baseline failures:\n${JSON.stringify(failures, null, 2)}`);
console.log(`Convocatorias inherited baseline: PASS (${viewports.length} viewports + interaction states + no-JS)`);
