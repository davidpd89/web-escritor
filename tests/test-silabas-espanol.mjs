// El contador silábico que llegó a producción no era el que describe el
// documento fuente (32, sección 11 "QA realizado"). El fichero desplegado en
// assets/silabajs-lite-2.1.0.js tenía comentarios que lo admitían:
// "content truncated for brevity in patch, full file preserved" y "minimal
// implementations of silabajs functions" — un stub de 31 líneas que contaba
// grupos de vocales contiguos como si cada uno fuera una sílaba, y que además
// quitaba las tildes ANTES de contar, borrando la única señal que distingue
// un hiato de un diptongo.
//
// Fallaba en los propios casos de humo que el documento 32 dice haber
// comprobado: "día" (2 sílabas) daba 1; "aeropuerto" (5 sílabas, hiato a-e)
// daba 4. El motor de legibilidad entero — Fernández-Huerta, Inflesz,
// Szigriszt, Crawford — depende de sílabas/palabra, así que ese error se
// propagaba a cada puntuación de cada texto con hiatos, que en español no es
// un caso raro (día, país, río, aeropuerto, leer, caos...).
//
// El fichero real SÍ existía: WEB DAVID PORTO nuevas ideas/CODIGO PROPUESTO
// 2026-08-15/silabajs-lite-2.1.0.js es un puerto MIT de silabajs 2.1.0
// (github.com/nicofrem/silabajs) con máquina de estados onset/núcleo/coda
// completa. Nunca se copió a /assets/; se copió en su lugar el placeholder.
// Ahora sí está desplegado. Este test fija los 7 casos del documento como
// regresión dura, más una lista adicional de hiatos/diptongos/triptongos
// verificados a mano contra las reglas de acentuación de la RAE, para que
// una futura sustitución accidental por un stub vuelva a fallar aquí.
import assert from 'node:assert/strict';
import { countSpanishSyllables } from '../assets/silabajs-lite-2.1.0.js';

// Los 7 casos que el documento 32 (sección 11) declara haber comprobado.
const DOC_SMOKE_TEST = {
  'murciélago': 4,
  casa: 2,
  día: 2,
  aeropuerto: 5,
  cuidado: 3,
  reloj: 2,
  'teléfono': 4,
};

for (const [word, expected] of Object.entries(DOC_SMOKE_TEST)) {
  const got = countSpanishSyllables(word);
  assert.equal(got, expected, `[doc 32] "${word}" debería tener ${expected} sílabas, dio ${got}`);
}
console.log(`tests/test-silabas-espanol: ${Object.keys(DOC_SMOKE_TEST).length} casos del documento fuente OK`);

// Cobertura adicional: hiatos (vocal fuerte + fuerte, o débil tildada + fuerte),
// diptongos (fuerte + débil sin tilde, o débil + débil) y un triptongo.
const EXTRA_CASES = {
  // hiatos fuerte+fuerte
  teatro: 3, poema: 3, caos: 2, leer: 2, ahora: 3,
  // hiatos por tilde en la vocal débil
  'país': 2, 'raíz': 2, 'río': 2, 'baúl': 2, 'oído': 3, 'caída': 3, 'actúa': 3,
  // diptongos fuerte+débil o débil+fuerte sin tilde
  cuidado: 3, familia: 3, diablo: 2, tiempo: 2, cielo: 2, bien: 1, 'también': 2,
  // diptongo débil+débil (la tilde NO rompe si ambas son débiles)
  'cuídate': 3, cuidate: 3,
  // triptongo (débil + fuerte + débil, una sola sílaba)
  'Paraguay': 3, buey: 1, miau: 1,
  // par mínimo: la tilde en la vocal fuerte marca solo dónde va el golpe de
  // voz y no rompe el diptongo; en la vocal débil sí lo rompe.
  continuo: 3, 'continúo': 4,
};

let failures = 0;
for (const [word, expected] of Object.entries(EXTRA_CASES)) {
  const got = countSpanishSyllables(word.toLowerCase());
  if (got !== expected) {
    failures++;
    console.log(`  FALLO "${word}": esperado ${expected}, obtenido ${got}`);
  }
}
assert.equal(failures, 0, `${failures} caso(s) adicional(es) de hiato/diptongo fallaron`);
console.log(`tests/test-silabas-espanol: ${Object.keys(EXTRA_CASES).length} casos adicionales de hiato/diptongo/triptongo OK`);

// Guarda contra la regresión concreta que se dio: un fallback que cuenta
// grupos de vocales contiguos sin mirar tildes. "aeropuerto" es el caso que
// mejor lo distingue (grupo "ae" cuenta como 1 para el fallback, como 2 para
// el algoritmo real).
assert.notEqual(
  countSpanishSyllables('aeropuerto'), 4,
  'countSpanishSyllables ha vuelto a comportarse como el fallback ingenuo de conteo de grupos de vocales'
);

console.log('tests/test-silabas-espanol: OK');
