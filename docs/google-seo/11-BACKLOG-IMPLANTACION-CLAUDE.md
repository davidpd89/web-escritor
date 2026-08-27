# 11 — Backlog de implantación para Claude

## Propósito

Este documento convierte la auditoría en trabajo ejecutable.

No todos los elementos pueden resolverse desde GitHub. Cada tarea tiene un **actor**:

- `REPO` — Claude puede implementar código/docs/tests en una rama/PR.
- `SEARCH-CONSOLE` — requiere acceso/acción en Google Search Console.
- `GOOGLE-ACCOUNT` — requiere un producto/cuenta Google fuera del repo.
- `CLOUDFLARE` — requiere configuración/verificación live en Cloudflare.
- `HUMAN` — decisión/revisión humana.
- `EDITORIAL` — depende de derechos, editorial, retailer, material o hecho real.
- `EXTERNAL` — acción/perfil/fuente de terceros.

## Reglas de ejecución

1. No desplegar producción sin autorización explícita.
2. No crear cuentas, propiedades, API keys, DNS, Merchant Center, Google Books Partner accounts ni perfiles externos automáticamente.
3. No inventar datos de Search Console.
4. No afirmar un ranking sin medirlo.
5. No publicar un retailer/Offer sin verificación.
6. No crear contenido masivo para cerrar tickets.
7. No mergear un cambio runtime solo porque el test local pasa; verificar public artifact y CI.
8. Releer `docs/google-seo/13-FUENTES-OFICIALES-Y-CORTE-2026-08-27.md` antes de implementar una feature que pueda haber cambiado.
9. Mantener separadas las autoridades `docs/search-console/` y `docs/ai-discoverability/`.
10. Todo P0 excluido debe quedar en issue/PR explícita, no solo en chat.

---

# Fase 0 — Baseline y P0

## SEO-001 — Retirar reviews de Amazon del JSON-LD de Samuel

**Prioridad:** P0  
**Actor:** REPO  
**Archivo principal:** `libros/samuel-entre-mundos/index.html`

### Acción

Eliminar del objeto `Book` la propiedad `review` cuando los objetos proceden de Amazon España.

### No hacer

- no reemplazar por `aggregateRating`;
- no cambiar el publisher para ocultar el origen;
- no copiar Goodreads/Casa del Libro;
- no eliminar necesariamente las citas visibles editoriales si existen y son legítimas: el problema P0 es el markup agregado de terceros.

### Tests

Crear/actualizar `tests/test-google-structured-data-policy.py`:

- `Book` de Samuel no contiene `review` de terceros;
- no `aggregateRating` derivado de retailers;
- Book factual sigue presente.

### Acceptance

- JSON-LD parsea;
- tests verdes;
- Rich Results Test manual posterior al deploy sin violación conocida;
- public artifact mantiene Book/ISBN/date/publisher.

---

## SEO-002 — Añadir guardrail contra third-party Review markup

**Prioridad:** P0  
**Actor:** REPO  
**Depende:** SEO-001

Crear un test que falle si se reintroduce:

- Review publisher Amazon/Goodreads/Casa del Libro/retailer en Book;
- `aggregateRating` externo.

No bloquear Review first-party futuro legítimo por diseño; test debe distinguir origen.

---

## SEO-003 — Inventario live de URLs factuales críticas

**Prioridad:** P0  
**Actor:** HUMAN/SEARCH-CONSOLE

URLs:

- `/`;
- `/autor.html`;
- `/libros/`;
- `/libros/samuel-entre-mundos/`;
- `/fragmento/`;
- `/las-manecillas-del-recuerdo/`;
- `/las-manecillas-del-recuerdo/fragmentos/`;
- `/premios.html`;
- `/prensa.html`;
- `/eventos.html`;
- `/ai/`.

Por URL registrar:

- HTTP;
- canonical live;
- robots meta;
- title;
- H1;
- ISBN/date/publisher cuando aplique;
- Search Console indexed state;
- Google-selected canonical;
- last crawl.

No inventar snapshot si no hay acceso.

---

## SEO-004 — Cerrar stale fact de Samuel 2025

**Prioridad:** P0  
**Actor:** SEARCH-CONSOLE/HUMAN  
**Depende:** SEO-003

Verificar que Google ya no presenta `Libros Indie, 2026` para `/fragmento/` o queries del libro.

Si persiste:

1. comprobar producción;
2. URL Inspection;
3. rendered HTML;
4. canonical;
5. links internos;
6. request indexing una vez si procede;
7. esperar recrawl;
8. comprobar SERP.

Closure = evidencia de dato correcto en Search/inspection, no solo repo.

---

## SEO-005 — Verificar stale home

**Prioridad:** P0  
**Actor:** SEARCH-CONSOLE/HUMAN

