# Autoridad final — 108 ideas de mejora web

**Corte de verificación:** 2026-08-28  
**Base auditada:** `main@c70852eeaac9fcdc0e73811687e62ab731f352a9`  
**Origen:** investigación histórica de PR #135, recuperada del HEAD `8e72321d047c0445c5ac411ebe242af8a0386929` y revalidada contra el repositorio y fuentes primarias vigentes.

Esta es la autoridad activa. Las pasadas intermedias de PR #135 son historia de investigación, no backlog. Una idea solo se implementa cuando su estado y su gate lo permiten.

## Estados

- `IMPLEMENT_NOW`: mejora demostrada, bajo riesgo y con encaje actual.
- `IMPLEMENT_AFTER_CURRENT_DEBT`: válida, pero debe ir después de deuda técnica/QA activa.
- `ALREADY_COVERED`: ya existe sustancialmente; mantener/auditar, no duplicar.
- `PARTIAL_AUDIT`: hay base pero falta medición o cierre concreto.
- `CONDITIONAL`: solo si se activa el trigger indicado.
- `EXTERNAL_OPERATION`: acción en servicio externo; requiere acceso/autorización y evidencia live.
- `DEFER`: potencial futuro, no compensa ahora.
- `REJECT`: no aporta suficiente valor, contradice evidencia o añade complejidad/riesgo.

Las claves `[S-*]` remiten a `02-PRIMARY-SOURCES-2026-08-28.md`.

## A · SEO técnico y contenido clásico

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| A.1 | ALREADY_COVERED | Ya existen hubs/colecciones/territorios; no imponer una receta artificial de “pillar cluster”. | Medir con GSC/Bing antes de crear nuevas páginas. |
| A.2 | ALREADY_COVERED | Samuel, Manecillas y Noveris ya tienen hubs canónicos. | Reforzar enlaces solo cuando falte una ruta real. |
| A.3 | ALREADY_COVERED | Existe `scripts/check-internal-graph.py` y QA de discoverability. | Mantener como contrato. |
| A.4 | IMPLEMENT_AFTER_CURRENT_DEBT | La revisión editorial periódica sí reduce contenido obsoleto; la fecha visible no debe falsificarse. | Añadir `reviewBy`/`reviewCadence` al registry; cambiar fecha pública solo tras cambio sustantivo. |
| A.5 | CONDITIONAL | Enlaces externos son útiles para evidencia/usuario, pero Google no documenta “outbound authority” como boost E-E-A-T. | Enlazar solo la fuente que sustenta una afirmación. |
| A.6 | PARTIAL_AUDIT | Google sigue soportando `BreadcrumbList` en desktop; hay breadcrumbs ya implantados en varias familias. [S-GOOGLE-BREADCRUMB] | Auditoría de cobertura + visible/schema parity; no duplicar. |
| A.7 | REJECT | `FAQPage` no es una oportunidad general de rich result para una web de autor; no añadir schema por ocupar SERP. [S-GOOGLE-FAQ] | FAQ visible solo si responde preguntas reales; sin promesa de rich result. |
| A.8 | REJECT | Dos libros no relacionados no justifican una página “orden de lectura”. | Reabrir solo si existe saga/orden real. |
| A.9 | ALREADY_COVERED | Canonicals ya tienen contratos y Search Console fue revisado; Google trata canonical como preferencia, no orden absoluta. [S-GOOGLE-CANONICAL] | Mantener auditoría y URL Inspection ante discrepancias. |
| A.10 | ALREADY_COVERED | Existe `404.html`. | Mejorar solo si datos muestran salidas útiles ausentes. |
| A.11 | CONDITIONAL | Image/video sitemaps ayudan sobre todo a media difícil de descubrir. [S-GOOGLE-IMAGE-SITEMAP] [S-GOOGLE-VIDEO-SITEMAP] | Añadir solo si auditoría detecta media importante no descubierta. |
| A.12 | REJECT | Google prohíbe agregar ratings/reviews de otros sitios; ya se corrigió el riesgo Amazon. [S-GOOGLE-REVIEWS] | Solo markup de reviews realmente capturadas/visibles en este sitio y legítimas. |

