(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.WordCounter = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const READING_WPM = 200; // velocidad de lectura silenciosa media en español

  function count(text) {
    const raw = String(text ?? '');
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