Comprobar si el title/snippet antiguo de home sigue apareciendo en búsquedas de marca.

Registrar:

- declared title;
- shown title;
- shown snippet;
- selected canonical.

No forzar un cambio de title si el problema es una copia antigua pendiente de recrawl.

---

## SEO-006 — Manual Actions baseline

**Prioridad:** P0  
**Actor:** SEARCH-CONSOLE

Revisar informe `Manual actions`.

Estado esperado: sin acciones.

Si existe una:

- no continuar con experimentos de ranking hasta identificarla;
- abrir ticket dedicado con exact reason/screenshots/dates.

---

## SEO-007 — Security Issues baseline

**Prioridad:** P0  
**Actor:** SEARCH-CONSOLE

Revisar `Security issues`.

Si existe:

- prioridad seguridad/ops;
- no resolver con noindex.

---

# Fase 1 — Sitemap / canonical / indexability

## SEO-008 — Normalizar slash de home en sitemap

**Prioridad:** P1  
**Actor:** REPO

Cambiar/generar:

`https://davidportodiaz.com/`

no variante sin slash.

Acceptance:

- canonical = sitemap loc;
- no duplicate home loc;
- tests.

---

## SEO-009 — Localizar autoridad real del sitemap

**Prioridad:** P1  
**Actor:** REPO

Determinar si `sitemap.xml` se mantiene manualmente o mediante script existente.

No parchear XML a mano si hay generador.

Documentar source-of-truth.

---

## SEO-010 — Generador determinista de sitemap

**Prioridad:** P1  
**Actor:** REPO  
**Depende:** SEO-009

Implementar/reutilizar `scripts/seo/build-sitemap.py` o equivalente.

Input principal:

`data/content-registry.json`

Output:

`sitemap.xml`

Flags:

- `--check`;
- deterministic;
- no network.

---

## SEO-011 — Contrato sitemap/indexability

**Prioridad:** P1  
**Actor:** REPO

Crear `tests/test-seo-indexability-contract.py`.

Assert:

- sitemap URLs únicas;
- public/indexable only;
- no `noindex`;
- no gated/internal/deprecated;
- no fragments;
- no redirects known;
- canonical form exact;
- home slash;
- registry parity.

---

## SEO-012 — Política `lastmod`

**Prioridad:** P1  
**Actor:** REPO + EDITORIAL

Elegir fuente real:

- `seoLastModified` en registry;
- o authority factual por familia;
- o metadata existente fiable.

No usar git checkout mtime/build date.

---

## SEO-013 — Implementar `lastmod` fiable

**Prioridad:** P1  
**Actor:** REPO  
**Depende:** SEO-012

Solo cambiar cuando cambia contenido material.

Tests:

- ISO date;
- no future accidental;
- deterministic;
- no touch-on-build.

---

## SEO-014 — Auditor canonical del public artifact

**Prioridad:** P1  
**Actor:** REPO

Crear `scripts/seo/audit-indexability.py`.

Reportar:

- URL;
- registry id;
- canonical;
- robots;
- sitemap expected/actual;
- source file.

Fail solo para contract violations objetivas.

---

## SEO-015 — Verificar HTTP/www/slash/index.html live

**Prioridad:** P1  
**Actor:** CLOUDFLARE/HUMAN

Para URLs prioritarias:

- http→https;
- www→canonical host;
- index.html→pretty URL;
- trailing slash;
- parameter behavior.

Guardar matriz status/final URL.

---

## SEO-016 — Mapa de redirects versionado

**Prioridad:** P2  
**Actor:** REPO

Crear fichero máquina-readable con:

- from;
- to;
- date;
- reason.

No duplicar configuración runtime si ya existe una autoridad de redirects; usarlo como fuente o reporte según arquitectura.

---

## SEO-017 — Test de redirect chains

**Prioridad:** P2  
**Actor:** REPO

Fail para nuevas chains >1 salto en mapa/control local.

---

## SEO-018 — Auditor soft-404 candidates

**Prioridad:** P2  
**Actor:** REPO + SEARCH-CONSOLE

Identificar 200 pages con:

- contenido retirado;
- resultados vacíos;
- mensajes «no disponible».

No cambiar automáticamente: revisar intención/noindex/404/410.

---

# Fase 2 — Query roles y arquitectura

## SEO-019 — Añadir inventario query-role

**Prioridad:** P1  
**Actor:** REPO

Crear `data/seo-query-roles.json` o integrar campo en registry.

Roles mínimos:

- entity;
- book-title;
- definition;
- comparison;
- recommendation;
- tool;
- directory;
- event;
- sample;
- topic-hub.

No guardar keyword stuffing.

---

## SEO-020 — Mapear todas las URLs indexables a role

**Prioridad:** P1  
**Actor:** REPO + HUMAN

