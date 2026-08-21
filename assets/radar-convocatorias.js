(() => {
  'use strict';

  const MS_DAY = 86400000;
  const STALE_DAYS = 30;
  const normalize = (value = '') => String(value)
    .toLocaleLowerCase('es')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim();

  const parseCivil = (value) => {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || ''));
    if (!match) return null;
    const year = Number(match[1]);
    const month = Number(match[2]);
    const day = Number(match[3]);
    const stamp = Date.UTC(year, month - 1, day);
    const check = new Date(stamp);
    if (check.getUTCFullYear() !== year || check.getUTCMonth() !== month - 1 || check.getUTCDate() !== day) return null;
    return { year, month, day, stamp };
  };

  const todayCivil = () => {
    const injected = parseCivil(window.__DP_RADAR_TODAY__);
    if (injected) return injected;
    const now = new Date();
    return parseCivil(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`);
  };

  const daysUntil = (deadline, today) => {
    const end = parseCivil(deadline);
    const start = typeof today === 'string' ? parseCivil(today) : today;
    if (!end || !start) return null;
    return Math.round((end.stamp - start.stamp) / MS_DAY);
  };

  const daysSince = (verifiedAt, today) => {
    const verified = parseCivil(verifiedAt);
    const start = typeof today === 'string' ? parseCivil(today) : today;
    if (!verified || !start) return null;
    return Math.round((start.stamp - verified.stamp) / MS_DAY);
  };

  const relativeLabel = (days) => {
    if (days === 0) return 'hoy';
    if (days === 1) return 'mañana';
    if (days > 1) return `faltan ${days} días`;
    return 'plazo finalizado';
  };

  window.DPRadarDates = Object.freeze({ parseCivil, daysUntil, daysSince, relativeLabel });

  const items = [...document.querySelectorAll('[data-radar-item]')];
  if (!items.length) return;

  const query = document.querySelector('[data-radar-search]');
  const type = document.querySelector('[data-radar-type]');
  const genre = document.querySelector('[data-radar-genre]');
  const soon = document.querySelector('[data-radar-soon]');
  const count = document.querySelector('[data-radar-count]');
  const clear = document.querySelector('[data-radar-clear]');
  const emptyClear = document.querySelector('[data-radar-empty-clear]');
  const empty = document.querySelector('[data-radar-filter-empty]');
  const today = todayCivil();

  const emit = (event, detail = {}) => document.dispatchEvent(new CustomEvent('dp:analytics', { detail: { event, ...detail } }));

  document.addEventListener('click', (event) => {
    const source = event.target.closest?.('[data-radar-source]');
    if (source) emit('radar_source_click', { opportunity_type: source.dataset.radarSourceType || 'unknown' });
    if (event.target.closest?.('[data-radar-calendar]')) emit('radar_calendar_click');
  });

  items.forEach((item) => {
    const remaining = daysUntil(item.dataset.deadline, today);
    const age = daysSince(item.dataset.verifiedAt, today);
    const expired = remaining === null || remaining < 0;
    const stale = age === null || age > STALE_DAYS;
    item.dataset.radarUnavailable = expired || stale ? 'true' : 'false';

    const relative = item.querySelector('[data-radar-relative]');
    if (relative && remaining !== null && remaining >= 0) relative.textContent = ` · ${relativeLabel(remaining)}`;

    const status = item.querySelector('[data-radar-status]');
    if (status) {
      if (expired) status.textContent = 'Plazo finalizado';
      else if (stale) status.textContent = 'Verificación caducada';
      else if (remaining === 0) status.textContent = 'Cierra hoy';
      else if (remaining === 1) status.textContent = 'Cierra mañana';
      else if (remaining <= 7) status.textContent = `Cierra en ${remaining} días`;
      else status.textContent = 'En plazo';
    }
  });

  const apply = () => {
    const q = normalize(query?.value);
    const wantedType = normalize(type?.value);
    const wantedGenre = normalize(genre?.value);
    let visible = 0;

    items.forEach((item) => {
      const remaining = daysUntil(item.dataset.deadline, today);
      const haystack = normalize(`${item.dataset.title || ''} ${item.dataset.organizer || ''} ${item.textContent || ''}`);
      const itemType = normalize(item.dataset.type);
      const itemGenres = normalize(item.dataset.genres).split('|');
      const available = item.dataset.radarUnavailable !== 'true';
      const closesSoon = remaining !== null && remaining >= 0 && remaining <= 7;
      const matches = available
        && (!q || haystack.includes(q))
        && (!wantedType || itemType === wantedType)
        && (!wantedGenre || itemGenres.includes(wantedGenre))
        && (!soon?.checked || closesSoon);
      item.hidden = !matches;
      if (matches) visible += 1;
    });

    if (count) count.textContent = `${visible} ${visible === 1 ? 'convocatoria' : 'convocatorias'} visibles`;
    if (empty) empty.hidden = visible !== 0;
  };

  [query, type, genre, soon].forEach((control) => {
    control?.addEventListener(control === query ? 'input' : 'change', apply);
  });

  const clearFilters = () => {
    if (query) query.value = '';
    if (type) type.value = '';
    if (genre) genre.value = '';
    if (soon) soon.checked = false;
    apply();
    query?.focus();
  };

  clear?.addEventListener('click', clearFilters);
  emptyClear?.addEventListener('click', clearFilters);
  apply();
})();
