import assert from 'node:assert/strict';
import { analyzeChapterBatch, analyzeChapter } from '../assets/analizador-capitulos-engine.js';

const chapters = [
  { id: 'c1', title: 'C1', text: 'Hola mundo.\n\n—Hola dijo Ana.\n\nContinuación.' },
  { id: 'c2', title: 'C2', text: 'Segundo capítulo.\n\n«Cita» y más texto.' },
];
const result = analyzeChapterBatch(chapters, ['Ana']);
assert.equal(result.chapterCount, 2);
assert.equal(result.totalWords > 0, true);
assert.equal(typeof result.chapters[0].dialoguePercentage, 'number');
const single = analyzeChapter(chapters[0], ['Ana']);
assert.equal(single.mentions['Ana'] >= 0, true);

// El fixture que el documento 34 (sección "QA ejecutado") dice haber
// comprobado: tres capítulos de tamaños muy distintos, separador de escena
// "***", menciones de nombres y un bloque dialogado, con las desviaciones
// respecto a la mediana como resultado concreto. El texto exacto del
// documento no está reproducido ahí (solo los números), así que este
// fixture usa cifras redondas propias que verifican la misma fórmula:
// desviación = (palabras_capítulo − mediana) / mediana.
const c1 = '—Hola —dijo Noa—, ¿qué tal? Brais no respondió.\n\n***\n\nSiguió solo.'; // 10 palabras
const c2 = Array.from({ length: 150 }, (_, i) => `palabra${i + 1}`).join(' '); // 150 palabras
const c3 = Array.from({ length: 50 }, (_, i) => `termino${i + 1}`).join(' '); // 50 palabras (mediana)

const batch = analyzeChapterBatch(
  [
    { id: 'c1', title: 'Capítulo 1', text: c1 },
    { id: 'c2', title: 'Capítulo 2', text: c2 },
    { id: 'c3', title: 'Capítulo 3', text: c3 },
  ],
  ['Noa', 'Brais']
);

assert.equal(batch.chapterCount, 3);
assert.equal(batch.medianWords, 50, 'la mediana de [10,150,50] debe ser 50');
assert.equal(batch.chapters[0].words, 10);
assert.equal(batch.chapters[1].words, 150);
assert.equal(batch.chapters[2].words, 50);
assert.equal(batch.chapters[0].deviationFromMedianPct, -80, 'C1: (10-50)/50 = -80%');
assert.equal(batch.chapters[1].deviationFromMedianPct, 200, 'C2: (150-50)/50 = +200%');
assert.equal(batch.chapters[2].deviationFromMedianPct, 0, 'C3 es la propia mediana: 0%');

assert.equal(batch.chapters[0].explicitSceneBreaks, 1, 'debe detectar el separador "***"');
assert.equal(batch.chapters[0].mentions['Noa'], 1, 'debe contar la mención de "Noa"');
assert.equal(batch.chapters[0].mentions['Brais'], 1, 'debe contar la mención de "Brais"');
assert(batch.chapters[0].dialoguePercentage > 0, 'debe detectar el bloque dialogado del C1');

console.log('tests/test-analizador-capitulos: OK');