No dejar leaf pública sin role/parent/hub conceptual.

---

## SEO-021 — Export query→page desde Search Console

**Prioridad:** P1  
**Actor:** SEARCH-CONSOLE

Para clusters principales.

No crear datos ficticios si API/BigQuery aún no está configurado.

---

## SEO-022 — Diagnóstico portal fantasy

**Prioridad:** P1  
**Actor:** SEARCH-CONSOLE + HUMAN

Comparar URLs:

- definition;
- comparison;
- topic hub;
- analysis;
- recommendation;
- Samuel.

Decision per overlap:

protect/improve/merge/clarify.

---

## SEO-023 — Diagnóstico magia con coste

**Prioridad:** P1  
**Actor:** SEARCH-CONSOLE + HUMAN

Revisar recommendation vs Noveris/worldbuilding vs retired page.

No reindexar retired page sin decisión editorial.

---

## SEO-024 — Diagnóstico herramientas

**Prioridad:** P1  
**Actor:** SEARCH-CONSOLE

Top queries por tool y hubs.

Detectar si hub compite con tool para query específica.

---

## SEO-025 — Grafo de enlaces internos

**Prioridad:** P1  
**Actor:** REPO

Crear `scripts/seo/build-link-graph.py` sobre public dist.

Por URL:

- depth home;
- depth hub;
- inbound count;
- anchors;
- outbound;
- parent/hub.

---

## SEO-026 — Flag orphan/near-orphan

**Prioridad:** P1  
**Actor:** REPO  
**Depende:** SEO-025

Flag, no auto-link.

---

## SEO-027 — Link a noindex/redirect/404 report

**Prioridad:** P1  
**Actor:** REPO

Reutilizar broken-links workflow cuando sea posible; añadir semántica de registry.

---

## SEO-028 — Inbound links para books

**Prioridad:** P1  
**Actor:** REPO/HUMAN

Samuel/Manecillas deben recibir enlaces naturales desde:

- Obras;
- Autor;
- artículos pertinentes;
- eventos pertinentes;
- recomendaciones cuando corresponda.

No insertarlos en cada página.

---

## SEO-029 — Interlinking Cuaderno topics

**Prioridad:** P1  
**Actor:** REPO/HUMAN

Asegurar:

`hub → topic → article`

y article→topic/hub cuando útil.

---

## SEO-030 — Tool journey links

**Prioridad:** P1  
**Actor:** REPO/HUMAN

Enlazar siguientes herramientas por tarea real, no listado completo.

---

# Fase 3 — SERP / titles / snippets

## SEO-031 — Inventario titles/H1/descriptions

**Prioridad:** P1  
**Actor:** REPO

Generar reporte automático por public dist.

Flags:

- missing;
- duplicate exact;
- title==boilerplate suspicious;
- multiple H1 only if structural issue;
- missing description priority pages.

No aplicar límites rígidos de caracteres como error.

---

## SEO-032 — Capturar Google shown titles de URLs top

**Prioridad:** P1  
**Actor:** HUMAN/SEARCH-CONSOLE

Prioridad:

- home;
- autor;
- books;
- top articles;
- top tools.

Manual/neutral evidence; no scraping agresivo.

---

## SEO-033 — Title experiment backlog

**Prioridad:** P1  
**Actor:** SEARCH-CONSOLE/HUMAN

Elegir solo páginas con impressions suficientes.

No cambiar toda la web.

---

## SEO-034 — Mejorar tool titles donde los datos lo justifiquen

**Prioridad:** P1  
**Actor:** REPO + SEARCH-CONSOLE  
**Depende:** SEO-033

Una PR por cohorte pequeña.

---

## SEO-035 — Snippet stale-fact audit

**Prioridad:** P0/P1  
**Actor:** HUMAN

Buscar:

- Samuel 2026;
- Manecillas prelaunch/outdated;
- old contact;
- old title.

Registrar y cerrar.

---

## SEO-036 — Evaluate `data-nosnippet`

**Prioridad:** P2  
**Actor:** HUMAN/REPO

Solo si Google extrae consistentemente newsletter/nav/disclaimer irrelevante.

No implementar preventivamente.

---

## SEO-037 — Sitelinks baseline

**Prioridad:** P2  
**Actor:** HUMAN

Query brand; registrar sitelinks actuales.

No intentar forzar.

---

## SEO-038 — Site name baseline

**Prioridad:** P2  
**Actor:** HUMAN

Confirmar si Google muestra `David Porto Díaz`.

Si no, revisar WebSite/name/heading consistency antes de añadir markup nuevo.

---

## SEO-039 — Favicon baseline

**Prioridad:** P2  
**Actor:** HUMAN/REPO

Confirmar resultado Search y crawlability.

---

# Fase 4 — Structured data

