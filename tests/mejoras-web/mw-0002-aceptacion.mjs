import assert from 'node:assert/strict';
import { chromium } from 'playwright';

// MW-0002: semántica, numeración y conservación del archivo del Cuaderno.
// El ejecutor proporciona un servidor local mediante SITE_ORIGIN.
const origin = process.env.SITE_ORIGIN;
assert.ok(origin, 'SITE_ORIGIN debe apuntar al servidor local del repositorio');

const expectedIndices = ['02', '03', '04', '05', '06', '07', '08'];
const expectedHrefs = [
  '/cuaderno/que-es-el-portal-fantasy/',
  '/cuaderno/portal-fantasy-vs-fantasia-epica/',
  '/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/',
  '/cuaderno/worldbuilding-noveris-ciudad-magica/',
  '/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/',
  '/recomendaciones/portal-fantasy-espanol/',
  '/recomendaciones/magia-con-coste/',
];

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({
    viewport: { width: 1280, height: 800 },
    reducedMotion: 'reduce',
  });

  const response = await page.goto(`${origin.replace(/\/$/, '')}/cuaderno/`, {
    waitUntil: 'domcontentloaded',
    timeout: 20000,
  });
  assert.ok(response?.ok(), 'No se pudo cargar /cuaderno/');

  const archive = page.locator('ol.cuaderno-ledger');
  assert.equal(await archive.count(), 1, 'Debe existir una única lista ordenada del archivo');

  // Semántica accesible y numeración nativa del DOM.
  assert.equal(await archive.getAttribute('role'), 'list', 'Falta role="list"');
  assert.equal(await archive.getAttribute('start'), '2', 'Falta start="2"');
  assert.equal(await archive.evaluate(el => el.start), 2, 'HTML OListElement.start debe valer 2');

  // Exactamente siete elementos directos, numerados visualmente del 02 al 08.
  const entries = archive.locator(':scope > li');
  assert.equal(await entries.count(), 7, 'Deben existir exactamente siete li directos');
  assert.deepEqual(
    await archive.locator(':scope > li > .cuaderno-entry__index').allInnerTexts(),
    expectedIndices,
    'Los índices visibles deben conservar el orden 02–08',
  );

  // Los destinos editoriales no deben modificarse.
  const hrefs = await archive.locator(':scope > li .cuaderno-entry__body h3 a')
    .evaluateAll(links => links.map(link => link.getAttribute('href')));
  assert.deepEqual(hrefs, expectedHrefs, 'Los enlaces del archivo han cambiado');

  // Conservación de la hoja de estilos y de las reglas cromáticas del archivo.
  assert.equal(
    await page.locator('link[rel="stylesheet"][href="/assets/cuaderno-index.css?v=1"]').count(),
    1,
    'La hoja de estilos original debe permanecer cargada',
  );
  const borders = await archive.evaluate(el => {
    const computed = getComputedStyle(el);
    return {
      top: computed.borderTopColor,
      bottom: computed.borderBottomColor,
    };
  });
  assert.deepEqual(borders, {
    top: 'rgb(29, 79, 150)',
    bottom: 'rgb(184, 134, 11)',
  }, 'Las reglas editoriales del archivo han cambiado');
} finally {
  await browser.close();
}

console.log('MW-0002: PASS');
