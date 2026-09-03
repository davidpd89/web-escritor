// "está"/"están"/"son" are conjugated forms of estar/ser, the same closed
// class already covered here by "era/eran/eres/es/fue/fueron" -- omitting
// them let completely ordinary text ("La ciudad está tranquila... está
// llena... está bien construida") get its most basic grammar flagged as a
// "dominant word" to fix, confirmed by running a realistic paragraph
// through analyzeRepetitions() and seeing "está" (4x) and "son" (3x) listed
// as overused. normalizeWord() only lowercases (no accent-stripping), so
// "está" needs its own accented entry -- it does not collide with the
// unaccented demonstrative "esta" already in this list.
const BASIC_STOPWORDS = new Set(`a al algo algunas algunos ante antes como con contra cual cuando de del desde donde durante e el ella ellas ellos en entre era erais eramos eran eras eres es esa esas ese eso esos esta estaba estaban estas este esto estos está están fue fueron ha han hasta hay la las le les lo los mas me mi mis muy ni no nos o para pero por porque que quien se si sin sobre son su sus te tu tus un una unas uno unos y ya yo`.split(/\s+/));

// Hyphenated compounds (e.g. "político-social") must stay one token, like
// every sibling tokenizer in this codebase (contador-palabras, legibilidad,
// analizador-capitulos, variedad-lexica all include the hyphen here) --
// this one didn't, so "político-social" split into "político" + "social"
// and inflated a genuine 2x repeat of the standalone word "político" into a
// false 3x dominant-word hit, confirmed live.
const WORD_RE = /[\p{L}\p{M}]+(?:[’'-][\p{L}\p{M}]+)*/gu;
// Zero-width space/joiners and BOM match nothing in \p{L}\p{M} -- one landing
// inside a word (a real artifact from some PDF/OCR extraction pipelines)
// splits it into two tokens, inflating the repetition counts this tool reports.
const INVISIBLE_RE = /[\u200B-\u200D\uFEFF]/g;

function normalizeWord(value) {
  return String(value || '').toLocaleLowerCase('es-ES').replace(/’/g, "'");
}

function tokenize(text) {
  const out = [];
  // A name/word typed directly (NFC) and the same word arriving via pasted
  // manuscript text that happens to be NFD-encoded (a real, observed paste
  // artifact) are visually identical but byte-different -- confirmed live
  // to split one real 4x repetition into two separate 2x "echoes" instead
  // of flagging it as one, potentially hiding it below this tool's
  // detection threshold entirely.
  for (const match of String(text || '').normalize('NFC').replace(INVISIBLE_RE, '').matchAll(WORD_RE)) {
    out.push({ raw: match[0], norm: normalizeWord(match[0]), start: match.index ?? 0 });
  }
  return out;
}

function splitSentences(text) {
  return String(text || '')
    .replace(/\s+/g, ' ')
    .split(/(?<=[.!?…])\s+(?=[\p{L}«“"¿¡])/u)
    .map(s => s.trim()).filter(Boolean);
}

function splitParagraphs(text) {
  return String(text || '').split(/\n\s*\n+/).map(p => p.trim()).filter(Boolean);
}

function parseList(value) {
  return String(value || '')
    .split(/[\n,;]+/)
    .map(v => v.trim())
    .filter(Boolean);
}

function sequenceCount(tokenNorms, phraseNorms) {
  if (!phraseNorms.length || phraseNorms.length > tokenNorms.length) return { count: 0, positions: [] };
  const positions = [];
  outer: for (let i = 0; i <= tokenNorms.length - phraseNorms.length; i++) {
    for (let j = 0; j < phraseNorms.length; j++) {
      if (tokenNorms[i + j] !== phraseNorms[j]) continue outer;
    }
    positions.push(i);
  }
  return { count: positions.length, positions };
}

function context(tokens, index, radius = 7) {
  const start = Math.max(0, index - radius);
  const end = Math.min(tokens.length, index + radius + 1);
  return `${start > 0 ? '… ' : ''}${tokens.slice(start, end).map(t => t.raw).join(' ')}${end < tokens.length ? ' …' : ''}`;
}

function detectImmediateDuplicates(tokens) {
  const rows = [];
  for (let i = 1; i < tokens.length; i++) {
    if (tokens[i].norm && tokens[i].norm === tokens[i - 1].norm) {
      rows.push({ word: tokens[i].raw, index: i, context: context(tokens, i, 6) });
    }
  }
  return rows;
}

function frequencyMap(tokens, ignored, includeCommon) {
  const map = new Map();
  tokens.forEach((token, index) => {
    if (ignored.has(token.norm)) return;
    if (!includeCommon && BASIC_STOPWORDS.has(token.norm)) return;
    const entry = map.get(token.norm) || { word: token.raw, norm: token.norm, positions: [] };
    entry.positions.push(index);
    map.set(token.norm, entry);
  });
  return map;
}

function detectEchoes(tokens, map, windowSize) {
  const rows = [];
  for (const entry of map.values()) {
    if (entry.positions.length < 2) continue;
    let closestGap = Infinity;
    let closePairs = 0;
    for (let i = 1; i < entry.positions.length; i++) {
      const gap = entry.positions[i] - entry.positions[i - 1];
      closestGap = Math.min(closestGap, gap);
      if (gap <= windowSize) closePairs++;
    }
    if (!closePairs) continue;
    rows.push({
      word: entry.word,
      count: entry.positions.length,
      closePairs,
      closestGap,
      per1000: Number(((entry.positions.length / Math.max(tokens.length, 1)) * 1000).toFixed(1)),
      samples: entry.positions.slice(0, 3).map(pos => context(tokens, pos, 6)),
    });
  }
  rows.sort((a, b) => b.closePairs - a.closePairs || a.closestGap - b.closestGap || b.count - a.count || a.word.localeCompare(b.word, 'es'));
  return rows.slice(0, 40);
}

function detectDominantWords(tokens, map) {
  return [...map.values()]
    .filter(entry => entry.positions.length >= 3)
    .map(entry => ({
      word: entry.word,
      count: entry.positions.length,
      per1000: Number(((entry.positions.length / Math.max(tokens.length, 1)) * 1000).toFixed(1)),
    }))
    .sort((a, b) => b.per1000 - a.per1000 || b.count - a.count || a.word.localeCompare(b.word, 'es'))
    .slice(0, 30);
}

function prefixKey(text, length) {
  const parts = tokenize(text).map(t => t.norm).slice(0, length);
  return parts.length === length ? parts.join(' ') : '';
}

function repeatedPrefixes(items, length = 2) {
  const map = new Map();
  items.forEach((text, index) => {
    const key = prefixKey(text, length);
    if (!key) return;
    const entry = map.get(key) || { prefix: key, indexes: [] };
    entry.indexes.push(index + 1);
    map.set(key, entry);
  });
  return [...map.values()].filter(x => x.indexes.length >= 2)
    .sort((a, b) => b.indexes.length - a.indexes.length || a.prefix.localeCompare(b.prefix, 'es'))
    .slice(0, 20);
}

function detectNgrams(tokens, ignored, includeCommon) {
  const norms = tokens.map(t => t.norm);
  const candidates = [];
  for (let size = 5; size >= 2; size--) {
    const map = new Map();
    for (let i = 0; i <= norms.length - size; i++) {
      const slice = norms.slice(i, i + size);
      if (slice.some(w => ignored.has(w))) continue;
      if (!includeCommon && slice.every(w => BASIC_STOPWORDS.has(w))) continue;
      const key = slice.join(' ');
      const entry = map.get(key) || { phrase: tokens.slice(i, i + size).map(t => t.raw).join(' '), size, positions: [] };
      entry.positions.push(i);
      map.set(key, entry);
    }
    for (const entry of map.values()) {
      if (entry.positions.length >= 2) candidates.push({ ...entry, count: entry.positions.length });
    }
  }
  candidates.sort((a, b) => b.size - a.size || b.count - a.count || a.phrase.localeCompare(b.phrase, 'es'));

  const kept = [];
  for (const item of candidates) {
    const normalized = normalizeWord(item.phrase);
    if (kept.some(k => k.size > item.size && normalizeWord(k.phrase).includes(normalized) && k.count === item.count)) continue;
    kept.push(item);
    if (kept.length >= 25) break;
  }
  return kept.map(item => ({ phrase: item.phrase, words: item.size, count: item.count, samples: item.positions.slice(0, 2).map(pos => context(tokens, pos, item.size + 4)) }));
}

function detectCustomTics(tokens, tics) {
  const norms = tokens.map(t => t.norm);
  return tics.map(tic => {
    const phrase = tokenize(tic).map(t => t.norm);
    const found = sequenceCount(norms, phrase);
    return {
      tic,
      count: found.count,
      samples: found.positions.slice(0, 3).map(pos => context(tokens, pos, Math.max(6, phrase.length + 3)))
    };
  }).filter(x => x.count > 0).sort((a, b) => b.count - a.count || a.tic.localeCompare(b.tic, 'es'));
}

export function analyzeRepetitions(text, options = {}) {
  const tokens = tokenize(text);
  if (!tokens.length) return { empty: true };

  const windowSize = Math.min(100, Math.max(5, Number(options.windowSize) || 30));
  const ignored = new Set(parseList(options.ignored).flatMap(item => tokenize(item).map(t => t.norm)));
  const tics = parseList(options.tics);
  const includeCommon = Boolean(options.includeCommon);
  const map = frequencyMap(tokens, ignored, includeCommon);
  const phraseTokens = tokens.length > 30000 ? tokens.slice(0, 30000) : tokens;
  const sentences = splitSentences(text);
  const paragraphs = splitParagraphs(text);

  return {
    empty: false,
    wordCount: tokens.length,
    uniqueAnalyzedWords: map.size,
    windowSize,
    immediateDuplicates: detectImmediateDuplicates(tokens),
    echoes: detectEchoes(tokens, map, windowSize),
    dominantWords: detectDominantWords(tokens, map),
    sentenceStarts: repeatedPrefixes(sentences, 2),
    paragraphStarts: repeatedPrefixes(paragraphs, 2),
    repeatedPhrases: detectNgrams(phraseTokens, ignored, includeCommon),
    phraseScanWords: phraseTokens.length,
    customTics: detectCustomTics(tokens, tics),
  };
}
