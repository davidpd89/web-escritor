# Release Readiness Evidence (Static Preflight Gate)

- Generated: `2026-10-30T16:12:31.921214+00:00`
- Branch: `handoff/catalogue-page-url-parity-20261030`
- HEAD: `d0ba47dca11b921f5fa4d9ef0d9c9363293e5fbb`
- Previous SHA (rollback candidate): `2ccebd5fcd508472ba3511913026a32cd6bb3f1f`

## Status: `STATIC_CHECKS_PASSED`

> **Este informe certifica el estado STATIC_CHECKS_PASSED.**
>
> Cubre las comprobaciones estáticas, de paridad, unitarias y contratos locales
> headless. No sustituye la ejecución completa de los gates requeridos de CI
> (Lighthouse, Pa11y, sitewide browser suites) ni el smoke post-despliegue en producción.
> El ciclo completo de release exige: `STATIC_CHECKS_PASSED` -> `CI_REQUIRED_GATES_PASSED` -> `PRODUCTION_VERIFIED`.

## Commit Window (latest 20)

```text
d0ba47dca [ENCARGO P3] Catálogo: normalizar en la URL las páginas fuera de rango
2ccebd5fc docs: encargar paridad URL y paginacion del catalogo
c369f933e [ENCARGO P2] Homogeneizar tipografía de campos móviles y verificar Safari (#995)
7a92c9eed [ENCARGO P1] Pagefind: conservar el índice si falla su reconstrucción (#994)
2dc6804ce [ENCARGO P2] Preflight: no certificar éxito en informes BLOCKED (#996)
85a335e83 fix: close audit gaps in QA, newsletter accessibility and public metrics (#993)
c63bf1eed Rescatar correcciones QA pendientes: Noveris, publicar-web, contrato Atlas, Pagefind y kit de prensa (#991)
8a2898bfe Accesibilidad: contraste, impresión de Al otro lado, error del popup, aviso de copia y enlaces de compra (#992)
d0ef6ea78 Seguridad: CSP en el embed del asistente, en lecturas y completa en 8 herramientas (#990)
51877af7d Quitar el symlink node_modules y refrescar el radar a 2026-10-30 (#989)
20bdf5993 SEO: Article.image en cuatro artículos del Cuaderno y fediverse:creator en portada y novelas (#988)
f123ab78f Portada: salto al contenido bajo la introducción, ahorro de datos y AVIF de Samuel (#987)
59adf6220 Accesibilidad y SEO: 7 correcciones verificadas contra main (#986)
22171a7ea Mejoras del laboratorio verificadas contra main (13) (#985)
21820f26b fix(qa): la auditoría de producción no exige generated_for de ayer (#983)
3689c513d feat(apoyar): activar /apoyar/ con PayPal.me y Ko-fi, RRSS y Donar en cabecera, aviso de apoyo en el pie (#982)
69528da78 UX: pie Anterior · Índice · Siguiente en fichas hermanas (#980)
78e5fa6e2 Atlas: el alimentador de Wikidata respeta el límite de WDQS (plazo total y consultas por país) (#981)
3dfc3ae02 feat(atlas): catálogo filtrable (país, ciudad, tipo, vínculo, obra, autor) sobre el contrato de datos del Atlas (#977)
0fce702c1 Libros: conector editorial genérico (Anagrama y Nórdica) y reparto por turnos entre fuentes (#978)
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
| CI parity: Atlas pages | `python scripts/build-atlas-pages.py --data data/atlas/catalogue.json --root . --check` | `PASS` |
| CI parity: Atlas release contract | `python scripts/check_atlas_release_contract.py --root . --manifest data/atlas-routes-manifest.json` | `PASS` |
| CI parity: heading structure | `python scripts/check-heading-structure.py` | `PASS` |
| CI parity: public document/form contract | `python scripts/check-public-document-form-contract.py` | `PASS` |
| CI parity: jsonld absolute URLs | `python scripts/check-jsonld-absolute-urls.py` | `PASS` |
| CI parity: canonical entity IDs | `python scripts/check-canonical-entity-ids.py` | `PASS` |
| CI parity: Wikidata sameAs known-good | `python scripts/check-wikidata-sameas.py` | `PASS` |
| CI parity: editorial facts | `python scripts/check-editorial-facts.py` | `PASS` |
| CI parity: recommendations evidence | `python scripts/check-recommendations-evidence.py --check` | `PASS` |
| CI parity: Noveris editorial quarantine | `python scripts/check-noveris-magic-quarantine.py --check` | `PASS` |
| CI parity: public time semantics | `python scripts/check-public-time-semantics.py` | `PASS` |
| CI parity: article date and review lifecycle | `python scripts/check-article-dates.py --check` | `PASS` |
| CI parity: global discoverability | `python scripts/check-global-discoverability.py` | `PASS` |
| CI parity: AVIF/WebP format ladder | `python scripts/check-image-format-ladder.py --check` | `PASS` |
| CI parity: professional writer resources | `python scripts/check-professional-resources.py` | `PASS` |
| CI parity: AI discoverability | `python scripts/check-ai-discoverability.py` | `PASS` |
| CI parity: social cards strict | `python scripts/check-social-cards.py --strict` | `PASS` |
| CI parity: copy tildes | `python scripts/check-copy-tildes.py` | `PASS` |
| CI parity: head icon normalization | `python scripts/check-head-icons.py --check` | `PASS` |
| CI parity: head icon normalizer regression | `python tests/test-head-icon-normalizer.py` | `PASS` |
| CI parity: interaction a11y anti-patterns | `python scripts/check-interaction-a11y-contracts.py` | `PASS` |
| CI parity: radar clock projection | `python scripts/check-radar-clock-current.py` | `PASS` |
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
Local asset check: 470 HTML files scanned; 0 broken local reference(s) (including 0 JS reference target(s) and 0 CSS url() target(s)).
```

