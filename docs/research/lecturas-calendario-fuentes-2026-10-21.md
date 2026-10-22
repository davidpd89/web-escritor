# Investigación aplicada — catálogo de lecturas, 21/10/2026

> **Estado:** propuesta para revisión, no integrada en el ciclo diario. Esta rama no modifica `main`, el workflow, los feeds, los precios, la web publicada ni la configuración. **No se han ejecutado tests, Actions, builds ni despliegues.** Los archivos de prueba solo quedan preparados.
>
> **PR de referencia:** [#661](https://github.com/davidpd89/web-escritor/pull/661), ya fusionada. Esta PR parte de `main`, no de la rama ya cerrada.

## 1. Estado real examinado y no duplicaciones

Se revisaron las PR [#660](https://github.com/davidpd89/web-escritor/pull/660), [#661](https://github.com/davidpd89/web-escritor/pull/661), [#662](https://github.com/davidpd89/web-escritor/pull/662), [#665](https://github.com/davidpd89/web-escritor/pull/665) y [#676](https://github.com/davidpd89/web-escritor/pull/676), además de los archivos actuales de `main`.

| Función | Estado contrastado | Consecuencia |
|---|---|---|
| Ingesta diaria Penguin 06:30 UTC, hasta 5 altas/80 peticiones | En `reading-catalogue-sync.yml` y configuración, #661 | Conservar un único escritor. |
| Navegación, fichas de autores, paginación de 24, filtros por fecha, recomendaciones | En `build-reading-catalogue.py`, #660/#665 | No reconstruir. |
| Ratings Goodreads/Hardcover/Google Books | Ya separados; piloto 26 ISBN: 15 libros con rating coincidente, Google Books 503, #665 | No prometer cobertura nueva ni sustituir providers. |
| Creators API / precios | Integración preparada, cuenta sin elegibilidad confirmada | No inventar precios ni buscar scraping. |
| Pinterest | Siete RSS integrados y apagados (`rss_enabled=false`), #665; #662 cerrada sin merge | No reabrir rama antigua ni conectar la cuenta. |
| Retoma de lotes y regresiones de publicación | Corregidas en #676, fusionada | No añadir planificador paralelo. |

**Cuello de botella de cobertura:** el snapshot de `data/reading-intake-state.json` examinado en el trabajo anterior contenía 74 ISBN detectados, 25 publicados, 49 pendientes y 44 bloqueados por nombre de sello no reconocido, repartidos en 13 denominaciones. Es un recuento histórico, **no una medición posterior a esta PR**. Recuperar sellos válidos podría mejorar más la cobertura que incorporar una tercera API.

## 2. Entregable A — calendario iCalendar estático, sin registro ni dependencias

Archivos:
- `scripts/reading_release_calendar.py`: generador aislado de calendario agregado y un `.ics` por lanzamiento futuro.
- `tests/test_reading_release_calendar.py`: 11 casos sintéticos **escritos y no ejecutados**.

**Contrato exacto de entrada:** `data/reading-catalogue.json`, exclusivamente libros con `estado="publicado"`, `fecha_publicacion` completa ISO válida y `id`/`slug` validados. No se deriva una fecha a partir de `fecha_publicacion_parcial`, el año, la etiqueta de novedad ni la fecha de detección. No necesita credenciales.

**Contrato de salida:** `assets/reading-calendar/proximos-lanzamientos.ics` y `assets/reading-calendar/<id>.ics` para lanzamientos futuros, **solo cuando se decida integrarlo**. El feed incluye eventos desde 30 días atrás hasta 365 días adelante (valores ajustables) para que no desaparezcan el mismo día; los archivos individuales solo existen antes del lanzamiento. Carpeta recomendada exclusivamente generada: limpia solo archivos ICS antiguos con nombre de libro reconocido y firma PRODID propia; nunca elimina calendarios ajenos en una carpeta elegida por error. Esta PR **no ha generado ni publicado** ningún `.ics` real.

**Compatibilidad RFC 5545 preparada:** `VCALENDAR/VEVENT`, `UID` estable por ID del catálogo, `DTSTAMP` UTC determinista normalizado al día de actualización verificado, `DTSTART;VALUE=DATE`, `DTEND;VALUE=DATE` no inclusivo (+1 día), `TRANSP:TRANSPARENT`, URL a ficha propia, escapes de texto, CRLF y plegado por 75 octetos sin romper UTF-8. Sin alarmas automáticas prometidas: la notificación depende de cada calendario y sus preferencias.

**Uso futuro, explícito, aún no ejecutado:**

```bash
python scripts/reading_release_calendar.py --preview --today 2026-10-21
python scripts/reading_release_calendar.py --out assets/reading-calendar
```

**Integración sugerida después de probar:** llamar al generador en `scripts/refresh-reading-catalogue.py` dentro del **mismo ciclo diario**, después de preparar el catálogo y antes de detectar archivos cambiados; incorporar `assets/reading-calendar/` a `git add` y a la allowlist de `scripts/publish-reading-refresh.py`. El empaquetador `build-public-dist.py` acepta el prefijo `assets/` por diseño, pero hay que confirmar MIME `text/calendar`, accesibilidad HTTP y comportamiento de descarga en el servidor real. Evitar generar HTML o enlaces hasta tener calendario público comprobado. Añadir un enlace "Guardar lanzamiento en mi calendario" solo a libros futuros con archivo generado y un enlace de suscripción en el índice; en móvil verificar que no bloquea ni confunde con el botón Amazon.

**Criterios de aceptación futuros:** importar en Google Calendar, Apple Calendar y Outlook (móvil y escritorio); interpretar evento de día completo en Madrid sin desfases; no crear eventos para fechas parciales; comprobar caracteres con tildes y saltos de línea; confirmar descargas, MIME, UID estable y actualización al cambiar fechas. Un archivo descargado es una **importación puntual**; una URL ICS suscrita puede actualizarse, pero la frecuencia de refresco es del cliente y no equivale a un aviso en tiempo real.

**Fuentes comprobadas:**
- Estándar: https://www.rfc-editor.org/rfc/rfc5545
- Google, calendario público desde URL: https://support.google.com/calendar/answer/37100
- Outlook, diferencias entre importar y suscribirse: https://support.microsoft.com/es-ES/Outlook/import-or-subscribe-to-a-calendar-in-outlook-com-or-outlook-on-the-web
- Alternativa de código [collective/icalendar](https://github.com/collective/icalendar), licencia BSD-2-Clause; [ics-py](https://github.com/ics-py/ics-py), Apache-2.0. **Descartadas para este alcance**: el formato básico con eventos de día completo cabe en Python estándar; añadir dependencia no aporta ventaja demostrada. No se ha copiado código de terceros.

## 3. Entregable B — desbloquear cobertura sin relajar ISBN

Archivos:
- `scripts/reading_publisher_audit.py`: recorre **sin modificar** `reading-intake-state.json`, cuenta ISBN únicos por sello bloqueado, lista ejemplos y presenta hasta tres *candidatos para revisión* utilizando los slugs reales de `data/editoriales.json` resueltos por `reading_intake_publishers.resolve_publishers`.
- `tests/test_reading_publisher_audit.py`: casos sintéticos pendientes de ejecución.

No añade ningún alias ni publica un solo libro: la similitud textual no demuestra identidad de editoriales. El objetivo es crear una cola revisable, priorizada por volumen. Después de comparar denominaciones, grupo editorial, fichas originales, ISBN y la ficha real del sello en nuestro registro, **solo un cambio explícito y revisado** a `publisher_aliases` o al registro canónico puede desbloquear registros. Reusar el validador actual (autor, edición, idioma, fecha, portada y sinopsis); nunca aceptar automáticamente por nombre parecido.

Uso de lectura, **no ejecutado**:

```bash
python scripts/reading_publisher_audit.py
```

Piloto propuesto: revisar primero Penguin Bolsillo (9), DK (7), Aguilar (5) y Debate (4) del snapshot histórico: 25 de los 44 ISBN bloqueados. Recalcular el número actual con el script antes de decidir. Medir ISBN que pasan el validador **por causa**, no solo los que cambian de estado. Conservar los rechazados con motivo explícito.

## 4. Fuente secundaria: Planeta de Libros — oportunidad real, adaptador todavía no justificado

Se ha leído su [página oficial de novedades](https://www.planetadelibros.com/libros-novedades/p/1) y dos fichas de edición el 21/10/2026:

| Edición oficial comprobada | ISBN en ficha | Fecha indicada | Sello |
|---|---|---|---|
| [Una corte de armonía rota — Sarah J. Maas](https://www.planetadelibros.com/libro-una-corte-de-armonia-rota/456755) | 9788408325338 | 28/10/2026 | Crossbooks |
| [Todas las noches, todas las ciudades — Dolores Redondo](https://www.planetadelibros.com/libro-todas-las-noches-todas-las-ciudades/458857) | 9788423370504 | 21/10/2026 | Ediciones Destino |

Las fichas contienen título, autor, fecha, ISBN, sello, presentación, número de páginas, géneros y cubierta. **Esto valida un mínimo de dos ejemplos visibles para extracción HTML, no una API pública, ni robots.txt, ni un conector estable, ni cobertura comparativa.** No se ha verificado un endpoint reutilizable ni la autorización técnica de acceso automatizado; la lectura de robots.txt falló desde la herramienta de investigación. No crear ahora un conector que afirme soporte completo.

**Experimento posterior, acotado a lectura:** comprobar robots.txt, condiciones y límites; tomar 20 fichas distribuidas por géneros y dos páginas de novedades; inspeccionar HTML/JSON-LD y sitemaps reales; extraer solo edición española, ISBN-13 con checksum, fecha exacta, sello y cubierta; conciliar duplicados con el catálogo Penguin. Usar el `CachedHTTP` existente con nuevo host solo después de autorizarlo explícitamente en la configuración, ritmo de 1,5 s y presupuesto global de 80, sin nuevas tareas cron. Medir tasa de fichas completas, cambios del HTML, conflictos de identidad y cantidad de ISBN válidos realmente **nuevos**. Si ≥15/20 fichas completas y al menos 10 ISBN nuevos tras deduplicación, y la fuente permite acceso estable, preparar adaptador específico; si no, buscar un proveedor mejor. Umbrales de **decisión propuestos**, no resultados observados.

Se valorarán también Open Library/Wikidata/BookBrainz para contrastar identificadores, **sin convertirlos automáticamente en fuentes primarias de novedades españolas**: para esta tarea prevalece la fecha y edición comunicadas por el sello.

## 5. UX, captación y SEO — decisiones pequeñas y medibles

**Páginas editoriales seleccionadas, piloto, no código de producción en esta PR.** Proponer solo 3 páginas si hay al menos 6 fichas verificadas por tema, introducción y criterio editorial propios (no relleno): "Próximas novedades de fantasía", "Misterio y thriller de 2026" y "Libros para Halloween". Enlazar cada ficha, sus categorías y próximas fechas; evitar generar una URL por combinación de filtro o un texto repetido por categoría. Medir impresiones, CTR y visitas a fichas con Search Console, si se dispone de datos; no presuponer mejora de tráfico. El índice ya tiene categorías, etiquetas, filtros, Pagefind y SEO: reutilizar su renderizado.

**Series y sagas:** Planeta muestra vínculos y series en algunas fichas, pero el contrato `BOOK_FIELDS` actual no dispone de una entidad saga; no inventar volumen por heurísticas del título. Si se aborda después, exigir identificador estable, orden confirmado, fuentes de cada relación y enlaces solo a libros existentes. Evitar una segunda base de datos de libros.

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
4. Si el `.ics` pasa importaciones, añadirlo al único ciclo de publicación y al render de fichas; ampliar allowlist y verificación del artifact. No crear segundo workflow.
5. Validar piloto Planeta; incorporar solamente si aporta ISBN netos y robustez suficiente.
6. Medir CTR, acceso a fichero y conversiones de ficha cuando exista tráfico; no declarar SEO ni Pinterest ganadores sin analítica.

**Lo que esta PR no afirma:** que las pruebas han pasado, que existe un calendario publicado, que ya hay recordatorios push, que Pinterest publica pines o que Planeta autoriza un crawler. El código está preparado para revisión y necesita integración y QA posterior.


---

## 7. Auditoría final transversal: precios, reseñas, autores, editoriales, SEO y rendimiento (21/10/2026)

**Inventario actualizado de esta PR:** a los cinco archivos iniciales se suman scripts/reading_content_opportunities.py y tests/test_reading_content_opportunities.py, y cambios concretos (sin desplegar) en scripts/reading_amazon_market.py, assets/reading-catalogue.js y tests/test_reading_amazon_market.py. En total, **10 archivos**. No se han ejecutado tests ni builds. El código modificado solo puede entrar en producción tras los controles de la rama y recompilación/versionado del asset JS por el proceso habitual.

### 7.1 Precios Amazon: corrección comprobable, importante para su uso futuro

**Hallazgo:** en el snapshot revisado, el generador de ofertas establecía caducidad de 24 horas (scripts/reading_amazon_market.py) y la UI aceptaba 24 horas (assets/reading-catalogue.js). Las [prácticas oficiales de Creators API](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/concepts/best-programming-practices) indican **TTL de 1 hora para Offers**, frente a un día para otros recursos. No es correcto extender el precio a 24 h por coincidir con la ingesta diaria.

**Cambio ya preparado en esta PR:** expiración de ofertas a +1 h, o antes si vence el descuento; rechazo en el cliente de ofertas de más de 1 h; ajuste del test histórico y caso nuevo. Además, el precio mínimo se acompaña de su **formato** (p. ej. eBook) para no hacerlo pasar por el precio de la edición impresa. No se modifica el consumo de API, los cron ni las credenciales. El CTA existente de Amazon permanece aunque no haya precio válido. Como el ciclo se ejecuta una vez al día, **el precio solo podrá ser visible una hora después de cada actualización válida**: es preferible al dato caducado, pero no es una solución para mostrar ofertas todo el día.

**Revisión pendiente antes del merge:** ejecutar tests/test_reading_amazon_market.py y QA navegador para ofertas con fecha pasada, 1 h, límite exacto y ausencia de credenciales. Inspeccionar la versión del recurso JS en scripts/templates/reading-catalogue.html.tmpl y el HTML generado; actualizar su cache-busting mediante el mecanismo normal del proyecto y regenerar artefactos permitidos en una PR posterior de integración. Comprobar que las políticas de cacheado, declaraciones de precio y derechos asociados a los recursos Amazon siguen vigentes. La documentación de automatización existente habla todavía de TTL 24 h y deberá quedar coherente con el nuevo límite al integrar.

**Otra oportunidad real detectada:** la documentación [Creators API — buenas prácticas](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/concepts/best-programming-practices) avisa de no alterar enlaces proporcionados por la API. El código actual construye un enlace /dp/{ASIN}?tag=... a partir del identificador. Investigar conservación **sin modificar** de detailPageURL cuando la respuesta oficial la devuelva y verificar dominio, ASIN y afiliación; preparar una regresión offline de URI válida, otro host, tag ausente y formatos distintos. No cambiar destinos hasta comprobar el contrato concreto español y sus respuestas reales, porque actualmente la cuenta devuelve falta de elegibilidad. Referencias: [GetItems/cURL oficial](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/get-started/using-curl) y [OffersV2](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/api-reference/resources/offersV2).

**Alternativas de UX A/B:** A: precio con formato y hora de consulta junto al CTA (un precio disponible con TTL estricto). B: CTA estable «Consultar precio en Amazon» cuando no existe dato vigente. B es el comportamiento seguro por defecto y A solo se añade temporalmente cuando hay oferta. No anunciar descuentos del precio de referencia sin fuente válida.

### 7.2 Reseñas y valoraciones: origen atribuido sin estrellas inventadas

**Estado existente:** assets/reading-catalogue.js presenta una puntuación identificada por Google Books, Hardcover o Goodreads, con enlace y total de votos. Las reseñas locales se publican solo tras aprobación; scripts/build-reading-catalogue.py introduce JSON-LD de reseñas propias aprobadas y su AggregateRating individual, **no convierte las valoraciones ajenas en opiniones propias**. Se conservará esta separación.

La [guía oficial de Google de fragmentos de reseñas](https://developers.google.com/search/docs/appearance/structured-data/review-snippet?hl=es) exige que el rating marcado resulte visible, se refiera a la obra específica y advierte expresamente: «No agregues reseñas ni valoraciones de otros sitios web». Por eso no mezclar estrellas de Goodreads/Hardcover/Google Books en un promedio propio ni presentar los números de votos externos como valoraciones de David Porto. La cifra de una plataforma puede abarcar distintas ediciones aunque el ISBN haya servido para encontrar el registro; etiquetar claramente **origen** y **unidad**.

**Mejora UX (especificación, no implementada):** ofrecer «Valoraciones externas» con fuente/hora de consulta y enlaces independientes si coinciden varias, en vez de presentar una sola como la opinión editorial de la web. Las opiniones de lectores propias se mantienen en bloque separado y moderado. Solo usar estrellas en marcado Schema cuando haya reseñas locales auténticas visibles y consentimiento válido; sin falsa calificación agregada. El formulario público sigue fuera de alcance.

### 7.3 Autores: ya hay páginas automáticas; aumentar riqueza sin inventar identidades

**Ya implementado en #661/#665/#676:** update_authors crea y actualiza el registro por nombre, render_author genera URL canónica por autor con todos sus libros, géneros, sellos enlazados, fechas, imágenes y fuentes. enrich_author_bios consulta perfiles oficiales de Penguin con máximo siete intentos por día dentro del mismo presupuesto HTTP, extracto biográfico breve con enlace a la fuente y caducidad de 30 días. author_identity_conflicts bloquea perfiles diferentes con el mismo nombre. No crear duplicados ni otro crawler.

**Hallazgo de calidad:** cuando no hay biografía externa, la ficha muestra un contador y una lista de libros, pero puede aportar poca información original; un nombre sin identidad resuelta NO se debe ampliar automáticamente usando una búsqueda vaga. El informe nuevo scripts/reading_content_opportunities.py ordena precisamente autores del catálogo sin biografía primaria y fichas con una sola obra. Puede orientar la investigación sin alterar las páginas.

**Contrato de enriquecimiento por etapas:**

1. Leer nombre y perfil oficial asociado al ISBN y registrar la URL de la autoridad editorial. Identidad de persona por URL/ID verificado, no por nombre aproximado.
2. Si existe biografía editorial del mismo perfil, guardar 1 extracto corto atribuido, fecha de verificación y fuente. No copiar todo el texto ni completar lagunas con LLM.
3. Fuentes opcionales para **contrastar identidad**: [Open Library Authors API](https://openlibrary.org/dev/docs/api/authors), [Open Library API usage](https://openlibrary.org/developers/api), Wikidata/VIAF/BNE cuando haya identificadores compatibles. La documentación Open Library prohíbe usar su API como backend masivo comercial; cachear, identificar usuario y preferir lotes/dumps cuando proceda. Ninguna búsqueda nominal aislada aporta prueba de coincidencia.
4. Biografía editorial futura: datos confirmados y **distintos** de los metadatos del libro (trayectoria, premios verificables, relación con saga/editorial, obras en la web). Cada afirmación con origen. Si solo hay una ficha y ninguna biografía fiable, mantener un perfil útil para la navegación sin inflarlo con texto repetitivo.
5. Anotar equivalencias de nombres (seudónimos, transliteraciones y coautorías) como candidatos de identidad a revisar. Mantener un único perfil canónico y redirecciones solo cuando haya prueba; preservar URLs. Extender Book.author @id enlazado a Person existente, que ya hace el builder.

No usar ProfilePage de Google indiscriminadamente: su guía limita esta función a perfiles de participantes o creadores asociados al sitio; para escritores externos catalogados, la combinación actual Person + CollectionPage es más prudente y expresa el contenido. [Guía oficial](https://developers.google.com/search/docs/appearance/structured-data/profile-page).

**QA futuro:** homónimos, dos coautores, cambio de nombre editorial, extracto vacío, perfil 404, fuente redirigida, biografía manual protegida, autor con 200 libros y render sin datos de API en el navegador.

### 7.4 Editoriales: catálogo bibliográfico y recepción de manuscritos NO son un único hecho

**Ya implementado:** data/editoriales.json distingue status=open|closed|indirect|award_only|unknown, direct_submission, fuentes, verificación e historial. build-editoriales.py valida fuente primaria, oculta correos en estado closed, advierte tras 90 días y genera páginas estáticas; reading_publisher_links.py lista libros asociados al slug real. NO recrear el directorio. El estado de recepción no debe decidir si un libro del sello se publica.

**Modelo objetivo sin crear una segunda fuente de verdad:** una editorial canónica con dos conjuntos de afirmaciones independientes:

- **Bibliografía y sello**: slug, nombre, grupo, alias oficiales, fuentes de ISBN y publicaciones. Puede surgir del intake y beneficiarse de autopublicación si la identidad está validada y el modelo de datos permite una ficha mínima de catálogo.
- **Recepción de manuscritos**: estado, vía directa/indirecta, requisitos, correo, URLs, fecha, texto o selector de la fuente oficial. No extrapolar de que la editorial publique libros; nunca marcar open/closed solo por la existencia de un formulario o por un sitemap. Para nuevos sellos sin prueba usar unknown (sin CTA «Enviar manuscrito»).

**Flujo de descubrimiento propuesto en el escritor actual**: detecta sello nuevo desde ficha de edición, lo compara con editorial canónica por alias/URL/datos verificables, lo anota en una cola aislada y genera una PR de propuestas **sin mutar el registro**. Para sello ya conocido puede vincular ISBN a slug después de pasar validación. Para nueva editorial aún no aceptada por build-editoriales.py, Claude deberá decidir si admite un subtipo de ficha bibliográfica mínima con status=unknown o si exige completar el expediente. No rellenar requisitos, resumen, historia y fuentes con frases ficticias para superar el validador.

**Autocomprobación de recepción sin falsa certeza**: consultar páginas oficiales ya incluidas en sources, con ETag/Last-Modified si el proveedor lo permite, caché y comparación de contenido relevante; almacenar fecha de último HTTP y fecha **distinta** de confirmación real del estado. Una respuesta 200 o página idéntica no demuestra que el estado siga vigente si la sección de envíos desapareció. Si cambia un párrafo de requisitos o no se puede confirmar, propuesta de revisión y no sobrescribir un estado manual. Si la URL desaparece, aplicar unknown/sin correo activo conforme a la política actual. No añadir un segundo workflow: rotación dentro del presupuesto y del escritor existente.

**Límite de autopublicación razonable:** automatizar *hechos bibliográficos verificados y enlaces derivados*. Estados de manuscritos y contactos activos solo tras confirmación textual desde la web oficial; si es ambiguo, no publicar automáticamente. El informe scripts/reading_content_opportunities.py incluye editoriales que superan 90 días desde la última verificación, sin modificar estados.

### 7.5 SEO: ampliar información útil, no multiplicar URLs sin contenido

Actualmente: fichas Book con ISBN/formato/fecha/publisher, Person por autor, CollectionPage, BreadcrumbList, enlaces internos, sitemap y Pagefind. El [marcado de Book para acciones en Google](https://developers.google.com/search/docs/appearance/structured-data/book) exige registro de interés y participación limitada a proveedores grandes: **no** presentar ese programa especializado como una mejora automática de rich snippets por añadir Book JSON-LD. El JSON-LD existente sirve para describir la página, sin garantizar resultados enriquecidos.

La [política oficial de abuso de contenido a gran escala](https://developers.google.com/search/docs/essentials/spam-policies) desaconseja miles de páginas repetidas que carezcan de utilidad. Objetivo de calidad por URL publicada:
- Cada libro con una edición real y un ISBN/autor/fuente/portada verificados, sin sinopsis ni reseñas inventadas.
- Autor con selección de libros reales del sitio, fuente biográfica cuando existe y enlaces a sello/género; si se queda solo en un contador, priorizar su enriquecimiento editorial en lugar de añadir párrafos mecánicos.
- Editorial con estado y prueba primaria de recepción si se afirma, libros vinculados, fecha de verificación y condiciones.
- Selección temática con explicación propia, libros suficientes, enlaces a fichas, actualización significativa y canonical estable. **No** publicar automáticamente combinaciones de todos los filtros como landing SEO.
- Devolver información útil en HTML estático, no depender de JS para el contenido esencial. Los filtros actuales usan fragmentos #; Google recomienda evitar espacios infinitos de URLs facetadas ([guía](https://developers.google.com/crawling/docs/faceted-navigation)).
- Mantener dateModified/lastmod solo si cambia realmente contenido relevante, no por ejecutar el cron. IndexNow no fuerza indexación. Medir en Search Console a 30–60 días impresiones, clics, CTR, consultas, cobertura y URLs excluidas.

**Prioridad de linking interno**: libro → autor y editorial; autor → libros y sellos; editorial → libros, autores publicados y categorías; selecciones temáticas → libros. No convertir todo en enlaces recíprocos indiscriminados. La parte libro/autores/editoriales ya existe en buena medida; el informe de auditoría señala huecos.

### 7.6 Rendimiento: el riesgo real es el HTML y DOM de un catálogo de miles de tarjetas

La home /recomendaciones/ genera el HTML de **todas** las tarjetas, aunque JS pagine de 24 en 24. Ya se probaron 100/200 títulos en #665, no 5.000. Una futura cobertura masiva crecería en transferencia inicial, DOM, tiempo de parseo y coste de comprobaciones, incluso con servidor estático. No añadir frameworks ni bases de datos por anticipación.

**Puerta para escalar (propuesta, no cifra medida):** un piloto de 500 y 1.000 libros sintéticos sin publicarlos; capturar bytes HTML, elementos DOM, memoria/INP, LCP, CLS, CPU en filtros y tiempos de build/QA; comparar con baseline 200. Objetivos iniciales para revisar: LCP p75 ≤2,5 s, INP p75 ≤200 ms, CLS p75 ≤0,1; son umbrales de Core Web Vitals, **no resultados** ([web.dev](https://web.dev/articles/vitals)). Si el coste aumenta, pasar a hubs HTML estáticos paginados o por categorías con enlaces rastreables y buscar en índice compacto generado durante build; no renderizar miles de portadas ocultas. Conservar Pagefind como búsqueda externa ya existente, sin cargar librerías nuevas. Mantener cubierta principal prioritaria, fuera de pantalla lazy y tamaños definidos.

**Si se usa una única PR automática diaria:** costes de QA y despliegue deben controlarse con lotes chicos y checks por SHA; optimizar en el builder/preprocesado, nunca realizando peticiones a servicios externos desde cada ficha en tiempo de navegación. No tocar el cron actual.

### 7.7 Nueva herramienta de observabilidad offline

scripts/reading_content_opportunities.py y tests/test_reading_content_opportunities.py (sin ejecutar). Consume solo:
- data/reading-catalogue.json;
- data/reading-authors.json;
- data/editoriales.json;
- assets/reading-market.json.

Informe: libros publicados, autores únicos y fichas faltantes, autores con biografía externa ausente, sellos no enlazados, editoriales caducadas 90 días, fechas exactas de próximos 30 días, fechas parciales, ofertas caducadas y ratings separados por proveedor. **No descarga, no inventa, no cambia datos.** Un resultado del informe no justifica publicar una editorial o biografía.

Preflight posterior autorizado:
    python scripts/reading_content_opportunities.py --today 2026-10-21
    python -m unittest discover -s tests -p 'test_reading*.py' -v

En este encargo **no se han ejecutado esos comandos**.

## 8. Plan de integración ordenado para Claude — sin otra arquitectura

1. **Revisar el diff exacto de esta PR** frente al SHA actual de main y la PR de lote automático #682; evitar tocar los mismos artefactos que esté publicando el bot. Resolver primero cualquier desfase de base.
2. **Revisar estáticamente los cambios y los contratos**: iCalendar (UID/escape/folding/fechas), informe editorial (no aprobaciones), auditoría cruzada (lectura solamente), 1 h OffersV2 (Python+JS) y etiquetas de formato. Marcar errores sin ejecutar tests si sigue vigente la prohibición del usuario.
3. **Cuando se autorice:** correr pruebas acotadas en checkout aislado y QA de navegador. Regenerar/versionar reading-catalogue.js mediante el pipeline oficial; no editar cientos de HTML directamente a mano.
4. **Integrar calendario** en el único refresh-reading-catalogue.py; añadir su carpeta de salida a rutas de staging y a la allowlist de publicación, así como los checks de compilación y de HTTP/MIME (el directorio assets ya es público bajo la allowlist de dist). Asegurar que la existencia de un lanzamiento futuro no dispara un merge automático si no hay diferencias de archivos.
5. **Verificar fuentes/identidades de autores** desde el dato editorial antes de añadir nuevas biografías. Convertir homónimos en propuestas, no merges automáticos. Mantener perfiles manuales como autoridad.
6. **Mejorar editoriales** con una cola de candidatos de sellos nuevos y una rotación de comprobaciones oficiales; separar catalogación bibliográfica de admisión de originales. Mantener la política de unknown y ocultación de contactos no confirmados.
7. **Poner límites de cobertura/SEO/performance** antes de escalar más allá de 200 libros, contrastar Search Console y métricas de campo; priorizar datos y enlaces únicos sobre páginas paramétricas duplicadas.
8. **No lanzar acciones** sin autorización: ningún CI, prueba, push al main, despliegue, nueva tarea programada, activación de Pinterest o compra externa forma parte de este trabajo.

**Veredicto:** lo más útil ahora es recuperar sellos legítimos, añadir biografías con procedencia y un calendario exportable, manteniendo el único escritor diario. Los precios han recibido una corrección concreta para no ofrecer datos obsoletos; el crecimiento de páginas y la fuente Planeta requieren pilotos medidos. No se promete rentabilidad SEO ni cobertura exhaustiva.


---

## 9. Actualización decisiva: sustitución de Creators API y cláusula de no comparación (21/10/2026)

La investigación adicional ha comprobado que **Amazon.es prohíbe presentar una comparación de precios de tiendas ajenas con un enlace afiliado si no se puede mostrar también el precio Amazon autorizado**. No se puede solucionar simplemente con scraping, bots, Drive o un agente de ChatGPT. Referencia oficial: https://afiliados.amazon.es/help/operating/linking.

**Decisión de arquitectura:** dos modos **excluyentes**, controlados por `purchase_price_mode`: `amazon_affiliate` (estado por defecto, sin importe de otra tienda) y `publisher_only` (sin enlace afiliado Amazon en el HTML, se utiliza precio procedente del proveedor/editorial al que dirige la compra). No confundir importes entre proveedores. Google Books `saleInfo` permite únicamente eBooks exactos comercializados en España; una consulta de rating por ISBN de tapa dura no implica precio de ebook. Penguin tiene precios visibles en la ficha oficial, pero extraer el campo del HTML crudo, las condiciones y la cobertura siguen **pendientes de piloto**.

**Código adicional:** `scripts/reading_free_prices.py`, `tests/test_reading_free_prices.py`, `tests/test_reading_price_mode.py`, `assets/reading-free-prices.json` vacío, configuración de encendido separado, escritores y allowlist ampliados, modo de render en `scripts/build-reading-catalogue.py`, compatibilidad de filtro y precio en `assets/reading-catalogue.js`. La funcionalidad está **desactivada** en la configuración hasta verificación y QA. `amazon_price_refresh.enabled=false` evita gasto inútil de peticiones de una cuenta sin elegibilidad.

**Análisis completo con matrices de alternativas, fuentes, contratos, comandos y procedimiento de activación:** [Precios sin Creators API y catálogo](precios-sin-creators-y-catalogo-2026-10-21.md).

**Ajuste del plan de implementación anterior:** las propuestas de mostrar el importe editorial junto a un CTA afiliado Amazon quedan expresamente **descartadas**. La mejora de 1 h de TTL de Amazon queda solo como salvaguarda futura de la API cuando sea elegible; no desbloquea precios actuales. La nueva solución gratuita y viable (condicionada al acceso editorial) no depende de ventas, pero tampoco promete cobertura del 100 % ni un precio Amazon disfrazado.
