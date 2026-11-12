// Índice de autores: filtros combinables, ordenación, paginación y test de descubrimiento.
// Sin JS la lista completa sigue visible y los controles permanecen desactivados.
(() => {
  'use strict';
  const root = document.querySelector('.catalogue-authors-index');
  const form = root?.querySelector('[data-index-filters]');
  const list = root?.querySelector('[data-index-list]');
  if (!root || !form || !list) return;
  const status = root.querySelector('[data-index-count]');
  const empty = root.querySelector('[data-index-empty]');
  const noun = form.dataset.noun || 'autores';
  const pagination = root.querySelector('[data-index-pagination]');
  const search = root.querySelector('[data-index-filter="q"]');
  const stateField = root.querySelector('[data-index-filter="estado"]');
  const orderField = root.querySelector('[data-index-filter="orden"]');
  const typeSelect = form.querySelector('select[data-index-filter="tipo"]');
  const groupField = form.querySelector('[data-index-filter="grupo"]');
  const pageSize = Math.max(1, Number(root.dataset.indexPageSize) || list.children.length);
  const now = new Date();
  const today = root.dataset.indexDate || [now.getFullYear(), String(now.getMonth() + 1).padStart(2, '0'), String(now.getDate()).padStart(2, '0')].join('-');
  const anchor = new Date(today + 'T00:00:00Z');
  anchor.setUTCDate(anchor.getUTCDate() - 30);
  const recent = anchor.toISOString().slice(0, 10);
  const fold = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const items = [...list.children].map((li, index) => {
    const dates = (li.dataset.dates || '').split(' ').filter(Boolean);
    return {
      li,
      index,
      text: fold(li.dataset.search || li.textContent),
      groups: (li.dataset.groups || '').split(' ').filter(Boolean),
      owner: li.dataset.owner || '',
      books: Number(li.dataset.books) || 0,
      latest: dates.filter(date => date <= today).pop() || '',
      next: dates.find(date => date > today) || '',
    };
  });
  const compare = (a, b) => (a > b) - (a < b);
  const sorters = {
    nombre: (a, b) => a.index - b.index,
    proximo: (a, b) => compare(a.next || '~', b.next || '~') || a.index - b.index,
    reciente: (a, b) => compare(b.latest, a.latest) || a.index - b.index,
    libros: (a, b) => b.books - a.books || a.index - b.index,
  };
  const typeFields = () => [...form.querySelectorAll('input[type="checkbox"][data-index-filter="tipo"]')];
  const selectedTypes = () => typeFields().length
    ? typeFields().filter(field => field.checked).map(field => field.value)
    : typeSelect?.value ? [typeSelect.value] : [];
  let page = 1;
  let timer = 0;

  const writeHash = () => {
    const params = new URLSearchParams();
    const query = search.value.trim();
    if (query) params.set('q', query);
    for (const type of selectedTypes()) params.append('tipo', type);
    if (groupField?.value) params.set('grupo', groupField.value);
    if (stateField.value) params.set('estado', stateField.value);
    if (orderField.value && orderField.value !== 'nombre') params.set('orden', orderField.value);
    if (page > 1) params.set('pagina', String(page));
    const hash = params.toString();
    if (hash !== location.hash.slice(1)) history.replaceState(history.state, '', hash ? '#' + hash : location.pathname + location.search);
  };

  const renderPagination = (pageCount) => {
    if (!pagination) return;
    pagination.replaceChildren();
    if (pageCount <= 1) return;
    const makeButton = (label, destination, ariaLabel) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = label;
      button.setAttribute('aria-label', ariaLabel);
      button.disabled = destination === page;
      button.addEventListener('click', () => {
        page = destination;
        apply(false);
        const heading = root.querySelector('#authors-list');
        heading.focus();
        heading.scrollIntoView({ block: 'start' });
      });
      return button;
    };
    pagination.append(makeButton('Anterior', Math.max(1, page - 1), 'Autores anteriores'));
    const label = document.createElement('span');
    label.setAttribute('aria-current', 'page');
    label.textContent = 'Página ' + page + ' de ' + pageCount;
    pagination.append(label);
    pagination.append(makeButton('Siguiente', Math.min(pageCount, page + 1), 'Autores siguientes'));
  };

  function apply(resetPage = true) {
    const query = fold(search.value.trim());
    const types = selectedTypes();
    const group = groupField?.value || '';
    const state = stateField.value;
    const sorter = sorters[orderField.value] ? orderField.value : 'nombre';
    const matching = items.filter(item => (!query || item.text.includes(query))
      && (!types.length || types.some(type => item.groups.includes(type)))
      && (!group || item.owner === group)
      && (state !== 'proximos' || item.next !== '')
      && (state !== 'novedad' || item.latest >= recent));
    matching.sort(sorters[sorter]);
    if (resetPage) page = 1;
    const pageCount = Math.max(1, Math.ceil(matching.length / pageSize));
    page = Math.min(page, pageCount);
    const visible = matching.slice((page - 1) * pageSize, page * pageSize);
    for (const item of items) item.li.hidden = true;
    list.replaceChildren(...visible.map(item => item.li));
    if (status) status.textContent = matching.length === items.length
      ? items.length + ' ' + noun
      : 'Mostrando ' + matching.length + ' de ' + items.length + ' ' + noun;
    if (empty) empty.hidden = matching.length > 0;
    renderPagination(pageCount);
    writeHash();
  }

  const readHash = () => {
    const params = new URLSearchParams(location.hash.slice(1));
    search.value = (params.get('q') || '').slice(0, 120);
    const types = new Set(params.getAll('tipo'));
    for (const field of typeFields()) field.checked = types.has(field.value);
    if (typeSelect) typeSelect.value = [...typeSelect.options].some(option => option.value === params.get('tipo'))
      ? params.get('tipo') : '';
    if (groupField) groupField.value = [...groupField.options].some(option => option.value === params.get('grupo'))
      ? params.get('grupo') : '';
    stateField.value = [...stateField.options].some(option => option.value === params.get('estado'))
      ? params.get('estado') : '';
    orderField.value = sorters[params.get('orden')] ? params.get('orden') : 'nombre';
    const requestedPage = Number(params.get('pagina'));
    page = Number.isSafeInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1;
    apply(false);
  };

  form.addEventListener('submit', event => { event.preventDefault(); apply(); });
  root.addEventListener('change', event => {
    if (event.target.matches('[data-index-filter]')) apply();
  });
  search?.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => apply(), 150);
  });
  form.addEventListener('reset', () => setTimeout(() => apply(), 0));
  root.querySelector('[data-index-reset]')?.addEventListener('click', () => form.reset());
  root.querySelector('[data-index-shortcut]')?.addEventListener('click', () => {
    stateField.value = 'proximos';
    orderField.value = 'proximo';
    apply();
  });
  root.querySelector('[data-author-filter-toggle]')?.addEventListener('click', event => {
    const button = event.currentTarget;
    const expanded = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', String(!expanded));
    root.querySelector('#authors-filter-panel').hidden = expanded;
  });
  root.querySelector('[data-author-quiz-submit]')?.addEventListener('click', () => {
    const quizType = root.querySelector('[data-author-quiz-type]').value;
    const quizState = root.querySelector('[data-author-quiz-state]').value;
    search.value = '';
    for (const field of typeFields()) field.checked = !quizType || field.value === quizType;
    stateField.value = quizState;
    orderField.value = quizState === 'proximos' ? 'proximo' : quizState === 'novedad' ? 'reciente' : 'nombre';
    apply();
    root.querySelector('.catalogue-authors-quiz').open = false;
    const heading = root.querySelector('#authors-list');
    heading.focus();
    heading.scrollIntoView({ block: 'start', behavior: 'smooth' });
  });
  window.addEventListener('hashchange', readHash);

  for (const control of root.querySelectorAll('[data-index-filter]')) control.disabled = false;
  form.querySelector('fieldset').disabled = false;
  for (const control of root.querySelectorAll('[data-author-quiz-type], [data-author-quiz-state], [data-author-quiz-submit]')) control.disabled = false;
  const filterToggle = root.querySelector('[data-author-filter-toggle]');
  if (filterToggle) filterToggle.disabled = false;
  if (filterToggle && matchMedia('(max-width: 900px)').matches) {
    filterToggle.setAttribute('aria-expanded', 'false');
    root.querySelector('#authors-filter-panel').hidden = true;
  }
  readHash();
})();
