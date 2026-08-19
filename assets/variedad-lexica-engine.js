const WORD_RE = /[\p{L}\p{M}]+(?:[’'\-][\p{L}\p{M}]+)*/gu;

export function tokenizeSpanish(text) {
  return (String(text || '').normalize('NFC').match(WORD_RE) || [])
    .map(token => token.toLocaleLowerCase('es-ES'));
}

export function typeTokenRatio(tokens) {
  if (!tokens.length) return null;
  return new Set(tokens).size / tokens.length;
}

export function movingAverageTTR(tokens, windowSize = 50) {
  const size = Math.max(2, Math.floor(Number(windowSize) || 50));
  if (tokens.length < size) return null;

  const counts = new Map();
  let unique = 0;
  let total = 0;
  let windows = 0;

  const add = token => {
    const prev = counts.get(token) || 0;
    if (prev === 0) unique += 1;
    counts.set(token, prev + 1);
  };

  const remove = token => {
    const prev = counts.get(token) || 0;
    if (prev <= 1) {
      counts.delete(token);
      if (prev === 1) unique -= 1;
    } else {
      counts.set(token, prev - 1);
    }
  };

  for (let i = 0; i < size; i += 1) add(tokens[i]);
  total += unique / size;
  windows += 1;

  for (let start = 1; start <= tokens.length - size; start += 1) {
    remove(tokens[start - 1]);
    add(tokens[start + size - 1]);
    total += unique / size;
    windows += 1;
  }

  return windows ? total / windows : null;
}

function mtldDirection(tokens, threshold = 0.72, minFactorTokens = 10) {
  if (!tokens.length) return null;

  let factors = 0;
  let factorLength = 0;
  const types = new Set();

  for (let index = 0; index < tokens.length; index += 1) {
    factorLength += 1;
    types.add(tokens[index]);
    const ttr = types.size / factorLength;
    const atLastToken = index === tokens.length - 1;

    if (!atLastToken && factorLength >= minFactorTokens && ttr < threshold) {
      factors += 1;
      factorLength = 0;
      types.clear();
      continue;
    }

    if (atLastToken && factorLength > 0) {
      factors += (1 - ttr) / (1 - threshold);
    }
  }

  if (!Number.isFinite(factors) || factors <= 0) return null;
  return tokens.length / factors;
}

export function mtld(tokens, threshold = 0.72) {
  const limit = Number(threshold);
  if (!tokens.length || !Number.isFinite(limit) || limit <= 0 || limit >= 1) return null;

  const forward = mtldDirection(tokens, limit);
  const backward = mtldDirection([...tokens].reverse(), limit);
  const usable = [forward, backward].filter(Number.isFinite);
  if (!usable.length) return null;
  return usable.reduce((sum, value) => sum + value, 0) / usable.length;
}

export function fixedSegmentProfile(tokens, segmentSize = 200, mattrWindow = 50) {
  const window = Math.max(2, Math.floor(Number(mattrWindow) || 50));
  const size = Math.max(window, Math.floor(Number(segmentSize) || 200));
  const rows = [];

  for (let start = 0; start < tokens.length; start += size) {
    const segment = tokens.slice(start, start + size);
    if (segment.length < window) continue;
    rows.push({
      index: rows.length + 1,
      startWord: start + 1,
      endWord: start + segment.length,
      tokenCount: segment.length,
      typeCount: new Set(segment).size,
      ttr: typeTokenRatio(segment),
      mattr: movingAverageTTR(segment, window),
    });
  }

  return rows;
}

export function analyzeLexicalDiversity(text, options = {}) {
  const segmentSize = Math.max(50, Math.floor(Number(options.segmentSize) || 200));
  const tokens = tokenizeSpanish(text);
  const frequencies = new Map();

  for (const token of tokens) frequencies.set(token, (frequencies.get(token) || 0) + 1);

  const typeCount = frequencies.size;
  const hapaxCount = [...frequencies.values()].filter(value => value === 1).length;

  return {
    tokenCount: tokens.length,
    typeCount,
    hapaxCount,
    hapaxShareOfTypes: typeCount ? hapaxCount / typeCount : null,
    ttr: typeTokenRatio(tokens),
    mattr50: movingAverageTTR(tokens, 50),
    mattr100: movingAverageTTR(tokens, 100),
    mtld: tokens.length >= 50 ? mtld(tokens, 0.72) : null,
    mtldThreshold: 0.72,
    segmentSize,
    profile: fixedSegmentProfile(tokens, segmentSize, 50),
    minimumForWindow50: tokens.length >= 50,
    sampleShort: tokens.length < 100,
    method: 'surface-forms',
  };
}
