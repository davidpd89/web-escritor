// Integration adapter for the site's existing data attributes. Not a UI library.
// Multi-select interface is supplied verbatim by Choices.js v11.2.4 (MIT).
export const MULTI = ['genero', 'tematica', 'temporada', 'edad', 'contenido', 'epoca', 'formato'];
// Campos ya admitidos en reading-catalogue.js: nunca perderlos en URL compartidas.
export const SCALAR = ['paginas', 'novedad', 'desde', 'hasta', 'precio_min', 'precio_max', 'descuento', 'valoracion'];

export function parseHash(hash) {
  const params = new URLSearchParams(hash.replace(/^#/, ''));
  const state = { q: params.get('q') || '', grupo: params.get('grupo') || '', orden: params.get('orden') || 'editorial' };
  for (const key of MULTI) state[key] = [...new Set(params.getAll(key).filter(Boolean))];
  for (const key of SCALAR) state[key] = params.get(key) || '';
  state.pagina = Math.max(1, Number.parseInt(params.get('pagina'), 10) || 1);
  return state;
}

export function writeHash(state) {
  const params = new URLSearchParams();
  if (state.q) params.set('q', state.q);
  if (state.grupo) params.set('grupo', state.grupo);
  for (const key of MULTI) for (const value of [...new Set(selection(state[key]))].sort()) params.append(key, value);
  for (const key of SCALAR) if (state[key]) params.set(key, String(state[key]));
  if (state.orden && state.orden !== 'editorial') params.set('orden', state.orden);
  if (state.pagina > 1) params.set('pagina', String(state.pagina));
  return params.size ? '#' + params : '';
}

const selection = wanted => Array.isArray(wanted) ? wanted : wanted ? [wanted] : [];
const anyOf = (available, wanted) => {
  const picked = selection(wanted);
  return !picked.length || picked.some(value => available.includes(value));
};

export function matchesMulti(book, state) {
  const categories = book.categories || [];
  const formats = book.formats || [];
  if (state.grupo && book.group !== state.grupo) return false;
  const normalized = (book.search || book.title || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const query = (state.q || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  if (query && !normalized.includes(query)) return false;
  for (const facet of MULTI) {
    const pool = facet === 'formato' ? formats : categories;
    if (!anyOf(pool, state[facet])) return false;
  }
  return true;
}

export function availableOptions(books, state, facet, choices) {
  if (!MULTI.includes(facet)) throw new Error("Unknown facet: " + facet);
  // Exclude own facet, preserving all other selected groups: AND across dimensions.
  const withoutOwnFacet = { ...state, [facet]: [] };
  const candidates = books.filter(book => matchesMulti(book, withoutOwnFacet));
  return choices.map(({ value, label }) => ({
    value, label,
    count: candidates.filter(book => matchesMulti(book, { ...withoutOwnFacet, [facet]: [value] })).length,
    selected: selection(state[facet]).includes(value)
  })).filter(option => option.count > 0 || option.selected);
}

/** Descarta valores retirados de la taxonomía, sin borrar selecciones válidas con 0 resultados.
 * La lista maestra de opciones debe venir del catálogo completo, no de facetas ya recortadas. */
export function sanitizeFacetSelections(state, masters) {
  const clean = { ...state };
  for (const [facet, choices] of Object.entries(masters)) {
    if (!MULTI.includes(facet)) continue;
    const allowed = new Set(choices.map(choice => choice.value));
    const raw = Array.isArray(state[facet]) ? state[facet] : state[facet] ? [state[facet]] : [];
    clean[facet] = [...new Set(raw)].filter(value => allowed.has(value));
  }
  return clean;
}

/**
 * Adaptador mínimo para assets/reading-catalogue.js::matchingOffers().
 * Recibe EXCLUSIVAMENTE ofertas previamente validadas por validOffer/fresh.
 * Cruza formato y precio EN LA MISMA oferta: evita falsos positivos de un
 * libro con tapa blanda barata y tapa dura cara cuando solo se pide tapa dura.
 */
export function matchingOffersMulti(offers, state) {
  const selected = Array.isArray(state.formato)
    ? state.formato : state.formato ? [state.formato] : [];
  const min = state.precio_min ? Math.round(Number(state.precio_min) * 100) : null;
  const max = state.precio_max ? Math.round(Number(state.precio_max) * 100) : null;
  const requiredDiscount = state.descuento ? Number(state.descuento) : 0;
  return offers.filter(offer => {
    if (selected.length && !selected.includes(offer.formato)) return false;
    if (min !== null && offer.precio_centimos < min) return false;
    if (max !== null && offer.precio_centimos > max) return false;
    const reference = offer.precio_referencia_centimos;
    const discount = Number.isSafeInteger(reference) && reference > offer.precio_centimos
      ? Math.floor((reference - offer.precio_centimos) / reference * 100) : 0;
    return discount >= requiredDiscount;
  });
}
