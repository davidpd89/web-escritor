# Atlas mundial · rendimiento, filtros, SEO y prototipo HTML estático (21/10/2026)

**PR hija de [#666](https://github.com/davidpd89/web-escritor/pull/666), fase de interfaz/SEO**. No modifica web desplegada. Código añadido como [prototipo de generación offline](../../scripts/atlas_static_preview.py), [pruebas sintéticas](../../tests/test_atlas_static_preview.py). No Actions.

## Plan editorial: tres entradas y una única fuente de verdad

- **Buscar un libro/autor**: enlace desde ficha de lectura existente `/recomendaciones/libros/<slug>/` a lugares de obra. No duplicar ficha de compra ni publicar enlaces Amazon nuevos con ISBN inventado.
- **Buscar un destino**: país → región (si aporta) → ciudad → lugares literarios. Destinos de contenido original comprobado, no crear una URL por combinación vacía.
- **Buscar tipo de lugar**: librerías, bibliotecas, casas de autores, homenajes, escenarios, rodajes, inspiración, rutas. El tipo **lugar** no equivale al tipo **relación**.
- **Filtros UX**: país, ciudad, libro/saga, autor, categoría de lugar, relación (escenario literal/rodaje/inspiración/homenaje), época si está acreditada, accesibilidad confirmada y distancia solo cuando hay geolocalización consentida. Conservar múltiples etiquetas por sitio.
- **Etiquetas de veracidad**: `documentado`, `inferencia editorial`, `homenaje`, `controvertido`, `pendiente`; filtros para candidatos pendientes **solo en Sheets**, no en web pública.

## Política de URLs y navegación (propuesta, pendiente de integración)

| Tipo | URL canónica | Indexación |
|---|---|---|
| Hub editorial | `/atlas-literario/` | Solo si tiene destinos aprobados |
| Destino | `/atlas-literario/destinos/<slug>/` | Solo si hay texto original sustantivo + lugar(es) aprobado(s) |
| Lugar | `/atlas-literario/lugares/<slug>/` | Solo si hay texto original, fuentes válidas y aprobación |
| Ruta | `/atlas-literario/rutas/<slug>/` | Fase posterior, recorrido real documentado |
| Obra | `/recomendaciones/libros/<slug>/` | Reutilizar ficha existente, no otro libro duplicado |
| Filtro combinado | `#pais=...&tipo=...` o estado interno de JS | **No crear URLs indexables** arbitrarias; evitar explosión de facetas |
| País / autor / saga | Enlace indexable propio **solo con páginas de valor editorial y suficiente contenido verificado** | No producir automáticamente por cada QID o etiqueta |

Fuentes de decisión: [Google faceted navigation](https://developers.google.com/crawling/docs/faceted-navigation), [canonicalización](https://developers.google.com/search/docs/crawling-indexing/canonicalization), [política de abuso de contenido a escala](https://developers.google.com/search/docs/essentials/spam-policies) y [contenido útil](https://developers.google.com/search/docs/fundamentals/creating-helpful-content).

**Error común evitado:** generar 78 millones de URLs de POI de Overture o miles de ciudades sin investigación solo para posicionar. Google advierte contra contenido masivo sin valor diferencial. Publicar pocas fichas valiosas, mantener muchos candidatos internos.

## Patrones de UI adaptables sin reescribir el sitio

- Copias MIT originales de Read the Places en [#668](https://github.com/davidpd89/web-escritor/pull/668): `facets.ts`, `BrowseList.astro`, `browse.astro` (páginas país/autor/época); `waypoints.geojson.ts` y `atlas.ts` (datos de mapas); `tiles.ts`, `plates.ts` (mapas como WebP estáticos). Están vendorizadas como investigación, **NO integradas**.
- **Nuestro sitio ya usa HTML/CSS/JS y builders Python**. El archivo [atlas_static_preview.py](../../scripts/atlas_static_preview.py) genera índice, destino y lugar sin Astro ni Svelte ni solicitudes externas. Reutiliza solo datos `approved`, resumen editorial propio y fuente HTTPS con evidencia/fecha; no escribe en sitemap ni registry.
- El prototipo incluye HTML escapado, JSON-LD neutralizado contra cierre de `<script>`, breadcrumbs, canonical, enlace opcional de mapa externo (sin tiles y sin WebGL) y `Place`/ `CollectionPage` de schema.org.
- Rechaza publicar pin exacto si precisión es `area`, `city` o `unlocated`; no transforma una obra de ficción en coordenada material exacta.
- **Aviso:** genera documentos HTML minimalistas para una vista previa. El código definitivo tendrá que usar shell, tipografía, colores y componentes reales del sitio. No montar otro diseño paralelo; usar CSS actual del atlas solo tras revisar consistencia visual y navegabilidad de #660.

## Rendimiento: presupuesto por página (objetivos, NO métricas observadas)

- [Web Vitals](https://web.dev/articles/vitals): **LCP ≤2,5s, INP ≤200ms, CLS ≤0,1**, medidos en p75 móvil/escritorio. No afirmar que la nueva sección ya los cumple sin medición de campo.
- **No cargar JS del mapa en listados o home**. Usar enlace a OSM o miniatura WebP generada previamente. Si el usuario abre mapa interactivo, activar JS bajo interacción directa y descarga parcial por destino. Fuente [web.dev facades](https://web.dev/articles/embed-best-practices).
- Primer HTML contiene **el contenido indexable** (título, resumen propio, fichas enlazadas y evidencias); sin JS funciona. Filtros client-side solo para el subconjunto visible; cuando el atlas crezca, generar índices o shards JSON **por país/ciudad**. Nunca volcar 100.000 tarjetas al DOM.
- Imágenes con `width/height`, formatos WebP y `srcset`, lazy para fuera del primer viewport; imagen LCP principal `loading=eager` cuando sea necesaria, no cargar mapa al inicio. Sin imágenes con derechos dudosos no usar placeholders de terceros.
- Introducir presupuestos de peso **por medir** (HTML, JS, imágenes, cantidad de peticiones, TBT/INP) comparando con páginas de libros existentes. No inventar un umbral de bytes «garantizado» antes de prueba real.
- No cargar `MapLibre`, `Leaflet`, teselas, Google Places ni Open Library en cada visita; cero llamadas a terceros necesarias para la lectura básica. La vista de mapas puede cargar piezas por interacción.
- Vigilar caché, WebP de teselas y licencias de proveedor: el código MIT de `plates.ts` no implica que CARTO/OSM permita cualquier uso o almacenamiento de imágenes.

## SEO estructurado: medidas y límites

- Tipo `Place` o `TouristAttraction` en lugares reales con datos auténticos; `CollectionPage` para destino y `BreadcrumbList` para jerarquía. No tratar páginas de autor como `LocalBusiness` ni añadir estrellas/comercio sin proveedor real.
- Fuente [schema.org TouristAttraction](https://schema.org/TouristAttraction) y [Google BreadcrumbList](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb). Un objeto JSON-LD válido **no garantiza** resultados enriquecidos.
- **Corrección del patrón upstream**: en `apps/web/src/lib/structured-data.ts` de Read the Places aún figura `SearchAction` como aspirante a «sitelinks search box». Google **retiró esta función en noviembre de 2024** ([comunicado oficial](https://developers.google.com/search/blog/2024/10/sitelinks-search-box)). No copiar esa justificación SEO aunque se guarde el archivo upstream literal en #668.
- También `ItemList` no concede por sí solo el carrusel de Google para una lista de lugares literarios: las [features admitidas](https://developers.google.com/search/docs/appearance/structured-data/carousel) son específicas. No prometer «carrusel enriquecido» del atlas.
- Un JSON-LD con `Book` no debe afirmar `isAccessibleForFree` ni fotos/disponibilidad cuando no estén comprobados.
- Prevención de URLs huérfanas: primero generar fichas, después enlazar desde índices, registrar en `data/content-registry.json`, `build-sitemap.py` y `Pagefind` actuales. Se documentó que el builder legado hacía tarjetas enlazando a fichas inexistentes.

## Pruebas de vista previa preparadas, no ejecutadas

1. solo índice/destino/lugar aprobados;
2. sin páginas vacías cuando no hay aprobados;
3. sin fuentes válidas o texto editorial mínimo → no se publica;
4. dato externo malicioso como `</script>` o `<img onerror>` queda escapado;
5. pin exacto solo con precisión adecuada;
6. relaciones candidatas o sin evidencia NO visibles.

**Modo futuro de generación**: `python scripts/atlas_static_preview.py path/a/snapshot-aprobado.json --out .ci/atlas-preview` (NO ejecutar sobre carpeta de producción). El programa exige carpeta que incluya `atlas-preview` para reducir errores. Los tests están escritos, pero **NO se ejecutan en esta fase** por la regla del proyecto.

## Pendientes necesarios antes de integrar en main

- Ejecutar tests y QA de navegador autorizado; comprobar integración con shell sin romper menú, pie, breadcrumbs ni CLS.
- Integrar contrato [#669](https://github.com/davidpd89/web-escritor/pull/669) para validar referencias antes de generar, no fiarse solo del `status`; revisar criterio de texto de calidad (140 caracteres es umbral de seguridad **técnico**, NO garantía SEO).
- Abrir PR aparte de generador de rutas e índice países/autores cuando haya suficientes aprobados.
- Construir filtros combinados accesibles con back/forward, etiquetas múltiples, paginación y noindex de búsquedas arbitrarias.
- Medir Chrome en móvil y tamaños de texto, teclado, no-JS, contraste y contrastes de design system; indexación real tras publicación.

## 22/10? No: ampliación de la misma jornada 21/10/2026 — shards para filtros mundiales

Se ha añadido [scripts/atlas_facets_snapshot.py](../../scripts/atlas_facets_snapshot.py) y [tests/test_atlas_facets_snapshot.py](../../tests/test_atlas_facets_snapshot.py) (cuatro pruebas sintéticas, NO ejecutadas).

**Flujo de escala:**
1. La portada solo contiene índice HTML y enlaces a países/destinos, sin 100.000 registros de lugares.
2. Se publica (en un futuro, no ahora) un manifiesto pequeño `/atlas-literario/facets/index.json` con países, destinos y conteos por categoría.
3. Cuando el usuario elige **ciudad/destino**, se descarga **un único shard** `/atlas-literario/facets/destinos/<slug>.json` de los lugares aprobados de esa ciudad, con tipos y relaciones aprobadas a libros/autores/adaptaciones.
4. El navegador filtra en memoria **solo el shard activo** (tipo de lugar, obra, autor, relación, palabras). Cambiar de ciudad intercambia el shard; no cargar mapas ni miles de elementos en el primer render.
5. El manifest no genera por sí mismo nuevas páginas SEO: las URLs canónicas son las fichas aprobadas. Los filtros combinados nunca generan rutas rastreables infinitas.

**Siguiente fase:** UI JS accesible con país→ciudad→obra/tipo/autor, estado URL fragment (no query rastreable), resultados paginados, `aria-live` con recuento, soporte teclado y back/forward. El snapshot ya queda preparado para esa UI sin llamar APIs de terceros.

**Invariante de privacidad:** los shards solo contienen ID público, nombre, tipo, URL y enlaces de relaciones aprobadas; no raw dumps, emails, fotos sin derechos, coordenadas de domicilios privados ni notas internas. `MAX_TEXT_LENGTH=140` del preview NO garantiza utilidad, así que el gate editorial y QA de contenido real seguirán existiendo.

**Corrección nueva:** el renderizador aborta si dos lugares o destinos generarían la misma URL (no sobrescribe slugs homónimos) y omite el hub si no hay destinos publicables; tests de regresión escritos.

## Prototipo JS adicional (no cargado en producción)

- [research/atlas-ui/atlas-filters-preview.js](../../research/atlas-ui/atlas-filters-preview.js): JavaScript autónomo que **no necesita framework ni librería externa**. Primer fetch de `facets/index.json` tras foco/clic en controles; solo descarga `facets/destinos/<slug>.json` de la ciudad seleccionada. Filtra por país, destino, tipo, obra, autor, tipo de vínculo y búsqueda normalizada. Muestra 30 resultados por página, utiliza `document.createElement/textContent` (no `innerHTML` con texto externo), protege las URLs destino y conserva estado en hash para no multiplicar páginas indexables.
- [research/atlas-ui/filters.example.html.txt](../../research/atlas-ui/filters.example.html.txt): HTML semántico de controles con labels, estados `aria-live`, paginación con botones y enlace conceptual a CSS común. (guardado como `.txt` para que los chequeos del sitio no lo traten como página) **Este HTML y JS no se han insertado en ninguna página**, por tanto no representan una experiencia web ya funcional. Requieren la integración futura del script (defer) en la página real del hub junto con enlaces SSR para lectores sin JS.
- El selector país es ISO2 visible temporalmente; integrar nombres locales `Intl.DisplayNames(['es'])` o tabla propia cuando se apruebe, no presentar códigos técnicos al usuario.
- **Pendiente** de test de teclado, accionado móvil, estado hash al retroceder, fallos de red, múltiples filtros, 0 resultados, 10k/100k fichas, CSP real y timeouts. Evitar añadir a main sin validar que no existe regresión.
- El JS no hace geolocalización, no llama a APIs ni mapas, no ejecuta búsquedas de IA y no usa datos de cuentas/usuarios; `URLSearchParams` para hash no envía criterios a servidor.
