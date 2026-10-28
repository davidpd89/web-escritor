import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';

const source = await fs.readFile(new URL('../cloudflare-worker-assistant.js', import.meta.url), 'utf8');
const context = vm.createContext({ Response, JSON });
vm.runInContext(source.replace('export default {', 'const worker = {') + '\nglobalThis.testJson = json;', context);

for (const status of [200, 400, 403, 429, 502, 503]) {
  const response = context.testJson('https://davidportodiaz.com', status, {
    ok: status === 200,
    answer: 'Consulta privada del visitante',
    code: status === 200 ? undefined : 'error'
  });
  assert.equal(response.status, status, `/api/assistant: estado HTTP ${status}`);
  assert.equal(response.headers.get('Cache-Control'), 'no-store', `/api/assistant: estado ${status} permite almacenar respuestas privadas`);
  assert.match(response.headers.get('Content-Type') || '', /^application\/json\b/i, `/api/assistant: Content-Type incorrecto para ${status}`);
  assert.equal(response.headers.get('X-Content-Type-Options'), 'nosniff', `/api/assistant: falta nosniff en ${status}`);
  assert.equal(response.headers.get('Access-Control-Allow-Origin'), 'https://davidportodiaz.com', `/api/assistant: origen incorrecto en ${status}`);
}
console.log('assistant-response-cache-privacy: OK');