import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/editoriales-index';
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
  ['tablet-768', 768, 1024],
  ['tablet-767', 767, 900],
  ['layout-641', 641, 900],
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

function columnCount(value) {
  if (!value || value === 'none') return 0;
  return value.trim().split(/\s+/).length;
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

      const directoryToken = await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--directory-blue').trim());
      const methodToken = await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--method-blue').trim());
      assert.equal(directoryToken.toLowerCase(), '#1d4f96', `${name}: el hub no activa sus tokens de directorio`);
      assert.equal(methodToken, '', `${name}: el hub hereda tokens exclusivos de Metodología`);

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 1, `${name}: overflow horizontal ${overflow}px`);

      const hero = await snapshot(page.locator('.tool-hero'));
      const heroTitle = await snapshot(page.locator('.tool-hero h1'));
      const heroEyebrow = await snapshot(page.locator('.tool-hero .eyebrow'));
      const heroNote = await snapshot(page.locator('.tool-hero > .tool-note'));
      const finder = await snapshot(page.locator('.tool-finder'));
      const options = await snapshot(page.locator('.tool-options'));
      const directory = await snapshot(page.locator('main#contenido > .v1-section').last());
      const cardsWrap = await snapshot(page.locator('[data-editoriales-directory] .id-cards'));
      const firstCard = await snapshot(cards.first());
      const firstCardHead = await snapshot(cards.first().locator('.editorial-card__head'));
      const firstCardTitle = await snapshot(cards.first().locator('h2'));
      const firstBadge = await snapshot(cards.first().locator('.editorial-badge'));
      const firstGenres = await snapshot(cards.first().locator('.editorial-genres'));
      const firstVerified = await snapshot(cards.first().locator('.editorial-verified'));
      const firstAction = await snapshot(cards.first().locator('.id-card__actions .text-action'));
      const activeContext = await snapshot(page.locator('.section-context [aria-current="page"]'));
      const footer = await snapshot(page.locator('.site-footer'));
      const ordinal = await cards.first().evaluate(el => ({
        content: getComputedStyle(el, '::before').content,
        color: getComputedStyle(el, '::before').color,
      }));
      const footerRule = await page.locator('.site-footer').evaluate(el => getComputedStyle(el, '::before').backgroundImage);

      assert.equal(heroTitle.color, BLUE, `${name}: H1 pierde el azul editorial`);
      assert.ok(hero.backgroundImage.includes(BLUE) && hero.backgroundImage.includes(GOLD), `${name}: hero pierde la doble regla azul/dorado`);
      assert.equal(heroEyebrow.color, GOLD_TEXT, `${name}: apertura manuscrita pierde el dorado AA`);
      assert.ok(heroEyebrow.fontFamily.includes('Yellowtail'), `${name}: apertura deja de ser manuscrita`);
      assert.ok(heroNote.boxShadow.includes(BLUE) && heroNote.boxShadow.includes(GOLD), `${name}: aviso de confianza pierde los rails`);
      assert.equal(columnCount(hero.gridTemplateColumns), width > 900 ? 2 : 1, `${name}: seam 901/900 del hero incorrecto`);

      assert.equal(finder.display, 'grid', `${name}: mesa de consulta deja de ser grid`);
      assert.ok(finder.boxShadow.includes(BLUE) && finder.boxShadow.includes(GOLD), `${name}: mesa de consulta pierde el rail azul/dorado`);
      assert.equal(columnCount(options.gridTemplateColumns), width > 900 ? 3 : width > 640 ? 2 : 1, `${name}: seam de filtros incorrecto`);

      assert.equal(firstCard.display, 'grid', `${name}: expediente deja de ser grid`);
      assert.equal(columnCount(firstCard.gridTemplateColumns), width > 640 ? 2 : 1, `${name}: seam 641/640 del expediente incorrecto`);
      assert.equal(firstCardTitle.color, BLUE, `${name}: título de editorial pierde el azul`);
      assert.equal(firstBadge.color, BLUE_DEEP, `${name}: badge abierto pierde el azul profundo`);
      assert.equal(firstBadge.backgroundColor, PALE, `${name}: badge abierto pierde el fondo pálido`);
      assert.ok(firstAction.fontFamily.includes('Yellowtail'), `${name}: acción del expediente deja de ser manuscrita`);
      assert.equal(firstAction.color, BLUE, `${name}: acción del expediente pierde el azul`);
      assert.ok(ordinal.content.includes('publisher-record'), `${name}: expediente pierde la numeración editorial`);
      assert.equal(ordinal.color, GOLD_TEXT, `${name}: numeración pierde el dorado AA`);

      assert.equal(activeContext.color, BLUE, `${name}: navegación contextual pierde el azul`);
      assert.ok(activeContext.boxShadow.includes(GOLD), `${name}: contexto activo pierde el cierre dorado`);
      assert.ok(footerRule.includes(BLUE) && footerRule.includes(GOLD), `${name}: footer pierde la doble regla editorial`);

      measurements.push({
        name, width, height, overflow, directoryToken, methodToken,
        hero, heroTitle, heroEyebrow, heroNote, finder, options, directory, cardsWrap,
        firstCard, firstCardHead, firstCardTitle, firstBadge, firstGenres, firstVerified, firstAction,
        ordinal, activeContext, footer, footerRule,
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
    assert.equal(await interactionPage.locator('[data-editorial-card]:visible h2').textContent(), 'Duermevela Ediciones', 'interaction: filtro closed devuelve la editorial incorrecta');
    await interactionPage.evaluate(() => {
      if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
      window.scrollTo(0, 0);
    });
    await interactionPage.waitForTimeout(50);
    await interactionPage.screenshot({ path: path.join(OUT, 'editoriales-filtered-390.png'), fullPage: true });

    await interactionPage.locator('[data-editoriales-reset]').click();
    await interactionPage.locator('[data-editoriales-search]').fill('zzzz-sin-resultados');
    assert.equal(await interactionPage.locator('[data-editoriales-empty]').isVisible(), true, 'interaction: empty state no aparece');
    const emptyStyle = await snapshot(interactionPage.locator('[data-editoriales-empty]'));
    assert.ok(emptyStyle.boxShadow.includes(BLUE) && emptyStyle.boxShadow.includes(GOLD), 'interaction: empty state pierde los rails del registro');
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
    assert.equal(await isolationPage.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--directory-blue').trim()), '', 'isolation: Minotauro hereda tokens del directorio');
    assert.equal(await isolationPage.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--method-blue').trim()), '', 'isolation: Minotauro hereda tokens de Metodología');
    const detailOrdinal = await isolationPage.locator('main#contenido .tool-findings-block').first().evaluate(el => getComputedStyle(el, '::before').content);
    assert.ok(!detailOrdinal.includes('publisher-record'), 'isolation: ficha individual hereda numeración del directorio');
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

const byName = Object.fromEntries(measurements.map(item => [item.name, item]));
for (const [wider, narrower] of [['layout-901', 'layout-900'], ['tablet-768', 'tablet-767'], ['layout-641', 'mid-640'], ['mobile-390', 'mobile-389']]) {
  if (byName[wider] && byName[narrower]) {
    assert.ok(
      parseFloat(byName[narrower].heroTitle.fontSize) <= parseFloat(byName[wider].heroTitle.fontSize) + 0.1,
      `${narrower}: el H1 crece al estrechar desde ${wider}`,
    );
  }
}

fs.writeFileSync(
  path.join(OUT, 'editoriales-index-design-report.json'),
  JSON.stringify({ route: '/editoriales/', phase: 'visual-system-contract', viewports: viewports.length, measurements, failures }, null, 2),
);

assert.deepEqual(failures, [], `Editoriales visual-system failures:\n${JSON.stringify(failures, null, 2)}`);
console.log(`Editoriales visual-system QA: PASS (${viewports.length} viewports + interaction states + publisher isolation)`);
