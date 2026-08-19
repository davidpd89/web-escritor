import { normalizeProject, circularLayout, visibleGraph, relationshipSummary, serializeProject, parseProject, slugify } from './mapa-personajes-core.js';

const $ = sel => document.querySelector(sel);
const els = {
  title: $('#map-title'),
  characterName: $('#character-name'),
  addCharacter: $('#add-character'),
  from: $('#relation-from'),
  to: $('#relation-to'),
  type: $('#relation-type'),
  label: $('#relation-label'),
  evolution: $('#relation-evolution'),
  directed: $('#relation-directed'),
  addRelation: $('#add-relation'),
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

function announce(message) { els.status.textContent = message; }
function analytics(event, target = '') {
  document.dispatchEvent(new CustomEvent('dp:analytics', { detail: { event, target } }));
}

function addCharacter(name) {
  name = String(name || '').trim();
  if (!name) return;
  const base = slugify(name);
  let id = base, i = 2;
  while (project.characters.some(c => c.id === id)) id = `${base}-${i++}`;
  project.characters.push({ id, name, note: '' });
  render(true);
  announce(`Personaje añadido: ${name}`);
}

function addRelation() {
  const from = els.from.value;
  const to = els.to.value;
  if (!from || !to || from === to) {
    announce('Selecciona dos personajes distintos.');
    return;
  }
  project.relations.push({
    from, to, type: els.type.value, label: els.label.value.trim(),
    evolution: els.evolution.value.trim(), directed: els.directed.checked,
  });
  project = normalizeProject(project);
  els.label.value = '';
  els.evolution.value = '';
  render(false);
  announce('Relación añadida.');
}

function selectOptions() {
  const options = project.characters.map(c => `<option value="${escapeHtml(c.id)}">${escapeHtml(c.name)}</option>`).join('');
  const blank = '<option value="">Selecciona…</option>';
  const previous = [els.from.value, els.to.value, els.focus.value];
  els.from.innerHTML = blank + options;
  els.to.innerHTML = blank + options;
  els.focus.innerHTML = '<option value="">Todos los personajes</option>' + options;
  if (project.characters.some(c => c.id === previous[0])) els.from.value = previous[0];
  if (project.characters.some(c => c.id === previous[1])) els.to.value = previous[1];
  if (project.characters.some(c => c.id === previous[2])) els.focus.value = previous[2];
}

function escapeHtml(value) {
  return String(value).replace(/[&<>\'\"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
}

function activeTypes() {
  return [...els.filters].filter(el => el.checked).map(el => el.value);
}

function render(resetPositions = false) {
  project.title = els.title.value.trim();
  selectOptions();
  const graph = visibleGraph(project, { focusId: els.focus.value, types: activeTypes() });
  const width = 900, height = 580;
  const fresh = circularLayout(graph.characters, width, height, els.focus.value);
  if (resetPositions) positions.clear();
  for (const node of fresh) {
    if (!positions.has(node.id) || els.focus.value) positions.set(node.id, { x: node.x, y: node.y });
  }
  const byId = new Map(graph.characters.map(c => [c.id, { ...c, ...(positions.get(c.id) || {}) }]));
  els.svg.innerHTML = '';
  els.svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  els.empty.hidden = graph.characters.length > 0;

  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  defs.innerHTML = '<marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" /></marker>';
  els.svg.appendChild(defs);

  for (const rel of graph.relations) {
    const a = byId.get(rel.from), b = byId.get(rel.to);
    if (!a || !b) continue;
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.classList.add('map-edge', `type-${rel.type}`);
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', a.x); line.setAttribute('y1', a.y); line.setAttribute('x2', b.x); line.setAttribute('y2', b.y);
    if (rel.directed) line.setAttribute('marker-end', 'url(#arrow)');
    g.appendChild(line);
    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.setAttribute('x', (a.x + b.x) / 2); label.setAttribute('y', (a.y + b.y) / 2 - 8);
    label.textContent = rel.label || rel.type;
    g.appendChild(label);
    els.svg.appendChild(g);
  }

  for (const c of graph.characters) {
    const pos = byId.get(c.id);
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.classList.add('map-node'); g.dataset.id = c.id; g.setAttribute('transform', `translate(${pos.x} ${pos.y})`);
    g.innerHTML = `<circle r="42"></circle><text text-anchor="middle" dy="4">${escapeHtml(c.name.slice(0, 18))}</text>`;
    makeDraggable(g, c.id);
    els.svg.appendChild(g);
  }

  const summary = relationshipSummary(project);
  els.stats.innerHTML = `<strong>${summary.characters}</strong> personajes · <strong>${summary.relations}</strong> relaciones` +
    (summary.mostConnected[0] ? ` · más conectado: <strong>${escapeHtml(summary.mostConnected[0].character)}</strong> (${summary.mostConnected[0].count})` : '');
  els.list.innerHTML = project.relations.map((r, i) => {
    const a = project.characters.find(c => c.id === r.from)?.name || r.from;
    const b = project.characters.find(c => c.id === r.to)?.name || r.to;
    return `<li><span><strong>${escapeHtml(a)}</strong> ${r.directed ? '→' : '—'} <strong>${escapeHtml(b)}</strong> · ${escapeHtml(r.label || r.type)}${r.evolution ? `<small>${escapeHtml(r.evolution)}</small>` : ''}</span><button type="button" data-remove-relation="${i}" aria-label="Eliminar relación ${escapeHtml(a)} y ${escapeHtml(b)}">×</button></li>`;
  }).join('');
}

function makeDraggable(node, id) {
  let dragging = false;
  node.addEventListener('pointerdown', e => { dragging = true; node.setPointerCapture(e.pointerId); });
  node.addEventListener('pointermove', e => {
    if (!dragging) return;
    const pt = els.svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY;
    const p = pt.matrixTransform(els.svg.getScreenCTM().inverse());
    positions.set(id, { x: p.x, y: p.y });
    render(false);
  });
  node.addEventListener('pointerup', () => { dragging = false; });
}

function download(name, type, text) {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

els.addCharacter.addEventListener('click', () => { addCharacter(els.characterName.value); els.characterName.value = ''; analytics('character_map_add_character'); });
els.characterName.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); els.addCharacter.click(); } });
els.addRelation.addEventListener('click', () => { addRelation(); analytics('character_map_add_relation'); });
els.focus.addEventListener('change', () => { positions.clear(); render(true); analytics('character_map_focus', els.focus.value ? 'single' : 'all'); });
els.filters.forEach(el => el.addEventListener('change', () => render(false)));
els.title.addEventListener('input', () => { project.title = els.title.value.trim(); });
els.list.addEventListener('click', e => { const btn = e.target.closest('[data-remove-relation]'); if (!btn) return; project.relations.splice(Number(btn.dataset.removeRelation), 1); project = normalizeProject(project); render(false); });
els.exportJson.addEventListener('click', () => { download('mapa-personajes.json', 'application/json', serializeProject(project)); analytics('character_map_export', 'json'); });
els.exportSvg.addEventListener('click', () => { const clone = els.svg.cloneNode(true); clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg'); download('mapa-personajes.svg', 'image/svg+xml', new XMLSerializer().serializeToString(clone)); analytics('character_map_export', 'svg'); });
els.importJson.addEventListener('click', () => els.file.click());
els.file.addEventListener('change', async () => {
  const file = els.file.files?.[0]; if (!file) return;
  try { project = parseProject(await file.text()); els.title.value = project.title; positions.clear(); render(true); announce('Mapa importado.'); analytics('character_map_import'); }
  catch { announce('No se ha podido leer ese JSON.'); }
  els.file.value = '';
});
els.clear.addEventListener('click', () => { project = normalizeProject({}); positions.clear(); els.title.value = ''; render(true); announce('Mapa vaciado.'); analytics('character_map_clear'); });

render(true);
