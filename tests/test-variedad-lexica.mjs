import assert from 'node:assert/strict';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { analyzeLexicalDiversity, tokenizeSpanish } from '../assets/variedad-lexica-engine.js';

const text = 'Una casa vieja. Una casa nueva. Un coche. Un árbol.';
const tokens = tokenizeSpanish(text);
const res = analyzeLexicalDiversity(text);

assert(tokens.length > 0, 'tokenize should produce tokens');
assert(typeof res.tokenCount === 'number');
assert(Array.isArray(res.profile));

// El documento fuente (48, sección 5) fija cuatro escalones de muestra:
// <20 -> sin resultado; 20-49 -> solo estadísticas básicas; 50-99 -> MATTR-50
// y MTLD disponibles, sin MATTR-100; 100+ -> MATTR-100 también disponible.
const words = (n) => Array.from({ length: n }, (_, i) => `palabra${i % 5}`).join(' ');
assert.equal(analyzeLexicalDiversity(words(19)).mattr50, null, '<20 no debe dar MATTR-50');
const tier2049 = analyzeLexicalDiversity(words(30));
assert.equal(tier2049.mattr50, null, '20-49: sin MATTR-50');
assert.equal(tier2049.mtld, null, '20-49: sin MTLD');
const tier5099 = analyzeLexicalDiversity(words(60));
assert.notEqual(tier5099.mattr50, null, '50-99: MATTR-50 debe estar disponible');
assert.notEqual(tier5099.mtld, null, '50-99: MTLD debe estar disponible');
assert.equal(tier5099.mattr100, null, '50-99: MATTR-100 aún no debe estar disponible');
const tier100 = analyzeLexicalDiversity(words(120));
assert.notEqual(tier100.mattr100, null, '100+: MATTR-100 debe estar disponible');

// Umbral MTLD 0,72 fijado en el propio motor, tal y como pide el documento.
assert.equal(analyzeLexicalDiversity('x').mtldThreshold, 0.72);

// Trabaja con formas ortográficas, no con lemas (doc 48, sección 2.4):
// "casa"/"casas" son formas distintas, igual que "si"/"sí".
assert.deepEqual(tokenizeSpanish('casa casas'), ['casa', 'casas']);
assert.deepEqual(tokenizeSpanish('si sí'), ['si', 'sí']);
assert.deepEqual(tokenizeSpanish('Casa CASA casa'), ['casa', 'casa', 'casa']);

// Bug real encontrado y corregido: el texto de "Cargar ejemplo" en
// assets/variedad-lexica.js tenía solo 14 palabras — por debajo incluso del
// mínimo de 20 que el propio análisis exige. Pulsar el ejemplo y luego
// "Analizar" (el primer gesto obvio de cualquier visitante) no mostraba
// ningún resultado, solo el aviso de "pega al menos 20 palabras". Este test
// lee el SAMPLE real del fichero fuente para que la regresión no pueda
// volver a colarse sin que algo se ponga en rojo.
const jsSource = fs.readFileSync(fileURLToPath(new URL('../assets/variedad-lexica.js', import.meta.url)), 'utf8');
const sampleMatch = jsSource.match(/const SAMPLE = `([\s\S]*?)`;/);
assert(sampleMatch, 'no se encontró la constante SAMPLE en variedad-lexica.js');
const sampleWordCount = tokenizeSpanish(sampleMatch[1]).length;
assert(
  sampleWordCount >= 100,
  `el ejemplo precargable tiene ${sampleWordCount} palabras; necesita al menos 100 para demostrar las cuatro métricas (incluida MATTR-100), no solo para superar el mínimo de 20`
);

console.log('tests/test-variedad-lexica: OK');
