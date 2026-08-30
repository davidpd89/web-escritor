import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/editoriales-index';
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

const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}),
});

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
      const response = await page.goto(`${ORIGIN}/editoriales/`, { waitUntil: 'networkidle', timeout: 20000 });
      assert.ok(response?.ok(), `${name}: /editoriales/ no carga`);
      await page.evaluate(() => document.fonts?.ready);
      await page.waitForTimeout(120);

      assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'herramientas', `${name}: contexto Herramientas perdido`);
      assert.equal(await page.locator('main#contenido').getAttribute('data-family'), 'tool', `${name}: familia tool alterada`);
      assert.equal(await page.locator('main#contenido').getAttribute('data-editoriales-directory'), '', `${name}: marcador de directorio ausente`);
      assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'), 'https://davidportodiaz.com/editoriales/', `${name}: canonical alterado`);
      assert.equal(await page.locator('h1').count(), 1, `${name}: H1 no único`);
      assert.equal((await page.locator('h1').textContent()).trim(), 'Editoriales y recepción de manuscritos, verificadas.', `${name}: H1 alterado`);
      assert.equal(await page.locator('.section-context [aria-current="page"]').getAttribute('href'), '/editoriales/', `${name}: contexto no marca Editoriales`);

      const cards = page.locator('[data-editorial-card]');
      assert.equal(await cards.count(), 3, `${name}: directorio ya no conserva tres fichas`);
      assert.deepEqual(await cards.evaluateAll(nodes => nodes.map(node => ({
        name: node.getAttribute('data-name'),
        status: node.getAttribute('data-status'),
        direct: node.getAttribute('data-direct'),
      }))), [
        { name: 'Minotauro', status: 'open', direct: 'true' },
        { name: 'Nocturna Ediciones', status: 'open', direct: 'true' },
        { name: 'Duermevela Ediciones', status: 'closed', direct: 'false' },
      ], `${name}: datos cerrados de las fichas alterados`);

      assert.equal(await page.locator('[data-editoriales-search]').count(), 1, `${name}: buscador ausente`);
      assert.equal(await page.locator('[data-editoriales-genre]').count(), 1, `${name}: filtro de género ausente`);
      assert.equal(await page.locator('[data-editoriales-status]').count(), 1, `${name}: filtro de estado ausente`);
      assert.equal(await page.locator('[data-editoriales-direct]').count(), 1, `${name}: filtro de envío directo ausente`);
      assert.equal(await page.locator('[data-editoriales-count]').count(), 1, `${name}: contador de resultados ausente`);

      const methodToken = await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--method-blue').trim());
      assert.equal(methodToken, '', `${name}: el hub hereda tokens exclusivos de Metodología`);

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 1, `${name}: overflow horizontal ${overflow}px`);

      const hero = await snapshot(page.locator('.tool-hero'));
      const heroTitle = await snapshot(page.locator('.tool-hero h1'));
      const heroEyebrow = await snapshot(page.locator('.tool-hero .eyebrow'));
      const finder = await snapshot(page.locator('.tool-finder'));
      const options = await snapshot(page.locator('.tool-options'));
      const directory = await snapshot(page.locator('main#contenido > .v1-section').last());
      const cardsWrap = await snapshot(page.locator('[data-editoriales-directory] .id-cards'));
      const firstCard = await snapshot(cards.first());
      const firstCardHead = await snapshot(cards.first().locator('.editorial-card__head'));
      const firstBadge = await snapshot(cards.first().locator('.editorial-badge'));
      const firstGenres = await snapshot(cards.first().locator('.editorial-genres'));
      const firstVerified = await snapshot(cards.first().locator('.editorial-verified'));
      const activeContext = await snapshot(page.locator('.section-context [aria-current="page"]'));
      const footer = await snapshot(page.locator('.site-footer'));

      measurements.push({
        name, width, height, overflow, methodToken,
        hero, heroTitle, heroEyebrow, finder, options, directory, cardsWrap,
        firstCard, firstCardHead, firstBadge, firstGenres, firstVerified, activeContext, footer,
      });

      await page.evaluate(() => {
        if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
        window.scrollTo(0, 0);
      });
      await page.waitForTimeout(50);
      await page.screenshot({ path: path.join(OUT, `editoriales-${name}.png`), fullPage: true });
    } catch (error) {
      failures.push({ viewport: name, width, height, error: error instanceof Error ? error.message : String(error) });
    } finally {
      await context.close();
    }
  }

  const interactionContext = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
  await interactionContext.addInitScript(() => {
    try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {}
  });
  const interactionPage = await interactionContext.newPage();
  try {
    const response = await interactionPage.goto(`${ORIGIN}/editoriales/`, { waitUntil: 'networkidle', timeout: 20000 });
    assert.ok(response?.ok(), 'interaction: /editoriales/ no carga');
    await interactionPage.locator('[data-editoriales-status]').selectOption('closed');
    assert.equal(await interactionPage.locator('[data-editorial-card]:visible').count(), 1, 'interaction: filtro closed deja de devolver una ficha');
    assert.equal((await interactionPage.locator('[data-editoriales-count]').textContent()).trim(), '1 editorial', 'interaction: contador filtrado incorrecto');
    await interactionPage.evaluate(() => {
      if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
      window.scrollTo(0, 0);
    });
    await interactionPage.waitForTimeout(50);
    await interactionPage.screenshot({ path: path.join(OUT, 'editoriales-filtered-390.png'), fullPage: true });

    await interactionPage.locator('[data-editoriales-reset]').click();
    await interactionPage.locator('[data-editoriales-search]').fill('zzzz-sin-resultados');
    assert.equal(await interactionPage.locator('[data-editoriales-empty]').isVisible(), true, 'interaction: empty state no aparece');
    await interactionPage.evaluate(() => {
      if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
      window.scrollTo(0, 0);
    });
    await interactionPage.waitForTimeout(50);
    await interactionPage.screenshot({ path: path.join(OUT, 'editoriales-empty-390.png'), fullPage: true });
  } catch (error) {
    failures.push({ viewport: 'interaction-mobile-390', width: 390, height: 844, error: error instanceof Error ? error.message : String(error) });
  } finally {
    await interactionContext.close();
  }

  const isolationContext = await browser.newContext({ viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce' });
  await isolationContext.addInitScript(() => {
    try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {}
  });
  const isolationPage = await isolationContext.newPage();
  try {
    const response = await isolationPage.goto(`${ORIGIN}/editoriales/minotauro/`, { waitUntil: 'networkidle', timeout: 20000 });
    assert.ok(response?.ok(), 'isolation: /editoriales/minotauro/ no carga');
    assert.equal(await isolationPage.locator('main#contenido').getAttribute('data-editoriales-directory'), null, 'isolation: una ficha individual finge ser el directorio');
    assert.equal(await isolationPage.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--method-blue').trim()), '', 'isolation: Minotauro hereda tokens de Metodología');
    await isolationPage.evaluate(() => window.scrollTo(0, 0));
    await isolationPage.waitForTimeout(50);
    await isolationPage.screenshot({ path: path.join(OUT, 'publisher-control-1280.png'), fullPage: true });
  } catch (error) {
    failures.push({ viewport: 'publisher-isolation-1280', width: 1280, height: 800, error: error instanceof Error ? error.message : String(error) });
  } finally {
    await isolationContext.close();
  }
} finally {
  await browser.close();
}

fs.writeFileSync(
  path.join(OUT, 'editoriales-index-design-report.json'),
  JSON.stringify({ route: '/editoriales/', phase: 'inherited-baseline', viewports: viewports.length, measurements, failures }, null, 2),
);

assert.deepEqual(failures, [], `Editoriales inherited-baseline failures:\n${JSON.stringify(failures, null, 2)}`);
console.log(`Editoriales inherited baseline: PASS (${viewports.length} viewports + interaction states + publisher isolation)`);
