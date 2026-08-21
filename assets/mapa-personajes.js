import {
  normalizeProject,
  circularLayout,
  visibleGraph,
  relationshipSummary,
  serializeProject,
  parseProject,
  slugify,
} from './mapa-personajes-core.js';

const $ = sel => document.querySelector(sel);
const root = $('[data-character-map]');

const els = {
  title: $('#map-title'),
  characterName: $('#character-name'),
  addCharacter: $('#add-character'),
  characterError: $('[data-character-error]'),
  from: $('#relation-from'),
  to: $('#relation-to'),
  type: $('#relation-type'),
  label: $('#relation-label'),
  evolution: $('#relation-evolution'),
  directed: $('#relation-directed'),
  addRelation: $('#add-relation'),
  relationError: $('[data-relation-error]'),
  focus: $('#map-focus'),
  filters: document.querySelectorAll('[data-relation-filter]'),
  svg: $('#character-map'),
  empty: $('#map-empty'),
  stats: $('#map-stats'),
  list: $('#relation-list'),
  exportJson: $('#export-json'),
  importJson: $('#import-json'),
  file: $('#import-file'),
  exportSvg: $('#export-svg'),
  clear: $('#clear-map'),
  status: $('#map-status'),
};

let project = normalizeProject({ title: '', characters: [], relations: [] });
let positions = new Map();
let dragState = null;

function announce(message) {
  els.status.textContent = message;
}

function analytics(event, target = '') {
  document.dispatchEvent(new CustomEvent('dp:analytics', { detail: { event, target } }));
}

function equivalentName(value) {
  return String(value || '')
    .normalize('NFKC')
    .trim()
    .replace(/\s+/g, ' ')
    .toLocaleLowerCase('es');
}

function setCharacterError(message = '') {
  els.characterError.textContent = message;
  els.characterName.setAttribute('aria-invalid', message ? 'true' : 'false');
}

function setRelationError(message = '') {
  els.relationError.textContent = message;
  [els.from, els.to].forEach(el => el.setAttribute('aria-invalid', message ? 'true' : 'false'));
}

function addCharacter(name) {
  name = String(name || '').trim().replace(/\s+/g, ' ');
  if (!name) {
    setCharacterError('Escribe un nombre antes de añadir el personaje.');
    announce('No se ha añadido ningún personaje.');
    return false;
  }
  if (project.characters.some(c => equivalentName(c.name) === equivalentName(name))) {
    setCharacterError('Ese personaje ya está en el mapa.');
    announce('No se ha añadido el duplicado.');
    return false;
  }

  setCharacterError();
  const base = slugify(name);
  let id = base;
  let i = 2;
  while (project.characters.some(c => c.id === id)) id = `${base}-${i++}`;

  project.characters.push({ id, name, note: '' });
  render(true);
  announce(`Personaje añadido: ${name}`);
  return true;
}

function addRelation() {
  const from = els.from.value;
  const to = els.to.value;
  if (!from || !to || from === to) {
    setRelationError('Selecciona dos personajes distintos.');
    announce('No se ha añadido la relación.');
    return false;
  }

  const candidate = normalizeProject({
    ...project,
    relations: [
      ...project.relations,
      {
        from,
        to,
        type: els.type.value,
        label: els.label.value.trim(),
        evolution: els.evolution.value.trim(),
        directed: els.directed.checked,
      },
    ],
  });

  if (candidate.relations.length === project.relations.length) {
    setRelationError('Esa relación ya está declarada con el mismo tipo y etiqueta.');
    announce('No se ha añadido la relación duplicada.');
    return false;
  }

  setRelationError();
  project = candidate;
  els.label.value = '';
  els.evolution.value = '';
  render(false);
  announce('Relación añadida.');
  return true;
}

function selectOptions() {
  const options = project.characters
    .map(c => `<option value="${escapeHtml(c.id)}">${escapeHtml(c.name)}</option>`)
    .join('');
  const previous = [els.from.value, els.to.value, els.focus.value];

  els.from.innerHTML = '<option value="">Selecciona…</option>' + options;
  els.to.innerHTML = '<option value="">Selecciona…</option>' + options;
  els.focus.innerHTML = '<option value="">Todos los personajes</option>' + options;

  if (project.characters.some(c => c.id === previous[0])) els.from.value = previous[0];
  if (project.characters.some(c => c.id === previous[1])) els.to.value = previous[1];
  if (project.characters.some(c => c.id === previous[2])) els.focus.value = previous[2];
}

