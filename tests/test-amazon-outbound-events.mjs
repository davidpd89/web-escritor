// Contratos de salida Amazon: no requieren navegador, login ni red.
// A ejecutar al autorizar QA: node --test tests/test-amazon-outbound-events.mjs
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import vm from 'node:vm';
import test from 'node:test';

const base = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const script = readFileSync(resolve(base, 'script.js'), 'utf8').replace(/\r\n/g, '\n');
const start = script.indexOf('function _amazonOutboundCategory(');
const end = script.indexOf('\n}\n\n// Delegación', start);
assert.ok(start > -1 && end > start, 'Falta función pura de clasificación');
const fn = vm.runInNewContext('(' + script.slice(start, end + 2) + ')', { URL });
const registry = JSON.parse(readFileSync(resolve(base, 'data/analytics-events.json'), 'utf8'));
const names = new Set(registry.events.map(x => x.name));
const product = 'https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21';
const short = 'https://amzn.to/4zW6Yeu';
const search = 'https://www.amazon.es/s?k=9788498382372&tag=davidporto-21';
const classify = (href, page = '/', header = false, catalogue = false) =>
  fn(href, page, header, catalogue);

test('cobertura y precedencia de superficies', () => {
  assert.equal(classify(short, '/libros/samuel-entre-mundos/', true), 'comprar-amazon-header');
  assert.equal(classify(product), 'comprar-amazon-home');
  assert.equal(classify(product, '/libros/samuel-entre-mundos/'), 'comprar-amazon-samuel');
  assert.equal(classify(short, '/las-manecillas-del-recuerdo/'), 'comprar-amazon-manecillas');
  assert.equal(classify(search, '/recomendaciones/', false, true), 'comprar-amazon-recomendaciones');
  assert.equal(classify(product, '/recomendaciones/libros/coraline/', false, true), 'comprar-amazon-recomendaciones');
  assert.equal(classify(product, '/autor.html'), 'comprar-amazon');
  assert.equal(classify('https://www.amazon.es/Nombre-del-libro/dp/B0GB6LGQFH?tag=davidporto-21', '/autor.html'), 'comprar-amazon');
  assert.equal(classify('https://www.amazon.es/Nombre-del-libro/gp/product/B0GB6LGQFH?tag=davidporto-21', '/recomendaciones/', false, true), 'comprar-amazon-recomendaciones');
});

test('no confundir Author Follow, otros dominios o subcadenas engañosas con compra', () => {
  assert.equal(classify('https://www.amazon.es/stores/author/B0GZFP1JV3'), null);
  assert.equal(classify('https://amazon.es.evil.test/dp/B0GB6LGQFH'), null);
  assert.equal(classify('https://notamazon.es/dp/B0GB6LGQFH'), null);
  assert.equal(classify('http://www.amazon.es/dp/B0GB6LGQFH'), null);
  assert.equal(classify('https://amzn.to/4zW6Yeu/mal'), null);
  assert.equal(classify('https://www.amazon.es/gp/'), null);
  assert.equal(classify('https://www.amazon.es/dp/B0GB6LGQFH#customerReviews'), null);
  assert.equal(classify('https://www.casadellibro.com/'), null);
});

test('todos los eventos están en autoridad y modal de Samuel queda separado', () => {
  for (const name of [
    'comprar-amazon', 'comprar-amazon-header', 'comprar-amazon-home',
    'comprar-amazon-samuel', 'comprar-amazon-manecillas',
    'comprar-amazon-recomendaciones', 'comprar-amazon-papel',
  ]) {
    assert.ok(names.has(name), 'Evento no registrado: ' + name);
  }
  assert.match(script, /if \(!link \|\| link\.closest\("#buy-dialog"\)\) return;/);
  const body = script.slice(script.indexOf('// Delegación imprescindible:'), script.indexOf('// Leer fragmento gratis --'));
  assert.match(body, /if \(category\) _gcEvent\(category,/);
  // Una emisión única para compra O reseña, y otra separada para Follow.
  assert.equal((body.match(/_gcEvent\(category,/g) || []).length, 1, 'Un solo evento para salida comercial/lectora');
  assert.equal((body.match(/_gcEvent\("seguir-autor-amazon",/g) || []).length, 1, 'Un solo evento de Follow');
});

// Ejecuta el listener real de script.js con un DOM mínimo simulado.
function runClick({ follow = false, dataset = {}, href, page = '/', inside = [], throwing = false }) {
  const events = [];
  let handler;
  const link = {
    href,
    dataset,
    getAttribute: () => href,
    closest: (sel) => (inside.includes(sel) ? {} : null),
    matches: (sel) => follow && sel.includes('amazon-author-follow-link'),
  };
  const section = script.slice(script.indexOf('function _readerReviewOutboundCategory('), script.indexOf('// Leer fragmento gratis --'));
  vm.runInNewContext(section, {
    URL,
    document: { addEventListener: (type, fn) => { if (type === 'click') handler = fn; } },
    window: { location: { pathname: page } },
    _gcEvent: (name) => { if (throwing) throw new Error('boom'); events.push(name); },
  });
  handler({ target: { closest: (sel) => (sel === 'a[href]' ? link : null) } });
  return events;
}

test('listener: exactamente un evento por clic y ninguno desde el modal de Samuel', () => {
  assert.deepEqual(runClick({ href: product }), ['comprar-amazon-home']);
  assert.deepEqual(runClick({ href: short, inside: ['.header-buy'] }), ['comprar-amazon-header']);
  assert.deepEqual(runClick({ href: product, page: '/libros/samuel-entre-mundos/', inside: ['#buy-dialog'] }), []);
  assert.deepEqual(runClick({ href: 'https://www.amazon.es/stores/author/B0GZFP1JV3' }), []);
  assert.deepEqual(runClick({ href: 'https://www.amazon.es/stores/author/B0GZFP1JV3', follow: true }), ['seguir-autor-amazon']);
});

test('listener: reseñas y Author Follow nunca cuentan como compra', () => {
  const review = 'https://www.amazon.es/dp/B0GB6LGQFH#customerReviews';
  assert.deepEqual(runClick({ href: review, page: '/libros/samuel-entre-mundos/', dataset: { readerReview: 'amazon', book: 'samuel' } }), ['visita-resenas-amazon-samuel']);
  assert.deepEqual(runClick({ href: review, page: '/libros/samuel-entre-mundos/' }), []);
  assert.deepEqual(runClick({ href: 'https://www.amazon.es/dp/OTRO000000#customerReviews', dataset: { readerReview: 'amazon', book: 'samuel' } }), []);
});
