# 05 · Captación gratuita, límites reales y arquitectura de automatización (revisión 21/10/2026)

## Recomendación: no empezar por scraping de blogs

**Pirámide de fuentes:**
1. **Catálogos oficiales abiertos por municipio** para POIs (Madrid, París, etc.).
2. **OSM/Overpass** para cubrir librerías, bibliotecas, museos y coordenadas que no tengan fuente pública oficial; *candidatos*, no emblematicidad ni vínculo literario.
3. **Wikidata + Open Library** para identidad obra/autor y pistas sobre narración, adaptaciones, biografías (no direcciones privadas).
4. **Institución cultural, texto original en dominio público cuando sea lícito, archivos/autor/editorial/film commission** para **vínculos concretos**.
5. **Wikimedia Commons** solo imágenes con licencia por archivo y atribución.
6. Blogs y rutas turísticas como **señales para investigar**, no registros reutilizados en bloque; comprobar cada afirmación desde una fuente adecuada. Escritura de resúmenes propios.

### Fuentes con datos listos para un primer piloto

**Madrid, fuente pública estructurada:**
- [Datos abiertos · Bibliotecas de Madrid](https://datos.madrid.es/dataset/201747-0-bibliobuses-bibliotecas/downloads), recursos JSON/CSV/GEO, direcciones y coordenadas. Importación por descarga periódica de recurso oficial, sin API de pago.
- [Portal cultura y ocio Madrid](https://datos.madrid.es/group/cultura-ocio): museos, monumentos, edificios y bibliotecas; algunos recursos actualizados diariamente. Revisar fecha de cada dataset y licencia individual.
- [Condiciones de reutilización](https://datos.madrid.es/pages/condiciones-de-uso): generales CC BY 4.0 para usos comerciales y no comerciales, con excepciones expresas para categorías concretas. Guardar dataset, licencia y fecha de descarga; **no asumir que todos los contenidos municipales incluidas fotos tienen CC BY**.
- [Madrid Turismo — Barrio de las Letras](https://www.esmadrid.com/barrios-de-madrid/barrio-letras): verifica conexiones concretas (ver piloto de 06). Su información descriptiva no es un dataset para copiar masivamente.

**París, fuente pública estructurada:**
- [Explore API v2.1 París](https://www.data.gouv.fr/dataservices/explore-api-v2-86) base `https://opendata.paris.fr/api/explore/v2.1/`, acceso abierto. Consultar dataset por dataset, respetar ODbL y límites de paginación.
- [Ciudad de París: 50 placas dedicadas a personajes literarios](https://www.paris.fr/pages/des-plaques-pour-commemorer-les-personnages-litteraires-de-paris-29191): listado editorial con obras/personajes y ubicaciones públicas, 30 nuevas placas anunciadas en diciembre de 2025. Excelente fuente primaria para **placas homenaje** (NO prueba de que la trama ocurra exactamente en la dirección de la placa).
- [Ministerio de Cultura francés — direcciones de bibliotecas](https://culture.data.gouv.fr/datasets/adresses-des-bibliotheques-publiques-2): descarga GeoJSON, licencia Licence Ouverte 2.0, cobertura Francia.
- No usar el dataset de «Tous les documents des bibliothèques de prêt» como fuente actualizada de libros: el propio Ayuntamiento señala que representa una instantánea **de julio de 2018**, pese a metadatos procesados después. No sirve para POIs actuales.

### APIs abiertas, acceso y límite de uso por política pública

| Origen | Acceso / automatización | Condición crítica |
| --- | --- | --- |
| [Wikidata Query Service](https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual) | SPARQL HTTP por lote de QID; gratis para uso razonable, cachear | Timeout **60 s**, 60 s de CPU por cliente cada 60 s, hasta 5 queries paralelas/IP; 429 y Retry-After. Identificar User-Agent; no masificar |
| [Open Library](https://openlibrary.org/developers/api) | REST/JSON Works, Authors y búsquedas; usar caché e IDs de obras | 1 req/s no identificado; 3 req/s identificado por User-Agent de app + email. **No backend comercial ni cosecha masiva**. Para lotes grandes usar dumps permitidos |
| [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API) | Consultas de POIs por área pequeñas; no exige token | Instancias públicas pueden saturarse; 10 000 consultas/día y 1 GB/día son cifras de tolerancia indicadas para una instancia concreta, **NO cuota garantizada**, ni objetivo de consumo; usar pocas consultas por semana/ciudad, caché y respeto 429 |
| [Nominatim servidor público](https://operations.osmfoundation.org/policies/nominatim/) | Geocoding ocasional para un POI ya seleccionado | Máximo absoluto 1 req/s, sin autocompletado ni consultas sistemáticas de POIs; no usarlo para cosechar bibliotecas de todas las ciudades |
| [Wikimedia Commons Imageinfo](https://www.mediawiki.org/wiki/API:Imageinfo) | Búsqueda metadata/licencias, sin clave de pago | Verificar términos, autor, fuente y licencia por archivo, enlace de atribución; API nueva de Attribution todavía beta |
| [Google Sheets API](https://developers.google.com/workspace/sheets/api/limits) | Backoffice para importación en lotes, requiere acceso autorizado | Limitar operaciones, secreto servidor, reintentos, no exponer hojas privadas al navegador |
| [Europeana APIs](https://www.europeana.eu/en/how-to-register-for-and-manage-an-api-key) | Patrimonio digital, autores/archivos, **clave personal/proyecto** | Uso operativo requiere clave de proyecto; no asumir API completamente libre de registro, revisar derechos de cada imagen/objeto |
| [Datos Madrid](https://datos.madrid.es/dataset) | Descarga de recursos JSON/CSV, CKAN según dataset | Sin pago en datasets revisados; licencia puede variar por recurso |
| [París Explore API](https://www.data.gouv.fr/dataservices/explore-api-v2-86) | Búsqueda y export por dataset | API abierta; licencia ODbL en muchos datasets y cuotas por proveedor a comprobar |

### Importante: 100 % gratis en servicios ≠ servicio sin costes ni condiciones

- Software y datos abiertos permiten desarrollar sin pagar por cada ficha, **pero** mapas con teselas y hosting tienen política de uso. Evitar depender de Google Places (facturación y condiciones) si el objetivo es gratuita y mantenible.
- [Leaflet](https://leafletjs.com/) con OSM tiles: prototipo viable; [política tiles OSMF](https://operations.osmfoundation.org/policies/tiles/) exige atribución, identificación de cliente, caché y restringe descargas masivas. Sin SLA.
- [Protomaps / PMTiles](https://github.com/protomaps/PMTiles) + [MapLibre](https://maplibre.org/maplibre-gl-js/docs/) alternativa para archivos de mapas servidos desde alojamiento estático, sin petición a un proveedor por visita. Licencia PMTiles BSD-3-Clause; **el mapa base OSM subyacente mantiene ODbL/atribución**. **El almacenamiento y el tráfico pueden costar dinero** según proveedor. [Guía PMTiles](https://docs.protomaps.com/guide/getting-started); [integración MapLibre](https://docs.protomaps.com/pmtiles/maplibre). No elegir hasta medir límites de hosting real y caché.
- Importante: [protomaps-leaflet](https://github.com/protomaps/protomaps-leaflet) está en mantenimiento; no elegirlo como nuevo stack por inercia.

## Pipeline futuro propuesto, sin activar automatismos en esta PR

### Un descubridor por tipo de evidencia, una cola de revisión

1. **Seed de entidades** desde 12 ideas existentes y destinos aprobados. Guardar `seed_source`, `provider_record_id` y `retrieved_at`.
2. **Fuentes municipales**: pedir recurso mensual/semanal con `If-Modified-Since`/`ETag` cuando lo admita; descargar solo cambios. Ingerir nombre, dirección, web, coordenadas, fuente y licencia en dataset de *candidatos*; no promover a «histórico» por estar en inventario municipal.
3. **OSM**: deduplicación por `osm_type + osm_id`; conflación con Wikidata QID, nombre normalizado, dirección y proximidad, marcando ambiguos para revisión. No unir librerías diferentes por nombre comercial.
4. **Obras**: resolver contra IDs ya existentes en catálogo de libros, y enriquecer candidatos Open Library/Wikidata. Registrar relación narrativa/rodaje solo si propiedad y referente correctos.
5. **Pruebas**: guardar URL institucional exacta y anotación breve del dato demostrado; soporte/corroboración y fecha. IA puede proponer redacción ORIGINAL y búsqueda, no otorgar `approved`.
6. **Sheets**: revisión y estados. Solo sujetos y vínculos aprobados avanzan al snapshot. El frontend no consulta Sheets.
7. **Snapshot**: claves y hashes estables, JSON separado por `destinos`, `lugares`, `relaciones`, `rutas` para carga selectiva; imágenes licenciadas locales; abortar build ante referencias rotas.
8. **Writer**: usar o extender el único publicador existente de #661 con gates de QA, cola y locking **solo cuando sea compatible y autorizado**. Una PR de datos por lote, no commit a main sin aprobación del usuario.
9. **Mantenimiento**: reconsulta de POIs cambiados, estado abierto/cerrado, enlazado de fuentes, URLs rota, fotos revocadas, rutas y eventos. Una variación externa importante se convierte en ticket de revisión, no en edición pública ciega.

**Modelo de trabajo sin secretos de pago:** endpoints abiertos + lotes pequeños semanales + generación estática desde JSON revisado y commits. Coste de LLM no es necesariamente cero: no hacer llamadas al modelo desde los visitantes; investigación manual asistida por chat o proveedor permitido por usuario; evitar consumo de tokens en cron por defecto.

### Reglas de fiabilidad

- Tres etapas separadas `candidate` / `evidence-reviewed` / `published`; no convertir `HTTP 200` en verdad editorial.
- Enlace oficial y licencia **son propiedades diferentes**. Página web pública puede permitir lectura, no reproducción automatizada de imágenes/textos.
- Las fotos deben poder omitirse si no hay permisos; hacer fichas con tipografía y geografía en lugar de imágenes inventadas.
- La fuente que prueba `librería existente` no prueba `librería mítica`, ni una placa demuestra `escenario textual en esa calle`.
- Caducidad por campo: acceso y horarios con frecuente comprobación, historia con menor frecuencia; explicitar última revisión visible cuando sea relevante.
- `published` solo después de aprobación humana; filtros por ciudad/obra/autor nunca publican miles de combinaciones vacías.

## Backlog gratuito para investigar después

- [ ] Extraer campos reales del JSON de bibliotecas de Madrid, licencia y fecha desde la descarga; verificar si CKAN JSON usa coordenadas WGS84.
- [ ] Identificar datasets actuales de librerías francesas, no confundir directorios comerciales con licencias abiertas.
- [ ] Preparar mini-registro de 10 candidatos con procedencia y separarlos de 3 vínculos editoriales contrastados.
- [ ] Experimentar lectura de datos Wikidata en batch identificando QIDs, con caché y sin publicar automáticamente.
- [ ] Medir si un mapa libre con PMTiles cabe en cuotas de hosting existente; alternativa mapa solo al pulsar.
- [ ] Verificar Pinterest RSS y su compatibilidad con fichas de destinos/lugares, tomando #662 como referencia después de que se estabilice.
