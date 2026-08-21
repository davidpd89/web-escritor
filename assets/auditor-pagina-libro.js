import { auditBookPageHtml } from './book-page-audit-rules.js';

const STATUS_LABEL = { ok: 'OK', review: 'Revisar', info: 'Info', optional: 'Opcional' };
const GROUPS = [
  ['core', 'Lo esencial para el lector'],
  ['metadata', 'Datos de la edición'],
  ['enriched', 'Contenido que puede ayudar'],
  ['structured', 'Datos estructurados'],
  ['consistency', 'Inconsistencias'],
];

function escapeHtml(v) {
  return String(v ?? '').replace(/[&<>'"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c]));
}

function renderFindingList(items) {
  if (!items.length) return '<p class="audit-empty">Sin elementos en este bloque.</p>';
  return `<ul class="audit-findings">${items.map(f => `
    <li class="audit-finding audit-finding--${f.status}">
      <span class="audit-finding__badge">${STATUS_LABEL[f.status] || escapeHtml(f.status)}</span>
      <div><strong>${escapeHtml(f.title)}</strong><p>${escapeHtml(f.detail)}</p>${f.evidence ? `<p class="audit-evidence">Evidencia: ${escapeHtml(f.evidence)}</p>` : ''}</div>
    </li>`).join('')}</ul>`;
}

function render(result, refs) {
  refs.results.hidden = false;
  const titleText = result.detectedTitle ? `Título detectado: ${result.detectedTitle}` : 'No se ha podido detectar un título.';
  refs.detected.textContent = result.url ? `${titleText} · Referencia: ${result.url}` : titleText;

  const sections = GROUPS.map(([key, label]) => {
    const items = result.findings[key] || [];
    return `<section class="audit-group"><h2>${escapeHtml(label)}</h2>${renderFindingList(items)}</section>`;
  }).join('');
  refs.groups.innerHTML = sections;

  const hasBookSchema = result.findings.structured[0]?.status === 'ok';
  const hasCover = result.findings.core.find(f => f.id === 'book_cover')?.status === 'ok';
  const ctas = [];
  if (!hasBookSchema) ctas.push('<a class="button secondary" href="/herramientas/json-ld-escritores/">Generar JSON-LD del libro →</a>');
  if (!hasCover) ctas.push('<a class="button secondary" href="/herramientas/metadatos-libro/">Revisar metadatos e imagen social →</a>');
  refs.ctas.innerHTML = ctas.join('');
  refs.ctas.hidden = ctas.length === 0;

  refs.status.textContent = 'Auditoría orientativa generada localmente. El HTML pegado no se envía ni se guarda.';
}

export function init() {
  const form = document.querySelector('[data-book-audit-form]');
  if (!form) return;

  const refs = {
    html: form.querySelector('[data-book-audit-html]'),
    url: form.querySelector('[data-book-audit-url]'),
    title: form.querySelector('[data-book-audit-title]'),
    status: document.querySelector('[data-book-audit-status]'),
    results: document.querySelector('[data-book-audit-results]'),
    detected: document.querySelector('[data-book-audit-detected]'),
    groups: document.querySelector('[data-book-audit-groups]'),
    ctas: document.querySelector('[data-book-audit-ctas]'),
  };

  form.addEventListener('submit', event => {
    event.preventDefault();
    const html = refs.html.value;
    if (!html.trim()) {
      refs.results.hidden = true;
      refs.status.textContent = 'Pega el código HTML de la página del libro.';
      return;
    }
    const result = auditBookPageHtml(html, {
      url: refs.url.value.trim(),
      expectedTitle: refs.title.value.trim(),
    });
    render(result, refs);
  });

  form.querySelector('[data-book-audit-clear]')?.addEventListener('click', () => {
    form.reset();
    refs.results.hidden = true;
    refs.status.textContent = 'Nada de lo que pegues se envía al servidor.';
  });

  const processor = document.querySelector('[data-publishing-processor]');
  if (processor) {
    processor.inert = false;
    processor.removeAttribute('inert');
    processor.removeAttribute('aria-disabled');
  }
}

if (typeof document !== 'undefined') init();
