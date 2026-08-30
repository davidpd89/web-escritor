import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/herramientas-hub';
fs.mkdirSync(OUT, { recursive: true });

const BLUE = 'rgb(29, 79, 150)';
const GOLD = 'rgb(184, 134, 11)';
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

const filterContract = [
  ['revisar', 8, 2],
  ['estructura', 3, 1],
  ['publicar', 8, 3],
  ['investigar', 2, 1],
  ['lectores', 1, 1],
  ['local', 22, 8],
  ['all', 22, 8],
];

function columns(value) {
  return value === 'none' ? 0 : value.split(' ').filter(Boolean).length;
}

async function snapshot(locator, pseudo = null) {
  return locator.evaluate((el, pseudoElement) => {
    const s = getComputedStyle(el, pseudoElement);
    return {
      display: s.display,
      gridTemplateColumns: s.gridTemplateColumns,
      color: s.color,
      backgroundColor: s.backgroundColor,
      boxShadow: s.boxShadow,
      borderRadius: s.borderRadius,
      fontSize: s.fontSize,
      content: s.content,
      counterIncrement: s.counterIncrement,
      position: s.position,
    };
  }, pseudo);
}

async function assertFilters(page, name) {
  for (const [filter, expectedTools, expectedSections] of filterContract) {
    const button = page.locator(`.tool-filters button[data-filter="${filter}"]`);
    await button.click();
    assert.equal(await button.getAttribute('aria-pressed'), 'true', `${name}: ${filter} no queda activo`);
    assert.equal(await page.locator('[data-tool]:not([hidden])').count(), expectedTools, `${name}: ${filter} muestra un número incorrecto de herramientas`);
    assert.equal(await page.locator('[data-tool-section]:not([hidden])').count(), expectedSections, `${name}: ${filter} muestra un número incorrecto de familias`);
    assert.equal(
      (await page.locator('[data-tool-count]').textContent()).trim(),
      `${expectedTools} ${expectedTools === 1 ? 'herramienta' : 'herramientas'}`,
      `${name}: contador incorrecto para ${filter}`,
    );
  }
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
      const response = await page.goto(`${ORIGIN}/herramientas/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      assert.ok(response?.ok(), `${name}: /herramientas/ no carga`);
      await page.evaluate(() => document.fonts?.ready);

      assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'herramientas', `${name}: contexto Herramientas perdido`);
      assert.equal(await page.locator('main#contenido').getAttribute('data-family'), 'tools-hub', `${name}: familia tools-hub perdida`);
      assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'), 'https://davidportodiaz.com/herramientas/', `${name}: canonical alterado`);
      assert.equal(await page.locator('link[href="/assets/herramientas-index.css"]').count(), 1, `${name}: capa visual exclusiva no cargada`);
      assert.equal(await page.locator('h1').count(), 1, `${name}: H1 no único`);
      assert.equal(await page.locator('.section-context [aria-current="page"]').getAttribute('href'), '/herramientas/', `${name}: contexto no marca el hub`);
      assert.notEqual((await snapshot(page.locator('.header-search'))).display, 'none', `${name}: Asistente del header no disponible`);

      const tools = page.locator('[data-tool]');
      const filters = page.locator('.tool-filters button[data-filter]');
      const sections = page.locator('.tools-section[data-tool-section]');
      assert.equal(await tools.count(), 22, `${name}: el hub no conserva 22 herramientas`);
      assert.equal(await filters.count(), 7, `${name}: el finder no conserva siete filtros`);
      assert.equal(await sections.count(), 8, `${name}: secciones de herramientas alteradas`);
      assert.equal(await page.locator('#directorios .id-card').count(), 2, `${name}: directorios relacionados alterados`);
      assert.equal(await page.locator('#metodo').count(), 1, `${name}: bloque de método ausente`);

      const rootToken = await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--tools-blue').trim());
      assert.equal(rootToken.toLowerCase(), '#1d4f96', `${name}: token azul del hub perdido`);

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 1, `${name}: overflow horizontal ${overflow}px`);

      const masthead = await snapshot(page.locator('.v1-masthead'));
      const hero = await snapshot(page.locator('.v1-masthead h1'));
      const finder = await snapshot(page.locator('.tool-finder'));
      const filterGrid = await snapshot(page.locator('.tool-filters'));
      const activeFilter = await snapshot(page.locator('.tool-filters button[data-filter="all"]'));
      const firstSection = await snapshot(sections.first());
      const firstGrid = await snapshot(page.locator('.tools-section .id-cards').first());
      const firstFamilyIndex = await snapshot(page.locator('.tools-section>h2').first(), '::before');
      const firstTitle = await snapshot(page.locator('[data-tool] h3 a').first());
      const firstAction = await snapshot(page.locator('[data-tool] .text-action').first());
      const singleGrid = await snapshot(page.locator('.tools-section').filter({ has: page.locator('.id-card:only-child') }).first().locator('.id-cards'));

      assert.equal(columns(masthead.gridTemplateColumns), 1, `${name}: masthead no es de una columna`);
      assert.equal(hero.color, BLUE, `${name}: H1 no usa azul editorial`);
      assert.ok(finder.boxShadow.includes(BLUE) && finder.boxShadow.includes(GOLD), `${name}: finder pierde rail azul/dorado`);
      assert.equal(activeFilter.backgroundColor, BLUE, `${name}: filtro activo no usa azul`);
      assert.equal(activeFilter.color, 'rgb(255, 255, 255)', `${name}: filtro activo pierde contraste blanco`);
      assert.equal(firstTitle.color, BLUE, `${name}: títulos de herramienta no usan azul`);
      assert.equal(firstAction.color, BLUE, `${name}: acción de herramienta no usa azul`);
      assert.equal(firstAction.backgroundColor, TRANSPARENT, `${name}: acción vuelve a botón relleno`);
      assert.equal(firstAction.borderRadius, '0px', `${name}: acción vuelve a tratamiento SaaS redondeado`);
      assert.ok(firstSection.counterIncrement.includes('tools-family'), `${name}: contador de familias no incrementa`);
      assert.ok(firstFamilyIndex.content.includes('counter(tools-family') && firstFamilyIndex.content.includes('/'), `${name}: expresión visual de numeración de familias perdida`);

      const expectedFilterColumns = width > 900 ? 4 : width > 389 ? 2 : 1;
      const expectedToolColumns = width > 900 ? 3 : width > 640 ? 2 : 1;
      const expectedFamilyColumns = width > 767 ? 2 : 1;
      const expectedSingleColumns = width > 900 ? 2 : 1;
      assert.equal(columns(filterGrid.gridTemplateColumns), expectedFilterColumns, `${name}: seam de filtros incorrecto`);
      assert.equal(columns(firstGrid.gridTemplateColumns), expectedToolColumns, `${name}: seam de catálogo incorrecto`);
      assert.equal(columns(firstSection.gridTemplateColumns), expectedFamilyColumns, `${name}: seam de cabecera de familia incorrecto`);
      assert.equal(columns(singleGrid.gridTemplateColumns), expectedSingleColumns, `${name}: sección de herramienta única no tiene cadencia deliberada`);

      await assertFilters(page, name);

      measurements.push({
        name,
        width,
        height,
        overflow,
        filterColumns: columns(filterGrid.gridTemplateColumns),
        toolColumns: columns(firstGrid.gridTemplateColumns),
        familyColumns: columns(firstSection.gridTemplateColumns),
        singleToolColumns: columns(singleGrid.gridTemplateColumns),
        familyCounter: firstSection.counterIncrement,
        familyIndexExpression: firstFamilyIndex.content,
        masthead,
        finder,
        firstTitle,
        firstAction,
      });

      await page.locator('.tool-filters button[data-filter="all"]').click();
      await page.evaluate(() => {
        if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
        window.scrollTo(0, 0);
      });
      await page.waitForTimeout(50);
      await page.screenshot({ path: path.join(OUT, `herramientas-index-${name}.png`), fullPage: true });
    } catch (error) {
      failures.push({ viewport: name, width, height, error: error instanceof Error ? error.message : String(error) });
    } finally {
      await context.close();
    }
  }

  const isolationContext = await browser.newContext({ viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce' });
  const isolationPage = await isolationContext.newPage();
  try {
    const response = await isolationPage.goto(`${ORIGIN}/herramientas/manuscrito/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    assert.ok(response?.ok(), 'isolation: /herramientas/manuscrito/ no carga');
    assert.equal(await isolationPage.locator('link[href="/assets/herramientas-index.css"]').count(), 0, 'isolation: hoja del hub contamina una herramienta individual');
    const token = await isolationPage.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--tools-blue').trim());
    assert.equal(token, '', 'isolation: token del hub filtra a herramientas individuales');
  } catch (error) {
    failures.push({ viewport: 'tool-isolation', width: 1280, height: 800, error: error instanceof Error ? error.message : String(error) });
  } finally {
    await isolationContext.close();
  }
} finally {
  await browser.close();
}

fs.writeFileSync(
  path.join(OUT, 'herramientas-index-design-report.json'),
  `${JSON.stringify({ route: '/herramientas/', viewports, measurements, filterContract, failures }, null, 2)}\n`,
);

assert.deepEqual(failures, [], `Herramientas hub visual-system failures:\n${JSON.stringify(failures, null, 2)}`);
console.log(`herramientas-index-design-browser: PASS (${viewports.length} viewports + tool isolation)`);
