import { analyzeLexicalDiversity, tokenizeSpanish } from './variedad-lexica-engine.js';

const form = document.querySelector('[data-lexical-form]');
const input = document.querySelector('[data-lexical-input]');
const status = document.querySelector('[data-lexical-status]');
const counter = document.querySelector('[data-lexical-count]');
const results = document.querySelector('[data-lexical-results]');
const summary = document.querySelector('[data-lexical-summary]');
const metrics = document.querySelector('[data-lexical-metrics]');
const profile = document.querySelector('[data-lexical-profile]');
const profileNote = document.querySelector('[data-lexical-profile-note]');
const sampleButton = document.querySelector('[data-lexical-sample]');
const clearButton = document.querySelector('[data-lexical-clear]');

// 144 palabras: por debajo de 100 no se puede mostrar MATTR-100, y el propio
// botón "Cargar ejemplo" existe para que un visitante vea la herramienta
// funcionar sin tener que pegar su propio texto primero. La frase anterior
// tenía solo 14 palabras — por debajo incluso del mínimo de 20 que exige el
// propio análisis — así que pulsar el ejemplo y luego "Analizar" no mostraba
// ningún resultado, solo el aviso de "pega al menos 20 palabras".
const SAMPLE = `Marta releyó el capítulo entero antes de tocar nada. El primer párrafo repetía «puerta» tres veces en dos frases; lo dejó así porque la puerta era el objeto de la escena, no un descuido. El segundo párrafo era distinto: ahí había usado «mirar», «observar», «contemplar» y «fijarse» casi seguidos, y ese exceso de sinónimos sonaba más a diccionario que a una mujer cansada entrando en su propia casa.

Cambió tres verbos y dejó uno repetido. La variedad no era el objetivo; el ritmo sí. Un texto que evita toda repetición puede acabar sonando artificial, como si alguien hubiera pasado un tesauro por encima sin escuchar cómo sonaba en voz alta.

Cerró el capítulo, abrió el siguiente y encontró justo el problema contrario: cuarenta líneas sin una sola palabra que se repitiera, ninguna respiración, ninguna vuelta. Ahí sí hacía falta bajar el vocabulario, no subirlo.`;

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[char]));
}

function fmtRatio(value, digits = 3) {
  return Number.isFinite(value) ? value.toLocaleString('es-ES', { minimumFractionDigits: digits, maximumFractionDigits: digits }) : '—';
}

function fmtNumber(value, digits = 1) {
  return Number.isFinite(value) ? value.toLocaleString('es-ES', { minimumFractionDigits: digits, maximumFractionDigits: digits }) : '—';
}

function wordBucket(count) {
  if (count < 100) return 'lt100';
  if (count < 500) return '100_499';
  if (count < 2000) return '500_1999';
  if (count < 10000) return '2000_9999';
  return 'gte10000';
}

function track() { /* analytics disabled for privacy */ }

function updateCounter() {
  if (!counter || !input) return;
  const count = tokenizeSpanish(input.value).length;
  counter.textContent = `${count.toLocaleString('es-ES')} ${count === 1 ? 'palabra' : 'palabras'}`;
}

function metricCard(name, value, note, featured = false) {
  return `<article class="lexical-metric${featured ? ' lexical-metric--main' : ''}">
    <p class="lexical-metric__name">${escapeHTML(name)}</p>
    <p class="lexical-metric__value">${escapeHTML(value)}</p>
    <p class="lexical-metric__note">${escapeHTML(note)}</p>
  </article>`;
}

function renderProfile(rows) {
  if (!profile || !profileNote) return;

  if (rows.length < 2) {
    profile.innerHTML = '';
    profileNote.textContent = 'Para comparar tramos internos hacen falta al menos dos bloques de 50 palabras; con unos 400 términos la vista empieza a ser especialmente útil.';
    return;
  }

  const values = rows.map(row => row.mattr).filter(Number.isFinite);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const spread = max - min;
  profileNote.textContent = `En esta muestra, MATTR-50 varía ${fmtRatio(spread)} entre el tramo más bajo y el más alto.`;

  profile.innerHTML = rows.map(row => {
    const width = spread > 0 ? 28 + ((row.mattr - min) / spread) * 72 : 64;
    return `<div class="lexical-profile-row">
      <span class="lexical-profile-row__label">${row.startWord.toLocaleString('es-ES')}–${row.endWord.toLocaleString('es-ES')}</span>
      <span class="lexical-profile-row__track" aria-hidden="true"><span class="lexical-profile-row__bar" style="--lexical-width:${width.toFixed(1)}%"></span></span>
      <span class="lexical-profile-row__value">${fmtRatio(row.mattr)}</span>
    </div>`;
  }).join('');
}

