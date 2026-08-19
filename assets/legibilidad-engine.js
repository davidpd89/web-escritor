import { countSpanishSyllables } from './silabajs-lite-2.1.0.js';

const WORD_RE = /[\p{L}\p{M}]+(?:[’'-][\p{L}\p{M}]+)*/gu;
const SENTENCE_RE = /[^.!?…]+(?:[.!?…]+|$)/gu;

export function wordsFrom(text) {
  return String(text || '').normalize('NFC').match(WORD_RE) || [];
}

export function sentencesFrom(text) {
  const raw = String(text || '').normalize('NFC').match(SENTENCE_RE) || [];
  return raw.map((s) => s.trim()).filter((s) => wordsFrom(s).length > 0);
}

export function paragraphsFrom(text) {
  return String(text || '').normalize('NFC').split(/\n\s*\n+/).map((p) => p.trim()).filter(Boolean);
}

export function classifyInflesz(score) {
  if (score < 40) return 'Muy difícil';
  if (score < 55) return 'Algo difícil';
  if (score < 65) return 'Normal';
  if (score < 80) return 'Bastante fácil';
  return 'Muy fácil';
}

export function classifyFernandezHuerta(score) {
  if (score >= 91) return 'Muy fácil';
  if (score >= 81) return 'Fácil';
  if (score >= 71) return 'Algo fácil';
  if (score >= 61) return 'Normal';
  if (score >= 51) return 'Algo difícil';
  if (score >= 31) return 'Difícil';
  return 'Muy difícil';
}

const round = (n, d = 1) => Number.isFinite(n) ? Number(n.toFixed(d)) : null;
const clamp = (n, min = 0, max = 100) => Math.min(max, Math.max(min, n));
const syllablesIn = (words) => words.reduce((sum, word) => sum + countSpanishSyllables(word.replace(/[’'-]/g, '')), 0);

export function analyzeText(text) {
  const normalized = String(text || '').normalize('NFC').trim();
  const words = wordsFrom(normalized);
  const sentences = sentencesFrom(normalized);
  const paragraphs = paragraphsFrom(normalized);
  const wordCount = words.length;

  if (wordCount === 0) {
    return { empty: true, wordCount: 0, sentenceCount: 0, paragraphCount: 0 };
  }

  const sentenceCount = Math.max(1, sentences.length);
  const syllables = syllablesIn(words);
  const letters = words.reduce((sum, word) => sum + [...word].filter((ch) => /\p{L}/u.test(ch)).length, 0);
  const polys = words.reduce((sum, word) => sum + (countSpanishSyllables(word.replace(/[’'-]/g, '')) >= 3 ? 1 : 0), 0);
  const syllablesPerWord = syllables / wordCount;
  const wordsPerSentence = wordCount / sentenceCount;
  const sentencesPer100 = (sentenceCount * 100) / wordCount;
  const syllablesPer100 = (syllables * 100) / wordCount;

  // Fernández-Huerta: variante normalizada a longitud media de frase.
  // La fórmula histórica se publicó para muestras de 100 palabras y existe
  // una discusión documentada sobre la interpretación del término de frases.
  // En la interfaz explicamos esta decisión para que el resultado sea auditable.
  const fernandezHuertaRaw = 206.84 - (60 * syllablesPerWord) - (102 * sentenceCount / wordCount);

  // Flesch-Szigriszt; INFLESZ interpreta esta puntuación en cinco tramos.
  const szigrisztRaw = 206.835 - (62.3 * syllablesPerWord) - wordsPerSentence;

  // Gutiérrez de Polini: 95.2 - 9.7*(letras/palabra) - 0.35*(palabras/frase).
  const gutierrezRaw = 95.2 - (9.7 * letters / wordCount) - (0.35 * wordsPerSentence);

  // Crawford: estimación escolar basada en frases y sílabas por 100 palabras.
  const crawfordRaw = (-0.205 * sentencesPer100) + (0.049 * syllablesPer100) - 3.407;

  const sentenceRows = sentences.map((sentence, index) => {
    const sw = wordsFrom(sentence);
    return { index: index + 1, text: sentence, words: sw.length, syllables: syllablesIn(sw) };
  }).sort((a, b) => b.words - a.words);

  const paragraphRows = paragraphs.map((paragraph, index) => {
    const pw = wordsFrom(paragraph);
    const ps = sentencesFrom(paragraph);
    if (pw.length < 20 || ps.length === 0) {
      return { index: index + 1, text: paragraph, words: pw.length, score: null, label: 'Muestra corta' };
    }
    const pSyllables = syllablesIn(pw);
    const pScore = 206.835 - (62.3 * (pSyllables / pw.length)) - (pw.length / ps.length);
    return { index: index + 1, text: paragraph, words: pw.length, score: round(clamp(pScore)), raw: round(pScore), label: classifyInflesz(pScore) };
  });

  const comparableParagraphs = paragraphRows.filter((p) => p.score !== null).sort((a, b) => a.score - b.score);

  return {
    empty: false,
    wordCount,
    sentenceCount: sentences.length,
    paragraphCount: paragraphs.length,
    syllables,
    letters,
    polysyllabicWords: polys,
    avgWordsPerSentence: round(wordsPerSentence),
    avgSyllablesPerWord: round(syllablesPerWord, 2),
    fernandezHuerta: { score: round(clamp(fernandezHuertaRaw)), raw: round(fernandezHuertaRaw), label: classifyFernandezHuerta(fernandezHuertaRaw) },
    inflesz: { score: round(clamp(szigrisztRaw)), raw: round(szigrisztRaw), label: classifyInflesz(szigrisztRaw) },
    gutierrez: { score: round(gutierrezRaw), raw: round(gutierrezRaw), label: 'Úsalo para comparar versiones del mismo texto' },
    crawford: { score: round(crawfordRaw, 2), raw: round(crawfordRaw, 2), label: 'Estimación escolar; no es una nota literaria' },
    longestSentences: sentenceRows.slice(0, 5),
    densestParagraphs: comparableParagraphs.slice(0, 5),
    paragraphRows,
  };
}
