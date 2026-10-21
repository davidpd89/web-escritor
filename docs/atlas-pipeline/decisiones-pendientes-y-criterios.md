# Decisiones de producto antes de la implementación — preguntas ya contestadas por arquitectura

**Fecha 21/10/2026.** Complementa [ADR-000](https://github.com/davidpd89/web-escritor/pull/666) y [contrato de artefactos](contrato-integracion-y-gates.md). No crear alternativas paralelas aquí: las decisiones firmes viven en ADR, esta es una lista de *decisiones por defecto y criterios de aceptación* para el futuro desarrollo.

| Pregunta concreta | Respuesta de trabajo (salvo revisión editorial) | Qué lo validará |
|---|---|---|
| ¿Se entra por destino, título o autor? | **Las tres puertas en el hub**, sin duplicar datos ni generar fichas comerciales. Catálogo de lectura existente es destino del enlace de obra. | 3 flujos completos móvil y desktop; ninguno requiere mapa |
| ¿Qué muestra una ciudad sin libros asociados? | Bibliotecas/librerías históricas **si tienen valor cultural propio comprobado**; no inventar relación con novelas. | Relación vacía no impide ficha cultural curada, pero siempre requiere fuentes y originalidad |
| ¿Qué hacemos con lugares ficticios o ambiguos? | **No pin exacto**. Mostrar ambigüedad en obra y zona literaria si tiene sentido; nunca ubicar casa de autor en lugar de trama. | Ejemplos de ficción inventada, topónimo clásico, lugar moderno homónimo |
| ¿Cuándo indexar página de país/región? | Solo si tiene contenido editorial distintivo, lugares suficientes y enlaces reales. **No umbral mágico de 140 caracteres**: eso es validación técnica del preview, NO criterio SEO. | QA de calidad por personas; Search Console después |
| ¿Qué hacemos con fotos y portadas? | Portada de libro se conserva en su ficha actual. Foto de lugar solo con licencia y autor acreditado; en su defecto tarjeta sin imagen o ilustración propia. | Evidencia `images.license/license_url/attribution` y check de formato/CLS |
| ¿API o base de datos en cada visita? | **No**. Dumps/versiones offline → páginas HTML y JSON mínimo, Pagefind existente y mapa diferido. | Red navegador: 0 peticiones a Wikidata/OL/Overture por entrar |
| ¿Cuándo usar un mapa? | Solo si el lector lo pide; lista navegable siempre. Una secuencia literaria NO se presenta como ruta caminable ni promete kilómetros. | Playwright + redes bloqueadas + accesibilidad |
| ¿Dónde entra la IA? | **No necesaria para producción básica**. Puede proponer candidatos cuando el uso legal del texto lo permite, nunca confirmar un dato ni escribir relleno SEO por defecto. | 0 tokens por visita; 100 % de vínculos publicados revisados |
| ¿Cómo se detectan y unen duplicados? | IDs externos y proximidad solo crean **propuestas**, jamás auto-merge. [#679](https://github.com/davidpd89/web-escritor/pull/679). | Métricas falsos positivos con muestra en 3 destinos |
| ¿Cómo se limita coste gratuito? | Descarga por release/país/bbox + caché y batch, no planet dump en CI. P840/P915 en QIDs elegidos ([#678](https://github.com/davidpd89/web-escritor/pull/678)). | Volumen bytes/CPU/solicitudes y cuota del proveedor registrados |
| ¿Cómo evitar que se rompa la búsqueda existente? | **No usar `data-pagefind-body` solo en Atlas**; Pagefind global con `data-pagefind-filter`. Indexar primero los HTML reales. | [#677](https://github.com/davidpd89/web-escritor/pull/677) y regresión de indexación |
| ¿Cómo se publica y se revierte? | Un solo publicador serial con #661 cuando se autorice, primera edición por PR manual, snapshots versionados con SHA y rollback probado. | 0 páginas huérfanas, sitemap/Pagefind coherentes, CI autorizado |
| ¿Cómo se mide éxito? | Métricas SEO de consultas de intención real + scroll/interacción + clic desde Atlas a libros/obras; no total de 78M POIs. | Search Console, Analytics existente, sin rastreo nuevo invasivo |

## Solo cuatro decisiones editoriales que podrían necesitar aprobación humana

1. **Orden de presentación** de las tres puertas: por defecto «Explorar destinos / Buscar libro / Buscar autor»; se puede cambiar según datos reales de búsqueda, sin alterar arquitectura.
2. **Primer conjunto de destinos**: seleccionar piloto geográficamente diverso (mínimo 3 países, obras y lugares confirmados), evitando desplegar sin contenido verificable. Propuesta editorial, **no hay ninguna selección aprobada**.
3. **Frecuencia de actualización**: preferir nuevas fichas con revisión por lotes y fuentes frescas, no «cada día refrescar 78 millones». Proponer semanal o mensual cuando se mida el coste del primer dump.
4. **Fotos y proveedores de mapas**: si faltan derechos o cuota gratis verificable, se publica lista sin imagen/tiles y enlace a OSM. Activar mapas interactivos solo con condiciones de teselas claras.

## Puntos bloqueantes de desarrollo (NO se resuelven con documentación adicional)

- Conectar contrato #669 y extractores a normalizador mundial que pueda tratar **IDs y fuentes heterogéneas**; los pilotos no son ingestores planetarios.
- Implementar revisión Sheets/captura de aprobación real y proyección pública sin `reviewer_note_private`, fotos ni licencias pendientes.
- Reutilizar shell real; emitir HTML y manifest de release que Pagefind, sitemap y content-registry consuman sin listas divergentes.
- Ejecutar por primera vez tests sintéticos, Playwright, Lighthouse, Pa11y, enlaces y presupuestos **cuando el usuario lo autorice**. Nada aquí afirma PASS.
