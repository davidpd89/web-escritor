# Contrato de implementación «Atlas mundial»: integración en piezas (21/10/2026)

**P4 · planificación técnica en [#670](https://github.com/davidpd89/web-escritor/pull/670)**. Documento operativo para un futuro implementador/Codex; prevalece [ADR-000 de #666](https://github.com/davidpd89/web-escritor/pull/666). Evita volver a buscar repositorios y rehacer arquitectura. **No declara terminado algo sin QA.**

## 1. Flujo definitivo y frontera de confianza

```text
Open Library Works dumps ----BookBrainz CC0 (opcional) -----\
Wikidata P840/P915 -----------> candidatos internos     [SIN derecho de publicación]
Overture/OSM ------------------/
Pleiades/NHLE/Mérimée --------/           |
FilmMap CC0 (adaptaciones) ---------------+--> reconciliación IDs/versión/licencia
                                            --> evidencia concreta POR relación
                                            --> Sheets: revisión humana
                                            --> snapshot APROBADO privado
                                            --> gate de integridad + proyección pública
                                            --> HTML shell existente + Pagefind + sitemap
                                            --> PR revisada con SHA -> merge usuario
```

**Capas innegociables:** proveedor!=verdad literaria; obra!=edición; POI!=escena; película!=novela; topónimo antiguo!=fachada moderna; foto!=metadato. Un error de API o falta de derechos nunca despublica masivamente.

## 2. Contratos mínimos entre módulos y ficheros

| Artefacto (nombre de interfaz propuesta, NO fichero ya creado) | Responsable | Entrada | Salida y control |
|---|---|---|---|
| `source-manifest.json` | cada adaptador | endpoint o dump local, release fijada | `provider, dataset_id, version, retrieved_at, sha256, rights_uri, attribution, license_checked_at, cursor, bounds, count`; obligatorio sin secretos |
| `raw-candidates/*.jsonl` fuera del repo | extractores #671/#673/#675 | dump Works, bbox Overture, Pleiades snapshot | `provider_record_id`, nombres, external IDs, precisión, estado candidate; nunca HTML ni claves |
| `candidate-normalized.jsonl` | deduper (FUTURO) | varios proveedores | clave estable + IDs externos + conflictos y provenance; **no merge automático por título/latlon aproximadas** |
| `editorial-queue.tsv` | puente Sheets (FUTURO) | candidatos normalizados y propuestas de relación | IDs, evidencia por vínculo, veredicto, licencia, fecha, revisor. Enviar fragmentos, no dump total |
| `atlas-internal-v1.json` | exportador editorial (FUTURO) | filas aprobadas Sheets y catálogo de obras | 9 colecciones de #669 + notas internas. PRIVADO, no copiar a `dist/` |
| `atlas-public-projection-v1.json` | gate (FUTURO) | interno aprobado+revisado | **únicamente** IDs, nombres/texto original, URL source válida, licencia de fotos permitidas, relaciones verificadas; excluir `reviewer_note_private` |
| `atlas/facets/index.json` + `destinos/<slug>.json` | preview #672 → futuro generador real | proyección pública | JSON mínimo de regiones/ciudades, lugares aprobados, vínculos; gzip/ETag/CDN, URL segura |
| `/atlas-literario/`, `destinos/`, `lugares/` | renderer #672 → futuro shell | proyección pública | HTML completo, canonical, breadcrumbs, Pagefind, sitemap, una URL por ficha real |

**Semántica de estados**: `candidate, researching, reviewed, approved, rejected, retired`. Approval depende de **persona/revisor**, fecha y referencia, no del proveedor; cualquier fila con `status=approved` pero evidencia/entidad no aprobada → error de build.

## 3. Qué está preparado y qué falta exactamente por PR

| PR | Preparado y copiado | Falta para poder usarla |
|---|---|---|
| [#667](https://github.com/davidpd89/web-escritor/pull/667) | Fichas técnicas oficiales y licencias (OL, Overture, GeoNames, Pleiades, FilmMap, IIIF, BookBrainz, patrimonio) | Muestreo medido, fuentes elegidas y matriz de atribución por lotes |
| [#668](https://github.com/davidpd89/web-escritor/pull/668) | Código original MIT/BSD/ISC con avisos, filtros/mapas/styling de terceros | Adaptar dependencias/paquetes; no cargar Astro/servidor MCP entero en web; controlar licencia de tiles |
| [#669](https://github.com/davidpd89/web-escritor/pull/669) | JSON Schema 2020-12 y gate de referencias con casos sintéticos | Ejecutar QA autorizado; validación JSON Schema completa, cruce real de IDs, proyección pública |
| [#671](https://github.com/davidpd89/web-escritor/pull/671) | Works dump local -> candidatos de `subject_places` | Checkpoint mundial, comprobación de archivo real, dedupe QIDs y fuente literaria |
| [#673](https://github.com/davidpd89/web-escritor/pull/673) | GeoJSON bbox + puente `place` candidates | DuckDB/GeoParquet para volumen, manifest, dedupe con OSM, datos reales |
| [#675](https://github.com/davidpd89/web-escritor/pull/675) | JSON individual Pleiades -> aliases/épocas/centro aproximado candidates | Procesador de dump por lotes, match Pleiades ↔ GeoNames/Wikidata, periodo y fuente literaria |
| [#672](https://github.com/davidpd89/web-escritor/pull/672) | Preview HTML canónico + facetas/JS lazy | Integración site shell, CSS/CSP/Pagefind/sitemap, búsqueda mundial libro/autor, mediciones Core Web Vitals |
| [#670](https://github.com/davidpd89/web-escritor/pull/670) | Este contrato y roadmap | No implementar autopublisher sin puerta de seguridad, locks y control de #661 |

## 4. Decisiones de ejecución eficiente

- APIs online solo para **descubrimiento puntual**; volúmenes del mundo por **dumps regionales** y cursor. No hacer 50.000 peticiones Pleiades ni centenares por libro contra Open Library.
- Emplear solo Python estándar para transformaciones pequeñas y existente Python build. Si el cuello es volumen, incorporar DuckDB con versión fijada, no desplegar Postgres/Next.js por comodidad.
- Reutilizar Pagefind existente para búsqueda textual global; evaluar un **índice mínimo invertido obra/autor→IDs de destinos** antes de añadir otro motor. No descargar millones de `places` en el cliente.
- Google Sheets como *revisión*, no frontend ni fichero único de millones de candidatos. Estado de revisión persistente por IDs; operación en lotes de máximo razonable tras medir.
- El mapa es *progressive enhancement*: HTML y texto siempre listos sin JS, mapa externo primero, después WebP estático legítimo/Leaflet bajo clic. UI solo descarga JSON de destino visible.
- Rutas: reducir geometrías con Simplify.js **solo después de rutas geográficas verdaderas**, no confundir secuencia narrativa con itinerario caminable.
- Cuando un origen deja de responder, conservar último snapshot verificado y generar alerta editorial; **no borrar fichas sin revisar**.

## 5. Definition of Done específica y comprobable (futuro, sin ejecutar ahora)

1. **Fuente**: URL + release + licencia/atribución + integridad SHA + fecha; 0 llamadas de IA por visita.
2. **Modelos**: 0 claves huérfanas, 0 slugs duplicados, 0 relaciones aprobadas→candidatas, 0 imágenes sin permiso; errores bloquean publicación.
3. **Web**: ninguna tarjeta hacia 404, canonical 1 por URL, sitemap/Pagefind solo aprobados; mismo header/footer del sitio real, no doble diseño.
4. **SEO**: no facetas indexables infinitas, no `SearchAction` sitelinks antiguo, no claims de estrellas o horarios inventados; HTML rastreable sin JS.
5. **Performance**: presupuestos LCP/INP/CLS medidos p75 móvil y desktop comparando páginas existentes; JS/mapa no cargado en primer render.
6. **Accesibilidad**: filtros por teclado, aria-live, sin JS y estados de carga/error; cambio rápido de ciudad no pinta respuesta antigua (corregido en #672).
7. **Publicación**: proceso serial con #661; PR manual para primeras fichas. Actions/QA/merge solo cuando lo autorice el usuario.
8. **Regresión**: /recomendaciones/ y Amazon no alterados, schema/filtrado/editoriales del catálogo tras merge #665 revisados.
