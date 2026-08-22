# PR Notes — Sitewide Reflow Gate V1

- Date: 2026-08-22
- Compare base: `gpt/release-readiness-v1`
- Compare branch: `gpt/reflow-gate-sitewide-v1`
- Compare URL: `https://github.com/davidpd89/web-escritor/compare/gpt/release-readiness-v1...gpt/reflow-gate-sitewide-v1?expand=1`

## Scope

This PR adds and hardens the sitewide text-reflow QA gate under stress conditions (text spacing + zoom 200%) and stabilizes shared responsive behavior so the gate detects real layout regressions instead of false positives.

### Included commits

1. `a7eb163` — `qa: add sitewide reflow gate and harden shared responsive layouts`
2. `16af1be` — `qa: stabilize reflow gate measurement and pass sitewide checks`

## What Changed

### QA gate

- Added workflow: `.github/workflows/sitewide-reflow-qa.yml`
- Added browser QA script: `qa/sitewide-reflow-browser.mjs`
- Route scope cleanup:
  - ignores `lab/`
  - skips `/data/*.html`

### Measurement hardening

- Replaced document-level `scrollWidth - clientWidth` heuristic with element-level visible overflow checks using `getBoundingClientRect()`.
- Normalized geometry when zoom is applied.
- Ignored elements nested inside intentional horizontal scrollers (`overflow-x: auto|scroll`) so tables/canvases with designed horizontal scrolling do not trigger false positives.

### Shared responsive hardening (from initial commit)

- Updated shared CSS layers to reduce narrow viewport overflow risk across public pages, including:
  - `assets/v1-editorial.css`
  - `assets/v1-families.css`
  - `assets/v1-book.css`
  - `assets/v1-samuel.css`
  - `assets/v1-legal.css`
  - `assets/v1-findability.css`
  - `assets/v1-components.css`
  - `assets/v1-base.css`
  - `assets/v1-shell.css`
  - `assets/v1-tools.css`
  - `assets/v1-home.css`
  - `assets/jsonld-escritores.css`
  - `offline.html`

## Validation Evidence (fresh run)

Executed locally on branch `gpt/reflow-gate-sitewide-v1`:

```text
python scripts/check-local-assets.py
Local asset check: 87 HTML files scanned; 0 broken local reference(s) (including 0 JS reference target(s) and 0 CSS url() target(s)).

python scripts/check-hrefs.py
HREF-OK

python scripts/check-navigation-coverage.py
PASS: navigation coverage (56 registry routes, 55 sitemap routes, 17 interactive tools)

node tests/test-newsletter-client-contract.mjs
test-newsletter-client-contract: all assertions passed

node qa/sitewide-reflow-browser.mjs
sitewide-reflow-browser: OK (66 routes, 2 viewports, 132 checks)
```

## Risk and Rationale

- Main risk: under-reporting overflow for components intentionally contained by horizontal scrollers.
- Rationale: this is expected and desired for accessibility reflow validation. If overflow is intentionally contained by a reachable scroller, it should not fail a page-level reflow gate.
- Remaining guardrails:
  - Non-contained page overflow still fails.
  - Public route inventory is still fully scanned.

## Merge Checklist

- [x] Branch clean and pushed (snapshot at publication)
- [x] Compare is auto-mergeable (GitHub compare showed "Able to merge")
- [x] Sitewide reflow gate green locally
- [x] Core integrity checks green locally
- [ ] PR opened/updated in GitHub UI against `gpt/release-readiness-v1` (auth/UI step)
- [ ] Reviewer sign-off

## Stack Context

- PR #22 (`gpt/global-shell-closure-v1` -> `implementacion-web-2026`): merged.
- PR #23 (`gpt/newsletter-contact-v1` -> `implementacion-web-2026`): merged.
- PR #27 (`gpt/release-readiness-v1` -> `gpt/site-residual-cleanup-v1`): open.
- This branch (`gpt/reflow-gate-sitewide-v1`) is stacked above `gpt/release-readiness-v1` and should be merged into that base before final promotion in the stack.

## Rollback

If needed, rollback compare branch to base:

```bash
git switch gpt/reflow-gate-sitewide-v1
git revert --no-edit 16af1be
git revert --no-edit a7eb163
git push
```

Do not execute rollback unless incident response explicitly requires it.
