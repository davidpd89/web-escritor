# Ahrefs Free / Webmaster Tools + AI Visibility

Fecha de investigación: **2026-09-07**  
PR owner: **#463 · `tracking/ahrefs-free`**  
Estado: **OWNERSHIP_VERIFIED · SITE_AUDIT_BASELINE_REVIEWED · SCHEMA_BUGS_FIXED_VIA_482 · BACKLINKS_KEYWORDS_AI_VISIBILITY_NOT_YET_TRIAGED**

## Actualización (2026-09-09) — verificación de propiedad confirmada y primer Site Audit real ejecutado

Corrección sobre el estado anterior (`OWNERSHIP_VERIFICATION_PENDING_DEPLOY`, que quedó desactualizado sin que nadie lo revisara después del deploy): entrando en vivo a `app.ahrefs.com`, el proyecto **"David Porto Díaz · *.davidportodiaz.com/*"** ya está verificado y con datos reales — Health Score 100, 79 URLs rastreadas en el último crawl (211 en un crawl más amplio anterior), 0 errores internos, Domain Rating 2, 355 dominios de referencia.

### Site Audit — hallazgos reales clasificados

- **`Structured data has schema.org validation error` (6 páginas) → `REAL_BUG`, corregido en #482**: `Person.dateModified` no es una propiedad válida de schema.org (eliminada de `index.html`/`autor.html`/`premios.html`); `Person.award` en `index.html` usaba objetos `Thing` en vez de `Text` (aplanado a texto). `Event.eventStatus: EventCompleted` en `eventos.html`/`ferias.html`/el artículo de la Feria de Madrid también es un valor inválido (`EventStatusType` de schema.org solo define `EventScheduled/Cancelled/Postponed/Rescheduled/MovedOnline`), pero **no se ha tocado**: `scripts/build-event-calendars.py` y dos tests (`test-ferias-parity.py`, `qa/identity-public-browser.mjs`) usan ese valor no estándar como la señal deliberada que distingue eventos archivados de próximos para el feed .ics. Corregirlo bien requiere rediseñar esa distinción (p. ej. derivarla de `endDate` en vez de un `eventStatus` inventado), no un rename de paso — pendiente para una sesión dedicada.
- **`Noindex page` / `Noindex follow page` (4 cada uno)**: `FALSE_POSITIVE` esperado — son `privacidad.html`/`aviso-legal.html` con `robots: noindex, follow` intencional (páginas legales, ya documentado en `privacidad.html`).
- **`3XX redirect` (3) / `HTTP to HTTPS redirect` (2)**: probablemente intencional (canonicalización HTTPS/afiliados) — no triado en detalle todavía.
- **`Meta description too long` (2) / `Meta description too short` (1) / `Title too long (not indexable)` (1)**: no identificadas las URLs exactas todavía — pendiente de triar en una próxima sesión (afecta directamente al snippet en resultados de búsqueda, así que tiene valor real si se confirma).
- **`CSS file size too large` (1)**: pendiente de identificar el archivo — puede ser `FALSE_POSITIVE` si el umbral de Ahrefs no coincide con el presupuesto de rendimiento que ya vigila `performance-budget` en CI.
- **`Page has only one dofollow incoming internal link` (2)**: pendiente de identificar qué páginas — si son reales, es una oportunidad de mejorar enlazado interno (`REAL_IMPROVEMENT`).

### Pendiente de ejecutar (no tocado todavía)

- Backlinks/referring domains: 355 dominios de referencia visibles en el dashboard, sin explorar ancla/calidad/enlaces perdidos.
- Keywords/páginas orgánicas: Ahrefs muestra 0 en el resumen (probablemente porque el sitio es muy reciente en su índice, no necesariamente un problema real) — sin explorar Keywords Explorer.
- AI Visibility Checker (menciones en ChatGPT/Gemini/Perplexity/Copilot/Google AI Overviews): no ejecutado todavía.
- Clasificación completa de los issues de Site Audit restantes (redirects, meta description, CSS size, enlazado interno) en `REAL_BUG`/`REAL_IMPROVEMENT`/`FALSE_POSITIVE`/`LOW_VALUE`.

