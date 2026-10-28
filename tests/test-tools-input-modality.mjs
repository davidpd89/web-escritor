import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const html = fs.readFileSync('herramientas/dialogo/index.html', 'utf8');
const script = fs.readFileSync('qa/tools-browser.mjs', 'utf8');

assert.match(html, /id="dialogue-text"/);
assert.match(script, /#dialogue-text/);
assert.match(script, /\[data-dialogue-results\]/);

const samples = [
  '—¿Qué haces? —preguntó Ana.\n—Nada.',
  '«Volveré», dijo Lucía.\n¡Mañana!',
  'Árbol, árbol; pingüino.\nNiño y niña.',
  'Primera línea\r\nSegunda línea\r\nTercera línea'
];

for (const sample of samples) {
  const typed = Array.from(sample).join('');
  const pasted = sample;
  const replaced = 'texto provisional'.replace('texto provisional', sample);
  assert.equal(typed, pasted);
  assert.equal(replaced, pasted);
  assert.equal([...typed].length, [...pasted].length);
}

console.log('OK: corpus Unicode y modalidades de entrada preparado');