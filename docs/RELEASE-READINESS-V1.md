# Release Readiness Evidence V1

- Generated: `2026-09-08T06:01:12.042340+00:00`
- Branch: `fix/privacy-text-clarity-audit-tracking-2026-09-08`
- HEAD: `2258ec654b726059ce5ec1645bee971938dfe9ac`
- Previous SHA (rollback candidate): `7dc1d57893f4aa22cbba8671a6a2ce27b6f7d1aa`

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
2258ec65 Corregir consentimiento de analítica de Clarity (denied por defecto) (#473)
7dc1d578 docs: record 2026-09-08 corrections to the Wikidata/Amazon closure (#474)
5188ed3c Enlazar Google Preferred Sources en el Cuaderno (#472)
517cf160 feat: link Manecillas' now-combined Goodreads work in sameAs (#471)
ead76838 Cierre Amazon Author Central + Goodreads + Wikidata (2026-09-07) (#470)
7c1b91e4 Clarity consent closure + noindex/keyword/interlinking audit (#395)
6359cbde SEO fixes: Amazon links, dead ASINs, RSS styling, Bing title, Microsoft Clarity (#393)
8c1a7044 docs: track Bing/GSC backlink-authority gap as a pending item (#394)
d2f70aa2 fix: disambiguate Home buy-CTA accessible names, purge stale v14 cache (#392)
c5578022 fix: content-parity regex broke by #390's intentional dt/dd space (#391)
1ec49bfa fix: sitewide dt/dd search-index concatenation across every fact ledger (#390)
5895e54f fix: Samuel entre mundos ledger dt/dd search-index concatenation (#389)
c5466531 fix: .mjs cache staleness and blank-Home fallback recovery (#388)
df32de9c fix: second post-Kindle-launch QA round (newsletter, dynamic CTAs, assistant editions) (#387)
75c91f44 fix: post-Kindle-launch consistency sweep (stale copy, dates, nav, CSS) (#386)
6e8a244a fix: manecillas sample --check false-positive on a local Windows checkout (#385)
f8311aaa feat: activate Las manecillas del recuerdo's Kindle purchase link sitewide (#384)
a88bfa24 feat: add Comprar CTA to Manecillas Home hero + fix script cache-busting gap (#382)
d55679af fix: two relative assets/ references survived PR #365's absolute-path cleanup on Home (#383)
72d11bd4 fix: closing dialogue quote after a number stayed straight, and reset only fired on blank paragraphs (#381)
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
  [noindex-skipped] 34 pages excluded (noindex): aviso-legal.html, privacidad.html, samuel-entre-mundos.html, asistente\embed.html, asistente\index.html, cuaderno\sistema-de-magia-noveris\index.html, donde-empieza-la-jaula\index.html, gracias-suscripcion\index.html �

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
EDITORIAL FACT CHECK � mode=launch � date=2026-09-08 � publication=2026-09-03
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
NOTICE  shared article card used by 4 pages: https://davidportodiaz.com/assets/eventos/og-feria-libro-madrid-2026-david-porto-samuel.jpg :: .claude/worktrees/agent-a4a0f10ba479e3318/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/index.html, .claude/worktrees/agent-aa779067cd4e87151/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/index.html, .claude/worktrees/agent-aaa07b6a8f068661e/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/index.html, cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/index.html
NOTICE  shared article card used by 8 pages: https://davidportodiaz.com/assets/og-clubes-lectura-samuel-entre-mundos.jpg :: .claude/worktrees/agent-a4a0f10ba479e3318/clubes-de-lectura/samuel-entre-mundos/guia-imprimible/index.html, .claude/worktrees/agent-a4a0f10ba479e3318/clubes-de-lectura/samuel-entre-mundos/index.html, .claude/worktrees/agent-aa779067cd4e87151/clubes-de
... [truncated]
```

### CI parity: copy tildes — PASS

```text
COPY TILDES: OK (180 ficheros HTML/JS revisados)
```

### Authority: machine-readable contract — PASS

```text
PASS � machine authority contract (680 checks).
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

## Rollback Procedure (Documented, not executed)

1. Identify incident and freeze merges.
2. Checkout rollback target SHA: `7dc1d57893f4aa22cbba8671a6a2ce27b6f7d1aa`.
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