No cerrar esta rama como "hecho" hasta completar esos cuatro puntos — las plantillas/verificación de dominio están terminadas, pero el valor real de Ahrefs (backlinks, keywords, AI visibility) todavía no se ha extraído.

## Ejecución (2026-09-08)

Con la sesión de Ahrefs ya logueada por el autor: el flujo "Create project" →
Ahrefs Webmaster Tools no pide tarjeta ni pantalla de pago en ningún paso;
solo pide (paso 2) instalar opcionalmente "Ahrefs Web Analytics" -- un script
de terceros nuevo en el sitio -- que se ha dejado sin instalar a propósito
("Continue without analytics") porque añadir un tracker de terceros al sitio
en producción es una decisión que corresponde al autor, no algo a decidir
de forma autónoma.

Verificación de propiedad elegida: **HTML tag** (de las 4 opciones -- Google
Search Console, DNS record, HTML file, HTML tag -- es la única verificable
sin acceso a Google/DNS del autor). Se añadió a `index.html`:

```html
<meta name="ahrefs-site-verification" content="41735c3561cc3c682929cae030ab01f0e684bc6aa43b9a0a036282e4696a10d8">
```

Pendiente: una vez esta rama se mergee y despliegue, volver a Ahrefs →
Projects manager → davidportodiaz.com → "Recheck status" para completar la
verificación. Sin necesidad de intervención del autor salvo ese clic (o se
completa desde esta misma sesión tras el deploy).

## Objetivo

Aprovechar únicamente la capa gratuita de Ahrefs que pueda aportar señal nueva frente a Search Console, Bing, Clarity y el QA propio del repo.

No se trata de instalar otra herramienta por tenerla, sino de extraer:

- problemas técnicos que nuestros checks no hayan visto;
- backlinks/referring domains;
- keywords/páginas orgánicas;
- pérdidas de enlaces;
- visibilidad en IA;
- una baseline repetible.

## Alcance gratuito verificado hoy

Ahrefs Webmaster Tools permite actualmente, en sitios verificados:

- proyectos verificados ilimitados;
- **5.000 crawl credits por proyecto/mes** en Site Audit;
- hasta **1.000 backlinks** visibles a la vez;
- hasta **1.000 keywords** visibles a la vez;
- Site Audit y Site Explorer sobre sitios propios verificados.

Fuente oficial:

- https://ahrefs.com/webmaster-tools/

No necesitamos un plan de pago para esta PR.

## AI Visibility gratuito

Ahrefs ofrece actualmente un **AI Visibility Checker** gratuito y sin registro que consulta/mide visibilidad en:

- ChatGPT;
- Gemini;
- Perplexity;
- Microsoft Copilot;
- Google AI Overviews;
- Google AI Mode.

La vista gratuita es limitada, pero suficiente para crear baseline de marca/obras y detectar qué temas/dominos/páginas aparecen asociados.

Fuente oficial:

- https://ahrefs.com/es/ai-visibility-checker

El Brand Radar completo cuesta dinero y queda **fuera**. No iniciar trial ni upgrade para cerrar esta tarea.

## Qué NO instalar

Ahrefs ofrece Web Analytics, pero no lo necesitamos ahora.

Ya existen:

- Microsoft Clarity;
- GoatCounter;
- Metricool;
- Search Console;
- Bing Webmaster Tools.

Otro tracker incrementaría requests/privacy/mantenimiento sin una señal claramente diferencial.

Estado deseado:

`AHREFS_WEB_ANALYTICS_NOT_INSTALLED`

salvo que Claude demuestre una función exclusiva de alto valor que no podamos obtener de las herramientas actuales.

## Verificación del dominio

Preferencia:

1. importar/verificar mediante Google Search Console si Ahrefs ofrece esa vía en la cuenta;
2. HTML file / meta tag solo si hace falta;
3. DNS únicamente si las opciones anteriores no funcionan.

