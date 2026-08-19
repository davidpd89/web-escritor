import { countSpanishSyllables } from './silabajs-lite-2.1.0.js';

export function analyzeText(text) {
  const txt = String(text || '').trim();
  const words = txt ? txt.split(/\s+/).filter(Boolean) : [];
  const wordCount = words.length;
  const sentences = txt ? txt.split(/[.!?]+/).filter(s => s.trim().length > 0) : [];
  const sentenceCount = sentences.length || 1;
  let syllables = 0;
  for (const w of words) syllables += countSpanishSyllables(w.replace(/[^\p{L}áéíóúüñÑçÇ]/gu, ''));
  const avgWordsPerSentence = wordCount / sentenceCount || 0;
  const sylPer100Words = wordCount ? (syllables / wordCount) * 100 : 0;
  // Minimal Inflesz-like score (not official)
  const infleszScore = Math.max(0, Math.min(100, 206.84 - 0.846 * (wordCount / sentenceCount) - 1.02 * (syllables / wordCount * 100)));

  return {
    empty: !txt,
    wordCount,
    sentenceCount,
    syllables,
    avgWordsPerSentence,
    inflesz: { score: infleszScore },
  };
}
