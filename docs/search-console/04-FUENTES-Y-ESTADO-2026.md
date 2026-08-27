# 04 — Fuentes oficiales y estado de funciones — 27/08/2026

Este fichero permite auditar de dónde sale cada recomendación de la PR. Se han priorizado **Search Console Help** y **Google Search Central / Google for Developers**. No se toman blogs SEO de terceros como autoridad para describir funcionalidades de producto.

## 1. Estados utilizados

- **GA / disponible:** Google documenta la función como parte normal de Search Console, aunque un informe concreto puede aparecer solo si hay datos.
- **ROLLOUT:** Google indica explícitamente que se está desplegando a un subconjunto/gradualmente.
- **EXPERIMENTAL:** Google describe la función como experimento o insight no generalizable.
- **CONDICIONAL:** el informe solo aparece si Google detecta datos/tipo suficiente.
- **OPERATIVO/EMERGENCIA:** herramienta real, pero no debe usarse como optimización rutinaria.

---

## 2. Inventario de funciones 2026

| ID | Función | Estado 27/08/2026 | Uso en este proyecto |
|---|---|---|---|
| SC-OVERVIEW | Overview / resumen | GA | triage |
| SC-RECOMMENDATIONS | Recommendations | GA | issues/oportunidades/configuración |
| SC-ANNOTATIONS | Anotaciones | GA | correlacionar releases/cambios con performance |
| SC-PERFORMANCE | Search Performance | GA | clics, impressions, CTR, position |
| SC-BRAND | Branded/non-branded | GA condicionado a volumen; no subproperties | adquisición nueva vs. demanda de marca |
| SC-24H | 24 hours / hourly | GA | lanzamientos/incidentes |
| SC-INSIGHTS | Search Console Insights | ROLLOUT | tendencias editoriales |
| SC-SOCIAL-INSIGHTS | social channel insights | EXPERIMENTAL | complementar properties sociales |
| SC-GENAI-REPORT | GenAI Search performance | ROLLOUT | AI Overviews + AI Mode impressions |
| SC-GENAI-DISCOVER | GenAI Discover performance | ROLLOUT | IA en Discover |
| SC-GENAI-CONTROL | Search generative AI control | ROLLOUT | mantener inclusión si queremos alcance |
| SC-PLATFORM | Platform properties | ROLLOUT | Instagram/TikTok/X/YouTube en Google |
| SC-SITEMAPS | Sitemaps | GA | discovery/estado |
| SC-PAGE-INDEXING | Page indexing | GA | expected vs unexpected exclusions |
| SC-URL-INSPECTION | URL Inspection UI | GA | indexed + live test |
| SC-CWV | Core Web Vitals | GA/condicional a datos de campo | UX real |
| SC-HTTPS | HTTPS report | GA | 0 HTTP indexado |
| SC-CRAWL-STATS | Crawl Stats | GA root properties | hosting/rastreo/incidentes |
| SC-ROBOTS | robots.txt report | GA root properties | errores/recrawl emergencia |
| SC-RICH-RESULTS | Rich result reports | CONDICIONAL | schema detectado |
| SC-DISCOVER | Discover Performance | CONDICIONAL a impressions | contenido recomendado |
| SC-NEWS | Google News Performance | CONDICIONAL | news.google.com/apps |
| SC-LINKS | Links | GA | backlinks + internal links |
| SC-MANUAL-ACTIONS | Manual Actions | GA | P0 |
| SC-SECURITY | Security Issues | GA | P0 |
| SC-REMOVALS | Removals + SafeSearch | OPERATIVO/EMERGENCIA | retirada temporal/urgente |
| SC-USERS | Users & permissions | GA | gobierno |
| SC-ASSOCIATIONS | Associations | GA | GA/Ads/Merchant/etc. con caso real |
| SC-ACHIEVEMENTS | Achievements | GA | hito, no ranking |
| SC-CHANGE-ADDRESS | Change of Address | OPERATIVO migración | cambio de dominio |
| SC-EXPORT-MANUAL | Report export | GA | análisis puntual |
| SC-BQ | Bulk export BigQuery | GA | histórico propio diario |
| SC-API | Search Console API | GA | automatización |
| SC-URL-API | URL Inspection API | GA | monitor indexed version |

---

## 3. Fuentes: fundamentos y catálogo de informes

### SC-ABOUT

Search Console overview / propósito:

https://support.google.com/webmasters/answer/9128668?hl=es-es

Google define Search Console como herramienta para rastreo/indexación, tráfico, errores y alertas.

### SC-REPORTS

Resumen oficial de informes y herramientas:

https://support.google.com/webmasters/answer/9133276?hl=es

Usar esta página como inventario vivo: si Google retira o añade un informe, este documento debe revisarse.

---

