import assert from 'node:assert/strict';
import { analyzeChapterBatch, analyzeChapter } from '../assets/analizador-capitulos-engine.js';
const chapters = [
  {id:'c1', title:'C1', text:'Hola mundo.\n\n—Hola dijo Noa.\n\nContinuación.'},
  {id:'c2', title:'C2', text:'Segundo capítulo.\n\n«Cita» y más texto.'}
];
const result = analyzeChapterBatch(chapters, ['Noa']);
assert.equal(result.chapterCount, 2);
assert.equal(result.totalWords > 0, true);
assert.equal(typeof result.chapters[0].dialoguePercentage, 'number');
const single = analyzeChapter(chapters[0], ['Noa']);
assert.equal(single.mentions['Noa'] >= 0, true);
console.log('tests/test-analizador-capitulos: OK');
