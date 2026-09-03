(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.WordCounter = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const READING_WPM = 200; // velocidad de lectura silenciosa media en español

  // Zero-width space/joiners and BOM are invisible in the textarea but match
  // nothing in \p{L}\p{N} -- one landing inside a word (a real artifact from
  // some PDF/OCR extraction pipelines) split it into two word-matches,
  // confirmed live to inflate the count (e.g. 3 words -> 4 from a single
  // stray character). Stripped once here so every derived count (words,
  // chars, sentences) agrees with what the writer actually sees.
  const INVISIBLE_RE = /[\u200B-\u200D\uFEFF]/g;

  function count(text) {
    const raw = String(text ?? '').replace(INVISIBLE_RE, '');
    const trimmed = raw.trim();

    const words = trimmed ? (trimmed.match(/[\p{L}\p{N}'’-]+/gu) || []) : [];
    const wordCount = words.length;

    const charsWithSpaces = raw.length;
    const charsNoSpaces = raw.replace(/\s/g, '').length;

    const sentences = trimmed ? (trimmed.match(/[^.!?…]+[.!?…]+/gu) || (trimmed ? [trimmed] : [])) : [];
    const sentenceCount = Math.max(sentences.length, trimmed ? 1 : 0);

    const paragraphs = trimmed ? trimmed.split(/\n\s*\n+/).map(p => p.trim()).filter(Boolean) : [];
    const paragraphCount = paragraphs.length;

    const avgWordLength = wordCount ? words.reduce((sum, w) => sum + w.length, 0) / wordCount : 0;
    const avgWordsPerSentence = sentenceCount ? wordCount / sentenceCount : 0;
    const avgWordsPerParagraph = paragraphCount ? wordCount / paragraphCount : 0;

    const readingMinutes = wordCount / READING_WPM;

    return {
      wordCount,
      charsWithSpaces,
      charsNoSpaces,
      sentenceCount,
      paragraphCount,
      avgWordLength,
      avgWordsPerSentence,
      avgWordsPerParagraph,
      readingMinutes,
    };
  }

  function formatReadingTime(minutes) {
    if (minutes < 1) return '< 1 min';
    const whole = Math.round(minutes);
    if (whole < 60) return `${whole} min`;
    const h = Math.floor(whole / 60);
    const m = whole % 60;
    return m ? `${h} h ${m} min` : `${h} h`;
  }

  return { count, formatReadingTime, READING_WPM };
});
