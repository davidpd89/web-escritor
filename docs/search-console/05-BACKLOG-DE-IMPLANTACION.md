# 05 — Backlog de implantación: cuenta Google vs. repositorio

Este documento separa dos mundos que no deben confundirse:

- **ACCOUNT:** tareas que exigen entrar en Search Console / Google Cloud con la cuenta propietaria.
- **REPO:** tareas que Claude/GPT puede desarrollar, revisar y mergear en GitHub.

La automatización no debe intentar eludir la intervención humana para acciones sensibles de Search Console.

---

# A. ACCOUNT — Configuración inicial de Search Console

## GSC-A01 — Confirmar propiedad Domain

**Prioridad:** P0  
**Responsable:** propietario Google Search Console  
**Resultado esperado:** property `davidportodiaz.com` de tipo Domain, verified.

Pasos:

- [ ] abrir selector de properties;
- [ ] confirmar que existe `davidportodiaz.com` como Domain property;
- [ ] si no existe, crearla;
- [ ] verificar por DNS;
- [ ] documentar qué cuenta es verified owner;
- [ ] no borrar la verificación mientras haya usuarios delegados dependientes.

Evidencia a registrar en la PR/issue posterior: `DONE`, sin subir tokens DNS ni capturas con información sensible.

---

## GSC-A02 — Auditoría de usuarios y permisos

**Prioridad:** P0

- [ ] Settings > Users and permissions;
- [ ] identificar cada owner/full/restricted;
- [ ] retirar accesos obsoletos;
- [ ] conservar un verified owner controlado;
- [ ] decidir si hace falta una segunda cuenta de recuperación;
- [ ] registrar fecha de auditoría.

Cadencia: trimestral.

---

## GSC-A03 — Enviar sitemap raíz

**Prioridad:** P0

Enviar:

`https://davidportodiaz.com/sitemap.xml`

- [ ] comprobar `Success`/estado equivalente;
- [ ] fecha de lectura;
- [ ] URLs discovered;
- [ ] abrir Page Indexing filtrado por sitemap;
- [ ] no enviar `editoriales-sitemap.xml` adicional mientras duplique URLs del root.

Si Google rechaza el sitemap: abrir issue P0/P1 según impacto.

---

## GSC-A04 — Baseline de indexación

**Prioridad:** P0

Guardar recuentos por motivo:

- Indexed;
- Crawled not indexed;
- Discovered not indexed;
- noindex;
- robots;
- duplicate/canonical;
- redirect;
- 404/soft 404;
- server error;
- otros que muestre la property.

No guardar todos los ejemplos como «bugs». Clasificarlos contra intención del registry.

---

## GSC-A05 — Inspección inicial de URLs críticas

**Prioridad:** P0

Inspeccionar una a una:

- [ ] `https://davidportodiaz.com/`
- [ ] `https://davidportodiaz.com/autor.html`
- [ ] `https://davidportodiaz.com/libros/`
- [ ] `https://davidportodiaz.com/las-manecillas-del-recuerdo/`
- [ ] `https://davidportodiaz.com/libros/samuel-entre-mundos/`
- [ ] `https://davidportodiaz.com/cuaderno/`
- [ ] `https://davidportodiaz.com/herramientas/`
- [ ] `https://davidportodiaz.com/editoriales/`
- [ ] `https://davidportodiaz.com/convocatorias-escritores/`
- [ ] `https://davidportodiaz.com/recomendaciones/`
- [ ] `https://davidportodiaz.com/prensa.html`
- [ ] `https://davidportodiaz.com/premios.html`

Por URL registrar solo discrepancias:

- indexed;
- user canonical;
- Google canonical;
- crawl allowed;
- indexing allowed;
- last crawl;
- rich results detectados si procede.

---

## GSC-A06 — Manual Actions + Security Issues

**Prioridad:** P0

- [ ] comprobar Manual Actions;
- [ ] comprobar Security Issues;
- [ ] resultado esperado: sin incidencias;
- [ ] si hay cualquier incidencia, suspender optimizaciones y abrir incidente P0.

---

## GSC-A07 — Activar convención de anotaciones

**Prioridad:** P0

Crear/anotar próximos eventos relevantes.

