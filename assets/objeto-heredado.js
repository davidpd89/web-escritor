import {
  CERTAINTY_VALUES,
  createEmptyRecord,
  normalizeRecord,
  parseRecord,
  serializeRecord,
  suggestedFilename,
} from './objeto-heredado-core.js';

const root = document.querySelector('[data-object-record]');
if (!root) throw new Error('Falta [data-object-record].');

const $ = (selector, scope = root) => scope.querySelector(selector);
const $$ = (selector, scope = root) => [...scope.querySelectorAll(selector)];
const status = $('[data-record-status]');
const fileInput = $('[data-record-import]');
const form = $('form');

const certaintyOptions = CERTAINTY_VALUES.map((value) =>
  `<option value="${value}">${({comprobado:'Comprobado',recuerdo:'Recuerdo oral',hipotesis:'Hipótesis',desconocido:'Desconocido'})[value]}</option>`
).join('');

const templates = {
  photos: () => `<div class="record-row" data-row>
    <input aria-label="Nombre de archivo" data-key="filename" placeholder="IMG_1234.jpg">
    <input aria-label="Vista fotografiada" data-key="view" placeholder="Frente, reverso, marca…">
    <input aria-label="Nota de la fotografía" data-key="note" placeholder="Detalle relevante">
    <button type="button" class="record-remove" data-remove aria-label="Eliminar fotografía">×</button>
  </div>`,
  owners: () => `<div class="record-row record-row--owners" data-row>
    <input aria-label="Propietario" data-key="person" placeholder="Persona">
    <input aria-label="Desde" data-key="from" placeholder="Desde / aprox.">
    <input aria-label="Hasta" data-key="to" placeholder="Hasta / aprox.">
    <input aria-label="Lugar" data-key="location" placeholder="Lugar">
    <input aria-label="Cómo llegó o salió" data-key="transfer" placeholder="Herencia, compra, regalo…">
    <select aria-label="Certeza" data-key="certainty">${certaintyOptions}</select>
    <input aria-label="IDs de fuentes" data-key="source_ids" placeholder="F01, F03">
    <button type="button" class="record-remove" data-remove aria-label="Eliminar propietario">×</button>
  </div>`,
  evidence: () => `<div class="record-row record-row--evidence" data-row>
    <input aria-label="Identificador de fuente" data-key="id" placeholder="F01">
    <input aria-label="Tipo de fuente" data-key="type" placeholder="Foto, carta, marca, entrevista…">
    <input aria-label="Descripción" data-key="description" placeholder="Qué demuestra o aporta">
    <input aria-label="Ubicación de la fuente" data-key="location" placeholder="Caja, carpeta, URL, archivo…">
    <input aria-label="Fecha de comprobación" data-key="checked_on" type="date">
    <button type="button" class="record-remove" data-remove aria-label="Eliminar fuente">×</button>
  </div>`,
  oral_history: () => `<div class="record-row record-row--oral" data-row>
    <input aria-label="Persona entrevistada" data-key="speaker" placeholder="Persona">
    <input aria-label="Fecha de entrevista" data-key="interview_date" type="date">
    <textarea aria-label="Resumen o cita" data-key="summary" rows="2" placeholder="Qué recuerda; conserva las dudas y contradicciones"></textarea>
    <input aria-label="IDs de fuentes" data-key="source_ids" placeholder="F02">
    <select aria-label="Certeza" data-key="certainty">${certaintyOptions}</select>
    <button type="button" class="record-remove" data-remove aria-label="Eliminar recuerdo">×</button>
  </div>`,
  timeline: () => `<div class="record-row record-row--timeline" data-row>
    <input aria-label="Fecha inicial" data-key="from" placeholder="Desde / aprox.">
    <input aria-label="Fecha final" data-key="to" placeholder="Hasta / aprox.">
    <textarea aria-label="Hecho" data-key="event" rows="2" placeholder="Qué ocurrió"></textarea>
    <input aria-label="IDs de fuentes" data-key="source_ids" placeholder="F01, F02">
    <select aria-label="Certeza" data-key="certainty">${certaintyOptions}</select>
    <button type="button" class="record-remove" data-remove aria-label="Eliminar hecho">×</button>
  </div>`,
};

