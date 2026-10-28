(() => {
  'use strict';

  const MS_DAY = 86400000;
  const STALE_DAYS = 30;
  const SITE_TIME_ZONE = 'Europe/Madrid';
  // n with tilde and u with diaeresis are distinct letters in Spanish, not
  // accented n/u: folding them makes a search for one of them match every
  // word containing the base letter. Fold every other combining mark.
  const normalize = (value = '') => String(value)
    .toLocaleLowerCase('es')
    .normalize('NFD')
    .replace(/(?<!n)\u0303|(?<!u)\u0308|[\u0300-\u0302\u0304-\u0307\u0309-\u036f]/g, '')
    .normalize('NFC')
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

  const siteCivilDate = (value = new Date()) => {
    const instant = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(instant.getTime())) return null;
    const parts = Object.fromEntries(
      new Intl.DateTimeFormat('en-US', {
        timeZone: SITE_TIME_ZONE,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      }).formatToParts(instant).filter((part) => part.type !== 'literal').map((part) => [part.type, part.value]),
    );
    return parseCivil(`${parts.year}-${parts.month}-${parts.day}`);
  };

  const todayCivil = () => {
    const injected = parseCivil(window.__DP_RADAR_TODAY__);
    if (injected) return injected;
    return siteCivilDate(new Date());
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

  window.DPRadarDates = Object.freeze({ parseCivil, siteCivilDate, daysUntil, daysSince, relativeLabel, SITE_TIME_ZONE });

  const items = [...document.querySelectorAll('[data-radar-item]')];
  if (!items.length) return;

  const query = document.querySelector('[data-radar-search]');
  const type = document.querySelector('[data-radar-type]');
  const genre = document.querySelector('[data-radar-genre]');
  const kind = document.querySelector('select[data-radar-kind]');
  const soon = document.querySelector('[data-radar-soon]');
  const showExpired = document.querySelector('[data-radar-expired]');
  const count = document.querySelector('[data-radar-count]');
  const clear = document.querySelector('[data-radar-clear]');
  const emptyClear = document.querySelector('[data-radar-empty-clear]');
  const empty = document.querySelector('[data-radar-filter-empty]');
  let today = todayCivil();

  const emit = (event, detail = {}) => document.dispatchEvent(new CustomEvent('dp:analytics', { detail: { event, ...detail } }));

  document.addEventListener('click', (event) => {
    const source = event.target.closest?.('[data-radar-source]');
    if (source) emit('radar_source_click', { opportunity_type: source.dataset.radarSourceType || 'unknown' });
    if (event.target.closest?.('[data-radar-calendar]')) emit('radar_calendar_click');
  });

  const refreshAvailability = () => items.forEach((item) => {
    const isWatch = item.dataset.radarKind === 'watch';
    const isExpiredCard = item.dataset.radarKind === 'expired';
    const remaining = isWatch ? null : daysUntil(item.dataset.deadline, today);
    const age = daysSince(item.dataset.verifiedAt, today);
    const expired = !isWatch && (remaining === null || remaining < 0);
    const stale = age === null || age > STALE_DAYS;
    item.dataset.radarUnavailable = expired || stale ? 'true' : 'false';

    const status = item.querySelector('[data-radar-status]');
    if (status) {
      if (isWatch) {
        const watchLabel = item.dataset.watchKind === 'verification' ? 'Pendiente de verificar' : item.dataset.watchKind === 'recurring' ? 'Próxima edición a vigilar' : 'Próxima apertura';
        status.textContent = stale ? 'Verificación caducada' : watchLabel;
      }
      else if (expired) status.textContent = isExpiredCard
        ? `Cerr\u00f3 el ${new Date(`${item.dataset.deadline}T00:00:00Z`).toLocaleDateString('es-ES', { timeZone: 'UTC' })}`
        : 'Plazo finalizado';
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
    const wantedKind = normalize(kind?.value);
    let visible = 0;

    items.forEach((item) => {
      const declaredKind = item.dataset.radarKind;
      const itemKind = declaredKind === 'watch' || declaredKind === 'expired' ? declaredKind : 'active';
      const remaining = itemKind === 'active' ? daysUntil(item.dataset.deadline, today) : null;
      const haystack = normalize(`${item.dataset.title || ''} ${item.dataset.organizer || ''} ${item.textContent || ''}`);
      const itemType = normalize(item.dataset.type);
      const itemGenres = normalize(item.dataset.genres).split('|');
      // Una ficha de la seccion de cerradas esta 'no disponible' por
      // definicion -- su plazo paso -- y aun asi se puede mostrar si quien
      // lee lo pide. Lo que no cambia es el caso que este guard protege de
      // verdad: una ficha de la lista activa cuyo plazo ha pasado mientras el
      // HTML estaba cacheado sigue desapareciendo sola.
      const available = itemKind === 'expired'
        ? Boolean(showExpired?.checked)
        : item.dataset.radarUnavailable !== 'true';
      const closesSoon = remaining !== null && remaining >= 0 && remaining <= 7;
      const matches = available
        && (!q || haystack.includes(q))
        && (!wantedType || itemType === wantedType)
        && (!wantedGenre || itemGenres.includes(wantedGenre))
        && (!wantedKind || itemKind === wantedKind)
        && (!soon?.checked || (itemKind === 'active' && closesSoon));
      item.hidden = !matches;
      if (matches) visible += 1;
    });

    if (count) count.textContent = `${visible} ${visible === 1 ? 'convocatoria' : 'convocatorias'} ${visible === 1 ? 'visible' : 'visibles'}`;
    document.querySelectorAll('[data-radar-section]').forEach((section) => {
      section.hidden = section.querySelectorAll('[data-radar-item]:not([hidden])').length === 0;
    });
    if (empty) empty.hidden = visible !== 0;
  };

  // Solo estos parámetros pertenecen al radar. Otros parámetros se conservan.
  const FILTER_KEYS = ['q', 'tipo', 'genero', 'situacion', 'pronto', 'vencidas'];
  const validOption = (select, value) => value && [...(select?.options || [])].some((option) => option.value === value) ? value : '';

  const selectedParams = () => {
    const params = new URLSearchParams();
    if (query?.value.trim()) params.set('q', query.value.trim());
    if (type?.value) params.set('tipo', type.value);
    if (genre?.value) params.set('genero', genre.value);
    if (kind?.value) params.set('situacion', kind.value);
    if (soon?.checked) params.set('pronto', '1');
    if (showExpired?.checked) params.set('vencidas', '1');
    return params;
  };

  // Un fragmento sin '=' es un ancla, no una selección de filtros.
  const hashParams = () => {
    const fragment = location.hash.slice(1);
    return fragment && !fragment.includes('=') ? null : new URLSearchParams(fragment);
  };

  const restoreControls = (params) => {
    const savedQuery = params.get('q') || '';
    if (query) query.value = savedQuery.length <= 512 && !savedQuery.includes('\uFFFD') ? savedQuery : '';
    if (type) type.value = validOption(type, params.get('tipo'));
    if (genre) genre.value = validOption(genre, params.get('genero'));
    if (kind) kind.value = validOption(kind, params.get('situacion'));
    if (soon) soon.checked = params.get('pronto') === '1';
    if (showExpired) showExpired.checked = params.get('vencidas') === '1';
  };

  const nextUrl = () => {
    const original = hashParams();
    const params = original || new URLSearchParams();
    FILTER_KEYS.forEach((key) => params.delete(key));
    selectedParams().forEach((value, key) => params.set(key, value));
    const fragment = params.toString();
    const suffix = fragment ? `#${fragment}` : original === null ? location.hash : '';
    return `${location.pathname}${location.search}${suffix}`;
  };

  const snapshotState = () => ({
    ...(history.state && typeof history.state === 'object' ? history.state : {}),
    dpRadarFilters: selectedParams().toString(),
  });

  let lastRestoredUrl = location.href;
  const writeHash = (mode) => {
    const target = nextUrl();
    const current = `${location.pathname}${location.search}${location.hash}`;
    const saved = selectedParams().toString();
    if (target === current && history.state?.dpRadarFilters === saved) return;
    // No acumular entradas cuando la dirección no cambia.
    const method = target === current ? 'replaceState' : mode === 'push' ? 'pushState' : 'replaceState';
    history[method](snapshotState(), '', target);
    lastRestoredUrl = location.href;
  };

  const update = (mode) => {
    apply();
    writeHash(mode);
  };

  [query, type, genre, kind, soon, showExpired].forEach((control) => {
    control?.addEventListener(control === query ? 'input' : 'change', () => {
      update(control === query ? 'replace' : 'push');
    });
  });

  const clearFilters = () => {
    if (query) query.value = '';
    if (type) type.value = '';
    if (genre) genre.value = '';
    if (kind) kind.value = '';
    if (soon) soon.checked = false;
    if (showExpired) showExpired.checked = false;
    update('push');
    query?.focus();
  };

  // Las anclas conservan los filtros. El estado asociado al ancla permite
  // recuperar esa misma selección también al volver con Atrás/Adelante.
  const restore = () => {
    if (location.href === lastRestoredUrl) return;
    lastRestoredUrl = location.href;
    const params = hashParams();
    if (params) {
      restoreControls(params);
    } else if (typeof history.state?.dpRadarFilters === 'string') {
      restoreControls(new URLSearchParams(history.state.dpRadarFilters));
    } else {
      history.replaceState(snapshotState(), '', location.href);
    }
    apply();
  };
  window.addEventListener('popstate', restore);
  window.addEventListener('hashchange', restore);

  showExpired?.addEventListener('change', () => {
    if (showExpired.checked) emit('radar_expired_shown');
  });

  clear?.addEventListener('click', clearFilters);
  emptyClear?.addEventListener('click', clearFilters);
  const refreshClock = () => {
    const current = todayCivil();
    if (current?.stamp === today?.stamp) return;
    today = current;
    refreshAvailability();
    apply();
  };
  // Long-lived and restored tabs must stop advertising expired deadlines too.
  // Visibility/pageshow cover suspended background timers and bfcache restores.
  setInterval(refreshClock, 60000);
  document.addEventListener('visibilitychange', refreshClock);
  window.addEventListener('pageshow', refreshClock);
  const initialParams = hashParams();
  if (initialParams) {
    restoreControls(initialParams);
  } else if (typeof history.state?.dpRadarFilters === 'string') {
    restoreControls(new URLSearchParams(history.state.dpRadarFilters));
  }
  refreshAvailability();
  apply();
})();
