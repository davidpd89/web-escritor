import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.RECOMMENDATIONS_ARTIFACT_DIR || '.ci/reading-catalogue';
await fs.mkdir(OUT, { recursive: true });
const fixturePath = `${OUT}/fixture.json`;
execFileSync(process.env.PYTHON || 'python', ['tests/test-reading-catalogue.py', '--browser-fixture', fixturePath], { stdio: 'inherit' });
const fixture = JSON.parse(await fs.readFile(fixturePath, 'utf8'));
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const width of [320, 390, 768, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(`${BASE}/recomendaciones/`);
    await page.waitForSelector('[data-catalogue-filters]:visible');
    assert.match(await page.locator('h1').innerText(), /Recomendaciones de lectura/);
    assert.equal(await page.locator('[data-catalogue-book]').count(), 0);
    assert.match(await page.locator('[data-catalogue-empty]').innerText(), /preparando/);
    assert.equal(await page.locator('.section-context__links a').count(), 2);
    await page.locator('[data-filter="genero"]').selectOption('romantasy');
    await page.locator('[data-filter="temporada"]').selectOption('halloween');
    assert.equal(await page.locator('[data-catalogue-count]').innerText(), '0 libros');
    await page.getByRole('button', { name: 'Limpiar filtros' }).click();
    assert.equal(await page.locator('[data-filter="genero"]').inputValue(), '');
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await page.evaluate(() => { document.activeElement?.blur(); window.scrollTo({ top: 0, behavior: 'instant' }); });
    await page.waitForFunction(() => window.scrollY === 0);
    await page.screenshot({ path: `${OUT}/catalogue-${width}.png`, fullPage: true });
    await page.goto(`${BASE}/cuaderno/`);
    assert.equal(await page.locator('.cuaderno-feature h2 a, .cuaderno-entry h3 a').count(), 6);
    await page.getByRole('link', { name: 'Recomendaciones de lectura', exact: true }).first().click();
    assert.equal(new URL(page.url()).pathname, '/recomendaciones/');
    assert.deepEqual(errors, []);
    await context.close();
  }
  // Rendered data uses intercepted, isolated fixtures; no synthetic books on the site.
  const context = await browser.newContext({ viewport: { width: 390, height: 900 }, reducedMotion: 'reduce' });
  await context.route('**/recomendaciones/', route => route.fulfill({ contentType: 'text/html; charset=utf-8', body: fixture.hub }));
  await context.route('**/recomendaciones/libros/contrato-uno/', route => route.fulfill({ contentType: 'text/html; charset=utf-8', body: fixture.book }));
  await context.route('**/assets/reading-covers/*.png', route => route.fulfill({ contentType: 'image/png', body: Buffer.from(fixture.cover, 'base64') }));
  const page = await context.newPage();
  await page.clock.install({ time: new Date('2026-10-20T12:00:00Z') });
  await page.goto(`${BASE}/recomendaciones/`);
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 2);
  await page.locator('[data-filter="genero"]').selectOption('romantasy');
  await page.locator('[data-filter="temporada"]').selectOption('halloween');
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 1);
  const href = await page.locator('[data-catalogue-book]:visible h3 a').getAttribute('href');
  await page.locator('[data-filter="genero"]').selectOption('fantasia');
  assert.equal(await page.locator('[data-catalogue-book]:visible h3 a').getAttribute('href'), href);
  await page.locator('[data-filter="q"]').fill('TITULO');
  await page.locator('[data-filter="q"]').press('Enter');
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 1);
  await page.reload();
  assert.equal(await page.locator('[data-filter="q"]').inputValue(), 'TITULO');
  await page.getByRole('button', { name: 'Limpiar filtros' }).click();
  await page.locator('[data-filter="novedad"]').selectOption('180');
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 1);
  await page.clock.setSystemTime(new Date('2027-10-20T12:00:00Z'));
  await page.evaluate(() => window.dispatchEvent(new Event('pageshow')));
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 0);
  await page.getByRole('button', { name: 'Limpiar filtros' }).click();
  await page.locator('[data-filter="q"]').fill('zzzz');
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 0);
  assert(await page.locator('[data-catalogue-empty]').isVisible());
  await page.goto(`${BASE}${href}`);
  assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'), `https://davidportodiaz.com${href}`);
  assert.equal(await page.locator('main h1').innerText(), 'Título de prueba técnica');
  await page.locator('.catalogue-book-cover').evaluate(img => img.decode());
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
  await page.screenshot({ path: `${OUT}/book-fixture-mobile.png`, fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({ path: `${OUT}/book-fixture-desktop.png`, fullPage: true });
  await page.addInitScript(() => {
    window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
    Object.defineProperty(window, 'speechSynthesis', { value: {
      cancel() { window.__stopped = true; },
      speak(utterance) { window.__spoken = utterance.text; }
    }, configurable: true });
  });
  await page.reload();
  await page.getByRole('button', { name: 'Escuchar descripción' }).click();
  assert.match(await page.evaluate(() => window.__spoken), /Descripción original/);
  assert(await page.getByRole('button', { name: 'Escuchar descripción' }).isDisabled());
  await page.getByRole('button', { name: 'Detener lectura' }).click();
  assert(await page.getByRole('button', { name: 'Escuchar descripción' }).isEnabled());
  assert.match(await page.locator('[data-catalogue-speech-status]').innerText(), /detenida/);
  await context.close();
  const nojs = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 900 } });
  const staticPage = await nojs.newPage();
  await staticPage.goto(`${BASE}/recomendaciones/`);
  assert(await staticPage.locator('a[href="/recomendaciones/portal-fantasy-espanol/"]').first().isVisible());
  assert(await staticPage.locator('[data-filter="genero"]').isDisabled());
  await nojs.route('**/recomendaciones/', route => route.fulfill({ contentType: 'text/html; charset=utf-8', body: fixture.hub }));
  await staticPage.reload();
  assert.equal(await staticPage.locator('[data-catalogue-book]').count(), 2);
  assert.equal(await staticPage.locator('[data-catalogue-book] h3 a').first().getAttribute('href'), href);
  await nojs.close();
  console.log('PASS catálogo navegador: 4 tamaños, vacío real, filtros combinados, URL única, teclado, novedades, fichas y sin JS.');
} finally {
  await browser.close();
}
