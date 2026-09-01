# A.9 · Revalidación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #158  
Decisión operativa: **ALREADY_COVERED · NO_CODE · FUTURE_FEATURE_CONTRACT**

## Decisión cerrada

No se crea un nuevo sistema de canonicalización, un auditor de parámetros ni infraestructura de paginación mientras el sitio no publique realmente una familia de URLs con filtros/paginación.

La arquitectura actual ya protege la parte material:

- las páginas indexables declaran canonical;
- `scripts/check-internal-graph.py` reporta canonical ausente y colisiones;
- `scripts/build-sitemap.py` usa la canonical como URL publicada y deduplica por `loc`;
- navegación/registry/sitemap se comprueban en CI.

A.9 se reabre cuando una feature real introduzca nuevas URLs, no antes.

## Revalidación del repo actual

Búsquedas sobre `main`:

```text
?page=          → 0 resultados
URLSearchParams → 0 resultados
rel="next"      → 0 resultados
```

No existe una familia pública equivalente a:

```text
/cuaderno/?page=2
/herramientas/?categoria=manuscrito
/recomendaciones/?orden=popularidad
```

Por tanto, hoy no hay variantes indexables por query que clasificar como canonical/noindex ni páginas 2+ que proteger.

## Autoridades actuales

### `scripts/check-internal-graph.py`

El checker existente posee la integridad de canonical:

- `missing-canonical` en HTML indexable;
- `canonical-collision` cuando varias páginas reclaman la misma canonical;
- resolución de enlaces internos contra el inventario real;
- huérfanos y enlaces rotos como responsabilidades relacionadas.

Crear `check-canonical-params.py` ahora duplicaría autoridad sin tener una superficie nueva que auditar.

### `scripts/build-sitemap.py`

El sitemap:

- parte del HTML indexable real;
- excluye `noindex` y superficies internas;
- normaliza canonical HTTPS;
- deduplica por canonical;
- usa `dateModified` fiable para `lastmod` cuando existe;
- tiene `--check` en CI.

Esto alinea internal links, canonical y sitemap alrededor de una única URL pública.

## Documentación oficial vigente

### Canonicalización

Google Search Central:

https://developers.google.com/search/docs/crawling-indexing/canonicalization

La documentación actual mantiene las reglas relevantes:

- redirects y `rel="canonical"` son señales fuertes;
- sitemap es una señal más débil y debe ser coherente con la canonical elegida;
- las páginas propias deben enlazar internamente a la URL canónica;
- es buena práctica usar self-canonical;
- deben evitarse señales contradictorias.

### Paginación

Google Search Central:

https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading

Contrato vigente si en el futuro existe paginación real:

- cada página de la secuencia necesita una URL propia;
- Google trata cada URL paginada como una página distinta;
- **no se debe canonicalizar página 2, 3, etc. a página 1**;
- cada página debe tener su propia canonical;
- la secuencia debe enlazarse con `<a href>` rastreables;
- Google ya no usa `rel="next"` / `rel="prev"` como señal, aunque otros consumidores podrían usarlos.

### Filtros y ordenaciones

La misma guía de paginación recomienda evitar indexar variaciones de la misma lista creadas por filtros/ordenaciones, por ejemplo `?order=price`, mediante una política explícita de indexación/rastreo.

Google también mantiene documentación específica sobre faceted navigation:

https://developers.google.com/crawling/docs/faceted-navigation

Su problema principal es la explosión de combinaciones crawlables. La decisión debe tomarse antes de lanzar la feature: o impedir que esas combinaciones formen un espacio rastreable infinito, o diseñarlas deliberadamente si realmente necesitan crawling/indexación.

## Contrato futuro por tipo de URL

### 1. Parámetro de estado de UI sin intención indexable propia

Ejemplo hipotético:

```text
/herramientas/?categoria=manuscrito
```

Si solo representa la misma colección filtrada para el usuario:

