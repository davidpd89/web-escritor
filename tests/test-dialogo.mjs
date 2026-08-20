import assert from 'node:assert/strict';
import { analyzeDialogue } from '../assets/dialogo-espanol.js';

const sample = `—Hola —dijo Lola—, ¿vienes?\n\nNo respondió.\n\n—Entonces me voy.\n\nCapítulo 2\n\n"Esto es una cita no dialogal"`;
const res = analyzeDialogue(sample);
assert.equal(typeof res.dialoguePercentage, 'number');
assert(res.totalWords > 0);

// Los cuatro casos que el documento 33 (sección "Revalidación técnica",
// 19/08/2026) dice haber comprobado, verificados aquí contra el motor real
// para que dejen de ser una afirmación sin test detrás.

// 1. Raya + acotación + reanudación: el diálogo se cuenta, la acotación entre
// rayas no, y se detecta como UNA sola intervención (no dos, aunque el habla
// se reanude tras la acotación).
const r1 = analyzeDialogue('—No sé si debería entrar —dijo Ana, dudando— pero al final entró.');
assert.equal(r1.mode, 'dash');
assert.equal(r1.interventions, 1, 'raya + acotación + reanudación debe contar como 1 intervención');
assert.equal(r1.dialogueWords, 9, 'las palabras de la acotación ("dijo Ana, dudando") no cuentan como diálogo');
assert(r1.dialogueWords < r1.totalWords, 'el total debe incluir también la acotación y el cierre narrativo');

// 2. Texto solo con comillas (sin rayas): activa el modo de comillas.
const r2 = analyzeDialogue('Ella salió al jardín pensando en todo. «Esto es diálogo» fue lo único que dijo.');
assert.equal(r2.mode, 'quotes', 'sin rayas en el texto debe activarse el modo de comillas');
assert(r2.dialogueWords > 0, 'el fallback de comillas debe contar palabras dialogadas');

// 3. Dos capítulos: se generan dos bloques y los títulos no se suman al total.
const r3 = analyzeDialogue('Capítulo 1\n\n—Hola —dijo Ana.\n\nCapítulo II\n\n—Adiós —dijo Bruno.');
assert.deepEqual(r3.chapters.map((c) => c.title), ['Capítulo 1', 'Capítulo II']);
assert.equal(r3.totalWords, 6, 'las palabras de "Capítulo 1" / "Capítulo II" no deben sumarse al total');

// 4. Raya + pensamiento entre comillas: se mantiene mode=dash, el pensamiento
// entre comillas se cuenta aparte (quotedWords) y NO se suma al ratio
// principal de diálogo (dialogueWords).
const r4 = analyzeDialogue('—Sí —dijo. «Vaya día», pensó él para sus adentros con calma.');
assert.equal(r4.mode, 'dash', 'con raya presente el modo debe seguir siendo dash, no cambiar a quotes');
assert.equal(r4.dialogueWords, 1, 'solo "Sí" debe contar como diálogo principal');
assert.equal(r4.quotedWords, 2, 'el pensamiento entre comillas se registra aparte');

console.log('tests/test-dialogo: OK');
