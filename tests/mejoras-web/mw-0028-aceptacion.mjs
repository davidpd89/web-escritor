import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const ORIGIN = process.env.SITE_ORIGIN;
assert.ok(ORIGIN, 'SITE_ORIGIN debe apuntar al servidor local del repositorio');

const radar = JSON.parse(fs.readFileSync('convocatorias-escritores/opportunities.json', 'utf8'));
assert.match(radar.generated_for, /^\d{4}-\d{2}-\d{2}$/, 'generated_for es obligatorio');
assert.ok(Array.isArray(radar.items), 'opportunities.json debe contener items');
const defaults = [...radar.items, ...(radar.watchlist || [])];
const expected = defaults.filter(item => item.type === 'concurso' && (item.genres || []).includes('fantasía')).length;
assert.ok(expected > 0, 'El dataset debe contener oportunidades de fantasía y concurso');

const base = new URL('/convocatorias-escritores/?campana=qa', ORIGIN).href;
const canonical = 'https://davidportodiaz.com/convocatorias-escritores/';
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
await context.addInitScript(today => { window.__DP_RADAR_TODAY__ = today; }, radar.generated_for);
const errors = [];

const trackErrors = page => page.on('pageerror', error => errors.push(error.message));
const selection = async page => ({
  genre: await page.locator('[data-radar-genre]').inputValue(),
  type: await page.locator('[data-radar-type]').inputValue(),
  visible: await page.locator('[data-radar-item]:visible').count(),
  count: (await page.locator('[data-radar-count]').textContent()).trim(),
});

try {
  const page = await context.newPage();
  trackErrors(page);
  await page.goto(base, { waitUntil: 'networkidle' });
  assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'), canonical);

  // Los filtros discretos generan entradas navegables, no solo cambios visuales.
  await page.locator('[data-radar-genre]').selectOption('fantasía');
  const first = new URL(page.url());
  assert.equal(new URLSearchParams(first.hash.slice(1)).get('genero'), 'fantasía');
  await page.locator('[data-radar-type]').selectOption('concurso');
  const sharedUrl = page.url();
  const params = new URLSearchParams(new URL(sharedUrl).hash.slice(1));
  assert.equal(params.get('genero'), 'fantasía');
  assert.equal(params.get('tipo'), 'concurso');
  assert.equal(new URL(sharedUrl).searchParams.get('campana'), 'qa');
  const filtered = await selection(page);
  assert.deepEqual(filtered, {
    genre: 'fantasía', type: 'concurso', visible: expected,
    count: `${expected} ${expected === 1 ? 'convocatoria' : 'convocatorias'} ${expected === 1 ? 'visible' : 'visibles'}`,
  });

  // Una página independiente y una recarga restauran exactamente el resultado.
  const opened = await context.newPage();
  trackErrors(opened);
  await opened.goto(sharedUrl, { waitUntil: 'networkidle' });
  assert.deepEqual(await selection(opened), filtered);
  await opened.reload({ waitUntil: 'networkidle' });
  assert.deepEqual(await selection(opened), filtered);
  await page.reload({ waitUntil: 'networkidle' });
  assert.deepEqual(await selection(page), filtered);

  await page.goBack();
  assert.equal(await page.locator('[data-radar-genre]').inputValue(), 'fantasía');
  assert.equal(await page.locator('[data-radar-type]').inputValue(), '');
  await page.goForward();
  assert.deepEqual(await selection(page), filtered);

  // Escribir sustituye la entrada actual y no crea una por cada pulsación.
  const lengthBeforeTyping = await page.evaluate(() => history.length);
  await page.locator('[data-radar-search]').fill('AST');
  await page.locator('[data-radar-search]').fill('ASTER');
  assert.equal(await page.evaluate(() => history.length), lengthBeforeTyping);
  assert.equal(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('q'), 'ASTER');
  await page.reload({ waitUntil: 'networkidle' });
  assert.equal(await page.locator('[data-radar-search]').inputValue(), 'ASTER');
  await page.locator('[data-radar-search]').fill('');

  // El enlace de accesibilidad conserva los controles y todas las fichas visibles.
  await page.locator('.skip-link').focus();
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => location.hash === '#contenido');
  assert.deepEqual(await selection(page), filtered, '#contenido no debe destruir los filtros');
  assert.equal(await page.locator('main#contenido').count(), 1);
  await page.goBack();
  assert.deepEqual(await selection(page), filtered);
  await page.goForward();
  assert.deepEqual(await selection(page), filtered, 'Volver al ancla debe recuperar su selección');

  // Limpiar con ancla previa conserva el ancla y evita entradas repetidas.
  await page.locator('[data-radar-clear]').click();
  assert.equal(new URL(page.url()).hash, '#contenido');
  assert.equal(new URL(page.url()).searchParams.get('campana'), 'qa');
  assert.equal(await page.locator('[data-radar-item]:visible').count(), defaults.length);
  assert.equal(await page.locator('[data-radar-genre]').inputValue(), '');
  assert.equal(await page.locator('[data-radar-type]').inputValue(), '');
  const lengthAfterClear = await page.evaluate(() => history.length);
  await page.locator('[data-radar-clear]').click();
  assert.equal(await page.evaluate(() => history.length), lengthAfterClear);
  assert.equal(new URL(page.url()).hash, '#contenido');

  // Volver desde Limpiar a la entrada filtrada debe recuperar su selección.
  await page.goBack();
  assert.deepEqual(await selection(page), filtered);
  await page.goForward();
  assert.equal(await page.locator('[data-radar-genre]').inputValue(), '');
  assert.equal(await page.locator('[data-radar-type]').inputValue(), '');

  // Valores ajenos a las opciones y secuencias UTF-8 inválidas se descartan.
  await opened.goto(`${base}#tipo=incorrecto&genero=desconocido&situacion=error&pronto=si&vencidas=2&q=%FF`, { waitUntil: 'networkidle' });
  assert.equal(await opened.locator('[data-radar-search]').inputValue(), '');
  assert.equal(await opened.locator('[data-radar-type]').inputValue(), '');
  assert.equal(await opened.locator('[data-radar-genre]').inputValue(), '');
  assert.equal(await opened.locator('[data-radar-kind]').inputValue(), '');
  assert.equal(await opened.locator('[data-radar-soon]').isChecked(), false);
  assert.equal(await opened.locator('[data-radar-expired]').isChecked(), false);
  assert.equal(await opened.locator('[data-radar-item]:visible').count(), defaults.length);

  // Los parámetros de fragmento desconocidos no son propiedad del radar.
  await opened.goto(`${base}#origen=externo&genero=fantas%C3%ADa`, { waitUntil: 'networkidle' });
  await opened.locator('[data-radar-type]').selectOption('concurso');
  assert.equal(new URLSearchParams(new URL(opened.url()).hash.slice(1)).get('origen'), 'externo');
  await opened.locator('[data-radar-clear]').click();
  const afterClear = new URL(opened.url());
  assert.equal(afterClear.hash, '#origen=externo');
  assert.equal(afterClear.searchParams.get('campana'), 'qa');
  assert.equal(await opened.locator('[data-radar-item]:visible').count(), defaults.length);
  assert.equal(await opened.locator('link[rel="canonical"]').getAttribute('href'), canonical);
  assert.deepEqual(errors, [], `Errores JavaScript: ${errors.join('; ')}`);
  console.log('MW-0028: PASS');
} finally {
  await context.close();
  await browser.close();
}
