# 10 — Medición, experimentos, updates y recovery

## Objetivo

Evitar dos errores frecuentes:

1. cambiar cosas porque «parece SEO» sin saber si había un problema;
2. atribuir cualquier subida/bajada al último commit aunque Google estuviera desplegando un update, hubiera estacionalidad o cambiara el mix de queries.

La estrategia de medición debe conectar:

`query → SERP → page → click → user job → downstream action`

---

# 1. Fuente principal

La operación de Search Console está documentada en `docs/search-console/`.

Esta carpeta define **qué decisiones SEO tomar con esos datos**.

No duplicar:

- setup de propiedad;
- API auth;
- BigQuery;
- URL Inspection API;
- permisos.

---

# 2. KPIs por territorio

## Entidad/autor

- impressions de marca;
- clicks de marca;
- queries `David Porto...`;
- CTR;
- sitelinks;
- Knowledge Panel accuracy si existe;
- páginas del autor indexadas correctamente.

## Obras

- title queries;
- author+title;
- genre queries que aterrizan en book pages;
- clicks a fragmentos;
- clicks a retailers;
- impressions/images;
- event discovery.

## Cuaderno

- non-brand clicks;
- new queries;
- article winners/losers;
- topic cluster growth;
- CTR;
- links earned;
- Discover separado.

## Herramientas

- non-brand tool queries;
- landing clicks;
- completion/interaction cuando se mida de forma privacy-safe;
- links/referrals;
- returning users si existe señal legítima.

## Directorios

- queries por editorial/género/manuscrito;
- freshness/verified coverage;
- clicks hacia fuentes oficiales;
- indexed entity pages;
- links earned.

---

# 3. Brand vs non-brand

Brand sirve para medir reconocimiento y dominio de entidad.

Non-brand sirve para medir descubrimiento.

No celebrar crecimiento orgánico si todo procede únicamente de una campaña externa que aumenta búsquedas exactas del nombre sin crecer en ningún tema.

Tampoco infravalorar brand: para un autor, una marca creciente es un activo real.

---

# 4. Ventanas

## Operativa

- 7d vs 7d: detección rápida, ruido alto;
- 28d vs 28d: principal para decisiones tácticas;
- 90d: tendencias;
- YoY: cuando haya historia comparable;
- event-specific: lanzamiento/feria.

No comparar 28 días de agosto con 28 de diciembre sin considerar estacionalidad.

---

# 5. Dimensiones mínimas

Para cada diagnóstico:

- query;
- page;
- device;
- country si relevante;
- search appearance;
- date.

No usar posición media global como diagnóstico.

Una URL puede tener posición 4 en una query y 60 en otra.

---

# 6. Conversiones SEO

Ranking no es el objetivo final.

Eventos secundarios a medir, respetando privacidad:

- `read_fragment`;
- `retailer_click`;
- `newsletter_start/confirmed` si taxonomía lo contempla;
- `event_interest`;
- `tool_completed`;
- `press_contact`;
- `club_resource`.

No atribuir una venta a Google si solo conocemos un click a retailer externo.

---

# 7. Experiment framework

SEO no permite el mismo control que un A/B client-side clásico porque Google debe ver una versión estable y no debemos cloakear.

Preferir **time-based controlled changes** en una URL o cohorts comparables.

## Registro

```yaml
id: SEO-EXP-001
hypothesis: "..."
urls:
  - /...
query_cluster: "..."
primary_metric: clicks|ctr|impressions|position
secondary_metrics: [...]
change_date: YYYY-MM-DD
minimum_window_days: 28
baseline_window: ...
algorithm_updates: []
other_changes: []
result: pending|keep|revert|iterate
```

---

# 8. Experimentos de title

Elegir URLs con:

- impressions suficientes;
- ranking relativamente estable;
- CTR claramente mejorable;
- intención conocida.

Antes:

- guardar title declarado;
- title que Google muestra;
- top queries;
- CTR/position.

Después:

- esperar suficiente data;
- controlar cambios de position;
- comprobar si Google sigue reescribiendo;
- keep/revert.

No cambiar títulos semanalmente.

---

# 9. Experimentos de contenido

Hipótesis específicas:

- mejorar respuesta inicial a intención;
- añadir experiencia first-party;
- actualizar información obsoleta;
- incorporar tabla/metodología;
- reforzar internal links.

No hacer simultáneamente:

- nuevo title;
- reescritura total;
- cambio de URL;
- nuevo schema;
- 20 backlinks;

si queremos aprender qué ocurrió.

---

# 10. Experimentos de internal linking

Buenos candidatos:

- URL con impressions posición 8–20;
- buena calidad;
- pocos inbound links;
- relación temática clara.

Cambio:

- enlaces contextuales desde hub/piezas relevantes;
- anchor natural.

Medir:

- crawl/index;
- impressions;
- query distribution;
- position/clicks.

No introducir 50 enlaces exact-match de golpe.

---

# 11. Core updates

Google core updates son cambios amplios.

No existe una lista de «cosas que arreglar para el update».

Google recomienda evaluar calidad general y puede tardar hasta el siguiente update o más en reflejar mejoras.

## Si cae tráfico durante core update

1. no actuar el primer día;
2. esperar a que termine rollout;
3. comparar periodo adecuado;
4. segmentar páginas/queries;
5. separar pérdidas pequeñas de grandes;
6. revisar contenido con preguntas people-first;
7. revisar competidores/SERP intent sin copiar;
8. hacer mejoras sostenibles;
9. no borrar media web.

---

# 12. Spam updates

Al corte:

