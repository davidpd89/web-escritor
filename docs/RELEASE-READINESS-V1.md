# Release Readiness Evidence (Static Preflight Gate)

- Generated: `2026-09-30T11:27:25.087422+00:00`
- Branch: `fix/qa-hardening-mutation-journeys-supplychain`
- HEAD: `53741feb4947c6b7e1c8fa2b6a73bb39a7bd4484`
- Previous SHA (rollback candidate): `6a6a09eb2e60b105d667cf8388314a4a0facdbe2`

## Status: `STATIC_CHECKS_PASSED`

> **Este informe certifica el estado STATIC_CHECKS_PASSED.**
>
> Cubre las comprobaciones estáticas, de paridad, unitarias y contratos locales
> headless. No sustituye la ejecución completa de los gates requeridos de CI
> (Lighthouse, Pa11y, sitewide browser suites) ni el smoke post-despliegue en producción.
> El ciclo completo de release exige: `STATIC_CHECKS_PASSED` -> `CI_REQUIRED_GATES_PASSED` -> `PRODUCTION_VERIFIED`.

## Commit Window (latest 20)

```text
53741feb fix(qa): relocate browser suites to qa/, normalize sample generator newlines and sync release readiness
6a6a09eb feat(qa): harden mutation tests, supply-chain baseline, user journeys, keyboard resize and DOM integrity
03acd591 docs: sync release-readiness report for merged main
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
| SEO: meta quality & collision prevention | `python scripts/check-seo-meta-quality.py` | `PASS` |
| SEO: meta quality mutation tests | `python tests/test-seo-meta-quality.py` | `PASS` |
| DOM: integrity & ARIA resolution | `python scripts/check-dom-integrity.py` | `PASS` |
| DOM: integrity mutation tests | `python tests/test-dom-integrity.py` | `PASS` |
| Supply chain: baseline & zero prod vulns | `python tests/test-npm-supply-chain-baseline.py` | `PASS` |

## Output Excerpts

### CI parity: content indexes — PASS

```text
Local asset check: 100 HTML files scanned; 0 broken local reference(s) (including 0 JS reference target(s) and 0 CSS url() target(s)).
```

### CI parity: hrefs — PASS

```text
HREF-OK
```

### CI parity: internal graph — PASS

```text
INTERNAL GRAPH REPORT
Files scanned: 96
Indexable pages: 62

INFO (1):
  [noindex-skipped] 34 pages excluded (noindex): aviso-legal.html, privacidad.html, samuel-entre-mundos.html, asistente\embed.html, asistente\index.html, donde-empieza-la-jaula\index.html, gracias-suscripcion\index.html, lecturas\index.html �

Summary: 0 error(s), 0 warning(s)
```

### CI parity: navigation coverage — PASS

```text
PASS: navigation coverage (69 registry routes, 62 sitemap routes, 22 interactive tools)
```

### CI parity: heading structure — PASS

```text
Heading/skip-link structure: 80 ficheros HTML revisados; 0 problema(s).
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
NOTICE  shared article card used by 7 pages: https://davidportodiaz.com/assets/og-worldbuilding-noveris-ciudad-fantastica.jpg :: cuaderno/fantasia-juvenil-espanola-portales-magia-coste/index.html, cuaderno/libros-fantasia-juvenil-espanola-2025-2026/index.html, cuaderno/portal-fantasy-vs-fantasia-epica/index.html, cuaderno/que-es-el-portal-fantasy/index.html, cuaderno/worldbuilding-noveris-ciudad-magica/index.html, recomendaciones/magia-con-coste/index.html, recomendaciones/portal-fantasy-espanol/index.html
Social cards: 62 indexable HTML pages; 0 error(s), 0 warning(s), 1 notice(s).
```

### CI parity: copy tildes — PASS

```text
COPY TILDES: OK (183 ficheros HTML/JS revisados)
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
ok   evento-escritor-core.js generator exits 0 (stderr: (node:13316) [MODULE_TYPELESS_PACKAGE_JSON] Warning: Module type of file:///C:/GIT/web-escritor/assets/evento-escritor-core.js is not specified and it doesn't parse as CommonJS.
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
BUILT C:\GIT\web-escritor\.preview-dist-sitewide-qa: 428 file(s) included, 1363 excluded; manifest=.preview-dist-sitewide-qa-manifest.json
OK: C:\GIT\web-escritor\.preview-dist-sitewide-qa satisfies the allowlist-first public-artifact contract (428 files).
Auditing SEO & Schema on 73 published HTML pages...
SEO & Schema Smoke: 890/890 assertions passed.
ALL SEO & DISCOVERABILITY CHECKS PASSED 100%!
```

### SEO: meta quality & collision prevention — PASS

```text
OK — Sitewide SEO meta quality, uniqueness, canonical and OG parity verified.
```

### SEO: meta quality mutation tests — PASS

```text
ok   1. Current repository satisfies all SEO meta quality and uniqueness contracts
  ok   2. Clean mock dataset passes check_seo_meta_quality with 0 errors
  ok   3. Mutation test: duplicate <title> caught and rejected
  ok   4. Mutation test: duplicate meta description caught and rejected
  ok   5. Mutation test: multiple canonical tags caught and rejected
  ok   6. Mutation test: canonical route mismatch caught and rejected
  ok   7. Mutation test: og:url != canonical caught and rejected
  ok   8. Mutation test: missing title and description caught and rejected
test-seo-meta-quality: OK
```

### DOM: integrity & ARIA resolution — PASS

```text
OK — DOM integrity verified sitewide (IDs unique, ARIA/label references valid, no invalid interactive nesting).
```

### DOM: integrity mutation tests — PASS

```text
ok   1. Current repository satisfies all DOM integrity contracts
  ok   2. Mutation test: duplicate ID detected
  ok   3. Mutation test: broken label[for] detected
  ok   4. Mutation test: broken aria reference detected
  ok   5. Mutation test: invalid interactive nesting (<button> in <a>) detected
  ok   6. Mutation test: invalid interactive nesting (<select> in <button>) detected
  ok   7. Mutation test: broken aria-owns detected
test-dom-integrity: OK
```

### Supply chain: baseline & zero prod vulns — PASS

```text
ok   1. Production supply-chain has 0 vulnerabilities (npm audit --omit=dev)
  ok   2. All 18 dev supply-chain advisories match live npm audit exactly
test-npm-supply-chain-baseline: OK
```

## Rollback Procedure (Documented, not executed)

1. Identify incident and freeze merges.
2. Checkout rollback target SHA: `6a6a09eb2e60b105d667cf8388314a4a0facdbe2`.
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
