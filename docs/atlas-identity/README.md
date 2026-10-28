# P7a · Resolución de identidades de POIs para revisión humana (21/10/2026)

**PR hija independiente del [ADR-000 #666](https://github.com/davidpd89/web-escritor/pull/666)**. Esta pieza completa un hueco real entre los extractores (#673 Overture, #675 Pleiades futuro, OSM/GeoNames futuros) y la hoja de revisión Sheets. **No fusiona registros, no publica nada.**

## Por qué no basta con comparar nombre y distancia

Una librería puede tener nombre distinto en Wikidata/OSM/Overture, un museo antiguo puede aparecer como edificio y barrio, y varias sucursales comparten marca. Además, un punto de ciudad `geo_precision=city` no es una fachada. Un algoritmo automático que fusione `mismo nombre a 150 m` daría falsos positivos. Esta PR **solo sugiere parejas para revisión editorial**.

## Código existente y entrada exacta

- [scripts/atlas_candidate_identity_proposals.py](../../scripts/atlas_candidate_identity_proposals.py) **Python stdlib**, compara dos snapshots locales `{"schema_version":1,"places":[...]}`, máximo 3000 entradas por lado/4 MiB por archivo. Diseñado para pilotos por destino, **no para comparar el planeta**.
- [tests/test_atlas_candidate_identity_proposals.py](../../tests/test_atlas_candidate_identity_proposals.py): 9 casos sintéticos escritos, **NO ejecutados**.
- Separa `wikidata_qid`, `overture_gers_id`, `geonames_id`, `pleiades_id` y par `osm_type + osm_id`. Si hay ID común propone `shared_external_id_review`, pero no merge; si las ciudades asignadas discrepan propone `same_id_different_destination_review`.
- Si no hay ID compartido, solo propone por nombre normalizado (acentos) + **≤150 m** entre **dos coordenadas de punto/edificio explícitas**, en el **mismo destino**. El resultado siempre es `REVIEW_REQUIRED`, `automatic_merge=false`.
- Si dos QIDs son distintos, aunque nombre y distancia coincidan, deja `conflicting_qids_review`; nunca atribuye un libro por vecindad.
- No copia raws, emails ni direcciones; la salida contiene IDs y nombres, motivo, coincidencias verificables y distancia aproximada. Solo uso interno.

## Ejemplo de fase posterior, NO ejecutado

```sh
# Dos listas NORMALIZADAS como fragmentos candidate de proveedor; no datos públicos.
python scripts/atlas_candidate_identity_proposals.py \
  --left /datos/atlas/places-overture-coimbra.json \
  --right /datos/atlas/places-osm-coimbra.json \
  --out /datos/atlas/propuestas-coimbra.json
# 0 fusiones automáticas, revisión Sheets obligatoria.
```

**Integración futura con #673:** su `scripts/atlas_overture_to_contract.py` genera fragmentos `places` `status=candidate` compatibles. El segundo snapshot lo producirá un futuro importador OSM/Geofabrik/GeoNames. **Pleiades #675** produce candidato histórico `pl-...` con centro de área y todavía no `destination_id`: **NO introducirlo directamente**, primero reconciliar identidad/municipio sin precisión falsa. Una coordenada de ciudad no es elegible para dedupe por cercanía.

## Camino de escala sin API de pago

1. Tras comprobar reglas con 3 destinos y revisión editorial de falsos positivos, expandir con DuckDB/GeoParquet desde snapshots locales, `JOIN` bloqueado por ID o país/municipio + proximidad real y etiquetas normalizadas.
2. No ejecutar pares cuadráticos en 78M POIs ni todos los continentes en GitHub Actions. Los bloques se calculan fuera de CI con coste/almacenamiento monitorizados.
3. En Sheets, presentar pares + **mantener separados / misma identidad / duda**, usuario/revisor, fecha, razones y dos fuentes. Solo confirmaciones crean relación de IDs.
4. Registrar equivalencia alias/IDs en el grafo canónico #669, **sin reasignar slugs ya publicados** ni destruir fuentes o fechas.
5. Probar nombres en griego/cirílico/árabe: `unicodedata` sin transliteración interalfabeto puede perder coincidencias; en ese caso usar QIDs/IDs externos, nunca adivinar la identidad.
6. Registrar costes de almacenamiento y tasa de falsos positivos/negativos; eficacia se mide por horas ahorradas de revisión y errores evitados, no por total de uniones.

## Riesgos y decisiones no escondidas

- Esta PR no puede validar una equivalencia **con datos reales** sin muestras; es una heurística pequeña y deliberadamente conservadora.
- QID idéntico no siempre basta para fusionar casas/museos/destinos, y un QID distinto puede ser un error del proveedor: ambos son **propuestas**, no sentencia.
- La `id` editorial repetida en ambos snapshots provoca error explícito: resolver la procedencia antes de procesar cambios de versión de un mismo proveedor.
- El script solo acepta candidatos; los aprobados se revisan mediante otro flujo de actualización seguro. No toca datos públicos ni raw output de Google Sheets.

**Estado:** draft, un módulo; sin API, red, LLM, Actions, tests ejecutados, merge ni producción.