## SEO-040 — Audit all JSON-LD types

**Prioridad:** P1  
**Actor:** REPO

Crear `scripts/seo/audit-schema.py`.

Output types/ids/URLs/policy warnings.

---

## SEO-041 — Book factual parity

**Prioridad:** P1  
**Actor:** REPO

Assert Samuel/Manecillas:

- title;
- author;
- ISBN;
- publisher;
- date;
- pages.

Reuse editorial facts tests.

---

## SEO-042 — Offer guardrail

**Prioridad:** P1  
**Actor:** REPO

Fail if Manecillas gains Offer without verified commercial fact.

Samuel retailer links ≠ own Offer.

---

## SEO-043 — FAQPage debt inventory

**Prioridad:** P2  
**Actor:** REPO

List pages still emitting FAQPage.

Decide remove/keep for non-Google consumers.

No expand.

---

## SEO-044 — Remove FAQPage where no consumer needs it

**Prioridad:** P2  
**Actor:** REPO  
**Depende:** SEO-043

Keep visible FAQ content.

---

## SEO-045 — Event page template

**Prioridad:** P1  
**Actor:** REPO

Design future `/eventos/<slug>/` family.

No publish fake event.

Fields/schema per doc 06.

---

## SEO-046 — Event detail registry support

**Prioridad:** P1  
**Actor:** REPO

Add content-registry type/territory/parent pattern for future event pages.

---

## SEO-047 — Rich Results Test P0 manual

**Prioridad:** P0  
**Actor:** HUMAN

After Samuel schema fix, test URL/code.

Save result summary in PR/issue, no screenshots with private data.

---

## SEO-048 — SoftwareApplication validation sample

**Prioridad:** P2  
**Actor:** HUMAN/REPO

Validate representative tools against current Google type docs.

Do not add fake ratings/prices.

---

# Fase 5 — Content portfolio

## SEO-049 — People-first content brief template

**Prioridad:** P1  
**Actor:** REPO

Create reusable `docs/templates/seo-content-brief.md` or integrate existing editorial workflow.

Fields from doc 04.

---

## SEO-050 — New-content duplicate-intent gate

**Prioridad:** P1  
**Actor:** REPO

Before adding registry public article:

- require parent/hub;
- query role;
- reason new URL needed.

Do not require keyword volume.

---

## SEO-051 — Directory index quality gate

**Prioridad:** P1  
**Actor:** REPO/EDITORIAL

For editorial entity pages require factual minimum before `searchIndex/sitemap=true`.

---

## SEO-052 — `verifiedAt` freshness policy

**Prioridad:** P1  
**Actor:** EDITORIAL/REPO

Define expiry/review windows per data type.

Do not automatically noindex because date passes; flag for review.

---

## SEO-053 — Convocations expiry lifecycle

**Prioridad:** P1  
**Actor:** REPO/EDITORIAL

Define:

- open;
- closed;
- archive;
- noindex/redirect/retain.

Avoid stale «open» claims.

---

## SEO-054 — Recommendations methodology

**Prioridad:** P1  
**Actor:** HUMAN/EDITORIAL

Document selection criteria and relationship to own books.

---

## SEO-055 — Recommendation independence test

**Prioridad:** P1  
**Actor:** HUMAN

Review pages mentally without Samuel.

If useless, rewrite before promotion.

---

## SEO-056 — Portal fantasy content gap review

**Prioridad:** P2  
**Actor:** HUMAN/SEARCH-CONSOLE

Identify real unanswered jobs from queries; no page-per-PAA.

---

## SEO-057 — Noveris first-party content plan

**Prioridad:** P1  
**Actor:** EDITORIAL

Prioritize only canonical/public material.

No spoilers/internal lore unsupported.

---

## SEO-058 — Manecillas first-party editorial plan

**Prioridad:** P1  
**Actor:** EDITORIAL

Potential:

- novel-coral process;
- object/time structure;
- author notes;
- launch experience;
- club guide.

Publish only real material.

---

## SEO-059 — Tool methodology audit

**Prioridad:** P1  
**Actor:** HUMAN/REPO

Every indexable tool should have:

- what it does;
- methodology/limits;
- privacy;
- next action.

---

## SEO-060 — Tool misleading-functionality test

**Prioridad:** P1  
**Actor:** REPO

Smoke representative tools; no indexable tool should promise function unavailable in production.

Reuse tool tests.

---

# Fase 6 — Images / Discover / video

## SEO-061 — Media audit script

**Prioridad:** P1  
**Actor:** REPO

Create `scripts/seo/audit-media.py`.

Report:

- hero;
- `<img>`;
- dimensions;
- alt;
- srcset;
- lazy;
- OG/schema image;
- Discover large-image candidate.

---

## SEO-062 — Author image consistency