## 4. Propiedades, plataforma, usuarios y asociaciones

### SC-PROPERTIES

Añadir propiedades Domain, URL-prefix y platform:

https://support.google.com/webmasters/answer/34592?hl=es

Puntos verificados:

- Domain incluye protocolos/subdominios y usa DNS;
- URL-prefix limita por protocolo/prefijo;
- platform property es un tipo nuevo para cuentas/canales compatibles.

### SC-PLATFORM

Propiedades de plataforma:

https://support.google.com/webmasters/answer/17148418?hl=es

Estado oficial: **rollout gradual**.

Plataformas documentadas:

- Instagram;
- TikTok;
- X;
- YouTube.

Estas properties miden exposición del contenido de la plataforma en Google Search (y News/Discover si hay datos), no vistas nativas en la plataforma.

### SC-USERS

Propietarios, usuarios y permisos:

https://support.google.com/webmasters/answer/7687615?hl=es

Incluye verified owner, delegated owner, full user, restricted user y associate.

### SC-ASSOCIATIONS

Asociaciones:

https://support.google.com/webmasters/answer/9419894?hl=es-001

Google documenta asociaciones con, entre otros:

- Google Analytics;
- Google Ads;
- Merchant Center;
- Play/Android;
- Chrome Web Store;
- Vertex AI Agent Builder.

---

## 5. Performance, marca y Insights

### SC-PERFORMANCE

Introducción práctica al rendimiento:

https://support.google.com/webmasters/answer/10268906?hl=es

### SC-PERFORMANCE-TASKS / SC-BRAND

Casos de uso y branded/non-branded:

https://support.google.com/webmasters/answer/17010961?hl=es

Hechos actuales:

- filtro branded/non-branded desde 11/03/2025;
- funciona en web/image/video/news;
- no disponible en subproperties;
- puede no estar disponible con pocas impressions.

### SC-PERFORMANCE-DIMENSIONS

Dimensiones/agrupaciones y caveats:

https://support.google.com/webmasters/answer/17011259?hl=es

Google advierte de queries anonimizadas, límites de tabla y clasificación brand/genérica informativa.

### SC-INSIGHTS

Search Console Insights:

https://support.google.com/webmasters/answer/16308503?hl=es

Estado: rollout gradual.

Incluye resúmenes de rendimiento/tendencias y puede incorporar brand/generic y fuentes adicionales según disponibilidad.

---

## 6. Anotaciones

### SC-ANNOTATIONS

https://support.google.com/webmasters/answer/16530728?hl=es

Detalles investigados:

- system/custom annotations;
- compartidas en property;
- hasta 200 custom annotations;
- máximo 120 caracteres;
- mayores de 500 días se eliminan;
- no editables;
- no visibles en compare/24h.

---

## 7. IA generativa de Google Search

### SC-GENAI-REPORT

Informe IA generativa Search:

https://support.google.com/webmasters/answer/16984139?hl=es

Estado: rollout a subconjunto de properties.

Incluye:

- AI Overviews / Vistas creadas con IA;
- AI Mode / Modo IA;
- impresiones y dimensiones como pages/country/device/date.

Google indica que Search Labs no se incluye.

### SC-GENAI-CONTROL

Control de inclusión:

https://support.google.com/webmasters/answer/16908024?hl=es

Estado: rollout a subconjunto.

Controla inclusión en:

- AI Overviews;
- AI Mode;
- funciones generativas de Discover.

La recomendación del proyecto de mantener inclusión activa es **estratégica**, no una afirmación de Google sobre ranking.

### SC-ANOMALIES

Anomalías oficiales:

https://support.google.com/webmasters/answer/6211453?hl=es-419

A la fecha de corte son relevantes:

- 13/08/2026 Discover/GenAI Discover: logging error en clicks/impressions;
- 13–17/08/2026 GenAI Search: logging error en impressions.

Consultar siempre la página actual antes de diagnosticar un descenso.

---

## 8. Indexación, sitemaps, inspección y robots

### SC-PAGE-INDEXING

https://support.google.com/webmasters/answer/7440203?hl=es-es

Puntos clave:

- no todas las URLs deben indexarse;
- páginas importantes sí;
- ejemplos limitados;
- URL Inspection para casos concretos.

### SC-URL-INSPECTION

https://support.google.com/webmasters/answer/9012289?hl=es

Incluye versión indexada + live test + datos estructurados + request indexing.

### SC-URL-TROUBLESHOOTING

https://support.google.com/webmasters/answer/12482179?hl=es

Flujo de solución para una página concreta.

### SC-ROBOTS

https://support.google.com/webmasters/answer/6062598?hl=es

Puntos:

- top 20 hosts;
- versiones/estado;
- warnings/errors;
- request recrawl en emergencia;
- robots controla crawl, no sirve como `noindex`.

