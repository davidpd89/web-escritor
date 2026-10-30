import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

// El respaldo de copia (document.execCommand) devuelve false cuando falla: el botón
// no debe anunciar «Copiado» entonces. Se comprueba en el código fuente porque este
// contrato corre en el gate universal, sin navegador.
const source = readFileSync(new URL('../script.js', import.meta.url), 'utf8');
const fallback = source.split('\n').filter((line) => line.includes('document.execCommand("copy")'));
assert.equal(fallback.length, 1, 'script.js debe tener un único respaldo execCommand("copy")');
assert.match(fallback[0], /if\s*\(\s*document\.execCommand\("copy"\)\s*\)\s*done\(\)/,
  'el respaldo de copia debe confirmar solo si execCommand devuelve true');
console.log('PASS clipboard failure acknowledgement');
