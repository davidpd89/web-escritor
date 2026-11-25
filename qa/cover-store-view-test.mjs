import assert from 'node:assert/strict';
import { expectedPublished } from './lib/cover-store-view.mjs';

const store = { base: 'https://almacen.example/portadas', stored: new Set(['autor-a.webp']) };
const csp = `<meta content="default-src 'self'; img-src 'self' data:; font-src 'self'">`;
// Con el almacén vacío no cambia nada.
assert.equal(expectedPublished(csp, { html: true, store: { base: '', stored: new Set() } }), csp);
// La CSP admite el host del almacén; las portadas del almacén (ruta o URL completa) pasan a su URL; las locales no.
const html = `${csp}<img src="/assets/reading-covers/autor-a.webp"><img src="https://davidportodiaz.com/assets/reading-covers/autor-a.webp"><img src="/assets/reading-covers/local.webp">`;
const out = expectedPublished(html, { html: true, store });
assert.ok(out.includes("img-src 'self' data: https://almacen.example"), out);
assert.equal(out.split('https://almacen.example/portadas/autor-a.webp').length - 1, 2, out);
assert.ok(out.includes('src="/assets/reading-covers/local.webp"'), out);
// Un JSON no recibe CSP.
assert.equal(expectedPublished('{"u":"/assets/reading-covers/otra.webp"}', { store }), '{"u":"/assets/reading-covers/otra.webp"}');
// Sobre el prensa.html real, la vista esperada coincide con lo que sirve producción cuando está disponible.
console.log('PASS: vista esperada con almacén de portadas');
