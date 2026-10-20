/* Static books and purchase links work without JS; optional market data expires. */
(() => {
  'use strict';
  const root = document.querySelector('[data-reading-catalogue]');
  if (!root) return;
  const normalize = s => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es').trim();
  const form = root.querySelector('[data-catalogue-filters]');
  const cards = [...root.querySelectorAll('[data-catalogue-book]')];
  const originalOrder = new Map(cards.map((card, i) => [card, i]));
  const fields = form ? [...form.elements].filter(f => f.dataset.filter) : [];
  const collator = new Intl.Collator('es', { sensitivity: 'base', numeric: true });
  let market = { offers: [], ratings: [] };
  const stamp = s => typeof s === 'string' && /T.*(?:Z|[+-]\d\d:\d\d)$/.test(s) ? Date.parse(s) : NaN;
  const fresh = (e, hours) => { const start = stamp(e.actualizado_en), end = stamp(e.caduca_en), now = Date.now(); return Number.isFinite(start) && Number.isFinite(end) && start <= now && end > now && end > start && end - start <= hours * 3600000 && now - start <= hours * 3600000; };
  const safeURL = (raw, hosts, path) => { try { const u = new URL(raw); return u.protocol === 'https:' && !u.username && !u.password && !u.port && hosts.includes(u.hostname) && path.test(u.pathname) ? u : null; } catch { return null; } };
  const validOffer = o => { const u = safeURL(o.url, ['amazon.es', 'www.amazon.es'], /\/(?:dp|gp\/product)\/[A-Z0-9]{10}(?:\/|$)/); return fresh(o, 24) && o.moneda === 'EUR' && o.tipo === 'compra' && ['tapa-blanda', 'tapa-dura', 'ebook', 'audiolibro'].includes(o.formato) && Number.isSafeInteger(o.precio_centimos) && o.precio_centimos > 0 && o.precio_centimos < 100000000 && u && /^[A-Za-z0-9-]+$/.test(u.searchParams.get('tag') || ''); };
  const validRating = r => fresh(r, 168) && Number.isFinite(r.puntuacion) && r.puntuacion >= 0 && r.puntuacion <= 5 && Number.isSafeInteger(r.numero_valoraciones) && r.numero_valoraciones > 0 && safeURL(r.url, ['www.goodreads.com', 'goodreads.com'], /^\/book\/show\/\d/);
  const discount = o => Number.isSafeInteger(o.precio_referencia_centimos) && o.precio_referencia_centimos > o.precio_centimos ? Math.floor((o.precio_referencia_centimos - o.precio_centimos) / o.precio_referencia_centimos * 100) : 0;
  const offersFor = id => market.offers.filter(o => o.libro_id === id && validOffer(o));
  const ratingFor = id => market.ratings.find(r => r.libro_id === id && validRating(r));
  const money = cents => new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(cents / 100);
  const today = () => new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Madrid', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
  const isNew = s => { if (!s) return false; const days = (Date.parse(today() + 'T00:00:00Z') - Date.parse(s + 'T00:00:00Z')) / 86400000; return days >= 0 && days <= 180; };
  const values = () => Object.fromEntries(fields.map(f => [f.dataset.filter, f.disabled ? '' : f.value]));
  const matchingOffers = (card, v) => offersFor(card.dataset.bookId).filter(o => (!v.formato || o.formato === v.formato) && (!v.precio_min || o.precio_centimos >= Math.round(Number(v.precio_min) * 100)) && (!v.precio_max || o.precio_centimos <= Math.round(Number(v.precio_max) * 100)) && (!v.descuento || discount(o) >= Number(v.descuento)));
  const minPrice = (card, v) => { const o = matchingOffers(card, v); return o.length ? Math.min(...o.map(x => x.precio_centimos)) : null; };
  function renderMarket() {
    for (const box of root.querySelectorAll('[data-rating-book]')) {
      const r = ratingFor(box.dataset.ratingBook); box.replaceChildren(); if (!r) continue;
      const link = document.createElement('a'); link.href = r.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
      link.setAttribute('aria-label', r.puntuacion.toLocaleString('es-ES') + ' de 5 en Goodreads, ' + r.numero_valoraciones.toLocaleString('es-ES') + ' valoraciones');
      const stars = document.createElement('span'); stars.className = 'catalogue-stars'; stars.setAttribute('aria-hidden', 'true'); stars.style.setProperty('--rating', r.puntuacion / 5 * 100 + '%'); stars.textContent = '★★★★★';
      link.append(stars, ' ' + r.puntuacion.toLocaleString('es-ES') + '/5 · Goodreads'); link.title = 'Consultado el ' + new Date(r.actualizado_en).toLocaleDateString('es-ES'); box.append(link);
    }
    for (const f of root.querySelectorAll('[data-market-control]')) f.disabled = !market[f.dataset.marketControl].some(f.dataset.marketControl === 'offers' ? validOffer : validRating);
    for (const o of root.querySelectorAll('[data-sort-market]')) o.disabled = !market[o.dataset.sortMarket].some(o.dataset.sortMarket === 'offers' ? validOffer : validRating);
    for (const f of fields) if ((f.disabled || (f.tagName === 'SELECT' && f.selectedOptions[0]?.disabled)) && f.value) f.value = f.dataset.filter === 'orden' ? 'editorial' : '';
    const note = root.querySelector('[data-market-note]'); if (note) note.textContent = market.offers.some(validOffer) ? 'Precios en EUR sujetos a disponibilidad y condiciones en Amazon.' : 'Los filtros de precio y oferta estarán disponibles cuando haya precios vigentes.';
  }
  function apply(save = true) {
    const v = values(); let visible = 0;
    for (const card of cards) {
      const cats = card.dataset.categories.split(' '), published = card.dataset.published, year = card.dataset.year;
      const formats = new Set([...(card.dataset.formats || '').split(' '), ...offersFor(card.dataset.bookId).map(o => o.formato)]);
      const lower = published || (year ? year + '-01-01' : ''), upper = published || (year ? year + '-12-31' : '');
      const match = normalize(card.dataset.search).includes(normalize(v.q || '')) && ['genero', 'tematica', 'temporada', 'edad', 'contenido', 'epoca'].every(k => !v[k] || cats.includes(v[k])) && (!v.formato || formats.has(v.formato)) && (!v.novedad || isNew(published)) && (!v.desde || (upper && upper >= v.desde)) && (!v.hasta || (lower && lower <= v.hasta)) && (!v.valoracion || ratingFor(card.dataset.bookId)?.puntuacion >= Number(v.valoracion)) && (!(v.precio_min || v.precio_max || v.descuento) || matchingOffers(card, v).length > 0);
      card.hidden = !match; if (match) visible++;
    }
    const nullable = (x, y, desc = false) => x == null ? (y == null ? 0 : 1) : y == null ? -1 : desc ? y - x : x - y;
    const dateOf = card => card.dataset.published || card.dataset.year ? Date.parse(card.dataset.published || card.dataset.year + '-01-01') : null;
    const compare = (a, b) => {
      switch (v.orden) {
        case 'titulo': return collator.compare(a.dataset.title, b.dataset.title);
        case 'titulo_desc': return collator.compare(b.dataset.title, a.dataset.title);
        case 'autor': return collator.compare(a.dataset.author, b.dataset.author);
        case 'fecha_desc': case 'fecha_asc': return nullable(dateOf(a), dateOf(b), v.orden === 'fecha_desc');
        case 'precio_asc': case 'precio_desc': return nullable(minPrice(a, v), minPrice(b, v), v.orden === 'precio_desc');
        case 'valoracion_desc': return nullable(ratingFor(a.dataset.bookId)?.puntuacion ?? null, ratingFor(b.dataset.bookId)?.puntuacion ?? null, true);
        default: return 0;
      }
    };
    const grid = root.querySelector('.catalogue-grid'), sorted = [...cards].sort((a, b) => compare(a, b) || originalOrder.get(a) - originalOrder.get(b));
    if (grid && sorted.some((card, i) => grid.children[i] !== card)) { const fragment = document.createDocumentFragment(); sorted.forEach(card => fragment.append(card)); grid.replaceChildren(fragment); }
    for (const box of root.querySelectorAll('[data-price-book]')) {
      const offers = offersFor(box.dataset.priceBook).filter(o => !v.formato || o.formato === v.formato).sort((a, b) => a.precio_centimos - b.precio_centimos); box.replaceChildren(); box.hidden = !offers.length;
      if (offers.length) { const link = document.createElement('a'); link.href = offers[0].url; link.rel = 'sponsored nofollow noopener noreferrer'; link.target = '_blank'; link.textContent = 'Desde ' + money(offers[0].precio_centimos) + ' en Amazon'; link.title = 'Precio consultado el ' + new Date(offers[0].actualizado_en).toLocaleString('es-ES') + '. El precio aplicable será el de Amazon al comprar.'; box.append(link); }
    }
    if (form) {
      root.querySelector('[data-catalogue-count]').textContent = visible + (visible === 1 ? ' libro' : ' libros'); root.querySelector('[data-catalogue-empty]').hidden = visible !== 0;
      if (save) { const hash = new URLSearchParams(Object.entries(v).filter(([k, value]) => value && !(k === 'orden' && value === 'editorial'))); history.replaceState(null, '', location.pathname + location.search + (hash.size ? '#' + hash : '')); }
    }
  }
  function restore() {
    const params = new URLSearchParams(location.hash.slice(1));
    for (const f of fields) { const v = params.get(f.dataset.filter) || (f.dataset.filter === 'orden' ? 'editorial' : ''); f.value = f.tagName === 'SELECT' && ![...f.options].some(o => o.value === v) ? (f.dataset.filter === 'orden' ? 'editorial' : '') : v; }
    const advanced = form?.querySelector('details');
    if (advanced && fields.some(f => advanced.contains(f) && f.value && !f.disabled)) advanced.open = true;
    apply(false);
  }
  if (form) {
    form.querySelector('fieldset').disabled = false; form.querySelector('[type="reset"]').disabled = false;
    const sort = root.querySelector('[data-filter="orden"]'); if (sort) sort.disabled = false;
    fields.forEach(f => f.addEventListener('input', () => apply()));
    form.addEventListener('submit', event => { event.preventDefault(); apply(); }); form.addEventListener('reset', () => setTimeout(() => apply(), 0)); window.addEventListener('hashchange', restore); restore();
  }
  const refresh = () => { renderMarket(); apply(false); };
  window.addEventListener('pageshow', refresh); document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); }); setInterval(() => { if (!document.hidden) refresh(); }, 60000);
  const knownIds = new Set([...root.querySelectorAll('[data-rating-book]')].map(el => el.dataset.ratingBook));
  fetch('/assets/reading-market.json', { cache: 'no-store' }).then(r => r.ok ? r.json() : null).then(p => { if (p?.schema_version === 1 && Array.isArray(p.offers) && Array.isArray(p.ratings)) { market = { offers: p.offers.filter(o => o && typeof o === 'object' && knownIds.has(o.libro_id)), ratings: p.ratings.filter(r => r && typeof r === 'object' && knownIds.has(r.libro_id)) }; renderMarket(); restore(); } }).catch(() => { /* The static catalogue stays available. */ }); refresh();
  const speak = root.querySelector('[data-catalogue-speak]');
  if (speak && 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window) {
    const stop = root.querySelector('[data-catalogue-stop]'), status = root.querySelector('[data-catalogue-speech-status]'); speak.parentElement.hidden = false;
    const finish = message => { speak.disabled = false; stop.disabled = true; status.textContent = message; };
    speak.addEventListener('click', () => { speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(root.querySelector('[data-catalogue-description]').textContent); u.lang = 'es-ES'; u.onend = () => finish('Lectura terminada.'); u.onerror = () => finish('No se ha podido continuar la lectura.'); speak.disabled = true; stop.disabled = false; status.textContent = 'Leyendo la descripción.'; speechSynthesis.speak(u); });
    const cancel = () => { speechSynthesis.cancel(); finish('Lectura detenida.'); }; stop.addEventListener('click', cancel); window.addEventListener('pagehide', cancel);
  }
})();
