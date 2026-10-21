# Benchmark de productos operativos y patrones adoptables (21/10/2026)

**Esta es evidencia de producto, NO sustituto del ADR-000.** [Referencia canónica](https://github.com/davidpd89/web-escritor/blob/research/viajes-literarios-atlas-2026-10-21/docs/ideas/viajes-literarios/README.md). Hija [#670](https://github.com/davidpd89/web-escritor/pull/670) del padre #666. Sitios públicos inspiran UX; **sus datos, diseños y fotografías no se copian sin licencia**.

## Qué ya está montado en otros sitios

| Producto vivo y evidencia pública | Qué hace bien | Adaptar SIN copiar material protegido | Trampa a evitar |
|---|---|---|---|
| [Read the Places](https://readtheplaces.com/) / [código](https://github.com/markselby9/readtheplaces.com) | Obras → paradas en secuencia narrativa; ciudades, autor, era, tipo de evidencia | Código MIT original archivado en #668: `BrowseList.astro`, `facets.ts`, `waypoints.geojson.ts`, `tiles.ts`, JSON-LD; **portar algoritmo** al shell Python existente | Sus libros/datasets CC BY-SA y textos/mapas con derechos separados; `SearchAction` rich result obsoleto |
| [Finding Fiction — map](https://www.findingfiction.org/map) | Buscar ambientación por género, subgénero, continente, país, ciudad y época; agrupar pins por cantidad de libros; **no pin para ficción no resoluble** | UX multiselector, distinción `setting resolved` vs `fictional/unresolved`, contar y agrupar, navegación mapa↔lista | No confundir localización temática con calle literaria exacta; si el mapa falla debe seguir funcionando lista |
| [Writer’s Path, Londres](https://www.writerspath.co.uk/literary-map) | Patrimonio biográfico: placas, casas públicas, museos, librerías, cafés y estatuas con fichas, buscador y propuestas comunitarias | Template de lugar y la distinción casa museo pública / placa / homenaje / negocio; CTA «sugerir lugar» (revisión humana) | No exponer vivienda actual ni usar testimonios como prueba definitiva |
| [Map A Story](https://mapastory.com/) | Libro buscado por título → mapa de escenarios + contexto de paradas | Entrada principal «busca tu novela», autocomplete sobre **índice estático interno**, propuesta de ruta narrativa cuando hay fuente | No afirmar «todas las escenas» por un modelo si no hay prueba precisa |
| [Novels: On Location](https://github.com/ivanoblomov/novels-on-location) | App de novelas por destino y navegación mapa (mashup Google Maps/Books) | Patrón ciudad↔novela, fichas y filtros para viajero | Sin LICENSE visible en raíz; README describe MongoDB/Google Maps; **no copiar software sin permiso**, evitar costes/APIs de backend |
| [Atlas of Stories](https://github.com/rowanammar/Atlas-of-Stories) | Entrada por libro y mapa MapLibre; cache Firestore | Separar recuperación de obra, evidencia y caché de geocoding como módulos | Backend Gemini + Cloud Run/Firestore y secrets, no 100% gratis ni libre de LLM; sin LICENSE visible en raíz, no copiar |
| [World Book Atlas](https://github.com/Simon-byte-png/world-book-atlas) | Experiencia mundial por país, línea temporal, título original/traducido y búsqueda | «Explorar por continente/país» y título multilingüe, filtros por época | Su README admite cubiertas/reseñas de terceros y 154 títulos curados; **geografía del autor/origen del libro ≠ escenario de la trama**. Sin LICENSE raíz verificada, no copiar |
| [Literature Atlas mapped](https://literatureatlas.com/map/) | Exploración libros por región y periodo, 3.467 entradas en el sitio consultado | Filtro región×periodo y advertencia de registros sin localización fiable | En su propia web región suele significar **origen de obra**, no escenario; no mezclar hechos |
| [Movie Scene Map](https://moviescenemap.com/) · [FilmMap CC0](https://github.com/Flightmussy/filmmap-dataset) | Rodajes reales de cine/TV geolocalizados, fuente separada de animación/manga/videojuegos por P915/P840, datos abiertos de 161 países | Enlazar adaptación literaria → rodajes con QID y fuente, sin inferir escena concreta; CSV/GeoJSON por lotes | Copia MIT de su servidor MCP en #668 solo referencia; la web no dependerá de MCP en tiempo de visita |
| [Knight Lab StoryMapJS](https://github.com/NUKnightLab/StoryMapJS) | Narración secuencial por puntos, controles y traducciones | Inspirarse para futura ruta narrativa como componente opcional aislado | LICENSE raíz **MPL-2.0** pero `package.json` dice ISC; no vendorizar sin resolver licencia. Stack legacy con Leaflet 0.7 |

## Consecuencias de diseño: exactamente cuatro superficies, no veinte

1. **Hub `/atlas-literario/`**: buscar por libro o autor (Pagefind/índice local) y explorar por país/destino/tipo. Mosaico compacto de ciudades aprobadas; cero pins/renderers externos en carga inicial.
2. **Destino `/atlas-literario/destinos/<slug>/`**: descripción propia con fuente, puntos agrupados por librerías / bibliotecas / escenas / biografía / rodaje; filtros JS por shard del destino. Mapa opt-in, listado SSR para rastreo y sin JS.
3. **Lugar `/atlas-literario/lugares/<slug>/`**: un solo POI canónico, historia editorial, foto licenciada opcional, accesibilidad/horarios con fecha, obras relacionadas y el **tipo de vínculo** explícito con fuente (escena literal ≠ rodaje ≠ homenaje), mapa externo seguro.
4. **Obra/autor**: NO crear segundo perfil comercial ni duplicar SEO; enlazar desde el libro/autor del catálogo vigente. **Rutas** posteriores si hay bastantes puntos y trazados legítimos, con (orden) narrativo separado de trayecto caminable.

## Contrato de navegación (puertas equivalentes)

- **Destino primero:** continente/región → país → ciudad → lugares → libro(s); el nombre regional es navegación, no página SEO por país sin contenido original.
- **Libro primero:** título/saga/autor consultados en Pagefind o índice compacto → IDs de obras → destinos que tienen relaciones públicas aprobadas → lugares de la obra. Si el libro no está en `/recomendaciones/`, hacer una ficha contextual de atlas **solo si editorialmente aprobada**, sin inventar una edición ni ASIN.
- **Autor primero:** nombre/QID con desambiguación → obras existentes + museos/lugares biográficos públicos aprobados → ciudades. No mezclar «autor nació aquí» con «libro ocurre aquí».
- **Rutas:** visita física con orden y desplazamientos factibles **no es** la secuencia literaria; en dataset dos listas diferentes, `narrative_order` y `route_stop_order`.

## Escala, SEO y robustez

- Un JSON worldwide con todos los POIs nunca debe ir como primer request; `manifest países → shards ciudades → 30 resultados visibles` de #672. Se recomienda añadir índice invertido autor/obra → destinos para búsquedas directas **sin descargar una ciudad primero**. Ese índice puede servirse dividido por prefijo e idioma.
- Usar Pagefind ya presente para contenido público. En cada ficha proveer HTML visible de calidad, `canonical` única, `BreadcrumbList` válida y `Place/CollectionPage` con exactitud contextual. No metadatos de «libro gratis», «estrellas», «horario abierto» ni coordenadas inventadas.
- Acordar presupuesto de LCP, INP, CLS con QA real; el atlas no carga MapLibre, OSM tiles, Flutter ni SPARQL en el render básico.
- Captar miles de POIs candidatos de fuentes gratuitas permite cobertura eventual, **pero** Google desaconseja publicar páginas masivas de poco valor; solo publicar lo que tenga evidencia real y texto original.

## Huecos de producto que requieren código posterior (NO declarar implementado)

- Índice por libro/autor global, sin depender de la ciudad del selector (ausente en #672).
- Conexiones recíprocas desde `/recomendaciones/libros/`, navegación por saga y desambiguación de autor.
- Plantillas reales integradas con shell, Pagefind, sitemap, breadcrumbs del sitio y schema vigente (preview #672 no lo hace).
- Editor Sheets de relaciones con revisión por tipo (escenas/biografía/rodajes) y fotos con permisos de reutilización.
- Rutas compuestas y mapa bajo demanda con teselas autorizadas.
- Pruebas reales de SEO, JS back/forward, web vitals, links, XSS, PII y categorías.

**Fecha y estado:** investigación 21/10/2026; sin test/CI, merge ni despliegue. Referencias de productos pueden variar y no deben servir como fuente editorial de datos sin confirmación.

### Fuente audiovisual prioritaria añadida

[FilmMap dataset CC0](https://github.com/Flightmussy/filmmap-dataset) + [#667: análisis y licencia](https://github.com/davidpd89/web-escritor/pull/667) + [#668: MCP MIT literalmente copiado](https://github.com/davidpd89/web-escritor/pull/668). El dato más directo para **rodajes de adaptaciones literarias**. Conservar campos `kind/production_id/relation`, no equiparar videojuegos/manga con rodaje ni filmación con pasaje novelístico. El snapshot original de agosto 2026 no debe confundirse con la actualización del sitio en vivo. Lo público será nuestra revisión y contexto editorial, no un duplicado en bruto.

## Referencias comparativas nuevas: editorial verificable frente a mapas masivos (21/10/2026)

Se inspeccionaron [Akhand](https://github.com/CodeRustyPro/akhand) y [Literary Atlas](https://github.com/rostam/literary-atlas), **sin fichero LICENSE en la raíz** en la revisión. Son útiles como patrones de producto, **NO candidatos de copia literal de software/datos sin licencia**.

- **[Akhand](https://github.com/CodeRustyPro/akhand)**: release estricta documentada (17/03/2026) de **9.057 lugares** de literatura del sur de Asia, con filtros `q,region,city,author,genre,year_min,year_max`, API /places y GeoJSON, más capa WebGL de mapa de densidad/arcos y uso de Wikidata P840. Nos interesa su **pipeline de candidaturas → release depurada y versionada**, respuesta paginada y `/meta` con versión/recuento; **NO adoptar** un backend FastAPI + bases, LLM Gemini ni un frontend deck.gl cargado por defecto: nuestro sitio estático ya tiene mejores opciones ligeras para su alcance.
- **[Literary Atlas](https://github.com/rostam/literary-atlas)**: **191 reseñas → 147 con pin** y **44 sin pin** porque no hay emplazamiento inequívoco. Separa ambientación y publicación y distingue `fictionalised`, nombre real oculto tras ficción y sin ubicación. Su mapa se dibuja como **SVG y ~500 líneas JS sin librería** y genera geografía simplificada desde TopoJSON en build. Lo interesante es **mostrar honestamente cuántos registros NO se pueden situar** y una futura visualización época de trama vs fecha escritura, no copiar su pequeño gazetteer eurocéntrico ni inferencias LLM sin revisar.
- **[The Dogear](https://thedogear.com/about/)**: mapa de libros que parte de Open Library + Wikidata CC0 y aplica **revisión humana a cada vínculo libro↔lugar** antes de mostrarlo; sin rellenos generados. Su UX vincula ciudad → libros → tienda, mientras nosotros añadimos rutas, casas públicas, bibliotecas y evidencia por tipo. No se ha identificado licencia de código para copiar desde su sitio; **inspiración**, no vendor.

**Decisión ratificada tras comparar**: para este repo el mejor equilibrio sigue siendo **generación estática + Pagefind existente (búsqueda mundial) + JSON por destino (filtros locales) + mapa opcional**. Los casos de 9.000 puntos justifican un mapa dedicado después de la primera carga, pero **no** un servidor dinámico de mapas por visitante. Añadir visualización temporal solo si hay fechas narrativas revisadas y un objetivo de búsqueda real, no solo porque resulte vistosa.

**Auditoría legal:** GitHub público sin licencia no equivale a código libre. Se limita la copia literal a [#668](https://github.com/davidpd89/web-escritor/pull/668) con archivos ISC/MIT/BSD y SHA/licencias verificados.
