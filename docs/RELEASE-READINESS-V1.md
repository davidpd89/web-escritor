# Release Readiness Evidence V1

- Generated: `2026-08-22T12:02:02.305703+00:00`
- Branch: `gpt/release-readiness-v1`
- HEAD: `64fa58fb7f8bd223e9fa8c32c554f43d2286998c`
- Previous SHA (rollback candidate): `8a8d8f227a5e838876d4584aa9e220365fca2996`

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
64fa58f release: add pre-main readiness evidence package v1
8a8d8f2 Site audit: remove residual legacy and integration regressions V1 (#26)
e920727 Visual system: finish editorial frames routes and media treatment V1 (#24)
db68607 Convocatorias: migrate builder output to V1 shell parity (#22)
cc5ef69 Handoff: add tasks 7-11 and run the secret scan on every PR (#25)
9fc2e62 Harden newsletter client flows and contract checks (#23)
12efea3 fix(editoriales): reconcile builder templates with V1 pages (#21)
0d1cb96 docs(handoff): add controlled remaining-work execution plan (#20)
c820b21 fix(editoriales): stop the builder silently reverting the V1 directory
752af0e fix(cards): keep the "Verificado" badge inside its card
1ab3135 fix(masthead): give the headline room above its lead paragraph
8250e8c fix(header): stop the mobile header eating 15% of the screen
a05cac4 chore: remove probe scripts committed by mistake
1072c23 fix(qa): measure rendered layout, not the pre-stylesheet flash
7742d58 ci: make the repo-wide secret scan actually run, and fix its false positive
841fba4 fix(qa): findability preservation handles new pages and the landmark rename
109dbc0 fix(masthead): headline no longer spills out of its own measure
ad46b15 feat(footer): restore social profiles sitewide and fix two lost destinations
7a10f26 ci: promote the Pa11y WCAG2AA baseline to a pull-request gate
b863386 a11y: warn about disabled JavaScript on the four tools that did not
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

## Output Excerpts

### CI parity: content indexes — PASS

```text
Local asset check: 87 HTML files scanned; 0 broken local reference(s) (including 0 JS reference target(s) and 0 CSS url() target(s)).
```

### CI parity: hrefs — PASS

```text
HREF-OK
```

### CI parity: internal graph — PASS

```text
INTERNAL GRAPH REPORT
Files scanned: 84
Indexable pages: 55

INFO (1):
  [noindex-skipped] 29 pages excluded (noindex): aviso-legal.html, privacidad.html, samuel-entre-mundos.html, asistente\embed.html, asistente\index.html, donde-empieza-la-jaula\index.html, herramientas\auditor-web\index.html, lab\diseno-home-v1\article-pilot.html �

Summary: 0 error(s), 0 warning(s)
```

### CI parity: navigation coverage — PASS

```text
PASS: navigation coverage (56 registry routes, 55 sitemap routes, 17 interactive tools)
```

### CI parity: heading structure — PASS

```text
Heading/skip-link structure: 67 ficheros HTML revisados; 0 problema(s).
```

### CI parity: jsonld absolute URLs — PASS

```text
OK � 59 page(s) with JSON-LD checked, all url/@id/isPartOf/about/mainEntity/isBasedOn references are absolute.
```

### CI parity: canonical entity IDs — PASS

```text
CANONICAL ENTITY IDs: OK (4 entidades con @id, todas consistentes)
```

### CI parity: editorial facts — PASS

```text
EDITORIAL FACT CHECK � mode=prelaunch � date=2026-08-22 � publication=2026-09-03
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
NOTICE  shared article card used by 8 pages: https://davidportodiaz.com/assets/og-worldbuilding-noveris-ciudad-fantastica.webp
Social cards: 55 indexable HTML pages; 0 error(s), 0 warning(s), 0 notice(s).
```

### CI parity: copy tildes — PASS

```text
COPY TILDES: OK (148 ficheros HTML/JS revisados)
```

### Authority: machine-readable contract — PASS

```text
PASS � machine authority contract (568 checks).
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
Brevo error 500: secret upstream detail
```

### Newsletter: staging gate — PASS

```text
test-staging-newsletter-disable: all assertions passed
```

### Social card regression guard — PASS

```text
test-social-card-article-specific: OK (7 pages checked)
```

## Rollback Procedure (Documented, not executed)

1. Identify incident and freeze merges.
2. Checkout rollback target SHA: `8a8d8f227a5e838876d4584aa9e220365fca2996`.
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
