import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import vm from 'node:vm';

const source = readFileSync(resolve('assets/newsletter-general.js'), 'utf8');
const document = {
  readyState: 'loading',
  addEventListener() {},
  querySelectorAll() { return []; }
};
const window = { location: { hostname: 'davidportodiaz.com' } };
const context = vm.createContext({ window, document, URL, AbortController, setTimeout, clearTimeout });
vm.runInContext(source, context, { filename: 'assets/newsletter-general.js' });
const api = window.DPNewsletterGeneral;
assert(api && typeof api.errorMessage === 'function', 'assets/newsletter-general.js: falta API de mensajes');

const cases = ['offline', 'timeout', 'rate_limited', 'network_error', 'server_error', 'invalid_response'];
for (const code of cases) {
  const message = api.errorMessage(code);
  assert.equal(typeof message, 'string', `newsletter ${code}: mensaje no textual`);
  assert(message.trim().length >= 20, `newsletter ${code}: mensaje demasiado breve: ${message}`);
  assert(/[.!…]$/.test(message.trim()), `newsletter ${code}: mensaje sin cierre: ${message}`);
  assert(!/\b(?:undefined|null|NaN|AbortError|TypeError|HTTP\s*\d{3})\b/i.test(message),
    `newsletter ${code}: se muestra un detalle técnico: ${message}`);
  assert(!/https?:\/\/|\.html\b|\.js\b|workers\.dev/i.test(message),
    `newsletter ${code}: referencia técnica o ruta de archivo visible: ${message}`);
  assert(!/\b(?:please try again|request failed|network error|internal server error)\b/i.test(message),
    `newsletter ${code}: texto de error sin traducir: ${message}`);
}

assert.match(api.errorMessage('offline'), /conexi[oó]n|red/i,
  'newsletter offline: debe explicar el problema de conexión');
assert.match(api.errorMessage('timeout'), /tardando|tiempo|espera/i,
  'newsletter timeout: debe explicar la espera');
assert.match(api.errorMessage('rate_limited'), /intentos|espera|demasiad/i,
  'newsletter rate_limited: debe explicar el límite');
console.log(`PASS newsletter error copy: ${cases.length} estados reales`);
