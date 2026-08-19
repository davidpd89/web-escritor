export const SCHEMA_VERSION = 1;

export const CERTAINTY_VALUES = Object.freeze([
  'comprobado',
  'recuerdo',
  'hipotesis',
  'desconocido',
]);

const clean = (value) => String(value ?? '').replace(/\s+/g, ' ').trim();
const cleanMultiline = (value) => String(value ?? '').replace(/\r\n?/g, '\n').trim();

export function createEmptyRecord() {
  return {
    schema_version: SCHEMA_VERSION,
    exported_at: null,
    object: {
      title: '',
      type: '',
      materials: '',
      techniques: '',
      dimensions: '',
      marks: '',
      distinguishing_features: '',
      maker: '',
      date_period: '',
      current_location: '',
      condition_notes: '',
    },
    photos: [],
    owners: [],
    evidence: [],
    oral_history: [],
    timeline: [],
    open_questions: [],
    conservation: {
      observed_on: '',
      risks: '',
      changes_observed: '',
      next_steps: '',
    },
  };
}

function certainty(value) {
  const normalized = clean(value).toLowerCase();
  return CERTAINTY_VALUES.includes(normalized) ? normalized : 'desconocido';
}

function normalizePhoto(row = {}) {
  return {
    filename: clean(row.filename),
    view: clean(row.view),
    note: cleanMultiline(row.note),
  };
}

function normalizeOwner(row = {}) {
  return {
    person: clean(row.person),
    from: clean(row.from),
    to: clean(row.to),
    location: clean(row.location),
    transfer: cleanMultiline(row.transfer),
    source_ids: Array.isArray(row.source_ids) ? row.source_ids.map(clean).filter(Boolean) : [],
    certainty: certainty(row.certainty),
  };
}

function normalizeEvidence(row = {}) {
  return {
    id: clean(row.id),
    type: clean(row.type),
    description: cleanMultiline(row.description),
    location: cleanMultiline(row.location),
    checked_on: clean(row.checked_on),
  };
}

function normalizeOral(row = {}) {
  return {
    speaker: clean(row.speaker),
    interview_date: clean(row.interview_date),
    summary: cleanMultiline(row.summary),
    source_ids: Array.isArray(row.source_ids) ? row.source_ids.map(clean).filter(Boolean) : [],
    certainty: certainty(row.certainty || 'recuerdo'),
  };
}

function normalizeTimeline(row = {}) {
  return {
    from: clean(row.from),
    to: clean(row.to),
    event: cleanMultiline(row.event),
    source_ids: Array.isArray(row.source_ids) ? row.source_ids.map(clean).filter(Boolean) : [],
    certainty: certainty(row.certainty),
  };
}

const nonEmptyRow = (row) => Object.entries(row).some(([key, value]) => {
  if (key === 'certainty' && value === 'desconocido') return false;
  return Array.isArray(value) ? value.length > 0 : Boolean(value);
});

export function normalizeRecord(input = {}) {
  const base = createEmptyRecord();
  const object = input.object || {};
  const conservation = input.conservation || {};

  const result = {
    ...base,
    schema_version: SCHEMA_VERSION,
    exported_at: input.exported_at ? clean(input.exported_at) : null,
    object: {
      title: clean(object.title),
      type: clean(object.type),
      materials: clean(object.materials),
      techniques: clean(object.techniques),
      dimensions: clean(object.dimensions),
      marks: cleanMultiline(object.marks),
      distinguishing_features: cleanMultiline(object.distinguishing_features),
      maker: clean(object.maker),
      date_period: clean(object.date_period),
      current_location: clean(object.current_location),
      condition_notes: cleanMultiline(object.condition_notes),
    },
    photos: (Array.isArray(input.photos) ? input.photos : []).map(normalizePhoto).filter(nonEmptyRow),
    owners: (Array.isArray(input.owners) ? input.owners : []).map(normalizeOwner).filter(nonEmptyRow),
    evidence: (Array.isArray(input.evidence) ? input.evidence : []).map(normalizeEvidence).filter(nonEmptyRow),
    oral_history: (Array.isArray(input.oral_history) ? input.oral_history : []).map(normalizeOral).filter(nonEmptyRow),
    timeline: (Array.isArray(input.timeline) ? input.timeline : []).map(normalizeTimeline).filter(nonEmptyRow),
    open_questions: (Array.isArray(input.open_questions) ? input.open_questions : [])
      .map(cleanMultiline)
      .filter(Boolean),
    conservation: {
      observed_on: clean(conservation.observed_on),
      risks: cleanMultiline(conservation.risks),
      changes_observed: cleanMultiline(conservation.changes_observed),
      next_steps: cleanMultiline(conservation.next_steps),
    },
  };

  return result;
}

export function validateRecord(input) {
  const errors = [];
  if (!input || typeof input !== 'object' || Array.isArray(input)) {
    return ['El archivo no contiene un objeto JSON válido.'];
  }
  if (Number(input.schema_version) !== SCHEMA_VERSION) {
    errors.push(`Versión de esquema no compatible: ${input.schema_version ?? 'sin versión'}.`);
  }
  if (input.object != null && (typeof input.object !== 'object' || Array.isArray(input.object))) {
    errors.push('El bloque «object» no tiene el formato esperado.');
  }
  for (const key of ['photos', 'owners', 'evidence', 'oral_history', 'timeline', 'open_questions']) {
    if (input[key] != null && !Array.isArray(input[key])) errors.push(`«${key}» debe ser una lista.`);
  }
  return errors;
}

export function serializeRecord(input) {
  const record = normalizeRecord(input);
  record.exported_at = new Date().toISOString();
  return JSON.stringify(record, null, 2) + '\n';
}

export function parseRecord(text) {
  let parsed;
  try {
    parsed = JSON.parse(String(text));
  } catch {
    throw new Error('El archivo no contiene JSON válido.');
  }
  const errors = validateRecord(parsed);
  if (errors.length) throw new Error(errors.join(' '));
  return normalizeRecord(parsed);
}

export function suggestedFilename(record) {
  const raw = clean(record?.object?.title || 'objeto-heredado')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '') || 'objeto-heredado';
  return `${raw}-procedencia.json`;
}
