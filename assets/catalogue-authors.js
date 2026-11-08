// Índices de autores y de editoriales: búsqueda, tipo de libro, grupo, próximos/novedades y orden,
// con el estado en el #hash para compartir.
// Sin JS la lista completa sigue a la vista; el formulario solo se activa aquí.
(() => {
  'use strict';
  const form = document.querySelector('[data-index-filters]');
  const list = document.querySelector('[data-index-list]');
  if (!form || !list) return;
  const status = document.querySelector('[data-index-count]');
  const empty = document.querySelector('[data-index-empty]');
  const noun = form.dataset.noun || 'autores';
  const fold = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const pad = n => String(n).padStart(2, '0');
  const iso = d => d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  const now = new Date();
  const today = iso(now);
  const recent = iso(new Date(now.getFullYear(), now.getMonth(), now.getDate() - 30));
  const items = [...list.children].map((li, i) => {
    const dates = (li.dataset.dates || '').split(' ').filter(Boolean);
    return {
      li, i,
      text: fold(li.textContent),
      groups: (li.dataset.groups || '').split(' '),
      owner: li.dataset.owner || '',
      books: Number(li.dataset.books) || 0,
      latest: dates.filter(d => d <= today).pop() || '',
      next: dates.find(d => d > today) || '',
    };
  });
  const cmp = (a, b) => (a > b) - (a < b);
  const sorters = {
    nombre: (a, b) => a.i - b.i,
    proximo: (a, b) => cmp(a.next || '~', b.next || '~') || a.i - b.i,
    reciente: (a, b) => cmp(b.latest, a.latest) || a.i - b.i,
    libros: (a, b) => b.books - a.books || a.i - b.i,
  };
  const keys = ['q', 'tipo', 'grupo', 'estado', 'orden'];
  const field = key => form.querySelector('[data-index-filter="' + key + '"]');
  let order = 'nombre';
  let timer = 0;

  const apply = () => {
    const q = fold((field('q')?.value || '').trim());
    const tipo = field('tipo')?.value || '';
    const grupo = field('grupo')?.value || '';
    const estado = field('estado')?.value || '';
    const orden = sorters[field('orden')?.value] ? field('orden').value : 'nombre';
    let shown = 0;
    for (const it of items) {
      const ok = (!q || it.text.includes(q))
        && (!tipo || it.groups.includes(tipo))
        && (!grupo || it.owner === grupo)
        && (estado !== 'proximos' || it.next !== '')
        && (estado !== 'novedad' || it.latest >= recent);
      if (it.li.hidden === ok) it.li.hidden = !ok;
      shown += ok;
    }
    if (orden !== order) {
      order = orden;
      list.append(...items.slice().sort(sorters[orden]).map(it => it.li));
    }
    if (status) status.textContent = shown === items.length ? items.length + ' ' + noun : 'Mostrando ' + shown + ' de ' + items.length + ' ' + noun;
    if (empty) empty.hidden = shown > 0;
    const params = new URLSearchParams();
    for (const key of keys) {
      const value = field(key)?.value || '';
      if (value && !(key === 'orden' && value === 'nombre')) params.set(key, key === 'q' ? value.trim() : value);
    }
    const hash = params.toString();
    if (hash !== location.hash.slice(1)) history.replaceState(history.state, '', hash ? '#' + hash : location.pathname + location.search);
  };

  const read = () => {
    const params = new URLSearchParams(location.hash.slice(1));
    for (const key of keys) {
      const el = field(key);
      if (!el) continue;
      const value = params.get(key) || '';
      if (el.tagName === 'SELECT') el.value = [...el.options].some(o => o.value === value) ? value : el.options[0].value;
      else el.value = value.slice(0, 120);
    }
    apply();
  };

  form.addEventListener('submit', event => { event.preventDefault(); apply(); });
  form.addEventListener('change', apply);
  form.addEventListener('input', event => {
    if (event.target !== field('q')) return;
    clearTimeout(timer);
    timer = setTimeout(apply, 150);
  });
  form.addEventListener('reset', () => setTimeout(apply));
  document.querySelector('[data-index-reset]')?.addEventListener('click', () => form.reset());
  form.querySelector('[data-index-shortcut]')?.addEventListener('click', () => {
    field('estado').value = 'proximos';
    field('orden').value = 'proximo';
    apply();
  });
  window.addEventListener('hashchange', read);
  form.querySelector('fieldset').disabled = false;
  read();
})();
