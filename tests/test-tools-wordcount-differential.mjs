// Differential test (item 8 of the 2026-09 audit round): the same text
// should produce the same basic word count across Contador de Palabras,
// Legibilidad, Analizador de Capitulos, Repeticiones and Variedad Lexica --
// they all show a "palabras" figure to the writer, and a silent mismatch
// between two tools looking at the exact same pasted text would look like a
// bug in one of them even when it is a deliberate, undocumented difference
// in tokenizing rules (hyphens, digits, stray punctuation-only tokens).
import contadorPkg from '../assets/contador-palabras-engine.js';
const { count: countWords } = contadorPkg;
import { wordsFrom } from '../assets/legibilidad-engine.js';
import { words as chapterWords } from '../assets/analizador-capitulos-engine.js';
import { analyzeRepetitions } from '../assets/repeticiones-engine.js';
import { tokenizeSpanish } from '../assets/variedad-lexica-engine.js';

const engineCount = {
  'contador-palabras': (t) => countWords(t).wordCount,
  'legibilidad': (t) => wordsFrom(t).length,
  'analizador-capitulos': (t) => chapterWords(t).length,
  'repeticiones': (t) => { const r = analyzeRepetitions(t); return r.empty ? 0 : r.wordCount; },
  'variedad-lexica': (t) => tokenizeSpanish(t).length,
};

const samples = [
  {
    label: 'prosa realista sin guiones ni digitos',
    text: 'Ana caminaba despacio por el andén, pensando en lo que diría cuando llegara a casa. No tenía prisa, aunque el tren ya se alejaba.',
  },
  {
    label: 'dialogo con apostrofos',
    text: '—No sé qué decirte —murmuró—. D’Artagnan nunca lo habría dudado.',
  },
  {
    label: 'palabras con guion interno',
    text: 'Es un plan a largo plazo, físico-químico y político-social, bien pensado.',
  },
  {
    label: 'numeros y capitulo',
    text: 'Capítulo 12: en 1998 nacieron 45000 personas en esa provincia.',
  },
];

let mismatches = 0;
for (const { label, text } of samples) {
  const results = Object.fromEntries(Object.entries(engineCount).map(([name, fn]) => [name, fn(text)]));
  const values = Object.values(results);
  const allEqual = values.every((v) => v === values[0]);
  console.log(`${allEqual ? '  ok  ' : '  DIFF'} ${label}: ${JSON.stringify(results)}`);
  if (!allEqual) mismatches++;
}

console.log(`tests/test-tools-wordcount-differential: ${samples.length} sample(s), ${mismatches} with cross-tool mismatch(es)`);
console.log('tests/test-tools-wordcount-differential: OK (informational -- see summary above; differences are investigated, not asserted away)');