## B · IA / GEO / answer engines

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| B.1 | ALREADY_COVERED | `llms.txt` ya enlaza identidad, obras, Cuaderno, herramientas, recomendaciones, directorios, clubes, eventos y press-kit. | Mantener factual; no venderlo como ranking signal. |
| B.2 | ALREADY_COVERED | `robots.txt` ya separa OAI-SearchBot/ChatGPT-User/GPTBot, Perplexity, Claude Search/User/Bot, Applebot-Extended y Google-Extended. | Revalidación trimestral de tokens oficiales. |
| B.3 | CONDITIONAL | Respuesta directa mejora claridad cuando encaja, pero no existe formato secreto de GEO. | Usar solo en preguntas reales; no reescribir todo el Cuaderno. |
| B.4 | ALREADY_COVERED | Person/Book/Article y `sameAs` ya forman parte de la arquitectura de entidad. | Mantener paridad con hechos canónicos. |
| B.5 | ALREADY_COVERED | El corpus AI-discoverability ya define benchmark/controles negativos. | Ejecutar benchmark con cadencia, no “buscarse” manualmente sin metodología. |
| B.6 | EXTERNAL_OPERATION | Bing AI Performance muestra citas, grounding queries y páginas citadas; es señal directa de observabilidad, no ranking. [S-BING-AI-PERFORMANCE] | Configurar/auditar Bing Webmaster Tools si no está ya live; guardar baseline. |
| B.7 | IMPLEMENT_AFTER_CURRENT_DEBT | IndexNow aporta frescura para URLs cambiadas; 200/202 no garantizan indexación. [S-INDEXNOW] | Script post-deploy, solo URLs públicas realmente cambiadas; log de submission. |
| B.8 | CONDITIONAL | TL;DR puede ayudar lectura/extracción, pero también añadir ruido y duplicación. | Pilotar en 2–3 piezas largas con medición. |
| B.9 | CONDITIONAL | Glosario de Noveris/Samuel puede ser contenido canónico útil si evita spoilers y duplicación. | Crear solo desde canon verificado y con demanda editorial. |

## C · Estrategia editorial

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| C.1 | ALREADY_COVERED | El lanzamiento de Manecillas ya tiene gate/plan editorial. | Ejecutar la transición prevista, no crear otro calendario paralelo. |
| C.2 | CONDITIONAL | “Detrás del libro” es first-party único y difícil de replicar. | Priorizar piezas con experiencia/documentación real, no contenido promocional genérico. |
| C.3 | IMPLEMENT_AFTER_CURRENT_DEBT | Preguntas reales de lectores validan demanda. | Recogerlas sin PII y mapearlas a contenido existente antes de crear URL. |
| C.4 | CONDITIONAL | Fragmentos imprimibles aportan valor si los derechos lo permiten. | Gate de derechos + canonical/noindex según formato. |
| C.5 | REJECT | Generar páginas long-tail por subgénero/edad puede convertirse en scaled/doorway content. [S-GOOGLE-SPAM] | Solo nueva página con intención distinta y contenido original suficiente. |
| C.6 | REJECT | Intercambio de reseñas/enlaces orientado a SEO crea incentivos incompatibles con autoridad auténtica. | Colaboraciones editoriales sí; quid-pro-quo de ranking no. |
| C.7 | CONDITIONAL | Mapa/línea temporal solo merece coste si es asset editorial verdadero. | Diseñar tras contenido canónico, no como decoración SEO. |
| C.8 | PARTIAL_AUDIT | `empieza-aqui/` ya existe. | Auditar rutas por intención real y simplificar; no duplicar hub. |
| C.9 | DEFER | No hay necesidad actual de prometer traducciones. | Reabrir con proyecto/derechos/idioma concreto. |
| C.10 | IMPLEMENT_AFTER_CURRENT_DEBT | Archivo cronológico de prensa mejora verificabilidad y reutilización. | Modelar fuente, fecha, tipo, URL y extracto permitido; no inventar menciones. |

