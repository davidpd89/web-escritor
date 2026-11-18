// Paridad del motor de filtros (R5-5, Fable 18/11 §2.1): la página real contra la referencia pura
// qa/catalogue-filter-reference.mjs, con ≥ 2.000 consultas generadas con semilla fija.
//
// Por cada consulta compara: el recuento, los ids de la página pedida (en orden) y el recuento de cada casilla de
// faceta. Es el oráculo con el que cualquier cambio del motor (índices por faceta, fragmentos, etc.) demuestra que no
// cambia resultados. Mercado vacío, como el resto de la QA del catálogo.
//
// Uso: QA_ORIGIN=http://127.0.0.1:4173 node qa/catalogue-filter-parity.mjs   (QA_PARITY_QUERIES, QA_PARITY_SEED)
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { FACETS, filtrar } from './catalogue-filter-reference.mjs';

const origin = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const TOTAL = Number(process.env.QA_PARITY_QUERIES || 2000);
const SEED = Number(process.env.QA_PARITY_SEED || 20261118);
const PAGE_SIZE = 24;

// Mulberry32: misma semilla, mismas consultas en cualquier máquina.
const rng = (seed => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; })(SEED);
const pickOne = xs => xs[Math.floor(rng() * xs.length)];
const chance = p => rng() < p;

