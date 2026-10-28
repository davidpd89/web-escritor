# Código reutilizable: qué vendorizar y qué instalar (21/10/2026)

**Hija de [#666](https://github.com/davidpd89/web-escritor/pull/666).** El repositorio GitHub público **no concede automáticamente** derechos de copia. Hemos revisado las licencias originales de estos archivos; si se usa una librería, hay que cumplir su licencia, avisos y dependencias.

## Repos y licencias verificadas directamente

| Repositorio, licencia | Uso real en el Atlas | Modo recomendado |
|---|---|---|
| [Read the Places](https://github.com/markselby9/readtheplaces.com/blob/main/LICENSE) · código **MIT**, datos **CC BY-SA 4.0**, materiales terceros aparte | Detector candidatos y gate de frescura | **3 archivos TS copiados literalmente en esta PR** + normalizador + LICENSE. Mantener separados del runtime hasta adaptación. |
| [DuckDB](https://github.com/duckdb/duckdb/blob/main/LICENSE) · **MIT**, © 2018–2026 DuckDB Foundation | Consultar volcados Open Library JSONL/TSV y preparar filtros de millones de filas con SQL local sin servidor | **Instalar versión fijada**, no copiar motor C++; extraer JSON propio. |
| [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz/blob/main/LICENSE) · **MIT** | Comparación de alias/títulos, probable duplicado — nunca merge automático de homónimos | Dependencia opcional solo para trabajos offline de deduplicación. |
| [Leaflet](https://github.com/Leaflet/Leaflet/blob/main/LICENSE) · **BSD-2-Clause** | Mapa callejero por destino y puntos | Fijar release y guardar aviso. Añadir solo al cargar mapa (no en todas las páginas). |
| [MapLibre GL JS](https://github.com/maplibre/maplibre-gl-js/blob/main/LICENSE.txt) · licencia BSD con aviso de contribuyentes | Mapa vectorial y clusters muchos lugares | Alternativa posterior a Leaflet, no ambas sin necesidad; revisar worker/CSP y proveedor de teselas. |
| [PMTiles](https://github.com/protomaps/PMTiles/blob/main/LICENSE) · **BSD-3-Clause** para implementaciones, especificación pública/CC0 | Mapas de teselas en archivo con Range GET | Útil si hosting permite Range y los costes de ancho de banda son aceptables; no equivale a derechos de todos los tiles. |
| [Jinja](https://github.com/pallets/jinja/blob/main/LICENSE.txt) · licencia BSD | Plantillas HTML homogéneas | **Primero** reutilizar el builder existente; usar Jinja solo si reduce realmente duplicados de plantillas sin romper shell. |
| [python-jsonschema](https://github.com/python-jsonschema/jsonschema/blob/main/COPYING) · **MIT** | Validación completa del contrato JSON Schema v1 | Instalar versión fijada offline en QA **cuando se autorice**; evitar reimplementar todo estándar. |
| [spaCy](https://github.com/explosion/spaCy/blob/master/LICENSE) · **MIT** | NER local de topónimos en textos cuyo tratamiento sea legítimo | Fase avanzada, NO imprescindible con datos estructurados y bibliografía. Modelos tienen licencias propias. |
| [GLiNER](https://github.com/urchade/GLiNER/blob/main/LICENSE) · **Apache-2.0** | NER multilingüe/domain-specific cuando haya corpus con permisos | Fase avanzada, costes CPU/modelo y posibles licencias separadas; no deducir que todos los pesos puedan copiarse. |
| [Open Library Python client](https://github.com/internetarchive/openlibrary-client/blob/master/LICENSE) · **AGPL-3.0** | Cliente para consultar API Open Library | **Preferir API REST simple o descarga de dumps** para no asumir obligaciones AGPL sobre un servicio más amplio sin análisis específico. |

## Criterio de decisión reproducible

1. ¿Ya hay código propio probado en main? Sí → reutilizar en vez de introducir framework nuevo.
2. ¿Es código pequeño con licencia permisiva y función central? Sí → **vendor con fuente exacta, commit/blob, copyright y licencia** (como esta PR).
3. ¿Es librería grande mantenida activamente? Sí → usar paquete con versión fija, checksum/lock y avisos; **NO copiar miles de líneas** y perder actualizaciones de seguridad.
4. ¿Tiene licencia GPL/AGPL, copyleft de datos, o carece de LICENSE? → abrir investigación de compatibilidad antes de añadir código o dataset. Repos sin licencia pueden citarse y estudiarse, no copiarse por defecto.
5. Si el mismo proveedor da **código MIT y datos CC BY-SA**, tratarlos como dos objetos separados. Nunca suponer que copiar código concede permiso sobre los mapas/fotos/libros.

## Compatibilidad técnica actual

- Nuestra web es estática HTML/CSS/JS; `scripts/build-atlas-literario.py` y `scripts/build-reading-catalogue.py` ya son motores Python.
- No migrar el sitio a Next.js/Astro por copiar Read the Places. Bastaría adaptar algoritmos puntuales y mantener plantillas actuales.
- `places.ts` es **literal upstream**; su import `@rtp/schema` no resuelve fuera del monorepo. Una futura PR debe crear **adaptador**; no afirmar que el archivo está integrado, compilado ni listo para ejecutar.
- De frescura de despliegue, `freshness.ts` compara SHA de versión y conteos; en nuestra web debe reescribirse el medidor para comparar `published_places`, `published_relationships` y SHA real de Pages. La copia archivada no lo hace.

## Licencias/datos críticos en la web

- Al usar OSM/Geofabrik: reconocer `© OpenStreetMap contributors` y licenciamiento ODbL, respetar obligaciones de bases derivadas; software Leaflet BSD no cubre la licencia de datos.
- Fotografía de Commons: permiso individual, atribución y licencia; copyright de cubierta de novela distinto.
- Wikidata CC0 sí admite uso de estructura, pero **no garantiza que la afirmación sea correcta**.
- Nada del código vendorizado ejecuta redes, tests, builds o Actions por haber sido añadido aquí; no está importado por el catálogo público.

## QA pendiente

- [ ] Verificar, antes de ejecutar, licencia y versión exacta de cualquier paquete elegido, pin y compatibilidad con Python/Node del proyecto.
- [ ] Resolver alias del código copiado con un wrapper, nunca editar snapshot upstream original si queremos mantener trazabilidad.
- [ ] Tests de falsas detecciones multilingües (París/Paris, Georgia país/estado, Londres en varios países, nombres propios que no sean topónimos) y copyright de textos.
