# Release Readiness Evidence V1

- Generated: `2026-09-30T09:24:18.914303+00:00`
- Branch: `main`
- HEAD: `e8172f60a1d08fa156b6ef352543d0dd3979fa97`
- Previous SHA (rollback candidate): `0add07afac431e66ba9662ddf7eb5cc540a31710`

## Final Status: `STATIC_CHECKS_PASSED`

> **Este informe NO autoriza el merge a `main` ni el despliegue.**
>
> Cubre comprobaciones estaticas y el inventario de rutas. **No** ejecuta:
> los 12 suites de QA de navegador, Lighthouse, pa11y/WCAG2AA, el gate de
> reflow (zoom 200 % y text-spacing), no-JS, ni teclado. `STATIC_CHECKS_PASSED`
> significa exactamente lo que dice: las comprobaciones de esta tabla pasan.
> La evidencia completa la produce la tarea de release readiness v2 sobre un
> HEAD fresco, y la decision de promocionar a produccion es humana.

## Commit Window (latest 20)

```text
e8172f60 feat(qa): add supply-chain baseline, SEO collision checker, DOM integrity suite, search benchmark and core user journeys
0add07af docs(sync): update editorial facts review dates, sync machine-readable files and rebuild feed.xml
11a3b852 fix(analytics): unblock Clarity session capture with granted default and immediate implicit consent
260f5f65 test(qa): add cross-device and SEO smoke tests, update radar dataset and harden CI parity
4943b841 seo(structured-data): add missing BreadcrumbList JSON-LD to 27 published pages (#527)
4dacaed8 fix(qa): extend asset-version checker to cover JS-side dynamic/static imports (#526)
76317a8e perf(home): re-encode intro poster to WebP, real ~224ms LCP improvement (#525)
881d1f40 fix(qa): make production-analytics-smoke actually assert (was log-only) (#524)
ddcaf599 docs(qa): record 25x CI hunt evidence for the /autor.html @768 CLS flake (#523)
7e824251 test(qa): add manual production analytics smoke (positive-case, on-demand) (#522)
4d6a226a test(qa): add sitewide zero-console-errors crawl audit (#521)
efbdb5ca fix(analytics): close production-hostname guard gaps (staging, legacy tags, Clarity fallback) (#520)
7254d9f9 fix(analytics): also block Clarity/GoatCounter/Metricool on file:// opens (#518)
4022692f perf(lcp): defer Clarity's injection off the LCP-critical main thread (#519)
a17e8fd9 content(prensa): add Praza Pública opinion piece (#517)
d0788680 fix(analytics): stop GoatCounter/Metricool/Clarity from firing on localhost (#516)
ffa68c29 fix(seo): add ProfilePage dateCreated, drop invalid ItemList.dateModified (#515)
b2744a43 fix(security): add explicit Referrer-Policy meta tag sitewide (#513)
e5e0af10 fix(seo): correct press-mention JSON-LD authorship and add headline (#514)
1973e4c4 fix(footer): WCAG 1.4.4 zoom overflow + revive 2 dead CI checks (#508)
```

## Required Route Inventory

| Route | Validation | Status |
|---|---|---|
| `/` | `sitemap` | `PASS` |
| `/las-manecillas-del-recuerdo/` | `sitemap` | `PASS` |
| `/libros/samuel-entre-mundos/` | `sitemap` | `PASS` |
| `/autor.html` | `sitemap` | `PASS` |
| `/cuaderno/` | `sitemap` | `PASS` |
| `/herramientas/` | `sitemap` | `PASS` |
| `/recomendaciones/` | `sitemap` | `PASS` |
| `/editoriales/` | `sitemap` | `PASS` |
| `/prensa.html` | `sitemap` | `PASS` |
| `/eventos.html` | `sitemap` | `PASS` |
| `/asistente/` | `file` | `PASS` |
| `/privacidad.html` | `file` | `PASS` |
| `/aviso-legal.html` | `file` | `PASS` |
| `/sitemap.xml` | `file` | `PASS` |
| `/llms.txt` | `file` | `PASS` |
| `/robots.txt` | `file` | `PASS` |

## Automated Evidence Checks

