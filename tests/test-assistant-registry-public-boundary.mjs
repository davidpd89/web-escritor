import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';

const workerSource = await fs.readFile(new URL('../cloudflare-worker-assistant.js', import.meta.url), 'utf8');
const registry = JSON.parse(await fs.readFile(new URL('../data/assistant-source-registry.json', import.meta.url), 'utf8'));
const context = vm.createContext({ URL, Set });
vm.runInContext(workerSource.replace('export default {', 'const worker = {') + '\nglobalThis.validate = validateRegistry;', context);

assert.equal(context.validate(registry), true, '/data/assistant-source-registry.json: el registro público real no supera la validación del Worker');
const clone = () => structuredClone(registry);

const privateRegistry = clone();
privateRegistry.sources[0].visibility = 'private';
assert.equal(context.validate(privateRegistry), false, 'Registro RAG: se acepta una fuente privada');

const externalRegistry = clone();
externalRegistry.sources[0].url = 'https://example.com/documento';
assert.equal(context.validate(externalRegistry), false, 'Registro RAG: se acepta un destino externo');

const protocolRelative = clone();
protocolRelative.sources[0].url = '//example.com/documento';
assert.equal(context.validate(protocolRelative), false, 'Registro RAG: se acepta un enlace relativo al protocolo');

const duplicate = clone();
duplicate.sources.push(structuredClone(duplicate.sources[0]));
assert.equal(context.validate(duplicate), false, 'Registro RAG: se aceptan identificadores duplicados');

for (const source of registry.sources) {
  assert.equal(source.visibility, 'public', `Registro RAG: ${source.id} no es público`);
  assert.ok(source.url.startsWith('/') && !source.url.startsWith('//'), `Registro RAG: ${source.id} tiene URL no interna: ${source.url}`);
}
console.log('assistant-registry-public-boundary: OK');