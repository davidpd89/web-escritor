# A.9 · Auditoría de canonicals y paginación

Fecha de revisión: 2026-08-28
Idea original: confirmar canonicals correctos en páginas con parámetros/query views y paginación, especialmente posibles filtros de Herramientas/Recomendaciones.

## Veredicto

**ALREADY_COVERED para el sitio actual / MANTENER COMO CONTRATO DE FUTURAS VISTAS.**

La web actual ya tiene varias defensas de canonicalización y no hay evidencia de una arquitectura pública de filtros/paginación indexable que necesite una implementación nueva. La idea merece conservarse como regla de diseño para futuras vistas con parámetros, no como excusa para añadir canonicals nuevos a ciegas.

## Fuente primaria

Google Search Central · Canonicalization
https://developers.google.com/search/docs/crawling-indexing/canonicalization

Google explica que múltiples URLs con contenido igual/muy similar pueden surgir por:

- HTTP/HTTPS;
- variantes host;
- parámetros;
- filtrado/ordenación;
- rutas alternativas.

Señales fuertes/útiles incluyen:

- redirects;
- `rel="canonical"`;
- URL incluida en sitemap;
- consistencia interna.

Google puede elegir una canonical distinta si las señales son contradictorias. Canonical no es un mecanismo para ocultar contenido irrelevante ni sustituye `noindex` cuando la intención es no indexar una página.

Troubleshooting actualizado:
https://developers.google.com/search/docs/crawling-indexing/canonicalization-troubleshooting

## Estado real del repo

### `scripts/check-internal-graph.py`

Ya comprueba:

- missing canonical en páginas indexables;
- canonical collisions;
- resolución de enlaces internos contra la URL canónica.

### `scripts/check-global-discoverability.py`

El contrato histórico de #42 verifica:

- canonical indexable ↔ sitemap ↔ registry;
- ausencia de rutas internas/gated en superficies de descubrimiento;
- registry como autoridad del inventario público.

### Search Console

La auditoría operativa reciente ya clasificó variantes `http://`/`www` como redirects correctos, no como páginas que debieran indexarse.

### Arquitectura actual

No hay evidencia de un archivo paginado clásico (`?page=2`) ni de páginas indexables generadas por filtros de Herramientas/Recomendaciones. Las herramientas son rutas propias; Recomendaciones tiene hubs/rutas canónicas propias.

## Qué NO significa “cubierto”

No significa que cualquier futura query string esté automáticamente bien. Una UI futura podría introducir:

```text
/recomendaciones/?genero=fantasia
/recomendaciones/?orden=recientes
/herramientas/?tipo=texto
```

y entonces hay que decidir de antemano si cada vista:

1. es solo estado de UI;
2. representa contenido único que merece URL/indexación;
3. es una combinación facetada que debe mantenerse fuera del índice.

## Política propuesta para futuras vistas

### Caso A · filtro puramente UI

Ejemplo:

```text
/herramientas/?categoria=manuscrito
```

si solo filtra las mismas herramientas sin contenido editorial único:

- la URL base sigue siendo la única superficie indexable;
- no crear links crawlables a miles de combinaciones;
- la UI puede usar query/hash/history para estado, pero el contrato SEO debe estar definido;
- si el HTML de variante se sirve y Google puede rastrearlo, revisar canonical/noindex según arquitectura real.

### Caso B · página editorial única

Si una combinación merece posicionarse por valor propio, no dejarla como parámetro improvisado. Preferir una URL canónica explícita con contenido propio:

```text
/recomendaciones/portal-fantasy-espanol/
```

que ya es el patrón del proyecto.

### Caso C · paginación real

Si en el futuro Cuaderno crece y necesita `/cuaderno/page/2/`:

- cada página debe ser accesible mediante links `<a href>`;
- cada página paginada debe tener canonical coherente con su propio contenido, no todas apuntar a página 1 si contienen elementos diferentes;
- evitar URLs infinitas por orden/filter;
- el hub/archivo debe mantener navegación humana clara.

No basarse en `rel=prev/next` como requisito de Google: Google dejó de usar esas señales hace años. La arquitectura debe sostenerse por links/canonicals y contenido.

## Mejora pequeña que sí puede merecer la pena

### Test de variantes conocidas

Añadir una tabla de invariantes al smoke HTTP o a un checker:

```json
[
  {
    "url": "http://davidportodiaz.com/",
    "expect": "redirect",
    "canonical": "https://davidportodiaz.com/"
  },
  {
    "url": "https://www.davidportodiaz.com/",
    "expect": "redirect",
    "canonical": "https://davidportodiaz.com/"
  }
]
```

Esto es más útil que inventar reglas para parámetros que hoy no existen.

### Guardrail para nuevas rutas con `?`

Si un futuro builder/navigation empieza a emitir internal links con query strings, CI puede listarlos para revisión:

```python
if "?" in internal_href:
    findings.append({"type": "query-url-review", "href": href, "source": source})
```

No fallar automáticamente: Pagefind, formularios o parámetros funcionales pueden ser legítimos. Exigir una decisión registrada.

## Tests

- toda página indexable del registry tiene canonical válida;
- canonical indexable está en sitemap salvo excepción explícita;
- no hay dos páginas indexables reclamando la misma canonical sin motivo documentado;
- redirects HTTP/www terminan en canonical HTTPS;
- nuevas URLs internas con query se reportan para review;
- si aparece paginación, fixtures comprueban links/canonical por página;
- no usar canonical para “arreglar” páginas que realmente deberían ser `noindex`/redireccionadas.

## Qué NO hacer

- añadir `<link rel=canonical>` duplicado;
- apuntar todos los filtros a la base sin entender el contenido;
- canonicalizar páginas distintas a una sola solo para “concentrar SEO”;
- mantener parámetros crawlables infinitos;
- crear paginación si no hay volumen que la necesite;
- bloquear con robots URLs que necesitamos que Google vea para procesar canonical/noindex;
- tratar Search Console “Duplicate, Google chose different canonical” como error automático sin inspeccionar el caso.

## Coste / beneficio

Hoy: beneficio de nueva implementación grande = bajo, porque ya hay contratos y no existe la superficie problemática.
Guardrail futuro = coste bajo / valor alto preventivo.

## Definition of Done

- [x] checker actual cubre missing/collision;
- [x] registry/sitemap/canonical tienen contrato transversal;
- [x] HTTP/www auditados operativamente;
- [ ] documentar política de query/facets para futuras features;
- [ ] opcional: reportar internal query URLs si hoy no existe guardrail;
- [ ] no construir paginación/facets por adelantado.

## Recomendación de merge

**MERGE como `ALREADY_COVERED + future guardrail`.** No requiere cambios SEO productivos hoy.