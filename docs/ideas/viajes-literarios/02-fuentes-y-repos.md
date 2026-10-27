# Viajes literarios · investigación de fuentes, APIs y código abierto (v0.1)

**Revisión exploratoria:** 2026-10-21. Esta lista es un registro de candidatos comprobados a nivel documental, NO certifica que cada API tenga cobertura suficiente ni que pueda ingerirse toda su base sin condiciones. Revalidar límites, licencias, cambios y calidad al diseñar el piloto.

## A. Fuentes estructuradas prioritarias

| Fuente | Qué puede aportar | Límites y decisión |
| --- | --- | --- |
| [Wikidata Query Service / SPARQL](https://query.wikidata.org/) y [ejemplo oficial](https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples) | Identidades QID, obras, autores, relaciones geográficas y coordenadas estructuradas; P840 localización narrativa, P915 lugar de rodaje, P625 coordenada, P19 nacimiento, P551 residencia | **Descubrimiento**, no verdad automática: cobertura irregular, propiedades usadas de manera incompleta y referencias insuficientes en algunos registros. Separar adaptación/obra; no publicar domicilios privados. Guardar QID y origen por afirmación. Respetar servicio público y almacenamiento local. |
| [OpenStreetMap / Overpass](https://wiki.openstreetmap.org/wiki/Overpass_API) y [guía QL](https://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide) | Candidatos a librerías (shop=books), bibliotecas (amenity=library), museos, edificios culturales; topología y coordenadas | Etiquetas no prueban relevancia literaria ni si sigue abierto. Overpass público no es backend ilimitado: consultar por lotes pequeños y verificar; licencia [ODbL](https://www.openstreetmap.org/copyright), atribución y posibles obligaciones de base derivada. |
| [Open Library APIs](https://openlibrary.org/developers/api), [Works/Books](https://openlibrary.org/dev/docs/api/books), [Authors](https://openlibrary.org/dev/docs/api/authors) | Título, autor, obra/edición, IDs, posibles subject_places, enlaces a obras | No garantiza calles ni localizaciones de escenas. Uso identificado: documentación indica 1 req/s no identificado y 3 req/s identificado; no usar como backend masivo comercial; API para consultas acotadas, dumps para usos voluminosos si las condiciones lo permiten. |
| [Google Books API](https://developers.google.com/books/docs/v1/using) | Metadatos de volumen/ISBN, validación cruzada de obras y autores | No trae de forma fiable escenas georreferenciadas; revisar términos de visualización y cuota; no copiar reseñas, descripciones ni imágenes sin base de uso. |
| [Nominatim](https://operations.osmfoundation.org/policies/nominatim/) | Geocodificar dirección/POI verificado, búsqueda acotada | Servidor público máximo absoluto 1 req/s, atribución, identificación; prohíbe autocompletar desde API pública, consultas sistemáticas de POIs y uso intensivo. Priorizar OSM ID/coords verificadas; no geocodificar cientos de lugares indiscriminadamente. |
| [Wikimedia Commons API Imageinfo](https://www.mediawiki.org/wiki/API:Imageinfo) | Fotos con metadatos y licencias; selección editorial de imágenes | Revisión de licencia **por fichero**, autor, atribución, modificaciones y permiso de uso comercial; no asumir autorización por alojarse en Commons. [Guía de reutilización](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia). |
| [Google Sheets API](https://developers.google.com/workspace/sheets/api/limits) | Mesa de control y curación humana, importación autenticada por lotes | No debe consultarse por usuario final. API con cuotas y backoff; no dejar datos privados ni secretos en snapshots web. |
| Fuentes primarias culturales: webs de bibliotecas, librerías, casas-museo, ayuntamientos, turismo oficial, editoriales y creadores | Verificar historia, existencia, dirección pública, visitas, eventos e inspiración explícitamente declarada | Enlazar fuente y fecha; no copiar contenidos; distinguir marketing de documentación de la obra o rodaje. |

### Propiedades Wikidata importantes (son categorías diferentes)

- [P840 / narrative location](https://www.wikidata.org/wiki/Property:P840): transcurre la ficción en ese lugar.
- [P915 / filming location](https://www.wikidata.org/wiki/Property:P915): se rodó una adaptación/producción en ese lugar. La documentación de P915 pide usar P840 para la ambientación.
- [P625 / coordinate location](https://www.wikidata.org/wiki/Property:P625): coordenada de un lugar, no de una escena por defecto.
- Autor y lugar: distinguir casa-museo pública, nacimiento, estancia histórica y supuesto domicilio actual; **excluir ubicaciones privadas sensibles**.

### Borrador de consultas, para una fase posterior

1. Partir de un QID de **obra** validado por título + autor, consultar P840, guardar entidad-lugar y referencias; nunca equiparar resultado a prueba de calle/edificio.
2. Partir de QID de **adaptación**, consultar P915 y verificar en una segunda fuente de producción o turismo; etiquetar rodaje.
3. Por municipio OSM, consultar POIs tipo librería/biblioteca; seleccionar manualmente cuáles son emblemáticos. Evitar «todas las librerías de la ciudad» como categoría de interés editorial sin investigación.
4. Buscar fuentes culturales oficiales para explicar qué relación específica existe entre el lugar y el libro; citar la URL exacta de evidencia, no la portada de un buscador.
5. Guardar caché de candidatos + fuente + fecha + estado y someterlo a revisión. Nunca reutilizar como definitivo un enlace roto o un resultado sin respaldo.

## B. Motores y cartografía, priorización propuesta

**Opción sencilla recomendada al empezar: [Leaflet](https://leafletjs.com/examples.html)**. Marcadores, GeoJSON, popup, móvil y accesibilidad; coste de JavaScript razonable para pocos lugares. Comprobar integración con CSP del sitio, carga diferida, fallback textual y atribución del mapa.

**Para miles de puntos y capas: [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/)**. GeoJSON, clustering y vector tiles; mayor complejidad y coste gráfico; revisar CSP/worker/WebGL, hosting y derechos/licencia del proveedor de tiles. No asumir que demo tiles constituyen servicio productivo.

El software de mapa **no incluye automáticamente** un proveedor de teselas libre de límites. Si se usa [tile.openstreetmap.org](https://operations.osmfoundation.org/policies/tiles/): cumplir políticas de atribución, referer, caché y no prefetched/bulk; el servicio carece de SLA y no es backend de alto tráfico garantizado. Para escala real evaluar proveedor contratado o teselas propias.

Importación estática a **GeoJSON** y datos locales reducidos. Mapas solo para puntos físicos concretos; para ficción sin ubicación verificable, panel editorial sin pin.

## C. Proyectos públicos de código que conviene estudiar

| Proyecto | Idea replicable | Estado/licencia comprobada al revisar |
| --- | --- | --- |
| [Read the Places](https://github.com/markselby9/readtheplaces.com) · [diseño](https://github.com/markselby9/readtheplaces.com/blob/main/docs/DESIGN.md) | Lugares ordenados en la **secuencia narrativa**; evidencia, grado de certeza, diferencia dominio público/copyright y citas | Activo (oct-2026); [LICENSE](https://github.com/markselby9/readtheplaces.com/blob/main/LICENSE): código MIT en las carpetas especificadas, **datos de libros CC BY-SA 4.0**, materiales de terceros según ficha. **No mezclar ni copiar datos** con otra licencia sin revisión. |
| [Akhand](https://github.com/CodeRustyPro/akhand) | API y flujo de ingestión multi-fuente, clasificación geográfica, GeoJSON/CSV, visualizaciones MapLibre/deck.gl | README anuncia miles de lugares; cifras **no auditadas**. Sin archivo LICENSE visible en raíz en revisión inicial: derechos para reutilizar código/dataset **NO confirmados**, solo referencia conceptual hasta aclararlos. |
| [Literary Atlas](https://github.com/rostam/literary-atlas) | Pipeline build-time, mapa/timeline, no geolocalizar lugares imaginarios, marcadores de confianza | README documenta 191 reseñas y advierte que perfiles generados por modelo no se comprobaron manualmente. Sin LICENSE visible en raíz: **no copiar código ni datos** sin permiso claro. |
| [Bookish Bay Area](https://github.com/yvonneyeh/bookish-bay-area) | Descubrir libros por ciudad/barrio y combinar mapa y bibliotecas | Ejemplo de navegación por ubicación; tecnología de otro stack y Google Maps API. Sin LICENSE visible en raíz: solo arquitectura inspiracional hasta confirmar condiciones. |
| [Leaflet](https://github.com/Leaflet/Leaflet) | Motor de mapas ligero, eventos, capas y GeoJSON | Licencia BSD-2-Clause declarada por GitHub; si se incorpora, conservar avisos y fijar versión. |
| [MapLibre GL JS](https://github.com/maplibre/maplibre-gl-js) | Renderizado vectorial/WebGL, grandes colecciones GeoJSON, clustering | Proyecto abierto activo; licencia exacta de componentes/dependencias a revisar antes de integrar y mantener avisos. |

No se ha copiado código ni datasets de estos proyectos. En una fase posterior: evaluar rutas reales y commits relevantes, APIs y licencias por carpeta; prueba mínima de performance y accesibilidad; publicar atribuciones/copyright.

## D. Referentes editoriales y competencia (para estudiar, NO para extraer masivamente)

- [The Book Trail](https://www.thebooktrail.com/): descubre novelas por lugares; estudiar semántica de búsquedas e intención de viaje.
- [Literature Tour](https://literaturetour.com/): gazetteer de casas, librerías, museos, escenarios y cafés; estudiar taxonomía/retorno a destino.
- [Read the Places](https://readtheplaces.com/): secuencia narrativa con precisión de fuente.
- [VisitScotland](https://www.visitscotland.com/) y [VisitBritain](https://www.visitbritain.com/): rutas turísticas oficiales y rodajes, siempre contrastando asociación concreta.
- Instituciones locales: [Ayuntamiento de Madrid](https://www.madrid.es/), [Paris je t'aime](https://parisjetaime.com/), bibliotecas nacionales y museos. Verificar URL de ficha exacta antes de documentar una afirmación.

**Qué no hacer:** scraping indiscriminado de blogs/Tripadvisor/Maps; inventar una API de Goodreads para los lugares; copiar fotos, sinopsis o rutas; presentar una ubicación cinematográfica como pasaje del libro; extraer la dirección privada de un autor.

## E. Matriz de prioridad (hipótesis)

1. **Alta:** fuentes culturales oficiales + Wikidata + OSM/Overpass para candidatos + Open Library para identidad + fotos con licencias.
2. **Media:** Google Books para bibliografía, APIs patrimoniales locales/Europeana a evaluar, rutas oficiales descargables, Wikisource para obras en dominio público.
3. **Baja/pendiente:** scraping dinámico, valoraciones y horarios de terceros, autogeneración IA sin confirmación, servicios de pago para mapas si aún hay pocos puntos.

## F. Próximas tareas de investigación documentable

- [ ] Extraer un ejemplo SPARQL P840 y otro P915 con fuentes válidas, evaluar cobertura y falsos positivos en 5 obras reales.
- [ ] Ejemplos Overpass de shop=books y amenity=library en Madrid y París; medir duplicados/cierres/precisión.
- [ ] Medir latencia/tamaño de Leaflet vs MapLibre bajo CSP y móvil antes de escoger.
- [ ] Inspeccionar licencias de Akhand, Literary Atlas y Bookish; pedir permiso si procede; anotar commits precisos.
- [ ] Localizar bibliotecas/datasets públicos de turismo literario de Madrid, París, Irlanda, Portugal y Reino Unido y sus términos de reutilización.
- [ ] Definir forma de atribución visible para fotografía y OSM, además de almacenamiento de fuente original.
- [ ] Revisar restricciones sobre promociones y afiliados si una sección turística incorporase monetización adicional (no asumida).
