export const strip = (value) => String(value || '')
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .toLowerCase()
  .replace(/[^a-zñ]/g, '');

export const levenshtein = (a, b) => {
  a = strip(a); b = strip(b);
  if (!a.length) return b.length;
  if (!b.length) return a.length;
  const prev = Array.from({length: b.length + 1}, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    let diag = prev[0];
    prev[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const old = prev[j];
      prev[j] = Math.min(
        prev[j] + 1,
        prev[j - 1] + 1,
        diag + (a[i - 1] === b[j - 1] ? 0 : 1)
      );
      diag = old;
    }
  }
  return prev[b.length];
};

export const normalizedEditSimilarity = (a, b) => {
  a = strip(a); b = strip(b);
  const max = Math.max(a.length, b.length);
  return max ? 1 - levenshtein(a, b) / max : 1;
};

export const jaro = (s1, s2) => {
  s1 = strip(s1); s2 = strip(s2);
  if (s1 === s2) return 1;
  if (!s1.length || !s2.length) return 0;
  const range = Math.max(0, Math.floor(Math.max(s1.length, s2.length) / 2) - 1);
  const m1 = new Array(s1.length).fill(false);
  const m2 = new Array(s2.length).fill(false);
  let matches = 0;
  for (let i = 0; i < s1.length; i++) {
    const start = Math.max(0, i - range);
    const end = Math.min(i + range + 1, s2.length);
    for (let j = start; j < end; j++) {
      if (m2[j] || s1[i] !== s2[j]) continue;
      m1[i] = true; m2[j] = true; matches++; break;
    }
  }
  if (!matches) return 0;
  const a = [], b = [];
  for (let i = 0; i < s1.length; i++) if (m1[i]) a.push(s1[i]);
  for (let j = 0; j < s2.length; j++) if (m2[j]) b.push(s2[j]);
  let transpositions = 0;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) transpositions++;
  return (matches / s1.length + matches / s2.length + (matches - transpositions / 2) / matches) / 3;
};

export const jaroWinkler = (a, b) => {
  const sa = strip(a), sb = strip(b);
  const j = jaro(sa, sb);
  let prefix = 0;
  while (prefix < Math.min(4, sa.length, sb.length) && sa[prefix] === sb[prefix]) prefix++;
  return j + prefix * 0.1 * (1 - j);
};

export const vowelPattern = (value) => strip(value).replace(/[^aeiou]/g, '');
export const cvPattern = (value) => strip(value).replace(/[aeiou]/g, 'V').replace(/[^V]/g, 'C');

export const commonPrefixLength = (a, b) => {
  a = strip(a); b = strip(b);
  let i = 0;
  while (i < Math.min(a.length, b.length) && a[i] === b[i]) i++;
  return i;
};

export const pair = (left, right) => {
  const a = strip(left), b = strip(right);
  const exact = a && a === b;
  const edit = normalizedEditSimilarity(a, b);
  const jw = jaroWinkler(a, b);
  const vowels = normalizedEditSimilarity(vowelPattern(a), vowelPattern(b));
  const shape = normalizedEditSimilarity(cvPattern(a), cvPattern(b));
  const sameInitial = Boolean(a && b && a[0] === b[0]);
  const sameEnding = Boolean(a.length > 1 && b.length > 1 && a.slice(-2) === b.slice(-2));
  const prefix = commonPrefixLength(a, b);
  const lengthGap = Math.abs(a.length - b.length);

  let score = jw * 0.42 + edit * 0.30 + vowels * 0.12 + shape * 0.08;
  if (sameInitial) score += 0.04;
  if (sameEnding) score += 0.02;
  if (prefix >= 2) score += Math.min(0.04, prefix * 0.01);
  if (lengthGap >= 4) score -= 0.03;
  score = Math.max(0, Math.min(1, score));

  const reasons = [];
  if (exact) reasons.push('mismo nombre al normalizar tildes/mayúsculas');
  if (sameInitial) reasons.push('misma inicial');
  if (prefix >= 2) reasons.push(`prefijo común de ${prefix} letras`);
  if (sameEnding) reasons.push('terminación parecida');
  if (Math.abs(a.length - b.length) <= 1) reasons.push('longitud casi idéntica');
  if (vowels >= 0.8 && vowelPattern(a).length > 1) reasons.push('patrón vocálico parecido');
  if (shape >= 0.8) reasons.push('silueta consonante/vocal parecida');

  let level = 'low';
  if (exact || score >= 0.88) level = 'high';
  else if (score >= 0.76) level = 'medium';

  return {left, right, score, level, reasons, metrics: {edit, jaroWinkler: jw, vowels, shape, sameInitial, prefix, lengthGap}};
};

// Solo pliega mayúsculas/minúsculas para decidir si dos entradas de ENTRADA
// son el mismo dato repetido dos veces. Deliberadamente NO usa strip(): esa
// función también quita tildes, y una tilde de menos/más es precisamente el
// tipo de par que esta herramienta existe para detectar y mostrar (ver el
// ejemplo del propio documento fuente, "Ana / Antía"). "Bruno" y "Brunó" son
// dos grafías distintas que un autor puede haber elegido a propósito para dos
// personajes distintos: deben compararse y, si procede, marcarse como
// confundibles — no desaparecer en silencio como si fueran la misma entrada
// repetida. "Noa"/"noa"/"NOA" sí son literalmente el mismo dato tecleado con
// distinta caja, y esos sí deben colapsar en una sola entrada.
const dedupeKey = (value) => value.toLocaleLowerCase('es');

export const analyze = (names) => {
  // Deduplicar por forma normalizada de MAYÚSCULA/MINÚSCULA únicamente (ver
  // dedupeKey arriba), no por el string exacto. Antes se usaba un Set() sobre
  // el texto tal cual, así que "Noa"/"noa"/"NOA" no se consideraban
  // duplicados: llegaban los tres a pair(), que sí reconoce que son el mismo
  // nombre normalizado y los marcaba "alta" con el motivo "mismo nombre al
  // normalizar tildes/mayúsculas" — el contrato del documento fuente (34,
  // sección 13) pide justo lo contrario: que los duplicados de entrada se
  // eliminen, no que se informen como una alerta de confusión entre dos
  // personajes. Se conserva la PRIMERA grafía vista para mostrarla intacta.
  const seen = new Set();
  const cleaned = [];
  for (const raw of names || []) {
    const trimmed = String(raw).trim();
    if (!trimmed) continue;
    const key = dedupeKey(trimmed);
    if (seen.has(key)) continue;
    seen.add(key);
    cleaned.push(trimmed);
  }
  const pairs = [];
  for (let i = 0; i < cleaned.length; i++) {
    for (let j = i + 1; j < cleaned.length; j++) pairs.push(pair(cleaned[i], cleaned[j]));
  }
  pairs.sort((x, y) => y.score - x.score);
  return {
    names: cleaned,
    pairs,
    flagged: pairs.filter(p => p.level !== 'low'),
    counts: {
      totalNames: cleaned.length,
      comparedPairs: pairs.length,
      high: pairs.filter(p => p.level === 'high').length,
      medium: pairs.filter(p => p.level === 'medium').length
    }
  };
};
