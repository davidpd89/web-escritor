import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';

const source = await fs.readFile(new URL('../cloudflare-worker-assistant.js', import.meta.url), 'utf8');
const calls = [];
const context = vm.createContext({
  URL,
  Set,
  Response,
  fetch: async (url, options) => {
    calls.push({ url: String(url), options });
    return Response.json({ choices: [{ message: { content: 'Respuesta pública. [author]' } }] });
  }
});
vm.runInContext(source.replace('export default {', 'const worker = {') + '\nglobalThis.providers = PROVIDER_CHAIN; globalThis.runTestProvider = runProvider;', context);

const env = {
  GROQ_API_KEY: 'secret-groq-test',
  OPENROUTER_API_KEY: 'secret-openrouter-test'
};
const expected = new Map([
  ['groq', 'https://api.groq.com/openai/v1/chat/completions'],
  ['openrouter', 'https://openrouter.ai/api/v1/chat/completions']
]);
for (const provider of context.providers.filter(p => expected.has(p.id))) {
  calls.length = 0;
  const answer = await context.runTestProvider(provider, env, 'Instrucciones públicas del asistente', 'Pregunta sobre libros y contexto público');
  assert.equal(answer, 'Respuesta pública. [author]', `Proveedor ${provider.id}: respuesta no interpretada`);
  assert.equal(calls.length, 1, `Proveedor ${provider.id}: número inesperado de solicitudes salientes`);
  const { url, options } = calls[0];
  assert.equal(url, expected.get(provider.id), `Proveedor ${provider.id}: destino saliente inesperado`);
  assert.equal(options.method, 'POST', `Proveedor ${provider.id}: método incorrecto`);
  assert.equal(options.headers['Content-Type'], 'application/json', `Proveedor ${provider.id}: formato incorrecto`);
  const secret = provider.id === 'groq' ? env.GROQ_API_KEY : env.OPENROUTER_API_KEY;
  assert.equal(options.headers.Authorization, `Bearer ${secret}`, `Proveedor ${provider.id}: autorización incorrecta`);
  assert.equal(url.includes(secret), false, `Proveedor ${provider.id}: secreto filtrado en URL`);
  assert.equal(options.body.includes(secret), false, `Proveedor ${provider.id}: secreto filtrado en JSON`);
  const body = JSON.parse(options.body);
  assert.equal(body.messages.length, 2, `Proveedor ${provider.id}: mensajes inesperados`);
  assert.deepEqual(Array.from(body.messages, m => m.role), ['system', 'user'], `Proveedor ${provider.id}: roles incorrectos`);
  for (const [key, value] of Object.entries(options.headers)) {
    if (key !== 'Authorization') assert.equal(String(value).includes(secret), false, `Proveedor ${provider.id}: secreto filtrado en cabecera ${key}`);
  }
}
console.log('assistant-provider-egress-privacy: OK');