function escapeHtml(value) {
  return String(value).replace(/[&<>\'\"]/g, ch => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;',
  }[ch]));
}

function activeTypes() {
  return [...els.filters].filter(el => el.checked).map(el => el.value);
}

function updatePrimaryAction() {
  const readyForRelations = project.characters.length >= 2;
  els.addRelation.disabled = !readyForRelations;
  els.addCharacter.className = readyForRelations ? 'text-action' : 'primary-action';
  els.addRelation.className = readyForRelations ? 'primary-action' : 'text-action';
  root.dataset.state = project.relations.length
    ? 'result'
    : project.characters.length
      ? 'valid'
      : 'initial';
}

function setEdgeGeometry(edge) {
  const a = positions.get(edge.dataset.from);
  const b = positions.get(edge.dataset.to);
  if (!a || !b) return;

  const line = edge.querySelector('line');
  const label = edge.querySelector('text');
  if (line) {
    line.setAttribute('x1', a.x);
    line.setAttribute('y1', a.y);
    line.setAttribute('x2', b.x);
    line.setAttribute('y2', b.y);
  }
  if (label) {
    label.setAttribute('x', (a.x + b.x) / 2);
    label.setAttribute('y', (a.y + b.y) / 2 - 8);
  }
}

function moveNode(node, id, x, y) {
  const clamped = {
    x: Math.max(48, Math.min(852, x)),
    y: Math.max(48, Math.min(532, y)),
  };
  positions.set(id, clamped);
  node.setAttribute('transform', `translate(${clamped.x} ${clamped.y})`);
  els.svg.querySelectorAll('.map-edge').forEach(edge => {
    if (edge.dataset.from === id || edge.dataset.to === id) setEdgeGeometry(edge);
  });
}

function pointFromPointer(event) {
  const matrix = els.svg.getScreenCTM();
  if (!matrix) return null;
  const point = els.svg.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  return point.matrixTransform(matrix.inverse());
}

function stopDragging(pointerId = null) {
  if (!dragState || (pointerId !== null && pointerId !== dragState.pointerId)) return;
  dragState.node.classList.remove('is-dragging');
  dragState = null;
}

function render(resetPositions = false) {
  stopDragging();
  project.title = els.title.value.trim();
  selectOptions();
  updatePrimaryAction();

  const graph = visibleGraph(project, { focusId: els.focus.value, types: activeTypes() });
  const width = 900;
  const height = 580;
  const fresh = circularLayout(graph.characters, width, height, els.focus.value);

  if (resetPositions) positions.clear();
  for (const node of fresh) {
    if (!positions.has(node.id) || els.focus.value) positions.set(node.id, { x: node.x, y: node.y });
  }

  const byId = new Map(
    graph.characters.map(c => [c.id, { ...c, ...(positions.get(c.id) || {}) }]),
  );

  els.svg.innerHTML = '';
  els.svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  els.empty.hidden = graph.characters.length > 0;

  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  defs.innerHTML = '<marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" /></marker>';
  els.svg.appendChild(defs);

  for (const rel of graph.relations) {
    const a = byId.get(rel.from);
    const b = byId.get(rel.to);
    if (!a || !b) continue;

    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.classList.add('map-edge', `type-${rel.type}`);
    g.dataset.from = rel.from;
    g.dataset.to = rel.to;

    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    if (rel.directed) line.setAttribute('marker-end', 'url(#arrow)');
    g.appendChild(line);

    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.textContent = rel.label || rel.type;
    g.appendChild(label);

    els.svg.appendChild(g);
    setEdgeGeometry(g);
  }

  for (const c of graph.characters) {
    const pos = byId.get(c.id);
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.classList.add('map-node');
    g.dataset.id = c.id;
    g.setAttribute('transform', `translate(${pos.x} ${pos.y})`);

    const visualName = c.name.length > 20 ? `${c.name.slice(0, 19)}…` : c.name;
    g.innerHTML = `<title>${escapeHtml(c.name)}</title><circle r="42"></circle><text text-anchor="middle" dy="4">${escapeHtml(visualName)}</text>`;
    makeDraggable(g, c.id);
    els.svg.appendChild(g);
  }

  const total = relationshipSummary(project);
  const visible = relationshipSummary(graph);
  const filtered = total.characters !== visible.characters || total.relations !== visible.relations;
  if (filtered) {
    els.stats.innerHTML = `<strong>${visible.characters}</strong> personajes visibles · <strong>${visible.relations}</strong> relaciones visibles · total: <strong>${total.characters}</strong> personajes · <strong>${total.relations}</strong> relaciones`;
  } else {
    els.stats.innerHTML = `<strong>${total.characters}</strong> personajes · <strong>${total.relations}</strong> relaciones` +
      (total.mostConnected[0]
        ? ` · más conectado: <strong>${escapeHtml(total.mostConnected[0].character)}</strong> (${total.mostConnected[0].count})`
        : '');
  }

  els.list.innerHTML = project.relations.map((r, i) => {
    const a = project.characters.find(c => c.id === r.from)?.name || r.from;
    const b = project.characters.find(c => c.id === r.to)?.name || r.to;
    return `<li><span><strong>${escapeHtml(a)}</strong> ${r.directed ? '→' : '—'} <strong>${escapeHtml(b)}</strong> · ${escapeHtml(r.label || r.type)}${r.evolution ? `<small>${escapeHtml(r.evolution)}</small>` : ''}</span><button type="button" data-remove-relation="${i}" aria-label="Eliminar relación ${escapeHtml(a)} y ${escapeHtml(b)}">×</button></li>`;
  }).join('');
}

