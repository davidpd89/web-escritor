(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.PovDistribution = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const MAX_SCENES = 500;
  const MAX_POVS = 30;
  const MAX_LABEL = 80;
  const MAX_POV = 80;

  function clean(value) {
    return String(value ?? '').trim();
  }

  function splitRow(line) {
    if (line.includes('\t')) return line.split('\t');
    return line.split('|');
  }

  function parse(text) {
    const rawLines = String(text ?? '').split(/\r?\n/);
    const scenes = [];
    const errors = [];

    rawLines.forEach((raw, lineIndex) => {
      const line = raw.trim();
      if (!line || line.startsWith('#')) return;
      const parts = splitRow(raw).map(clean);
      if (parts.length < 2 || parts.length > 3) {
        errors.push(`Línea ${lineIndex + 1}: usa «escena | POV | palabras opcionales».`);
        return;
      }
      const [label, pov, wordsRaw = ''] = parts;
      if (!label || label.length > MAX_LABEL) {
        errors.push(`Línea ${lineIndex + 1}: etiqueta de escena ausente o demasiado larga.`);
        return;
      }
      if (!pov || pov.length > MAX_POV) {
        errors.push(`Línea ${lineIndex + 1}: POV ausente o demasiado largo.`);
        return;
      }
      let words = null;
      if (wordsRaw !== '') {
        if (!/^\d+$/.test(wordsRaw)) {
          errors.push(`Línea ${lineIndex + 1}: las palabras deben ser un entero positivo.`);
          return;
        }
        words = Number(wordsRaw);
        if (!Number.isSafeInteger(words) || words < 1 || words > 100000) {
          errors.push(`Línea ${lineIndex + 1}: palabras fuera del rango 1–100000.`);
          return;
        }
      }
      scenes.push({ label, pov, words, index: scenes.length + 1 });
    });

    if (scenes.length > MAX_SCENES) errors.push(`Máximo ${MAX_SCENES} escenas por análisis.`);
    const uniquePovs = [...new Set(scenes.map(s => s.pov))];
    if (uniquePovs.length > MAX_POVS) errors.push(`Máximo ${MAX_POVS} POV distintos por análisis.`);
    if (!scenes.length && !errors.length) errors.push('Añade al menos una escena.');

    return { scenes: errors.length ? [] : scenes, errors };
  }

  function longestRun(indices) {
    if (!indices.length) return 0;
    let best = 1, current = 1;
    for (let i = 1; i < indices.length; i += 1) {
      if (indices[i] === indices[i - 1] + 1) current += 1;
      else current = 1;
      best = Math.max(best, current);
    }
    return best;
  }

  function maxInternalGap(indices) {
    if (indices.length < 2) return 0;
    let best = 0;
    for (let i = 1; i < indices.length; i += 1) {
      best = Math.max(best, indices[i] - indices[i - 1] - 1);
    }
    return best;
  }

  function analyze(scenes) {
    if (!Array.isArray(scenes) || !scenes.length) throw new Error('Se requiere al menos una escena.');
    const povOrder = [];
    const seen = new Set();
    scenes.forEach(scene => {
      if (!seen.has(scene.pov)) { seen.add(scene.pov); povOrder.push(scene.pov); }
    });

    const completeWords = scenes.every(scene => Number.isInteger(scene.words) && scene.words > 0);
    const totalWords = completeWords ? scenes.reduce((sum, scene) => sum + scene.words, 0) : null;

    const povs = povOrder.map((pov, order) => {
      const positions = [];
      let words = 0;
      scenes.forEach((scene, i) => {
        if (scene.pov !== pov) return;
        positions.push(i + 1);
        if (completeWords) words += scene.words;
      });
      return {
        pov,
        order,
        sceneCount: positions.length,
        sceneShare: positions.length / scenes.length,
        wordCount: completeWords ? words : null,
        wordShare: completeWords && totalWords ? words / totalWords : null,
        firstScene: positions[0],
        lastScene: positions[positions.length - 1],
        longestRun: longestRun(positions),
        maxInternalGap: maxInternalGap(positions),
        positions
      };
    });

    return {
      scenes: scenes.map((s, i) => ({ ...s, index: i + 1, povOrder: povOrder.indexOf(s.pov) })),
      povs,
      totalScenes: scenes.length,
      totalPovs: povs.length,
      completeWords,
      totalWords
    };
  }

  function bucketSceneCount(n) {
    if (n < 10) return '1-9';
    if (n < 30) return '10-29';
    if (n < 80) return '30-79';
    return '80+';
  }

  // Formato V1 documentado "POV | palabras" (O.2, 2026-08-23): totales ya
  // agregados por punto de vista, no escenas individuales. Es un formato
  // DISTINTO y explicito (el usuario lo elige en la UI, no se infiere por
  // el numero de columnas): "escena | POV" y "POV | palabras" son ambos de
  // 2 columnas, así que adivinar cuál es cuál a partir del contenido sería
  // una heurística opaca. parse()/analyze() (escenas) no se tocan.
  function parseTotals(text) {
    const rawLines = String(text ?? '').split(/\r?\n/);
    const totals = [];
    const errors = [];
    const seenPovs = new Set();

    rawLines.forEach((raw, lineIndex) => {
      const line = raw.trim();
      if (!line || line.startsWith('#')) return;
      const parts = splitRow(raw).map(clean);
      if (parts.length !== 2) {
        errors.push(`Línea ${lineIndex + 1}: usa «POV | palabras».`);
        return;
      }
      const [pov, wordsRaw] = parts;
      if (!pov || pov.length > MAX_POV) {
        errors.push(`Línea ${lineIndex + 1}: POV ausente o demasiado largo.`);
        return;
      }
      if (!/^\d+$/.test(wordsRaw)) {
        errors.push(`Línea ${lineIndex + 1}: las palabras deben ser un entero positivo.`);
        return;
      }
      const words = Number(wordsRaw);
      if (!Number.isSafeInteger(words) || words < 1 || words > 10000000) {
        errors.push(`Línea ${lineIndex + 1}: palabras fuera del rango 1–10000000.`);
        return;
      }
      if (seenPovs.has(pov)) {
        errors.push(`Línea ${lineIndex + 1}: el POV «${pov}» ya aparece antes; usa una sola línea por POV.`);
        return;
      }
      seenPovs.add(pov);
      totals.push({ pov, words });
    });

    if (totals.length > MAX_POVS) errors.push(`Máximo ${MAX_POVS} POV distintos por análisis.`);
    if (!totals.length && !errors.length) errors.push('Añade al menos un POV con sus palabras.');

    return { totals: errors.length ? [] : totals, errors };
  }

  function analyzeTotals(totals) {
    if (!Array.isArray(totals) || !totals.length) throw new Error('Se requiere al menos un POV con palabras.');
    const totalWords = totals.reduce((sum, t) => sum + t.words, 0);
    const povs = totals.map((t, order) => ({
      pov: t.pov,
      order,
      wordCount: t.words,
      wordShare: totalWords ? t.words / totalWords : 0,
    }));
    return { mode: 'totals', povs, totalPovs: povs.length, totalWords };
  }

  // Rounding each POV's share independently for display (e.g. a three-way
  // 1/3 split -> 33 %, 33 %, 33 %) visibly sums to 99 %, which reads as a
  // bug even though the underlying counts are exact -- confirmed live with
  // a 3/7,2/7,2/7 scene split showing 43 %, 29 %, 29 % (sum 101 %).
  // Largest-remainder allocation guarantees a set of shares always sums to
  // exactly 100 as whole percentages.
  function sharesToWholePercent(shares) {
    const floors = shares.map(s => Math.floor(s * 100));
    const remainder = 100 - floors.reduce((sum, v) => sum + v, 0);
    const order = shares.map((s, i) => ({ i, frac: (s * 100) - floors[i] })).sort((a, b) => b.frac - a.frac);
    const result = floors.slice();
    for (let k = 0; k < remainder && k < order.length; k++) result[order[k].i]++;
    return result;
  }

  return { parse, analyze, parseTotals, analyzeTotals, bucketSceneCount, sharesToWholePercent, MAX_SCENES, MAX_POVS };
});
