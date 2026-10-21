# Decisión de búsqueda y UX: Pagefind global + shards por ciudad (21/10/2026)

**Hija [#672](https://github.com/davidpd89/web-escritor/pull/672)**, subordinada al [ADR único #666](https://github.com/davidpd89/web-escritor/pull/666). Basada en inspección de **`main` actualizado tras #665** y en la documentación de [Pagefind 1.5.2](https://pagefind.app/docs/), versión utilizada por el sitio.

## Hallazgo: NO hace falta construir otro buscador global

El proyecto ya tiene `/pagefind/`, `scripts/build-pagefind-index.py` y `pagefind@^1.5.2` en `package.json`. [Pagefind admite filtros por HTML](https://pagefind.app/docs/filtering/), [múltiples valores por página](https://pagefind.app/docs/js-api-filtering/), [metadata de resultados](https://pagefind.app/docs/metadata/) y [búsqueda multilingüe](https://pagefind.app/docs/multilingual/). En 1.5.0 incorporó búsqueda con Web Worker y búsqueda de metadata. Nuestra solución:

- **Búsqueda mundial**: Pagefind por obra, saga, autor, país, ciudad y tipo, sobre **páginas públicas reales**. Filtrar con `atlas_entity=place`; al seleccionar un libro que no tenga relación aprobada, mostrar «sin lugares documentados» y alternativas editoriales, no inventar sitio.
- **Exploración local**: el manifest país/ciudad y shards de [`atlas_facets_snapshot.py`](../../scripts/atlas_facets_snapshot.py) para solo ese destino; [`atlas-filters-preview.js`](../../research/atlas-ui/atlas-filters-preview.js) sin framework, 30 tarjetas por página, estado URL fragment y mapa bajo clic.
- **Enlace recíproco**: de `/recomendaciones/libros/<slug>/` a `/atlas-literario/lugares/<slug>/` solo cuando un ID de obra tenga relación aprobada, y viceversa. Reutilizar filtros, cards, badges y tipografía del catálogo actualizado con #665, no copiar su HTML a mano en cada destino.

### Atributos que debe escribir el futuro renderer en HTML indexable

```html
<!-- Ejemplo sintético, no publicable. Cada relación proviene del grafo aprobado. -->
<article data-pagefind-body>
  <h1 data-pagefind-meta="title">Biblioteca demostrativa</h1>
  <span data-pagefind-filter="atlas_entity:place"></span>
  <span data-pagefind-filter="atlas_country:PT"></span>
  <span data-pagefind-filter="atlas_city:dst-coimbra"></span>
  <span data-pagefind-filter="atlas_work:wrk-libro-verificado"></span>
  <span data-pagefind-filter="atlas_author:aut-identificador-estable"></span>
  <span data-pagefind-filter="atlas_relation:author_public_history"></span>
  <span data-pagefind-meta="atlas_location:Coimbra"></span>
  <p>Texto editorial original, con enlaces a fuentes documentales.</p>
</article>
```

`data-pagefind-filter` está soportado por Pagefind; puede repetirse `atlas_work` y `atlas_author` para varias relaciones en una misma página. **Punto a comprobar en QA:** atributos `atlas_*` no se filtrarán si `build-pagefind-index.py` sigue usando `git ls-files '*.html'` y los HTML se generan fuera de Git. La nueva [#677](https://github.com/davidpd89/web-escritor/pull/677) lo identifica como bloqueante.

**API de consulta preparada:** [`pagefind-global-search.example.mjs`](../../research/atlas-ui/pagefind-global-search.example.mjs) importa bajo demanda `/pagefind/pagefind.js`, hace `pagefind.search(query||null,{filters})` y solo resuelve el lote visible `item.data()`. Es un ejemplo **SIN conectar**, no crear un segundo servicio backend.

## Arquitectura visual (responsive) que aprovecha el diseño actual

1. **Entrada desde Cuaderno**: tarjeta «Viajes literarios» como sección editorial junto a «Libros recomendados», conservando el header global **Obras / Cuaderno / Herramientas**. Nuevo destino en `data/navigation.json.localNavSets.cuaderno`, con registro público `data/content-registry.json`.
2. **Hub Atlas**: hero editorial breve, input de búsqueda global, 3 entradas visuales «Por destino», «Por libro» y «Por autor» y filtros de categoría. Debajo 6–12 tarjetas destacadas con **motivo editorial**, no top genérico de 78M POIs; por defecto listado sin mapa para mantener LCP.
3. **País**: no generar necesariamente página SEO, solo opción de navegación; si se abre una landing indexable debe aportar rutas, contextos y destinos propios (no refritos automáticos).
4. **Destino**: introducción verificable, tabs **Lugares / Libros / Rutas** (cuando haya datos), chips «Escenario», «Rodaje», «Inspiración», «Homenaje», «Biblioteca», «Librería». El usuario cambia filtros sin recarga ni nuevos URLs indexables. Vista mapa mediante botón «Ver en mapa» y descarga diferida.
5. **Ficha lugar**: fotografía autorizada opcional, resumen propio, etiqueta de certeza y **tipo exacto de relación**, libro/autor/adaptación explícitos con enlace, fuente y fecha consultada, dirección pública y mapa externo (no localización falsa). «Cerca de aquí» solo si hay coords/permiso; no geolocalización por defecto.
6. **Libro**: reutilizar su ficha `/recomendaciones/`; un bloque «El libro en el mundo» con lugares aprobados, nunca nueva ficha de ISBN/afiliación duplicada.
7. **Estados vacíos**: país sin lugares, libro sin escenas verificadas, filtros 0, mapa sin permiso, 404, sin red, sin JS; mostrar recomendaciones/contexto reales, nunca «sin resultados» dentro de una caja vacía de pantalla entera.

**Móvil antes de desktop:** lista legible, controles en acordeón opcional con label visible, 1 columna de cards, filtros ordenados, botón de restablecer, acceso táctil, scroll controlado, retorno al mismo sitio. Comparar **390, 834, 1440 px** usando baselines de visual QA del sitio (no meter una UI React gigante).

## Especificación de SEO: búsquedas que sí merecen una página

| Intención | URL de destino | Condición editorial |
|---|---|---|
| «librerías históricas de París» | página de destino con lugares verificados | texto singular y fuentes; filtros sin indexar todas las facetas |
| «dónde transcurre [novela]» | ficha libro existente + enlaces a lugares | el texto o fuente primaria prueba el sitio; no mito turístico |
| «localizaciones del rodaje de [adaptación]» | ficha lugar/itinerario aprobado | P915 o film commission, bien separado de escenario de novela |
| «bibliotecas que visitar en Coimbra» | destino/lugar | dirección, acceso, fuentes/fecha real; si no se sabe horario, no inventarlo |
| «lugares de [autor]» | destinos/lugares públicos documentados | no publicar domicilio actual ni convertir nacimiento en trama |
| «rutas literarias por [ciudad]» | ruta indexable **solo si está documentada** | no prometer km/tiempos que no han sido comprobados |

**No** crear páginas para todas las combinaciones país+ciudad+obra+género, ni cubrir países sin POIs aprobados. Google penaliza estrategias de generación masiva sin valor original. JSON-LD `Place`/breadcrumbs no garantiza resultados enriquecidos; no usar reseñas fraudulentas, FAQ artificiales ni `SearchAction` retirado.

## Rendimiento y control anti-regresión

- Primer render: **HTML + CSS actual**, sin MapLibre ni Leaflet, sin Overture API, sin Open Library, sin Pagefind hasta que alguien busque y sin datos geográficos masivos en DOM.
- Presupuesto separado para `atlas-critical` y `atlas-optional-map`, declarando `import()` explícitamente en `data/performance-budgets.json` porque el checker actual **no sigue imports dinámicos**; tomar baseline real tras implementación.
- Atributos CSS/imagen respetan la web: dimensiones intrínsecas, lazy fuera del LCP, `loading=eager` para imagen LCP solo si se justifica. Map WebP estático requiere licencias por teselas.
- Lab [Lighthouse](https://developer.chrome.com/docs/lighthouse/overview) en al menos home+hub+destino+lugar; campo [Web Vitals](https://web.dev/articles/vitals) p75 cuando exista tráfico. Garantizar NO empeorar comparativamente el catálogo y home, no solo «sacar 100» en un entorno vacío.
- **Gate relevante:** [#677 QA y checklist](https://github.com/davidpd89/web-escritor/pull/677) mapea los 180 tests/70 workflows a rutas y pruebas reales; no incorporar cambios a workflows ni ampliar scope de #672 ahora.

**Decisiones abiertas que NO bloquean investigación:** prioridad de 3 puertas de entrada visual (destino/libro/autor); calidad mínima para página de país; si la categoría de POI puede tener página sin vinculación a obra; políticas de fotos de Commons/OSM; horizonte de actualización. Se pueden decidir con datos de Search Console y pruebas piloto, sin preguntar al usuario por cada detalle.

## Compatibilidad con gate QA #677: ya incorporada en el prototipo (21/10/2026)

El generador [`atlas_static_preview.py`](../../scripts/atlas_static_preview.py) ahora añade URL `og:url` idéntica a canonical y **facetas Pagefind** `atlas_entity:place|destination`, `atlas_country`, `atlas_city`, `atlas_work`, `atlas_author`, `atlas_adaptation` y `atlas_relation` a las fichas con relaciones aprobadas. Se genera una etiqueta por ID y vínculo, no una cadena arbitraria de texto de un tercero. La proyección de fuentes requiere además **título**, fecha y resumen de evidencia, alineándose parcialmente con [#669](https://github.com/davidpd89/web-escritor/pull/669).

Se corrigió una fixture del generador de shards que no incluía `sources.title`; se añadieron aserciones para canonical/OG y filtros. **Los tests no se han ejecutado**. Diferencia conocida: la [PR #677](https://github.com/davidpd89/web-escritor/pull/677) espera un manifest de release que #672, por ser preview, no construye todavía. No declarar que ambas ramas ya están integradas; solo que sus campos se han alineado conceptualmente.

### Corrección SEO crítica (21/10/2026): protección del índice global

La [documentación oficial de Pagefind](https://pagefind.app/docs/indexing/) confirma que cuando **alguna** página lleva `data-pagefind-body`, el conjunto de páginas **sin** esa marca puede quedar excluido del buscador. El prototipo #672 había empezado a marcar únicamente sus páginas Atlas, lo que podía **desindexar en Pagefind otros contenidos del sitio**. **Corregido: retirado del renderer y protegido por aserción sintética**. Mantener `data-pagefind-filter` es seguro: Pagefind recoge filtros aunque estén fuera del área de body. El [gate #677](https://github.com/davidpd89/web-escritor/pull/677) ahora detecta esta regresión antes de publicar. No se han ejecutado los tests.

## Puente Atlas ↔ catálogo real, sin duplicación (21/10/2026)

Revisado el `main` posterior a #665: `data/reading-catalogue.json` dispone de 26 registros `libros[]` con `id`, `slug`, `estado`; `scripts/build-reading-catalogue.py` construye URLs canónicas **`/recomendaciones/libros/<slug>/`**. No es correcto generar `/atlas-literario/libros/<slug>/` paralela ni adivinar slugs por título/ISBN.

- [`scripts/atlas_reading_crosslinks.py`](../../scripts/atlas_reading_crosslinks.py): valida `works[].reading_book_id` **exacto** frente a `libros[].id`, estado realmente `publicado`, slug seguro, unicidad de asociación; devuelve mapa mínimo `work_id → URL existente`. Falla ante ID inexistente, borrador, slug inválido, ID duplicado, nunca inventa enlaces Amazon.
- [`tests/test_atlas_reading_crosslinks.py`](../../tests/test_atlas_reading_crosslinks.py): **6 pruebas sintéticas** de integridad, NO ejecutadas.
- [`atlas_static_preview.py`](../../scripts/atlas_static_preview.py): acepta opcionalmente `--reading-catalogue data/reading-catalogue.json`; si se facilita, resuelve los IDs con ese validador y enlaza las obras relacionadas a la **ficha ya publicada**. Si no se facilita, se conservan nombres de obras como texto, nunca se crea una ficha duplicada. `pages_from(data, reading_links)` aplica allowlist de URL interna además del puente.
- **Regresión de veracidad**: `RELATION_SUBJECTS` en el preview impide atribuir `filming_location` a un `work`, `author_public_history` a una adaptación o `popular_claim_unverified` a una página pública. Toda relación mostrada exige `evidence_note`, aprobación, fecha, obra/autor/adaptación aprobados y fuentes HTTPS con título/fecha/evidencia. [`atlas_facets_snapshot.py`](../../scripts/atlas_facets_snapshot.py) usa la misma tabla de tipos para no mostrar en un filtro lo que el HTML oculta. Regresiones sintéticas preparadas y no ejecutadas.

**Uso futuro, NO ejecutado**:
```sh
python scripts/atlas_static_preview.py /datos/atlas-internal-v1.json \
  --reading-catalogue data/reading-catalogue.json \
  --out /datos/atlas-preview
```

No enlazar desde las páginas existentes del catálogo hacia el atlas hasta completar el gate de publicación #677 y verificar que los lugares relacionados tienen HTML real, sitemap y Pagefind, evitando regresiones del catálogo.

### Revisión final de fuente HTTPS y sincronía con contrato

El preview y el generador de shards importan la misma función `valid_https_url`: solo URL HTTPS con hostname, sin credenciales, espacios, caracteres de control ni puerto distinto de 443; la lista de fuentes de relaciones debe ser un array real. Antes, una URL `https://` sin host podía pasar el simple prefijo y terminar indexada. Ahora no genera ficha ni faceta aprobada; ambas rutas tienen pruebas de regresión preparadas, **NO ejecutadas**. No se afirma que estos gates validen la licencia o contenido de la página de origen.
