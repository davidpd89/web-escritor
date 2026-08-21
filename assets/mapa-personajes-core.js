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

export function parseProject(text) {
  const parsed = JSON.parse(text);
  return normalizeProject(parsed);
}