function makeDraggable(node, id) {
  node.addEventListener('pointerdown', event => {
    if (event.button !== 0 || !event.isPrimary) return;
    stopDragging();
    dragState = { node, id, pointerId: event.pointerId };
    node.classList.add('is-dragging');
    event.preventDefault();
  });
}

window.addEventListener('pointermove', event => {
  if (!dragState || event.pointerId !== dragState.pointerId) return;
  const point = pointFromPointer(event);
  if (!point) return;
  moveNode(dragState.node, dragState.id, point.x, point.y);
  event.preventDefault();
});
window.addEventListener('pointerup', event => stopDragging(event.pointerId));
window.addEventListener('pointercancel', event => stopDragging(event.pointerId));
window.addEventListener('blur', () => stopDragging());

function download(name, type, text) {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

els.addCharacter.addEventListener('click', () => {
  if (addCharacter(els.characterName.value)) {
    els.characterName.value = '';
    analytics('character_map_add_character');
  }
});
els.characterName.addEventListener('input', () => setCharacterError());
els.characterName.addEventListener('keydown', event => {
  if (event.key === 'Enter') {
    event.preventDefault();
    els.addCharacter.click();
  }
});
els.addRelation.addEventListener('click', () => {
  if (addRelation()) analytics('character_map_add_relation');
});
[els.from, els.to].forEach(el => el.addEventListener('change', () => setRelationError()));
els.focus.addEventListener('change', () => {
  positions.clear();
  render(true);
  analytics('character_map_focus', els.focus.value ? 'single' : 'all');
});
els.filters.forEach(el => el.addEventListener('change', () => render(false)));
els.title.addEventListener('input', () => {
  project.title = els.title.value.trim();
});
els.list.addEventListener('click', event => {
  const btn = event.target.closest('[data-remove-relation]');
  if (!btn) return;
  project.relations.splice(Number(btn.dataset.removeRelation), 1);
  project = normalizeProject(project);
  setRelationError();
  render(false);
  announce('Relación eliminada.');
});
els.exportJson.addEventListener('click', () => {
  download('mapa-personajes.json', 'application/json', serializeProject(project));
  analytics('character_map_export', 'json');
});
els.exportSvg.addEventListener('click', () => {
  const clone = els.svg.cloneNode(true);
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  download('mapa-personajes.svg', 'image/svg+xml', new XMLSerializer().serializeToString(clone));
  analytics('character_map_export', 'svg');
});
els.importJson.addEventListener('click', () => els.file.click());
els.file.addEventListener('change', async () => {
  const file = els.file.files?.[0];
  if (!file) return;
  try {
    project = parseProject(await file.text());
    els.title.value = project.title;
    positions.clear();
    setCharacterError();
    setRelationError();
    render(true);
    announce('Mapa importado.');
    analytics('character_map_import');
  } catch {
    announce('No se ha podido leer ese JSON.');
    root.dataset.state = 'error';
  }
  els.file.value = '';
});
els.clear.addEventListener('click', () => {
  project = normalizeProject({});
  positions.clear();
  els.title.value = '';
  setCharacterError();
  setRelationError();
  render(true);
  announce('Mapa vaciado.');
  analytics('character_map_clear');
});

render(true);