**Prioridad:** P2  
**Actor:** HUMAN/EXTERNAL

Review major profiles; use official current portrait when appropriate.

No require exact same image everywhere.

---

## SEO-063 — Book cover image audit

**Prioridad:** P1  
**Actor:** REPO

Ensure Book.image/OG/visible cover all point to valid public assets and correct book.

---

## SEO-064 — Discover image candidates

**Prioridad:** P1  
**Actor:** REPO/HUMAN

For key editorial articles:

- >=1200px when possible;
- meaningful horizontal crop;
- large preview enabled.

---

## SEO-065 — Discover report separated

**Prioridad:** P2  
**Actor:** SEARCH-CONSOLE

If report exists, monitor separately from Web.

---

## SEO-066 — Google News eligibility reality check

**Prioridad:** P2  
**Actor:** HUMAN

No Publisher Center submission task.

Review whether Cuaderno actually publishes news-like content.

---

## SEO-067 — Video strategy gate

**Prioridad:** P2  
**Actor:** HUMAN/EDITORIAL

Decide whether real video pipeline exists.

If no, status `DEFER`.

---

## SEO-068 — Video page template

**Prioridad:** P3  
**Actor:** REPO  
**Depende:** SEO-067=yes

Dedicated watch page + transcript + VideoObject.

---

## SEO-069 — Image sitemap evaluation

**Prioridad:** P3  
**Actor:** SEARCH-CONSOLE/REPO

Only if Google Images discovery insufficient.

Do not build by default.

---

# Fase 7 — Performance / mobile

## SEO-070 — CWV field baseline

**Prioridad:** P1  
**Actor:** SEARCH-CONSOLE

Record mobile/desktop groups:

- Good;
- Needs improvement;
- Poor.

---

## SEO-071 — Map CWV groups to templates

**Prioridad:** P1  
**Actor:** REPO + SEARCH-CONSOLE

Identify family root cause, not one URL patch.

---

## SEO-072 — LCP hero audit

**Prioridad:** P1  
**Actor:** REPO

Home/books/author/articles.

Check:

- no lazy LCP;
- fetchpriority;
- dimensions;
- responsive source.

---

## SEO-073 — INP tool stress test

**Prioridad:** P2  
**Actor:** REPO

Large text in analyzers; identify main-thread blocking.

---

## SEO-074 — CLS dynamic components audit

**Prioridad:** P1  
**Actor:** REPO

Newsletter, assistant, images, banners.

---

## SEO-075 — Newsletter interstitial mobile review

**Prioridad:** P1  
**Actor:** HUMAN/REPO

Confirm not intrusive/immediate/blocking.

---

## SEO-076 — Mobile factual parity test

**Prioridad:** P1  
**Actor:** REPO

Ensure responsive CSS/JS doesn't omit critical book/author facts or internal links.

---

## SEO-077 — Service worker stale-fact review

**Prioridad:** P1  
**Actor:** REPO

Critical book/page HTML must not remain stale excessively after deploy.

---

## SEO-078 — Live cache header audit

**Prioridad:** P2  
**Actor:** CLOUDFLARE/HUMAN

HTML vs immutable assets.

No changes without explicit auth.

---

# Fase 8 — Authority / external footprint

## SEO-079 — External profile parity audit David

**Prioridad:** P1  
**Actor:** EXTERNAL/HUMAN

Wikidata, ORCID, Author Central, Goodreads, Babelio, StoryGraph, social.

Fields:

- name;
- bio;
- photo;
- books;
- ISBN;
- URLs.

---

## SEO-080 — Samuel external footprint audit

**Prioridad:** P2  
**Actor:** HUMAN

Check links in `sameAs` still resolve and facts consistent.

---

## SEO-081 — Manecillas external footprint checklist

**Prioridad:** P1  
**Actor:** EDITORIAL/HUMAN

Execute only when sources exist after launch.

---

## SEO-082 — Monza page verification

**Prioridad:** P1  
**Actor:** EDITORIAL/EXTERNAL

After publisher listing exists, verify ISBN/date/cover/title.

Do not invent URL before it exists.

---

## SEO-083 — Retailer parity Manecillas

**Prioridad:** P1  
**Actor:** EDITORIAL/EXTERNAL

Only verified retailers; update canonical facts after evidence.

---

## SEO-084 — Goodreads/Open Library/LibraryThing Manecillas

**Prioridad:** P2  
**Actor:** HUMAN/EXTERNAL

Create/claim only within each platform rules and only one correct entity.

---

## SEO-085 — Press outreach asset audit

**Prioridad:** P1  
**Actor:** HUMAN

Press kit includes:

- fact sheet;
- bios;
- cover rights status;
- contact;
- URLs;
- no internal incident language.

---

## SEO-086 — Digital PR targets