- no convertir automáticamente cada combinación en landing SEO;
- evitar generar un grafo infinito de hrefs crawlables;
- decidir `noindex`/crawl policy según cómo se sirva la vista;
- conservar una base canónica clara;
- no meter variantes accidentales en sitemap.

El mecanismo concreto depende de la implementación real. No se predefine una regex universal hoy.

### 2. Intención editorial independiente

Si una selección merece indexarse porque responde una intención propia, debe convertirse preferiblemente en una URL editorial canónica estable, como ya ocurre con:

```text
/recomendaciones/portal-fantasy-espanol/
```

No esconder una página sustancial detrás de un parámetro accidental solo para después intentar resolver su canonicalización.

### 3. Paginación real

Si una colección crece hasta necesitar páginas 2+:

```text
/cuaderno/?page=2
/cuaderno/?page=3
```

entonces:

- URLs distintas;
- links secuenciales crawlables;
- cada página self-canonical;
- no canonicalizar todas a página 1;
- no usar fragmentos `#page=2` para representar páginas rastreables;
- añadir fixtures/tests concretos de esa familia;
- revisar sitemap según la arquitectura elegida y contenido real.

### 4. Ordenaciones duplicadas

Variantes que solo reordenan el mismo corpus no deberían convertirse por defecto en nuevas páginas indexables. La feature debe decidir cómo impedir indexación/crawl innecesario en vez de dejarlo al azar.

## Por qué NO se añade un “query URL scanner” ahora

Un checker que falle por cualquier `?` sería incorrecto:

- parámetros funcionales pueden ser legítimos;
- tracking no equivale a página indexable;
- formularios, búsqueda y estados UI tienen semánticas distintas;
- el repo actual no expone la familia problemática que justificaría ese gate.

Un scanner informativo también tendría escaso valor hoy: cero resultados conocidos y ningún consumidor de la señal.

Cuando aparezca la primera feature con parámetros, el test debe vivir junto a la autoridad que genere esas URLs y validar sus invariantes concretos.

## Alternativas descartadas

1. **Nuevo checker canonical genérico** — duplica `check-internal-graph.py`.
2. **Paginación preventiva** — no existe volumen/superficie actual.
3. **Canonical de todas las futuras páginas a page 1** — contradice la guía vigente para paginación real.
4. **`rel=next/prev` como requisito Google** — Google ya no lo usa.
5. **Fallar CI por cualquier query string** — falsos positivos y ausencia de contrato.
6. **Indexar cada filtro automáticamente** — riesgo de explosión de URLs/crawl.
7. **Resolver futuras features con una política universal antes de conocer su semántica** — sobrearquitectura.

## Trigger de reapertura

A.9 se reabre únicamente cuando una PR introduzca alguno de estos elementos:

- paginación real;
- filtros con URL;
- ordenaciones con URL;
- resultados de búsqueda indexables;
- variantes query que aparezcan en internal links/sitemap;
- duplicación/canonical conflict reproducible que los checks actuales no cubran.

Esa PR debe declarar explícitamente:

```text
qué URLs existen
cuáles son indexables
cuáles son crawlables
qué canonical tiene cada una
qué entra en sitemap
qué enlaces internos las descubren
qué tests protegen el contrato
```

## Definition of Done

- [x] historia de #135 preservada;
- [x] `main@291c8c6…` inspeccionado;
- [x] `?page=` ausente;
- [x] `URLSearchParams` ausente;
- [x] `rel="next"` ausente;
- [x] `check-internal-graph.py` revalidado como autoridad canonical;
- [x] `build-sitemap.py` revalidado;
- [x] documentación canonical vigente contrastada;
- [x] documentación de paginación vigente contrastada;
- [x] política de facetas/filtros vigente contrastada;
- [x] self-canonical por página paginada fijado como contrato futuro;
- [x] no existe gap de runtime actual;
- [x] trigger futuro ligado a una feature real.

**Conclusión:** A.9 sigue correctamente como `ALREADY_COVERED`. La mejora de producción no es escribir código para URLs que no existen; es dejar un contrato preciso para que la primera feature de filtros/paginación nazca sin deuda canonical.