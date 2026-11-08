/* Static books and purchase links work without JS; optional market data expires. */
(async () => {
  'use strict';
  const root = document.querySelector('[data-reading-catalogue]');
  if (!root) return;
  // Small, linked static pages remain usable without JS. Enhance the hub only
  // after every page of this exact catalogue snapshot has been loaded.
  const staticNav = root.querySelector('[data-catalogue-static-pagination]');
  const continuation = [...(staticNav?.querySelectorAll('a[data-catalogue-page]') || [])];
  // El catálogo completo (todas las páginas) se descarga e indexa al primer uso de filtros, buscador o test, o al
  // cargar con un estado en la URL (#…). Antes, la primera página ya lleva novedad, valoraciones y precios del día.
  const hydrate = async () => {
    const localCards = [...root.querySelectorAll('[data-catalogue-book]')];
    // Páginas en paralelo y con un reintento: en serie, un móvil tardaba ~10 s en poder filtrar.
    const readPage = async (link, attempt = 0) => {
      const url = new URL(link.href, location.href);
      if (url.origin !== location.origin || !/^\/recomendaciones\/pagina\/[1-9]\d*\/$/.test(url.pathname) || url.search || url.hash) throw new Error('Invalid catalogue page');
      try {
        const response = await fetch(url.href, { cache: 'no-cache', signal: AbortSignal.timeout(30000) });
        if (!response.ok || !response.headers.get('content-type')?.includes('text/html')) throw new Error('Catalogue unavailable');
        const page = new DOMParser().parseFromString(await response.text(), 'text/html');
        const canonical = new URL(url.pathname, document.querySelector('link[rel=canonical]').href).href;
        const version = page.querySelector('[data-catalogue-version]')?.dataset.catalogueVersion;
        if (page.querySelector('link[rel=canonical]')?.href !== canonical) throw new Error('Invalid catalogue page');
        return { version, cards: [...page.querySelectorAll('.catalogue-grid > [data-catalogue-book]')] };
      } catch (error) {
        if (attempt || error.message === 'Invalid catalogue page') throw error;
        return readPage(link, 1);
      }
    };
    try {
      const pages = await Promise.all(continuation.map(link => readPage(link)));
      if (pages.some(page => page.version !== root.dataset.catalogueVersion)) {
        // Tras cada publicación, el navegador puede servir esta página desde su caché (10 min en Pages)
        // y las demás ya nuevas: se recarga una vez, revalidando, en vez de dejar el catálogo sin filtros.
        const target = String(pages.find(page => page.version !== root.dataset.catalogueVersion).version);
        let retry = false;
        try { retry = sessionStorage.getItem('catalogue-reload') !== target; sessionStorage.setItem('catalogue-reload', target); } catch { /* sin almacenamiento: no se recarga */ }
        // Tras recargar sigue la descarga sin esperar otro gesto: el lector ya había empezado a filtrar.
        if (retry) { try { sessionStorage.setItem('catalogue-hydrate', '1'); } catch { /* opcional */ } location.reload(); return false; }
        throw new Error('Catalogue changed');
      }
      try { sessionStorage.removeItem('catalogue-reload'); } catch { /* opcional */ }
      const parts = pages.flatMap(page => page.cards);
      const original = [...root.querySelectorAll('[data-catalogue-book]')];
      const ids = new Set([...original, ...parts].map(card => card.dataset.bookId));
      if (ids.has(undefined) || ids.size !== original.length + parts.length || ids.size !== Number(root.dataset.catalogueTotal)) throw new Error('Incomplete catalogue');
      const fragment = document.createDocumentFragment();
      for (const card of parts) { card.hidden = true; fragment.append(card); }
      root.querySelector('.catalogue-grid').append(fragment);
      // Solo con el catálogo completo se pasa a la paginación de 24: si falla, sigue la página estática entera.
      localCards.slice(24).forEach(card => { card.hidden = true; });
    } catch {
      localCards.forEach(card => { card.hidden = false; });
      const count = root.querySelector('[data-catalogue-count]');
      if (count) count.textContent = 'No se pudo preparar la búsqueda completa. Puedes recorrer las páginas del catálogo.';
      return false;
    }
    if (staticNav) { staticNav.hidden = true; staticNav.classList.remove('catalogue-pagination'); }
    return true;
  };
  if (!continuation.length && staticNav) { staticNav.hidden = true; staticNav.classList.remove('catalogue-pagination'); }
  const FACET_SEARCH_FROM = 8; // opciones a partir de las cuales el filtro lleva buscador propio
  const normalize = s => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es').replace(/,/g, ' ').replace(/\s+/g, ' ').trim();
  // Solo los ISBN-13 completos admiten separadores y prefijos de presentación.
  const searchQuery = s => {
    const candidate = s.trim().replace(/^ISBN(?:-13)?\s*:?\s*/i, '');
    return /^97[89](?:[\s-]*\d){10}$/.test(candidate) ? candidate.replace(/[\s-]/g, '') : normalize(s);
  };
  const form = root.querySelector('[data-catalogue-filters]');
  let cards, searchIndex, originalOrder, hasDiscounts;
  const indexCards = () => {
    cards = [...root.querySelectorAll('[data-catalogue-book]')];
    // Reuse full title, authors and ISBN. Support cached HTML with data-search.
    searchIndex = new Map(cards.map(card => [card, normalize(card.dataset.search || `${card.dataset.title} ${card.dataset.author} ${card.querySelector('[data-isbn]')?.dataset.isbn || ''}`)]));
    originalOrder = new Map(cards.map((card, i) => [card, i]));
    hasDiscounts = cards.some(card => card.dataset.formatDiscounts);
  };
  indexCards();
  const fields = form ? [...form.elements].filter(f => f.dataset.filter) : [];
  // Filtros con varias opciones a la vez (OR dentro de cada uno, AND entre ellos), como casillas.
  const FACETS = ['grupo', 'genero', 'tematica', 'temporada', 'edad', 'contenido', 'formato'];
  const boxes = form ? [...form.querySelectorAll('input[data-facet]')] : [];
  const FIXED_ORDER = ['grupo', 'edad', 'formato'];
  const pick = x => Array.isArray(x) ? x : x ? [x] : [];
  let market = { offers: [], ratings: [], sales_ranks: [] };
  let currentPage = 1;
  const pageSize = 24;
  let offersIndex = new Map(), ratingsIndex = new Map(), ranksIndex = new Map();
  const stamp = s => typeof s === 'string' && /T.*(?:Z|[+-]\d\d:\d\d)$/.test(s) ? Date.parse(s) : NaN;
  const fresh = (e, hours) => { const start = stamp(e.actualizado_en), end = stamp(e.caduca_en), now = Date.now(); return Number.isFinite(start) && Number.isFinite(end) && start <= now && end > now && end > start && end - start <= hours * 3600000 && now - start <= hours * 3600000; };
  const safeURL = (raw, hosts, path) => { try { const u = new URL(raw); return u.protocol === 'https:' && !u.username && !u.password && !u.port && hosts.includes(u.hostname) && path.test(u.pathname) ? u : null; } catch { return null; } };
  const validOffer = o => { const u = safeURL(o.url, ['amazon.es', 'www.amazon.es'], /\/(?:dp|gp\/product)\/[A-Z0-9]{10}(?:\/|$)/); return fresh(o, 24) && o.moneda === 'EUR' && o.tipo === 'compra' && ['tapa-blanda', 'tapa-dura', 'ebook', 'audiolibro'].includes(o.formato) && Number.isSafeInteger(o.precio_centimos) && o.precio_centimos > 0 && o.precio_centimos < 100000000 && u && /^[A-Za-z0-9-]+$/.test(u.searchParams.get('tag') || ''); };
  // Puesto en Libros de Amazon.es; renderMarket revalida la caducidad cada minuto.
  const validRank = r => fresh(r, 216) && r.fuente === 'amazon_es_books' && Number.isSafeInteger(r.posicion) && r.posicion > 0 && r.posicion < 1e8;
  const rankFor = id => ranksIndex.get(id)?.posicion ?? null;
  const ratingSource = r => ['google_books', 'hardcover', 'amazon'].includes(r.fuente) ? r.fuente : !r.fuente || r.fuente === 'goodreads' ? 'goodreads' : null;
  const ratingLabel = r => ({google_books: 'Google Books', hardcover: 'Hardcover', amazon: 'Amazon'})[ratingSource(r)] || 'Goodreads';
  const validRating = r => {
    if (!fresh(r, 720) || !Number.isFinite(r.puntuacion) || r.puntuacion < 1 || r.puntuacion > 5 || !Number.isSafeInteger(r.numero_valoraciones) || r.numero_valoraciones < 5) return false; // una sola valoración no es una referencia
    const source = ratingSource(r);
    if (source === 'goodreads') return Boolean(safeURL(r.url, ['www.goodreads.com', 'goodreads.com'], /^\/book\/show\/\d/));
    if (source === 'google_books') { const link = safeURL(r.url, ['books.google.com'], /^\/books$/); return Boolean(link && /^[A-Za-z0-9_-]{1,150}$/.test(link.searchParams.get('id') || '')); }
    if (source === 'hardcover') return Boolean(safeURL(r.url, ['hardcover.app', 'www.hardcover.app'], /^\/books\/[a-z0-9]+(?:-[a-z0-9]+)*$/));
    if (source === 'amazon') return Boolean(safeURL(r.url, ['www.amazon.es', 'amazon.es'], /^\/dp\/[A-Z0-9]{10}$/));
    return false;
  };
  // Muestra de 1–4 valoraciones con fuente y vigencia válidas: existe, pero no es una nota fiable.
  const thinRating = r => Number.isSafeInteger(r.numero_valoraciones) && r.numero_valoraciones >= 1 && r.numero_valoraciones < 5 && validRating({...r, numero_valoraciones: 5});
  const discount = o => Number.isSafeInteger(o.precio_referencia_centimos) && o.precio_referencia_centimos > o.precio_centimos ? Math.round((o.precio_referencia_centimos - o.precio_centimos) / o.precio_referencia_centimos * 100) : 0;
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
  const isNew = (s, window) => { const days = ageDays(s); return window === 'proximamente' ? days < 0 : days >= 0 && (window === '15' ? days < 15 : days <= Number(window)); };
  function renderNovelty() {
    for (const label of root.querySelectorAll('[data-release-label]')) {
      const fresh = isNew(label.dataset.releaseLabel, '30'),  // contrato: «Novedad» un mes (NOVELTY_DAYS)
      upcoming = !fresh && isNew(label.dataset.releaseLabel, 'proximamente');
      const text = fresh ? 'Novedad' : upcoming ? 'Pr\u00f3ximamente' : '';
      if (label.dataset.releaseFallback !== undefined) {
        const shown = text || label.dataset.releaseFallback;
        if (label.textContent !== shown) label.textContent = shown;
        label.classList.toggle('catalogue-novelty', fresh || upcoming);
      } else { if (label.textContent !== text) label.textContent = text; if (label.hidden !== !text) label.hidden = !text; }
    }
  }
  const values = () => ({...Object.fromEntries(fields.map(f => [f.dataset.filter, f.disabled ? '' : f.value])), ...Object.fromEntries(FACETS.map(k => [k, boxes.filter(b => b.dataset.facet === k && b.checked).map(b => b.value)]))});
  // «formato:%:fecha»: sin reconfirmar en OFFER_MAX_DAYS, la oferta caduca.
  const OFFER_MAX_DAYS = 3;
  const offerCurrent = checked => /^\d{4}-\d{2}-\d{2}$/.test(checked || '') && (Date.parse(madridDate.format(new Date())) - Date.parse(checked)) / 864e5 <= OFFER_MAX_DAYS;
  const formatDiscounts = card => (card.dataset.formatDiscounts || '').split(' ').filter(Boolean).map(x => x.split(':')).filter(([, , checked]) => offerCurrent(checked)).map(([formato, pct]) => ({formato, pct: Number(pct)}));
  // Temporada: oferta vigente de 10 % o más.
  // Caché por versión de mercado (renderMarket la invalida): recalcular en cada clic disparaba el INP.
  let memo = new Map();
  const memoFor = card => { let m = memo.get(card); if (!m) memo.set(card, m = {}); return m; };
  const cardCategories = card => { const m = memoFor(card); return m.cats || (m.cats = [...card.dataset.categories.split(' '), ...(formatDiscounts(card).some(o => o.pct >= 10) ? ['ofertas-amazon'] : [])]); };
  const cardFormats = card => { const m = memoFor(card); return m.formats || (m.formats = new Set([...(card.dataset.formats || '').split(' '), ...offersFor(card.dataset.bookId).map(o => o.formato)])); };
  // Insignias de oferta sin reconfirmar: fuera en la página inicial y en las fichas que trae la hidratación.
  const pruneOffers = () => { for (const badge of root.querySelectorAll('[data-offer-checked]')) if (!offerCurrent(badge.dataset.offerChecked)) badge.remove(); };
  pruneOffers();
  const matchingOffers = (card, v) => [...offersFor(card.dataset.bookId).map(o => ({formato: o.formato, pct: discount(o)})), ...formatDiscounts(card)].filter(o => (!pick(v.formato).length || pick(v.formato).includes(o.formato)) && (!v.descuento || o.pct >= Number(v.descuento)));
  // Por defecto, solo publicados; los próximos se piden o se buscan.
  const released = (lower) => !lower || lower <= today();
  const ratingOk = (card, v) => { if (!v.valoracion) return true; const r = ratingFor(card.dataset.bookId)?.puntuacion; return r != null && (v.valoracion === 'menos-3' ? r < 3 : r >= Number(v.valoracion)); };
  // Precio por formato («ebook:999»): nunca se mezcla Kindle con papel.
  const formatPrices = card => new Map((card.dataset.formatPrices || '').split(' ').filter(Boolean).map(x => x.split(':')).map(([f, c]) => [f, Number(c)]));
  // Formato: el del precio, si no los de «Formato», si no cualquiera.
  const priceFormats = v => v.precio_formato ? [v.precio_formato] : pick(v.formato);
  const priceOf = (card, formats) => { const prices = [...formatPrices(card)].filter(([f]) => !formats.length || formats.includes(f)).map(([, c]) => c); return prices.length ? Math.min(...prices) : null; };
  const priceOk = (card, v) => {
    if (!v.precio_min && !v.precio_max) return true;
    const min = v.precio_min ? Math.round(Number(v.precio_min) * 100) : 0, max = v.precio_max ? Math.round(Number(v.precio_max) * 100) : Infinity, formats = priceFormats(v);
    return [...formatPrices(card)].some(([f, c]) => (!formats.length || formats.includes(f)) && c >= min && c <= max);
  };
  const ratingKeys = new WeakMap();
  function renderMarket() {
    offersIndex = new Map(); ratingsIndex = new Map(); ranksIndex = new Map(); memo = new Map();
    for (const r of market.sales_ranks.filter(validRank)) if (!ranksIndex.has(r.libro_id) || ranksIndex.get(r.libro_id).posicion > r.posicion) ranksIndex.set(r.libro_id, r);
    for (const offer of market.offers.filter(validOffer)) {
      if (!offersIndex.has(offer.libro_id)) offersIndex.set(offer.libro_id, []);
      offersIndex.get(offer.libro_id).push(offer);
    }
    const priority = {goodreads: 0, amazon: 1, hardcover: 2, google_books: 3};
    for (const rating of market.ratings.filter(validRating).sort((a, b) => priority[ratingSource(a)] - priority[ratingSource(b)])) {
      if (!ratingsIndex.has(rating.libro_id)) ratingsIndex.set(rating.libro_id, []);
      ratingsIndex.get(rating.libro_id).push(rating);
    }
    for (const box of root.querySelectorAll('[data-rating-book]')) {
      const r = ratingFor(box.dataset.ratingBook);
      const thinNow = r ? null : market.ratings.find(x => x.libro_id === box.dataset.ratingBook && thinRating(x));
      // Mismo contenido que en la pasada anterior: no se toca el DOM (cada minuto se revalida la caducidad).
      const key = r ? ['v', r.url, r.puntuacion, r.numero_valoraciones, r.actualizado_en, ratingSource(r)].join('|') : thinNow ? ['t', thinNow.url, thinNow.actualizado_en, ratingSource(thinNow)].join('|') : 'n|' + (box.dataset.isbn || '');
      if (ratingKeys.get(box) === key) continue;
      ratingKeys.set(box, key);
      box.replaceChildren(); box.hidden = false;
      if (!r) {
        // Sin nota verificada vigente no se pinta nota (ni estrellas vacías ni «0,0 (0)»).
        const thin = thinNow;
        const isbn = /^\d{13}$/.test(box.dataset.isbn) && box.dataset.isbn;
        // Sin nota verificada, la tarjeta no muestra nada; la ficha ofrece el enlace a Goodreads por ISBN (David, 2026-11-08).
        if (box.closest('.catalogue-card')) box.hidden = true;
        else if (thin || isbn) {
          const ref = document.createElement('a'); ref.target = '_blank'; ref.rel = 'noopener noreferrer'; ref.className = 'catalogue-rating__ref';
          if (thin) { ref.href = thin.url; ref.dataset.ratingState = 'insufficient'; ref.textContent = ratingLabel(thin) + ' · menos de 5 valoraciones'; ref.title = 'Muestra demasiado pequeña para mostrar una nota. Consultado el ' + new Date(thin.actualizado_en).toLocaleDateString('es-ES'); }
          else { ref.href = 'https://www.goodreads.com/book/isbn/' + isbn; ref.dataset.ratingState = 'unavailable'; ref.textContent = 'Goodreads · ver opiniones'; }
          box.append(ref);
        } else box.hidden = true;
        continue;
      }
      const link = document.createElement('a'); link.href = r.url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.dataset.ratingState = 'verified';
      const stars = document.createElement('span'); stars.className = 'catalogue-stars'; stars.setAttribute('aria-hidden', 'true'); stars.style.setProperty('--rating', r.puntuacion / 5 * 100 + '%'); stars.textContent = '★★★★★';
      link.append(ratingLabel(r) + ' ', stars, ' ' + r.puntuacion.toLocaleString('es-ES', {minimumFractionDigits: 1}) + ' (' + r.numero_valoraciones.toLocaleString('es-ES') + ')'); link.title = 'Consultado el ' + new Date(r.actualizado_en).toLocaleDateString('es-ES'); box.append(link);
    }
    for (const f of root.querySelectorAll('[data-market-control]')) {
      f.disabled = !(f.dataset.marketControl === 'offers' && hasDiscounts) && !market[f.dataset.marketControl].some(f.dataset.marketControl === 'offers' ? validOffer : validRating);
      f.closest('label').hidden = f.disabled;
    }
    // Umbral sin libros: desactivado.
    const best = Math.max(0, ...cards.map(card => Math.max(0, ...matchingOffers(card, {}).map(o => o.pct))));
    for (const o of root.querySelectorAll('[data-filter="descuento"] option')) if (o.value) o.disabled = Number(o.value) > best;
    const valid = {offers: validOffer, ratings: validRating, sales_ranks: validRank};
    for (const o of root.querySelectorAll('[data-sort-market]')) { const k = o.dataset.sortMarket; o.disabled = !market[k]?.some(valid[k]); o.hidden = o.disabled && k === 'sales_ranks'; }
    for (const f of fields) if ((f.disabled || (f.tagName === 'SELECT' && f.selectedOptions[0]?.disabled)) && f.value) f.value = f.dataset.filter === 'orden' ? 'editorial' : '';

  }
  let lastQuery = null, lastNormalized = '';
  const queryOf = v => { const q = v.q || ''; if (q !== lastQuery) { lastQuery = q; lastNormalized = searchQuery(q); } return lastNormalized; };
  const boundsOf = card => { const m = memoFor(card); if (m.lower == null) { const published = card.dataset.published, month = card.dataset.publishedMonth, year = card.dataset.year; m.lower = published || (month ? month + '-01' : year ? year + '-01-01' : ''); m.upper = published || (month ? new Date(Date.UTC(Number(month.slice(0, 4)), Number(month.slice(5)), 0)).toISOString().slice(0, 10) : year ? year + '-12-31' : ''); } return m; };
  const lowerOf = card => boundsOf(card).lower;
  const rangeOf = card => { const pages = Number(card.dataset.pages); return !pages ? '' : pages < 200 ? 'breve' : pages < 400 ? 'media' : pages < 600 ? 'larga' : 'muy-larga'; };
  // Condiciones que no son casillas: búsqueda, estado, extensión, fechas, nota, precio y descuento.
  const baseMatch = (card, v) => searchIndex.get(card).includes(queryOf(v)) && (v.estado === 'todos' || (!v.estado && v.q) || (v.estado === 'proximos' ? !released(lowerOf(card)) : released(lowerOf(card)))) && (!v.paginas || v.paginas === rangeOf(card)) && (!v.novedad || isNew(card.dataset.published, v.novedad)) && (!v.desde || (boundsOf(card).upper && boundsOf(card).upper >= v.desde)) && (!v.hasta || (lowerOf(card) && lowerOf(card) <= v.hasta)) && ratingOk(card, v) && priceOk(card, v) && (!v.descuento || matchingOffers(card, v).length > 0);
  const facetMatch = (card, v, k) => {
    const chosen = pick(v[k]);
    if (!chosen.length) return true;
    if (k === 'grupo') return chosen.includes(card.dataset.group);
    if (k === 'formato') { const formats = cardFormats(card); return chosen.some(x => formats.has(x)); }
    const cats = cardCategories(card); return chosen.some(x => cats.includes(x));
  };
  function matches(card, v) {
    return baseMatch(card, v) && FACETS.every(k => facetMatch(card, v, k));
  }
  // Cada filtro cuenta con los demás aplicados: una opción sin libros se atenúa (si está marcada, no se oculta).
  function facetValues(card, k) {
    if (k === 'formato') return cardFormats(card);
    const m = memoFor(card), key = k === 'grupo' ? 'groupSet' : 'catSet';
    return m[key] || (m[key] = new Set(k === 'grupo' ? [card.dataset.group] : cardCategories(card)));
  }
  function renderFacets(v) {
    if (!form) return;
    const typed = pick(v.grupo).length > 0;
    // Una ficha cuenta para la faceta k si cumple todo salvo, como mucho, la propia k.
    const totalsBy = new Map(FACETS.map(k => [k, new Set()])), countsBy = new Map(FACETS.map(k => [k, new Map()]));
    for (const card of cards) {
      for (const k of FACETS) for (const x of facetValues(card, k)) totalsBy.get(k).add(x);
      if (!baseMatch(card, v)) continue;
      const failing = FACETS.filter(k => !facetMatch(card, v, k));
      if (failing.length > 1) continue;
      for (const k of failing.length ? failing : FACETS) { const counts = countsBy.get(k); for (const x of facetValues(card, k)) counts.set(x, (counts.get(x) || 0) + 1); }
    }
    for (const k of FACETS) {
      // El generador omite los grupos sin ninguna categoría con libros.
      const group = form.querySelector('[data-facet-group="' + k + '"]');
      if (!group) continue;
      const own = boxes.filter(b => b.dataset.facet === k);
      // Buscador en filtros largos: acota la lista, no la selección.
      let finder = group.querySelector('[data-facet-search]');
      if (!finder && own.length > FACET_SEARCH_FROM) {
        finder = document.createElement('input'); finder.type = 'search'; finder.className = 'catalogue-facet__search'; finder.dataset.facetSearch = '';
        const name = group.querySelector('summary').firstChild.textContent.trim();
        finder.placeholder = 'Buscar en ' + name.toLocaleLowerCase('es') + '…'; finder.setAttribute('aria-label', 'Buscar opciones de ' + name.toLocaleLowerCase('es'));
        finder.addEventListener('input', () => renderFacets(values()));
        finder.addEventListener('keydown', e => { if (e.key === 'Enter') e.preventDefault(); });
        group.querySelector('.catalogue-facet__options').before(finder);
      }
      const query = finder ? normalize(finder.value) : '';
      const totals = totalsBy.get(k), counts = countsBy.get(k);
      for (const box of own) {
        const total = totals.has(box.value);
        const count = counts.get(box.value) || 0, label = box.closest('label');
        // Con un tipo de libro elegido solo quedan las opciones de ese tipo (Novela → sus géneros).
        const hide = (!total || (typed && k !== 'grupo' && !count) || (query && !normalize(label.textContent).includes(query))) && !box.checked;
        if (label.hidden !== hide) label.hidden = hide;
        const badge = label.querySelector('[data-facet-count]'), text = '(' + count + ')';
        if (badge.textContent !== text) badge.textContent = text;
        const off = !count && !box.checked;
        if (box.disabled !== off) box.disabled = off;
        label.classList.toggle('is-empty', off);
        if (label.dataset.count !== String(count)) label.dataset.count = count;
      }
      const chosen = own.filter(b => b.checked).length;
      // Marcadas, luego con libros, vacías al final.
      const list = group.querySelector('.catalogue-facet__options'), labels = own.map(b => b.closest('label'));
      labels.forEach((label, i) => { if (label.dataset.order == null) label.dataset.order = i; });
      const rank = label => label.querySelector('input').checked ? 0 : label.classList.contains('is-empty') ? 2 : 1;
      const ordered = [...labels].sort((a, b) => rank(a) - rank(b) || (FIXED_ORDER.includes(k) ? 0 : b.dataset.count - a.dataset.count) || a.dataset.order - b.dataset.order);
      if (ordered.some((label, i) => list.children[i] !== label)) list.prepend(...ordered);
      const shown = ordered.filter(label => !label.hidden), limit = 8, expanded = group.dataset.expanded === 'true' || Boolean(query);
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
      group.hidden = !query && own.every(b => b.closest('label').hidden);
      group.querySelector('[data-facet-selected]').textContent = chosen ? '(' + chosen + ' elegidas)' : '';
      if (chosen) group.open = true;
    }
  }
  let facetJob = 0;
  function apply(save = true) {
    const v = values();
    const nullable = (x, y, desc = false) => x == null ? (y == null ? 0 : 1) : y == null ? -1 : desc ? y - x : x - y;
    const dateOf = card => { const m = memoFor(card); if (m.date === undefined) m.date = card.dataset.published || card.dataset.publishedMonth || card.dataset.year ? Date.parse(card.dataset.published || (card.dataset.publishedMonth ? card.dataset.publishedMonth + '-01' : card.dataset.year + '-01-01')) : null; return m.date; };
    const rating = card => ratingFor(card.dataset.bookId)?.puntuacion ?? null;
    const compare = (a, b) => {
      // Orden por defecto adaptado: con un filtro de valoración, de menos a más estrellas (3, 3,5, 4…);
      // en próximos lanzamientos, el más cercano primero.
      if (v.orden === 'editorial' && v.valoracion) return nullable(rating(a), rating(b)) || nullable(dateOf(a), dateOf(b), true);
      if (v.orden === 'editorial' && v.estado === 'proximos') return nullable(dateOf(a), dateOf(b));
      switch (v.orden) {
        case 'editorial': case 'fecha_desc': case 'fecha_asc': return nullable(dateOf(a), dateOf(b), v.orden !== 'fecha_asc');
        case 'paginas_asc': case 'paginas_desc': return nullable(Number(a.dataset.pages) || null, Number(b.dataset.pages) || null, v.orden === 'paginas_desc');
        case 'precio_tapa-dura': case 'precio_tapa-blanda': case 'precio_ebook': case 'precio_audiolibro': { const format = [v.orden.slice(7)]; return nullable(priceOf(a, format), priceOf(b, format)); }
        // Con puesto primero; el resto, por fecha.
        case 'ventas': return nullable(rankFor(a.dataset.bookId), rankFor(b.dataset.bookId)) || nullable(dateOf(a), dateOf(b), true);
        case 'valoracion_desc': return nullable(ratingFor(a.dataset.bookId)?.puntuacion ?? null, ratingFor(b.dataset.bookId)?.puntuacion ?? null, true);
        default: return 0;
      }
    };
    // Filtrar antes de ordenar: solo se ordenan los resultados.
    const grid = root.querySelector('.catalogue-grid'), found = cards.filter(card => matches(card, v)).sort((a, b) => compare(a, b) || originalOrder.get(a) - originalOrder.get(b)), visible = found.length;
    // Recuentos de facetas tras el pintado (INP).
    const job = ++facetJob;
    root.dataset.facetsPending = 'true';
    requestAnimationFrame(() => setTimeout(() => { if (job === facetJob) { renderFacets(values()); delete root.dataset.facetsPending; } }, 0));
    const pages = Math.max(1, Math.ceil(visible / pageSize));
    currentPage = Math.min(currentPage, pages);
    const page = found.slice((currentPage - 1) * pageSize, currentPage * pageSize), shown = new Set(page);
    // Mover todas las fichas en cada clic hacía que Clarity reserializara ~90.000 nodos: solo se mueven las de la página.
    if (grid && page.some((card, i) => grid.children[i] !== card)) grid.prepend(...page);
    for (const card of cards) { const hide = !shown.has(card); if (card.hidden !== hide) card.hidden = hide; }
    renderPagination(pages, visible);
    if (form) {
      const refineCount = root.querySelector('[data-catalogue-refine-count]');
      const upcomingLink = root.querySelector('[data-catalogue-upcoming]'); if (upcomingLink) upcomingLink.hidden = v.estado === 'proximos' || v.estado === 'todos';
      if (refineCount) { const active = fields.filter(f => !['q', 'orden', 'estado'].includes(f.dataset.filter) && f.value && !f.disabled).length + boxes.filter(b => b.checked).length; refineCount.textContent = active ? '· ' + active + (active === 1 ? ' activo' : ' activos') : ''; }
      root.querySelector('[data-catalogue-count]').textContent = visible + (visible === 1 ? ' libro' : ' libros') + (pages > 1 ? ' · página ' + currentPage + ' de ' + pages : ''); root.querySelector('[data-catalogue-empty]').hidden = visible !== 0;
      if (save) { const hash = new URLSearchParams(Object.entries(v).filter(([k, value]) => !FACETS.includes(k) && value && !(k === 'orden' && value === 'editorial'))); for (const k of FACETS) for (const x of v[k]) hash.append(k, x); if (currentPage > 1) hash.set('pagina', String(currentPage)); history.replaceState(null, '', location.pathname + location.search + (hash.size ? '#' + hash : '')); }
      else {
        // #pagina fuera de rango: se corrige sin historial ni hashchange.
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
    // Números pulsables: primera, última y las vecinas de la actual; el resto se resume con «…».
    const numbers = document.createElement('span'); numbers.className = 'catalogue-pagination__pages';
    let last = 0;
    for (let page = 1; page <= pages; page++) {
      if (page !== 1 && page !== pages && Math.abs(page - currentPage) > 1) continue;
      if (page - last > 1) { const gap = document.createElement('span'); gap.className = 'catalogue-pagination__gap'; gap.setAttribute('aria-hidden', 'true'); gap.textContent = '…'; numbers.append(gap); }
      const number = move(String(page), page, false); number.setAttribute('aria-label', 'Página ' + page);
      if (page === currentPage) number.setAttribute('aria-current', 'page');
      numbers.append(number); last = page;
    }
    const position = document.createElement('span'); position.className = 'catalogue-pagination__position'; position.textContent = 'Página ' + currentPage + ' de ' + pages;
    nav.append(move('← Anterior', currentPage - 1, currentPage === 1), numbers, move('Siguiente →', currentPage + 1, currentPage === pages), position);
  }
  function setupQuiz() {
    if (!form || !cards.length) return;
    const quiz = root.querySelector('.catalogue-quiz');
    if (!quiz) return;
    const panel = quiz.querySelector('.catalogue-quiz__panel');
    panel.replaceChildren();
    let criteria = {}, index = 0, history = [], started = false, done = false;
    const optionsFrom = name => FACETS.includes(name) ? boxes.filter(b => b.dataset.facet === name).map(b => ({label: b.nextElementSibling.textContent, values: {[name]: b.value}})) : [...(fields.find(f => f.dataset.filter === name)?.options || [])].filter(o => o.value && !o.disabled).map(o => ({label: o.textContent, values: {[name]: o.value}}));
    const steps = [
      {key: 'grupo', question: '¿Qué tipo de libro buscas?', options: () => optionsFrom('grupo')},
      {key: 'novedad', question: '¿Buscas algo recién publicado?', options: () => [
        {label: 'Sí, una novedad', values: {novedad: '15'}},
        {label: 'Un próximo lanzamiento', values: {estado: 'proximos'}}]},
      {key: 'temporada', question: '¿Te apetece una lectura de temporada?', options: () => optionsFrom('temporada')},
      {key: 'genero', question: '¿Qué género te apetece?', options: () => optionsFrom('genero')},
      {key: 'tematica', question: '¿Hay algún tema que te interese?', options: () => optionsFrom('tematica')},
      {key: 'edad', question: '¿Para quién buscas el libro?', options: () => optionsFrom('edad')},
      {key: 'paginas', question: '¿Cuánto te apetece leer?', options: () => optionsFrom('paginas')},
      {key: 'formato', question: '¿Tienes un formato en mente?', options: () => optionsFrom('formato')},
      {key: 'valoracion', question: '¿Quieres priorizar las valoraciones de lectores?', options: () => optionsFrom('valoracion')},
      // El presupuesto se aplica al formato elegido antes (si lo hay), nunca mezclando Kindle y papel en silencio.
      {key: 'precio_max', question: () => criteria.formato ? '¿Qué presupuesto prefieres en ' + optionsFrom('formato').find(o => o.values.formato === criteria.formato).label.toLocaleLowerCase('es') + '?' : '¿Qué presupuesto prefieres (en cualquier formato)?', options: () => [10, 20, 30].map(price => ({label: 'Hasta ' + price + ' €', values: {precio_max: String(price)}}))}
    ];
    // Adaptativo: solo opciones que acotan lo que queda; una pregunta que no cambia nada se salta.
    const usable = step => {
      const left = cards.filter(card => matches(card, criteria)).length;
      return step.options().filter(o => { const n = cards.filter(card => matches(card, {...criteria, ...o.values})).length; return n > 0 && n < left; });
    };
    const button = (label, action) => {
      const element = document.createElement('button'); element.type = 'button'; element.textContent = label;
      element.addEventListener('click', action); return element;
    };
    const reset = () => { criteria = {}; index = 0; history = []; done = false; render(); };
    const showResults = () => {
      for (const field of fields) field.value = criteria[field.dataset.filter] || (field.dataset.filter === 'orden' ? 'editorial' : '');
      for (const box of boxes) box.checked = pick(criteria[box.dataset.facet]).includes(box.value);
      currentPage = 1; apply(); done = true; render();
      const result = root.querySelector('.catalogue-results-head h2'); result.tabIndex = -1; result.focus({preventScroll: true}); result.scrollIntoView({block: 'start'});
    };
    function render() {
      panel.replaceChildren();
      const count = cards.filter(card => matches(card, criteria)).length;
      // Con tres libros o menos no tiene sentido seguir preguntando.
      if (count <= 3) index = steps.length;
      while (index < steps.length && !usable(steps[index]).length) index++;
      const status = document.createElement('p'); status.className = 'catalogue-quiz__progress'; status.setAttribute('role', 'status');
      const heading = document.createElement('h2'); heading.tabIndex = -1;
      const choices = document.createElement('div'); choices.className = 'catalogue-quiz__choices';
      if (done) {
        // El test sigue abierto con los resultados aplicados.
        status.textContent = 'Resultados del test aplicados · ' + cards.filter(card => matches(card, values())).length + ' libros';
        heading.textContent = 'Estos son tus libros';
        choices.append(button('Restablecer filtros', () => { form.reset(); reset(); }));
      } else if (index < steps.length) {
        const question = steps[index].question;
        heading.textContent = typeof question === 'function' ? question() : question;
        for (const option of [...usable(steps[index]), {label: 'Me da igual, continuar', values: {}}]) {
          choices.append(button(option.label, () => {
            history.push({index, criteria: {...criteria}}); criteria = {...criteria, ...option.values}; index++; render();
          }));
        }
      } else {
        status.textContent = count + (count === 1 ? ' libro encaja con tus respuestas' : ' libros encajan con tus respuestas');
        heading.textContent = count ? 'Tu próxima lectura te espera' : 'Los datos han cambiado. Prueba otra selección';
        if (count) choices.append(button('Ver mis resultados', showResults));
      }
      const actions = document.createElement('div'); actions.className = 'catalogue-filter-actions';
      // Desde la primera pregunta se puede saltar al catálogo con lo respondido hasta ahora.
      if (!done && index < steps.length) { const now = button('Mostrar ya los resultados (' + count + (count === 1 ? ' libro)' : ' libros)'), showResults); now.className = 'catalogue-quiz__now'; actions.append(now); }
      if (history.length) actions.append(button('← Volver', () => { const previous = history.pop(); done = false; index = previous.index; criteria = previous.criteria; render(); }));
      actions.append(button('Empezar de nuevo', reset));
      status.hidden = !status.textContent;
      panel.append(status, heading, choices, actions); heading.focus({preventScroll: true});
    }
    quiz.addEventListener('toggle', () => { if (quiz.open && !started) { started = true; render(); } });
  }
  const enableControls = on => {
    if (!form) return;
    form.querySelector('fieldset').disabled = !on; form.querySelector('[type="reset"]').disabled = !on;
    for (const select of root.querySelectorAll('[data-filter="orden"], [data-filter="estado"]')) select.disabled = !on;
  };
  let hydrated = !continuation.length, ready = false, payload = null, touched = false;
  // Solo datos de mercado de libros presentes en la página (se recalcula al añadir el resto del catálogo).
  const adoptMarket = () => {
    if (!payload) return;
    const ids = new Set([...root.querySelectorAll('[data-rating-book]')].map(el => el.dataset.ratingBook)), known = x => x && typeof x === 'object' && ids.has(x.libro_id);
    market = { offers: payload.offers.filter(known), ratings: payload.ratings.filter(known), sales_ranks: (Array.isArray(payload.sales_ranks) ? payload.sales_ranks : []).filter(known) };
  };
  const refresh = () => { renderNovelty(); renderMarket(); if (ready) apply(false); };
  window.addEventListener('pageshow', refresh); document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); }); setInterval(() => { if (!document.hidden) refresh(); }, 60000);
  fetch('/assets/reading-market.json', { cache: 'no-store' }).then(r => r.ok ? r.json() : null).then(p => { if (p?.schema_version === 1 && Array.isArray(p.offers) && Array.isArray(p.ratings)) { payload = p; adoptMarket(); renderMarket(); if (ready) restore(); } }).catch(() => { /* The static catalogue stays available. */ }); refresh();
  if (document.fonts) document.fonts.load('1em "CatalogueNovelty"').then(faces => { root.classList.add(faces.length ? 'catalogue-fonts-ready' : 'catalogue-fonts-failed'); }).catch(() => root.classList.add('catalogue-fonts-failed'));
  else root.classList.add('catalogue-fonts-failed');
  if (!hydrated) {
    // Controles usables desde el principio: lo que el lector marque mientras carga se aplica al terminar.
    enableControls(true);
    root.addEventListener('input', () => { touched = true; }, true);
    root.addEventListener('change', () => { touched = true; }, true);
    let resume = false;
    try { resume = sessionStorage.getItem('catalogue-hydrate') === '1'; sessionStorage.removeItem('catalogue-hydrate'); } catch { /* opcional */ }
    if (!location.hash.slice(1) && !resume) await new Promise(resolve => {
      const events = ['pointerdown', 'focusin', 'keydown'], controls = 'input, select, textarea, button, summary, label';
      const go = event => {
        if (event.type !== 'hashchange' && !event.target.closest?.(controls)) return;
        events.forEach(type => root.removeEventListener(type, go, true));
        window.removeEventListener('hashchange', go);
        resolve();
      };
      events.forEach(type => root.addEventListener(type, go, true));
      window.addEventListener('hashchange', go);
    });
    const count = root.querySelector('[data-catalogue-count]');
    if (count) count.textContent = 'Preparando la búsqueda en todo el catálogo…';
    if (!await hydrate()) { enableControls(false); return; }
    // Una tarea por paso: todo seguido bloqueaba el primer filtro más de un segundo en móviles.
    const pause = () => new Promise(resolve => setTimeout(resolve, 0));
    hydrated = true; await pause(); indexCards(); pruneOffers(); await pause(); adoptMarket(); renderNovelty(); await pause(); renderMarket(); await pause();
  }
  if (form) {
    enableControls(true);
    const refineToggle = form.querySelector('[data-catalogue-refine-toggle]'), refine = form.querySelector('[data-catalogue-refine]');
    if (refineToggle && refine) {
      const setRefine = open => { refine.toggleAttribute('data-open', open); refineToggle.setAttribute('aria-expanded', String(open)); };
      refineToggle.addEventListener('click', () => setRefine(!refine.hasAttribute('data-open')));
      // Escape cierra el panel móvil y devuelve el foco.
      refine.addEventListener('keydown', event => { if (event.key === 'Escape' && getComputedStyle(refineToggle).display !== 'none') { event.preventDefault(); setRefine(false); refineToggle.focus(); } });
    }
    // Fechas al confirmar (change); «hasta» nunca antes de «desde».
    const from = form.querySelector('[data-filter="desde"]'), to = form.querySelector('[data-filter="hasta"]');
    const linkDates = () => { if (!from || !to) return; if (from.value && to.value && to.value < from.value) to.value = from.value; to.min = from.value || '1000-01-01'; from.max = to.value || '2100-12-31'; };
    fields.forEach(f => f.addEventListener(f.type === 'date' ? 'change' : 'input', () => { linkDates(); currentPage = 1; apply(); }));
    boxes.forEach(b => b.addEventListener('change', () => {
      currentPage = 1; apply();
      // Al elegir tipo se abre solo «Género».
      if (b.dataset.facet === 'grupo' && b.checked) for (const group of form.querySelectorAll('[data-facet-group]')) if (group.dataset.facetGroup !== 'grupo') group.open = group.dataset.facetGroup === 'genero' || group.querySelector('input:checked') !== null;
    }));
    form.addEventListener('submit', event => { event.preventDefault(); currentPage = 1; apply(); }); form.addEventListener('reset', () => setTimeout(() => { currentPage = 1; apply(); }, 0)); window.addEventListener('hashchange', restore);
    if (touched && !location.hash.slice(1)) { currentPage = 1; apply(); } else restore();
  }
  setupQuiz();
  // El test pudo abrirse antes de terminar la descarga: se pinta ahora.
  const quizBox = root.querySelector('.catalogue-quiz');
  if (quizBox?.open) quizBox.dispatchEvent(new Event('toggle'));
  ready = true; root.dataset.catalogueReady = 'true';
})();
