# QA Atlas — matriz de integración exacta con el CI ya existente

Fecha **21/10/2026**. Hija de [#666, ADR-000](https://github.com/davidpd89/web-escritor/pull/666). **Sólo tests y preparación: no workflows nuevos ni ejecutados, no merges.** El proyecto ya cuenta con **180 entradas en tests/** y **70 workflows** en la consulta de main de esta ronda; estas cantidades son un snapshot, no significan que todos estén activos o pasen.

## Hallazgos verificables en `main`: qué hay y qué no cubre todavía el Atlas

| Control existente | Rutas del código real y mecanismo | Extensión necesaria cuando las fichas se generen |
|---|---|---|
| **Atlas legado** | `scripts/build-atlas-literario.py`, `tests/test-atlas-literario.py`, `data/atlas-literario.json` | **Bloqueante real:** builder solo genera **index.html** y JSON, pero las tarjetas enlazan a `/atlas-literario/<slug>/` que no se genera. Todos los 12 registros siguen `planned`. Añadir generación de fichas y tests de 404/manifest, migrar index de prototipo a directorio real. |
| **SEO calidad** | `scripts/check-seo-meta-quality.py`, `tests/test-seo-meta-quality.py` | Aceptar todas las nuevas rutas: h1, título+descripción únicos, canonical con ruta, `og:url` coincidente, OG Twitter, noindex donde aplique. Las pruebas existentes mutan HTML de ejemplo, pero no conocen nuevo catálogo del atlas hasta que se incluya en el corpus. |
| **Sitemap** | `scripts/build-sitemap.py`, `tests/test-reading-catalogue.py` | Las páginas deben tener fichero HTML canónico **real** y aparecer solo aprobadas; no incluir facetas `#`, placeholders, destinos sin evidencia ni artefactos QA. Vigilar XML `lastmod` con fechas reales. |
| **Pagefind global** | `scripts/build-pagefind-index.py`, `tests/test-build-pagefind-index.py` | **Hallazgo técnico:** actualmente el corpus elegible procede de `git ls-files '*.html'` más `data/content-registry.json` y `meta robots`. Si Atlas escribe HTML solo a `dist/` fuera de Git, **no se indexará automáticamente**. Elegir una de 2 vías: (A) generator guarda rutas aprobadas en archivos Git versionados antes del build de Pagefind; (B) modificar el builder para indexar el directorio público generado y mantener allowlist equivalente. **No mantener ambas sin razón.** |
| **Search UX Pagefind** | `package.json` fija `pagefind ^1.5.2`, biblioteca ya instalada por CI | [Pagefind filtros nativos](https://pagefind.app/docs/filtering/), [JS API](https://pagefind.app/docs/js-api-filtering/), [metadatos](https://pagefind.app/docs/metadata/). Añadir `data-pagefind-filter` a HTML aprobado: `atlas_entity`, `atlas_country`, `atlas_city`, `atlas_work`, `atlas_author`, `atlas_relation`; múltiples obras/autores por lugar. **No crear segundo índice mundial**: [wrapper de muestra en #672](https://github.com/davidpd89/web-escritor/pull/672). Shards de ciudad sólo para exploración local. |
| **Presupuestos deterministas** | `data/performance-budgets.json`, `scripts/check-performance-budgets.py`, `tests/test-performance-budgets.py`, `.github/workflows/performance-budget-qa.yml` | Añadir **dos budgets separados** con baseline medido: `atlas-list-runtime` (JS/CSS críticos) y `atlas-map-optional` (MapLibre/Leaflet/supercluster solo bajo clic). El script sigue CSS imports, imports JS estáticos, **NO sigue `import()` dinámico**; el mapa necesita entrada explícita o escaparía de los límites. No inventar bytes antes de medir. `performance-budget-qa.yml` actualmente filtra cambios a assets/manifest/scripts genéricos; asegurar que los futuros ficheros coinciden con trigger. |
| **Lighthouse CI** | `lighthouserc.json`, `.github/workflows/lighthouse-ci.yml` | **Lista de rutas fija**, hoy **no incluye** `/atlas-literario/`: añadir hub, un destino y un lugar representativos, sin retirar los controles de sitio. thresholds actuales: performance aviso 0,85; a11y error 0,97; SEO error 0,98; LCP 3500 ms aviso, CLS ≤0,1 error; TBT 400 ms aviso. Exigir también comparación con páginas de /recomendaciones/. Core Web Vitals reales se miden p75, no equivalentes a score laboratorio. |
| **Accesibilidad** | `.github/workflows/pa11y-baseline.yml`, `.pa11yci`, `scripts/check-interaction-a11y-contracts.py` | Pa11y visita URLs del **sitemap**: si falta allí Atlas, ninguna prueba lo cubre. Incluir país/ciudad/libro, 0 resultados, control mapa opt-in, teclado, aria-live, foco al borrar, mapa no exclusivo; revisión WCAG 2.2 AA. |
| **Visual** | `qa/visual-regression-browser.mjs`, `qa/visual-baselines/`, `.github/workflows/visual-regression-qa.yml` | ROUTES es fijo (home, libros, cuaderno, recomendaciones, herramientas, asistente, legal) y tamaños 390×844 / 834×1194 / 1440×900. Añadir Atlas hub+destino+lugar; baseline **capturar en ubuntu-latest**, no local, por discrepancias tipográficas. El workflow decide relevantes por HTML/assets, así que **cambiar solo el builder Python podría NO activar comparación visual** sin retocar detection. |
| **Cross-browser** | `qa/cross-engine-smoke.mjs` | Rutas fija: ampliar con atlas; Chromium/Firefox/WebKit y 390px, tocar select/teclado/back, error/abort fetch. Preparado como script independiente en esta PR hasta integración. |
| **Seguridad CSP** | `qa/csp-public-shell-browser.mjs`, `.github/workflows/csp-public-shell-qa.yml` | Atlas debe usar mismo CSP y shell; no abrir `connect-src` a decenas de APIs por los filtros. Las páginas iniciales no solicitan proveedores externos ni cargan MapLibre. Si se activa mapa, permisos/teselas deben auditarse por destino y consentimiento funcional adecuado. |
| **Links** | `tests/test-public-link-contracts.py`, `tests/test-fragment-links-resolve.py`, `.github/workflows/broken-links.yml` Lychee | Enlaces a fichas generadas, referencias externas, anclas y alias de migración. El checker de fragments trabaja con HTML versionado; URLs generadas fuera de Git no entrarán automáticamente. Externas 429/robots y alojamiento no es prueba de origen editorial de la afirmación. |
| **Imágenes** | `tests/test-check-responsive-images.py`, `tests/test-check-image-format-ladder.py`, `scripts/check-responsive-images.py` | Tarjetas y fichas con `width/height`, alt útil, imagen LCP no lazy indiscriminadamente, versiones localizadas con licencia/atribución por archivo. No usar fotos de Commons si falta licencia individual ni foto de portada con derecho de terceros. |
| **Catálogo de lectura** | `scripts/build-reading-catalogue.py`, `assets/reading-catalogue.js/css`, `tests/test-reading-catalogue.py`, `.github/workflows/reading-general-catalogue-ux-qa.yml` | #665 YA FUSIONADA alteró filtros, catálogo y autor: enlazar IDs, no copiar plantillas/cubiertas sin validación. Regresión sobre `/recomendaciones/`, enlaces de afiliación y reviews moderadas. |
| **Publicación automática** | `scripts/publish-reading-refresh.py`, `.github/workflows/reading-catalogue-sync.yml` | Allowlist de rutas de catálogo no incluye Atlas. No crear segundo escritor concurrente ni ampliar allowlist antes de revisión de seguridad por rutas, bloqueos de carreras y generación de sitemap/Pagefind. |

## QA creado en esta PR (NO ejecutado)

1. **[scripts/check_atlas_release_contract.py](../../scripts/check_atlas_release_contract.py)**: validador offline sobre build estático **terminado**, `--root` y `--manifest`; comprueba URLs del manifest, páginas HTML, canónicos, title/description únicos, JSON-LD y BreadcrumbList, noindex indebido, HTML extra no aprobado, fugas de nombres de campos privados, enlaces a 404, facetas `atlas_entity` obligatorias para Pagefind y que hub/destino no carguen mapa pesado. No sustituye validación de derechos ni de exactitud.
2. **[tests/test_atlas_release_contract.py](../../tests/test_atlas_release_contract.py)**: nueve casos sintéticos en directorios temporales; incluye rotura intencionada de enlace, fuga privada, colisión canonical, mapa eager, JSON-LD y duplicado.
3. **[qa/atlas-release-browser.mjs](../../qa/atlas-release-browser.mjs)**: harness Playwright aislado; con un build publicado en carpeta local y manifest comprueba 3 navegadores, móvil/escritorio, navegación sin JS, ausencia de peticiones de mapa, desbordamiento, filtros país+ciudad y errores JS. Por diseño **falla si no existe** interfaz real de Atlas: no simular éxito. No está enganchado a ningún workflow.

### Contrato del manifest aprobado (archivo futuro generado, NO existe aún)

```json
{
  "schema_version": 1,
  "routes": [
    {"url": "/atlas-literario/", "kind": "hub"},
    {"url": "/atlas-literario/destinos/ciudad-verificada/", "kind": "destination"},
    {"url": "/atlas-literario/lugares/poivisitado/", "kind": "place"}
  ]
}
```

Debe guardarse en `atlas-release-manifest.json` al lado del HTML generado, **sin notas internas, datos sensibles ni fuentes protegidas**. El gate y el browser harness consumen ese mismo manifest: 1 lista de URLs aprobadas, no 3 listas manuales divergentes. **Si no hay destinos aprobados, no se puede ejecutar el gate positivo de lanzamiento y no se publica Atlas**.

### Ejecución POSTERIOR a desarrollo, prohibida por ahora

```bash
# Solo cuando el usuario autorice QA. Nunca se ha ejecutado ahora.
python -m unittest discover -s tests -p 'test_atlas_release_contract.py' -v
python scripts/check_atlas_release_contract.py --root /ruta/build-estatico --manifest /ruta/build-estatico/atlas-release-manifest.json
ATLAS_BROWSERS=chromium,firefox,webkit node qa/atlas-release-browser.mjs --root /ruta/build-estatico

# A continuación, revalidar QA del repo y registrar evidencias:
python tests/test-atlas-literario.py
python tests/test-seo-meta-quality.py
python tests/test-build-pagefind-index.py
python tests/test-fragment-links-resolve.py
python scripts/check-performance-budgets.py --check
python scripts/build-site-shell.py --check
# Las pruebas de browser, Pa11y, visual y LHCI se programan tras garantizar
# que las rutas Atlas se generan y figuran en manifest, sitemap y Pagefind.
```

## Matriz de casos funcionales pendientes para navegador y QA editorial

| Área | Escenarios mínimos | Estado |
|---|---|---|
| Destino | 0/1/50/500 lugares; país homónimo; cambio rápido de país; país sin ciudades | Por probar |
| Búsqueda | obra/saga/autor que devuelve ciudades, sin coincidencias, acentos y alias multilingüe, Pagefind en offline/worker no soportado | Por probar |
| Tipos de vínculo | libro **escena explícita**, autor **vivió en** (patrimonio público), adaptación **rodada en**, **homenaje**; no cruzar unos con otros | Por probar |
| Mapa | se mantiene vista lista con JS desactivado; mapa no carga hasta interacción; permisos tiles y atribución | Por probar |
| Seguridad | descripción con `</script>`, `javascript:`, enlaces externos con `target=_blank`, claves, notas de revisión, ruta `../` | Por probar |
| SEO | 3 canonicals para 3 entidades distintas, nunca duplicados; solo aprobados en sitemap, Pagefind y HTML; no facetas de búsqueda indexables | Por probar |
| Rendimiento | 2G/4G móvil emulado, 390/834/1440, 1/100/1000 POIs; budgets archivo y LCP/INP/CLS | Por probar |
| Licencias | Overture, OSM ODbL, Pleiades CC BY, FilmMap CC0, Commons por archivo, ISBN/portadas | Revisión humana |
| Resiliencia | API 429/503, actualización de dump fallida, foto retirada, proveedor desaparece y slug renombrado | Por probar |
| Publicación | colisión de dos writers, rollback de cambios, nuevo lugar antes de que sitemap/Pagefind estén actualizados | Por probar |

### Decisión de arquitectura sobre Pagefind

**Preferida**: el Pagefind existente ya puede filtrar el HTML por atributos `data-pagefind-filter` (autor, ciudad, obra, tipo de relación) y devolver metadatos `data-pagefind-meta`. [Documentación oficial filtros](https://pagefind.app/docs/filtering/) y [API JavaScript](https://pagefind.app/docs/js-api-filtering/). Para la UX: Pagefind atiende **búsqueda mundial**, mientras los shards JSON de [#672](https://github.com/davidpd89/web-escritor/pull/672) sirven **exploración detallada de una ciudad**. No crear un backend ni índice invertido mundial nuevo hasta demostrar carencia funcional.

**Importante**: según documentación de Pagefind 1.5.2 (versión declarada por la web), búsquedas enriquecidas admiten metadata de autor y filtros multi-valor. El `pagefind` del repo requiere URLs generadas dentro del corpus índice; la funcionalidad documental no arregla por sí sola su proceso `git ls-files`.

## Orden para incorporar gates cuando se permita ejecutar

**No activar nada ahora.** Tras integración del builder real, preparar una PR QA minúscula con solo: (a) incluir Atlas en matrices Lighthouse/visual/Pa11y/CSP/cross-engine, (b) generar manifest desde el mismo snapshot, (c) ejecutar test offline nuevo, (d) presupuestos report→enforce una vez medidos. Los workflows necesarios deben respetar los *required checks* existentes y no generar contextos faltantes por filtros `on.pull_request.paths`.

**No hay evidencia de resultado PASS**: esta PR contiene código de comprobación y diseño de activación solamente.

**Último ajuste:** el gate inspecciona que cada página destino/lugar/ruta incluya `data-pagefind-filter=atlas_entity:<kind>`; las fixtures sintéticas añaden estas etiquetas. Evita que una ficha exista en HTML pero no pueda filtrarse por categoría de entidad en Pagefind, siempre que la generación del propio índice incluya esas páginas. **Nueve** pruebas sintéticas preparadas, no ejecutadas.

### Nuevo gate contra desindexación masiva involuntaria

La página [Pagefind Indexing](https://pagefind.app/docs/indexing/) advierte que etiquetar **solo algunas** páginas con `data-pagefind-body` puede excluir todas las demás sin esa marca. El sitio existente indexa body por defecto; la #672 incluyó la marca en su primer prototipo, y ahora la **ha eliminado**. En [`check_atlas_release_contract.py`](../../scripts/check_atlas_release_contract.py) se rechaza esa marca en las páginas Atlas, con **novena prueba sintética**. No activar cambio global a `--root-selector` sin comprobar todo el contenido existente y sin migración homogénea.

## Regresión de enlaces Atlas → libros existentes (21/10/2026)

[#672](https://github.com/davidpd89/web-escritor/pull/672) ahora puede enlazar únicamente obras identificadas por `reading_book_id` en `data/reading-catalogue.json`, usando el slug publicado real del catálogo. **Este gate #677 también se ha ampliado:** si una página del Atlas enlaza a `/recomendaciones/libros/<slug>/`, verifica que **`index.html` exista en el build final**. Si es una ruta malformada o una URL inventada, bloquea el release. Incluye un caso positivo/negativo sintético (fichero ausente → error; fichero presente → permitido).

**10 pruebas sintéticas en este módulo, NO ejecutadas.** Esto complementa el comprobador de relaciones y enlaces internos Atlas y protege la conversión hacia recomendaciones sin romper SEO, canonicals ni ventas existentes. No es un vínculo de afiliación ni modifica el catálogo.

**Actualización 21/10:** 10 pruebas sintéticas escritas, sin ejecutar. Además de la protección de Pagefind, una ficha Atlas que enlaza a `/recomendaciones/libros/<slug>/` obliga a que exista `index.html` real en el build de producción, cerrando el hueco de enlaces cruzados. Todo queda supeditado a pruebas reales y manifest editorial.
