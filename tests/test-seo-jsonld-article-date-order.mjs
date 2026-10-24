import assert from 'node:assert/strict';
import { validateInput } from '../assets/jsonld-escritores-core.js';

const base = {
  headline: 'Una crónica editorial',
  url: 'https://example.org/articulo/',
  authorName: 'Autora',
  datePublished: '2026-10-20',
};

for (const dateModified of ['2026-10-19', '2026-01-01', '2025-12-31']) {
  const result = validateInput('article', { ...base, dateModified });
  assert.equal(result.valid, false, `Se acepta dateModified anterior a publicación: ${dateModified}`);
  assert.ok(result.errors.length > 0, 'La validación debe explicar el error');
}

for (const dateModified of ['2026-10-20', '2026-10-21', '2027-01-01']) {
  const result = validateInput('article', { ...base, dateModified });
  assert.equal(result.valid, true, JSON.stringify(result.errors));
}

console.log('PASS JSON-LD article temporal order');