| Check | Command | Status |
|---|---|---|
| CI parity: content indexes | `python scripts/check-local-assets.py` | `PASS` |
| CI parity: hrefs | `python scripts/check-hrefs.py` | `PASS` |
| CI parity: internal graph | `python scripts/check-internal-graph.py` | `PASS` |
| CI parity: navigation coverage | `python scripts/check-navigation-coverage.py` | `PASS` |
| CI parity: heading structure | `python scripts/check-heading-structure.py` | `PASS` |
| CI parity: jsonld absolute URLs | `python scripts/check-jsonld-absolute-urls.py` | `PASS` |
| CI parity: canonical entity IDs | `python scripts/check-canonical-entity-ids.py` | `PASS` |
| CI parity: editorial facts | `python scripts/check-editorial-facts.py` | `PASS` |
| CI parity: AI discoverability | `python scripts/check-ai-discoverability.py` | `PASS` |
| CI parity: social cards strict | `python scripts/check-social-cards.py --strict` | `PASS` |
| CI parity: copy tildes | `python scripts/check-copy-tildes.py` | `PASS` |
| Authority: machine-readable contract | `python tests/test-machine-authority.py` | `PASS` |
| Builder parity: editoriales | `python tests/test-editoriales-builder-parity-v1.py` | `PASS` |
| Builder parity: convocatorias | `python tests/test-radar-builder-parity-v1.py` | `PASS` |
| Newsletter: client contract | `node tests/test-newsletter-client-contract.mjs` | `PASS` |
| Newsletter: worker contract | `node qa/newsletter-worker-contract.mjs` | `PASS` |
| Newsletter: staging gate | `node tests/test-staging-newsletter-disable.mjs` | `PASS` |
| Social card regression guard | `python tests/test-social-card-article-specific.py` | `PASS` |
| Smoke: sample build parity | `python tests/test-manecillas-sample-build.py` | `PASS` |
| Smoke: radar freshness real clock | `python tests/test-radar-freshness-real-clock.py` | `PASS` |
| Smoke: ICS RFC5545 roundtrip | `python tests/test-ics-roundtrip-independent-parser.py` | `PASS` |
| Smoke: SEO & discoverability sitewide | `node tests/test-seo-discoverability-smoke.mjs` | `PASS` |
| Smoke: cross-device multi-viewport | `node tests/test-cross-device-smoke.mjs` | `PASS` |
| SEO: meta quality & collision prevention | `python scripts/check-seo-meta-quality.py` | `PASS` |
| DOM: integrity & ARIA resolution | `python scripts/check-dom-integrity.py` | `PASS` |
| Supply chain: baseline & zero prod vulns | `python tests/test-npm-supply-chain-baseline.py` | `PASS` |
| Search: Pagefind relevance benchmark | `node tests/test-pagefind-search-relevance-benchmark.mjs` | `PASS` |
| Journeys: Core end-to-end user flows | `node tests/test-core-user-journeys.mjs` | `PASS` |

## Output Excerpts

### CI parity: content indexes — PASS

```text
Local asset check: 173 HTML files scanned; 0 broken local reference(s) (including 0 JS reference target(s) and 0 CSS url() target(s)).
```

### CI parity: hrefs — PASS

```text
HREF-OK
```

### CI parity: internal graph — PASS

```text
INTERNAL GRAPH REPORT
Files scanned: 167
Indexable pages: 62

INFO (1):
  [noindex-skipped] 43 pages excluded (noindex): aviso-legal.html, privacidad.html, samuel-entre-mundos.html, .preview-dist-sitewide-qa\aviso-legal.html, .preview-dist-sitewide-qa\privacidad.html, .preview-dist-sitewide-qa\samuel-entre-mundos.html, asistente\embed.html, asistente\index.html �

Summary: 0 error(s), 0 warning(s)
```

### CI parity: navigation coverage — PASS

```text
PASS: navigation coverage (69 registry routes, 62 sitemap routes, 22 interactive tools)
```

### CI parity: heading structure — PASS

```text
Heading/skip-link structure: 153 ficheros HTML revisados; 0 problema(s).
```

### CI parity: jsonld absolute URLs — PASS

```text
OK � 72 page(s) with JSON-LD checked, all url/@id/isPartOf/about/mainEntity/isBasedOn references are absolute.
```

### CI parity: canonical entity IDs — PASS

```text
CANONICAL ENTITY IDs: OK (4 entidades con @id, todas consistentes)
```

### CI parity: editorial facts — PASS

