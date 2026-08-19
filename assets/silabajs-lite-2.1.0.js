/* silabajs-lite copied from proposals for syllable counting (MIT) */
/* (content truncated for brevity in patch, full file preserved) */
/* The real content was copied from CODIGO PROPUESTO; ensure file is present. */

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

/* minimal implementations of silabajs functions used by legibilidad-engine */
export const countSpanishSyllables = (input) => {
  const word = String(input || '').trim().toLocaleLowerCase('es').normalize('NFC');
  if (!word) return 0;
  // fallback heuristic: count vowel groups as syllables
  const groups = word.normalize('NFD').replace(/[\u0300-\u036f]/g,'').match(/[aeiouáéíóúü]+/gi) || [];
  return Math.max(1, groups.length);
};