Primer evento futuro obligatorio:

`RELEASE · Manecillas · publicación 03/09/2026`

No llenar las 200 anotaciones con cambios triviales.

---

## GSC-A08 — GenAI control

**Prioridad:** P0 si aparece  
**Estado feature:** rollout.

Settings > Search generative AI:

- [ ] comprobar si el control existe;
- [ ] si existe: mantener inclusión habilitada;
- [ ] registrar fecha/estado;
- [ ] no confundir con Google-Extended en robots.

Si la función no aparece: `NOT AVAILABLE YET`, no issue técnico.

---

## GSC-A09 — GenAI Search performance baseline

**Prioridad:** P1 si aparece  
**Estado:** rollout.

- [ ] abrir informe;
- [ ] exportar baseline con fecha;
- [ ] anotar total impressions;
- [ ] top pages;
- [ ] countries/devices si hay volumen;
- [ ] recordar anomalía 13–17 agosto 2026.

No incluir datos de queries porque el informe actual no documenta esa dimensión.

---

## GSC-A10 — GenAI Discover baseline

**Prioridad:** P2 si aparece.

- [ ] separar de Search GenAI;
- [ ] comprobar anomalías oficiales;
- [ ] guardar baseline.

---

## GSC-A11 — Platform property Instagram

**Prioridad:** P1 si rollout disponible.

Cuenta canónica según repo: Instagram `davidportodiaz`.

- [ ] Add property;
- [ ] seleccionar platform/Instagram si se ofrece;
- [ ] autenticar/verificar;
- [ ] comprobar Search performance;
- [ ] revisar Insights/Achievements disponibles;
- [ ] registrar estado de conexión.

---

## GSC-A12 — Platform property TikTok

**Prioridad:** P1 si rollout disponible.

Cuenta canónica según repo: TikTok `davidportoescritor`.

Mismos pasos que Instagram.

No crear X/YouTube hasta que el proyecto confirme cuentas oficiales.

---

## GSC-A13 — Search Performance baseline

**Prioridad:** P0

Exportar/registrar:

- últimos 28 días;
- 28 anteriores;
- últimos 3 meses;
- Search web;
- brand/nonbrand si disponible;
- pages;
- queries;
- devices;
- search appearance.

No subir dumps completos al repositorio salvo que se anonimicen y exista motivo.

---

## GSC-A14 — Baseline por territorios

**Prioridad:** P1

Crear filtros y guardar bookmarks/procedimiento para:

- Obras;
- Cuaderno;
- Herramientas;
- Editoriales/Convocatorias/Recursos;
- Recomendaciones;
- Entidad/Autor/Prensa.

---

## GSC-A15 — Core Web Vitals

**Prioridad:** P1

- [ ] mobile report;
- [ ] desktop report;
- [ ] Poor groups;
- [ ] Needs improvement;
- [ ] Good;
- [ ] mapear grupos a plantillas si hay incidencias.

Si no hay suficiente field data, documentar `INSUFFICIENT DATA`, no error.

---

## GSC-A16 — HTTPS

**Prioridad:** P1

- [ ] HTTP indexed URLs = objetivo 0;
- [ ] revisar cualquier causa HTTPS;
- [ ] si hay HTTP real indexado, abrir issue técnico.

---

## GSC-A17 — robots report

**Prioridad:** P1

- [ ] Google fetched current robots;
- [ ] no errors/warnings críticos;
- [ ] sitemap visible;
- [ ] no pedir recrawl si no hay cambio/incidente.

---

## GSC-A18 — Crawl Stats

**Prioridad:** P2

Baseline:

- crawl requests;
- avg response;
- download size;
- host status;
- response codes;
- crawl purpose;
- Googlebot types.

No convertir crawl budget en proyecto de optimización para un sitio pequeño.

---

## GSC-A19 — Links baseline

**Prioridad:** P1

Exportar/revisar:

- top externally linked pages;
- top linking sites;
- anchor text;
- internal linked pages;
- recent links/examples si aporta valor.

Objetivo: saber si Autor/Obras/recursos citables acumulan autoridad.

---

## GSC-A20 — Rich results

**Prioridad:** P1

