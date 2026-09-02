import { analyzeText, wordsFrom } from './legibilidad-engine.js';

const form = document.querySelector('[data-readability-form]');
const input = document.querySelector('[data-readability-input]');
const status = document.querySelector('[data-readability-status]');
const results = document.querySelector('[data-readability-results]');
const summary = document.querySelector('[data-summary]');
const metrics = document.querySelector('[data-metrics]');
const dense = document.querySelector('[data-dense]');
const longest = document.querySelector('[data-longest]');
const strip = document.querySelector('[data-density-strip]');
const counter = document.querySelector('[data-live-count]');
const sampleButton = document.querySelector('[data-readability-sample]');
const clearButton = document.querySelector('[data-readability-clear]');

const SAMPLE = `Marta dejó el café encima de la mesa y volvió al párrafo que llevaba media hora molestándola. La frase no era incorrecta. Tampoco estaba especialmente cargada. Aun así, cada vez que llegaba al final tenía que volver al principio para recordar dónde había empezado.

En la página siguiente ocurría lo contrario. Había una conversación rápida, dos interrupciones y una frase muy corta que rompía el ritmo justo cuando parecía que el personaje iba a explicarlo todo. Marta no quiso tocarla. Funcionaba así.

El tercer párrafo reunía fechas, nombres, dos incisos y una explicación técnica que había añadido durante la última revisión. Leyéndolo en voz alta encontró el problema antes de terminar. No borró la información: repartió parte en el párrafo anterior y dejó el dato importante donde estaba.`;

function escapeHTML(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}

function excerpt(text, max = 260) {
  const clean = String(text).replace(/\s+/g, ' ').trim();
  return clean.length > max ? clean.slice(0, max - 1).trimEnd() + '…' : clean;
}

function lengthBucket(words) {
  if (words < 100) return 'menos-100';
  if (words < 500) return '100-499';
  if (words < 2000) return '500-1999';
  return '2000-mas';
}

function track(words) {
  document.dispatchEvent(new CustomEvent('dp:analytics', {
    detail: { event: 'readability_analyze', target: lengthBucket(words) }
  }));
}

function updateCounter() {
  const words = wordsFrom(input?.value || '').length;
  if (counter) counter.textContent = `${words.toLocaleString('es-ES')} ${words === 1 ? 'palabra' : 'palabras'}`;
}

function metricCard(title, value, label, note, featured = false) {
  const display = value === null || value === undefined ? '—' : value;
  return `<article class="readability-metric${featured ? ' readability-metric--main' : ''}">
    <p class="readability-metric__name">${escapeHTML(title)}</p>
    <p class="readability-metric__score">${escapeHTML(display)}</p>
    <p class="readability-metric__label">${escapeHTML(label)}</p>
    <p class="readability-metric__note">${escapeHTML(note)}</p>
  </article>`;
}

function renderStrip(rows) {
  if (!strip) return;
  const usable = rows.filter((row) => row.score !== null);
  if (!usable.length) {
    strip.innerHTML = '<p class="readability-empty-note">Necesito párrafos de al menos 20 palabras para comparar la densidad entre bloques.</p>';
    return;
  }
  strip.innerHTML = usable.map((row) => {
    const density = Math.max(8, Math.min(100, 100 - row.score));
    return `<div class="density-row">
      <span class="density-row__label">Párrafo ${row.index}</span>
      <span class="density-row__track" aria-hidden="true"><span class="density-row__bar" style="--density:${density}%"></span></span>
      <span class="density-row__value">${row.score}</span>
    </div>`;
  }).join('');
}

function renderFindings(list, rows, kind) {
  if (!list) return;
  if (!rows.length) {
    list.innerHTML = '<li class="readability-empty-note">No hay una muestra suficiente para comparar.</li>';
    return;
  }
  list.innerHTML = rows.map((row) => {
    const meta = kind === 'paragraph'
      ? `Párrafo ${row.index} · ${row.words} palabras · Inflesz ${row.score} (${row.label})`
      : `Frase ${row.index} · ${row.words} palabras`;
    return `<li><p class="finding-meta">${escapeHTML(meta)}</p><p>${escapeHTML(excerpt(row.text))}</p></li>`;
  }).join('');
}

function render(data) {
  results.hidden = false;
  const denseFirst = data.densestParagraphs[0];
  let summaryText = data.reliableSample
    ? `En conjunto, Inflesz sitúa este fragmento en «${data.inflesz.label.toLowerCase()}» (${data.inflesz.score}).`
    : 'Necesito al menos 20 palabras con una frase real (con punto, exclamación o interrogación) para estimar la legibilidad.';
  if (denseFirst) summaryText += ` El párrafo ${denseFirst.index} es el bloque formalmente más denso de la muestra.`;
  const frasesLabel = data.sentenceCount === 1 ? 'frase' : 'frases';
  const parrafosLabel = data.paragraphCount === 1 ? 'párrafo' : 'párrafos';
  summary.innerHTML = `<p class="readability-summary__eyebrow">Lectura rápida</p><h2>${escapeHTML(summaryText)}</h2><p>${data.wordCount.toLocaleString('es-ES')} palabras · ${data.sentenceCount} ${frasesLabel} · ${data.paragraphCount} ${parrafosLabel} · media de ${data.avgWordsPerSentence} palabras por frase.</p>`;

  metrics.innerHTML = [
    metricCard('Inflesz', data.inflesz.score, data.inflesz.label, 'La referencia principal de esta herramienta. Describe facilidad formal; no calidad.', true),
    metricCard('Fernández-Huerta', data.fernandezHuerta.score, data.fernandezHuerta.label, 'Mostramos la variante normalizada descrita en la metodología.'),
    metricCard('Gutiérrez de Polini', data.gutierrez.score, 'Comparación interna', data.gutierrez.label),
    metricCard('Crawford', data.crawford.score, 'Nivel escolar estimado', data.crawford.label),
  ].join('');

  renderStrip(data.paragraphRows);
  renderFindings(dense, data.densestParagraphs, 'paragraph');
  renderFindings(longest, data.longestSentences, 'sentence');
  status.textContent = !data.reliableSample
    ? 'La muestra es demasiado corta o no tiene una frase real: no se calculan las fórmulas.'
    : data.wordCount < 100
    ? 'La muestra tiene menos de 100 palabras. Puedes mirar los resultados, pero compáralos con cautela.'
    : 'Análisis hecho en este navegador. El texto no se ha enviado a ningún servidor.';
  track(data.wordCount);
  results.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
}

form?.addEventListener('submit', (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) {
    status.textContent = 'Pega primero un texto. Puede ser un párrafo, una escena o un capítulo.';
    input.focus();
    return;
  }
  const data = analyzeText(text);
  if (data.empty) {
    status.textContent = 'No he encontrado palabras que pueda analizar.';
    return;
  }
  render(data);
});

sampleButton?.addEventListener('click', () => {
  input.value = SAMPLE;
  updateCounter();
  status.textContent = 'He cargado un ejemplo breve. Puedes analizarlo o sustituirlo por tu texto.';
  input.focus();
});

clearButton?.addEventListener('click', () => {
  input.value = '';
  results.hidden = true;
  summary.innerHTML = '';
  metrics.innerHTML = '';
  dense.innerHTML = '';
  longest.innerHTML = '';
  if (strip) strip.innerHTML = '';
  status.textContent = 'Nada de lo que pegues se guarda ni se envía.';
  updateCounter();
  input.focus();
});

input?.addEventListener('input', updateCounter, { passive: true });
updateCounter();
