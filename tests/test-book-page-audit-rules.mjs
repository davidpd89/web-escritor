import assert from 'node:assert/strict';
import { auditBookPageHtml } from '../assets/book-page-audit-rules.js';

const rich = `<!doctype html><html><head>
<title>La novela | Autora</title>
<meta name="description" content="Una descripción suficientemente larga para explicar la premisa, el conflicto y el tipo de lector al que puede interesarle esta novela contemporánea.">
<meta property="og:image" content="https://example.com/portada.webp">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Book","name":"La novela","isbn":"9781234567897","publisher":{"@type":"Organization","name":"Editorial X"},"datePublished":"2026-09-03","numberOfPages":272,"bookFormat":"https://schema.org/Paperback","author":{"@type":"Person","name":"Ana"}}<\/script>
</head><body><h1>La novela</h1><p>Autora: Ana. Ya disponible. ISBN 978-1-23456-789-7. Editorial X. 272 páginas. Tapa blanda.</p>
<img src="/portada.webp" alt="Portada de La novela"><a href="https://tienda.example/libro">Comprar</a>
<a href="/fragmento/">Leer un fragmento</a><a href="/prensa/">Kit de prensa</a></body></html>`;

const a = auditBookPageHtml(rich, { url: 'https://example.com/libro/' });
assert.equal(a.mode, 'book-page');
assert.equal(a.findings.core.find(x => x.id === 'book_title').status, 'ok');
assert.equal(a.findings.core.find(x => x.id === 'book_purchase').status, 'ok');
assert.equal(a.findings.metadata.find(x => x.id === 'book_isbn').status, 'ok');
assert.equal(a.findings.structured[0].status, 'ok');
assert.equal(a.findings.consistency.length, 0);

const isbnMismatch = rich.replace('978-1-23456-789-7', '978-9-87654-321-0');
assert.equal(auditBookPageHtml(isbnMismatch).findings.consistency.some(x => x.id === 'book_isbn_mismatch'), true);

const authorMismatch = rich.replace('Autora: Ana.', 'Autora: Beatriz.');
const authorResult = auditBookPageHtml(authorMismatch);
assert.equal(authorResult.findings.consistency.some(x => x.id === 'book_author_mismatch'), true);
assert.match(authorResult.findings.consistency.find(x => x.id === 'book_author_mismatch').evidence, /Beatriz.*Ana/);

const schemaOnlyIsbn = rich.replace(' ISBN 978-1-23456-789-7.', '');
assert.equal(auditBookPageHtml(schemaOnlyIsbn).findings.metadata.find(x => x.id === 'book_isbn').status, 'ok');

const minimal = '<html><head><title>Libro</title></head><body><h1>Libro</h1><p>Texto breve.</p></body></html>';
const c = auditBookPageHtml(minimal);
assert.equal(c.findings.core.find(x => x.id === 'book_purchase').status, 'review');
assert.equal(c.findings.structured[0].status, 'info');
assert.equal(c.findings.enriched.find(x => x.id === 'book_excerpt').status, 'optional');

const invalidJsonLd = '<html><body><h1>Libro</h1><script type="application/ld+json">{"@type":"Book",}</script></body></html>';
const d = auditBookPageHtml(invalidJsonLd);
assert.equal(d.findings.structured[0].id, 'book_schema_invalid');
assert.equal(d.findings.structured[0].status, 'review');
assert.equal(d.evidence.invalidJsonLdCount, 1);

const hostile = `<html><body><h1>Libro &amp; prueba</h1><p>Autora: Ana.</p><script>alert(1)</script><img src=x onerror=alert(1)><p>"</script>" & < > LOCAL_QA_SENTINEL_582931</p></body></html>`;
assert.doesNotThrow(() => auditBookPageHtml(hostile));
const hostileResult = auditBookPageHtml(hostile);
assert.equal(hostileResult.findings.core.find(x => x.id === 'book_title').status, 'ok');

assert.equal(auditBookPageHtml('').findings.core.find(x => x.id === 'book_title').status, 'review');

console.log('tests/test-book-page-audit-rules: OK');
