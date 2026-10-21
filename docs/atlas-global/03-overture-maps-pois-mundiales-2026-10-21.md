# Overture Maps Places: fuente MUNDIAL prioritaria (hallazgo 21/10/2026)

**Fase P1, [#667](https://github.com/davidpd89/web-escritor/pull/667), hija de [#666](https://github.com/davidpd89/web-escritor/pull/666).** Esta fuente pasa a ser candidata principal para **descubrir POIs reales en todo el mundo**. No sustituye bibliografía ni evidencia de novela↔lugar.

## Hallazgo contrastado con documentación oficial

- [Guía Overture Places](https://docs.overturemaps.org/guides/places/) — el explorador oficial documenta una capa mundial con **decenas de millones de POIs**, incluyendo empresas, espacios culturales e hitos. [Explorador de taxonomía](https://docs.overturemaps.org/guides/places/taxonomy-explorer/) muestra **78.517.770 lugares** en la edición de septiembre de 2026; este recuento puede cambiar y se refiere al dataset general, **NO a librerías ni lugares literarios**.
- Licencias de **Places**: CDLA Permissive 2.0 / Apache 2.0 y varias fuentes CC0 (ver procedencia por `sources`). Según documentación Overture, **Places no contiene OSM** y **no tiene obligaciones ODbL** por ese tema. No confundir con otros temas Overture con otras licencias. Guardar aviso de atribución de sus proveedores y URL de licencia.
- [Cliente oficial Python](https://docs.overturemaps.org/getting-data/overturemaps-py/): `pip install overturemaps` y `overturemaps download --bbox=<lon_min>,<lat_min>,<lon_max>,<lat_max> -f geojson --type=place -o city.geojson`. El cliente usa STAC para localizar edición actual; **no requiere API comercial por cada POI**, pero hay tráfico/disco/CPU. Descargas por bbox, no todo el planeta a CI.
- [DuckDB oficial para Overture](https://docs.overturemaps.org/getting-data/duckdb/): lectura GeoParquet con filtros de bbox y columnas, desde AWS; puede seleccionar subset sin descargar todo. **Comparar coste de egress, latencia y acceso cloud** según dónde se ejecute.
- [Taxonomía Overture](https://docs.overturemaps.org/guides/places/taxonomy/): versión septiembre 2026 **eliminó `categories`**. Usar `taxonomy` (hierarchy/primary/alternates) y `basic_category`; **no escribir adaptador nuevo leyendo solo `categories.primary`**. Taxonomía amplia (~2300 categorías), permitir mappings versionados por release.

## Aplicación específica a Atlas de Libros

POIs prioritarios (clases de dominio destino, no términos de Overture confirmados):
`bookshop`, `library`, `museum`, `writer_house_museum`, `literary_plaque`, `historic_site`, `cafe`, `landmark`.
**NO asumir que `bookshop` sea el nombre exacto del taxón Overture**: [taxonomía CSV de edición](https://docs.overturemaps.org/guides/places/taxonomy-explorer/) debe inspeccionarse y mapearse por `taxonomy.primary`/jerarquía/aliases. Debe incluirse `release_version`.

Columnas candidatas [guía](https://docs.overturemaps.org/guides/places/):
`id` (GERS persistent ID), `names` multilingüe, `geometry` Point, `bbox`, `addresses`, `taxonomy`, `basic_category`, `confidence`, `websites`, `sources`, `version`.
Una existencia/confluencia `confidence` alta **NO acredita** que la librería sea icónica ni que una novela ocurra allí. Guardar `external_ids.overture_gers_id` separadamente del `osm_type + osm_id`.

## Ejemplo del CLI oficial (DOCUMENTADO, NO ejecutado)

```sh
# Coordenadas del ejemplo oficial Overture; NO implica descarga de Roma realizada.
uvx overturemaps download --bbox=12.46,41.89,12.48,41.91 -f geojson --type=place -o /datos-temporales/roma-places.geojson
```

No añadir 78 millones al Git, ni generar automáticamente 78 millones de páginas. El filtro por cultura/lectura y geometría reduce enormemente el universo. Más tarde comprobar total real por país/idioma/tipo y sesgo de cobertura; compararlo con OSM/Geofabrik.

## Estrategia de extracción global económica

1. Un `manifest` `provider=overture; release=YYYY-MM-DD.X; bbox; categories; cursor; fetched_at` por lote.
2. Preseleccionar bbox de **destinos activos** que tengan obras o demanda. Luego expandir por países; no escanear planeta por cron diario.
3. Descargar/preparar por región usando Python CLI o DuckDB (primero evaluar 1 ciudad, luego ~10 regiones), normalizar GERS y conservar `sources`/licencias.
4. Cruce espacial con GeoNames/Wikidata/OSM por id externo, nombre, dirección y distancia **como candidato**; nunca mergear si hay dos sucursales homónimas sin revisar.
5. Resolver obra/autor vía Open Library/Wikidata; evidencia de relación separada.
6. Una fuente de POI que desaparece en nueva versión se envía a revisión, no desaparece de web automáticamente.

## Tabla de riesgos

- Datos generales pueden tener POIs cerrados/desactualizados/duplicados; filtros `confidence`, web oficial y `fetched_at`, pero revisión antes de afirmar horarios actuales.
- ID GERS estable entre releases según docs, pero cambios/matches a vigilar con bridge files/changelog.
- Taxonomía nueva en septiembre de 2026, campos de ediciones viejas no compatibles; test fixture con schema v2.0.0.
- POIs sin libro asociado son **candidatos culturales** (pueden justificar una ficha si son realmente notables). No inventar una relación.
- Licencia permisiva no concede licencia de fotos ni contenido de webs enlazadas.

## Comparativa de adquisición

- **Overture Places**: mejor primera opción para *POIs mundiales* con clasificación, fuente y licencia permisiva.
- **OSM/Geofabrik**: complemento para nombres, detalles locales y `amenity=library` / `shop=books`; ODbL distinto (atribución y base derivada a estudiar).
- **Wikidata**: identidad y relaciones de obra/autor/rodaje, sin cobertura exhaustiva.
- **Open Library dumps**: obras masivas, **no geocodificador literario**.
- **Portales culturales oficiales**: evidencias primarias y descripción editorial, útiles en pilotos y validación.

**Pendiente en P6:** extraer CSV taxonomía y confirmar el identificador exacto de bookstore/library/museum antes de escribir SQL/Python de producción; muestras por 5 continentes, derechos por campo, presupuesto disco y tasas de cambio. No se ha llamado a la API ni descargado parquet aquí.

## Verificación posterior: CSV completo de taxonomía de septiembre 2026 leído en GitHub

Se ha inspeccionado directamente [`OvertureMaps/docs/static/taxonomy/2026-09-23.0/taxonomy.csv`](https://github.com/OvertureMaps/docs/blob/main/static/taxonomy/2026-09-23.0/taxonomy.csv), blob Git `1ab9097166dc04c23b73fe738b0c277317b542db`, **2.303 registros aprox.** Se encontraron categorías reales `bookstore` y subtipos `academic_bookstore`, `used_bookstore`, `comic_books_store`; `library`; `museum`; `historic_site`, `memorial_site` y `monument`. La estructura y nombres de taxones se han trasladado al filtrador de candidatos de [#673](https://github.com/davidpd89/web-escritor/pull/673).

**Corrección de un riesgo previo:** ya no es necesario adivinar si el taxón se llama `book_store` o `bookstore` en esta edición: el nombre exacto para librería general es **`bookstore`**. Las variantes antiguas solo son compatibilidad heurística. Para cada nueva versión descargar CSV, comprobar diffs y testear adaptador antes de importar millones de registros.
