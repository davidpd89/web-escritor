import assert from 'node:assert/strict';
import fs from 'node:fs';

const BASE = process.env.QA_BASE_URL || process.env.BASE_URL || 'http://127.0.0.1:8000';
const css = fs.readFileSync('assets/v1-fonts.css', 'utf8');
const faces = [...css.matchAll(/@font-face\s*\{([^}]+)\}/g)].map(match => {
  const block = match[1];
  const family = block.match(/font-family:\s*['\"]?([^;'\"]+)/)?.[1]?.trim();
  const style = block.match(/font-style:\s*([^;]+)/)?.[1]?.trim();
  const weight = block.match(/font-weight:\s*([^;]+)/)?.[1]?.trim();
  const file = block.match(/url\(['\"]?([^)'\"]+\.woff2)['\"]?\)/)?.[1];
  return { family, style, weight, file };
}).filter(face => face.family && face.file);
assert(faces.length >= 8, `v1-fonts.css: solo ${faces.length} variantes encontradas`);
assert(faces.some(face => face.style === 'italic'), 'v1-fonts.css: no se descubrieron variantes cursivas');
assert(faces.some(face => face.weight?.includes(' ')), 'v1-fonts.css: no se descubrieron pesos variables');

const jobs = faces.flatMap(face => Array.from({ length: 3 }, () => face));
const results = await Promise.all(jobs.map(async face => {
  const url = new URL(face.file, new URL('/assets/v1-fonts.css', BASE));
  const response = await fetch(url, { signal: AbortSignal.timeout(15000) });
  assert.equal(response.status, 200, `${face.family}/${face.style}/${face.weight}: ${url.pathname} HTTP ${response.status}`);
  const bytes = Buffer.from(await response.arrayBuffer());
  assert(bytes.length > 100, `${face.family}/${face.style}/${face.weight}: ${url.pathname} vacío`);
  assert.equal(bytes.toString('ascii', 0, 4), 'wOF2', `${face.family}/${face.style}/${face.weight}: ${url.pathname} no es WOFF2`);
  return { face, size: bytes.length };
}));
for (const face of faces) {
  const sizes = new Set(results.filter(r => r.face === face).map(r => r.size));
  assert.equal(sizes.size, 1, `${face.family}/${face.style}/${face.weight}: tamaños distintos entre respuestas`);
}
console.log(`OK: ${faces.length} variantes tipográficas, ${jobs.length} peticiones concurrentes`);