## D · UX / interacción

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| D.1 | CONDITIONAL | Feedback de acciones sí; animación decorativa no. | Aplicar a estados reales (suscripción/copiar/etc.) con reduced-motion. |
| D.2 | REJECT | Un reader-mode propio duplica navegador y añade estado/QA. | Mejorar tipografía/medida de lectura de la página normal. |
| D.3 | PARTIAL_AUDIT | Progreso puede ayudar en piezas largas, pero añade JS/ruido. | Pilotar solo si métricas/entrevistas muestran necesidad. |
| D.4 | CONDITIONAL | “Leer después” local puede ser útil sin cuenta. | Solo contenido no sensible; export/clear y accesibilidad. |
| D.5 | ALREADY_COVERED | El repo genera Pagefind (`scripts/build-pagefind-index.py`). | Mejorar tuning/filtros con queries reales antes de buscar embeddings. |
| D.6 | REJECT | Con dos obras, un quiz general de recomendación es una capa artificial. | Reabrir con catálogo suficiente. |
| D.7 | REJECT | Hover preview es desktop-only y aumenta complejidad sin necesidad demostrada. | Mejorar cards/listados accesibles si hay problema de descubrimiento. |
| D.8 | DEFER | Toggle dark añade estado, contrastes y QA transversal. | Reabrir con demanda de usuarios; `prefers-color-scheme` primero. |
| D.9 | CONDITIONAL | Tiempo de lectura es barato si el contenido lo necesita. | Calcular en build y no mostrar en páginas donde no aporta. |
| D.10 | REJECT | Botón flotante al seleccionar texto es intrusivo y complejo en touch/a11y. | Compartir página/cita editorial preparada cuando tenga sentido. |
| D.11 | IMPLEMENT_AFTER_CURRENT_DEBT | Estados vacíos son UX real y medible. | Inventario de search/assistant/forms/club + copy de recuperación. |
| D.12 | CONDITIONAL | Siguiente/anterior funciona en series reales. | Derivar del registry; nunca mantener orden manual duplicado. |

## E · Rendimiento / Core Web Vitals

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| E.1 | PARTIAL_AUDIT | AVIF puede reducir bytes, pero el repo ya tiene WebP/AVIF en parte y cambiar todo sin medir genera trabajo inútil. | Inventario por peso/LCP; convertir solo candidatos rentables. |
| E.2 | IMPLEMENT_AFTER_CURRENT_DEBT | INP es CWV estable; evaluar p75 de campo cuando exista muestra. [S-WEBDEV-INP] | CrUX/field primero, profiler después. |
| E.3 | CONDITIONAL | `fetchpriority=high` solo para recurso realmente crítico; abuso compite con otros recursos. | Confirmar LCP por plantilla antes de añadirlo. |
| E.4 | CONDITIONAL | Preload de fuente solo si trace muestra mejora; exceso perjudica. | Auditar fuentes críticas y caché. |
| E.5 | IMPLEMENT_AFTER_CURRENT_DEBT | Un budget evita crecimiento silencioso, pero debe nacer del baseline real. | Registrar bytes actuales + margen; empezar warning y endurecer después. |
| E.6 | PARTIAL_AUDIT | El problema video/Range/PWA ya fue corregido; optimizaciones adicionales requieren trace. | No tocar salvo evidencia de LCP/CPU/network. |
| E.7 | PARTIAL_AUDIT | **No inferir compresión por DNS/proxy.** Debe observarse `Content-Encoding` live por tipo de recurso. | Smoke HTTP de HTML/CSS/JS con `Accept-Encoding`; documentar origen/CDN observado. |
| E.8 | IMPLEMENT_NOW | Terceros pueden afectar LCP/INP/privacidad y ya existen GoatCounter/Metricool/Turnstile/Brevo. | Medir waterfall/long tasks; conservar solo scripts con valor y estrategia de carga adecuada. |

