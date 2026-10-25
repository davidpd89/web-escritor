import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const ROOT = process.cwd();
const publishers = JSON.parse(fs.readFileSync(path.join(ROOT, 'editoriales/editoriales-data.json'), 'utf8')).publishers;
const html = fs.readFileSync(path.join(ROOT, 'editoriales/index.html'), 'utf8');
const script = fs.readFileSync(path.join(ROOT, 'assets/editoriales.js'), 'utf8');
const collator = new Intl.Collator('es', { sensitivity: 'base' });
const bySlug = new Map(publishers.map(p => [p.slug, p]));
assert.equal(bySlug.size, publishers.length, 'El JSON contiene slugs repetidos');

function decodeHtml(value) {
  const named = { amp: '&', quot: '"', apos: "'", lt: '<', gt: '>', nbsp: ' ' };
  return value.replace(/&(#(?:x[0-9a-f]+|[0-9]+)|[a-z][a-z0-9]+);/gi, (whole, code) => {
    if (code[0] !== '#') return named[code.toLowerCase()] ?? whole;
    const point = code[1]?.toLowerCase() === 'x' ? parseInt(code.slice(2), 16) : parseInt(code.slice(1), 10);
    return Number.isInteger(point) && point >= 0 && point <= 0x10ffff ? String.fromCodePoint(point) : whole;
  });
}
function attribute(tag, key) {
  const match = tag.match(new RegExp(`\\b${key}="([^"]*)"`));
  assert.ok(match, `Falta el atributo HTML ${key}`);
  return decodeHtml(match[1]);
}
function selectOptions(marker) {
  const match = html.match(new RegExp(`<select\\b(?=[^>]*\\bdata-editoriales-${marker}\\b)[^>]*>([\\s\\S]*?)<\\/select>`));
  assert.ok(match, `Falta el select publicado ${marker}`);
  return [...match[1].matchAll(/<option\b[^>]*\bvalue="([^"]*)"[^>]*>/g)].map(m => decodeHtml(m[1]));
}
const options = Object.fromEntries(['genre', 'status', 'country', 'sort'].map(key => [key, selectOptions(key)]));
for (const name of ['directory', 'search', 'direct', 'reset', 'count', 'empty']) {
  assert.match(html, new RegExp(`\\bdata-editoriales-${name}\\b`), `Falta el control publicado ${name}`);
}

