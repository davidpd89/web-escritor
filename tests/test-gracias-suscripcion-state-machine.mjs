import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';

const html = await fs.readFile(new URL('../gracias-suscripcion/index.html', import.meta.url), 'utf8');
const head = html.split('</head>')[0];
const scripts = [...head.matchAll(/<script(?![^>]*\bsrc=)(?![^>]*\btype=['"]application\/ld\+json['"])[^>]*>([\s\S]*?)<\/script>/gi)].map(m => m[1]);
assert.ok(scripts.length, 'Debe existir lógica de estado evaluable');

for (const initial of [null, '0', 'pending_confirmation', '1']) {
  const values = new Map();
  if (initial !== null) values.set('nl-subscribed', initial);
  const writes = [];
  const localStorage = {
    getItem: key => values.get(key) ?? null,
    setItem(key, value) { writes.push([key, String(value)]); values.set(key, String(value)); },
    removeItem: key => values.delete(key)
  };
  const context = vm.createContext({localStorage});
  for (const script of scripts) vm.runInContext(script, context, {timeout: 1000});
  if (initial !== '1') {
    assert.notEqual(values.get('nl-subscribed'), '1', `La visita directa convirtió ${initial} en confirmado`);
    assert.ok(!writes.some(([key, value]) => key === 'nl-subscribed' && value === '1'), 'Confirmación no acreditada');
  }
}
console.log('gracias-suscripcion state machine: PASS');
