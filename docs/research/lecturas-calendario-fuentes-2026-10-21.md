# Investigación aplicada — catálogo de lecturas, 21/10/2026

> **Estado:** propuesta para revisión, no integrada en el ciclo diario. Esta rama no modifica \`main\`, el workflow, los feeds, los precios, la web publicada ni la configuración. **No se han ejecutado tests, Actions, builds ni despliegues.** Los archivos de prueba solo quedan preparados.
>
> **PR de referencia:** [#661](https://github.com/davidpd89/web-escritor/pull/661), ya fusionada. Esta PR parte de \`main\`, no de la rama ya cerrada.

## 1. Estado real examinado y no duplicaciones

Se revisaron las PR [#660](https://github.com/davidpd89/web-escritor/pull/660), [#661](https://github.com/davidpd89/web-escritor/pull/661), [#662](https://github.com/davidpd89/web-escritor/pull/662), [#665](https://github.com/davidpd89/web-escritor/pull/665) y [#676](https://github.com/davidpd89/web-escritor/pull/676), además de los archivos actuales de \`main\`.

| Función | Estado contrastado | Consecuencia |
|---|---|---|
| Ingesta diaria Penguin 06:30 UTC, hasta 5 altas/80 peticiones | En \`reading-catalogue-sync.yml\` y configuración, #661 | Conservar un único escritor. |
| Navegación, fichas de autores, paginación de 24, filtros por fecha, recomendaciones | En \`build-reading-catalogue.py\`, #660/#665 | No reconstruir. |
| Ratings Goodreads/Hardcover/Google Books | Ya separados; piloto 26 ISBN: 15 libros con rating coincidente, Google Books 503, #665 | No prometer cobertura nueva ni sustituir providers. |
| Creators API / precios | Integración preparada, cuenta sin elegibilidad confirmada | No inventar precios ni buscar scraping. |
| Pinterest | Siete RSS integrados y apagados (\`rss_enabled=false\`), #665; #662 cerrada sin merge | No reabrir rama antigua ni conectar la cuenta. |
| Retoma de lotes y regresiones de publicación | Corregidas en #676, fusionada | No añadir planificador paralelo. |

**Cuello de botella de cobertura:** el snapshot de \`data/reading-intake-state.json\` examinado en el trabajo anterior contenía 74 ISBN detectados, 25 publicados, 49 pendientes y 44 bloqueados por nombre de sello no reconocido, repartidos en 13 denominaciones. Es un recuento histórico, **no una medición posterior a esta PR**. Recuperar sellos válidos podría mejorar más la cobertura que incorporar una tercera API.

## 2. Entregable A — calendario iCalendar estático, sin registro ni dependencias

Archivos:
- \`scripts/reading_release_calendar.py\`: generador aislado de calendario agregado y un \`.ics\` por lanzamiento futuro.
- \`tests/test_reading_release_calendar.py\`: 11 casos sintéticos **escritos y no ejecutados**.

**Contrato exacto de entrada:** \`data/reading-catalogue.json\`, exclusivamente libros con \`estado="publicado"\`, \`fecha_publicacion\` completa ISO válida y \`id\`/\`slug\` validados. No se deriva una fecha a partir de \`fecha_publicacion_parcial\`, el año, la etiqueta de novedad ni la fecha de detección. No necesita credenciales.

**Contrato de salida:** \`assets/reading-calendar/proximos-lanzamientos.ics\` y \`assets/reading-calendar/<id>.ics\` para lanzamientos futuros, **solo cuando se decida integrarlo**. El feed incluye eventos desde 30 días atrás hasta 365 días adelante (valores ajustables) para que no desaparezcan el mismo día; los archivos individuales solo existen antes del lanzamiento. Carpeta exclusivamente generada: limpia únicamente \`*.ics\` antiguos dentro de esa carpeta al escribir. Esta PR **no ha generado ni publicado** ningún \`.ics\` real.

**Compatibilidad RFC 5545 preparada:** \`VCALENDAR/VEVENT\`, \`UID\` estable por ID del catálogo, \`DTSTAMP\` UTC determinista normalizado al día de actualización verificado, \`DTSTART;VALUE=DATE\`, \`DTEND;VALUE=DATE\` no inclusivo (+1 día), \`TRANSP:TRANSPARENT\`, URL a ficha propia, escapes de texto, CRLF y plegado por 75 octetos sin romper UTF-8. Sin alarmas automáticas prometidas: la notificación depende de cada calendario y sus preferencias.

**Uso futuro, explícito, aún no ejecutado:**

\`\`\`bash
python scripts/reading_release_calendar.py --preview --today 2026-10-21
python scripts/reading_release_calendar.py --out assets/reading-calendar
\`\`\`

**Integración sugerida después de probar:** llamar al generador en \`scripts/refresh-reading-catalogue.py\` dentro del **mismo ciclo diario**, después de preparar el catálogo y antes de detectar archivos cambiados; incorporar \`assets/reading-calendar/\` a \`git add\` y a la allowlist de \`scripts/publish-reading-refresh.py\`. El empaquetador \`build-public-dist.py\` acepta el prefijo \`assets/\` por diseño, pero hay que confirmar MIME \`text/calendar\`, accesibilidad HTTP y comportamiento de descarga en el servidor real. Evitar generar HTML o enlaces hasta tener calendario público comprobado. Añadir un enlace "Guardar lanzamiento en mi calendario" solo a libros futuros con archivo generado y un enlace de suscripción en el índice; en móvil verificar que no bloquea ni confunde con el botón Amazon.

**Criterios de aceptación futuros:** importar en Google Calendar, Apple Calendar y Outlook (móvil y escritorio); interpretar evento de día completo en Madrid sin desfases; no crear eventos para fechas parciales; comprobar caracteres con tildes y saltos de línea; confirmar descargas, MIME, UID estable y actualización al cambiar fechas. Un archivo descargado es una **importación puntual**; una URL ICS suscrita puede actualizarse, pero la frecuencia de refresco es del cliente y no equivale a un aviso en tiempo real.

**Fuentes comprobadas:**
- Estándar: https://www.rfc-editor.org/rfc/rfc5545
- Google, calendario público desde URL: https://support.google.com/calendar/answer/37100
- Outlook, diferencias entre importar y suscribirse: https://support.microsoft.com/es-ES/Outlook/import-or-subscribe-to-a-calendar-in-outlook-com-or-outlook-on-the-web
- Alternativa de código [collective/icalendar](https://github.com/collective/icalendar), licencia BSD-2-Clause; [ics-py](https://github.com/ics-py/ics-py), Apache-2.0. **Descartadas para este alcance**: el formato básico con eventos de día completo cabe en Python estándar; añadir dependencia no aporta ventaja demostrada. No se ha copiado código de terceros.

## 3. Entregable B — desbloquear cobertura sin relajar ISBN

Archivos:
- \`scripts/reading_publisher_audit.py\`: recorre **sin modificar** \`reading-intake-state.json\`, cuenta ISBN únicos por sello bloqueado, lista ejemplos y presenta hasta tres *candidatos para revisión* utilizando los slugs reales de \`data/editoriales.json\` resueltos por \`reading_intake_publishers.resolve_publishers\`.
- \`tests/test_reading_publisher_audit.py\`: casos sintéticos pendientes de ejecución.

No añade ningún alias ni publica un solo libro: la similitud textual no demuestra identidad de editoriales. El objetivo es crear una cola revisable, priorizada por volumen. Después de comparar denominaciones, grupo editorial, fichas originales, ISBN y la ficha real del sello en nuestro registro, **solo un cambio explícito y revisado** a \`publisher_aliases\` o al registro canónico puede desbloquear registros. Reusar el validador actual (autor, edición, idioma, fecha, portada y sinopsis); nunca aceptar automáticamente por nombre parecido.

Uso de lectura, **no ejecutado**:

\`\`\`bash
python scripts/reading_publisher_audit.py
\`\`\`

Piloto propuesto: revisar primero Penguin Bolsillo (9), DK (7), Aguilar (5) y Debate (4) del snapshot histórico: 25 de los 44 ISBN bloqueados. Recalcular el número actual con el script antes de decidir. Medir ISBN que pasan el validador **por causa**, no solo los que cambian de estado. Conservar los rechazados con motivo explícito.

## 4. Fuente secundaria: Planeta de Libros — oportunidad real, adaptador todavía no justificado

Se ha leído su [página oficial de novedades](https://www.planetadelibros.com/libros-novedades/p/1) y dos fichas de edición el 21/10/2026:

| Edición oficial comprobada | ISBN en ficha | Fecha indicada | Sello |
|---|---|---|---|
| [Una corte de armonía rota — Sarah J. Maas](https://www.planetadelibros.com/libro-una-corte-de-armonia-rota/456755) | 9788408325338 | 28/10/2026 | Crossbooks |
| [Todas las noches, todas las ciudades — Dolores Redondo](https://www.planetadelibros.com/libro-todas-las-noches-todas-las-ciudades/458857) | 9788423370504 | 21/10/2026 | Ediciones Destino |

Las fichas contienen título, autor, fecha, ISBN, sello, presentación, número de páginas, géneros y cubierta. **Esto valida un mínimo de dos ejemplos visibles para extracción HTML, no una API pública, ni robots.txt, ni un conector estable, ni cobertura comparativa.** No se ha verificado un endpoint reutilizable ni la autorización técnica de acceso automatizado; la lectura de robots.txt falló desde la herramienta de investigación. No crear ahora un conector que afirme soporte completo.

**Experimento posterior, acotado a lectura:** comprobar robots.txt, condiciones y límites; tomar 20 fichas distribuidas por géneros y dos páginas de novedades; inspeccionar HTML/JSON-LD y sitemaps reales; extraer solo edición española, ISBN-13 con checksum, fecha exacta, sello y cubierta; conciliar duplicados con el catálogo Penguin. Usar el \`CachedHTTP\` existente con nuevo host solo después de autorizarlo explícitamente en la configuración, ritmo de 1,5 s y presupuesto global de 80, sin nuevas tareas cron. Medir tasa de fichas completas, cambios del HTML, conflictos de identidad y cantidad de ISBN válidos realmente **nuevos**. Si ≥15/20 fichas completas y al menos 10 ISBN nuevos tras deduplicación, y la fuente permite acceso estable, preparar adaptador específico; si no, buscar un proveedor mejor. Umbrales de **decisión propuestos**, no resultados observados.

Se valorarán también Open Library/Wikidata/BookBrainz para contrastar identificadores, **sin convertirlos automáticamente en fuentes primarias de novedades españolas**: para esta tarea prevalece la fecha y edición comunicadas por el sello.

## 5. UX, captación y SEO — decisiones pequeñas y medibles

**Páginas editoriales seleccionadas, piloto, no código de producción en esta PR.** Proponer solo 3 páginas si hay al menos 6 fichas verificadas por tema, introducción y criterio editorial propios (no relleno): "Próximas novedades de fantasía", "Misterio y thriller de 2026" y "Libros para Halloween". Enlazar cada ficha, sus categorías y próximas fechas; evitar generar una URL por combinación de filtro o un texto repetido por categoría. Medir impresiones, CTR y visitas a fichas con Search Console, si se dispone de datos; no presuponer mejora de tráfico. El índice ya tiene categorías, etiquetas, filtros, Pagefind y SEO: reutilizar su renderizado.

**Series y sagas:** Planeta muestra vínculos y series en algunas fichas, pero el contrato \`BOOK_FIELDS\` actual no dispone de una entidad saga; no inventar volumen por heurísticas del título. Si se aborda después, exigir identificador estable, orden confirmado, fuentes de cada relación y enlaces solo a libros existentes. Evitar una segunda base de datos de libros.

**Pinterest:** la [documentación oficial](https://help.pinterest.com/es/business/article/auto-publish-pins-from-your-rss-feed) confirma RSS 2.0 e imagen, enlace al dominio reclamado y publicación después de conectar la cuenta. Los siete feeds actuales están desactivados, con piloto limitado. Conservarlos: no reintroducir API, scraping, Chrome automatizado ni duplicar pines; medir en futuro clicks reales desde UTM, no estimarlos.

**SEO:** Google pide utilidad original y advierte contra páginas escaladas con textos repetidos: https://developers.google.com/search/docs/fundamentals/creating-helpful-content y https://developers.google.com/search/docs/essentials/spam-policies. Priorizar fichas bibliográficamente fiables y selección humana sobre miles de landing pages vacías.

## 6. Priorización y pasos para Claude/Codex

| Prioridad | Propuesta | Evidencia / criterio | Estado |
|---|---|---|---|
| Alta | Conciliación editorial | Bloqueo verificable en estado histórico; auditoría reproducible, sin cambios de datos | Código de informe y tests **sin ejecutar** |
| Alta | Calendario estático | RFC 5545 y soporte importación/suscripción; coste nulo sin cuentas | Generador y tests **sin ejecutar** |
| Media | Fuente Planeta | Dos ISBN/ediciones visibles, falta prueba sistemática y robots | Piloto especificado; **sin conector** |
| Media | Páginas SEO curadas | Se apoyan en catálogo existente; beneficio de tráfico no demostrado | Piloto condicionado a ≥6 fichas |
| Baja | Modelo de sagas | Metadatos del proveedor pueden aportar relaciones, pero falta contrato propio | Investigar cuando haya cobertura |
| Descartada | Nuevo cron/API Pinterest, duplicar filtros y quiz, nuevo proveedor de precio por scraping | Funciones ya presentes o coste/riesgo sin ganancia concreta | No hacer |

**Orden sugerido de revisión:**
1. Claude revisa estáticamente ambos scripts, fuentes, fechas, Unicode, salidas y las pruebas. **Todavía no se ejecuta nada.**
2. Con autorización para validar más adelante: ejecutar solo suites acotadas de los nuevos tests, revisar resultados y reparar discrepancias.
3. Revisar manualmente la cola actual de sellos; registrar y probar alias validados sin desactivar las salvaguardas.
4. Si el \`.ics\` pasa importaciones, añadirlo al único ciclo de publicación y al render de fichas; ampliar allowlist y verificación del artifact. No crear segundo workflow.
5. Validar piloto Planeta; incorporar solamente si aporta ISBN netos y robustez suficiente.
6. Medir CTR, acceso a fichero y conversiones de ficha cuando exista tráfico; no declarar SEO ni Pinterest ganadores sin analítica.

**Lo que esta PR no afirma:** que las pruebas han pasado, que existe un calendario publicado, que ya hay recordatorios push, que Pinterest publica pines o que Planeta autoriza un crawler. El código está preparado para revisión y necesita integración y QA posterior.
