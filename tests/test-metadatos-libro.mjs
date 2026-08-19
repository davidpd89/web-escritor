import assert from 'node:assert/strict';
import { buildMetaTags, validateMetaTags, httpsUrl } from '../assets/metadatos-libro.js';

// httpsUrl: only accepts valid https URLs
assert.equal(httpsUrl('https://example.com/book'), 'https://example.com/book');
assert.equal(httpsUrl('http://example.com/book'), '');
assert.equal(httpsUrl('not a url'), '');

const values = {
  book: 'Las manecillas del recuerdo',
  author: 'David Porto Díaz',
  site: 'David Porto Díaz',
  url: 'https://davidportodiaz.com/las-manecillas-del-recuerdo/',
  description: 'Novela coral sobre memoria familiar y objetos heredados.',
  image: 'https://davidportodiaz.com/assets/las-manecillas-del-recuerdo-social.webp',
  imageAlt: 'Portada de Las manecillas del recuerdo',
  isbn: '979-8-90514-935-1',
  releaseDate: '2026-09-03',
  authorUrl: 'https://davidportodiaz.com/autor.html',
  xSite: 'davidportodiaz',
};

const built = buildMetaTags(values);
assert.equal(built.canonical, values.url);
assert.equal(built.image, values.image);
assert.equal(built.title, 'Las manecillas del recuerdo — David Porto Díaz | David Porto Díaz');
assert.equal(built.socialTitle, 'Las manecillas del recuerdo — David Porto Díaz');
assert.match(built.lines, /<title>Las manecillas del recuerdo — David Porto Díaz \| David Porto Díaz<\/title>/);
assert.match(built.lines, /<meta property="book:isbn" content="9798905149351">/);
assert.match(built.lines, /<meta name="twitter:site" content="@davidportodiaz">/);

// A complete, well-formed set of values should produce zero warnings
assert.deepEqual(validateMetaTags(values, built), []);

// HTML-escaping in the generated block
const withMarkup = buildMetaTags({ ...values, description: 'Historias de "familia" & recuerdos' });
assert.match(withMarkup.lines, /content="Historias de &quot;familia&quot; &amp; recuerdos"/);

// Missing required fields surface warnings
const empty = buildMetaTags({});
const issues = validateMetaTags({}, empty);
assert.ok(issues.includes('Añade el título del libro.'));
assert.ok(issues.includes('Falta la URL canónica.'));
assert.ok(issues.includes('Falta una imagen social.'));

// Non-HTTPS URL is rejected, not silently downgraded
const insecure = buildMetaTags({ ...values, url: 'http://davidportodiaz.com/las-manecillas-del-recuerdo/' });
assert.equal(insecure.canonical, '');
assert.ok(validateMetaTags({ ...values, url: 'http://davidportodiaz.com/x/' }, insecure)
  .includes('La URL canónica debe ser una URL HTTPS válida.'));

console.log('tests/test-metadatos-libro: OK');