### CI parity: hrefs — PASS

```text
HREF-OK
```

### CI parity: internal graph — PASS

```text
INTERNAL GRAPH REPORT
Files scanned: 466
Indexable pages: 432

INFO (1):
  [noindex-skipped] 34 pages excluded (noindex): aviso-legal.html, privacidad.html, samuel-entre-mundos.html, asistente\embed.html, asistente\index.html, cuaderno\sistema-de-magia-noveris\index.html, donde-empieza-la-jaula\index.html, gracias-suscripcion\index.html …

Summary: 0 error(s), 0 warning(s)
```

### CI parity: navigation coverage — PASS

```text
PASS: navigation coverage (441 registry routes, 432 sitemap routes, 22 interactive tools)
```

### CI parity: Atlas pages — PASS

```text
PASS: 42 entradas en el catálogo, 18 fichas y hub, salida al día
```

### CI parity: Atlas release contract — PASS

```text
atlas-release-contract: 0 error(es)
```

### CI parity: heading structure — PASS

```text
Heading/skip-link structure: 450 ficheros HTML revisados; 0 problema(s).
```

### CI parity: public document/form contract — PASS

```text
PASS public document/form contract: 436 public HTML files
```

### CI parity: jsonld absolute URLs — PASS

```text
OK — 444 page(s) with JSON-LD checked, all url/@id/isPartOf/about/mainEntity/isBasedOn references are absolute.
```

### CI parity: canonical entity IDs — PASS

```text
CANONICAL ENTITY IDs: OK (204 entidades con @id, todas consistentes)
```

### CI parity: Wikidata sameAs known-good — PASS

```text
Found 6 distinct Wikidata QID(s) referenced in tracked HTML.

  Q119429258: OK (portal fantasy — fantasy fiction involving travel between universes) — index.html:190
  Q139678851: OK (David Porto Díaz — the author's own Wikidata item) — ai\index.html:138, autor.html:123, autor.html:507, index.html:203
  Q139915381: OK (Samuel entre mundos — the novel's work item; verified and corrected 2026-09-07 (publication year, stray genre and misattached award fixed)) — libros\samuel-entre-mundos\index.html:126
  Q139927664: OK (Noveris — fictional city in Samuel entre mundos (ES label only)) — ai\index.html:249, universo\noveris\index.html:97
  Q1822655: OK (worldbuilding — practice of constructing an imaginary world) — autor.html:117, index.html:192
  Q9326077: OK (speculative fiction — umbrella genre) — autor.html:116, index.html:191

OK — every referenced QID is in the verified table, none are k
... [truncated]
```

### CI parity: editorial facts — PASS

```text
EDITORIAL FACT CHECK · mode=launch · date=2026-10-30 · publication=2026-09-03
EDITORIAL FACT CHECK: OK
```

### CI parity: recommendations evidence — PASS

```text
Recommendations evidence check: 2 guia(s) revisada(s), 0 incumplimiento(s).
```

### CI parity: Noveris editorial quarantine — PASS

```text
Noveris magic quarantine check: 0 incumplimiento(s).
```

### CI parity: public time semantics — PASS

```text
PUBLIC TIME SEMANTICS: PASS (436 files, 672 <time> values, 460 JSON-LD blocks)
```

### CI parity: article date and review lifecycle — PASS

```text
PASS: article date/review lifecycle (6 Cuaderno articles, 0 scheduled reviews, 0 overdue, as-of 2026-10-30)
```

### CI parity: global discoverability — PASS

```text
PASS: global discoverability (477 tracked HTML artifacts; 432 indexable; search=IMPLEMENTADO; map=436 human destinations)
Inventory: artifacts\global-discoverability\inventory.json
```

### CI parity: AVIF/WebP format ladder — PASS

```text
Image format ladder check: 7 fuente(s) elegibles, 0 incumplimiento(s).
```

### CI parity: professional writer resources — PASS

```text
OK professional resources: data, detail coverage, generated outputs, real-clock freshness and ICS parity
```

### CI parity: AI discoverability — PASS