No modificar DNS por comodidad si GSC ya demuestra ownership.

Verificar:

- `davidportodiaz.com` sin `www` como proyecto principal;
- `www`/http como redirects, no proyectos duplicados;
- crawl scope canonical.

## Site Audit

Ejecutar crawl del sitio completo con JavaScript solo si Ahrefs lo necesita para ver contenido que de otro modo perdería. La web es mayoritariamente estática, por lo que un crawl HTML normal debería cubrir casi todo.

### Clasificación obligatoria de findings

Cada finding debe caer en:

- `REAL_BUG`
- `REAL_IMPROVEMENT`
- `FALSE_POSITIVE`
- `INTENTIONAL`
- `STALE_AHREFS_DATA`
- `LOW_VALUE`
- `EXTERNAL_DEPENDENCY`

No abrir PR por cada “warning” de herramienta.

### Prioridad técnica

Revisar especialmente:

- 4xx/5xx;
- redirects internos evitables;
- canonicals;
- indexability/noindex;
- sitemap;
- robots;
- orphan/near-orphan pages;
- inlinks;
- titles/H1;
- duplicate titles/descriptions solo cuando sean reales;
- hreflang si Ahrefs lo menciona, probablemente `NOT_APPLICABLE` en una web solo española;
- broken images/resources;
- internal links a Amazon/retailers rotos;
- structured data si Ahrefs lo expone;
- performance solo como señal complementaria, no sustituir Lighthouse/CrUX.

No considerar automáticamente `title > X chars` o `meta > Y chars` un bug. Evaluar SERP/claridad/CTR.

## Backlinks

Crear baseline real de:

- referring domains;
- backlinks;
- dofollow/nofollow/sponsored/UGC;
- anchors;
- first seen / last seen si la UI gratuita lo muestra;
- lost backlinks;
- backlinks rotos;
- páginas destino;
- dominios de autoridad vs spam.

### Páginas prioritarias

- Home;
- `/autor.html`;
- `/las-manecillas-del-recuerdo/`;
- `/las-manecillas-del-recuerdo/kindle/`;
- Samuel;
- artículo de fantasía juvenil que ya destaca en Bing AI Performance;
- herramientas con tráfico orgánico.

### Acciones útiles

- backlink legítimo apunta a URL 404 vieja → crear redirect solo si la equivalencia es real;
- enlace externo cita un dato desactualizado → valorar outreach;
- dominio bueno enlaza a Samuel pero no al autor/web principal → no “forzar” cambio si el enlace ya aporta valor;
- spam → normalmente ignorar; no iniciar desautorizaciones sin evidencia de daño/manual action.

## Organic keywords

Exportar/registrar las consultas/páginas con señal útil.

Cruzar con GSC/Bing, priorizando:

- keywords donde Ahrefs detecte ranking y GSC tenga impresiones;
- posiciones 4–20;
- queries con buena intención y página ya existente;
- long-tail alrededor de escritura, herramientas, lectores beta, portal fantasy, fantasía juvenil y libros.

No crear contenido nuevo solo porque Ahrefs genere una keyword.

## Páginas prioritarias para comparar

- contador de palabras/caracteres;
- lectores beta;
- portal fantasy;
- fantasía juvenil española;
- Manecillas;
- Samuel;
- autor;
- editoriales/manuscritos;
- herramientas de escritura.

## AI Visibility — baseline

Ejecutar el checker gratuito con, como mínimo:

1. `David Porto Díaz`
2. `Las manecillas del recuerdo`
3. `Samuel entre mundos`
4. `davidportodiaz.com` si el checker acepta bien dominios

Guardar por cada entidad:

- total de menciones si aparece;
- plataformas donde aparece;
- top topics;
- top cited domains;
- top cited pages;
- nuestra web citada sí/no;
- fecha.

### Interpretación

Ahrefs distingue **mention** de **citation**:

- mention: la IA nombra la marca/obra;
- citation: enlaza a una fuente.

Para nosotros una citation a `davidportodiaz.com` tiene más valor de atribución/tráfico potencial que una mención sin fuente.

