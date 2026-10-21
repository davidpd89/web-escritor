# P6a · Overture Places GeoJSON → candidatos culturales (21/10/2026)

**Hija de [#666](https://github.com/davidpd89/web-escritor/pull/666), vincular a [#667](https://github.com/davidpd89/web-escritor/pull/667)**. Esta fase crea un lector offline pequeño y deja la ingesta mundial a GeoParquet/DuckDB en P6b.

## Fuente, condiciones y cambio 2026

- [Overture Places oficial](https://docs.overturemaps.org/guides/places/) — 78.517.770 lugares generales según [Taxonomy Explorer, edición septiembre 2026](https://docs.overturemaps.org/guides/places/taxonomy-explorer/), NO librerías verificadas.
- [CLI oficial](https://docs.overturemaps.org/getting-data/overturemaps-py/): `uvx overturemaps download --bbox=12.46,41.89,12.48,41.91 -f geojson --type=place -o /ruta/roma-places.geojson`. El ejemplo solo sirve para ilustrar, **NO se ha ejecutado ni bajado nada**.
- [Licencias y versiones](https://docs.overturemaps.org/guides/places/): Places CDLA Permissive 2.0 / Apache 2.0 / contribuciones CC0, no ODbL por Places; atribuciones deben revisarse por fuente.
- **Septiembre 2026 eliminó `categories`**: preferir `taxonomy.primary/hierarchy/alternates` y `basic_category`, no código de tutorial antiguo basado solo en `categories.primary`.

## Archivos preparados

- `scripts/atlas_overture_geojson_candidates.py`: lee un GeoJSON FeatureCollection **ya descargado**, identifica alias posibles de bookshop, library, museum, historic_site, valida coordenadas y UUID GERS, elimina duplicados, produce IDs internos deterministas, conserva versión `--release`.
- `tests/test_atlas_overture_geojson_candidates.py`: seis pruebas sintéticas (taxonomía nueva, coordenadas inválidas, duplicados, privacidad y límites), preparadas pero **NO ejecutadas**.
- No exporta teléfono, correo, redes sociales ni contenidos textuales del proveedor; marca `status=candidate` y `place_relation_status=none`. **La categoría Overture es una etiqueta de POI, no prueba de novela o autor.**
- No usa API, claves, servicios LLM ni red. No modifica `data/atlas-literario.json`, HTML, main ni jobs.

## Precaución de escala: este NO es el procesador global

El script carga todo el **GeoJSON de una zona pequeña** en memoria y **rechaza entrada mayor de 16 MiB**. Es intencionado: analizar 78 millones de puntos cargando un GeoJSON global en memoria no es viable ni barato. [DuckDB + GeoParquet Overture](https://docs.overturemaps.org/getting-data/duckdb/) podrá leer solo regiones, categorías y campos útiles. Eso exige otro adapter de stream que procese particiones, checkpoints, actualización delta y licencias.

**Verificación adicional completada:** inspeccionado el [CSV de taxonomía Overture septiembre 2026](https://github.com/OvertureMaps/docs/blob/main/static/taxonomy/2026-09-23.0/taxonomy.csv), blob `1ab9097166dc04c23b73fe738b0c277317b542db`. Las categorías **reales** incluyen `bookstore`, `academic_bookstore`, `used_bookstore`, `comic_books_store`, `library`, `museum`, `historic_site`, `memorial_site` y `monument`. El código y sus fixtures contemplan esos identificadores. Algunas etiquetas heredadas/alternativas son heurísticas y siguen necesitando estudio. La taxonomía y el volumen pueden cambiar en otra release: **no tratar el mapping como exhaustivo ni eterno**.

## Etapa de normalización posterior

Salida JSONL es `CandidatePOI`, no un `place` aprobado en #669. Convertir mediante normalizador externo:
- `id` interno editorial estable; `overture_gers_id` (UUID original), release y confidence **del POI**, no certeza narrativa.
- `name`, `latitude/longitude`, categoría, fuentes y licencia por proveedor.
- resolver `destination_id` por división GeoNames/Overture o municipio oficial, comprobar conflictos con OSM type+id y Wikidata QID.
- comprobar POI público, tipo de establecimiento y sus posibles relaciones con obras.
- proponer `relationship` con `source_ids` específicos; `approved` solo por revisión humana.
- la interfaz pública no recibe raws ni datos personales.

## Acción futura local ilustrativa

```sh
python scripts/atlas_overture_geojson_candidates.py /datos/roma-places.geojson \
  --release 2026-09-23.1 --max-candidates 300 \
  --out /datos/atlas-roma-candidates.jsonl
# QA futuro autorizado:
python -m unittest discover -s tests -p 'test_atlas_overture_geojson_candidates.py'
```

**Definición de listo pendiente:** lectura real de al menos 2 regiones, comprobación taxonomy CSV y actualización P3, QA de la versión local y aprobación expresa para ejecutarlo. Hasta entonces esta PR permanece draft.

## Verificación de 9 taxones de interés en fichero original

Fuente directa: [OvertureMaps/docs taxonomy.csv](https://github.com/OvertureMaps/docs/blob/main/static/taxonomy/2026-09-23.0/taxonomy.csv). Jerarquías completas relevantes:

- `shopping > specialty_store > books_music_and_video_store > bookstore`
- `shopping > specialty_store > books_music_and_video_store > bookstore > academic_bookstore`
- `shopping > specialty_store > books_music_and_video_store > bookstore > used_bookstore`
- `shopping > specialty_store > books_music_and_video_store > bookstore > comic_books_store`
- `education > library`
- `arts_and_entertainment > museum`
- `cultural_and_historic > historic_site`
- `cultural_and_historic > memorial_site`
- `cultural_and_historic > memorial_site > monument`

**Consecuencia positiva:** el adaptador reconoce librerías de segunda mano y académicas, no solo la genérica, sin consultas de pago; `taxonomy.hierarchy` detecta descendientes. **Consecuencia limitada:** detectar biblioteca o monumento todavía no establece conexión literaria.

## Avance de implementación adicional: puente explícito hacia contrato #669

[scripts/atlas_overture_to_contract.py](../../scripts/atlas_overture_to_contract.py) y [tests/test_atlas_overture_to_contract.py](../../tests/test_atlas_overture_to_contract.py) (5 casos sintéticos, **NO ejecutados**) ya transforman los POIs prefiltrados de este módulo en registros `places` con **nombres, slug estable, GERS, release, coordenadas y estado candidate** del [contrato #669](https://github.com/davidpd89/web-escritor/pull/669). No los aprueban, generan texto ni publican.

**Interfaz**: `python scripts/atlas_overture_to_contract.py /datos/candidatos.jsonl --destination-id dst-rome --source-id src-overture --bbox 12.4 41.8 12.6 42.0 --out /datos/lugares-candidatos.json` (ejemplo **NO ejecutado**).

**Importante**: los IDs `dst-rome` y `src-overture` deben existir previamente en el snapshot maestro y sus licencias/evidencias estar registradas. La salida es un **fragmento** `{"schema_version":1,"places":[...]}`, **NO el documento completo** de 9 colecciones ni un JSON de la web. Requiere merge/deduplicación editorial controlada y validación de contrato antes de usar. La bbox la fija un destino curado: no supone que `city` del proveedor sea fiable ni geocodifica homónimos. Las bboxes que cruzan el antimeridiano se dividen en dos para no etiquetar mal puntos.

El contrato #669 se amplió para aceptar `place_type=historic_site` y `source_kind=overture_record`, porque anteriormente no admitía esos valores del extractor. Esto corrige una incompatibilidad real entre ramas, sin fusionarlas.
