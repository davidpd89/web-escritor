const RELATION_TYPES = new Set(['familia', 'amistad', 'romance', 'rivalidad', 'alianza', 'mentoria', 'secreto', 'otro']);

export function slugify(value) {
  return String(value || '')
    .normalize('NFD')
     .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'personaje';
}

export function normalizeProject(input = {}) {
  const seen = new Set();
  const characters = [];
  for (const raw of Array.isArray(input.characters) ? input.characters : []) {
    const name = String(raw?.name || '').trim();
    if (!name) continue;
    let id = String(raw?.id || slugify(name)).trim();
    const base = id;
    let i = 2;
    while (seen.has(id)) id = `${base}-${i++}`;
    seen.add(id);
    characters.push({ id, name, note: String(raw?.note || '').trim() });
  }

  const valid = new Set(characters.map(c => c.id));
  const relations = [];
  const edgeKeys = new Set();
  for (const raw of Array.isArray(input.relations) ? input.relations : []) {
    const from = String(raw?.from || '');
    const to = String(raw?.to || '');
    if (!valid.has(from) || !valid.has(to) || from === to) continue;
    const type = RELATION_TYPES.has(raw?.type) ? raw.type : 'otro';
    const label = String(raw?.label || '').trim().slice(0, 80);
    const evolution = String(raw?.evolution || '').trim().slice(0, 240);
    const directed = Boolean(raw?.directed);
    const key = directed ? `${from}>${to}|${type}|${label}` : `${[from, to].sort().join('~')}|${type}|${label}`;
    if (edgeKeys.has(key)) continue;
    edgeKeys.add(key);
    relations.push({ id: `r-${relations.length + 1}`, from, to, type, label, evolution, directed });
  }
  return { version: 1, title: String(input.title || '').trim().slice(0, 100), characters, relations };
}

export function circularLayout(characters, width = 900, height = 600, focusId = '') {
  const nodes = characters.map(c => ({ ...c }));
  if (!nodes.length) return [];
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.max(90, Math.min(width, height) * 0.34);
  if (focusId && nodes.some(n => n.id === focusId)) {
    const focus = nodes.find(n => n.id === focusId);
    focus.x = cx;
    focus.y = cy;
    const others = nodes.filter(n => n.id !== focusId);
    others.forEach((n, i) => {
      const angle = -Math.PI / 2 + (i * Math.PI * 2) / Math.max(1, others.length);
      n.x = cx + Math.cos(angle) * radius;
      n.y = cy + Math.sin(angle) * radius;
    });
    return nodes;
  }
  nodes.forEach((n, i) => {
    const angle = -Math.PI / 2 + (i * Math.PI * 2) / nodes.length;
    n.x = cx + Math.cos(angle) * radius;
    n.y = cy + Math.sin(angle) * radius;
  });
  return nodes;
}

export function visibleGraph(project, { focusId = '', types = null } = {}) {
  const normalized = normalizeProject(project);
  const enabled = types == null ? null : new Set(types);
  let relations = normalized.relations.filter(r => !enabled || enabled.has(r.type));
  let ids = new Set(normalized.characters.map(c => c.id));
  if (focusId) {
    relations = relations.filter(r => r.from === focusId || r.to === focusId);
    ids = new Set([focusId, ...relations.flatMap(r => [r.from, r.to])]);
  }
  return {
    ...normalized,
    characters: normalized.characters.filter(c => ids.has(c.id)),
    relations,
  };
}

export function relationshipSummary(project) {
  const p = normalizeProject(project);
  const degrees = new Map(p.characters.map(c => [c.id, 0]));
  const types = new Map();
  for (const r of p.relations) {
    degrees.set(r.from, (degrees.get(r.from) || 0) + 1);
    degrees.set(r.to, (degrees.get(r.to) || 0) + 1);
    types.set(r.type, (types.get(r.type) || 0) + 1);
  }
  const mostConnected = [...degrees.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([id, count]) => ({ character: p.characters.find(c => c.id === id)?.name || id, count }));
  return { characters: p.characters.length, relations: p.relations.length, mostConnected, byType: Object.fromEntries(types) };
}

