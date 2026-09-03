import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { analyzeRepetitions } from '../assets/repeticiones-engine.js';

// Caso genérico previo: solo comprobaba la forma del resultado, no que
// detectara nada en concreto.
const sample = `Ana miró la puerta. La puerta seguía abierta y Ana volvió a mirar la puerta antes de entrar. Parecía tranquila. Parecía tranquila.`;
const res = analyzeRepetitions(sample, { windowSize: 30 });
assert.equal(res.empty, false);
assert(res.wordCount > 0);
assert(Array.isArray(res.echoes));

// El caso de QA que el propio documento 33 (sección "QA realizado sobre la
// propuesta") dice haber comprobado, con sus seis afirmaciones concretas.
// Antes de este test nada lo verificaba contra el motor real: si alguna
// afirmación fallara (p. ej. `ignored`/`tics` con las claves equivocadas,
// que es justo lo que ocurrió al construir este test la primera vez —
// `excludeNames`/`customTics` como nombres de opción no existen, son
// `ignored`/`tics`) ningún test lo habría avisado.
const doc33Sample = `Noa dio un paso. Esto esto se quedó aquí sin querer. La puerta chirrió y Noa dio media vuelta. Entonces miró la puerta otra vez. Parecía tranquila, pero entonces algo cambió. Noa dio otro paso hacia la puerta. Parecía que el pasillo no acababa nunca. Entonces se detuvo del todo.`;
const doc33 = analyzeRepetitions(doc33Sample, { windowSize: 30 });

// 1. duplicado inmediato "esto esto"
assert(
  doc33.immediateDuplicates.some((d) => d.word.toLowerCase() === 'esto'),
  'debe detectar el duplicado inmediato "esto esto"'
);

// 2-4. apariciones de puerta (3), entonces (3), parecía (2)
const echoCount = (word) => doc33.echoes.find((e) => e.word.toLowerCase() === word)?.count;
assert.equal(echoCount('puerta'), 3, '"puerta" debe aparecer 3 veces');
assert.equal(echoCount('entonces'), 3, '"entonces" debe aparecer 3 veces');
assert.equal(echoCount('parecía'), 2, '"parecía" debe aparecer 2 veces');

// 5. frase repetida "Noa dio"
assert(
  doc33.repeatedPhrases.some((p) => p.phrase.toLowerCase() === 'noa dio'),
  'debe detectar la frase repetida "Noa dio"'
);

// 6. tics personalizados y exclusiones ("campos" separados en el propio
// formulario, así que se prueban con una llamada aparte, no combinados con lo
// anterior): "entonces" es palabra funcional y como tic explícito se cuenta
// igual; "Noa" pedido como exclusión desaparece de TODO el informe, incluida
// la detección de frases — "Noa dio" dejó de ser una frase repetida en esta
// llamada porque sus tokens ya no entran en el análisis. Eso no es un fallo:
// es la exclusión funcionando en el motor de n-gramas, no solo en echoes.
const withOptions = analyzeRepetitions(doc33Sample, { windowSize: 30, tics: ['entonces'], ignored: ['Noa'] });
const ticEntry = withOptions.customTics.find((t) => t.tic === 'entonces');
assert(ticEntry, 'el tic personalizado "entonces" debe aparecer en customTics');
assert.equal(ticEntry.count, 3, 'el tic "entonces" debe contarse 3 veces');
assert(
  !withOptions.echoes.some((e) => e.word.toLowerCase() === 'noa'),
  '"Noa" debe desaparecer de echoes cuando se pasa en ignored'
);
assert(
  !withOptions.dominantWords.some((w) => w.word.toLowerCase() === 'noa'),
  '"Noa" debe desaparecer de dominantWords cuando se pasa en ignored'
);
assert(
  !withOptions.repeatedPhrases.some((p) => p.phrase.toLowerCase().includes('noa')),
  '"Noa" tampoco debe aparecer dentro de ninguna frase repetida cuando se pasa en ignored'
);

// Palabras compuestas con guion deben seguir siendo un solo token, igual
// que en el resto de herramientas (contador-palabras, legibilidad,
// analizador-capitulos, variedad-lexica). Antes de este fix WORD_RE no
// incluía el guion, así que "político-social" se partía en "político" +
// "social" y una repetición real de 2x de "político" (como palabra suelta)
// aparecía inflada a un falso 3x en dominantWords -- confirmado en vivo.
const hyphenSample = 'Tenía un plan político. Después firmó el acuerdo político-social con calma. Era un final político para todos.';
const hyphenRes = analyzeRepetitions(hyphenSample);
assert.equal(hyphenRes.wordCount, 17, 'político-social debe contar como una sola palabra, no dos');
assert(
  !hyphenRes.dominantWords.some((w) => w.word.toLowerCase() === 'político'),
  '"político" no debe aparecer como dominante: solo se repite 2 veces como palabra suelta, no 3'
);

// Regresión de UI: el selector debe ser CSS válido. Este typo rompía la
// inicialización completa de la herramienta antes de ejecutar el motor.
const uiSource = readFileSync(new URL('../assets/repeticiones-espanol.js', import.meta.url), 'utf8');
assert.match(
  uiSource,
  /const results = \$\('\[data-repetition-results\]'\);/,
  'la UI debe buscar [data-repetition-results] con un selector CSS cerrado'
);
assert.equal(
  uiSource.includes("$('[data-repetition-results');"),
  false,
  'no debe reaparecer el selector incompleto que lanzaba DOMException'
);

// Stopword coverage audit (2026-09 round): "está"/"están"/"son" are
// conjugated forms of estar/ser, the same closed class already covered by
// "era/eran/eres/es/fue/fueron" in BASIC_STOPWORDS -- omitting them let
// completely ordinary Spanish text get its most basic grammar flagged as a
// "dominant word" to fix. Confirmed live before the fix: this paragraph's
// "está" (4x) and "son" (3x) both showed up in dominantWords.
const grammarSample = 'Los personajes de la novela son complejos. Todos ellos son distintos entre sí. La ciudad está tranquila por las noches, aunque de día está llena de gente. Está claro que la trama avanza, pero está bien construida.';
const grammarRes = analyzeRepetitions(grammarSample);
assert(
  !grammarRes.dominantWords.some((w) => ['está', 'son'].includes(w.word.toLowerCase())),
  '"está"/"son" son gramática básica, no deben aparecer como palabras dominantes por su sola frecuencia normal'
);

// Decimal localization audit (2026-09 round): per1000 (p.ej. 21.9) se
// interpolaba sin formatear, mostrando "21.9 por 1000 palabras" (punto) en
// lugar de "21,9 por 1000 palabras" (coma), inconsistente con el resto de
// números de este mismo fichero, que ya usan toLocaleString('es-ES').
assert.equal(
  uiSource.includes('${x.per1000} por 1000 palabras'),
  false,
  'per1000 no debe interpolarse sin formatear (punto decimal, no coma)'
);
assert.match(
  uiSource,
  /fmtDecimal\(x\.per1000\)/,
  'per1000 debe pasar por un formateador con coma decimal antes de mostrarse'
);

console.log('tests/test-repeticiones: OK');