```text
EDITORIAL FACT CHECK � mode=launch � date=2026-09-30 � publication=2026-09-03
EDITORIAL FACT CHECK: OK
```

### CI parity: AI discoverability — PASS

```text
[OK] Canonical sitemap declared: https://davidportodiaz.com/sitemap.xml
[OK] OAI-SearchBot can crawl all key paths � ChatGPT Search indexing/search visibility
[OK] ChatGPT-User can crawl all key paths � ChatGPT user-directed fetches
[OK] Claude-SearchBot can crawl all key paths � Claude search visibility
[OK] Claude-User can crawl all key paths � Claude user-directed fetches
[OK] PerplexityBot can crawl all key paths � Perplexity search visibility
[OK] Googlebot can crawl all key paths � Google Search / AI features use Google Search index
[OK] bingbot can crawl all key paths � Bing/Copilot search index
[INFO] Training-policy bot GPTBot: allowed � OpenAI model-development crawling
[INFO] Training-policy bot ClaudeBot: allowed � Anthropic model-development crawling
[INFO] Training-policy bot Google-Extended: allowed � Google generative-AI training/grounding control, separate from Googlebot
... [truncated]
```

### CI parity: social cards strict — PASS

```text
NOTICE  shared article card used by 4 pages: https://davidportodiaz.com/assets/og-clubes-lectura-samuel-entre-mundos.jpg :: .preview-dist-sitewide-qa/clubes-de-lectura/samuel-entre-mundos/guia-imprimible/index.html, .preview-dist-sitewide-qa/clubes-de-lectura/samuel-entre-mundos/index.html, clubes-de-lectura/samuel-entre-mundos/guia-imprimible/index.html, clubes-de-lectura/samuel-entre-mundos/index.html
NOTICE  shared article card used by 14 pages: https://davidportodiaz.com/assets/og-worldbuilding-noveris-ciudad-fantastica.jpg :: .preview-dist-sitewide-qa/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/index.html, .preview-dist-sitewide-qa/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/index.html, .preview-dist-sitewide-qa/cuaderno/portal-fantasy-vs-fantasia-epica/index.html, .preview-dist-sitewide-qa/cuaderno/que-es-el-portal-fantasy/index.html, .preview-dist-sitewide-qa/c
... [truncated]
```

### CI parity: copy tildes — PASS

```text
COPY TILDES: OK (330 ficheros HTML/JS revisados)
```

### Authority: machine-readable contract — PASS

```text
PASS � machine authority contract (742 checks).
```

### Builder parity: editoriales — PASS

```text
tests/test-editoriales-builder-parity-v1
  ok   editoriales/index.html está sincronizado con el builder
  ok   editoriales/editoriales-data.json está sincronizado con el builder
  ok   editoriales-sitemap.xml está sincronizado con el builder
  ok   metodologia-editorial/index.html está sincronizado con el builder
  ok   editoriales/minotauro/index.html está sincronizado con el builder
  ok   editoriales/nocturna-ediciones/index.html está sincronizado con el builder
  ok   editoriales/duermevela-ediciones/index.html está sincronizado con el builder
  ok   el índice generado mantiene shell V1
  ok   el índice generado carga CSS V1
  ok   el índice generado no vuelve al CSS legacy
tests/test-editoriales-builder-parity-v1: OK
```

### Builder parity: convocatorias — PASS

```text
tests/test-radar-builder-parity-v1
  ok   convocatorias-escritores/index.html está sincronizado
  ok   convocatorias-escritores/opportunities.json está sincronizado
  ok   convocatorias-escritores/deadlines.ics está sincronizado
  ok   el HTML generado mantiene shell V1
  ok   el HTML generado carga CSS V1
  ok   el HTML generado no vuelve al CSS legacy
tests/test-radar-builder-parity-v1: OK
```

### Newsletter: client contract — PASS

```text
test-newsletter-client-contract: all assertions passed
```

### Newsletter: worker contract — PASS

```text
newsletter Worker contract: PASS
Worker misconfigured: BREVO_DOI_TEMPLATE_ID must be a positive integer
Worker misconfigured: BREVO_DOI_REDIRECT_URL must be a valid HTTPS URL
Worker misconfigured: BREVO_LIST_ID must be a positive integer
Worker misconfigured: BREVO_API_KEY missing
Brevo DOI error 400: {"message":"Contact already exists","email":"qa-newsletter@example.test"}
Brevo DOI error 500: secret upstream detail
```

