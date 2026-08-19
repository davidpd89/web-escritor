(() => {
  'use strict';

  const root = document.querySelector('[data-editoriales-directory]');
  if (!root) return;

  const search = root.querySelector('[data-editoriales-search]');
  const genre = root.querySelector('[data-editoriales-genre]');
  const status = root.querySelector('[data-editoriales-status]');
  const direct = root.querySelector('[data-editoriales-direct]');
  const reset = root.querySelector('[data-editoriales-reset]');
  const count = root.querySelector('[data-editoriales-count]');
  const empty = root.querySelector('[data-editoriales-empty]');
  const cards = [...root.querySelectorAll('[data-editorial-card]')];

  const normalize = (value = '') => value
    .toLocaleLowerCase('es')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim();

  const readHash = () => {
    const params = new URLSearchParams(location.hash.replace(/^#/, ''));
    if (search) search.value = params.get('q') || '';
    if (genre) genre.value = params.get('genero') || '';
    if (status) status.value = params.get('estado') || '';
    if (direct) direct.checked = params.get('directo') === '1';
  };

  const writeHash = () => {
    const params = new URLSearchParams();
    if (search?.value.trim()) params.set('q', search.value.trim());
    if (genre?.value) params.set('genero', genre.value);
    if (status?.value) params.set('estado', status.value);
    if (direct?.checked) params.set('directo', '1');
    const next = params.toString();
    history.replaceState(null, '', `${location.pathname}${location.search}${next ? `#${next}` : ''}`);
  };

  const apply = ({ updateHash = true } = {}) => {
    const q = normalize(search?.value);
    const wantedGenre = normalize(genre?.value);
    const wantedStatus = status?.value || '';
    const onlyDirect = Boolean(direct?.checked);
    let visible = 0;

    cards.forEach((card) => {
      const haystack = normalize(`${card.dataset.name || ''} ${card.dataset.group || ''} ${card.dataset.genres || ''} ${card.textContent || ''}`);
      const genres = normalize(card.dataset.genres || '').split('|');
      const matches = (!q || haystack.includes(q))
        && (!wantedGenre || genres.includes(wantedGenre))
        && (!wantedStatus || card.dataset.status === wantedStatus)
        && (!onlyDirect || card.dataset.direct === 'true');

      card.hidden = !matches;
      if (matches) visible += 1;
    });

    if (count) count.textContent = `${visible} ${visible === 1 ? 'editorial' : 'editoriales'}`;
    if (empty) empty.hidden = visible !== 0;
    if (updateHash) writeHash();
  };

  [search, genre, status, direct].filter(Boolean).forEach((control) => {
    control.addEventListener(control === search ? 'input' : 'change', () => apply());
  });

  reset?.addEventListener('click', () => {
    if (search) search.value = '';
    if (genre) genre.value = '';
    if (status) status.value = '';
    if (direct) direct.checked = false;
    apply();
    search?.focus();
  });

  window.addEventListener('hashchange', () => {
    readHash();
    apply({ updateHash: false });
  });

  readHash();
  apply({ updateHash: false });
})();