function render(analysis) {
  if (!results || !summary || !metrics) return;

  const shortWarning = analysis.sampleShort
    ? 'La muestra es corta. TTR cambia mucho con la longitud y las métricas estabilizadas ganan sentido al comparar textos de tamaño suficiente.'
    : 'Compara las métricas entre versiones o tramos del mismo proyecto. No existe un valor universal que defina una prosa «mejor».';

  summary.innerHTML = `<p class="lexical-summary__eyebrow">Lectura descriptiva</p>
    <h2>${analysis.tokenCount.toLocaleString('es-ES')} palabras · ${analysis.typeCount.toLocaleString('es-ES')} formas distintas</h2>
    <p>${escapeHTML(shortWarning)}</p>`;

  metrics.innerHTML = [
    metricCard('TTR', fmtRatio(analysis.ttr), 'Formas distintas / palabras. Útil como dato bruto, muy sensible a la longitud.'),
    metricCard('MATTR-50', fmtRatio(analysis.mattr50), analysis.mattr50 === null ? 'Necesita al menos 50 palabras.' : 'Media de TTR en ventanas móviles de 50 palabras.', true),
    metricCard('MATTR-100', fmtRatio(analysis.mattr100), analysis.mattr100 === null ? 'Necesita al menos 100 palabras.' : 'Misma idea con una ventana mayor: el valor puede cambiar.'),
    metricCard('MTLD', fmtNumber(analysis.mtld, 1), analysis.mtld === null ? 'No estimable con esta muestra.' : 'Longitud media de factores hasta un umbral TTR de 0,72, calculada en ambos sentidos.'),
    metricCard('Formas únicas una vez', analysis.hapaxCount.toLocaleString('es-ES'), `${fmtRatio(analysis.hapaxShareOfTypes)} de las formas distintas aparecen una sola vez.`)
  ].join('');

  renderProfile(analysis.profile);
  results.hidden = false;
}

if (form && input) {
  input.addEventListener('input', updateCounter, { passive: true });

  form.addEventListener('submit', event => {
    event.preventDefault();
    const analysis = analyzeLexicalDiversity(input.value);

    if (analysis.tokenCount < 20) {
      status.textContent = 'Pega al menos 20 palabras para obtener una lectura mínimamente útil.';
      results.hidden = true;
      return;
    }

    render(analysis);
    status.textContent = analysis.tokenCount < 50
      ? 'He calculado las estadísticas básicas. MATTR-50 y MTLD necesitan una muestra mayor.'
      : 'Análisis terminado en este dispositivo. El texto no se ha enviado a ningún servidor.';
    track('lexical_diversity_analyze', analysis.tokenCount);
    results.scrollIntoView({ block: 'start', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  });

  sampleButton?.addEventListener('click', () => {
    input.value = SAMPLE;
    updateCounter();
    status.textContent = 'Ejemplo cargado. Puedes analizarlo o sustituirlo por tu texto.';
    track('lexical_diversity_sample', tokenizeSpanish(SAMPLE).length);
    input.focus();
  });

  clearButton?.addEventListener('click', () => {
    const previousCount = tokenizeSpanish(input.value).length;
    input.value = '';
    updateCounter();
    results.hidden = true;
    summary.innerHTML = '';
    metrics.innerHTML = '';
    if (profile) profile.innerHTML = '';
    if (profileNote) profileNote.textContent = '';
    status.textContent = 'Campo vacío. Nada de lo que pegues se guarda ni se envía.';
    track('lexical_diversity_clear', previousCount);
    input.focus();
  });

  updateCounter();
}
