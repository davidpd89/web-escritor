import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const api = require('../assets/contador-palabras-engine.js');
function ok(cond, msg) { if (!cond) throw new Error(msg); }

// Caso base: 5 palabras, 2 frases, 1 párrafo.
{
  const r = api.count('Hola mundo, esto es una prueba. Segunda frase aquí.');
  ok(r.wordCount === 9, `wordCount esperado 9, obtenido ${r.wordCount}`);
  ok(r.sentenceCount === 2, `sentenceCount esperado 2, obtenido ${r.sentenceCount}`);
  ok(r.paragraphCount === 1, `paragraphCount esperado 1, obtenido ${r.paragraphCount}`);
}

// Párrafos separados por línea en blanco.
{
  const r = api.count('Primer párrafo con palabras.\n\nSegundo párrafo distinto con más palabras.');
  ok(r.paragraphCount === 2, `paragraphCount esperado 2, obtenido ${r.paragraphCount}`);
}

// Texto vacío: todos los contadores en cero, sin división por cero.
{
  const r = api.count('');
  ok(r.wordCount === 0 && r.sentenceCount === 0 && r.paragraphCount === 0, 'texto vacío debe dar todo a 0');
  ok(r.avgWordLength === 0 && r.avgWordsPerSentence === 0, 'promedios en 0 sin NaN');
  ok(!Number.isNaN(r.avgWordLength) && !Number.isNaN(r.avgWordsPerSentence), 'no debe haber NaN');
}

// Solo espacios en blanco: igual que vacío.
{
  const r = api.count('   \n\n   ');
  ok(r.wordCount === 0, 'solo espacios en blanco -> 0 palabras');
}

// Caracteres con y sin espacios.
{
  const r = api.count('ab cd');
  ok(r.charsWithSpaces === 5, `charsWithSpaces esperado 5, obtenido ${r.charsWithSpaces}`);
  ok(r.charsNoSpaces === 4, `charsNoSpaces esperado 4, obtenido ${r.charsNoSpaces}`);
}

// Acentos y apóstrofos cuentan como parte de la palabra (español).
{
  const r = api.count('árbol niño corazón d’Artagnan');
  ok(r.wordCount === 4, `wordCount con acentos esperado 4, obtenido ${r.wordCount}`);
}

// Tiempo de lectura: escalado por README_WPM.
{
  const words = Array.from({ length: api.READING_WPM }, () => 'palabra').join(' ');
  const r = api.count(words);
  ok(Math.abs(r.readingMinutes - 1) < 1e-9, `readingMinutes esperado ~1, obtenido ${r.readingMinutes}`);
  ok(api.formatReadingTime(0.4) === '< 1 min', 'formatReadingTime < 1 min');
  ok(api.formatReadingTime(75) === '1 h 15 min', `formatReadingTime 75 -> obtenido ${api.formatReadingTime(75)}`);
  ok(api.formatReadingTime(120) === '2 h', `formatReadingTime 120 -> obtenido ${api.formatReadingTime(120)}`);
}

console.log('tests/test-contador-palabras: OK');