### SC-SITEMAPS

Catálogo principal Search Console Help:

https://support.google.com/webmasters/topic/9456557?hl=es

Además, el catálogo general de Search Console enlaza la gestión de Sitemaps:

https://support.google.com/webmasters/?hl=es

La política específica de un sitemap raíz único/no solapado para este repo es recomendación arquitectónica del proyecto, no requisito universal de Google.

---

## 9. Field UX, HTTPS y crawl

### SC-CWV

https://support.google.com/webmasters/answer/9205520?hl=es-001

Métricas de campo:

- LCP;
- INP;
- CLS.

Agrupa URLs en Good / Needs improvement / Poor.

### SC-HTTPS

https://support.google.com/webmasters/answer/11396518?hl=es

Objetivo de Google recomendado: evitar URLs HTTP indexadas y resolver causas HTTPS.

### SC-CRAWL-STATS

https://support.google.com/webmasters/answer/9679690?hl=es

Google indica que el informe está orientado a usuarios avanzados y que sitios pequeños normalmente no deben obsesionarse con crawl budget.

---

## 10. Enlaces

### SC-LINKS

https://support.google.com/webmasters/answer/9049606?hl=es

Hechos importantes:

- no es una lista completa de backlinks;
- tablas hasta 1.000 filas;
- datos agrupados por canonical/domain;
- enlaces externos e internos;
- exports especiales de backlinks pueden llegar a 100.000 filas de ejemplos/recientes.

---

## 11. Rich results y structured data

### SC-RICH-RESULTS

https://support.google.com/webmasters/answer/7552505?hl=es-us

Search Console crea informes separados para tipos de rich result detectados.

### SC-RICH-TROUBLESHOOT

https://support.google.com/webmasters/answer/13300208?hl=es-001

Proceso de errores → fix → validate.

### GOOGLE-STRUCTURED-GALLERY

https://developers.google.com/search/docs/appearance/structured-data/search-gallery?hl=es

Catálogo oficial actualizado de markup compatible.

Tipos relevantes investigados: Article, Breadcrumb, Event, Organization, Product, ProfilePage, image metadata, etc.

### GOOGLE-ARTICLE

https://developers.google.com/search/docs/appearance/structured-data/article?hl=es

### GOOGLE-BREADCRUMB

https://developers.google.com/search/docs/appearance/structured-data/breadcrumb

### GOOGLE-EVENT

https://developers.google.com/search/docs/appearance/structured-data/event?hl=es

### GOOGLE-PROFILE

https://developers.google.com/search/docs/appearance/structured-data/profile-page?hl=es

### GOOGLE-PRODUCT

https://developers.google.com/search/docs/appearance/structured-data/product

Google diferencia Product snippets de Merchant listings; merchant listings son para páginas donde se puede comprar directamente al merchant.

### GOOGLE-FAQ-RETIREMENT

La referencia actual de Search Analytics API documenta:

- 07/05/2026: FAQ rich results dejan de aparecer en Google Search;
- agosto 2026: retirada del soporte de FAQ search appearance en Search Console API.

https://developers.google.com/webmaster-tools/v1/searchanalytics/query?hl=es-419

---

## 12. Discover y News

### SC-DISCOVER

https://support.google.com/webmasters/answer/9216516?hl=es

Solo aparece si la property alcanza un mínimo de impressions en Discover.

### SC-NEWS

https://support.google.com/webmasters/answer/10083653?hl=es

El informe Google News cubre `news.google.com` y apps. La pestaña News de Google Search se analiza en Search Performance con search type News.

---

## 13. Seguridad, acciones manuales y retiradas

### SC-MANUAL-ACTIONS

https://support.google.com/webmasters/answer/9044175?hl=es

### SC-SECURITY

https://support.google.com/webmasters/answer/9044101?hl=es-ES

Diferencia oficial:

- manual action = incumplimientos detectados manualmente que pueden afectar ranking/indexación;
- security issue = sitio comprometido/peligroso para usuarios.

### SC-REMOVALS

https://support.google.com/webmasters/answer/9689846?hl=es

Hechos:

- retirada temporal ≈ 6 meses / 180 días;
- no impide crawl;
- no es retirada permanente;
- no se usa para limpiar 404 normales;
- robots.txt no es mecanismo de retirada permanente.

---

## 14. Migraciones

### SC-CHANGE-ADDRESS

https://support.google.com/webmasters/answer/9370220?hl=es

Uso: cambio real de dominio. Google mantiene la señal especial del cambio durante 180 días; redirects deben mantenerse al menos ese periodo y preferiblemente más mientras haya tráfico.

---

## 15. Export manual, BigQuery y API

### SC-EXPORT-MANUAL

