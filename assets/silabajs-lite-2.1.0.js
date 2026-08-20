/*
 * silabajs-lite-2.1.0.js
 * Adaptación mínima para conteo silábico a partir de silabajs 2.1.0.
 * Upstream: https://github.com/nicofrem/silabajs
 * Autor upstream: Nicolás Cofré Méndez
 * Licencia upstream: MIT
 *
 * Copyright (c) 2018 Nicolás Cofré Méndez
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

const STRONG_VOWELS = new Set(['a','e','o','á','é','ó','à','è','ò']);
const WEAK_VOWELS = new Set(['i','u','ü']);
const ACCENTED_WEAK_VOWELS = new Set(['í','ú','ì','ù','ü']);
const ALL_VOWELS = new Set([...STRONG_VOWELS, ...WEAK_VOWELS, ...ACCENTED_WEAK_VOWELS]);
const L_CLUSTER_INITIALS = new Set(['b','v','c','k','f','g','p','t']);
const R_CLUSTER_INITIALS = new Set(['b','v','c','d','k','f','g','p','t']);
const Y_PRECEDING_ALVEOLARS = new Set(['s','l','r','n','c']);
const ONSET_DIGRAPHS = new Set(['pt','ct','cn','ps','mn','gn','ft','pn','cz','tz','ts']);
const ACCENTED_STRONG = new Set(['á','é','ó','à','è','ò']);

const isConsonant = (c) => !ALL_VOWELS.has(c);
const vowelStrength = (c) => {
  if (STRONG_VOWELS.has(c)) return 0;
  if (ACCENTED_WEAK_VOWELS.has(c)) return 1;
  if (WEAK_VOWELS.has(c)) return 2;
  return -1;
};

const processOnset = (word, state) => {
  const len = word.length;
  let pos = state.position;
  let lastConsonant = 'a';
  while (pos < len && isConsonant(word[pos]) && word[pos] !== 'y') {
    lastConsonant = word[pos];
    pos++;
  }
  if (pos < len - 1) {
    if (word[pos] === 'u') {
      if (lastConsonant === 'q') pos++;
      else if (lastConsonant === 'g') {
        const next = word[pos + 1];
        if (next === 'e' || next === 'é' || next === 'i' || next === 'í') pos++;
      }
    } else if (word[pos] === 'ü' && lastConsonant === 'g') {
      pos++;
    }
  }
  return { ...state, position: pos };
};

const processNucleus = (word, state) => {
  const len = word.length;
  let pos = state.position;
  let foundTonic = state.foundTonic;
  let accentedLetterIndex = state.accentedLetterIndex;
  if (pos >= len) return { position: pos, foundTonic, accentedLetterIndex };
  if (word[pos] === 'y') pos++;
  let prevStrength = -1;
  if (pos < len) {
    const strength = vowelStrength(word[pos]);
    if (strength === 0) {
      if (ACCENTED_STRONG.has(word[pos])) { accentedLetterIndex = pos; foundTonic = true; }
      prevStrength = 0; pos++;
    } else if (strength === 1) {
      accentedLetterIndex = pos; foundTonic = true; pos++;
      return { position: pos, foundTonic, accentedLetterIndex };
    } else if (strength === 2) {
      prevStrength = 2; pos++;
    }
  }
  let hasIntercalatedH = false;
  if (pos < len && word[pos] === 'h') { pos++; hasIntercalatedH = true; }
  if (pos < len) {
    const strength = vowelStrength(word[pos]);
    if (strength === 0) {
      if (ACCENTED_STRONG.has(word[pos])) {
        accentedLetterIndex = pos;
        if (prevStrength !== 0) foundTonic = true;
      }
      if (prevStrength === 0) {
        if (hasIntercalatedH) pos--;
        return { position: pos, foundTonic, accentedLetterIndex };
      }
      pos++;
    } else if (strength === 1) {
      accentedLetterIndex = pos;
      if (prevStrength !== 0) { foundTonic = true; pos++; }
      else if (hasIntercalatedH) pos--;
      return { position: pos, foundTonic, accentedLetterIndex };
    } else if (strength === 2) {
      if (pos < len - 1) {
        const nextChar = word[pos + 1];
        if (!isConsonant(nextChar)) {
          if (hasIntercalatedH && word[pos - 1] === 'h') pos--;
          return { position: pos, foundTonic, accentedLetterIndex };
        }
      }
      if (word[pos] !== word[pos - 1]) pos++;
      return { position: pos, foundTonic, accentedLetterIndex };
    }
  }
  if (pos < len && (word[pos] === 'i' || word[pos] === 'u')) pos++;
  return { position: pos, foundTonic, accentedLetterIndex };
};

const handleTwoConsonants = (state, pos, c1, c2) => {
  if ((c1 === 'l' && c2 === 'l') || (c1 === 'c' && c2 === 'h') || (c1 === 'r' && c2 === 'r')) return { ...state, position: pos };
  if (c1 !== 's' && c1 !== 'r' && c2 === 'h') return { ...state, position: pos };
  if (c2 === 'y') return { ...state, position: Y_PRECEDING_ALVEOLARS.has(c1) ? pos : pos + 1 };
  if (L_CLUSTER_INITIALS.has(c1) && c2 === 'l') return { ...state, position: pos };
  if (R_CLUSTER_INITIALS.has(c1) && c2 === 'r') return { ...state, position: pos };
  return { ...state, position: pos + 1 };
};

const handleThreeOrMoreConsonants = (word, state, pos, c1, c2, c3) => {
  const len = word.length;
  if (pos + 3 === len) {
    if (c2 === 'y' && Y_PRECEDING_ALVEOLARS.has(c1)) return { ...state, position: pos };
    if (c3 === 'y') return { ...state, position: pos + 1 };
    return { ...state, position: pos + 3 };
  }
  if (c2 === 'y') return { ...state, position: Y_PRECEDING_ALVEOLARS.has(c1) ? pos : pos + 1 };
  if (ONSET_DIGRAPHS.has(c2 + c3)) return { ...state, position: pos + 1 };
  if (c3 === 'l' || c3 === 'r' || (c2 === 'c' && c3 === 'h') || c3 === 'y') return { ...state, position: pos + 1 };
  return { ...state, position: pos + 2 };
};

const processCoda = (word, state) => {
  const len = word.length;
  const pos = state.position;
  if (pos >= len || !isConsonant(word[pos])) return { ...state, position: pos };
  if (pos === len - 1) return { ...state, position: pos + 1 };
  if (!isConsonant(word[pos + 1])) return { ...state, position: pos };
  const c1 = word[pos], c2 = word[pos + 1];
  if (pos < len - 2) {
    const c3 = word[pos + 2];
    if (!isConsonant(c3)) return handleTwoConsonants(state, pos, c1, c2);
    return handleThreeOrMoreConsonants(word, state, pos, c1, c2, c3);
  }
  if (c2 === 'y') return { ...state, position: pos };
  return { ...state, position: pos + 2 };
};

export const countSpanishSyllables = (input) => {
  const word = String(input || '').trim().toLocaleLowerCase('es').normalize('NFC');
  if (!word) return 0;
  let state = { position: 0, foundTonic: false, accentedLetterIndex: -1 };
  let count = 0;
  const maxIterations = Math.max(4, word.length * 2);
  while (state.position < word.length && count < maxIterations) {
    const start = state.position;
    count++;
    state = processOnset(word, state);
    state = processNucleus(word, state);
    state = processCoda(word, state);
    if (state.position <= start) state = { ...state, position: start + 1 };
  }
  return Math.max(1, count);
};
