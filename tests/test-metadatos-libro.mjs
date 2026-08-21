import assert from 'node:assert/strict';
import { buildMetaTags, validateMetaTags, httpsUrl } from '../assets/metadatos-libro.js';

const valid = {
  book: 'La casa de prueba',
  author: 'Ana Ejemplo',
  site: 'Ana Ejemplo',
  url: 'https://example.test/libros/la-casa/',
  description: 'Una novela de prueba sobre memoria, familia y las decisiones que dejan huella.',
  image: 'https://assets.example.test/portada social.webp',
  imageAlt: 'Portada de «La casa de prueba» & autora',
  isbn: '978-1-23456-789-0',
  releaseDate: '2026-09-03',
  authorUrl: 'https://example.test/ana/',
  xSite: 'anaejemplo',
};

assert.equal(httpsUrl('https://example.test/book'), 'https://example.test/book');
assert.equal(httpsUrl('http://example.test/book'), '');
assert.equal(httpsUrl('javascript:alert(1)'), '');
assert.equal(httpsUrl('not a url'), '');

const built = buildMetaTags(valid);
assert.equal(built.canonical, valid.url);
assert.equal(built.image, 'https://assets.example.test/portada%20social.webp');
assert.match(built.lines, /book:isbn" content="9781234567890"/);
assert.match(built.lines, /twitter:site" content="@anaejemplo"/);
assert.deepEqual(validateMetaTags(valid, built), []);

const minimum = { book: 'Libro mínimo' };
const minimumBuilt = buildMetaTags(minimum);
assert.ok(!minimumBuilt.lines.includes('og:url'));
assert.ok(!minimumBuilt.lines.includes('og:image"'));
assert.ok(!minimumBuilt.lines.includes('book:isbn'));
assert.ok(!minimumBuilt.lines.includes('book:release_date'));
assert.ok(validateMetaTags(minimum, minimumBuilt).length >= 3);

const longTitle = buildMetaTags({ ...valid, book: 'Título '.repeat(20) });
assert.ok(validateMetaTags({ ...valid, book: 'Título '.repeat(20) }, longTitle).some(x => x.includes('título social')));

const longDescriptionValue = { ...valid, description: 'Descripción '.repeat(30) };
assert.ok(validateMetaTags(longDescriptionValue, buildMetaTags(longDescriptionValue)).some(x => x.includes('descripción es larga')));

assert.ok(validateMetaTags({ ...valid, description: '' }, buildMetaTags({ ...valid, description: '' })).some(x => x.includes('descripción específica')));
assert.equal(buildMetaTags({ ...valid, url: 'http://example.test/libro' }).canonical, '');
assert.equal(buildMetaTags({ ...valid, url: 'https://exa mple.test' }).canonical, '');
assert.equal(buildMetaTags({ ...valid, url: 'https://example.test/libro' }).canonical, 'https://example.test/libro');
assert.equal(buildMetaTags({ ...valid, image: 'javascript:alert(1)' }).image, '');
assert.ok(validateMetaTags({ ...valid, authorUrl: 'javascript:alert(1)' }, buildMetaTags({ ...valid, authorUrl: 'javascript:alert(1)' })).some(x => x.includes('perfil del autor')));
assert.ok(validateMetaTags({ ...valid, image: 'https://assets.example.test/a.webp', imageAlt: '' }, buildMetaTags({ ...valid, image: 'https://assets.example.test/a.webp', imageAlt: '' })).some(x => x.includes('texto alternativo')));

for (const patch of [{isbn:''},{releaseDate:''}]) {
  const out = buildMetaTags({ ...valid, ...patch }).lines;
  if ('isbn' in patch) assert.equal(out.includes('book:isbn'), false);
  if ('releaseDate' in patch) assert.equal(out.includes('book:release_date'), false);
}

const hostile = buildMetaTags({
  ...valid,
  book: 'Niña & «mar» <script>alert(1)</script>',
  author: 'Ana "Ejemplo"',
  site: 'Sitio > prueba',
  description: '"</script>" & < > ñ',
  imageAlt: '"><svg onload=alert(1)>',
  xSite: '"><img src=x onerror=alert(1)>',
});
assert.ok(hostile.lines.includes('&amp;'));
assert.ok(hostile.lines.includes('&lt;script&gt;alert(1)&lt;/script&gt;'));
assert.ok(hostile.lines.includes('&quot;'));
assert.equal(hostile.lines.includes('<svg onload='), false);
assert.equal(hostile.lines.includes('<img src=x'), false);

console.log('tests/test-metadatos-libro: OK');
