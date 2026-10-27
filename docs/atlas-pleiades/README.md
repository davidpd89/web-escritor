# Pleiades → candidatos de topónimo histórico (P7a, independiente)

**PR hija de [#666 / ADR-000](https://github.com/davidpd89/web-escritor/pull/666).** Fuente documentada en [#667 (fuentes mundiales)](https://github.com/davidpd89/web-escritor/pull/667). Esta PR añade **solo** código pequeño, sin tareas automáticas ni integración con web.

## Justificación

Un topónimo en una novela histórica puede representar una ciudad bajo un nombre anterior. Un sistema ingenuo trataría `Athenae`, `Athens`, `Atenas` como tres lugares o geocodificaría un sitio arqueológico inexistente a un comercio actual. [Pleiades](https://pleiades.stoa.org/downloads) conserva identidades históricas, alias, periodos y geometría aproximada: permite buscar equivalencias de sitios clásicos, **sin inventar que una novela transcurre en ese lugar**.

- [API/dumps oficial](https://api.pleiades.stoa.org/), [release 4.1 en GitHub](https://github.com/isawnyu/pleiades.datasets/releases): edición 28/05/2025 con 41.480 lugares publicada según Pleiades. Descargar snapshots numerados para reproducibilidad; JSON/RDF de cada recurso mediante endpoint `/places/{id}/json`.
- [Licencia Pleiades](https://pleiades.stoa.org/help/using-pleiades-data): **CC BY 3.0**, atribución obligatoria. Los metadatos de citas bibliográficas incluidos en JSON pueden remitir a terceros; no copiar `formattedCitation` ni material de terceros a nuestra web.
- [Ejemplo oficial vivo de Atenas](https://pleiades.stoa.org/places/579885/json): `features: []`, pero `reprPoint: [23.72..., 37.97...]`, `names[].romanized/attested`, `language` y `attestations[].timePeriod`. **El centro de una ciudad NO es la coordenada de una escena literaria**.

## Archivos (sin dependencias externas ni red)

- [scripts/atlas_pleiades_candidates.py](scripts/atlas_pleiades_candidates.py): lee **un fichero JSON Pleiades local** hasta 2 MiB; genera una fila candidata con ID externo, alias históricos, periodo, punto representativo con `geo_precision=area_or_city` o `unlocated`, estado `candidate`, URL origen y `CC-BY-3.0`. No importa fotografías, HTML de citas o biografía.
- [tests/test_atlas_pleiades_candidates.py](tests/test_atlas_pleiades_candidates.py): **6 casos sintéticos escritos, NO ejecutados**: record sin features, names/época, lon/lat, ausencia de punto, borradores y citas ajenas.

### Ejemplo de uso futuro local

```sh
# No se ha ejecutado ni descargado en esta PR:
python scripts/atlas_pleiades_candidates.py /datos/pleiades/579885.json \
  --release 4.1 --output /datos/atlas-candidatos/pleiades-579885.json
# QA posterior autorizado:
python -m unittest discover -s tests -p 'test_atlas_pleiades_candidates.py'
```

**Salida:** candidata de topónimo antiguo para reconciliación, **NO** es una fila `place` del contrato #669 y **NO** se presenta en HTML. Para transformarla a `place`, un editor debe resolver (a) identidad y ubicación moderna, (b) si es visitable, (c) precisión real, (d) vínculo con obra/autores avalado, (e) fuente de cada afirmación y licencia. Algunos nombres clásicos fueron *territorios*, no POIs físicos visitables.

## Deuda concreta antes de implementación mundial

1. Probar contra muestra diversa de 10 IDs con y sin coordenadas, transliteraciones y periodos; comprobar el `id` real y esquemas alternativos de dump.
2. Procesar el **dump versionado completo en streaming**, no 41.480 descargas a la API; deduplicación `pleiades_id → wikidata_qid → geonames_id` con revisión de ambiguos.
3. Convertir periodo histórico del gazetteer a fechas solo cuando sean auténticamente comparables; evitar usar año de Pleiades como época del argumento de novela.
4. Unificar fuentes y estado aprobado en snapshot #669; `reprPoint` puede mostrarse a escala zona/ciudad cuando hay fuente, jamás como fachada exacta.
5. Atender condiciones CC BY 3.0 con atribución por fuente, separadas de fuentes CC0 y ODbL en el mismo lugar.

**Esta PR no cambia** main, sitemap, CSS, Pagefind, JS, Actions, ni catálogo de lectura; requiere revisión/QA antes de merge.