Inventariar solo los informes que Search Console muestra realmente.

Por tipo:

- valid items;
- invalid;
- warnings;
- templates afectadas.

No abrir tarea para «crear informe Book» si Google no ofrece ese rich-result report.

---

## GSC-A21 — Discover / News

**Prioridad:** P2 condicional

- [ ] ¿Discover report aparece?
- [ ] ¿Google News report aparece?
- [ ] si no: `NO SUFFICIENT DATA/NOT SHOWN`;
- [ ] si sí: establecer baseline separado.

---

## GSC-A22 — Associations

**Prioridad:** P2

- [ ] revisar associations existentes;
- [ ] GA4 solo si existe y se decide usar;
- [ ] Ads solo si hay campañas;
- [ ] Merchant Center solo si la web se convierte en merchant directo;
- [ ] retirar asociaciones obsoletas.

---

# B. BIGQUERY — Implantación

## GSC-B01 — Crear proyecto GCP

**Prioridad:** P0/P1  
**Requiere aprobación de cuenta/facturación.**

- [ ] proyecto dedicado o claramente gobernado;
- [ ] billing;
- [ ] budget alert;
- [ ] BigQuery API;
- [ ] BigQuery Storage API.

---

## GSC-B02 — Permisos de export

Dar a:

`search-console-data-export@system.gserviceaccount.com`

roles oficiales:

- [ ] BigQuery Job User;
- [ ] BigQuery Data Editor.

No dar Owner.

---

## GSC-B03 — Configurar bulk export

Search Console > Settings > Bulk data export.

- [ ] project ID;
- [ ] dataset name (`searchconsole` recomendado salvo convención propia);
- [ ] iniciar;
- [ ] revisar primer export;
- [ ] anotar fecha de inicio.

---

## GSC-B04 — Monitor inicial

- [ ] `searchdata_site_impression` existe;
- [ ] `searchdata_url_impression` existe;
- [ ] `ExportLog` existe;
- [ ] primera fecha correcta;
- [ ] no confundir falta de histórico previo con error.

---

## GSC-B05 — Coste y retención

- [ ] presupuesto/alerta;
- [ ] revisión de bytes procesados;
- [ ] queries con filtro `data_date`;
- [ ] no aplicar expiración agresiva sin decisión.

---

# C. REPO — Trabajo que Claude puede implementar

## GSC-R01 — Carpeta `scripts/search-console/`

**Prioridad:** P1 después de resolver autenticación.

Propuesta:

```text
scripts/search-console/
├── README.md
├── config.example.json
├── fetch-search-analytics.py
├── inspect-priority-urls.py
├── check-sitemap-status.py
├── classify-territories.py
└── summarize-gsc.py
```

Criterios:

- read-only;
- idempotente;
- no secrets;
- UTF-8;
- retries/backoff;
- cuotas;
- logging seguro.

---

## GSC-R02 — Dependencias

Antes de añadir paquetes:

- comprobar stack Python existente;
- evitar SDKs enormes si Google auth/client mínimo basta;
- pinning/reproducibilidad;
- actualizar `scripts/requirements.txt` solo si procede;
- no meter Node si todo el flujo es Python.

---

## GSC-R03 — Configuración de propiedad

No hardcodear disperso.

Ejemplo no secreto:

```json
{
  "siteUrl": "sc-domain:davidportodiaz.com",
  "timezone": "Europe/Madrid",
  "finalDataLagDays": 3
}
```

El identificador de property no es una credencial.

---

## GSC-R04 — Derivar URLs desde `content-registry`

En vez de mantener dos inventarios, Claude debe estudiar:

- `status`;
- `searchIndex`;
- `sitemap`;
- `territory`;
- `sourceFile`;
- `url`.

Proponer un `monitorPriority` o mapa externo solo si hace falta distinguir P0/P1.

No marcar como bug automático una página public/searchIndex que Google decida no indexar.

---

## GSC-R05 — Search Analytics extractor

Tests obligatorios:

- rowLimit 25k;
- pagination;
- final vs all;
- query/page dimensions;
- retries;
- empty response;
- rate limit;
- date PT vs local Madrid;
- no duplicate writes.

---

