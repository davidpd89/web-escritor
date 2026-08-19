import * as engine from './nombres-personajes-engine.js';
if (typeof window !== 'undefined') {
  window.DPCharacterNames = {
    strip: engine.strip,
    levenshtein: engine.levenshtein,
    normalizedEditSimilarity: engine.normalizedEditSimilarity,
    jaroWinkler: engine.jaroWinkler,
    pair: engine.pair,
    analyze: engine.analyze,
  };
}
