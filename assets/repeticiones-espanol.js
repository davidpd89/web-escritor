import { analyzeRepetitions } from './repeticiones-engine.js';

const $ = (sel, root = document) => root.querySelector(sel);
const form = $('[data-repetition-form]');
if (!form) throw new Error('Falta [data-repetition-form]');
const input = $('[data-repetition-input]', form);
const windowSelect = $('[data-repetition-window]', form);
const ticsInput = $('[data-repetition-tics]', form);
const ignoredInput = $('[data-repetition-ignore]', form);
const commonInput = $('[data-repetition-common]', form);
const results = $('[data-repetition-results]');
const status = $('[data-repetition-status]');

function esc(value) {
  return String(value ?? '').replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
}
// per1000 arrives as a plain number (e.g. 21.9) from the engine; every other
// number in this file already goes through toLocaleString('es-ES') before
// display, but this one didn't -- confirmed live showing "21.9 por 1000
// palabras" (period) instead of "21,9 por 1000 palabras" (comma).
function fmtDecimal(n) {
  return Number(n).toLocaleString('es-ES', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
}
function emit() { /* analytics disabled for privacy */ }
function bucket(n) {
  if (n < 100) return '<100';
  if (n < 500) return '100-499';
  if (n < 2000) return '500-1999';
  if (n < 10000) return '2000-9999';
  return '10000+';
}
function empty(message) { return `<li class="repetition-empty">${esc(message)}</li>`; }
function sampleList(samples = []) { return samples.map(s => `<q>${esc(s)}</q>`).join(''); }

function render(data) {
  if (data.empty) {
    results.hidden = true;
    status.textContent = 'Pega un texto para analizarlo.';
    return;
  }
  results.hidden = false;
  const phraseNote = data.phraseScanWords < data.wordCount ? ` Las frases repetidas se han buscado en las primeras ${data.phraseScanWords.toLocaleString('es-ES')} palabras para evitar bloquear el navegador.` : '';
  status.textContent = `Analizadas ${data.wordCount.toLocaleString('es-ES')} palabras. Nada del texto ha salido de tu navegador.${phraseNote}`;
  $('[data-repetition-summary]', results).innerHTML = `
    <div><strong>${data.wordCount.toLocaleString('es-ES')}</strong><span>palabras</span></div>
    <div><strong>${data.uniqueAnalyzedWords.toLocaleString('es-ES')}</strong><span>formas analizadas</span></div>
    <div><strong>${data.echoes.length}</strong><span>ecos cercanos</span></div>
    <div><strong>${data.repeatedPhrases.length}</strong><span>frases repetidas</span></div>`;

  $('[data-immediate]', results).innerHTML = data.immediateDuplicates.length
    ? data.immediateDuplicates.map(x => `<li><strong>${esc(x.word)}</strong><p>${esc(x.context)}</p></li>`).join('')
    : empty('No se han detectado duplicados inmediatos.');

  $('[data-echoes]', results).innerHTML = data.echoes.length
    ? data.echoes.slice(0, 25).map(x => `<li><div><strong>${esc(x.word)}</strong><span>${x.count} apariciones · ${x.closePairs} pares a ≤${data.windowSize} palabras · distancia mínima ${x.closestGap}</span></div>${sampleList(x.samples)}</li>`).join('')
    : empty('No se han detectado ecos con la ventana elegida.');

  $('[data-dominant]', results).innerHTML = data.dominantWords.length
    ? data.dominantWords.slice(0, 20).map(x => `<li><strong>${esc(x.word)}</strong><span>${x.count} · ${fmtDecimal(x.per1000)} por 1000 palabras</span></li>`).join('')
    : empty('No hay palabras de contenido con frecuencia suficiente para destacar.');

  const starts = [
    ...data.sentenceStarts.map(x => ({ type: 'frases', ...x })),
    ...data.paragraphStarts.map(x => ({ type: 'párrafos', ...x })),
  ];
  $('[data-starts]', results).innerHTML = starts.length
    ? starts.map(x => `<li><strong>${esc(x.prefix)}</strong><span>Inicio repetido en ${x.type}: ${x.indexes.join(', ')}</span></li>`).join('')
    : empty('No se repiten comienzos de dos palabras en frases o párrafos.');

  $('[data-phrases]', results).innerHTML = data.repeatedPhrases.length
    ? data.repeatedPhrases.map(x => `<li><div><strong>${esc(x.phrase)}</strong><span>${x.count} veces · ${x.words} palabras</span></div>${sampleList(x.samples)}</li>`).join('')
    : empty('No se han detectado secuencias repetidas de 2–5 palabras.');

  $('[data-tics]', results).innerHTML = data.customTics.length
    ? data.customTics.map(x => `<li><div><strong>${esc(x.tic)}</strong><span>${x.count} apariciones</span></div>${sampleList(x.samples)}</li>`).join('')
    : empty(ticsInput.value.trim() ? 'Ninguno de tus tics personalizados aparece en el texto.' : 'Añade palabras o expresiones arriba si quieres vigilarlas de forma explícita.');
}

function analyze() {
  const data = analyzeRepetitions(input.value, {
    windowSize: windowSelect.value,
    tics: ticsInput.value,
    ignored: ignoredInput.value,
    includeCommon: commonInput.checked,
  });
  render(data);
  if (!data.empty) emit('repetition_analyze', { target: `${bucket(data.wordCount)}|w${data.windowSize}` });
}

form.addEventListener('submit', event => { event.preventDefault(); analyze(); });
$('[data-repetition-sample]', form)?.addEventListener('click', () => {
  input.value = `Ana miró la puerta. La puerta seguía abierta y Ana volvió a mirar la puerta antes de entrar. Parecía tranquila. Parecía tranquila, al menos desde fuera.\n\nAna dio un paso. Ana dio otro paso. Entonces miró a Bruno, y entonces comprendió que llevaba toda la conversación diciendo entonces sin darse cuenta.`;
  ticsInput.value = 'parecía, entonces, Ana dio';
  analyze(); emit('repetition_sample'); input.focus();
});
$('[data-repetition-clear]', form)?.addEventListener('click', () => {
  input.value = ''; ticsInput.value = ''; ignoredInput.value = ''; results.hidden = true;
  status.textContent = 'Texto borrado. Nada se guarda ni se envía.'; emit('repetition_clear'); input.focus();
});