```text
[OK] Canonical sitemap declared: https://davidportodiaz.com/sitemap.xml
[OK] OAI-SearchBot can crawl all key paths — ChatGPT Search indexing/search visibility
[OK] ChatGPT-User can crawl all key paths — ChatGPT user-directed fetches
[OK] Claude-SearchBot can crawl all key paths — Claude search visibility
[OK] Claude-User can crawl all key paths — Claude user-directed fetches
[OK] PerplexityBot can crawl all key paths — Perplexity search visibility
[OK] Googlebot can crawl all key paths — Google Search / AI features use Google Search index
[OK] bingbot can crawl all key paths — Bing/Copilot search index
[INFO] Training-policy bot GPTBot: allowed — OpenAI model-development crawling
[INFO] Training-policy bot ClaudeBot: allowed — Anthropic model-development crawling
[INFO] Training-policy bot Google-Extended: allowed — Google generative-AI training/grounding control, separate from Googlebot
... [truncated]
```

### CI parity: social cards strict — PASS

```text
NOTICE  shared article card used by 7 pages: https://davidportodiaz.com/assets/og-worldbuilding-noveris-ciudad-fantastica.jpg :: cuaderno/fantasia-juvenil-espanola-portales-magia-coste/index.html, cuaderno/libros-fantasia-juvenil-espanola-2025-2026/index.html, cuaderno/portal-fantasy-vs-fantasia-epica/index.html, cuaderno/que-es-el-portal-fantasy/index.html, cuaderno/worldbuilding-noveris-ciudad-magica/index.html, recomendaciones/magia-con-coste/index.html, recomendaciones/portal-fantasy-espanol/index.html
Social cards: 432 indexable HTML pages; 0 error(s), 0 warning(s), 1 notice(s).
```

### CI parity: copy tildes — PASS

```text
COPY TILDES: OK (557 ficheros HTML/JS revisados)
```

### CI parity: head icon normalization — PASS

```text
HEAD ICON CONTRACT: OK — verified; changed=0
```

### CI parity: head icon normalizer regression — PASS

```text
PASS head icon normalizer: browser ICO migrated, Apple touch brand preserved, self excluded
```

### CI parity: interaction a11y anti-patterns — PASS

```text
INTERACTION/A11Y CONTRACTS: PASS (449 tracked public HTML files)
```

### CI parity: radar clock projection — PASS

```text
RADAR CLOCK: CURRENT for 2026-10-30 (active=67 watch=13; generated_for=2026-10-30)
```

### Authority: machine-readable contract — PASS

```text
PASS — machine authority contract (808 checks).
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
  ok   editoriales/umbriel/index.html está sincronizado con el builder
  ok   editoriales/editorial-hidra/index.html está sincronizado con el builder
  ok   editoriales/nova/index.html está sincronizado con el builder
  ok   editoriales/runas/index.html está sincronizado con el builder
  ok   editoriales/gamon-fantasy/index.html está sincroniza
... [truncated]
```

### Builder parity: convocatorias — PASS

```text
tests/test-radar-builder-parity-v1
  ok   campos privados extra en radar se rechazan
  ok   campos privados extra en watchlist se rechazan
  ok   ids duplicados entre radar y watchlist se rechazan
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
Brevo DOI error 400
Brevo DOI error 500
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
ok mutation: future verified_at is never treated as current
ok mutation: future watchlist verification stays hidden
ok mutation: cross-list duplicate id -> FAIL
test-radar-freshness-real-clock: OK
```

### Smoke: ICS RFC5545 roundtrip — PASS

```text
ok   evento-escritor-core.js generator exits 0 (stderr: (node:10212) [MODULE_TYPELESS_PACKAGE_JSON] Warning: Module type of file:///C:/GIT/wt-page/assets/evento-escritor-core.js is not specified and it doesn't parse as CommonJS.
Reparsing as ES module beca)
  ok   icalendar parses exactly 1 VEVENT from the event tool's ICS
  ok   SUMMARY round-trips with accents intact
  ok   DTSTART is 17:00 UTC per icalendar (got 2026-09-03 17:00:00+00:00)
  ok   folded DESCRIPTION unfolds correctly
  ok   event tool's JSON-LD re-parses with json.loads and keeps @type Event
  ok   JSON-LD nested address survives re-parse
  ok   icalendar parses 0 VEVENT(s) from the radar builder's ICS
  ok   the committed deadlines.ics parses with icalendar
tests/test-ics-roundtrip-independent-parser: OK
```

### Smoke: SEO & discoverability sitewide — PASS

```text
Auditing SEO & Schema on 443 published HTML pages...
SEO & Schema Smoke: 5704/5704 assertions passed.
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
  ok   2. All 6 dev supply-chain advisories match live npm audit exactly
test-npm-supply-chain-baseline: OK
```

## Rollback Procedure (Documented, not executed)

1. Identify incident and freeze merges.
2. Checkout rollback target SHA: `2ccebd5fcd508472ba3511913026a32cd6bb3f1f`.
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
