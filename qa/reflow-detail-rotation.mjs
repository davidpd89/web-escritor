// Rotacion de fichas en la auditoria completa del reflow.
// Las fichas /recomendaciones/{libros,autores,editoriales}/<slug>/ salen de una misma plantilla:
// recorrerlas todas hace que la duracion crezca con el catalogo. Cada dia se recorre 1/K de cada
// tipo (todas quedan cubiertas en K dias) mas las N mas pesadas (peor caso de la plantilla).
// El resto de paginas se recorre siempre entero.
export const DETAIL_ROUTE = /^\/recomendaciones\/(libros|autores|editoriales)\/[^/]+\/$/;

// FNV-1a de 32 bits: estable entre runs, shards y versiones de Node.
export function routeBucket(route, k) {
  let h = 0x811c9dc5;
  for (let i = 0; i < route.length; i++) {
    h ^= route.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h % k;
}

export function rotateDetailRoutes(routes, { k, day, heaviest = 5, sizeOf = () => 0 }) {
  if (!Number.isInteger(k) || k <= 1) return { routes: [...routes], skipped: 0, kinds: {} };
  const slot = ((day % k) + k) % k;
  const keep = [];
  const byKind = new Map();
  for (const route of routes) {
    const m = DETAIL_ROUTE.exec(route);
    if (!m) keep.push(route);
    else (byKind.get(m[1]) || byKind.set(m[1], []).get(m[1])).push(route);
  }
  const kinds = {};
  let skipped = 0;
  for (const [kind, list] of byKind) {
    const sorted = [...list].sort((a, b) => a.localeCompare(b));
    // Franja por hash de la ruta, no por posicion: las altas y bajas no mueven a las demas fichas.
    const chosen = new Set(sorted.filter((r) => routeBucket(r, k) === slot));
    const bySize = sorted.map((r) => [r, sizeOf(r)]).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
    for (const [r] of bySize.slice(0, heaviest)) chosen.add(r);
    kinds[kind] = { total: sorted.length, audited: chosen.size };
    skipped += sorted.length - chosen.size;
    keep.push(...chosen);
  }
  return { routes: keep.sort((a, b) => a.localeCompare(b)), skipped, kinds };
}
