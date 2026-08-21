import assert from 'node:assert/strict';
import { analyze, pair, strip } from '../assets/nombres-personajes-engine.js';

const sample = ['Ana', 'Anah', 'Ana Díaz', 'Bruno', 'Brunó'];
const res = analyze(sample);
assert.equal(res.names.length, 5);
assert(Array.isArray(res.pairs));

// Los 4 ejemplos que el propio documento 34 (sección 7, "Ejemplos esperados")
// da como clasificación esperada.
const marco = pair('Marco', 'Marcos');
assert.equal(marco.level, 'high', 'Marco/Marcos debe ser "alerta alta"');

const lara = pair('Lara', 'Lana');
assert(['high', 'medium'].includes(lara.level), 'Lara/Lana debe ser "alta/media"');

const ana = pair('Ana', 'Antía');
assert.equal(ana.level, 'low', 'Ana/Antía: el resto de rasgos reduce la puntuación por debajo de alta/media');
assert(ana.reasons.includes('misma inicial'), 'Ana/Antía debe señalar la inicial compartida');

const cibran = pair('Cibrán', 'Xurxo');
assert.equal(cibran.level, 'low', 'Cibrán/Xurxo debe ser "baja"');

// Bug real encontrado y corregido: analyze() deduplicaba con un Set() sobre
// el texto exacto, así que "Noa"/"noa"/"NOA" (el mismo nombre tecleado con
// distinta caja — un accidente de entrada real, no dos personajes) no se
// eliminaban como pide el documento ("duplicados de entrada se eliminan").
// En vez de desaparecer, llegaban los tres a pair(), que SÍ reconoce que es
// el mismo nombre normalizado y los marcaba "alta" — el informe acababa con
// una alerta ruidosa sobre un personaje confundido consigo mismo.
const caseDupes = analyze(['Noa', 'noa', 'NOA', 'Brais', 'Brais', ' Ana ', 'ana']);
assert.deepEqual(
  caseDupes.names,
  ['Noa', 'Brais', 'Ana'],
  'los duplicados por mayúsculas/minúsculas deben colapsar en una sola entrada, con la primera grafía vista'
);
assert.equal(caseDupes.counts.high, 0, 'sin duplicados de caja no debe quedar ninguna alerta "alta" de autoconfusión');

// Y la corrección no debe pasarse de largo: dos grafías que solo difieren en
// una TILDE (no en la caja) son un par real del tipo que la herramienta
// existe para señalar — deben seguir comparándose y no fusionarse en la
// deduplicación, exactamente como en el ejemplo de arriba con 5 nombres.
const accentPair = res.pairs.find((p) => p.left === 'Bruno' && p.right === 'Brunó');
assert(accentPair, 'Bruno/Brunó deben seguir siendo dos entradas separadas y comparadas entre sí');
assert.equal(accentPair.level, 'high');

// Regresión: NFD descompone ñ como n + U+0303. Si se eliminan todas las marcas
// combinantes sin recomponerla antes, "Niña" se convierte en "nina" y el
// motor la trata como idéntica a "Nina". Las tildes vocálicas sí se pliegan,
// pero la ñ debe conservarse como letra española independiente.
assert.equal(strip('Álvaro'), 'alvaro', 'las tildes vocálicas se normalizan');
assert.equal(strip('Niña'), 'niña', 'la ñ debe sobrevivir a la normalización');
const enyePair = pair('Nina', 'Niña');
assert.notEqual(enyePair.metrics.edit, 1, 'Nina/Niña no deben colapsar a la misma forma ortográfica');
assert(!enyePair.reasons.includes('mismo nombre al normalizar tildes/mayúsculas'));

const single = res.pairs[0];
assert.equal(typeof single.score, 'number');
assert(single.score >= 0 && single.score <= 1);

console.log('tests/test-nombres-personajes: OK');