function announce(message) {
  if (status) status.textContent = message;
}

function addRow(kind, data = {}) {
  const container = $(`[data-rows="${kind}"]`);
  if (!container || !templates[kind]) return;
  container.insertAdjacentHTML('beforeend', templates[kind]());
  const row = container.lastElementChild;
  Object.entries(data).forEach(([key, value]) => {
    const field = $(`[data-key="${CSS.escape(key)}"]`, row);
    if (!field) return;
    field.value = Array.isArray(value) ? value.join(', ') : value ?? '';
  });
}

function collectRows(kind) {
  return $$(`[data-rows="${kind}"] [data-row]`).map((row) => {
    const out = {};
    $$('[data-key]', row).forEach((field) => {
      const key = field.dataset.key;
      const value = field.value;
      out[key] = key === 'source_ids'
        ? value.split(',').map((item) => item.trim()).filter(Boolean)
        : value;
    });
    return out;
  });
}

function collect() {
  const record = createEmptyRecord();
  $$('[data-object-field]').forEach((field) => { record.object[field.dataset.objectField] = field.value; });
  $$('[data-conservation-field]').forEach((field) => { record.conservation[field.dataset.conservationField] = field.value; });
  for (const kind of Object.keys(templates)) record[kind] = collectRows(kind);
  record.open_questions = $('[data-open-questions]').value.split('\n').map((x) => x.trim()).filter(Boolean);
  return normalizeRecord(record);
}

function hydrate(record) {
  form.reset();
  $$('[data-rows]').forEach((node) => { node.innerHTML = ''; });
  $$('[data-object-field]').forEach((field) => { field.value = record.object[field.dataset.objectField] || ''; });
  $$('[data-conservation-field]').forEach((field) => { field.value = record.conservation[field.dataset.conservationField] || ''; });
  $('[data-open-questions]').value = record.open_questions.join('\n');
  for (const kind of Object.keys(templates)) {
    const rows = record[kind] || [];
    rows.forEach((row) => addRow(kind, row));
  }
}

function downloadJson() {
  const record = collect();
  const blob = new Blob([serializeRecord(record)], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = suggestedFilename(record);
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  announce('Archivo JSON descargado. Guárdalo para continuar otro día.');
  window.dispatchEvent(new CustomEvent('dp:analytics', { detail: { event: 'object_record_export' } }));
}

root.addEventListener('click', (event) => {
  const add = event.target.closest('[data-add-row]');
  if (add) { addRow(add.dataset.addRow); return; }
  const remove = event.target.closest('[data-remove]');
  if (remove) remove.closest('[data-row]')?.remove();
});

$('[data-record-export]').addEventListener('click', downloadJson);
$('[data-record-print]').addEventListener('click', () => {
  window.print();
  window.dispatchEvent(new CustomEvent('dp:analytics', { detail: { event: 'object_record_print' } }));
});
$('[data-record-clear]').addEventListener('click', () => {
  hydrate(createEmptyRecord());
  announce('Ficha vaciada. No se ha enviado ni borrado ningún archivo de tu dispositivo.');
});
$('[data-record-open]').addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', async () => {
  const file = fileInput.files?.[0];
  if (!file) return;
  try {
    const record = parseRecord(await file.text());
    hydrate(record);
    announce(`Archivo «${file.name}» cargado.`);
    window.dispatchEvent(new CustomEvent('dp:analytics', { detail: { event: 'object_record_import' } }));
  } catch (error) {
    announce(`No se pudo abrir: ${error.message}`);
  } finally {
    fileInput.value = '';
  }
});

for (const kind of Object.keys(templates)) addRow(kind);
announce('Todo lo que escribas se mantiene en esta página hasta que cierres o recargues. Descarga el JSON para conservarlo.');
