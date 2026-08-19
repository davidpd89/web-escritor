import assert from 'node:assert/strict';
import { analyzeDialogue } from '../assets/dialogo-espanol.js';

const sample = `—Hola —dijo Lola—, ¿vienes?\n\nNo respondió.\n\n—Entonces me voy.\n\nCapítulo 2\n\n"Esto es una cita no dialogal"`;
const res = analyzeDialogue(sample);
assert.equal(typeof res.dialoguePercentage, 'number');
assert(res.totalWords > 0);
console.log('tests/test-dialogo: OK');
