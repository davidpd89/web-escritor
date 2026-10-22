/**
 * PROTOTIPO DE INVESTIGACIÓN — no se carga en producción.
 * Facetas dependientes de los resultados reales (sin servidor ni dependencia).
 * Inspirado en la semántica de RefinementList de Algolia InstantSearch (MIT):
 * https://github.com/algolia/instantsearch/blob/master/packages/instantsearch.js/src/connectors/refinement-list/connectRefinementList.ts
 * Implementación original ajustada al catálogo: un valor por desplegable (AND entre filtros).
 */

/**
 * Calcula las opciones de UNA faceta manteniendo el resto de filtros.
 * Excluye la selección de la propia faceta para permitir cambiarla.
 * Conservar siempre la opción elegida (aunque tenga 0 resultados) impide
 * borrados silenciosos tras compartir un enlace o cambiar otros filtros.
 *
 * @param {{records:unknown[], selected:Object<string,string>, facet:string,
 *   choices:Array<{value:string,label:string}>, match:(record:unknown,state:Object<string,string>)=>boolean}} params
 */
export function calculateFacetOptions({ records, selected, facet, choices, match }) {
  const otherFilters = { ...selected, [facet]: '' };
  const eligible = records.filter(record => match(record, otherFilters));
  const current = selected[facet] || '';
  return choices.map(choice => {
    const value = choice.value;
    const count = value
      ? eligible.filter(record => match(record, { ...otherFilters, [facet]: value })).length
      : eligible.length;
    return { ...choice, count, selected: value !== '' && value === current,
      available: value === '' || value === current || count > 0 };
  }).filter(option => option.available);
}

/** Fuente de verdad para chips y conteo; nunca incluye ordenación. */
export function activeFilters(selected, labelFor) {
  return Object.entries(selected)
    .filter(([key, value]) => key !== 'orden' && Boolean(value))
    .map(([key, value]) => ({
      key, value, label: labelFor(key, value),
      next: { ...selected, [key]: '' }
    }));
}

/**
 * Adaptador de referencia para <select> nativos. Requiere llamada desde apply(),
 * con opciones originales inmutables capturadas ANTES de modificarlas.
 * No crea controles accesibles personalizados ni reemplaza el estado del formulario.
 */
export function updateSelect(select, options) {
  const previousValue = select.value;
  const signature = JSON.stringify(options.map(o => [o.value, o.label, o.count]));
  if (select.dataset.facetSignature === signature) return;
  select.dataset.facetSignature = signature;
  const fragment = document.createDocumentFragment();
  for (const option of options) {
    const element = document.createElement('option');
    element.value = option.value;
    element.textContent = option.value ? `${option.label} (${option.count})` : option.label;
    fragment.append(element);
  }
  select.replaceChildren(fragment);
  select.value = previousValue;
}
