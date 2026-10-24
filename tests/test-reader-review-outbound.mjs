// Pruebas offline de URLs, CTAs y del listener delegado de reseñas.
// No navega, no crea cuentas y no envía eventos reales.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import vm from 'node:vm';
import test from 'node:test';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const read = p => readFileSync(resolve(root, p), 'utf8');
const script = read('script.js').replace(/\r\n/g, '\n');
const registry = JSON.parse(read('data/analytics-events.json'));
const byName = new Map(registry.events.map(x => [x.name, x]));

function isolatedFunction(name, closingComment) {
  const start = script.indexOf('function ' + name + '(');
  const end = script.indexOf('\n}\n\n' + closingComment, start);
  assert.ok(start !== -1 && end > start, 'Función pura no localizable: ' + name);
  return vm.runInNewContext('(' + script.slice(start, end + 2) + ')', { URL });
}
const review = isolatedFunction('_readerReviewOutboundCategory', '// Enlaces de compra');
const amazon = isolatedFunction('_amazonOutboundCategory', '// Delegación imprescindible:');

const links = {
  amazonSamuel: 'https://www.amazon.es/dp/B0GB6LGQFH#customerReviews',
  goodreadsSamuel: 'https://www.goodreads.com/book/show/245605636-samuel-entre-mundos',
  casaSamuel: 'https://www.casadellibro.com/libro-samuel-entre-mundos/9791387659776/17856720',
  goodreadsManecillas: 'https://www.goodreads.com/book/show/258289637-las-manecillas-del-recuerdo',
  casaManecillas: 'https://www.casadellibro.com/libro-las-manecillas-del-recuerdo/9798905149351/18668032',
};

test('rutas autorizadas generan eventos de clic, no reseñas publicadas', () => {
  for (const [url, platform, book, event] of [
    [links.amazonSamuel, 'amazon', 'samuel', 'visita-resenas-amazon-samuel'],
    [links.goodreadsSamuel, 'goodreads', 'samuel', 'visita-resenas-goodreads-samuel'],
    [links.casaSamuel, 'casa', 'samuel', 'visita-resenas-casa-samuel'],
    [links.goodreadsManecillas, 'goodreads', 'manecillas', 'visita-resenas-goodreads-manecillas'],
    [links.casaManecillas, 'casa', 'manecillas', 'visita-resenas-casa-manecillas']
  ]) {
    assert.equal(review(url, platform, book), event);
    assert.equal(byName.get(event)?.action, 'review_outbound');
  }
});

test('enlaces no autorizados o editados no simulan conversiones', () => {
  assert.equal(review('https://www.amazon.es/dp/B0GB6LGQFH', 'amazon', 'samuel'), null);
  assert.equal(review('https://amazon.es.fake.test/dp/B0GB6LGQFH#customerReviews', 'amazon', 'samuel'), null);
  assert.equal(review('http://www.amazon.es/dp/B0GB6LGQFH#customerReviews', 'amazon', 'samuel'), null);
  assert.equal(review('https://www.amazon.es/dp/INVALID999#customerReviews', 'amazon', 'samuel'), null);
  assert.equal(review(links.casaSamuel, 'goodreads', 'samuel'), null);
  assert.equal(review(links.goodreadsSamuel, 'goodreads', 'manecillas'), null);
  assert.equal(review('javascript:alert(1)', 'goodreads', 'samuel'), null);
  assert.equal(review('https://www.casadellibro.com/libro-samuel-entre-mundos/9791387659776/17856720', 'casa', '__proto__'), null);
});

test('Amazon no interpreta customerReviews como compra aunque falte marcador', () => {
  assert.equal(amazon(links.amazonSamuel, '/autor.html', false, false), null);
  assert.equal(amazon(links.amazonSamuel.toLowerCase().replace('#customerreviews', '#CUSTOMERREVIEWS'), '/', false, false), null);
  assert.equal(amazon('https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21', '/autor.html', false, false), 'comprar-amazon');
  assert.equal(amazon('https://amzn.to/4zW6Yeu', '/', true, false), 'comprar-amazon-header');
});

