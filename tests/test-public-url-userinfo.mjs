// Los generadores públicos (JSON-LD, metadatos de libro y kit de prensa) no
// pueden dar por válida una URL con usuario o contraseña embebidos: acabaría
// copiada en metadatos y ficheros pensados para publicarse. Se rechaza con
// un aviso propio que no repite la credencial. Fixtures 100 % sintéticos.
import assert from 'node:assert/strict';
import { buildJsonLd, validateInput } from '../assets/jsonld-escritores-core.js';
import { buildMetaTags, validateMetaTags } from '../assets/metadatos-libro.js';
import { validatePressKitModel } from '../assets/kit-prensa-core.js';

const SECRET = 'demo-pass-7Q';
const rejected = [
  `https://demo-user:${SECRET}@example.com/libro`,
  'https://demo-user@example.com/libro',
  `https://:${SECRET}@example.com/libro`,
  `https://demo%40user:${encodeURIComponent(SECRET + ':/')}@example.com/libro`,
];
const accepted = [
  'https://example.com/libro',
  'https://example.com/libro?utm_source=x&a=1,2#capitulo-1',
  'https://example.com/ruta%20con%20espacios/',
];

// Los mensajes de fallo tampoco deben imprimir la credencial.
const redact = (u) => u.replace(/\/\/[^@/]*@/, '//***@');

function assertNoSecret(messages, context) {
  const text = messages.join('\n');
  assert.ok(!text.includes(SECRET) && !text.includes(encodeURIComponent(SECRET)), `${context}: el aviso no debe mostrar la contraseña`);
  assert.ok(!text.includes('demo-user') && !text.includes('demo%40user'), `${context}: el aviso no debe mostrar el usuario`);
}

// --- JSON-LD ---
for (const url of rejected) {
  for (const [field, label] of [['url', 'canónica'], ['image', 'imagen']]) {
    const data = { name: 'Autora de prueba', url: 'https://example.com/perfil', [field]: url };
    const { errors } = validateInput('profile', data);
    assert.ok(errors.some((e) => /usuario ni contraseña/.test(e)), `JSON-LD ${field} (${label}) debe rechazar userinfo: ${redact(url)}`);
    assertNoSecret(errors, `JSON-LD ${field}`);
  }
  const same = validateInput('profile', { name: 'Autora de prueba', url: 'https://example.com/perfil', sameAs: `https://example.org/a\n${url}` });
  assert.ok(same.errors.some((e) => /usuario ni contraseña/.test(e)), `JSON-LD sameAs debe rechazar userinfo: ${redact(url)}`);
  assertNoSecret(same.errors, 'JSON-LD sameAs');
  const book = validateInput('book', { name: 'Libro', url: 'https://example.com/libro', authorName: 'Autora', authorUrl: url });
  assert.ok(book.errors.some((e) => /usuario ni contraseña/.test(e)), `JSON-LD authorUrl debe rechazar userinfo: ${redact(url)}`);
  // La vista previa (visible aunque no se pueda copiar) tampoco lleva la credencial.
  const preview = JSON.stringify([
    buildJsonLd('profile', { name: 'A', url, image: url, sameAs: `https://example.org/a
${url}` }),
    buildJsonLd('book', { name: 'L', url, authorName: 'A', authorUrl: url }),
    buildJsonLd('event', { name: 'E', url, organizerName: 'O', organizerUrl: url }),
  ]);
  assert.ok(!preview.includes('@example.com'), `JSON-LD: la vista previa no debe copiar userinfo: ${redact(url)}`);
  assert.ok(preview.includes('https://example.org/a'), 'JSON-LD: el resto de sameAs se conserva');
}
for (const url of accepted) {
  // sameAs admite varias URL separadas por salto de línea o coma; la coma de
  // la query no es un caso de esta regresión.
  const { errors } = validateInput('profile', { name: 'Autora de prueba', url, image: url, sameAs: url.replace(/,/g, '%2C') });
  assert.deepEqual(errors, [], `JSON-LD debe aceptar ${url}`);
}

// --- Metadatos de libro ---
const meta = { book: 'Libro', description: 'Descripción', url: 'https://example.com/libro', image: 'https://example.com/p.jpg', imageAlt: 'Portada' };
for (const url of rejected) {
  for (const field of ['url', 'image', 'authorUrl']) {
    const v = { ...meta, [field]: url };
    const built = buildMetaTags(v);
    assert.ok(!built.lines.includes('@example.com'), `metadatos ${field}: la salida no debe contener userinfo`);
    const items = validateMetaTags(v, built);
    assert.ok(items.some((e) => /usuario ni contraseña/.test(e)), `metadatos ${field} debe rechazar userinfo: ${redact(url)}`);
    assertNoSecret(items, `metadatos ${field}`);
  }
}
for (const url of accepted) {
  const v = { ...meta, url, authorUrl: url };
  const built = buildMetaTags(v);
  assert.equal(built.canonical, new URL(url).href, `metadatos debe conservar ${url}`);
  assert.deepEqual(validateMetaTags(v, built), [], `metadatos debe aceptar ${url}`);
}

// --- Kit de prensa ---
const kit = { authorName: 'Autora', contactEmail: 'prensa@example.com', bioShort: 'Bio', bookTitle: 'Libro', bookDescription: 'Sinopsis', assetPermission: 'contact_only' };
for (const url of rejected) {
  for (const field of ['website', 'purchaseUrl']) {
    const errors = validatePressKitModel({ ...kit, [field]: url });
    assert.ok(errors.some((e) => /usuario ni contraseña/.test(e)), `kit ${field} debe rechazar userinfo: ${redact(url)}`);
    assertNoSecret(errors, `kit ${field}`);
  }
}
for (const url of accepted) {
  assert.deepEqual(validatePressKitModel({ ...kit, website: url, purchaseUrl: url }), [], `kit debe aceptar ${url}`);
}

console.log('test-public-url-userinfo: OK');