### Newsletter: staging gate — PASS

```text
test-staging-newsletter-disable: all assertions passed
```

### Social card regression guard — PASS

```text
test-social-card-article-specific: OK (7 pages checked)
```

### Smoke: sample build parity — PASS

```text
test-manecillas-sample-build: OK
```

### Smoke: radar freshness real clock — PASS

```text
ok mutation: stale published dataset -> FAIL
ok mutation control: stale hidden item -> PASS
ok current: freshly verified dataset -> PASS
test-radar-freshness-real-clock: OK
```

### Smoke: ICS RFC5545 roundtrip — PASS

```text
ok   evento-escritor-core.js generator exits 0 (stderr: (node:54668) [MODULE_TYPELESS_PACKAGE_JSON] Warning: Module type of file:///C:/GIT/web-escritor/assets/evento-escritor-core.js is not specified and it doesn't parse as CommonJS.
Reparsing as ES module)
  ok   icalendar parses exactly 1 VEVENT from the event tool's ICS
  ok   SUMMARY round-trips with accents intact
  ok   DTSTART is 17:00 UTC per icalendar (got 2026-09-03 17:00:00+00:00)
  ok   folded DESCRIPTION unfolds correctly
  ok   event tool's JSON-LD re-parses with json.loads and keeps @type Event
  ok   JSON-LD nested address survives re-parse
  ok   icalendar parses 2 VEVENT(s) from the radar builder's ICS
  ok   the committed deadlines.ics parses with icalendar
tests/test-ics-roundtrip-independent-parser: OK
```

### Smoke: SEO & discoverability sitewide — PASS

```text
Auditing SEO & Schema on 73 published HTML pages...
SEO & Schema Smoke: 890/890 assertions passed.
ALL SEO & DISCOVERABILITY CHECKS PASSED 100%!
```

### Smoke: cross-device multi-viewport — PASS

```text
BUILT C:\GIT\web-escritor\.preview-dist-sitewide-qa: 428 file(s) included, 1363 excluded; manifest=.preview-dist-sitewide-qa-manifest.json
OK: C:\GIT\web-escritor\.preview-dist-sitewide-qa satisfies the allowlist-first public-artifact contract (428 files).
Cross-device smoke testing 31 routes across 10 viewports...
Testing No-JS fallback across core routes...

Results: 341 checks PASSED, 0 FAILED.
ALL CROSS-DEVICE SMOKE CHECKS PASSED 100%!
```

### SEO: meta quality & collision prevention — PASS

```text
OK — Sitewide SEO meta quality, uniqueness, canonical and OG parity verified.
```

### DOM: integrity & ARIA resolution — PASS

```text
OK — DOM integrity verified sitewide (IDs unique, ARIA/label references valid, no invalid interactive nesting).
```

### Supply chain: baseline & zero prod vulns — PASS

```text
ok   1. Production supply-chain has 0 vulnerabilities (npm audit --omit=dev)
  ok   2. All 27 dev supply-chain advisories are tracked in data/npm-supply-chain-baseline.json
test-npm-supply-chain-baseline: OK
```

### Search: Pagefind relevance benchmark — PASS

```text
test-pagefind-search-relevance-benchmark: PASS (11 human query patterns, zero-results and noindex exclusion)
```

### Journeys: Core end-to-end user flows — PASS

```text
ok   Journey 1: Home -> Las manecillas del recuerdo
  ok   Journey 2: Home -> Autor bio (/autor.html)
  ok   Journey 3: Home -> Fragmento / lectura de Manecillas
  ok   Journey 4: Cuaderno -> Lectura de artículo
  ok   Journey 5: Herramientas -> Contador de palabras interacción viva
  ok   Journey 7: Radar de convocatorias -> Filtro en vivo e interacción
test-core-user-journeys: OK (All 7 end-to-end user journeys verified)
```

## Rollback Procedure (Documented, not executed)

1. Identify incident and freeze merges.
2. Checkout rollback target SHA: `0add07afac431e66ba9662ddf7eb5cc540a31710`.
3. Re-run core checks:
```bash
python scripts/check-local-assets.py
python scripts/check-social-cards.py --strict
python scripts/check-ai-discoverability.py
python tests/test-machine-authority.py
```
4. Confirm route inventory and CI green before any promotion decision.

## Notes

- This report does not merge to main.
- This report does not deploy.