https://support.google.com/webmasters/answer/12919797?hl=es

- Sheets/Excel/CSV;
- export de la vista del informe;
- tablas normalmente limitadas a 1.000 filas de ejemplos.

### SC-BQ-OVERVIEW

https://support.google.com/webmasters/answer/12918484?hl=es

Export diario de performance a BigQuery, excepto queries anonimizadas.

### SC-BQ-SETUP

https://support.google.com/webmasters/answer/12917675?hl=es

Requisitos:

- GCP + billing;
- BigQuery API;
- BigQuery Storage API;
- `search-console-data-export@system.gserviceaccount.com`;
- BigQuery Job User;
- BigQuery Data Editor.

### SC-BQ-MANAGE

https://support.google.com/webmasters/answer/12919198?hl=es

Monitorización/estado de export.

### SC-BQ-TABLES

https://support.google.com/webmasters/answer/12917991?hl=es

Tablas:

- `searchdata_site_impression`;
- `searchdata_url_impression`;
- `ExportLog`.

### SC-BQ-QUERY-GUIDELINES

https://support.google.com/webmasters/answer/12917174?hl=es

Google exige/aconseja:

- agregar siempre;
- limitar por partición/fecha;
- filtrar queries anonimizadas cuando se analiza texto de query.

### SC-API

https://developers.google.com/webmaster-tools

Servicios: Search Analytics, Sitemaps, Sites, URL Inspection.

### SC-API-EXPORT

https://support.google.com/webmasters/answer/12919192?hl=es

Search Analytics API: hasta 50.000 filas/día/tipo/property.

### SC-API-QUERY

https://developers.google.com/webmaster-tools/v1/searchanalytics/query

Detalles actuales:

- `rowLimit` 1–25.000;
- `startRow` pagination;
- `dataState=final|all|hourly_all`;
- metadata para periodos incompletos.

### SC-API-QUOTAS

https://developers.google.com/webmaster-tools/limits?hl=en

Cuotas verificadas:

- Search Analytics: 1.200 QPM site/user; 30M QPD + 40k QPM project;
- URL Inspection: 2.000 QPD + 600 QPM site; 10M QPD + 15k QPM project;
- other resources: 20 QPS/200 QPM user; 100M QPD project.

### SC-URL-API

https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect?hl=es-419

Limitación fundamental: **solo versión del índice**; no live URL test.

---

## 16. Fuentes internas del repositorio cruzadas

Estas no sustituyen documentación Google; sirven para adaptar la estrategia al sitio real:

- `/robots.txt` — sitemap y crawl policy actual;
- `/sitemap.xml` — inventario de URLs indexables generado;
- `/data/content-registry.json` — autoridad interna de status/searchIndex/sitemap/territory;
- `/press-kit/david-porto-diaz.json` — perfiles sociales canónicos y entidad;
- `scripts/check-global-discoverability.py` y QA asociados — contratos predeploy;
- `scripts/build-public-dist.py` — frontera pública;
- auditorías de superficie/machine authority — noindex, staging y facts.

### Hallazgos de adaptación

1. `robots.txt` ya declara el sitemap raíz.
2. El sitemap raíz incluye las principales áreas públicas.
3. Instagram/TikTok constan como perfiles canónicos: son candidatos reales para Platform properties.
4. X/YouTube no constan en el contrato social actual: no inventar properties.
5. El sitio ya tiene QA técnico fuerte; GSC debe aportar la capa externa de «qué hizo Google realmente», no duplicar CI.

---

## 17. Funciones que NO se deben sobreinterpretar

### Recommendations

Son opcionales. No son órdenes ni garantía de mejora.

### Position

Media agregada; no usar como KPI único.

### Links

Muestra/muestreo, no backlink index completo.

### Page Indexing

No es objetivo indexar cada URL.

### Core Web Vitals

Puede no mostrar grupos sin suficiente field data.

### Discover/News/GenAI/Rich results

Ausencia del informe puede significar:

- no suficiente data;
- feature rollout;
- tipo no detectado;
- property no elegible;

no necesariamente implementación rota.

### Platform properties

Miden Google Search exposure del contenido social; no analytics nativa de redes.

---

## 18. Research watchlist

Revisar trimestralmente si Google cambia:

- rollout de GenAI reports/control;
- dimensiones/métricas GenAI (actualmente más limitadas que Search normal);
- API específica para GenAI;
- soporte BigQuery para properties de plataforma;
- disponibilidad general de Platform properties;
- social channel insights;
- Search Console Insights;
- branded/non-branded export/API;
- structured-data features retiradas/nuevas;
- cuotas API;
- export schema/fields de BigQuery.

Fecha de próxima revisión recomendada: **noviembre de 2026**, o antes si Search Console anuncia un cambio relevante.