## GSC-R06 — URL Inspection monitor

Salida agregada segura:

- URL;
- verdict;
- coverageState;
- robotsTxtState;
- indexingState;
- userCanonical;
- googleCanonical;
- lastCrawlTime.

No hacer live test: API no lo soporta.

---

## GSC-R07 — Sitemap monitor

Comparar:

- sitemap esperado repo;
- estado API Search Console;
- last submitted/downloaded si API lo expone;
- warnings/errors.

No re-submit diario.

---

## GSC-R08 — Territory classifier

Fuente única preferida: registry.

Testear al menos:

- Manecillas;
- Samuel;
- Cuaderno;
- Tools;
- Editoriales;
- Convocatorias;
- Recomendaciones;
- Autor/Prensa;
- unknown.

---

## GSC-R09 — Alert engine

Primera versión: solo reglas binarias de alto valor.

- priority URL no indexed;
- Google canonical inesperada;
- sitemap API error;
- export stale (si se consulta BQ);
- tráfico territorial con caída persistente solo si baseline mínimo.

No abrir GitHub issues automáticamente hasta validar falsos positivos durante varias semanas. Primero generar report/digest.

---

## GSC-R10 — Workflow daily

Solo después de seguridad/auth.

- schedule diario;
- no ejecutar en forks con secrets;
- permission `contents: read`;
- artifacts sin queries completas;
- output summary.

---

## GSC-R11 — Workflow weekly

Digest:

- territory trends;
- top gains/losses;
- new generic queries agregadas;
- CTR opportunities;
- index priority changes.

No modificar archivos web.

---

## GSC-R12 — BigQuery SQL versionado

Ruta propuesta:

```text
scripts/search-console/sql/
├── daily-web.sql
├── territory-trends.sql
├── query-opportunities.sql
├── rising-pages.sql
├── potential-cannibalization.sql
└── export-health.sql
```

Todo SQL:

- parametrizado;
- filtra partición;
- agrega;
- usa `SAFE_DIVIDE`;
- no presume dataset/project hardcoded.

---

## GSC-R13 — Tests sintéticos

Nunca golpear API real en unit tests.

Fixtures:

- pagination;
- anonymized query;
- multiple same-key rows;
- no impressions;
- partial data;
- index drop;
- canonical drift;
- expected noindex;
- unknown territory.

---

## GSC-R14 — Documentar secrets

Solo nombres, nunca valores:

- OAuth client/secret si se usa;
- refresh token o workload identity;
- GCP project;
- dataset.

Preferir Workload Identity/OIDC si encaja y reduce secretos estáticos; validar con documentación Google antes de implementar.

---

# D. Lanzamiento Manecillas — checklist temporal

## 03/09/2026

- [ ] annotation release;
- [ ] URL Inspection ficha;
- [ ] fragmentos;
- [ ] sitemap;
- [ ] 24h performance;
- [ ] brand query baseline;
- [ ] GenAI if available;
- [ ] no inventar purchaseUrl/Offer.

## 06/09 aprox.

- [ ] index state;
- [ ] first impressions;
- [ ] no technical blockers.

## 10/09 aprox.

- [ ] query/page first-week review;
- [ ] no over-optimization.

## 01/10 aprox.

- [ ] 28-day analysis;
- [ ] CTR/content opportunities;
- [ ] external links;
- [ ] discovery by generic topics.

---

# E. Definition of Done de esta iniciativa

La iniciativa Search Console estará en estado **OPERATIVA** cuando:

- [ ] GSC-A01 a A07 cerradas;
- [ ] GenAI/platform items marcadas `DONE` o `NOT AVAILABLE YET`;
- [ ] GSC-A13/A14 baselines realizados;
- [ ] CWV/HTTPS/robots/manual/security revisados;
- [ ] Links baseline;
- [ ] BQ export activo o decisión de no usar documentada;
- [ ] runbook semanal/mensual asignado;
- [ ] cualquier automatización futura respeta `03-AUTOMATIZACION-API-BIGQUERY.md`;
- [ ] no hay credenciales ni dumps privados en Git;
- [ ] las decisiones SEO siguen pasando por PR/QA, nunca por un bot que edita producción automáticamente.