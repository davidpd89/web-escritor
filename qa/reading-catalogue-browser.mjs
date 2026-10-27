import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.RECOMMENDATIONS_ARTIFACT_DIR || '.ci/reading-catalogue';
const publicData = JSON.parse(await fs.readFile('data/reading-catalogue.json', 'utf8'));
const realCount = publicData.libros.filter(b => b.estado === 'publicado').length;
await fs.mkdir(OUT, { recursive: true });
const fixturePath = `${OUT}/fixture.json`;
execFileSync(process.env.PYTHON || 'python', ['tests/test-reading-catalogue.py', '--browser-fixture', fixturePath], { stdio: 'inherit' });
const fixture = JSON.parse(await fs.readFile(fixturePath, 'utf8'));
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const width of [320, 390, 768, 1024, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce' });
    // El popup de newsletter se abre por temporizador en /cuaderno/ y tapa el clic en runners lentos.
    await context.addInitScript(() => { try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {} });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(`${BASE}/recomendaciones/`);
    await page.waitForSelector('[data-catalogue-filters]:visible');
    assert.match(await page.locator('h1').innerText(), /Libros recomendados/);
    assert.equal(await page.locator('[data-catalogue-book]').count(), realCount);
    assert(await page.locator('[data-catalogue-empty]').isHidden());
    assert.deepEqual(await page.locator('.section-context__links a').allInnerTexts(), ['Catálogo', 'Autores', 'Editoriales', 'Concursos']);
    await page.locator('details[data-facet-group="genero"]').evaluate(d => { d.open = true; });
    // Sin libros compatibles la opción queda desactivada en lugar de llevar a una página vacía.
    assert(await page.locator('input[data-facet="genero"][value="romantasy"]').isDisabled());
    await page.locator('input[data-facet="grupo"][value="cocina"]').check();
    await page.getByRole('button', { name: 'Restablecer' }).click();
    assert.equal(await page.locator('input[data-facet]:checked').count(), 0);
    await page.waitForFunction(n => document.querySelectorAll('[data-catalogue-book]:not([hidden])').length === Math.min(n,24), realCount);
    assert.equal(await page.locator('[data-catalogue-book]:visible').count(), Math.min(realCount,24));
    await page.getByRole('button', { name: 'Buscar libros', exact: true }).focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('[data-catalogue-book]:visible').count(), Math.min(realCount,24));
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await page.evaluate(() => { document.activeElement?.blur(); window.scrollTo({ top: 0, behavior: 'instant' }); });
    await page.waitForFunction(() => window.scrollY === 0);
    await page.screenshot({ path: `${OUT}/catalogue-${width}.png`, fullPage: true });
    await page.goto(`${BASE}/cuaderno/`);
    assert.equal(await page.locator('.cuaderno-feature h2 a, .cuaderno-entry h3 a').count(), 8);
    await page.getByRole('link', { name: 'Libros recomendados', exact: true }).first().click();
    assert.equal(new URL(page.url()).pathname, '/recomendaciones/');
    assert.deepEqual(errors, []);
    await context.close();
  }
  // Real pilot: same purchase component and optional sections as other books.
  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
    const page = await context.newPage();
    await page.goto(`${BASE}/recomendaciones/libros/coraline/`);
    assert.equal(await page.locator('main h1').innerText(), 'Coraline');
    await page.locator('.catalogue-book-cover').evaluate(img => img.decode());
    const coverLink = page.locator('.catalogue-cover-panel > a');
    assert.equal(await coverLink.getAttribute('href'), await page.locator('a[data-purchase-format="tapa-blanda"]').getAttribute('href'));
    assert.match(await coverLink.getAttribute('rel'), /sponsored/);
    await coverLink.focus();
    assert(await coverLink.evaluate(a => a === document.activeElement));
    assert.equal(await page.locator('[data-purchase-format]').count(), 4);
    assert.equal(await page.locator('audio,[data-catalogue-speak],.catalogue-fragment').count(), 0, 'No non-scalable audio or sample UI');
    const reviews = page.locator('details').filter({ has: page.locator('summary', { hasText: 'Opiniones y referencias externas' }) });
    assert.equal(await reviews.getAttribute('open'), null);
    await reviews.locator('summary').click();
    assert(await reviews.locator('a').first().isVisible());
    assert(!/Voz sintética|Esta comprobación no implica|compras adscritas/.test(await page.locator('main').innerText()));
    await page.screenshot({ path: `${OUT}/coraline-mobile.png`, fullPage: true });
    await context.close();
  }
  // Large text and custom spacing must preserve all content on narrow screens.
  for (const width of [320, 390, 768]) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    for (const route of ['/recomendaciones/', '/recomendaciones/libros/coraline/', '/recomendaciones/autores/neil-gaiman/']) {
      for (const css of ['html{font-size:200%!important}', '*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}', 'html{font-size:200%!important}*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}']) {
        await page.goto(`${BASE}${route}`);
        await page.addStyleTag({ content: css });
        await page.evaluate(() => document.fonts.ready);
        const overflow = await page.locator('main *').evaluateAll(nodes => nodes.flatMap(node => {
          const r = node.getBoundingClientRect(), s = getComputedStyle(node);
          return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && (r.right > innerWidth + 1 || r.left < -1) ? [{ tag: node.tagName, class: node.className, right: r.right, left: r.left }] : [];
        }));
        assert.deepEqual(overflow, [], `${route} @ ${width}: ${css}`);
      }
    }
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
  await page.locator('details[data-facet-group="genero"]').evaluate(d => { d.open = true; }); await page.locator('details[data-facet-group="temporada"]').evaluate(d => { d.open = true; }); await page.locator('input[data-facet="genero"][value="romantasy"]').check();
  await page.locator('input[data-facet="temporada"][value="halloween"]').check();
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 1);
  const href = await page.locator('[data-catalogue-book]:visible h3 a').getAttribute('href');
  await page.locator('input[data-facet="genero"][value="romantasy"]').uncheck(); await page.locator('input[data-facet="genero"][value="fantasia"]').check();
  assert.equal(await page.locator('[data-catalogue-book]:visible h3 a').getAttribute('href'), href);
  await page.locator('[data-filter="q"]').fill('TITULO');
  await page.locator('[data-filter="q"]').press('Enter');
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 1);
  await page.reload();
  assert.equal(await page.locator('[data-filter="q"]').inputValue(), 'TITULO');
  await page.getByRole('button', { name: 'Restablecer' }).click();
  await page.locator('[data-filter="novedad"]').selectOption('180');
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 1);
  await page.clock.setSystemTime(new Date('2027-10-20T12:00:00Z'));
  await page.evaluate(() => window.dispatchEvent(new Event('pageshow')));
  assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 0);
  await page.getByRole('button', { name: 'Restablecer' }).click();
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
  await page.reload();
  assert.equal(await page.locator('[data-catalogue-speak],audio,.catalogue-fragment').count(),0);
  await context.close();
  const nojs = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 900 } });
  const staticPage = await nojs.newPage();
  await staticPage.goto(`${BASE}/recomendaciones/`);
  assert(await staticPage.locator('a[href="/recomendaciones/libros/coraline/"]').first().isVisible());
  assert(await staticPage.locator('input[data-facet="genero"]').first().isDisabled());
  await nojs.route('**/recomendaciones/', route => route.fulfill({ contentType: 'text/html; charset=utf-8', body: fixture.hub }));
  await staticPage.reload();
  assert.equal(await staticPage.locator('[data-catalogue-book]').count(), 2);
  assert.equal(await staticPage.locator('[data-catalogue-book] h3 a').first().getAttribute('href'), href);
  await nojs.close();
  console.log('PASS catálogo navegador: 5 tamaños, vacío real, filtros combinados, URL única, teclado, novedades, fichas y sin JS.');
} finally {
  await browser.close();
}
