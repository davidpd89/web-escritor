// Referencia pura del motor de filtros de /recomendaciones/ (R5-5, oráculo de paridad, Fable 18/11 §2.1).
//
// Copia fiel, sin DOM, de matches/compare/renderFacets de assets/reading-catalogue.js: mismos datos que lee el motor
// (el `dataset` de cada ficha) y la misma consulta (los valores del formulario). No cambia comportamiento: si el motor
// cambia, qa/catalogue-filter-parity.mjs lo detecta contra la página real y esta copia se actualiza en la misma PR.
//
// filtrar(libros, consulta, ctx) → { ids, total, facetas }
//   libros: [{ bookId, title, author, isbn, search, published, publishedMonth, year, pages, categories, formats,
//              group, formatPrices, formatDiscounts }] en el orden del DOM al hidratar (el orden original).
//   consulta: { q, estado, orden, paginas, novedad, desde, hasta, valoracion, precio_min, precio_max, precio_formato,
//               descuento, formato: [], grupo: [], genero: [], edad: [] }
//   ctx: { today: 'AAAA-MM-DD', offersFor(id) → [{formato, pct}], ratingFor(id) → nota|null, rankFor(id) → puesto|null }
//        Sin mercado (la QA lo vacía), los tres devuelven vacío.

export const FACETS = ['grupo', 'genero', 'edad', 'formato'];
const OFFER_MAX_DAYS = 3;

export const normalize = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLocaleLowerCase('es').replace(/,/g, ' ').replace(/\s+/g, ' ').trim();
export const searchQuery = s => {
  const candidate = s.trim().replace(/^ISBN(?:-13)?\s*:?\s*/i, '');
  return /^97[89](?:[\s-]*\d){10}$/.test(candidate) ? candidate.replace(/[\s-]/g, '') : normalize(s);
};
const pick = x => Array.isArray(x) ? x : x ? [x] : [];
const isDay = s => /^\d{4}-\d{2}-\d{2}$/.test(s || '');