**Prioridad:** P2  
**Actor:** HUMAN

Segment:

- literary media;
- local media;
- podcasts;
- bookstores;
- clubs;
- events.

No mass link-spam outreach.

---

## SEO-087 — Knowledge Panel check

**Prioridad:** P1  
**Actor:** HUMAN

Search neutral; record exists/not found.

---

## SEO-088 — Claim Knowledge Panel

**Prioridad:** P1 conditional  
**Actor:** GOOGLE-ACCOUNT/HUMAN  
**Depende:** SEO-087 = exists+claimable

Use official claim flow.

---

## SEO-089 — Knowledge Panel fact corrections

**Prioridad:** P1 conditional  
**Actor:** HUMAN  
**Depende:** panel claimed/feedback available

Only evidence-backed corrections.

---

## SEO-090 — Disavow gate

**Prioridad:** P3  
**Actor:** HUMAN

Default = do not use.

Open only if manual action/known large artificial link scheme.

---

# Fase 9 — Google products

## SEO-091 — Preferred Sources eligibility check

**Prioridad:** P1  
**Actor:** HUMAN

Check official source-preferences tool for domain.

Record yes/no.

---

## SEO-092 — Preferred Sources CTA design

**Prioridad:** P2 conditional  
**Actor:** REPO/HUMAN  
**Depende:** SEO-091=yes

Choose:

- official standard button;
- custom SDK;
- deeplink.

Prefer low-JS/deeplink if performance/CSP simplicity wins.

---

## SEO-093 — Preferred Sources CSP/perf review

**Prioridad:** P2  
**Actor:** REPO

If JS implementation, update CSP deliberately and measure third-party cost.

---

## SEO-094 — Google Trends research baseline

**Prioridad:** P2  
**Actor:** HUMAN

Create saved research notes for core clusters.

Remember 0–100 is relative.

---

## SEO-095 — Google Books presence Samuel

**Prioridad:** P1  
**Actor:** HUMAN/EDITORIAL

Check whether entry exists and who manages it.

No create account/upload without rights decision.

---

## SEO-096 — Google Books rights decision Samuel

**Prioridad:** P2  
**Actor:** EDITORIAL/HUMAN

Coordinate with Libros Indie/contract.

---

## SEO-097 — Google Books presence Manecillas

**Prioridad:** P1 post-launch  
**Actor:** HUMAN/EDITORIAL

Coordinate Monza.

---

## SEO-098 — Google Play Books commercial decision

**Prioridad:** P3  
**Actor:** EDITORIAL/HUMAN

Separate from web SEO.

---

## SEO-099 — Google Business Profile gate

**Prioridad:** N/A now  
**Actor:** HUMAN

Do not create unless business later becomes eligible under physical/service-area rules.

---

## SEO-100 — Merchant Center gate

**Prioridad:** N/A now  
**Actor:** HUMAN

No direct merchant/checkout → no setup.

---

# Fase 10 — Events

## SEO-101 — Future event URL policy

**Prioridad:** P1  
**Actor:** REPO/EDITORIAL

Any strategically important confirmed future event gets dedicated URL.

No page before event facts confirmed.

---

## SEO-102 — Event template schema tests

**Prioridad:** P1  
**Actor:** REPO

Required visible/schema fields.

---

## SEO-103 — Event hub links

**Prioridad:** P1  
**Actor:** REPO

Hub links detail; detail links hub/book/author.

---

## SEO-104 — Event completion lifecycle

**Prioridad:** P1  
**Actor:** REPO/EDITORIAL

After event:

- completed;
- archive content/photos if valuable;
- retain or 404 based on value.

No fake future date refresh.

---

# Fase 11 — Measurement / experiments

## SEO-105 — SEO change log

**Prioridad:** P1  
**Actor:** REPO

Create `data/seo-change-log.json` or equivalent.

Only material Search changes.

---

## SEO-106 — Google update registry

**Prioridad:** P1  
**Actor:** REPO

Create `data/seo-google-updates.json` seeded with official 2026 events.

No rumors.

---

## SEO-107 — Search Console annotations workflow

**Prioridad:** P1  
**Actor:** SEARCH-CONSOLE/HUMAN

Annotate material releases if feature available.

---

## SEO-108 — Experiment template

**Prioridad:** P1  
**Actor:** REPO

Versioned hypothesis/window/metrics/result.

---

## SEO-109 — First title experiment

**Prioridad:** P2  
**Actor:** SEARCH-CONSOLE + REPO

Choose after enough baseline data, not arbitrary URL.

---

## SEO-110 — First internal-link experiment

**Prioridad:** P2  
**Actor:** SEARCH-CONSOLE + REPO

Candidate page position 8–20 + few relevant inbound links.

---

## SEO-111 — Monthly SEO report