No convertir la muestra gratuita en un KPI exacto de cuota de mercado.

## Cruzar con Bing AI Performance

Ya sabemos que Bing ha mostrado citas de páginas concretas del Cuaderno.

Comparar Ahrefs vs Bing:

- páginas citadas en ambos;
- temas repetidos;
- dominios externos que aparecen como fuentes;
- Manecillas/Samuel presentes o ausentes;
- oportunidades donde una página ya tiene autoridad temática pero no enlaza suficientemente al libro correspondiente.

## Cruzar con Search Console

Para cualquier keyword/page descubierta por Ahrefs:

- impresiones GSC;
- clicks;
- CTR;
- posición;
- index status;
- internal links.

Ahrefs no debe sustituir GSC para datos Google de primera mano.

## Broken links externos

Ahrefs puede ayudar a localizar:

- backlinks a URLs antiguas;
- links externos rotos desde nuestra web;
- recursos externos migrados.

Antes de corregir:

1. reproducir;
2. comprobar redirect chain;
3. identificar destino canónico;
4. cambiar owner/generador, no solo output si aplica.

## Qué cambios de repo puede generar esta PR

Solo findings reales, por ejemplo:

- redirect útil por backlink real a URL histórica;
- internal link roto;
- canonical incorrecto;
- página útil accidentalmente noindex;
- orphan page real;
- structured-data inconsistency;
- metadata claramente peor que una alternativa verificada;
- link graph insuficiente en una página estratégica.

No mezclar una doc-only PR con 20 cambios si Ahrefs descubre una tarea grande. Abrir una PR de código separada y enlazarla desde #463.

## Baseline a guardar

Fecha 2026-09-07/ejecución real:

- Health Score;
- crawled URLs;
- errors/warnings/notices;
- referring domains;
- backlinks;
- organic keywords;
- top pages;
- AI mentions/citations;
- URLs rotas externas/internas relevantes.

No conservar cifras como “verdad eterna”; son snapshots.

## Próxima revisión

Después del baseline:

- Site Audit: mensual o tras cambios grandes;
- backlinks: mensual;
- AI Visibility free: mensual;
- keywords: mensual;
- no revisar diariamente sin motivo.

## Secuencia exacta para Claude

### Fase 1 · cuenta

1. Entrar en Ahrefs.
2. Confirmar Free/AWT, sin plan pago.
3. Añadir/verificar `davidportodiaz.com`.
4. No instalar analytics.

### Fase 2 · Site Audit

1. crawl completo;
2. abrir All issues;
3. revisar errores uno a uno;
4. clasificar;
5. reproducir `REAL_BUG` en repo/live;
6. abrir PR solo si procede.

### Fase 3 · backlinks

1. referring domains;
2. backlinks;
3. anchors;
4. best by links;
5. broken/lost;
6. oportunidades reales.

### Fase 4 · organic search

1. organic keywords;
2. top pages;
3. posiciones 4–20;
4. cruzar GSC/Bing;
5. registrar acciones.

### Fase 5 · IA

Ejecutar checker gratuito con las 4 entidades y documentar.

### Fase 6 · cierre

Dejar:

- baseline;
- findings corregidos;
- findings descartados y motivo;
- PRs derivadas;
- próxima revisión.

## Fuentes verificadas

- https://ahrefs.com/webmaster-tools/
- https://ahrefs.com/es/webmaster-tools
- https://ahrefs.com/es/ai-visibility-checker
- https://ahrefs.com/es/brand-radar — solo para entender diferencia free vs paid; **NO comprar**.

## Criterio de cierre

`ACCOUNT_FREE · DOMAIN_VERIFIED · SITE_AUDIT_REVIEWED · BACKLINK_BASELINE_CAPTURED · KEYWORD_BASELINE_CAPTURED · AI_VISIBILITY_BASELINE_CAPTURED · ACTIONABLE_FINDINGS_IMPLEMENTED_OR_TRACKED · NO_EXTRA_ANALYTICS · NO_PAID_UPGRADE`