test('HTML: cada enlace marcado corresponde a un destino y libro real', () => {
  for (const [file, expected] of [
    ['autor.html', [['amazon', 'samuel'], ['goodreads', 'samuel']]],
    ['libros/samuel-entre-mundos/index.html', [['amazon', 'samuel'], ['goodreads', 'samuel'], ['casa', 'samuel']]],
    ['las-manecillas-del-recuerdo/index.html', [['goodreads', 'manecillas'], ['casa', 'manecillas']]]
  ]) {
    const anchors = [...read(file).matchAll(/<a\b[^>]*\bdata-reader-review="([^"]+)"[^>]*>[\s\S]*?<\/a>/g)];
    assert.equal(anchors.length, expected.length, file);
    for (const [i, match] of anchors.entries()) {
      const [platform, book] = expected[i];
      const html = match[0];
      assert.match(html, new RegExp('data-reader-review="' + platform + '"'));
      assert.match(html, new RegExp('data-book="' + book + '"'));
      const href = html.match(/\bhref="([^"]+)"/)?.[1];
      assert.ok(href);
      assert.ok(review(href, platform, book), 'URL incorrecta en ' + file);
      assert.match(html, /rel="noopener noreferrer"/);
      assert.doesNotMatch(html, /tag=|sponsored/);
    }
  }
});

test('listener real emite un solo evento por clic saliente de opiniones', () => {
  const start = script.indexOf('// Delegación imprescindible:');
  const end = script.indexOf('// Leer fragmento gratis --', start);
  assert.ok(start > -1 && end > start);
  let clickHandler;
  let emitted = [];
  const mock = {
    document: {
      addEventListener(type, fn) { if (type === 'click') clickHandler = fn; }
    },
    _readerReviewOutboundCategory: review,
    _amazonOutboundCategory: amazon,
    window: { location: { pathname: '/libros/samuel-entre-mundos/' } },
    URL,
    _gcEvent(name) { emitted.push(name); }
  };
  vm.runInNewContext(script.slice(start, end), mock);
  assert.equal(typeof clickHandler, 'function');

  function click(url, provider, book, follow = false, modal = false) {
    emitted = [];
    const link = {
      href: url,
      dataset: { readerReview: provider, book },
      closest(sel) { return sel === '#buy-dialog' ? (modal ? {} : null) : null; },
      matches() { return follow; }
    };
    clickHandler({ target: { closest() { return link; } } });
    return emitted.slice();
  }
  assert.deepEqual(click(links.amazonSamuel, 'amazon', 'samuel'), ['visita-resenas-amazon-samuel']);
  assert.deepEqual(click(links.goodreadsSamuel, 'goodreads', 'samuel'), ['visita-resenas-goodreads-samuel']);
  assert.deepEqual(click('https://www.amazon.es/dp/B0GB6LGQFH', 'amazon', 'samuel'), []);
  assert.deepEqual(click('https://www.amazon.es/dp/B0GB6LGQFH#customerReviews', undefined, 'samuel'), []);
  assert.deepEqual(click('https://www.amazon.es/dp/B0GB6LGQFH', undefined, 'samuel'), ['comprar-amazon-samuel']);
  assert.deepEqual(click('https://www.amazon.es/dp/B0GB6LGQFH', undefined, 'samuel', false, true), []);
  assert.deepEqual(click('https://www.amazon.es/stores/author/B0GZFP1JV3', undefined, 'samuel', true), ['seguir-autor-amazon']);
});

test('evento de seguimiento de la PR hermana se mantiene y no se solapa', () => {
  assert.equal(byName.get('seguir-autor-amazon')?.action, 'author_follow_outbound');
  assert.match(script, /_gcEvent\("seguir-autor-amazon",/);
});