// Libros en el orden de hidratación (el `originalOrder` del motor): las fichas de /recomendaciones/ y luego las de cada
// página de continuación, en el orden de sus enlaces. Se leen del HTML servido, no del DOM ya reordenado.
const decode = s => s.replace(/&(?:#x([0-9a-f]+)|#(\d+)|(amp|lt|gt|quot|apos));/gi, (m, hex, dec, name) => hex ? String.fromCodePoint(parseInt(hex, 16)) : dec ? String.fromCodePoint(Number(dec)) : ({amp: '&', lt: '<', gt: '>', quot: '"', apos: "'"})[name.toLowerCase()]);
const camel = s => s.replace(/-([a-z])/g, (m, c) => c.toUpperCase());
const cardsOf = html => {
  const start = html.indexOf('<ul class="catalogue-grid">');
  assert.ok(start >= 0, 'página sin rejilla del catálogo');
  return [...html.slice(start).matchAll(/<li class="catalogue-card" data-catalogue-book([^>]*)>/g)].map(m => Object.fromEntries(
    [...m[1].matchAll(/data-([a-z][a-z0-9-]*)(?:="([^"]*)")?/g)].map(a => [camel(a[1]), decode(a[2] || '')])));
};
const get = async path => { const r = await fetch(origin + path); assert.equal(r.status, 200, `${path}: HTTP ${r.status}`); return r.text(); };
const first = await get('/recomendaciones/');
const nav = first.slice(first.indexOf('data-catalogue-static-pagination'));
const links = [...nav.matchAll(/<a [^>]*href="([^"]*)"[^>]*data-catalogue-page|<a [^>]*data-catalogue-page[^>]*href="([^"]*)"/g)].map(m => new URL(decode(m[1] || m[2]), origin + '/recomendaciones/').pathname);
const libros = cardsOf(first);
for (const path of links) libros.push(...cardsOf(await get(path)));
const declared = Number(first.match(/data-catalogue-total="(\d+)"/)?.[1]);
assert.equal(libros.length, declared, `se reconstruyeron ${libros.length} libros y el catálogo declara ${declared}`);
assert.equal(new Set(libros.map(b => b.bookId)).size, libros.length, 'ids repetidos en el catálogo');

const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
const fallos = [];
try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, serviceWorkers: 'block' });
  await context.addInitScript(() => { try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {} });
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.origin !== origin) return route.abort();
    if (url.pathname === '/assets/reading-market.json') return route.fulfill({ json: { schema_version: 1, offers: [], ratings: [], sales_ranks: [] } });
    return route.continue();
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  // Con estado en la URL el catálogo se hidrata sin esperar un gesto.
  await page.goto(`${origin}/recomendaciones/#orden=fecha_desc`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => document.querySelector('[data-reading-catalogue]')?.dataset.catalogueReady === 'true', null, { timeout: 60000 });

  const today = await page.evaluate(() => new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Madrid', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()));
  const controls = await page.evaluate(() => ({
    selects: Object.fromEntries([...document.querySelectorAll('select[data-filter]')].map(s => [s.dataset.filter, [...s.options].map(o => o.value)])),
    facets: Object.fromEntries(['grupo', 'genero', 'edad', 'formato'].map(k => [k, [...document.querySelectorAll(`input[data-facet="${k}"]`)].map(b => b.value)])),
  }));
  const ctx = { today };

  // Aplica el estado por la URL como un enlace compartido; el oyente propio va detrás del del motor (restore → apply),
  // así que al dispararse la página ya está filtrada. Luego se esperan los recuentos de facetas (rAF + tarea).
  const aplicar = hash => page.evaluate(async hash => {
    const root = document.querySelector('[data-reading-catalogue]');
    if (location.hash.slice(1) !== hash) await new Promise(resolve => { window.addEventListener('hashchange', resolve, { once: true }); location.hash = hash; });
    else window.dispatchEvent(new HashChangeEvent('hashchange'));
    while (root.dataset.facetsPending) await new Promise(resolve => requestAnimationFrame(() => setTimeout(resolve, 0)));
    const fields = [...root.querySelectorAll('[data-filter]')];
    const consulta = { ...Object.fromEntries(fields.map(f => [f.dataset.filter, f.disabled ? '' : f.value])) };
    for (const k of ['grupo', 'genero', 'edad', 'formato']) consulta[k] = [...root.querySelectorAll(`input[data-facet="${k}"]`)].filter(b => b.checked).map(b => b.value);
    return {
      consulta,
      count: Number(root.querySelector('[data-catalogue-count]').textContent.match(/^\d+/)?.[0] ?? -1),
      ids: [...root.querySelectorAll('.catalogue-grid > [data-catalogue-book]')].filter(c => !c.hidden).map(c => c.dataset.bookId),
      facetas: Object.fromEntries(['grupo', 'genero', 'edad', 'formato'].map(k => [k, Object.fromEntries([...root.querySelectorAll(`input[data-facet="${k}"]`)].map(b => [b.value, Number(b.closest('label').dataset.count || 0)]))])),
    };
  }, hash);

  // Generador. Consultas como listas [clave, valor] (la forma de la URL compartida).
  const ordenes = controls.selects.orden || ['editorial'];
  const opciones = k => (controls.selects[k] || []).filter(Boolean);
  const valoresFaceta = Object.entries(controls.facets).flatMap(([k, xs]) => xs.map(x => [k, x]));
  const fechas = [...new Set(libros.map(b => b.published || (b.publishedMonth ? b.publishedMonth + '-01' : '')).filter(Boolean))].sort();
  const palabras = libros.flatMap(b => `${b.title || ''} ${b.author || ''}`.split(/\s+/)).filter(w => w.length > 3);
  const textos = () => pickOne([
    () => pickOne(palabras),
    () => pickOne(palabras).slice(0, 4).toUpperCase(),
    () => { const b = pickOne(libros); return b.isbn ? (chance(0.5) ? b.isbn : 'ISBN: ' + b.isbn.replace(/^(\d{3})(\d)(\d{4})/, '$1-$2-$3-')) : b.title; },
    () => 'zzzz-sin-resultado',
  ])();
  const extra = () => {
    const xs = [];
    if (chance(0.5)) xs.push(['orden', pickOne(ordenes)]);
    if (chance(0.3)) xs.push(['estado', pickOne(opciones('estado'))]);
    if (chance(0.15)) xs.push(['paginas', pickOne(opciones('paginas'))]);
    if (chance(0.1)) xs.push(['desde', pickOne(fechas)]);
    if (chance(0.1)) xs.push(['hasta', pickOne(fechas)]);
    if (chance(0.1)) { xs.push(['precio_min', String(Math.floor(rng() * 15))]); if (chance(0.5)) xs.push(['precio_max', String(15 + Math.floor(rng() * 20))]); if (chance(0.5) && opciones('precio_formato').length) xs.push(['precio_formato', pickOne(opciones('precio_formato'))]); }
    if (chance(0.05) && opciones('descuento').length) xs.push(['descuento', pickOne(opciones('descuento'))]);
    return xs;
  };
  const consultas = [[]];
  for (const o of ordenes) consultas.push([['orden', o]]);
  for (const k of Object.keys(controls.selects)) if (k !== 'orden') for (const x of opciones(k)) consultas.push([[k, x]]);
  for (const kv of valoresFaceta) consultas.push([kv], [kv, ...extra()]);
  while (consultas.length < TOTAL) {
    const n = 2 + (chance(0.4) ? 1 : 0), xs = [];
    for (let i = 0; i < n; i++) xs.push(pickOne(valoresFaceta));
    if (chance(0.25)) xs.push(['q', textos()]);
    consultas.push([...new Map(xs.map(kv => [kv.join('='), kv])).values(), ...extra()]);
  }

  let paginas = 0;
  const t0 = Date.now();
  for (const [i, entradas] of consultas.entries()) {
    const params = new URLSearchParams(entradas);
    // Primero sin página para conocer el total; luego página intermedia o última si hay más de una.
    let real = await aplicar(params.toString());
    let ref = filtrar(libros, real.consulta, ctx);
    const total = Math.max(1, Math.ceil(ref.total / PAGE_SIZE));
    let n = 1;
    if (total > 1 && chance(0.6)) {
      n = chance(0.5) ? total : 1 + Math.floor(total / 2);
      params.set('pagina', String(n));
      real = await aplicar(params.toString());
      ref = filtrar(libros, real.consulta, ctx);
      paginas++;
    }
    const esperado = ref.ids.slice((n - 1) * PAGE_SIZE, n * PAGE_SIZE);
    const diffs = [];
    if (real.count !== ref.total) diffs.push(`recuento ${real.count} ≠ ${ref.total}`);
    if (JSON.stringify(real.ids) !== JSON.stringify(esperado)) diffs.push(`página ${n}: ids ${JSON.stringify(real.ids.slice(0, 5))}… ≠ ${JSON.stringify(esperado.slice(0, 5))}…`);
    for (const k of FACETS) for (const [x, c] of Object.entries(real.facetas[k])) if (c !== (ref.facetas[k][x] || 0)) diffs.push(`${k}=${x}: ${c} ≠ ${ref.facetas[k][x] || 0}`);
    if (diffs.length) fallos.push(`#${i} ${params}: ${diffs.slice(0, 4).join('; ')}`);
    if (fallos.length >= 20) break;
  }
  assert.deepEqual(errors, [], 'errores de JavaScript en la página');
  if (fallos.length) {
    console.error(fallos.join('\n'));
    throw new Error(`${fallos.length} consultas sin paridad (de ${consultas.length})`);
  }
  console.log(`OK paridad del motor de filtros: ${consultas.length} consultas (${paginas} con página > 1) sobre ${libros.length} libros, semilla ${SEED}, ${Math.round((Date.now() - t0) / 1000)} s`);
} finally {
  await browser.close();
}
