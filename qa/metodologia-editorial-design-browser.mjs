import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/metodologia-editorial';
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
    return {
      display: s.display,
      gridTemplateColumns: s.gridTemplateColumns,
      color: s.color,
      backgroundColor: s.backgroundColor,
      borderTopWidth: s.borderTopWidth,
      borderBottomWidth: s.borderBottomWidth,
      borderRadius: s.borderRadius,
      boxShadow: s.boxShadow,
      fontSize: s.fontSize,
      lineHeight: s.lineHeight,
      maxWidth: s.maxWidth,
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

      const hero = await snapshot(page.locator('.tool-hero'));
      const heroTitle = await snapshot(page.locator('.tool-hero h1'));
      const section = await snapshot(page.locator('main#contenido > .v1-section'));
      const firstFinding = await snapshot(page.locator('.tool-findings-block').first());
      const ledger = await snapshot(page.locator('.spec-ledger'));
      const firstFact = await snapshot(page.locator('.editorial-fact').first());
      const note = await snapshot(page.locator('.tool-note'));

      measurements.push({ name, width, height, overflow, hero, heroTitle, section, firstFinding, ledger, firstFact, note });

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
} finally {
  await browser.close();
}

fs.writeFileSync(
  path.join(OUT, 'metodologia-editorial-design-report.json'),
  JSON.stringify({ route: '/metodologia-editorial/', viewports: viewports.length, measurements, failures }, null, 2),
);

assert.deepEqual(failures, [], `Metodología editorial baseline failures:\n${JSON.stringify(failures, null, 2)}`);
console.log(`Metodología editorial baseline: PASS (${viewports.length} viewports)`);
