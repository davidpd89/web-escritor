import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/metodologia-editorial';
fs.mkdirSync(OUT, { recursive: true });

const BLUE = 'rgb(29, 79, 150)';
const GOLD = 'rgb(184, 134, 11)';
const GOLD_TEXT = 'rgb(155, 110, 0)';

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
    return {
      display: s.display,
      gridTemplateColumns: s.gridTemplateColumns,
      color: s.color,
      backgroundColor: s.backgroundColor,
      backgroundImage: s.backgroundImage,
      borderTopWidth: s.borderTopWidth,
      borderBottomWidth: s.borderBottomWidth,
      borderRadius: s.borderRadius,
      boxShadow: s.boxShadow,
      fontSize: s.fontSize,
      lineHeight: s.lineHeight,
      maxWidth: s.maxWidth,
      position: s.position,
      counterIncrement: s.counterIncrement,
    };
  });
}

function columnCount(value) {
  if (!value || value === 'none') return 0;
  return value.trim().split(/\s+/).length;
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
      const response = await page.goto(`${ORIGIN}/metodologia-editorial/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      assert.ok(response?.ok(), `${name}: /metodologia-editorial/ no carga`);
      await page.evaluate(() => document.fonts?.ready);
      await page.waitForTimeout(120);

      assert.equal(await page.locator('html').getAttribute('data-editorial-context'), 'herramientas', `${name}: contexto Herramientas perdido`);
      assert.equal(await page.locator('main#contenido').getAttribute('data-family'), 'tool', `${name}: familia heredada alterada`);
      assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'), 'https://davidportodiaz.com/metodologia-editorial/', `${name}: canonical alterado`);
      assert.equal(await page.locator('h1').count(), 1, `${name}: H1 no único`);
      assert.equal((await page.locator('h1').textContent()).trim(), 'Cómo se verifica esta información.', `${name}: H1 alterado`);
      assert.equal(await page.locator('.section-context [aria-current="page"]').getAttribute('href'), '/metodologia-editorial/', `${name}: contexto no marca Metodología`);
      assert.equal(await page.locator('.tool-findings-block').count(), 5, `${name}: no conserva cinco bloques metodológicos`);
      assert.equal(await page.locator('.spec-ledger .editorial-fact').count(), 5, `${name}: ledger de estados alterado`);
      assert.equal(await page.locator('.tool-note').count(), 1, `${name}: nota legal ausente`);
      assert.equal(await page.locator('main#contenido a[href="mailto:davidportodiaz@gmail.com"]').count(), 1, `${name}: canal de correcciones alterado`);

      const statusTerms = await page.locator('.spec-ledger dt').allTextContents();
      assert.deepEqual(statusTerms.map(value => value.trim()), ['open', 'closed', 'indirect', 'award_only', 'unknown'], `${name}: estados cerrados alterados`);

      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 1, `${name}: overflow horizontal ${overflow}px`);

      const methodToken = await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--method-blue').trim());
      const hero = await snapshot(page.locator('.tool-hero'));
      const heroTitle = await snapshot(page.locator('.tool-hero h1'));
      const activeContext = await snapshot(page.locator('.section-context [aria-current="page"]'));
      const section = await snapshot(page.locator('main#contenido > .v1-section'));
      const firstFinding = await snapshot(page.locator('.tool-findings-block').first());
      const firstFindingTitle = await snapshot(page.locator('.tool-findings-block h2').first());
      const ledger = await snapshot(page.locator('.spec-ledger'));
      const firstFact = await snapshot(page.locator('.editorial-fact').first());
      const firstStateTerm = await snapshot(page.locator('.spec-ledger dt').first());
      const note = await snapshot(page.locator('.tool-note'));
      const stepMarker = await page.locator('.tool-findings-block h2').first().evaluate(el => getComputedStyle(el, '::before').content);

      assert.equal(methodToken.toLowerCase(), '#1d4f96', `${name}: el scope de Metodología no activa sus tokens`);
      assert.equal(heroTitle.color, BLUE, `${name}: H1 pierde el azul editorial`);
      assert.ok(hero.backgroundImage.includes('rgb(29, 79, 150)') && hero.backgroundImage.includes('rgb(184, 134, 11)'), `${name}: hero pierde la doble regla azul/dorado`);
      assert.equal(activeContext.color, BLUE, `${name}: navegación contextual pierde el azul`);
      assert.ok(activeContext.boxShadow.includes(GOLD), `${name}: navegación contextual pierde el cierre dorado`);
      assert.equal(firstFinding.display, 'grid', `${name}: los pasos dejan de ser una rejilla editorial`);
      assert.ok(firstFinding.counterIncrement.includes('method-step'), `${name}: los pasos pierden el contador`);
      assert.ok(stepMarker.includes('counter(method-step'), `${name}: la numeración 01–05 deja de usar el contador editorial`);
      assert.equal(firstFindingTitle.color, BLUE, `${name}: títulos de paso pierden el azul`);
      assert.equal(firstStateTerm.color, GOLD_TEXT, `${name}: texto dorado pequeño pierde el tono AA`);
      assert.equal(columnCount(firstFinding.gridTemplateColumns), width > 900 ? 2 : 1, `${name}: seam 901/900 del protocolo incorrecto`);
      assert.equal(columnCount(ledger.gridTemplateColumns), width > 767 ? 2 : 1, `${name}: seam 768/767 del diccionario de estados incorrecto`);
      assert.equal(columnCount(firstFact.gridTemplateColumns), width > 640 ? 2 : 1, `${name}: seam 640 del registro de estado incorrecto`);
      assert.ok(note.boxShadow.includes(BLUE) && note.boxShadow.includes(GOLD), `${name}: cierre de confianza pierde los rails azul/dorado`);

      measurements.push({ name, width, height, overflow, methodToken, hero, heroTitle, activeContext, section, firstFinding, firstFindingTitle, ledger, firstFact, firstStateTerm, note, stepMarker });

      await page.evaluate(() => {
        if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
        window.scrollTo(0, 0);
      });
      await page.waitForTimeout(50);
      await page.screenshot({ path: path.join(OUT, `metodologia-editorial-${name}.png`), fullPage: true });
    } catch (error) {
      failures.push({ viewport: name, width, height, error: error instanceof Error ? error.message : String(error) });
    } finally {
      await context.close();
    }
  }

  const isolationContext = await browser.newContext({ viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce' });
  const isolationPage = await isolationContext.newPage();
  try {
    const response = await isolationPage.goto(`${ORIGIN}/editoriales/minotauro/`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    assert.ok(response?.ok(), 'isolation: /editoriales/minotauro/ no carga');
    await isolationPage.evaluate(() => document.fonts?.ready);
    await isolationPage.waitForTimeout(120);

    const leakedToken = await isolationPage.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--method-blue').trim());
    const publisherStepMarker = await isolationPage.locator('.tool-findings-block h2').first().evaluate(el => getComputedStyle(el, '::before').content);
    assert.equal(leakedToken, '', 'isolation: una ficha editorial hereda los tokens exclusivos de Metodología');
    assert.ok(!publisherStepMarker.includes('method-step'), 'isolation: una ficha editorial hereda la numeración del protocolo');

    await isolationPage.evaluate(() => window.scrollTo(0, 0));
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
if (byName['tablet-768'] && byName['tablet-767']) {
  assert.ok(parseFloat(byName['tablet-767'].heroTitle.fontSize) <= parseFloat(byName['tablet-768'].heroTitle.fontSize) + 0.1, '767px: el H1 crece al estrechar el viewport');
}
if (byName['mobile-390'] && byName['mobile-389']) {
  assert.ok(parseFloat(byName['mobile-389'].heroTitle.fontSize) <= parseFloat(byName['mobile-390'].heroTitle.fontSize) + 0.1, '389px: el H1 crece al estrechar el viewport');
}

fs.writeFileSync(
  path.join(OUT, 'metodologia-editorial-design-report.json'),
  JSON.stringify({ route: '/metodologia-editorial/', viewports: viewports.length, measurements, failures }, null, 2),
);

assert.deepEqual(failures, [], `Metodología editorial visual-system failures:\n${JSON.stringify(failures, null, 2)}`);
console.log(`Metodología editorial visual-system QA: PASS (${viewports.length} viewports + publisher isolation)`);
