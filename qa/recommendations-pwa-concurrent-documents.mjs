import assert from 'node:assert/strict';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const routes = [
  '/recomendaciones/',
  '/recomendaciones/portal-fantasy-espanol/',
  '/recomendaciones/magia-con-coste/',
  '/recomendaciones/libros/coraline/'
];

const baseline = new Map();

async function read(route) {
  const response = await fetch(new URL(route, BASE), {
    signal: AbortSignal.timeout(15000)
  });
  assert.equal(response.status, 200, `${route}: HTTP ${response.status}`);
  assert.match(response.headers.get('content-type') || '', /text\/html/i, `${route}: Content-Type incorrecto`);
  const html = await response.text();
  assert(html.length > 1000, `${route}: HTML vacío o truncado (${html.length} caracteres)`);
  assert.match(html, /<main\b/i, `${route}: falta main`);
  assert.match(html, /<\/html\s*>/i, `${route}: documento incompleto`);
  const title = html.match(/<title\b[^>]*>([^<]+)<\/title>/i)?.[1]?.trim();
  assert(title, `${route}: falta título documental`);
  return { html, title };
}

for (const route of routes) baseline.set(route, await read(route));

const requests = Array.from({ length: 48 }, (_, i) => routes[i % routes.length]);
const results = await Promise.all(requests.map(async route => ({ route, result: await read(route) })));

for (const { route, result } of results) {
  assert.equal(result.title, baseline.get(route).title, `${route}: identidad alterada durante carga`);
  assert.equal(result.html, baseline.get(route).html, `${route}: bytes HTML distintos de la respuesta de referencia`);
}

console.log(`OK: ${results.length} respuestas concurrentes de ${routes.length} documentos reales`);
