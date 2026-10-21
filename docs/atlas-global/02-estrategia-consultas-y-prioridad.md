# Atlas global · consultas reutilizables y priorización sin modelos (2026-10-21)

**PR hija #666, documentación únicamente.**

## Pipeline de candidatos, no de afirmaciones

`seed existente → IDs externos → extracción limitada → normalización → deduplicación → relación propuesta → fuentes específicas → aprobación editorial → snapshot → HTML`

```text
                 ┌ Open Library WORKS (dump mensual / lotes) ┐
catálogo libros ─┤                                       ├─ obras + autores
                 └ Wikidata QID (P840; P915 adaptación)    ┘
datos regiones ─┬─ Geofabrik PBF/Osmium (shop=books, amenity=library)
                ├─ GeoNames (localidad, alias idioma)
                └─ portals cultura abiertos (museos, patrimonio)
                   ↓
                lugares físicos con external_ids y candidatos de relaciones
                   ↓
                cola de evidencias (fuentes ≠ URLs de buscador)
                   ↓
                aprobación → datos públicos del atlas
```

## Consultas y campos mínimos

**Wikidata por obra identificada:** `SELECT ?lugar WHERE { wd:QID_OBRA wdt:P840 ?lugar }` (resolver QID real antes). Para adaptación: `wd:QID_SERIE wdt:P915 ?lugar`. `wdt:` **no incluye por sí solo referencias de afirmación**: resolver statements y fuentes al seleccionar. Usar paginación/límites y consultas agrupadas por QIDs, no consulta individual por cada publicación.

**Open Library por localización:** ver [Subjects API](https://openlibrary.org/dev/docs/api/subjects), [Search API](https://openlibrary.org/dev/docs/api/search). Los `subjects/place:...` no son equiparables automáticamente a `narrative location`; conservar relación `tema_geografico` como candidata débil.

**OSM por región:** PBF regional con filtro `shop=books`, `amenity=library`, `amenity=public_bookcase`, `tourism=museum` condicionado a tema literario. Degradar a «lugar cultural» si no existe relación con novela. `out center` de Overpass para ways devuelve centro geométrico, **no la entrada**; precisión `edificio/zona/ciudad` explícita.

## Normalización e IDs

- Obra `reading_book_id` cuando esté en `data/reading-catalogue.json`; de otro modo `external_id_openlibrary_work`/ `wikidata_qid` y estado interno hasta ficha aprobada. No deduplicar por ISBN ni título a secas.
- Destino: `geonameid` + país + región, con `wikidata_qid` y alias locales. Resolver Londres UK frente a ciudades homónimas.
- Lugar: `osm_type` + `osm_id` (no solo número, pues node/way/relation pueden compartir id); QID; dirección pública; `lat/lon` WGS84; jerarquía y precisión.
- Relación: clave estable `(obra_id, lugar_id, tipo_relacion, adaptacion_id, escena_id?)`, evidencia independiente de POI; mismo sitio admite obras múltiples.
- Revisión de cambios: `observed_at` y `source_version`, `fingerprint`; si cambian fuentes, no despublicar automáticamente fichas existentes.
- Idioma: títulos localizados separados de metadatos/relaciones; fallback ES → idioma original → EN cuando exista, sin traducción automática inventada.

## Scoring de priorización, NO de veracidad

Se puede ordenar el **trabajo editorial** por: fuente oficial disponible + referencias múltiples + destino conocido + relación precisa + fotografía legítima + demanda de búsqueda. Ninguna puntuación debe elevar `status` a publicado. Guardar `reason` y `rejections` para estudiar falsas conexiones.

## Estrategia de CPU y tokens

- Clasificación por heurísticas y claves estructuradas primero; extraer relaciones conocidas sin LLM. Caché ETag y artefactos locales; batch y `max_records/max_bytes/max_requests` bajos con resume/checkpoints.
- Para obras de dominio público legalmente verificadas, extracción de topónimos con NER local CPU (spaCy/GLiNER opcional; no correr GPU por defecto), **solo candidatos**; revisar ambiguos y no transformar el nombre «Paris» en pin por coincidencia sin contexto.
- Para libros modernos, no cosechar texto protegido ni invocar modelos que «recuerden» escenas sin fuente. Buscar declaraciones de autor, guías institucionales, académicos y sitios de adaptaciones.
- Los visitantes consultarán índices JSON y páginas precalculadas, **no APIs de tercero**. Así el coste marginal de consulta de libros/lugares se limita al hosting existente.
- Fichas y filtros en HTML/CSS/JS propio con generador actual; mapas opcionales cargados bajo demanda. No duplicar N servicios de backends para una web estática.

## Pruebas pendientes

- Cobertura Wikidata: 20 obras de 5 continentes y distintos géneros, sin cherry-picking de 20 famosos; medir % con P840/P915 referencias útiles.
- Precisión librerías OSM: muestras en 5 ciudades, falsos positivos/cerradas, deduplicación por OSM type+id.
- Rendimiento: construir JSON de 100/1000/10.000 POIs con filtros, sin mapas, medir tamaño comprimido y tiempo en móvil.
- Licencias: carpeta de procedencia y avisos de atribución para cada dato ODbL/CC BY y cada foto, evitando mezcla accidental de datasets share-alike.

## Actualización 21/10/2026: Wikidata v1 → QLever sin reescribir nuestro atlas

- **[Migración oficial de Wikidata](https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/WDQS_backend_update/Migrate)**: v1 de `query.wikidata.org` y v2 de `query-next.wikidata.org` convivirán **al menos hasta febrero de 2027**. El segundo endpoint puede contestar *Unauthorized User-Agent* hasta apertura pública. No programar un switch temporal ciego ni afirmar que v2 funciona públicamente hoy.
- **[Alternativas comunitarias](https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/Alternative_endpoints)**: `qlever.dev/wikidata` puede resultar más rápido para ciertos queries, pero hay que medir disponibilidad, recencia de datos, política de uso y compatibilidad SPARQL antes de seleccionarlo. No duplicar consultas contra dos proveedores ante 429 automáticamente.
- **[Límites v1](https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual)**: 60 s por consulta, presupuesto de CPU por usuario/IP, hasta cinco consultas paralelas, 429 con `Retry-After`. El futuro executor será offline, un User-Agent explícito, caché/manifest/versiones/reintentos exponenciales, sin dispararlo en GitHub Actions ni visita web. Evitar `SERVICE wikibase:label` al primer prototipo por semántica dependiente del motor.
- **[Nueva PR #678](https://github.com/davidpd89/web-escritor/pull/678)**: generador offline ya creado de SPARQL con `VALUES wd:Q...` para `P840` (ambientación obra), `P915` (rodaje adaptación), `P551` (residencia autor), sin HTTP; 20 IDs/lote por defecto y SHA. **Consulta no es afirmación publicada**: P840 no demuestra calle concreta, P915 no representa novela, P551 exige filtrar residencias privadas.

**Resultado:** el modelo canónico #669 no conoce QLever/Blazegraph; solo origen con licencia, `provider_release`, QID y tipo de relación. En la publicación solo entra la conexión verificada por persona, con fuente documental. El cambio de proveedor SPARQL afecta a un único adaptador futuro.