export function filtrar(libros, consulta, ctx = {}) {
  const v = consulta;
  const today = ctx.today;
  const offersFor = ctx.offersFor || (() => []);
  const ratingFor = ctx.ratingFor || (() => null);
  const rankFor = ctx.rankFor || (() => null);
  const ageDays = s => isDay(s) ? (Date.parse(today + 'T00:00:00Z') - Date.parse(s + 'T00:00:00Z')) / 86400000 : NaN;
  const isNew = (s, window) => { const days = ageDays(s); return window === 'proximamente' ? days < 0 : days >= 0 && (window === '15' ? days < 15 : days <= Number(window)); };
  const offerCurrent = checked => isDay(checked) && (Date.parse(today) - Date.parse(checked)) / 864e5 <= OFFER_MAX_DAYS;
  const formatDiscounts = b => (b.formatDiscounts || '').split(' ').filter(Boolean).map(x => x.split(':')).filter(([, , checked]) => offerCurrent(checked)).map(([formato, pct]) => ({formato, pct: Number(pct)}));
  const cats = b => b.categories.split(' ');
  const formatsOf = b => new Set([...(b.formats || '').split(' '), ...offersFor(b.bookId).map(o => o.formato)]);
  const matchingOffers = b => [...offersFor(b.bookId), ...formatDiscounts(b)].filter(o => (!priceFormats().length || priceFormats().includes(o.formato)) && (!v.descuento || o.pct >= Number(v.descuento)));
  const released = lower => !lower || lower <= today;
  const ratingOk = b => { if (!v.valoracion) return true; const r = ratingFor(b.bookId); return r != null && (v.valoracion === 'menos-3' ? r < 3 : r >= Number(v.valoracion)); };
  const formatPrices = b => new Map((b.formatPrices || '').split(' ').filter(Boolean).map(x => x.split(':')).map(([f, c]) => [f, Number(c)]));
  const priceFormats = () => v.precio_formato ? [v.precio_formato] : pick(v.formato);
  const priceOf = (b, formats) => { const prices = [...formatPrices(b)].filter(([f]) => !formats.length || formats.includes(f)).map(([, c]) => c); return prices.length ? Math.min(...prices) : null; };
  const priceOk = b => {
    if (!v.precio_min && !v.precio_max) return true;
    const min = v.precio_min ? Math.round(Number(v.precio_min) * 100) : 0, max = v.precio_max ? Math.round(Number(v.precio_max) * 100) : Infinity, formats = priceFormats();
    return [...formatPrices(b)].some(([f, c]) => (!formats.length || formats.includes(f)) && c >= min && c <= max);
  };
  const bounds = b => {
    const published = b.published, month = b.publishedMonth, year = b.year;
    return {
      lower: published || (month ? month + '-01' : year ? year + '-01-01' : ''),
      upper: published || (month ? new Date(Date.UTC(Number(month.slice(0, 4)), Number(month.slice(5)), 0)).toISOString().slice(0, 10) : year ? year + '-12-31' : ''),
    };
  };
  const rangeOf = b => { const pages = Number(b.pages); return !pages ? '' : pages < 200 ? 'breve' : pages < 400 ? 'media' : pages < 600 ? 'larga' : 'muy-larga'; };
  const query = searchQuery(v.q || '');
  const searchOf = b => normalize(b.search || `${b.title} ${b.author} ${b.isbn || ''}`);
  const baseMatch = b => {
    const {lower, upper} = bounds(b);
    return searchOf(b).includes(query) && (v.estado === 'todos' || (!v.estado && v.q) || (v.estado === 'proximos' ? !released(lower) : released(lower))) && (!v.paginas || v.paginas === rangeOf(b)) && (!v.novedad || isNew(b.published, v.novedad)) && (!v.desde || (upper && upper >= v.desde)) && (!v.hasta || (lower && lower <= v.hasta)) && ratingOk(b) && priceOk(b) && (!v.descuento || matchingOffers(b).length > 0);
  };
  const facetValues = (b, k) => k === 'formato' ? formatsOf(b) : new Set(k === 'grupo' ? [b.group] : cats(b));
  const facetMatch = (b, k) => {
    const chosen = pick(v[k]);
    if (!chosen.length) return true;
    if (k === 'grupo') return chosen.includes(b.group);
    if (k === 'formato') { const formats = formatsOf(b); return chosen.some(x => formats.has(x)); }
    const c = cats(b); return chosen.some(x => c.includes(x));
  };

  const nullable = (x, y, desc = false) => x == null ? (y == null ? 0 : 1) : y == null ? -1 : desc ? y - x : x - y;
  const dateOf = b => b.published || b.publishedMonth || b.year ? Date.parse(b.published || (b.publishedMonth ? b.publishedMonth + '-01' : b.year + '-01-01')) : null;
  const orden = v.orden || 'editorial';
  const compare = (a, b) => {
    if (orden === 'editorial' && v.valoracion) return nullable(ratingFor(a.bookId), ratingFor(b.bookId)) || nullable(dateOf(a), dateOf(b), true);
    if (orden === 'editorial' && v.estado === 'proximos') return nullable(dateOf(a), dateOf(b));
    switch (orden) {
      case 'editorial': case 'fecha_desc': case 'fecha_asc': return nullable(dateOf(a), dateOf(b), orden !== 'fecha_asc');
      case 'paginas_asc': case 'paginas_desc': return nullable(Number(a.pages) || null, Number(b.pages) || null, orden === 'paginas_desc');
      case 'precio_tapa-dura': case 'precio_tapa-blanda': case 'precio_ebook': case 'precio_audiolibro': { const format = [orden.slice(7)]; return nullable(priceOf(a, format), priceOf(b, format)); }
      case 'ventas': return nullable(rankFor(a.bookId), rankFor(b.bookId)) || nullable(dateOf(a), dateOf(b), true);
      case 'valoracion_desc': return nullable(ratingFor(a.bookId), ratingFor(b.bookId), true);
      default: return 0;
    }
  };

  const original = new Map(libros.map((b, i) => [b, i]));
  const found = [];
  const counts = new Map(FACETS.map(k => [k, new Map()]));
  for (const b of libros) {
    if (!baseMatch(b)) continue;
    const failing = FACETS.filter(k => !facetMatch(b, k));
    if (!failing.length) found.push(b);
    if (failing.length > 1) continue;
    for (const k of failing.length ? failing : FACETS) { const c = counts.get(k); for (const x of facetValues(b, k)) c.set(x, (c.get(x) || 0) + 1); }
  }
  found.sort((a, b) => compare(a, b) || original.get(a) - original.get(b));
  return {
    ids: found.map(b => b.bookId),
    total: found.length,
    facetas: Object.fromEntries(FACETS.map(k => [k, Object.fromEntries([...counts.get(k)].sort())])),
  };
}
