import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/herramientas-hub';
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

function columns(value) {
  return value === 'none' ? 0 : value.split(' ').filter(Boolean).length;
}

async function snapshot(locator) {
  return locator.evaluate(el => {
    const s = getComputedStyle(el);
    return {
      display: s.display,
      gridTemplateColumns: s.gridTemplateColumns,
      color: s.color,
      backgroundColor: s.backgroundColor,
      borderTopWidth: s.borderTopWidth,
      borderBottomWidth: s.borderBottomWidth,
      position: s.position,
    };
  });
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
      assert.equal(await page.locator('h1').count(), 1, `${name}: H1 no único`);
      assert.equal(await page.locator('.section-context [aria-current="page"]').getAttribute('href'), '/herramientas/', `${name}: contexto no marca el hub`);
      assert.notEqual((await snapshot(page.locator('.header-search'))).display, 'none', `${name}: Asistente del header no disponible`);

      const tools = page.locator('[data-tool]');
      const filters = page.locator('.tool-filters button[data-filter]');
      const sections = page.locator('.tools-section[data-tool-section]');
      assert.equal(await tools.count(), 22, `${name}: el hub no conserva 22 herramientas`);
      assert.equal(await filters.count(), 7, `${name}: el finder no conserva siete filtros`);
      assert.equal(await sections.count(), 8, `${name}: secciones de herramientas alteradas`);
      assert.equal((await page.locator('[data-tool-count]').innerText()).trim(), '22 herramientas', `${name}: contador inicial alterado`);
      assert.equal(await page.locator('#directorios .id-card').count(), 2, `${name}: directorios relacionados alterados`);
      assert.equal(await page.locator('#metodo').count(), 1, `${name}: bloque de método ausente`);

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 1, `${name}: overflow horizontal ${overflow}px`);

      const firstGrid = await snapshot(page.locator('.tools-section .id-cards').first());
      const masthead = await snapshot(page.locator('.v1-masthead'));
      const finder = await snapshot(page.locator('.tool-finder'));
      const firstCard = await snapshot(page.locator('[data-tool]').first());

      measurements.push({
        name,
        width,
        height,
        overflow,
        firstGridColumns: columns(firstGrid.gridTemplateColumns),
        firstGridTemplateColumns: firstGrid.gridTemplateColumns,
        masthead,
        finder,
        firstCard,
      });

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
} finally {
  await browser.close();
}

fs.writeFileSync(
  path.join(OUT, 'herramientas-index-design-report.json'),
  `${JSON.stringify({ route: '/herramientas/', viewports, measurements, failures }, null, 2)}\n`,
);

assert.deepEqual(failures, [], `Herramientas hub design baseline failures:\n${JSON.stringify(failures, null, 2)}`);
console.log(`herramientas-index-design-browser: PASS (${viewports.length} viewports)`);
