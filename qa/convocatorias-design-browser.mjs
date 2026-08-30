import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/convocatorias';
const FIXED_TODAY = '2026-08-21';
fs.mkdirSync(OUT, { recursive: true });

const BLUE = 'rgb(29, 79, 150)';
const BLUE_DEEP = 'rgb(13, 44, 87)';
const GOLD = 'rgb(184, 134, 11)';
const GOLD_TEXT = 'rgb(155, 110, 0)';
const PALE = 'rgb(238, 250, 255)';

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
      borderColor: s.borderColor,
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

async function stabilizeTypography(page) {
  const loaded = await page.evaluate(async () => {
    if (!document.fonts) return { instrument: false, newsreader: false, manrope: false };
    await Promise.all([
      document.fonts.load('400 64px "Instrument Serif"', 'Convocatorias'),
      document.fonts.load('400 18px Newsreader', 'Concursos premios ayudas becas'),
      document.fonts.load('700 14px Manrope', 'FECHA LÍMITE EN PLAZO'),
    ]);
    await document.fonts.ready;
    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    return {
      instrument: document.fonts.check('400 64px "Instrument Serif"', 'Convocatorias'),
      newsreader: document.fonts.check('400 18px Newsreader', 'Concursos premios ayudas becas'),
      manrope: document.fonts.check('700 14px Manrope', 'FECHA LÍMITE EN PLAZO'),
    };
  });
  assert.deepEqual(loaded, { instrument: true, newsreader: true, manrope: true }, 'tipografías editoriales no cargadas');
  return loaded;
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
      const fontChecks = await stabilizeTypography(page);

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

      const radarToken = await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--radar-blue').trim());
      const directoryToken = await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--directory-blue').trim());
      const methodToken = await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--method-blue').trim());
      assert.equal(radarToken.toLowerCase(), '#1d4f96', `${name}: tokens del radar no activos`);
      assert.equal(directoryToken, '', `${name}: Convocatorias hereda tokens del directorio`);
      assert.equal(methodToken, '', `${name}: Convocatorias hereda tokens de Metodología`);

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 1, `${name}: overflow horizontal ${overflow}px`);

      const hero = await snapshot(page.locator('.tool-hero'));
      const heroTitle = await snapshot(page.locator('.tool-hero h1'));
      const titleStableBefore = { width: heroTitle.width, height: heroTitle.height, fontSize: heroTitle.fontSize, maxWidth: heroTitle.maxWidth };
      await page.waitForTimeout(140);
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      const titleStableAfterRaw = await snapshot(page.locator('.tool-hero h1'));
      const titleStableAfter = { width: titleStableAfterRaw.width, height: titleStableAfterRaw.height, fontSize: titleStableAfterRaw.fontSize, maxWidth: titleStableAfterRaw.maxWidth };
      assert.deepEqual(titleStableAfter, titleStableBefore, `${name}: geometría del H1 no estable antes de medir`);

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
      const firstDeadline = await snapshot(items.first().locator('dl>div').first());
      const firstDeadlineTerm = await snapshot(items.first().locator('dl>div').first().locator('dt'));
      const firstDeadlineTime = await snapshot(items.first().locator('dl>div').first().locator('time'));
      const firstSource = await snapshot(items.first().locator('[data-radar-source]'));
      const method = await snapshot(page.locator('.tool-findings-block'));
      const activeContext = await snapshot(page.locator('.section-context [aria-current="page"]'));
      const footer = await snapshot(page.locator('.site-footer'));
      const footerRule = await page.locator('.site-footer').evaluate(el => getComputedStyle(el, '::before').backgroundImage);

      assert.equal(hero.display, 'grid', `${name}: hero deja de ser grid`);
      assert.equal(columnCount(hero.gridTemplateColumns), width > 900 ? 2 : 1, `${name}: seam 901/900 del hero incorrecto`);
      assert.ok(hero.backgroundImage.includes(BLUE) && hero.backgroundImage.includes(GOLD), `${name}: hero pierde la doble regla azul/dorado`);
      assert.equal(heroTitle.color, BLUE, `${name}: H1 pierde el azul del radar`);
      assert.ok(heroTitle.fontFamily.includes('Instrument Serif'), `${name}: H1 pierde la tipografía editorial`);
      assert.equal(heroEyebrow.color, GOLD_TEXT, `${name}: eyebrow pierde el dorado AA`);
      assert.ok(heroNote.boxShadow.includes(BLUE) && heroNote.boxShadow.includes(GOLD), `${name}: aviso de confianza pierde rails`);
      assert.ok(calendar.boxShadow.includes(GOLD), `${name}: acción de calendario pierde acento temporal`);

      assert.equal(finder.display, 'grid', `${name}: finder deja de ser grid`);
      assert.ok(finder.backgroundImage.includes(BLUE) && finder.backgroundImage.includes(GOLD), `${name}: finder pierde su doble línea temporal`);
      assert.equal(columnCount(options.gridTemplateColumns), width > 900 ? 3 : width > 640 ? 2 : 1, `${name}: seam de filtros incorrecto`);

      assert.equal(firstCard.display, 'grid', `${name}: expediente temporal deja de ser grid`);
      assert.equal(columnCount(firstCard.gridTemplateColumns), width > 900 ? 2 : 1, `${name}: seam 901/900 del expediente incorrecto`);
      assert.equal(firstTitle.color, BLUE, `${name}: título de convocatoria pierde azul`);
      assert.equal(firstBadge.color, BLUE_DEEP, `${name}: badge pierde azul profundo`);
      assert.equal(firstBadge.backgroundColor, PALE, `${name}: badge pierde fondo pálido`);
      assert.equal(columnCount(firstLedger.gridTemplateColumns), width > 640 ? 3 : 1, `${name}: seam 641/640 del ledger incorrecto`);
      assert.ok(firstDeadline.boxShadow.includes(BLUE) && firstDeadline.boxShadow.includes(GOLD), `${name}: fecha límite pierde rails`);
      assert.equal(firstDeadlineTerm.color, GOLD_TEXT, `${name}: etiqueta Fecha límite pierde dorado AA`);
      assert.equal(firstDeadlineTime.color, BLUE, `${name}: fecha límite pierde jerarquía azul`);
      assert.ok(firstDeadlineTime.fontFamily.includes('Instrument Serif'), `${name}: fecha límite pierde tipografía editorial`);
      assert.equal(firstSource.color, BLUE, `${name}: fuente oficial pierde acción azul`);
      assert.ok(method.boxShadow.includes(BLUE) && method.boxShadow.includes(GOLD), `${name}: bloque de método pierde rails`);
      assert.equal(activeContext.color, BLUE, `${name}: navegación contextual pierde azul`);
      assert.ok(activeContext.boxShadow.includes(GOLD), `${name}: navegación contextual pierde cierre dorado`);
      assert.ok(footerRule.includes(BLUE) && footerRule.includes(GOLD), `${name}: footer pierde doble regla`);

      measurements.push({
        name, width, height, overflow, radarToken, directoryToken, methodToken, fontChecks,
        hero, heroTitle, titleStableBefore, titleStableAfter, heroEyebrow, heroNote, heroActions, calendar,
        finder, options, grid, firstCard, firstTop, firstTitle, firstBadge, firstLedger,
        firstDeadline, firstDeadlineTerm, firstDeadlineTime, firstSource, method, activeContext, footer, footerRule,
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
    await stabilizeTypography(interactionPage);

    await interactionPage.locator('[data-radar-search]').fill('KUTXA');
    assert.equal(await interactionPage.locator('[data-radar-item]:visible').count(), 1, 'interaction: búsqueda Kutxa no devuelve una oportunidad');
    assert.equal((await interactionPage.locator('[data-radar-count]').textContent()).trim(), '1 convocatoria visible', 'interaction: singular del contador no corregido');
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
    const emptyStyle = await snapshot(interactionPage.locator('[data-radar-filter-empty]'));
    assert.ok(emptyStyle.boxShadow.includes(BLUE) && emptyStyle.boxShadow.includes(GOLD), 'interaction: empty state pierde rails');
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
    const overflow = await noJsPage.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    assert.ok(overflow <= 1, `no-js: overflow horizontal ${overflow}px`);
    await noJsPage.screenshot({ path: path.join(OUT, 'convocatorias-no-js-390.png'), fullPage: true });
  } catch (error) {
    failures.push({ viewport: 'no-js-mobile-390', width: 390, height: 844, error: error instanceof Error ? error.message : String(error) });
  } finally {
    await noJsContext.close();
  }

  const isolationContext = await prepareContext(browser, { width: 1280, height: 800 });
  const isolationPage = await isolationContext.newPage();
  try {
    const response = await isolationPage.goto(`${ORIGIN}/editoriales/`, { waitUntil: 'networkidle', timeout: 20000 });
    assert.ok(response?.ok(), 'isolation: /editoriales/ no carga');
    assert.equal(await isolationPage.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--radar-blue').trim()), '', 'isolation: Editoriales hereda tokens del radar');
    assert.equal((await isolationPage.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--directory-blue').trim())).toLowerCase(), '#1d4f96', 'isolation: Editoriales pierde sus tokens propios');
    assert.equal(await isolationPage.locator('[data-radar-grid]').count(), 0, 'isolation: Editoriales contiene grid del radar');
    await isolationPage.evaluate(() => window.scrollTo(0, 0));
    await isolationPage.waitForTimeout(50);
    await isolationPage.screenshot({ path: path.join(OUT, 'editoriales-control-1280.png'), fullPage: true });
  } catch (error) {
    failures.push({ viewport: 'editoriales-isolation-1280', width: 1280, height: 800, error: error instanceof Error ? error.message : String(error) });
  } finally {
    await isolationContext.close();
  }
} finally {
  await browser.close();
}

const byName = Object.fromEntries(measurements.map(item => [item.name, item]));
for (const [wider, narrower] of [
  ['layout-901', 'layout-900'],
  ['ledger-861', 'ledger-860'],
  ['layout-641', 'layout-640'],
  ['record-521', 'record-520'],
  ['mobile-390', 'mobile-389'],
]) {
  if (byName[wider] && byName[narrower]) {
    assert.ok(
      parseFloat(byName[narrower].heroTitle.fontSize) <= parseFloat(byName[wider].heroTitle.fontSize) + 0.1,
      `${narrower}: el H1 crece al estrechar desde ${wider}`,
    );
  }
}

fs.writeFileSync(
  path.join(OUT, 'convocatorias-design-report.json'),
  JSON.stringify({ route: '/convocatorias-escritores/', phase: 'visual-system-contract', fixedToday: FIXED_TODAY, viewports: viewports.length, measurements, failures }, null, 2),
);

assert.deepEqual(failures, [], `Convocatorias visual-system failures:\n${JSON.stringify(failures, null, 2)}`);
console.log(`Convocatorias visual-system QA: PASS (${viewports.length} viewports + interaction states + no-JS + Editoriales isolation)`);
