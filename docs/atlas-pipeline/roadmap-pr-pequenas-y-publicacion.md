# Atlas global · roadmap de implementación por PR pequeñas y sin LLM en el runtime

Investigación hija de [PR padre #666](https://github.com/davidpd89/web-escritor/pull/666). **Solo documentación de arquitectura**: no se activa ningún cron, build ni despliegue.

## Cadena de PRs (cada una pequeña y mergeable por separado una vez validada)

| Fase/PR | Scope único | Depende de | Criterio de entrada/salida |
|---|---|---|---|
| P0 — [#666](https://github.com/davidpd89/web-escritor/pull/666) | Documento padre, decisiones, catálogo legado y reconciliación | ninguna | Solo investigación; no fusionar como implementación |
| P1 — [#667 Fuentes mundiales](https://github.com/davidpd89/web-escritor/pull/667) | Inventario y consultas Open Library/Wikidata/Geofabrik/GeoNames/Commons | #666 como índice | Licencias/cuotas y plan de descarga local verificadas |
| P2 — [#668 Copia MIT](https://github.com/davidpd89/web-escritor/pull/668) | Código upstream copiado literal + licencia y procedencia | #666 | Copia exacta, carpeta aislada no ejecutable hasta adaptación |
| P3 — [#669 Contrato](https://github.com/davidpd89/web-escritor/pull/669) | Schema, estados, integridad relacional y ejemplos sintéticos | #666, revisión fuentes | QA offline en momento autorizado |
| P4 — [#670 Orquestación (ESTA PR)](https://github.com/davidpd89/web-escritor/pull/670) | Arquitectura de ingesta → curación → snapshot → HTML y roadmap | #666 y consulta P1-P3 | No tocar cron existente, identificar gates y responsables |
| P5 — Importador de fuentes bibliográficas | 1 adapter local Open Library + 1 adapter Wikidata, caché y checkpoint | P1+P3 | Snapshot **candidatos** sin publicación, O(1) llamadas/candidato o dumps |
| P6 — Importador cultural mundial | Extractos Geofabrik acotados + GeoNames, merges por IDs | P1+P3 | Duplicados, licencias y precisión controlados |
| P7 — Curación Sheets | Adaptar patrón `import-reading-sheet.py`: batchGet, review y diffs | P3+P5/P6 | Solo aprobados a vista pública, staging cerrado |
| P8 — Generación de páginas | Refactor `build-atlas-literario.py` y plantillas site shell, detalles/destinos/listas | P3+P7 | Sin enlaces huérfanos, canonical, sitemap/Pagefind, accesibilidad y QA móvil |
| P9 — Mapa (OPCIONAL) | Leaflet con tiles legales o PMTiles; vista lista sin JS | P8 | Performance, licencias, coste, SEO y fallback demostrado |
| P10 — Publicación con control | Extender coordinador y allowed paths de #661, integridad y lock | P8; P9 opcional | QA por SHA, sin merges simultáneos, recuperación fallos |
| P11 — Distribución | Reusar enfoques RSS/Pinterest de #662 cuando estén fusionados | P8+P10 | Pines a URLs propias, licencias correctas de imágenes |

**Importante:** estas fases P5-P11 son un backlog de ingeniería, NO PRs que afirmemos haber creado. No abrir PR vacías; abrirlas solo con documentación/código real en cada una y scope corto.

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