**Prioridad:** P1  
**Actor:** HUMAN/AUTOMATION

One-page summary + appendix.

Do not make it a 100-metric dashboard.

---

## SEO-112 — Traffic drop runbook implementation

**Prioridad:** P1  
**Actor:** HUMAN

Use decision tree doc 10 before changes.

---

## SEO-113 — Core update protocol

**Prioridad:** P1  
**Actor:** HUMAN

No day-one panic changes.

---

## SEO-114 — Spam update protocol

**Prioridad:** P1  
**Actor:** HUMAN

Review policies/directories/links/schema if material loss.

---

# Fase 12 — Automation / CI

## SEO-115 — `scripts/seo/` package directory

**Prioridad:** P1  
**Actor:** REPO

Add README with read-only/deterministic conventions.

No network in CI unless explicit workflow.

---

## SEO-116 — Unified SEO audit command

**Prioridad:** P2  
**Actor:** REPO

Possible:

`python scripts/seo/audit-site.py --dist .preview-dist`

Combines reports, does not rewrite.

---

## SEO-117 — Machine-readable report artifact

**Prioridad:** P2  
**Actor:** REPO

JSON output for future dashboards.

Exclude PII/secrets.

---

## SEO-118 — Human-readable Markdown report

**Prioridad:** P2  
**Actor:** REPO

Summarize actionable violations/warnings.

---

## SEO-119 — CI workflow `google-seo-contract.yml`

**Prioridad:** P1  
**Actor:** REPO

Run on relevant changes.

Checks:

- indexability contract;
- sitemap;
- schema policy;
- query-role registry parity if adopted.

Do not run Lighthouse again.

---

## SEO-120 — Avoid CI path blind spots

**Prioridad:** P1  
**Actor:** REPO

If output can change from shared generator/data, workflow triggers must include those sources or run broadly on PR.

---

## SEO-121 — No network dependency for core contract

**Prioridad:** P1  
**Actor:** REPO

Official policy URLs are documentation, not CI dependencies.

---

## SEO-122 — Public artifact SEO audit

**Prioridad:** P1  
**Actor:** REPO

Audit built artifact, not repository source alone.

---

## SEO-123 — Content registry/schema contract

**Prioridad:** P1  
**Actor:** REPO

Ensure registry sourceFile/public state aligns with built page meta.

---

## SEO-124 — Test no gated/noindex in sitemap

**Prioridad:** P1  
**Actor:** REPO

Explicit regression test.

---

## SEO-125 — Test no fragment loc in sitemap

**Prioridad:** P1  
**Actor:** REPO

Memoria internal fragment remains non-sitemap.

---

## SEO-126 — Test canonical absolute HTTPS

**Prioridad:** P1  
**Actor:** REPO

For indexable pages.

---

## SEO-127 — Test no meta keywords introduced

**Prioridad:** P3  
**Actor:** REPO

Optional lint warning, not critical failure if another standard needs it; no current need.

---

## SEO-128 — Test no fake Offer

**Prioridad:** P1  
**Actor:** REPO

Reuse editorial facts.

---

## SEO-129 — Test no third-party aggregateRating

**Prioridad:** P0  
**Actor:** REPO

Part of SEO-002.

---

## SEO-130 — Test event unique URL in future template

**Prioridad:** P1  
**Actor:** REPO

Do not fail historical hub objects until migration decision; apply to new detail family.

---

# Fase 13 — Editorial operations

## SEO-131 — SEO review in publish checklist

**Prioridad:** P1  
**Actor:** HUMAN/REPO

For new indexable page:

- intent;
- owner;
- title/H1;
- canonical;
- hub/internal links;
- sources;
- index status;
- image;
- schema if legitimate.

---

## SEO-132 — No keyword quota in briefs

**Prioridad:** policy  
**Actor:** HUMAN

Ban density/mandatory repetitions.

---

## SEO-133 — No arbitrary word-count requirement

**Prioridad:** policy  
**Actor:** HUMAN

Length follows task.

---

## SEO-134 — Honest date policy

**Prioridad:** P1  
**Actor:** HUMAN/REPO

Document what qualifies as material update.

---

## SEO-135 — AI-assisted content disclosure/process decision

**Prioridad:** P2  
**Actor:** HUMAN

Define internal use, fact-checking and review. Google does not require a generic disclosure just because AI assisted, but transparency about how content was created can be useful when users reasonably expect it.

No blanket badge unless editorially useful.

---

## SEO-136 — External source hierarchy

**Prioridad:** P1  
**Actor:** HUMAN

Primary sources first for factual directories/articles.

---

## SEO-137 — Corrections mechanism

**Prioridad:** P2  
**Actor:** HUMAN/REPO

For directories/factual resources, provide simple way to report outdated info when useful.

---

