const WORD_RE = /[\p{L}\p{M}\p{N}]+(?:['’-][\p{L}\p{M}\p{N}]+)*/gu;
// Zero-width space/joiners and BOM match nothing in \p{L}\p{M}\p{N} -- one
// landing inside a word (a real artifact from some PDF/OCR extraction
// pipelines) splits it into two matches, inflating the word count that
// drives this tool's reading-time estimate.
const INVISIBLE_RE = /[\u200B-\u200D\uFEFF]/g;

export function countWords(value) {
  return (String(value || '').replace(INVISIBLE_RE, '').normalize('NFC').match(WORD_RE) || []).length;
}

function clampNum(value, min, max, fallback) {
  const parsed = Number(String(value ?? '').replace(',', '.'));
  const n = Number.isFinite(parsed) ? parsed : fallback;
  return Math.min(max, Math.max(min, n));
}

export function formatDuration(minutes) {
  const totalSeconds = Math.max(0, Math.round(minutes * 60));
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  if (h) return `${h} h ${m} min ${s} s`;
  if (m) return `${m} min ${s} s`;
  return `${s} s`;
}

/**
 * Pure calculation: read-aloud time for a given word count (or text),
 * speaking speed (words per minute), pause buffer, and a target duration.
 * No DOM, no network — safe to run in Node for tests.
 *
 * @param {{text?:string, manualWords?:number, wpm?:number, bufferPct?:number, targetMinutes?:number}} input
 */
export function calculateReadAloud(input = {}) {
  const speed = clampNum(input.wpm, 60, 300, 155);
  const bufferPct = clampNum(input.bufferPct, 0, 100, 0);
  const pauseFactor = 1 + bufferPct / 100;
  const targetMinutes = clampNum(input.targetMinutes, 0.5, 600, 5);

  const typedWords = input.text ? countWords(input.text) : 0;
  const manual = Math.max(0, Math.floor(Number(input.manualWords) || 0));
  const words = typedWords || manual;

  if (!words) {
    return { words: 0, minutes: 0, duration: null, maxWordsForTarget: 0, effectiveWpm: 0, quickBudgets: [] };
  }

  const baseMinutes = words / speed;
  const finalMinutes = baseMinutes * pauseFactor;
  const maxWordsForTarget = Math.floor((targetMinutes * speed) / pauseFactor);
  const effectiveWpm = speed / pauseFactor;
  const quickBudgets = [3, 5, 10, 15].map(minutes => ({
    minutes,
    words: Math.floor((minutes * speed) / pauseFactor),
  }));

  return {
    words,
    minutes: finalMinutes,
    duration: formatDuration(finalMinutes),
    maxWordsForTarget,
    effectiveWpm,
    quickBudgets,
  };
}

function fmt(n) {
  return Number(n || 0).toLocaleString('es-ES');
}

export function render(result, refs) {
  if (!result.words) {
    refs.results.hidden = true;
    refs.status.textContent = 'Pega un texto o introduce un número de palabras.';
    return;
  }
  refs.wordCount.textContent = fmt(result.words);
  refs.duration.textContent = result.duration;
  refs.capacity.textContent = `${fmt(result.maxWordsForTarget)} palabras aprox.`;
  refs.effective.textContent = `${Math.round(result.effectiveWpm)} ppm efectivas`;
  refs.quick.replaceChildren();
  result.quickBudgets.forEach(({ minutes, words }) => {
    const li = document.createElement('li');
    li.textContent = `${minutes} min → unas ${fmt(words)} palabras`;
    refs.quick.append(li);
  });
  refs.results.hidden = false;
  refs.status.textContent = 'Cálculo realizado localmente. El texto no se envía ni se guarda.';
}

export function init() {
  const form = document.querySelector('[data-readaloud-form]');
  if (!form) return;

  const refs = {
    text: form.querySelector('[data-readaloud-text]'),
    manualWords: form.querySelector('[data-readaloud-manual-words]'),
    wpm: form.querySelector('[data-readaloud-wpm]'),
    buffer: form.querySelector('[data-readaloud-buffer]'),
    target: form.querySelector('[data-readaloud-target]'),
    results: document.querySelector('[data-readaloud-results]'),
    duration: document.querySelector('[data-readaloud-duration]'),
    wordCount: document.querySelector('[data-readaloud-word-count]'),
    capacity: document.querySelector('[data-readaloud-capacity]'),
    effective: document.querySelector('[data-readaloud-effective]'),
    quick: document.querySelector('[data-readaloud-quick]'),
    status: document.querySelector('[data-readaloud-status]'),
  };
  const sample = form.querySelector('[data-readaloud-sample]');
  const clear = form.querySelector('[data-readaloud-clear]');

  const runCalculation = () => {
    const result = calculateReadAloud({
      text: refs.text.value,
      manualWords: refs.manualWords.value,
      wpm: refs.wpm.value,
      bufferPct: refs.buffer.value,
      targetMinutes: refs.target.value,
    });
    render(result, refs);
  };

  form.addEventListener('submit', event => { event.preventDefault(); runCalculation(); });

  sample?.addEventListener('click', () => {
    refs.text.value = 'La mujer dejó el reloj sobre la mesa y esperó. Nadie había preguntado por él en años. Cuando abrió la caja, encontró una nota doblada cuatro veces y decidió llamar a su hermana antes de convertir un recuerdo incompleto en una certeza.';
    refs.manualWords.value = '';
    refs.status.textContent = 'Ejemplo cargado. Ajusta la velocidad o el margen y calcula.';
  });

  clear?.addEventListener('click', () => {
    refs.text.value = '';
    refs.manualWords.value = '';
    refs.results.hidden = true;
    refs.status.textContent = 'Nada de lo que pegues se envía al servidor.';
  });

  form.querySelectorAll('[data-wpm-reference]').forEach(button => {
    button.addEventListener('click', () => {
      refs.wpm.value = button.dataset.wpmReference;
      refs.status.textContent = button.dataset.referenceLabel || 'Referencia aplicada.';
    });
  });
}

if (typeof document !== 'undefined') init();