// Fixture derivada de los artículos HTML publicados, no de tarjetas inventadas desde JSON.
const publishedCards = [...html.matchAll(/<article\b([^>]*\bdata-editorial-card\b[^>]*)>([\s\S]*?)<\/article>/g)].map((match, index) => {
  const [, tag, body] = match;
  const titleLink = body.match(/<h2>\s*<a\b[^>]*\bhref="([^"]+)"[^>]*>([\s\S]*?)<\/a>/);
  assert.ok(titleLink, `Tarjeta ${index}: falta el enlace de su ficha`);
  const route = decodeHtml(titleLink[1]).match(/^\/editoriales\/([^/?#]+)\/$/);
  assert.ok(route, `Tarjeta ${index}: ruta de ficha incorrecta: ${titleLink[1]}`);
  const slug = decodeURIComponent(route[1]);
  const data = {
    name: attribute(tag, 'data-name'),
    group: attribute(tag, 'data-group'),
    genres: attribute(tag, 'data-genres'),
    status: attribute(tag, 'data-status'),
    country: attribute(tag, 'data-country'),
    verifiedAt: attribute(tag, 'data-verified-at'),
    direct: attribute(tag, 'data-direct'),
  };
  const record = bySlug.get(slug);
  assert.ok(record, `Tarjeta publicada sin correspondencia en JSON: ${slug}`);
  assert.equal(decodeHtml(titleLink[2].replace(/<[^>]*>/g, '')).trim(), record.name, `${slug}: título del enlace`);
  for (const [key, expected] of Object.entries({
    name: record.name, group: record.group, genres: record.genres.join('|'),
    status: record.status, country: record.country, verifiedAt: record.verified_at,
    direct: String(record.direct_submission),
  })) assert.equal(data[key], expected, `${slug}: atributo ${key} frente al JSON`);
  return { slug, dataset: data, textContent: decodeHtml(body.replace(/<[^>]*>/g, '')) };
});
assert.equal(publishedCards.length, publishers.length, 'La cantidad de tarjetas HTML no coincide con el JSON');
assert.equal(new Set(publishedCards.map(p => p.slug)).size, publishers.length, 'Tarjetas HTML duplicadas');
assert.deepEqual(publishedCards.map(p => p.slug), publishers.map(p => p.slug), 'Orden inicial HTML distinto del JSON');
const publishedText = new Map(publishedCards.map(p => [p.slug, p.textContent]));

const axes = {
  status: ['open', 'closed', 'indirect', 'unknown'],
  country: ['España', 'Chile', 'México'],
  genre: ['fantasía', 'narrativa', 'ensayo'],
  direct: [false, true],
  sort: ['availability', 'name', 'recent'],
};
for (const [field, values] of Object.entries(axes)) for (const value of values) {
  const present = field === 'direct' ? true : field === 'sort' ? options.sort.includes(value)
    : field === 'genre' ? publishers.some(p => p.genres.includes(value)) && options.genre.includes(value)
    : publishers.some(p => p[field] === value) && options[field].includes(value);
  assert.ok(present, `Valor pairwise inexistente en datos/HTML: ${field}=${value}`);
}

const names = Object.keys(axes);
const candidates = [];
function enumerate(i, row) {
  if (i === names.length) { candidates.push({ ...row }); return; }
  const key = names[i];
  for (const value of axes[key]) enumerate(i + 1, { ...row, [key]: value });
}
enumerate(0, {});
function pairs(row) {
  const keys = [];
  for (let i = 0; i < names.length; i++) for (let j = i + 1; j < names.length; j++) {
    keys.push(JSON.stringify([names[i], row[names[i]], names[j], row[names[j]]]));
  }
  return keys;
}
const uncovered = new Set(candidates.flatMap(pairs));
const matrix = [];
while (uncovered.size) {
  const best = candidates.reduce((chosen, row) => {
    const score = pairs(row).filter(pair => uncovered.has(pair)).length;
    return score > chosen.score ? { row, score } : chosen;
  }, { row: null, score: 0 });
  assert.ok(best.row && best.score > 0, 'La cobertura pairwise no converge');
  matrix.push(best.row);
  for (const pair of pairs(best.row)) uncovered.delete(pair);
}
assert.equal(candidates.length, 216, 'Cambió el producto cartesiano previsto');
assert.equal(matrix.length, 14, 'Cambió el tamaño de la matriz greedy determinista');

// Oráculo ajeno a apply(): filtros desde JSON y texto efectivamente publicado.
// Conserva ñ y ü, pero ignora otras tildes, igual que la búsqueda de producción.
function normalizeOracle(value = '') {
  let output = '', base = '';
  for (const letter of String(value).toLocaleLowerCase('es').normalize('NFD')) {
    if (/\p{M}/u.test(letter)) {
      if ((letter === '\u0303' && base === 'n') || (letter === '\u0308' && base === 'u')) output += letter;
    } else { base = letter; output += letter; }
  }
  return output.normalize('NFC').trim();
}
assert.equal(normalizeOracle('FANTASÍA'), normalizeOracle('fantasia'));
assert.notEqual(normalizeOracle('España'), normalizeOracle('Espana'));
function expectedIds({ status = '', country = '', genre = '', direct = false, search = '' }) {
  const q = normalizeOracle(search), g = normalizeOracle(genre), c = normalizeOracle(country);
  return publishers.filter(p => {
    const searchable = normalizeOracle(`${p.name} ${p.group} ${p.genres.join('|')} ${p.country} ${publishedText.get(p.slug)}`);
    return (!status || p.status === status) &&
      (!c || normalizeOracle(p.country) === c) &&
      (!g || p.genres.some(value => normalizeOracle(value) === g)) &&
      (!direct || p.direct_submission === true) &&
      (!q || searchable.includes(q));
  }).map(p => p.slug);
}
function expectedOrder(mode = 'availability') {
  const sorted = [...publishers];
  if (mode === 'name') sorted.sort((a, b) => collator.compare(a.name, b.name));
  if (mode === 'recent') sorted.sort((a, b) => b.verified_at.localeCompare(a.verified_at) || collator.compare(a.name, b.name));
  return sorted.map(p => p.slug);
}

function setup(initialHash = '') {
  const listeners = new Map();
  function control(value = '', values = []) {
    const events = new Map();
    return {
      value, checked: false, options: values.map(option => ({ value: option })),
      addEventListener(type, fn) { events.set(type, fn); },
      fire(type) { assert.ok(events.has(type), `No se registró el evento ${type}`); events.get(type)(); },
      focus() {},
    };
  }
  const cards = publishedCards.map(p => ({ slug: p.slug, dataset: { ...p.dataset }, textContent: p.textContent, hidden: false }));
  const grid = {
    children: [...cards],
    appendChild(item) {
      const index = this.children.indexOf(item);
      assert.notEqual(index, -1, 'La ordenación insertó una tarjeta ajena al HTML');
      this.children.splice(index, 1); this.children.push(item);
    },
  };
  const controls = {
    '[data-editoriales-search]': control(),
    '[data-editoriales-genre]': control('', options.genre),
    '[data-editoriales-status]': control('', options.status),
    '[data-editoriales-country]': control('', options.country),
    '[data-editoriales-sort]': control('availability', options.sort),
    '[data-editoriales-direct]': control(),
    '[data-editoriales-reset]': control(),
    '[data-editoriales-count]': { textContent: '' },
    '[data-editoriales-empty]': { hidden: true },
    '.id-cards': grid,
  };
  const root = {
    querySelector(selector) { assert.ok(selector in controls, `Selector no simulado: ${selector}`); return controls[selector]; },
    querySelectorAll(selector) { assert.equal(selector, '[data-editorial-card]'); return cards; },
  };
  const location = { pathname: '/editoriales/', search: '', hash: '', href: '' };
  const entries = [`/editoriales/${initialHash}`];
  let position = 0;
  const setLocation = value => {
    const parsed = new URL(value, 'https://davidportodiaz.com');
    location.pathname = parsed.pathname; location.search = parsed.search;
    location.hash = parsed.hash; location.href = parsed.href;
  };
  setLocation(entries[0]);
  const history = {
    pushState(_state, _title, url) {
      entries.splice(position + 1); entries.push(url); position++; setLocation(url);
    },
    replaceState(_state, _title, url) { entries[position] = url; setLocation(url); },
  };
  const window = { addEventListener(type, fn) { listeners.set(type, fn); } };
  vm.runInNewContext(script, {
    document: { querySelector(selector) { assert.equal(selector, '[data-editoriales-directory]'); return root; } },
    window, location, history, URLSearchParams, Intl,
  }, { filename: 'assets/editoriales.js', timeout: 2000 });
  const el = {
    search: controls['[data-editoriales-search]'], genre: controls['[data-editoriales-genre]'],
    status: controls['[data-editoriales-status]'], country: controls['[data-editoriales-country]'],
    sort: controls['[data-editoriales-sort]'], direct: controls['[data-editoriales-direct]'],
    reset: controls['[data-editoriales-reset]'], count: controls['[data-editoriales-count]'],
    empty: controls['[data-editoriales-empty]'],
  };
  function change(key, value) {
    assert.ok(key in el, `Control desconocido: ${key}`);
    if (key === 'direct') el[key].checked = value;
    else el[key].value = value;
    el[key].fire(key === 'search' ? 'input' : 'change');
  }
  function emit(type) { assert.ok(listeners.has(type), `Falta evento ${type}`); listeners.get(type)(); }
  function move(delta) {
    const next = position + delta;
    assert.ok(next >= 0 && next < entries.length, 'Historial fuera de rango');
    position = next; setLocation(entries[position]); emit('popstate');
  }
  function setHash(hash) {
    assert.ok(!hash || hash.startsWith('#'), 'El fragmento debe empezar por #');
    entries.splice(position + 1); entries.push(`${location.pathname}${location.search}${hash}`);
    position++; setLocation(entries[position]); emit('hashchange');
  }
  return { el, grid, location, change, back: () => move(-1), forward: () => move(1), setHash };
}

function assertView(view, row, label) {
  const expected = new Set(expectedIds(row));
  const order = expectedOrder(row.sort || 'availability');
  assert.deepEqual(view.grid.children.map(card => card.slug), order, `${label}: orden completo por slug`);
  assert.deepEqual(view.grid.children.filter(card => !card.hidden).map(card => card.slug),
    order.filter(slug => expected.has(slug)), `${label}: orden e identidad de las tarjetas visibles`);
  assert.equal(view.el.count.textContent, `${expected.size} ${expected.size === 1 ? 'editorial' : 'editoriales'}`, `${label}: contador`);
  assert.equal(view.el.empty.hidden, expected.size !== 0, `${label}: estado vacío`);
  for (const key of ['search', 'genre', 'status', 'country', 'sort']) {
    assert.equal(view.el[key].value, row[key] ?? (key === 'sort' ? 'availability' : ''), `${label}: control ${key}`);
  }
  assert.equal(view.el.direct.checked, Boolean(row.direct), `${label}: checkbox de envío directo`);
  const actualHash = [...new URLSearchParams(view.location.hash.replace(/^#/, '')).entries()].sort(([a], [b]) => a.localeCompare(b));
  const wanted = new URLSearchParams();
  if (row.search?.trim()) wanted.set('q', row.search.trim());
  if (row.genre) wanted.set('genero', row.genre);
  if (row.status) wanted.set('estado', row.status);
  if (row.country) wanted.set('pais', row.country);
  if (row.sort && row.sort !== 'availability') wanted.set('orden', row.sort);
  if (row.direct) wanted.set('directo', '1');
  assert.deepEqual(actualHash, [...wanted.entries()].sort(([a], [b]) => a.localeCompare(b)), `${label}: fragmento URL exacto`);
}

let positive = 0, empty = 0;
for (const [index, row] of matrix.entries()) {
  if (expectedIds(row).length) positive++; else empty++;
  const view = setup();
  for (const key of ['status', 'country', 'genre', 'direct', 'sort']) view.change(key, row[key]);
  assertView(view, row, `par ${index + 1}`);
}
assert.ok(positive > 0 && empty > 0, `La matriz necesita resultados y vacíos: ${positive}/${empty}`);

{
  const row = { status: 'open', country: 'España', genre: 'fantasía', direct: true, sort: 'name', search: 'MINOTAURO' };
  const view = setup();
  for (const key of ['status', 'country', 'genre', 'direct', 'sort', 'search']) view.change(key, row[key]);
  assert.deepEqual(expectedIds(row), ['minotauro'], 'Minotauro debe ser único');
  assertView(view, row, 'búsqueda combinada Minotauro');
  const restored = setup(view.location.hash);
  assertView(restored, row, 'URL inicial compartida');
}
{
  const row = { status: 'open', country: 'España', genre: 'narrativa', direct: true, sort: 'recent', search: 'GRUPO PLANETA' };
  assert.ok(expectedIds(row).length > 0, 'Debe haber coincidencias por grupo editorial');
  assert.ok(expectedIds(row).some(slug => !normalizeOracle(bySlug.get(slug).name).includes(normalizeOracle(row.search)) &&
    normalizeOracle(bySlug.get(slug).group).includes(normalizeOracle(row.search))), 'La búsqueda debe recuperar alguna tarjeta solo por grupo, no por nombre');
  const view = setup();
  for (const key of ['status', 'country', 'genre', 'direct', 'sort', 'search']) view.change(key, row[key]);
  assertView(view, row, 'búsqueda por grupo y filtros simultáneos');
  const fromHash = setup();
  fromHash.setHash('#q=GRUPO+PLANETA&genero=narrativa&estado=open&pais=Espa%C3%B1a&orden=recent&directo=1');
  assertView(fromHash, row, 'hashchange de URL externa');
  fromHash.setHash('');
  assertView(fromHash, {}, 'hashchange de limpieza externa');
}
{
  const row = { status: 'open', country: 'España', genre: 'fantasía', direct: true, sort: 'name', search: 'FANTASIA' };
  const view = setup();
  for (const key of ['status', 'country', 'genre', 'direct', 'sort', 'search']) view.change(key, row[key]);
  assert.ok(expectedIds(row).length > 0, 'Debe haber coincidencia sin tilde');
  assertView(view, row, 'búsqueda sin tilde sobre género con tilde');
}
{
  const view = setup();
  view.change('status', 'closed'); view.change('country', 'España'); view.change('direct', true);
  assertView(view, { status: 'closed', country: 'España', direct: true }, 'historial C');
  view.back(); assertView(view, { status: 'closed', country: 'España' }, 'Atrás B');
  view.back(); assertView(view, { status: 'closed' }, 'Atrás A');
  view.forward(); assertView(view, { status: 'closed', country: 'España' }, 'Adelante B');
  view.el.reset.fire('click');
  assertView(view, {}, 'Limpiar filtros');
}
{
  // Limpiar desde una ordenación no predeterminada debe devolver el control, el orden del DOM y la URL a disponibilidad.
  const view = setup();
  for (const [key, value] of [['status', 'open'], ['direct', true], ['sort', 'recent']]) view.change(key, value);
  assertView(view, { status: 'open', direct: true, sort: 'recent' }, 'antes de limpiar con orden recent');
  view.el.reset.fire('click');
  assertView(view, {}, 'Limpiar filtros desde una ordenación no predeterminada');
}
console.log(`test-editoriales-pairwise: OK (${matrix.length} combinaciones, ${positive} positivas, ${empty} vacías, HTML real y restauración)`);