## F · Accesibilidad

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| F.1 | IMPLEMENT_NOW | WCAG 2.5.8 AA exige 24 CSS px con excepciones; el proyecto mantiene contrato visual propio de 42 px en controles principales. [S-WCAG22] | Auditor sitewide + no rebajar contrato 42→24 donde ya fue deliberado. |
| F.2 | IMPLEMENT_NOW | WCAG exige resize 200% y text spacing; `zoom:2` no equivale a `font-size:200%`. [S-WCAG22] | QA browser separado con font-size 200% + text-spacing real. |
| F.3 | CONDITIONAL | Transcripción necesaria si hay contenido audiovisual con información hablada. | Añadir junto al media, no como deuda posterior. |
| F.4 | IMPLEMENT_AFTER_CURRENT_DEBT | Foco visible/no oculto es contrato funcional. | Auditor teclado por familias y modales; automatización + manual. |
| F.5 | REJECT | Un “modo texto grande” propio duplica resize del navegador y aumenta estados. | Hacer que el sitio soporte correctamente zoom/text-size nativo. |
| F.6 | PARTIAL_AUDIT | El asistente tiene semántica propia; necesita prueba de lector de pantalla/announcements. | NVDA/VoiceOver + roles/live regions + foco del diálogo. |

## G · IA / personalización

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| G.1 | PARTIAL_AUDIT | Recomendación conversacional encaja solo si está anclada a catálogo/canon. | Negative tests + respuestas “no sé/no encaja”; no recomendar por instrucción oculta. |
| G.2 | CONDITIONAL | IA puede acelerar borradores de club, nunca ser autoridad factual. | Human review obligatoria y fuentes/canon. |
| G.3 | CONDITIONAL | Alt asistido puede ahorrar trabajo, pero el contexto/función de imagen requieren humano. | Tooling de borrador, nunca auto-commit. |
| G.4 | REJECT | Metadatos en inglés sin páginas inglesas reales crean incoherencia. | Traducir cuando exista página localizada real. |
| G.5 | DEFER | Registrar preguntas del asistente añade tratamiento de datos/retención. | Solo con hipótesis, minimización, política y consentimiento/base legal aplicable. |

## H · Brevo / newsletter

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| H.1 | IMPLEMENT_AFTER_CURRENT_DEBT | Preferencias por interés son valiosas; Consent Groups existen pero solo cuando feature/plan lo permite; Professional/Enterprise según ayuda actual. [S-BREVO-CONSENT] | Baseline con listas/segmentos; no subir de plan solo por esta feature. |
| H.2 | IMPLEMENT_AFTER_CURRENT_DEBT | Welcome series tiene sentido después de verificar DOI, routing y entrega real. | E2E primero; luego 2–4 mensajes con reentrada/exclusiones claras. |
| H.3 | CONDITIONAL | Contenido exclusivo puede ser incentivo si hay derechos y valor real. | Definir derecho/cadencia antes del funnel. |
| H.4 | DEFER | Win-back necesita volumen e historial; hoy sería sobreoptimización. | Trigger por tamaño/engagement suficiente. |
| H.5 | DEFER | A/B necesita muestra útil; no hacer estadística ficticia con lista pequeña. | Reabrir con audiencia suficiente y métrica primaria. |
| H.6 | CONDITIONAL | Reenvío/compartir es barato pero debe respetar tracking/UTM y diseño email. | Pilotar cuando exista cadencia estable. |

## I · Analítica / privacidad

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| I.1 | REJECT | Dashboard público de tráfico no mejora el producto y crea mantenimiento/divulgación innecesarios. | Métricas internas. |
| I.2 | IMPLEMENT_NOW | Hay varios terceros; hay que documentar qué datos/envíos/consentimiento implica cada uno. | Matriz live de GoatCounter/Metricool/Turnstile/Brevo y política. |
| I.3 | DEFER | Scroll-depth sin pregunta concreta añade telemetría por curiosidad. | Reabrir ante hipótesis editorial específica. |
| I.4 | IMPLEMENT_AFTER_CURRENT_DEBT | Correlacionar contenido→suscripción sí guía decisiones. | Empezar con UTMs/SOURCE y export manual; no añadir tracker nuevo. |
| I.5 | IMPLEMENT_AFTER_CURRENT_DEBT | Minimización periódica reduce riesgo y deuda. | Inventario anual de campos, retención, finalidad y purge. |