export function serializeProject(project) {
  return JSON.stringify(normalizeProject(project), null, 2);
}

export const PROJECT_VERSION = 1;

// Error de importación con un motivo legible para anunciarlo tal cual.
export class ProjectImportError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ProjectImportError';
  }
}

const isPlainObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const isOptionalString = value => value === undefined || typeof value === 'string';

// Valida un fichero externo contra el contrato v1 antes de tocar el estado.
// normalizeProject() es tolerante para el estado interno; aquí cualquier dato
// que se descartaría o recortaría en silencio provoca rechazo.
export function validateProject(input) {
  const fail = message => { throw new ProjectImportError(message); };
  if (!isPlainObject(input)) fail('El archivo no es un mapa de personajes.');
  if (input.version !== undefined && input.version !== PROJECT_VERSION) {
    fail(`Versión de mapa no admitida: ${String(input.version).slice(0, 20)}.`);
  }
  if (!Array.isArray(input.characters)) fail('El archivo no es un mapa de personajes: falta la lista de personajes.');
  if (input.relations !== undefined && !Array.isArray(input.relations)) fail('La lista de relaciones no es válida.');
  if (!isOptionalString(input.title)) fail('El título del mapa no es texto.');
  if ((input.title || '').trim().length > 100) fail('El título del mapa supera 100 caracteres.');

  const ids = new Set();
  input.characters.forEach((raw, index) => {
    const n = index + 1;
    if (!isPlainObject(raw)) fail(`El personaje ${n} no es válido.`);
    if (typeof raw.name !== 'string' || !raw.name.trim()) fail(`El personaje ${n} no tiene nombre.`);
    if (!isOptionalString(raw.id) || !isOptionalString(raw.note)) fail(`El personaje ${n} tiene campos que no son texto.`);
    const id = (raw.id || slugify(raw.name)).trim();
    if (ids.has(id)) fail(`Identificador de personaje repetido: ${id.slice(0, 40)}.`);
    ids.add(id);
  });

  const edgeKeys = new Set();
  (input.relations || []).forEach((raw, index) => {
    const n = index + 1;
    if (!isPlainObject(raw)) fail(`La relación ${n} no es válida.`);
    if (typeof raw.from !== 'string' || typeof raw.to !== 'string') fail(`La relación ${n} no indica sus personajes.`);
    if (!ids.has(raw.from) || !ids.has(raw.to)) fail(`La relación ${n} apunta a un personaje que no existe.`);
    if (raw.from === raw.to) fail(`La relación ${n} une a un personaje consigo mismo.`);
    if (raw.type !== undefined && !RELATION_TYPES.has(raw.type)) fail(`La relación ${n} tiene un tipo desconocido.`);
    if (!isOptionalString(raw.label) || !isOptionalString(raw.evolution)) fail(`La relación ${n} tiene campos que no son texto.`);
    if ((raw.label || '').trim().length > 80) fail(`La etiqueta de la relación ${n} supera 80 caracteres.`);
    if ((raw.evolution || '').trim().length > 240) fail(`La evolución de la relación ${n} supera 240 caracteres.`);
    if (raw.directed !== undefined && typeof raw.directed !== 'boolean') fail(`La relación ${n} tiene una dirección no válida.`);
    const type = raw.type || 'otro';
    const label = (raw.label || '').trim();
    const key = raw.directed ? `${raw.from}>${raw.to}|${type}|${label}` : `${[raw.from, raw.to].sort().join('~')}|${type}|${label}`;
    if (edgeKeys.has(key)) fail(`La relación ${n} está repetida.`);
    edgeKeys.add(key);
  });

  const project = normalizeProject(input);
  // Red de seguridad: la normalización no puede perder nada de lo validado.
  if (project.characters.length !== input.characters.length || project.relations.length !== (input.relations || []).length) {
    fail('El archivo contiene datos que no se pueden conservar.');
  }
  return project;
}

export function parseProject(text) {
  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new ProjectImportError('El archivo no es un JSON válido.');
  }
  return validateProject(parsed);
}