## SEO-138 — Editorial review of `hasCredential`

**Prioridad:** P2  
**Actor:** HUMAN

Confirm `Marketing Online` credential on Person is true/public/useful; remove if it adds noise or cannot be substantiated.

Do not equate it to literary expertise.

---

# Fase 14 — Launch / Manecillas

## SEO-139 — Pre-03/09 Search baseline

**Prioridad:** P1  
**Actor:** SEARCH-CONSOLE/HUMAN

Capture:

- indexed state;
- impressions;
- title queries;
- current snippet;
- image presence.

---

## SEO-140 — 03/09 production facts verification

**Prioridad:** P0 launch  
**Actor:** HUMAN/EDITORIAL

After release actions:

- publication wording;
- retailer only if verified;
- ISBN;
- Monza;
- price vs offer distinction.

---

## SEO-141 — Post-launch recrawl

**Prioridad:** P1  
**Actor:** SEARCH-CONSOLE

Inspect/request critical URL once after actual production change.

---

## SEO-142 — Post-launch external footprint

**Prioridad:** P1  
**Actor:** EDITORIAL/EXTERNAL

See SEO-081–084.

---

## SEO-143 — Post-launch event pages

**Prioridad:** conditional  
**Actor:** REPO/EDITORIAL

Only confirmed events.

---

## SEO-144 — Post-launch article opportunities

**Prioridad:** P2  
**Actor:** EDITORIAL

First-party launch/process only, not 20 keyword pages around title.

---

# Fase 15 — Review after implementation

## SEO-145 — Full public artifact build

**Actor:** REPO

Run existing build + SEO contract.

---

## SEO-146 — Existing CI

Require applicable workflows green:

- Public artifact contract;
- global discoverability;
- content indexes;
- broken links;
- Lighthouse;
- accessibility;
- CSP;
- runtime scoping;
- machine authority;
- relevant browser QA.

Do not dismiss failure as flaky without logs.

---

## SEO-147 — Manual diff review

Verify no runtime file changed unintentionally in documentation-only PR.

For implementation PRs, review only intended paths.

---

## SEO-148 — Production smoke after authorized deploy

Critical pages/status/meta/schema.

---

## SEO-149 — Search Console verification

Index/canonical/enhancement where relevant.

---

## SEO-150 — Close backlog with evidence

A task is not `DONE` because code exists.

States:

- `TODO`;
- `IN PROGRESS`;
- `CODE COMPLETE`;
- `DEPLOYED`;
- `VERIFIED LIVE`;
- `VERIFIED SEARCH`;
- `N/A`;
- `DEFER`.

Use the level appropriate to the task.

---

# Recommended Claude execution order

1. Rebase/resync branch with latest `main`.
2. Read README + docs 01, 02, 06, 12, 13.
3. Implement **SEO-001 + SEO-002** first.
4. Run all existing factual/machine tests.
5. Implement sitemap/canonical contract SEO-008–014.
6. Implement schema audit SEO-040–042.
7. Build link graph/query role infrastructure SEO-019/025–027.
8. Add unified SEO CI without duplicating Lighthouse.
9. Do not implement Search Console/account tasks without access/authorization.
10. Hand user a checklist for SEO-003–007 and account/live gates.
11. Then work content/architecture P1 based on actual Search Console data.
12. Preferred Sources/Google Books only after explicit eligibility/rights check.
13. Event detail code can be prepared, but no fake event page.
14. Merge implementation only when CI + factual review is green.

---

# Minimum commands after implementation

Exact scripts may change, but target command set:

```bash
python scripts/build-public-dist.py
python scripts/build-public-dist.py --check-contents .preview-dist
python tests/test-public-artifact-contract.py
python tests/test-machine-authority.py
python tests/test-google-structured-data-policy.py
python tests/test-seo-indexability-contract.py
python scripts/seo/audit-indexability.py --dist .preview-dist
python scripts/seo/audit-schema.py --dist .preview-dist
python scripts/seo/build-link-graph.py --dist .preview-dist
```

Do not invent a command in CI until its script exists.

---

# Definition of Done del programa SEO

No significa «posición 1».

Significa:

- P0 compliance cerrado;
- facts stale conocidos corregidos en Search;
- sitemap/canonical/indexability contract automatizado;
- lastmod fiable;
- query roles completos;
- internal graph auditable;
- pages-per-keyword bloqueadas por proceso;
- structured data factual y policy-safe;
- events futuros con arquitectura correcta;
- images/Discover preparados donde tenga sentido;
- CWV field monitored;
- external entity profiles coherentes;
- Manecillas con footprint real post-launch;
- Knowledge Panel/Preferred Sources/Google Books evaluados con gates reales;
- experiments medidos;
- updates anotados;
- no spam patterns;
- Claude puede continuar sin depender de este chat.