## J · Comunidad / club de lectura

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| J.1 | DEFER | Hilos asíncronos implican moderación/cuentas/backend o tercero. | Reabrir con comunidad activa que lo demande. |
| J.2 | CONDITIONAL | Guías por capítulo aportan si el club realmente trabaja varias sesiones. | Crear tras uso real, no por SEO. |
| J.3 | PARTIAL_AUDIT | Ya existe `herramientas/eventos-ics/`; no crear otra implementación. | Reusar motor ICS en eventos/club si hay sesión real. |
| J.4 | REJECT | Badges/gamificación añaden ruido y estado sin objetivo actual. | Reconocimiento editorial manual si surge. |
| J.5 | CONDITIONAL | AMA escrito produce contenido first-party si hay preguntas auténticas. | Pilotar desde preguntas reales, con edición. |
| J.6 | PARTIAL_AUDIT | Lectores beta ya tienen arquitectura Brevo separada, pero el journey debe verificarse E2E. | Cerrar aislamiento/routing antes de ampliar programa. |

## K · Monetización

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| K.1 | CONDITIONAL | Venta/dedicatoria directa solo con logística, derechos, fiscalidad y proceso real. | No simular ecommerce; definir operación antes de UI/schema. |
| K.2 | DEFER | Bundle coleccionista sin demanda/logística es inventar catálogo. | Validar demanda primero. |
| K.3 | CONDITIONAL | Afiliación solo si relación real y disclosure; Google prefiere `rel=sponsored`. [S-GOOGLE-SPONSORED] | Registrar partner/condiciones/URL y marcar enlace. |
| K.4 | DEFER | Merch no es prioridad de producto. | Encuesta/ventas existentes primero. |
| K.5 | DEFER | Patreon/Ko-fi cambia modelo de relación/negocio. | Solo decisión explícita del autor. |

## L · PWA / móvil

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| L.1 | REJECT | Push exige suscripciones, backend/sender, VAPID, permisos y política; no se obtiene “gratis” por tener PWA. [S-MDN-PUSH] | Reabrir solo con necesidad de notificación fuerte. |
| L.2 | ALREADY_COVERED | Existe service worker/offline shell y ya se corrigió cache freshness/media Range. | Mantener contratos PWA. |
| L.3 | ALREADY_COVERED | `manifest.json` ya contiene shortcuts. | Revisar destinos cuando cambie IA. |
| L.4 | DEFER | Badging tiene soporte/contexto limitado y poco valor sin sistema de novedades. [S-MDN-BADGING] | No implementar ahora. |

## M · Seguridad / infraestructura

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| M.1 | PARTIAL_AUDIT | CSP está en HTML, pero las cabeceras live deben observarse; Cloudflare/DNS no las prueba. | Smoke de HSTS/X-Content-Type-Options/frame policy/CSP live. |
| M.2 | DEFER | HSTS preload es compromiso de todos los subdominios y tiene coste de reversión. | Solo tras inventario y periodo estable HTTPS completo. |
| M.3 | IMPLEMENT_AFTER_CURRENT_DEBT | Headers obsoletos deben retirarse si existen. | Auditar live; cambio solo con evidencia. |
| M.4 | CONDITIONAL | Monitor externo de TLS/DNS puede aportar redundancia. | Añadir solo si existe canal/owner de alertas. |
| M.5 | CONDITIONAL | Git ya da backup/versionado; export adicional solo ante RTO/RPO específico. | Definir recuperación antes de duplicar backups. |

## N · Internacionalización

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| N.1 | DEFER | `hreflang` sirve para variantes localizadas reales, no para intención futura. [S-GOOGLE-HREFLANG] | Implementar junto a primeras URLs traducidas reales. |
| N.2 | DEFER | `og:locale:alternate` sin contenido alternativo real no aporta. | Misma condición que N.1. |
| N.3 | CONDITIONAL | Glosario interno de nombres ayuda traducción cuando exista proyecto real. | Crear con traductor/editor, no antes. |

