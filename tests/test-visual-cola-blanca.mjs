// La comparación visual ignora la cola de filas blancas puras de una captura fullPage (relleno al encoger la
// página), pero un cambio de alto del contenido sigue detectándose.
import assert from 'node:assert/strict';
import { trimWhiteTail } from '../qa/png-cola-blanca.mjs';

function png(rows) { // rows: array de colores [r,g,b] por fila, ancho 2
  const data = Buffer.alloc(rows.length * 2 * 4);
  rows.forEach((c, y) => { for (let x = 0; x < 2; x += 1) data.set([...c, 255], (y * 2 + x) * 4); });
  return { width: 2, height: rows.length, data };
}
const OSCURO = [24, 20, 18]; const BLANCO = [255, 255, 255];
const a = trimWhiteTail(png([OSCURO, OSCURO, BLANCO, BLANCO, BLANCO]));
const b = trimWhiteTail(png([OSCURO, OSCURO, BLANCO]));
assert.equal(a.height, 2); assert.equal(b.height, 2);
assert.deepEqual(Buffer.from(a.data), Buffer.from(b.data));
const sinCola = png([OSCURO, BLANCO, OSCURO]);
assert.equal(trimWhiteTail(sinCola), sinCola, 'el blanco intermedio es contenido');
assert.notEqual(trimWhiteTail(png([OSCURO, OSCURO, OSCURO, BLANCO])).height, a.height, 'más contenido = otro alto');
console.log('tests/test-visual-cola-blanca: OK');
