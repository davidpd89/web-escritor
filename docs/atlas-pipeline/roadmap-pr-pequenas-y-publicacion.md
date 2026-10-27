# Atlas global · roadmap de implementación por PR pequeñas y sin LLM en el runtime

Investigación hija de [PR padre #666](https://github.com/davidpd89/web-escritor/pull/666). **Solo documentación de arquitectura**: no se activa ningún cron, build ni despliegue.

## Registro de fases — prevalece [ADR-000](https://github.com/davidpd89/web-escritor/blob/research/viajes-literarios-atlas-2026-10-21/docs/ideas/viajes-literarios/README.md)

**Estado:** P5 y P8 se desglosan en prototipos e integración futura; P6a es Overture y P6b un adaptador independiente de Pleiades, mientras la verdadera ingesta global de ambos continúa pendiente. Este documento NO implica que una tarea planificada esté implementada o probada.

| Fase/PR | Scope único | Depende de | Criterio de entrada/salida |
|---|---|---|---|
| P0 — [#666](https://github.com/davidpd89/web-escritor/pull/666) | Documento padre, decisiones, catálogo legado y reconciliación | ninguna | Solo investigación; no fusionar como implementación |
| P1 — [#667 Fuentes mundiales](https://github.com/davidpd89/web-escritor/pull/667) | Inventario y consultas Open Library/Wikidata/Geofabrik/GeoNames/Commons | #666 como índice | Licencias/cuotas y plan de descarga local verificadas |
| P2 — [#668 Copias MIT/BSD/ISC](https://github.com/davidpd89/web-escritor/pull/668) | Código upstream copiado literal + licencia y procedencia | #666 | Copia exacta, carpeta aislada no ejecutable hasta adaptación |
| P3 — [#669 Contrato](https://github.com/davidpd89/web-escritor/pull/669) | Schema, estados, integridad relacional y ejemplos sintéticos | #666, revisión fuentes | QA offline en momento autorizado |
| P4 — [#670 Orquestación (ESTA PR)](https://github.com/davidpd89/web-escritor/pull/670) | Arquitectura de ingesta → curación → snapshot → HTML y roadmap | #666 y consulta P1-P3 | No tocar cron existente, identificar gates y responsables |
| P5a — [#671 Muestreador Open Library](https://github.com/davidpd89/web-escritor/pull/671) | **Solo lector parcial offline Works dump**; sin Wikidata ni checkpoint mundial | #667, #669 como contrato posterior | Candidatos, no publicación; QA y normalizador pendientes |
| P5b — [#678 Wikidata por lotes](https://github.com/davidpd89/web-escritor/pull/678) | Generación offline de SPARQL P840/P915/P551, QIDs validados, sin executor ni HTTP | #667, #669 | Espera executor con límites WDQS/QLever y corroboración editorial |
| P6a — [#673 Overture POI por bbox](https://github.com/davidpd89/web-escritor/pull/673) | **Solo lector offline Overture GeoJSON pequeño**, no GeoParquet/GeoNames/OSM | #667, #669 como contrato posterior | Etiquetas y GERS; QA y normalizador pendientes |
| P6b — [#675 Pleiades histórico](https://github.com/davidpd89/web-escritor/pull/675) | **Solo topónimos históricos de un JSON individual**, sin dump global ni vínculo literario | #667 como fuente, #669 tras reconciliación | Alias históricos y precisión a escala de área, QA pendiente |
| P7a — [#679 Dedupe para revisión](https://github.com/davidpd89/web-escritor/pull/679) | Propuestas entre fuentes por IDs y nombre/150 m solo si posición precisa; nunca auto-merge | #669+#673; futuros OSM/GeoNames | QA con fuentes reales y ratio de falsos positivos pendiente |
| P7b — Curación Sheets (FUTURA, no PR creada) | Adaptar patrón `import-reading-sheet.py`: batchGet, review y diffs | P3+P5/P6 | Solo aprobados a vista pública, staging cerrado |
| P8a — [#672 Preview HTML, SEO, filtros por destino](https://github.com/davidpd89/web-escritor/pull/672) | **Preview HTML y JSON shards** fuera del site shell; NO genera sitemap/Pagefind en producción | #669 como contrato posterior | Integración, navegadores, rendimiento/seguridad y SEO pendientes |
| P8-QA — [#677 QA release](https://github.com/davidpd89/web-escritor/pull/677) | Validador manifest→HTML + tests sintéticos + QA browser preparado, sin activar Actions | P8a para el prototipo; integración real futura | No ejecutar hasta que exista shell y manifest de Atlas aprobado |
| P9 — Mapa opcional (FUTURA, no PR creada) | Leaflet con tiles legales o PMTiles; vista lista sin JS | P8 | Performance, licencias, coste, SEO y fallback demostrado |
| P10 — Publicación con control (FUTURA, no PR creada) | Extender coordinador y allowed paths de #661, integridad y lock | P8; P9 opcional | QA por SHA, sin merges simultáneos, recuperación fallos |

| P11 — Distribución (FUTURA, no PR creada) | Reusar enfoques RSS/Pinterest de #662 cuando estén fusionados | P8+P10 | Pines a URLs propias, licencias correctas de imágenes |

**Importante:** varias fases P5a/P6a/P6b/P8a/P8-QA tienen PRs reales documentadas; el resto de las subfases P5–P11 sigue pendiente. No afirmar que importador mundial, curación Sheets, publicación o QA estén implementados. No abrir PR vacías; abrirlas solo con documentación/código real en cada una y scope corto.

## «Fácil, rápido, homogéneo» no significa publicar sin QA

**Normalización canónica**: construir una única función que transforme proveedores diferentes en una representación común con IDs, `source_ref`, timestamp y revisión. Evitar cien plantillas manuales para ciudades: tres plantillas de contenido (destino, lugar, relación/obra) alimentadas por el mismo esquema y motor de diseño web actual.

### Acuerdo de APIs pequeñas y robustas para adaptadores

```text
Adapter.extract(cursor, budget) -> CandidateBatch{
  provider, schema_version, fetched_at, next_cursor?,
  raw_ref, source_license, records[]
}
Normalizer.transform(batch) -> CanonicalCandidates[]
Deduper.resolve(candidates, current) -> {new, match, conflict}
EvidenceGate.propose(candidates) -> ReviewQueue
SheetsBridge.export(reviewed) -> InternalSnapshot
PublicationGate.validate(snapshot) -> PublicProjection
StaticSite.build(projection) -> generated paths
```

**Presupuestos y robustez:** timeouts, `max_requests`, `max_bytes`, `max_items`, backoff sobre 429, ETag, caché de respuesta, checkpoint, manifests reproducibles, `dry_run`. Un 429/cierre de API **no** debe despublicar registros existentes. Nunca mezclar origen raw con `approved`. No almacenar raws completos protegidos ni dumps multi-GB en GitHub.

### Flujo propuesto (sin tokens de modelo)

```text
 Descargas periódicas y consultas acotadas
 Open Library Works — Wikidata QIDs — OSM/Geofabrik — GeoNames
                         ↓
       adaptadores independientes, caché y licencia de origen
                         ↓
     normalizador de identidades + deduplicación con trazabilidad
                         ↓
             COLA DE RELACIONES CANDIDATAS
                         ↓
              Sheets: aprobación humana
                         ↓
          JSON interno → validador → snapshot público
                         ↓
  builders existentes + shell + sitemap + Pagefind + JSON-LD
                         ↓
     PR de artefactos, gates por SHA, merge solo tras aprobación
```

### Estados robustos de publication gate

- `candidate` = detectado automáticamente, jamás publicado.
- `researching` = cola humana.
- `reviewed` = evidencia examinada, todavía no publicada.
- `approved` = URL de fuente realmente prueba afirmación concreta, derechos foto revisados, sin privacidad.
- `rejected/retired` = no se publica y se conserva rastro del motivo.
- Todo borrado público pasa por revisión y redirección, jamás se dispara por un error de API.

### Modelo HTML SEO mínimo: 3 plantillas

**Destino**: canonical estable `/atlas-literario/destinos/<slug>/`; título y descripción original, sitios aprobados agrupados, mapa diferido opcional; páginas vacías no indexables.

**Lugar**: canonical `/atlas-literario/lugares/<slug>/`; ubicación precisa o zona, motivo editorial, tipo de POI, fuentes para relación, fotos permitidas y créditos, enlaces a obras, rutas y ciudad. Librería sin novela no inventa conexión.

**Libro**: mantener siempre ficha existente `/recomendaciones/libros/<slug>/` cuando exista, con bloque «Lugares de este libro», no clonarla dentro del atlas. Si el libro no está publicado, el atlas puede mostrar solo datos bibliográficos permitidos en contexto de lugar; no crear una «ficha libro» comercial.

**Rutas**: fase posterior `/atlas-literario/rutas/<slug>/`, sin Google Directions, horarios ni duraciones adivinadas. Manual o proveedor de rutas legal con contrato.

**Fichas** HTML accesibles sin JS, mapa solo como mejora; navegación y SEO de `data/content-registry.json`, `data/navigation.json`, `build-site-shell.py`, `build-sitemap.py`, `build-pagefind-index.py`, no páginas aisladas con header distinto.

### Integración comercial y costos

- No hacer ping de Google Books/Map APIs desde cada usuario, ni acceso directo a Sheets mediante credencial en HTML.
- No automatizar recomendaciones de hoteles/experiencias de pago ni crear enlaces afiliados turísticos sin programa comercial aprobado.
- Reusar el catálogo Amazon actual solo para ediciones con enlaces válidos y atribución de afiliación visible. Los lugares y mapas no dependen de Amazon.
- Pinterest, solo si hay imagen con licencia publicable y URL propia; nunca reutilizar una cubierta que solo esté autorizada para ficha de libro.
- Ingestión «global» = procesamiento incremental **por regiones** y libros prioritarios, no un cron que descarga el planeta cada mañana.

## Modos de despliegue: decisión A/B

**A (primera fase, menor riesgo):** snapshots aprobados importados mediante PR manual, aprovechando los scripts de generación existentes sin abrir nuevo cron.

**B (escalado posterior):** añadir Atlas como otro productor de artefactos que usa el **mismo escritor serializado** del catálogo de lectura. Requerirá tocar allowed paths de `scripts/publish-reading-refresh.py`, pruebas de seguridad contra rutas externas, CI por SHA y control de carreras de `sitemap.xml` y `pagefind/`. No emitir un segundo auto-merge paralelo.

## Cuellos de botella previsibles

1. **Derechos sobre texto/imágenes**: metadatos abiertos no conceden automáticamente copyright del libro ni fotos.
2. **Calidad de enlaces narrativos**: P840 incompleto, y las guías de localizaciones suelen mezclar adaptación/inspiración/novela.
3. **Duplicados a nivel global**: títulos traducidos, autores homónimos, librerías con sucursales.
4. **Escala de datos**: dumps Open Library/Geofabrik son grandes, no guardar planetas ni íntegros en repo.
5. **Revisión**: priorizar 3 tipos de contenido: lugar cultural oficial, relación literaria documentada, relación disputada explicada con fuente. Nunca «certeza = alta» inventada por modelo.

## Definition of Done del programa

- Cada fuente conserva URL, fecha, licencia y permiso de uso comercial.
- Cada obra, lugar, autor y adaptación tiene ID estable y deduplicación.
- Cada conexión narrativa/biográfica tiene fuente específica y revisión.
- Catálogo puede crecer a miles de candidatos **sin incrementar a miles las llamadas a IA**.
- HTML, web performance, CSP, accesibilidad, sitemap, Pagefind y navegación coherentes.
- Identidad de edición / Amazon se conserva del catálogo actual.
- Sin acciones sobre main, CI o auto-merge hasta permiso del propietario y validación real.

### Estado real de P5 al 21/10/2026

[#671](https://github.com/davidpd89/web-escritor/pull/671) prepara código offline de lectura de dumps Works como candidaturas, pero **no es todavía el adaptador normalizado final**: faltan contrato #669, licencia real y checkpoints para el mundo entero. Esta fase se divide en P5a (muestreador ya creado) y P5b (conversión/homologación posterior), sin autopublicar nada.

### 21/10/2026: PR nuevas reales y dependencias

- [#672](https://github.com/davidpd89/web-escritor/pull/672): generador estático de índice/destino/lugar (previa, no producción), sin mapa embebido, gate de evidencia, HTML y JSON-LD seguros, canonical, breadcrumbs, shards por destino para filtros sin cargar un JSON mundial. No se ha ejecutado QA.
- [#673](https://github.com/davidpd89/web-escritor/pull/673): Overture Places como complemento mundial gratuito (GeoJSON por zonas) para POIs culturales, exporta **solo candidatos**. Pendiente P6b (GeoParquet a escala), taxonomía real y pruebas.
- [#669](https://github.com/davidpd89/web-escritor/pull/669) corregida: relaciones/rutas aprobadas ya no pueden apuntar a entidades candidatas; acepta `overture_gers_id` y versión del origen, sin confundir confianza de POI con certeza narrativa. Pruebas escritas, aún no ejecutadas.

**Importante:** los ejemplos de CLI de Overture no significan descargas realizadas ni cobertura literaria del dataset. Ninguna de las tres PR incorpora código a web actual hasta permiso y validación.
## Actualización sin contradicciones 21/10/2026

- [#675](https://github.com/davidpd89/web-escritor/pull/675) añade candidato histórico Pleiades sin repetir el alcance de #673; ambas salidas siguen como candidatos de fuentes distintas.
- El [contrato operativo y DoD](contrato-integracion-y-gates.md) determina los límites de cada snapshot y publicación; se consulta después del ADR-000, antes de empezar código nuevo.
- En [#672](https://github.com/davidpd89/web-escritor/pull/672) se corrigió carrera de carga asíncrona: un cambio rápido de país/ciudad invalida la petición previa. Pendiente QA real.

### Auditoría site-shell / Pagefind (21/10/2026)

La [#677](https://github.com/davidpd89/web-escritor/pull/677) constató que el builder real `scripts/build-pagefind-index.py` indexa **HTML rastreado por Git**; para incorporar páginas producidas por atlas build al final hay que versionarlas o cambiar explícitamente su lectura al directorio estático con exclusiones equivalentes. Además `lighthouserc.json`, `qa/visual-regression-browser.mjs`, `qa/cross-engine-smoke.mjs` y `qa/csp-public-shell-browser.mjs` necesitan registrar las rutas nuevas. Los presupuestos deterministas no siguen `import()`, por lo que el mapa opcional requiere grupo de presupuesto propio. **No tocar workflows ahora.** El [diseño de Pagefind + UI existente de #672](https://github.com/davidpd89/web-escritor/pull/672) elimina la necesidad de mantener otro buscador global y permite la misma navegación responsive del catálogo de lectura vigente.

### Segunda ronda de autocontrol (21/10/2026)

- [#678](https://github.com/davidpd89/web-escritor/pull/678) cubre el hueco entre ID de obra/autor y consulta Wikidata: crea consultas seguras **pero NO se conecta al endpoint**. Migración pública WDQS→QLever y cuotas en [#667](https://github.com/davidpd89/web-escritor/pull/667).
- [#679](https://github.com/davidpd89/web-escritor/pull/679) cubre el hueco de deduplicación candidato→Sheets sin falsos merges automáticos; escala mundial DuckDB pendiente. **La curación Sheets real sigue FUTURA**.
- [#669](https://github.com/davidpd89/web-escritor/pull/669) corregida: fuente `approved` con URL/título/fecha/evidencia; listas inválidas no bloquean el proceso con excepciones. 13 tests sintéticos no ejecutados.
- [#672](https://github.com/davidpd89/web-escritor/pull/672) produce atributos nativos Pagefind para ID de ciudad/obra/autor/vínculo, pero **se eliminó** `data-pagefind-body` porque [Pagefind advierte](https://pagefind.app/docs/indexing/) que un subconjunto marcado puede hacer desaparecer del buscador al resto de páginas sin la marca. [#677](https://github.com/davidpd89/web-escritor/pull/677) incorpora regresión offline que prohíbe este error en las fichas Atlas.
