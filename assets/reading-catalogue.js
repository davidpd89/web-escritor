/* Static books and purchase links work without JS; optional market data expires. */
(() => {
  'use strict';
  const root = document.querySelector('[data-reading-catalogue]');
  if (!root) return;
  const normalize = s => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es').trim();
  // Solo los ISBN-13 completos admiten separadores y prefijos de presentación.
  const searchQuery = s => {
    const candidate = s.trim().replace(/^ISBN(?:-13)?\s*:?\s*/i, '');
    return /^97[89](?:[\s-]*\d){10}$/.test(candidate) ? candidate.replace(/[\s-]/g, '') : normalize(s);
  };
  const form = root.querySelector('[data-catalogue-filters]');
  const cards = [...root.querySelectorAll('[data-catalogue-book]')];
  const originalOrder = new Map(cards.map((card, i) => [card, i]));
  const fields = form ? [...form.elements].filter(f => f.dataset.filter) : [];
  // Filtros con varias opciones a la vez (OR dentro de cada uno, AND entre ellos), como casillas.
  const FACETS = ['grupo', 'genero', 'tematica', 'temporada', 'edad', 'contenido', 'epoca', 'formato'];
  const boxes = form ? [...form.querySelectorAll('input[data-facet]')] : [];
  const pick = x => Array.isArray(x) ? x : x ? [x] : [];
  const collator = new Intl.Collator('es', { sensitivity: 'base', numeric: true });
  let market = { offers: [], ratings: [] };
  let currentPage = 1;
  const pageSize = 24;
  let offersIndex = new Map(), ratingsIndex = new Map();
  const stamp = s => typeof s === 'string' && /T.*(?:Z|[+-]\d\d:\d\d)$/.test(s) ? Date.parse(s) : NaN;
  const fresh = (e, hours) => { const start = stamp(e.actualizado_en), end = stamp(e.caduca_en), now = Date.now(); return Number.isFinite(start) && Number.isFinite(end) && start <= now && end > now && end > start && end - start <= hours * 3600000 && now - start <= hours * 3600000; };
  const safeURL = (raw, hosts, path) => { try { const u = new URL(raw); return u.protocol === 'https:' && !u.username && !u.password && !u.port && hosts.includes(u.hostname) && path.test(u.pathname) ? u : null; } catch { return null; } };
  const validOffer = o => { const u = safeURL(o.url, ['amazon.es', 'www.amazon.es'], /\/(?:dp|gp\/product)\/[A-Z0-9]{10}(?:\/|$)/); return fresh(o, 24) && o.moneda === 'EUR' && o.tipo === 'compra' && ['tapa-blanda', 'tapa-dura', 'ebook', 'audiolibro'].includes(o.formato) && Number.isSafeInteger(o.precio_centimos) && o.precio_centimos > 0 && o.precio_centimos < 100000000 && u && /^[A-Za-z0-9-]+$/.test(u.searchParams.get('tag') || ''); };
  const ratingSource = r => ['google_books', 'hardcover'].includes(r.fuente) ? r.fuente : !r.fuente || r.fuente === 'goodreads' ? 'goodreads' : null;
  const ratingLabel = r => ratingSource(r) === 'google_books' ? 'Google Books' : ratingSource(r) === 'hardcover' ? 'Hardcover' : 'Goodreads';
  const validRating = r => {
    if (!fresh(r, 720) || !Number.isFinite(r.puntuacion) || r.puntuacion < 1 || r.puntuacion > 5 || !Number.isSafeInteger(r.numero_valoraciones) || r.numero_valoraciones < 5) return false; // una sola valoración no es una referencia
    const source = ratingSource(r);
    if (source === 'goodreads') return Boolean(safeURL(r.url, ['www.goodreads.com', 'goodreads.com'], /^\/book\/show\/\d/));
    if (source === 'google_books') { const link = safeURL(r.url, ['books.google.com'], /^\/books$/); return Boolean(link && /^[A-Za-z0-9_-]{1,150}$/.test(link.searchParams.get('id') || '')); }
    if (source === 'hardcover') return Boolean(safeURL(r.url, ['hardcover.app', 'www.hardcover.app'], /^\/books\/[a-z0-9]+(?:-[a-z0-9]+)*$/));
    return false;
  };
  // Muestra de 1–4 valoraciones con fuente y vigencia válidas: existe, pero no es una nota fiable.
  const thinRating = r => Number.isSafeInteger(r.numero_valoraciones) && r.numero_valoraciones >= 1 && r.numero_valoraciones < 5 && validRating({...r, numero_valoraciones: 5});
  const discount = o => Number.isSafeInteger(o.precio_referencia_centimos) && o.precio_referencia_centimos > o.precio_centimos ? Math.floor((o.precio_referencia_centimos - o.precio_centimos) / o.precio_referencia_centimos * 100) : 0;
  // Index entries are validated by renderMarket. Recheck expiry on interaction,
  // without reparsing the same URLs for every card and quiz option.
  const offersFor = id => (offersIndex.get(id) || []).filter(o => fresh(o, 24));
  const ratingFor = id => (ratingsIndex.get(id) || []).find(r => fresh(r, 720));
  const madridDate = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Madrid', year: 'numeric', month: '2-digit', day: '2-digit' });
  let dateMinute = -1, dateValue;
  const today = () => {
    const minute = Math.floor(Date.now() / 60000);
    if (minute !== dateMinute) { dateMinute = minute; dateValue = madridDate.format(new Date()); }
    return dateValue;
  };
  const ageDays = s => /^\d{4}-\d{2}-\d{2}$/.test(s || '') ? (Date.parse(today() + 'T00:00:00Z') - Date.parse(s + 'T00:00:00Z')) / 86400000 : NaN;
  const isNew = (s, window) => { const days = ageDays(s); return window === 'proximamente' ? days < 0 && days >= -30 : days >= 0 && (window === '15' ? days < 15 : days <= Number(window)); };
  function renderNovelty() {
    for (const label of root.querySelectorAll('[data-release-label]')) {
      const fresh = isNew(label.dataset.releaseLabel, '15'), upcoming = !fresh && isNew(label.dataset.releaseLabel, 'proximamente');
      const text = fresh ? 'Novedad' : upcoming ? 'Pr\u00f3ximamente' : '';
      if (label.dataset.releaseFallback !== undefined) {
        label.textContent = text || label.dataset.releaseFallback;
        label.classList.toggle('catalogue-novelty', fresh || upcoming);
      } else { label.textContent = text; label.hidden = !text; }
    }
  }
  const values = () => ({...Object.fromEntries(fields.map(f => [f.dataset.filter, f.disabled ? '' : f.value])), ...Object.fromEntries(FACETS.map(k => [k, boxes.filter(b => b.dataset.facet === k && b.checked).map(b => b.value)]))});
  const matchingOffers = (card, v) => offersFor(card.dataset.bookId).filter(o => (!pick(v.formato).length || pick(v.formato).includes(o.formato)) && (!v.descuento || discount(o) >= Number(v.descuento)));
  // El precio que se filtra y ordena es el PVP de la edición publicada por la editorial: siempre disponible y comparable.
  const pvpOf = card => Number(card.dataset.pvp) || null;
  const priceOk = (card, v) => { const c = pvpOf(card); return (!v.precio_min || (c !== null && c >= Math.round(Number(v.precio_min) * 100))) && (!v.precio_max || (c !== null && c <= Math.round(Number(v.precio_max) * 100))); };
  const minPrice = card => pvpOf(card);
  function renderMarket() {
    offersIndex = new Map(); ratingsIndex = new Map();
    for (const offer of market.offers.filter(validOffer)) {
      if (!offersIndex.has(offer.libro_id)) offersIndex.set(offer.libro_id, []);
      offersIndex.get(offer.libro_id).push(offer);
    }
    const priority = {goodreads: 0, hardcover: 1, google_books: 2};
    for (const rating of market.ratings.filter(validRating).sort((a, b) => priority[ratingSource(a)] - priority[ratingSource(b)])) {
      if (!ratingsIndex.has(rating.libro_id)) ratingsIndex.set(rating.libro_id, []);
      ratingsIndex.get(rating.libro_id).push(rating);
    }
    for (const box of root.querySelectorAll('[data-rating-book]')) {
      const r = ratingFor(box.dataset.ratingBook); box.replaceChildren(); box.hidden = false;
      if (!r) {
        // Sin valoración verificada vigente NO se pinta una nota: ni estrellas vacías ni «0,0 (0)».
        // Que aquí no haya dato utilizable (caducado, proveedor caído, fuente no válida) no prueba que la fuente tenga cero opiniones.
        const thin = market.ratings.find(x => x.libro_id === box.dataset.ratingBook && thinRating(x));
        const isbn = /^\d{13}$/.test(box.dataset.isbn || '') ? box.dataset.isbn : '';
        // Tarjeta y ficha muestran lo mismo: nota verificada o enlace neutro a Goodreads.
        if (thin || isbn) {
          const ref = document.createElement('a'); ref.href = thin ? thin.url : 'https://www.goodreads.com/book/isbn/' + isbn; ref.target = '_blank'; ref.rel = 'noopener noreferrer';
          ref.className = 'catalogue-rating__ref'; ref.dataset.ratingState = thin ? 'insufficient' : 'unavailable';
          ref.textContent = thin ? ratingLabel(thin) + ' · menos de 5 valoraciones' : 'Goodreads · consultar ficha';
          ref.title = thin ? 'Muestra demasiado pequeña para mostrar una nota. Consultado el ' + new Date(thin.actualizado_en).toLocaleDateString('es-ES') : 'Sin valoración verificada en este catálogo';
          box.append(ref);
        }
        continue;
      }
      const link = document.createElement('a'); link.href = r.url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.dataset.ratingState = 'verified';
      const stars = document.createElement('span'); stars.className = 'catalogue-stars'; stars.setAttribute('aria-hidden', 'true'); stars.style.setProperty('--rating', r.puntuacion / 5 * 100 + '%'); stars.textContent = '★★★★★';
      link.append(ratingLabel(r) + ' ', stars, ' ' + r.puntuacion.toLocaleString('es-ES', {minimumFractionDigits: 1}) + ' (' + r.numero_valoraciones.toLocaleString('es-ES') + ')'); link.title = 'Consultado el ' + new Date(r.actualizado_en).toLocaleDateString('es-ES'); box.append(link);
    }
    for (const f of root.querySelectorAll('[data-market-control]')) {
      f.disabled = !market[f.dataset.marketControl].some(f.dataset.marketControl === 'offers' ? validOffer : validRating);
      f.closest('label').hidden = f.disabled;
    }
    for (const o of root.querySelectorAll('[data-sort-market]')) o.disabled = !market[o.dataset.sortMarket].some(o.dataset.sortMarket === 'offers' ? validOffer : validRating);
    for (const f of fields) if ((f.disabled || (f.tagName === 'SELECT' && f.selectedOptions[0]?.disabled)) && f.value) f.value = f.dataset.filter === 'orden' ? 'editorial' : '';

  }
  function matches(card, v) {
      const cats = card.dataset.categories.split(' '), published = card.dataset.published, month = card.dataset.publishedMonth, year = card.dataset.year;
      const formats = new Set([...(card.dataset.formats || '').split(' '), ...offersFor(card.dataset.bookId).map(o => o.formato)]);
      const lower = published || (month ? month + '-01' : year ? year + '-01-01' : '');
      const upper = published || (month ? new Date(Date.UTC(Number(month.slice(0, 4)), Number(month.slice(5)), 0)).toISOString().slice(0, 10) : year ? year + '-12-31' : '');
      const pages = Number(card.dataset.pages), range = !pages ? 'sin-dato' : pages < 200 ? 'breve' : pages < 400 ? 'media' : pages < 600 ? 'larga' : 'muy-larga';
      return normalize(card.dataset.search).includes(searchQuery(v.q || '')) && ['genero', 'tematica', 'temporada', 'edad', 'contenido', 'epoca'].every(k => !pick(v[k]).length || pick(v[k]).some(x => cats.includes(x))) && (!pick(v.grupo).length || pick(v.grupo).includes(card.dataset.group)) && (!pick(v.formato).length || pick(v.formato).some(x => formats.has(x))) && (!v.paginas || v.paginas === range) && (!v.novedad || isNew(published, v.novedad)) && (!v.desde || (upper && upper >= v.desde)) && (!v.hasta || (lower && lower <= v.hasta)) && (!v.valoracion || ratingFor(card.dataset.bookId)?.puntuacion >= Number(v.valoracion)) && priceOk(card, v) && (!v.descuento || matchingOffers(card, v).length > 0);
  }
  // Cada filtro cuenta sus opciones con el resto de filtros aplicados (sin el suyo): una opcion sin libros se atenua y nunca se oculta si esta marcada.
  const cardFacets = new Map(cards.map(card => [card, {}]));
  function facetValues(card, k) {
    const cached = cardFacets.get(card);
    if (k === 'formato') return new Set([...(card.dataset.formats || '').split(' '), ...offersFor(card.dataset.bookId).map(o => o.formato)]);
    return cached[k] || (cached[k] = new Set(k === 'grupo' ? [card.dataset.group] : card.dataset.categories.split(' ')));
  }
  function renderFacets(v) {
    if (!form) return;
    for (const k of FACETS) {
      // El generador omite los grupos sin ninguna categoría con libros.
      const group = form.querySelector('[data-facet-group="' + k + '"]');
      if (!group) continue;
      const own = boxes.filter(b => b.dataset.facet === k);
      const candidates = cards.filter(card => matches(card, {...v, [k]: []}));
      const sets = candidates.map(card => facetValues(card, k));
      for (const box of own) {
        const total = cards.some(card => facetValues(card, k).has(box.value));
        const count = sets.filter(set => set.has(box.value)).length, label = box.closest('label');
        label.hidden = !total && !box.checked;
        label.querySelector('[data-facet-count]').textContent = '(' + count + ')';
        box.disabled = !count && !box.checked;
        label.classList.toggle('is-empty', box.disabled);
        label.dataset.count = count;
      }
      const chosen = own.filter(b => b.checked).length;
      // Marcadas primero; después las que tienen libros (de más a menos, salvo el tipo de libro, que conserva su orden) y al final las vacías.
      const list = group.querySelector('.catalogue-facet__options'), labels = own.map(b => b.closest('label'));
      labels.forEach((label, i) => { if (label.dataset.order == null) label.dataset.order = i; });
      const rank = label => label.querySelector('input').checked ? 0 : label.classList.contains('is-empty') ? 2 : 1;
      const ordered = [...labels].sort((a, b) => rank(a) - rank(b) || (k === 'grupo' ? 0 : b.dataset.count - a.dataset.count) || a.dataset.order - b.dataset.order);
      if (ordered.some((label, i) => list.children[i] !== label)) list.prepend(...ordered);
      const shown = ordered.filter(label => !label.hidden), limit = 8, expanded = group.dataset.expanded === 'true';
      let more = group.querySelector('[data-facet-more]');
      if (shown.length > limit + 2 && !more) {
        more = document.createElement('button'); more.type = 'button'; more.className = 'catalogue-facet__more'; more.dataset.facetMore = '';
        more.addEventListener('click', () => { group.dataset.expanded = group.dataset.expanded === 'true' ? 'false' : 'true'; renderFacets(values()); });
        list.after(more);
      }
      if (more) {
        // Nunca se pliega una opción con libros: solo las vacías que sobran.
        const keep = Math.max(limit, shown.filter(label => !label.classList.contains('is-empty')).length);
        const collapsible = shown.length > keep + 2;
        more.hidden = !collapsible;
        shown.forEach((label, i) => label.classList.toggle('is-collapsed', collapsible && !expanded && i >= keep && !label.querySelector('input').checked));
        more.textContent = expanded ? 'Ver menos' : 'Ver todas (' + shown.length + ')';
        more.setAttribute('aria-expanded', String(expanded));
      }
      group.hidden = own.every(b => b.closest('label').hidden);
      group.querySelector('[data-facet-selected]').textContent = chosen ? '(' + chosen + ' elegidas)' : '';
      if (chosen) group.open = true;
    }
  }
  function apply(save = true) {
    const v = values();
    const nullable = (x, y, desc = false) => x == null ? (y == null ? 0 : 1) : y == null ? -1 : desc ? y - x : x - y;
    const dateOf = card => card.dataset.published || card.dataset.publishedMonth || card.dataset.year ? Date.parse(card.dataset.published || (card.dataset.publishedMonth ? card.dataset.publishedMonth + '-01' : card.dataset.year + '-01-01')) : null;
    const compare = (a, b) => {
      switch (v.orden) {
        case 'titulo': return collator.compare(a.dataset.title, b.dataset.title);
        case 'titulo_desc': return collator.compare(b.dataset.title, a.dataset.title);
        case 'autor': return collator.compare(a.dataset.author, b.dataset.author);
        case 'editorial': case 'fecha_desc': case 'fecha_asc': return nullable(dateOf(a), dateOf(b), v.orden !== 'fecha_asc');
        case 'paginas_asc': case 'paginas_desc': return nullable(Number(a.dataset.pages) || null, Number(b.dataset.pages) || null, v.orden === 'paginas_desc');
        case 'precio_asc': case 'precio_desc': return nullable(minPrice(a, v), minPrice(b, v), v.orden === 'precio_desc');
        case 'valoracion_desc': return nullable(ratingFor(a.dataset.bookId)?.puntuacion ?? null, ratingFor(b.dataset.bookId)?.puntuacion ?? null, true);
        default: return 0;
      }
    };
    const grid = root.querySelector('.catalogue-grid'), sorted = [...cards].sort((a, b) => compare(a, b) || originalOrder.get(a) - originalOrder.get(b));
    if (grid && sorted.some((card, i) => grid.children[i] !== card)) { const fragment = document.createDocumentFragment(); sorted.forEach(card => fragment.append(card)); grid.replaceChildren(fragment); }
    const found = sorted.filter(card => matches(card, v)), visible = found.length;
    renderFacets(v);
    const pages = Math.max(1, Math.ceil(visible / pageSize));
    currentPage = Math.min(currentPage, pages);
    const shown = new Set(found.slice((currentPage - 1) * pageSize, currentPage * pageSize));
    for (const card of cards) card.hidden = !shown.has(card);
    renderPagination(pages, visible);
    if (form) {
      const refineCount = root.querySelector('[data-catalogue-refine-count]');
      if (refineCount) { const active = fields.filter(f => !['q', 'orden'].includes(f.dataset.filter) && f.value && !f.disabled).length + boxes.filter(b => b.checked).length; refineCount.textContent = active ? '· ' + active + (active === 1 ? ' activo' : ' activos') : ''; }
      root.querySelector('[data-catalogue-count]').textContent = visible + (visible === 1 ? ' libro' : ' libros') + (pages > 1 ? ' · página ' + currentPage + ' de ' + pages : ''); root.querySelector('[data-catalogue-empty]').hidden = visible !== 0;
      if (save) { const hash = new URLSearchParams(Object.entries(v).filter(([k, value]) => !FACETS.includes(k) && value && !(k === 'orden' && value === 'editorial'))); for (const k of FACETS) for (const x of v[k]) hash.append(k, x); if (currentPage > 1) hash.set('pagina', String(currentPage)); history.replaceState(null, '', location.pathname + location.search + (hash.size ? '#' + hash : '')); }
      else {
        // Restaurar o refrescar datos puede limitar la página (#pagina=99, vacía o no numérica):
        // se corrige solo esa clave, sin entrada nueva en el historial ni hashchange.
        const hash = new URLSearchParams(location.hash.slice(1)), page = currentPage > 1 ? String(currentPage) : null;
        if (hash.get('pagina') !== page && (hash.has('pagina') || page)) { if (page) hash.set('pagina', page); else hash.delete('pagina'); history.replaceState(history.state, '', location.pathname + location.search + (hash.size ? '#' + hash : '')); }
      }
    }
  }
  function restore() {
    const params = new URLSearchParams(location.hash.slice(1));
    currentPage = Math.max(1, Math.min(100000, Number.parseInt(params.get('pagina'), 10) || 1));
    for (const f of fields) { const v = params.get(f.dataset.filter) || (f.dataset.filter === 'orden' ? 'editorial' : ''); f.value = f.tagName === 'SELECT' && ![...f.options].some(o => o.value === v) ? (f.dataset.filter === 'orden' ? 'editorial' : '') : v; }
    for (const box of boxes) box.checked = params.getAll(box.dataset.facet).includes(box.value);
    const advanced = form?.querySelector('.catalogue-more-filters');
    if (advanced && fields.some(f => advanced.contains(f) && f.value && !f.disabled)) advanced.open = true;
    apply(false);
  }
  function renderPagination(pages) {
    if (!form) return;
    let nav = root.querySelector('[data-catalogue-pagination]');
    if (!nav) {
      nav = document.createElement('nav'); nav.className = 'catalogue-pagination';
      nav.dataset.cataloguePagination = ''; nav.setAttribute('aria-label', 'Páginas del catálogo');
      root.querySelector('.catalogue-grid').after(nav);
    }
    nav.replaceChildren(); nav.hidden = pages <= 1;
    const move = (label, page, disabled) => {
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = label; button.disabled = disabled;
      button.addEventListener('click', () => {
        currentPage = page; apply();
        const heading = root.querySelector('.catalogue-results-head h2');
        heading.tabIndex = -1; heading.focus({preventScroll: true}); heading.scrollIntoView({block: 'start'});
      });
      return button;
    };
    const position = document.createElement('span'); position.textContent = 'Página ' + currentPage + ' de ' + pages;
    nav.append(move('← Anterior', currentPage - 1, currentPage === 1), position, move('Siguiente →', currentPage + 1, currentPage === pages));
  }
  function setupQuiz() {
    if (!form || !cards.length) return;
    const quiz = root.querySelector('.catalogue-quiz');
    if (!quiz) return;
    const panel = quiz.querySelector('.catalogue-quiz__panel');
    panel.replaceChildren();
    let criteria = {}, index = 0, history = [], started = false;
    const optionsFrom = name => FACETS.includes(name) ? boxes.filter(b => b.dataset.facet === name).map(b => ({label: b.nextElementSibling.textContent, values: {[name]: b.value}})) : [...(fields.find(f => f.dataset.filter === name)?.options || [])].filter(o => o.value && !o.disabled).map(o => ({label: o.textContent, values: {[name]: o.value}}));
    const steps = [
      {key: 'novedad', question: '¿Buscas algo recién publicado?', options: () => [
        {label: 'Sí, una novedad', values: {novedad: '15'}},
        {label: 'Un próximo lanzamiento', values: {novedad: 'proximamente'}},
        {label: 'Un clásico', values: {epoca: 'clasicos'}}]},
      {key: 'temporada', question: '¿Te apetece una lectura de temporada?', options: () => optionsFrom('temporada')},
      {key: 'genero', question: '¿Qué género te apetece?', options: () => optionsFrom('genero')},
      {key: 'tematica', question: '¿Hay algún tema que te interese?', options: () => optionsFrom('tematica')},
      {key: 'edad', question: '¿Para quién buscas el libro?', options: () => optionsFrom('edad')},
      {key: 'paginas', question: '¿Cuánto te apetece leer?', options: () => optionsFrom('paginas')},
      {key: 'formato', question: '¿Tienes un formato en mente?', options: () => optionsFrom('formato')},
      {key: 'valoracion', question: '¿Quieres priorizar las valoraciones de lectores?', options: () => optionsFrom('valoracion')},
      {key: 'precio_max', question: '¿Qué presupuesto prefieres?', options: () => [10, 20, 30].map(price => ({label: 'Hasta ' + price + ' €', values: {precio_max: String(price)}}))}
    ];
    const usable = step => step.options().filter(o => cards.some(card => matches(card, {...criteria, ...o.values})));
    const button = (label, action) => {
      const element = document.createElement('button'); element.type = 'button'; element.textContent = label;
      element.addEventListener('click', action); return element;
    };
    const reset = () => { criteria = {}; index = 0; history = []; render(); };
    function render() {
      panel.replaceChildren();
      while (index < steps.length && !usable(steps[index]).length) index++;
      const count = cards.filter(card => matches(card, criteria)).length;
      const status = document.createElement('p'); status.className = 'catalogue-quiz__progress'; status.setAttribute('role', 'status');
      const heading = document.createElement('h2'); heading.tabIndex = -1;
      const choices = document.createElement('div'); choices.className = 'catalogue-quiz__choices';
      if (index < steps.length) {
        const total = history.length + steps.slice(index).filter(step => usable(step).length).length;
        status.textContent = 'Pregunta ' + (history.length + 1) + ' de ' + total + ' · ' + count + ' libros disponibles';
        heading.textContent = steps[index].question;
        for (const option of [...usable(steps[index]), {label: 'Me da igual, continuar', values: {}}]) {
          choices.append(button(option.label, () => {
            history.push({index, criteria: {...criteria}}); criteria = {...criteria, ...option.values}; index++; render();
          }));
        }
      } else {
        status.textContent = count + (count === 1 ? ' libro encaja con tus respuestas' : ' libros encajan con tus respuestas');
        heading.textContent = count ? 'Tu próxima lectura te espera' : 'Los datos han cambiado. Prueba otra selección';
        if (count) choices.append(button('Ver mis resultados', () => {
          for (const field of fields) field.value = criteria[field.dataset.filter] || (field.dataset.filter === 'orden' ? 'editorial' : '');
          for (const box of boxes) box.checked = pick(criteria[box.dataset.facet]).includes(box.value);
          currentPage = 1; apply(); quiz.open = false;
          const result = root.querySelector('.catalogue-results-head h2'); result.tabIndex = -1; result.focus({preventScroll: true}); result.scrollIntoView({block: 'start'});
        }));
      }
      const actions = document.createElement('div'); actions.className = 'catalogue-filter-actions';
      if (history.length) actions.append(button('← Volver', () => { const previous = history.pop(); index = previous.index; criteria = previous.criteria; render(); }));
      actions.append(button('Empezar de nuevo', reset));
      panel.append(status, heading, choices, actions); heading.focus({preventScroll: true});
    }
    quiz.addEventListener('toggle', () => { if (quiz.open && !started) { started = true; render(); } });
  }
  if (form) {
    form.querySelector('fieldset').disabled = false; form.querySelector('[type="reset"]').disabled = false;
    const sort = root.querySelector('[data-filter="orden"]'); if (sort) sort.disabled = false;
    const refineToggle = form.querySelector('[data-catalogue-refine-toggle]'), refine = form.querySelector('[data-catalogue-refine]');
    if (refineToggle && refine) {
      const setRefine = open => { refine.toggleAttribute('data-open', open); refineToggle.setAttribute('aria-expanded', String(open)); };
      refineToggle.addEventListener('click', () => setRefine(!refine.hasAttribute('data-open')));
      // Escape cierra el panel móvil y devuelve el foco al botón (el <details> de «Más filtros» tiene prioridad).
      refine.addEventListener('keydown', event => { if (event.key === 'Escape' && getComputedStyle(refineToggle).display !== 'none') { event.preventDefault(); setRefine(false); refineToggle.focus(); } });
    }
    fields.forEach(f => f.addEventListener('input', () => { currentPage = 1; apply(); }));
    boxes.forEach(b => b.addEventListener('change', () => { currentPage = 1; apply(); }));
    form.addEventListener('submit', event => { event.preventDefault(); currentPage = 1; apply(); }); form.addEventListener('reset', () => setTimeout(() => { currentPage = 1; apply(); }, 0)); window.addEventListener('hashchange', restore); restore();
  }
  const refresh = () => { renderNovelty(); renderMarket(); apply(false); };
  window.addEventListener('pageshow', refresh); document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); }); setInterval(() => { if (!document.hidden) refresh(); }, 60000);
  const knownIds = new Set([...root.querySelectorAll('[data-rating-book]')].map(el => el.dataset.ratingBook));
  fetch('/assets/reading-market.json', { cache: 'no-store' }).then(r => r.ok ? r.json() : null).then(p => { if (p?.schema_version === 1 && Array.isArray(p.offers) && Array.isArray(p.ratings)) { market = { offers: p.offers.filter(o => o && typeof o === 'object' && knownIds.has(o.libro_id)), ratings: p.ratings.filter(r => r && typeof r === 'object' && knownIds.has(r.libro_id)) }; renderMarket(); restore(); } }).catch(() => { /* The static catalogue stays available. */ }); refresh();
  setupQuiz();
  if (document.fonts) document.fonts.load('1em "CatalogueNovelty"').then(faces => { root.classList.add(faces.length ? 'catalogue-fonts-ready' : 'catalogue-fonts-failed'); }).catch(() => root.classList.add('catalogue-fonts-failed'));
  else root.classList.add('catalogue-fonts-failed');
})();