- August 2026 spam update: 18/08 → 21/08, duración 2d16h;
- June 2026 spam update;
- March 2026 spam update.

Si una pérdida coincide:

- revisar spam policies;
- directorios escalados;
- links;
- contenido automatizado;
- reputación;
- structured data;
- no asumir penalty sin evidencia.

Una caída durante spam update no prueba manual action.

---

# 13. Discover updates

February 2026 Discover update debe anotarse separadamente.

No mezclar:

- Web clicks;
- Discover clicks;
- News.

Cada superficie puede moverse de forma distinta.

---

# 14. Update calendar

Mantener:

`data/seo-google-updates.json` o documento versionado.

Campos:

```json
{
  "name": "August 2026 spam update",
  "type": "spam",
  "start": "2026-08-18",
  "end": "2026-08-21",
  "source": "Google Search Status Dashboard"
}
```

No utilizar rumores como update confirmado.

---

# 15. Traffic drop decision tree

## Paso 1 — tracking

¿Hay datos disponibles?

- Search Console;
- analytics;
- deploy incident.

## Paso 2 — sitewide vs pages

- toda web;
- familia;
- URL;
- query.

## Paso 3 — clicks vs impressions

- impressions caen → visibility/demand/indexing;
- impressions estables, clicks caen → CTR/SERP mix;
- position cambia → ranking/intent/competition;
- clicks Search Console estables, analytics cae → analytics issue.

## Paso 4 — indexación

- URL indexed?;
- canonical selected?;
- robots/noindex?;
- status?;
- sitemap?;

## Paso 5 — technical

- 5xx;
- DNS;
- Cloudflare;
- deploy;
- CWV severe;
- mobile rendering.

## Paso 6 — algorithm

- official update?;
- rollout window?

## Paso 7 — SERP/intent

- new features?;
- intent changed?;
- query seasonality?

## Paso 8 — content

- factual?
- unique?
- useful?
- stale?
- competitor better satisfies job?

---

# 16. Recovery: indexing error

If critical URL deindexed unexpectedly:

1. fetch live;
2. status;
3. robots;
4. canonical;
5. sitemap;
6. URL Inspection;
7. rendered HTML;
8. links internal;
9. duplicate/canonical owner;
10. fix root cause;
11. deploy;
12. request indexing once;
13. monitor.

No request indexing 20 times.

---

# 17. Recovery: structured data manual action

Ver doc 06.

Resumen:

- identify exact violation;
- fix template/generator;
- validate all affected;
- deploy;
- reconsideration only after complete correction.

P0 third-party Amazon reviews debe corregirse antes de convertirse en problema.

---

# 18. Recovery: unnatural links

Solo si manual action/evidence real.

1. identify links created/controlled;
2. try removal where reasonable;
3. document;
4. disavow only if justified;
5. reconsideration.

No panic-disavow organic spam.

---

# 19. Recovery: hacked/spam

Si Security Issues:

- security incident > SEO experiment;
- isolate/fix;
- remove malicious content;
- update credentials;
- verify server;
- request review;
- Search Console monitoring.

No simplemente noindexear el hack.

---

# 20. Release annotations

Toda release material:

- title/meta overhaul;
- navigation;
- book status;
- schema;
- sitemap;
- redirect;
- major article update;
- launch;
- performance change;

se anota en Search Console (si feature disponible) y en changelog SEO.

---

# 21. SEO changelog

Propuesta:

`data/seo-change-log.json`

No incluir todo commit.

Solo cambios con hipótesis/impacto Search.

Ejemplo:

```json
{
  "date": "2026-08-27",
  "type": "structured-data",
  "urls": ["/libros/samuel-entre-mundos/"],
  "summary": "Removed third-party Amazon Review objects from Book JSON-LD",
  "reason": "Google review snippet policy compliance"
}
```

---

# 22. Weekly review

- anomalies;
- clicks/impressions;
- top gains/losses;
- new queries;
- index errors;
- manual/security;
- launch URLs.

No hacer cambios solo por weekly noise.

---

# 23. Monthly review

- territory performance;
- brand/nonbrand;
- CTR opportunities;
- content decay;
- query cannibalization;
- CWV;
- links;
- SERP brand/books;
- experiments.

---

# 24. Quarterly review

- architecture;
- hubs;
- stale/retired content;
- external profiles;
- Knowledge Panel;
- content portfolio;
- Google docs/policy changes;
- ROI of tools/directories.

---

# 25. Reporting format

No 100 metrics.

One-page executive:

- organic clicks;
- nonbrand clicks;
- top 5 gains/losses;
- indexed critical URLs;
- open P0 issues;
- experiments;
- next 3 actions.

Appendix contains detail.

---

# 26. Forecasts

No promise:

- «this will increase traffic 30%»;
- «position 1 in 3 months».

Forecasts are scenarios based on:

- current impressions;
- positions;
- expected CTR range;
- keyword demand;
- content pipeline.

Label assumptions.

---

# 27. Third-party tools

Google explicitly warns that third-party SEO tools do not have Google internal ranking data and cannot know exact rankings/scores/future impact.

Use them for:

- crawling;
- link discovery;
- keyword estimates;
- comparisons.

Not as authority for:

- «Google SEO score 92»;
- exact ranking difficulty;
- penalties;
- hidden algorithm weights.

---

# 28. Acceptance criteria

- decisions use segmented data;
- brand/nonbrand separated;
- Search/Discover separated;
- update windows logged;
- experiments versioned;
- no premature causal claims;
- recovery protocols exist;
- release annotations used;
- third-party scores not treated as Google truth;
- organic conversions measured without inventing retailer sales;
- reports prioritize actions, not vanity metrics.