## O · Redes / distribución

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| O.1 | ALREADY_COVERED | El feed real es `feed.xml`, generado por `scripts/build-feed.py`. | Mejorar descubribilidad del feed solo si usuarios lo necesitan; no inventar `rss.xml`. |
| O.2 | IMPLEMENT_AFTER_CURRENT_DEBT | OG image por artículo puede mejorar compartición si hoy domina una imagen genérica. | Generación build-time con snapshot tests, sin IA visual genérica. |
| O.3 | REJECT | Extractos preformateados al final de cada pieza añaden ruido y duplicación. | Copy social vive en workflow editorial. |
| O.4 | CONDITIONAL | Metricool sirve para redistribuir evergreen, pero es operación editorial. | Calendario solo con contenido probado; no tocar runtime. |

## P · Herramientas para escritores

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| P.1 | CONDITIONAL | Exportar resultado aporta solo en herramientas cuyo output tenga valor fuera de página. | Pilotar 1 herramienta no sensible; imprimir/PDF nativo antes de librería. |
| P.2 | CONDITIONAL | Persistencia local puede ayudar, pero manuscritos son sensibles y localStorage perdura. | Opt-in, clear/export, no persistir texto sensible por defecto. |
| P.3 | REJECT | Changelog público de tools no tiene audiencia demostrada. | Notas en Cuaderno cuando una mejora sea editorialmente relevante. |
| P.4 | IMPLEMENT_AFTER_CURRENT_DEBT | Crosslinks relevantes mejoran recorrido y grafo. | Derivar relaciones desde registry, no hardcodear enlaces en 22 herramientas. |

## Q · Medición / validación

| ID | Decisión | Motivo / evidencia actual | Siguiente paso |
|---|---|---|---|
| Q.1 | PARTIAL_AUDIT | CrUX es field data útil, pero depende de suficiente muestra. [S-CRUX] | Consultar origin/page cuando haya datos; no inventar conclusiones con “sin datos”. |
| Q.2 | IMPLEMENT_AFTER_CURRENT_DEBT | Google + Bing muestran superficies distintas, incluida IA de Bing. [S-BING-AI-PERFORMANCE] | Cadencia trimestral con checklist y snapshot. |
| Q.3 | IMPLEMENT_NOW | Registrar hipótesis/resultados evita repetir experimentos y atribuciones falsas. | `data/experiments.json` + schema + owner/date/metric/result. |
| Q.4 | ALREADY_COVERED | Ya existen runbooks/gates de lanzamiento de Manecillas y release integrity. | Generalizar después del lanzamiento, no duplicar ahora. |

## Decisiones transversales sobre herramientas externas

Estas no crean IDs nuevos; aclaran cómo ejecutar los anteriores:

- **Ahrefs Webmaster Tools:** `CONDITIONAL`, segunda opinión gratuita de crawl/backlinks para propiedad verificada; no sustituye Search Console/Bing ni se convierte en “score de SEO”.
- **Screaming Frog Free:** `CONDITIONAL`, crawl local/ad-hoc; útil como segunda implementación para detectar divergencias. No añadir al CI si duplica nuestros checkers.
- **Microsoft Clarity + MCP:** `CONDITIONAL`. El MCP oficial **sigue activo en 2026** (`microsoft/clarity-mcp-server`); cualquier afirmación de que fue retirado es falsa. Solo instalar tracking si existe una hipótesis UX, revisión de privacidad/consentimiento y owner. [S-CLARITY-MCP]
- **Google Books / Play Books:** `CONDITIONAL` a derechos y capacidad del autor/editorial para gestionar el título. No subir libros unilateralmente.
- **BookBub / Books2Read:** `DEFER/CONDITIONAL` principalmente a ebook y presencia en retailers compatibles/múltiples; no abrir cuentas vacías por SEO.

## Criterio de cierre

Esta autoridad se considera suficientemente afianzada cuando:

1. el registry machine-readable contiene exactamente A.1–Q.4 (108 IDs) sin duplicados;
2. las fuentes primarias tienen URL exacta y fecha de comprobación;
3. ningún `REJECT`/`DEFER` aparece como tarea activa de implementación;
4. las mejoras `ALREADY_COVERED` apuntan a evidencia real de `main`;
5. las operaciones externas nunca se marcan hechas sin evidencia live;
6. cualquier cambio de proveedor/API posterior obliga a revalidar la decisión afectada, no todo el corpus.
