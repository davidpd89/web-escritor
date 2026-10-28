import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';

const source = await fs.readFile(new URL('../cloudflare-worker-assistant.js', import.meta.url), 'utf8');
const context = vm.createContext({ Response, URL, Set });
vm.runInContext(source.replace('export default {', 'const worker = {') + '\nglobalThis.testOrigins = getAllowedOrigins; globalThis.testCors = corsHeaders;', context);

const origins = context.testOrigins({
  ASSISTANT_ALLOWED_ORIGINS: 'https://staging.example.com,http://insecure.example.com,https://example.com/path,https://user@example.com,*,https://preview.example.com:8443'
});
for (const origin of ['https://davidportodiaz.com', 'https://staging.example.com', 'https://preview.example.com:8443']) {
  assert.equal(origins.has(origin), true, `/api/assistant: origen HTTPS permitido ausente: ${origin}`);
}
for (const origin of ['http://insecure.example.com', 'https://example.com/path', 'https://user@example.com', '*', 'https://evil.example']) {
  assert.equal(origins.has(origin), false, `/api/assistant: origen no autorizado aceptado: ${origin}`);
}
const headers = context.testCors('https://staging.example.com');
assert.equal(headers['Access-Control-Allow-Origin'], 'https://staging.example.com');
assert.equal(headers.Vary, 'Origin', '/api/assistant: falta separación de caché por Origin');
assert.equal(headers['Access-Control-Allow-Credentials'], undefined, '/api/assistant: se habilitaron credenciales CORS sin necesidad');
assert.match(headers['Access-Control-Allow-Methods'], /POST/);
console.log('assistant-cors-origin-isolation: OK');