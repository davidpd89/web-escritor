# Atlas mundial — contrato v1 para nueve colecciones, sin datos públicos

PR hija de [#666](https://github.com/davidpd89/web-escritor/pull/666). **Fase de ingeniería base**, no publica fichas, no migra `data/atlas-literario.json`, no ejecuta Actions ni modifica páginas existentes.

## Fuentes de verdad, decisiones

- [schema](../../schemas/atlas/catalogue-v1.schema.json): documento JSON Schema Draft 2020-12 que separa `destinations`, `places`, `works`, `authors`, `adaptations`, `sources`, `relationships`, `images`, `routes`. Se pueden añadir tablas cuando se apruebe v2, no cambiar silenciosamente v1.
- [comprobador](../../scripts/atlas_contract_check.py): Python standard-library para las **referencias entre entidades** y algunas reglas de publicación: ID único, destino/lugar, obra/autores, adaptación↔obra, rodaje↔adaptación, fuente obligatoria en relación, mito no aprobado, geo sin pin falso, autor sin dirección actual, imágenes con atribución. No es validador JSON Schema completo.
- [pruebas sintéticas](../../tests/test_atlas_contract_check.py): nueve casos sintéticos sin archivos reales ni red; **escritos, NO ejecutados** por respetar la instrucción de no lanzar pruebas/Actions. Cuando se autorice CI, comprobar resultado y reparar cualquier falla.

**Punto esencial:** el JSON representa la **mesa editorial interna**. Una futura exportación a la web (PR distinta) debe publicar **solamente** relaciones y entidades aprobadas, suprimir `reviewer_note_private` y demás datos privados, evitar claves, direcciones particulares de autores y HTML de fuentes externas.

### Reglas futuras fuera de JSON Schema

JSON Schema comprueba formas, no existencia de claves externas ni que una fuente realmente pruebe una relación. El comprobador offline contempla algunas reglas cruzadas. Quedan pendientes: fechas ISO de calendario real (no solo regex), URL allowlist/redirect, unicode alias, deduplicación de obras, calidad de imagen/permiso comercial, suplantación de enlaces, datos privados y propiedad intelectual; todo ello en una PR de validación reforzada.

### Contrato Sheets — no mezclar con importador de libros existente

**Pestañas recomendadas**: 01_DESTINOS, 02_LUGARES, 03_OBRAS, 04_AUTORES, 05_ADAPTACIONES, 06_FUENTES, 07_RELACIONES, 08_IMAGENES, 09_RUTAS. Los nombres difieren deliberadamente de las pestañas del catálogo de lectura. Exportación a JSON versionado con mapeo de claves. Ver docs de [PR #666](https://github.com/davidpd89/web-escritor/pull/666).

**Separar WORK vs EDITION:** `works.reading_book_id` hace referencia al libro existente en el catálogo del autor cuando haya ficha real; ISBN es de edición, no clave global de obra. Una obra sin ficha aprobada no crea automáticamente portada ni enlace Amazon.

**Geografía:** los campos `latitude` y `longitude` se guardan separados en JSON y se convierten a GeoJSON en orden `[longitude, latitude]` cuando existan. El tipo `geo_precision=city|area|unlocated` no se presenta con un pin de fachada.

**Visibilidad:** permitir POIs culturales (librería, biblioteca) con fuente propia aunque no tengan novela relacionada. Las conexiones a novelas/rodajes/autores tienen evidencia individual y estado propio.

### Ejecución de revisión

```sh
pip install jsonschema==4.26.0   # solo para la capa JSON Schema de las pruebas
python -m unittest discover -s tests -p 'test_atlas_contract_*.py'
python scripts/atlas_contract_check.py ruta/a/snapshot-interno.json   # 0 ok, 1 fallos, 2 JSON ilegible
```

Dos capas complementarias: `tests/test_atlas_contract_schema.py` valida el schema con un validador real Draft 2020-12 (con `format: date`); el gate Python cubre lo que JSON Schema no puede expresar (referencias, estados aprobado/candidato, slugs únicos, parada de ruta del mismo destino). El workflow `atlas-contract.yml` las ejecuta en cada cambio de estos ficheros.

## No metas estos cambios en un cron automáticamente

El publicador de [PR #661](https://github.com/davidpd89/web-escritor/pull/661) tiene allowlist de rutas que **no incluye Atlas**. Incorporar un publicador separado sin locking es incorrecto. Ver plan de orquestación en la hija de automatización. Una futura PR de publicación deberá ampliar allowlist, pruebas de seguridad, diffs de artefactos y regeneración de shell/sitemap/Pagefind.

## Pendiente antes de marcar «ready for merge»

- [x] Contrato declarativo v1, sin dataset real.
- [x] Validador referencial sin red, casos sintéticos preparados.
- [ ] QA local y JSON Schema completo comprobados contra pruebas; confirmar en momento autorizado.
- [ ] Revisión de fuentes de verdad de `reading_book_id` y IDs aceptados.
- [ ] Decidir si esquema detallado se versiona como backoffice (recomendado) o si se genera una proyección pública independiente.

## Compatibilidad detectada con otros módulos (21/10/2026)

- Contrato ahora incluye `place_type=historic_site` y `source_kind=overture_record/geonames_record/whg_record`. Sin esto el extractor de Overture [#673](https://github.com/davidpd89/web-escritor/pull/673) proponía registros incompatibles con nuestro propio JSON Schema. **Corregido**.
- `places.overture_gers_id`, `overture_release`, `overture_confidence` describen **POI externo**; no certifican relación novela-lugar.
- `destinations.summary_original` permite exigir introducciones editoriales auténticas antes de crear páginas indexables en [#672](https://github.com/davidpd89/web-escritor/pull/672).
- El validador Python ya rechaza que una relación/ruta `approved` apunte a un lugar, destino u obra aún candidatos (nueve casos sintéticos preparados, pero **NO ejecutados**).
- El nuevo convertidor de [#673](https://github.com/davidpd89/web-escritor/pull/673) solo produce `places` candidatas con un `destination_id` y `source_id` de la base editorial. Es un **fragmento interno** y debe unirse al snapshot antes de validación completa. No confundir contrato de 9 colecciones con un CSV/fragmento de importador.

Las decisiones de esquema vigentes están en [ADR-000](https://github.com/davidpd89/web-escritor/blob/research/viajes-literarios-atlas-2026-10-21/docs/ideas/viajes-literarios/README.md); este documento solo detalla implementación y pruebas pendientes.

## Auditoría correctiva posterior (21/10/2026)

El gate Python anterior podía **aprobar un lugar con una fuente que solo tuviera `id`**, sin título, fecha ni evidencia, porque comprobaba únicamente la existencia de `source_ids`. Ya está corregido: para lugares y relaciones `approved`, cada fuente referenciada exige URL HTTPS, título, `retrieved_at` y `evidence_summary`; una imagen `approved` no puede apuntar a un lugar `candidate`. Las listas `author_ids`, `source_ids`, `image_ids` y `place_ids` malformadas generan errores de contrato, no excepciones inesperadas. 13 pruebas sintéticas, ejecutadas.

La comprobación Python sigue siendo **suplementaria**, no sustituye a JSON Schema 2020-12 ni verifica que la URL responda 200 o que el texto fuente sea legalmente reproducible. El constructor HTML #672 conserva su propio gate provisional y deberá reutilizar el contrato de 9 colecciones durante la integración. No afirmar mergeable hasta QA.

### URL de fuente: bloqueo adicional

El parser `urlsplit` más una regex para espacios/control exige **URL HTTPS con hostname**, sin credenciales incrustadas ni puertos ajenos a 443 para fuentes aprobadas. Esto corrige un caso que antes pasaba: la cadena `https://` cumplía un simple `startswith('https://')` pese a no ser un enlace válido. **14 casos sintéticos, ejecutados**. La comprobación de que un sitio externo responde y licencia material sigue pendiente de QA con permisos.

### Hallazgos de compatibilidad verificados (23/10/2026)

- [#673](https://github.com/davidpd89/web-escritor/pull/673) `atlas_overture_to_contract.py` escribe `overture_confidence: row.get("provider_confidence")`; si el proveedor no la trae emite `null`, que el schema rechaza (`type: number`). Debe omitir la clave cuando es `None`. Salida por lo demás schema-válida como `places` candidatas (probado con la forma del fragmento).
- [#672](https://github.com/davidpd89/web-escritor/pull/672) mantiene su gate propio (aprobado + `verified_at` + HTTPS); es menos estricto que este contrato (no comprueba slugs únicos, paradas del mismo destino ni fechas reales). Debe reutilizar `atlas_contract_check.problems()` antes de renderizar.
- `works.reading_book_id`: los IDs de `data/reading-catalogue.json` (63) cumplen el patrón de ID del contrato; la existencia/`estado=publicado` del libro la comprueba #672 con `--reading-catalogue`, no este gate.
