import assert from 'node:assert/strict';
import { analyzeDialogueConventions } from '../assets/dialogo-convenciones.js';

const sampleMixed = [
  '- Esto abre con guion.',
  '—Esto abre con raya.',
  '"Comillas rectas" y también «comillas angulares».',
  '—dijo ella, Volvió de inmediato.',
].join('\n');

const resMixed = analyzeDialogueConventions(sampleMixed);
assert.equal(resMixed.issues.some((x) => x.code === 'hyphen-instead-of-dash'), true, 'must detect hyphen openers');
assert.equal(resMixed.issues.some((x) => x.code === 'mixed-quotes'), true, 'must detect mixed quote styles');
assert.equal(resMixed.warnings.some((x) => x.code === 'punctuation-after-dialogue-tag'), true, 'must flag suspicious narration punctuation');

const sampleHyphenNoSpace = [
  '-Hola, ¿qué tal? -dijo Juan.',
  '-Bien -respondió ella.',
].join('\n');
const resHyphenNoSpace = analyzeDialogueConventions(sampleHyphenNoSpace);
assert.equal(resHyphenNoSpace.issues.some((x) => x.code === 'hyphen-instead-of-dash'), true, 'must detect hyphen openers with no space after the hyphen (the same spacing convention as em-dash dialogue)');

const sampleClean = [
  '—No deberías entrar —dijo Ana—. Volveré mañana.',
  '—Te espero en la puerta.',
  '«No tardes», pensó mientras cerraba.',
].join('\n');

const resClean = analyzeDialogueConventions(sampleClean);
assert.equal(resClean.issues.length, 0, 'clean sample should not raise convention issues');
assert.equal(resClean.quoteCounts.angle > 0, true, 'must count angle quotes');

console.log('test-dialogo-convenciones: all assertions passed');
