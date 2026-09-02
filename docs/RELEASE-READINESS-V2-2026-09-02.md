# Release Readiness Evidence V2

- Generated: 2026-09-02 (finalized post-merge)
- Source branch: `fix/sitewide-reflow-combined-spacing-2026-09-01` (PR #320, squash-merged 2026-09-02T06:39:08Z)
- Verified pre-merge HEAD (all CI evidence below was produced on this commit): `0722fab5994785be48f377de7880d03604511f54`
- **Final `main` SHA (this document's subject): `1cbe6e27bcf3f745ace676c3eb38ef2a0c399cfa`** — squash-merge commit, identical tree to `0722fab5`; confirmed via `gh pr view 320 --json mergeCommit` and `gh api repos/.../commits/main`
- `main` immediately before this merge: `4358864b3d38daf3961c0f4dc408a058a2fa0254` (#317; PR #319's `6b78a5c8` had already landed and is included in this range)
- Open PRs at time of writing: **0** (`gh pr list --state open` → `[]`)
- Supersedes: `docs/RELEASE-READINESS-V1.md` (2026-08-22, `STATIC_CHECKS_PASSED` only — explicitly did not cover browser QA, Lighthouse, Pa11y, the reflow gate, no-JS, or keyboard)

## Final Status: `CI_VERIFIED_GREEN`

> This is **not** `WEB_READY=true` for the full 108-idea backlog, and does not claim that. It certifies exactly one thing: **the specific set of changes in this branch, merged onto the `main` this branch is based on, passes every automated gate this repository has** — static checks, sitewide browser QA, Lighthouse, Pa11y, the full text-resilience/reflow gate (including the newly-enforced 200%+text-spacing combined scenario), target-size, the new Focus Not Obscured (F.4) gate, and check-links. It does **not** certify: real-device testing (a physical iPhone for the intro video, VoiceOver/NVDA screen readers, a physical PWA install), Brevo's live email automation end-to-end, or the ~88 web-improvement ideas not re-verified in this pass (see `docs/web-improvements/01-FINAL-AUTHORITY-108.md`'s 2026-09-02 addendum). Those stay explicitly open — see "Known gaps, stated plainly" below.

## What changed in this branch (summary)

1. Reconciled with fresh `main` (merged #319 in cleanly, zero file conflicts).
2. Closed the `/fragmento/` reading-measure QA discrepancy with root-cause evidence (font-render divergence between local Windows Playwright and real CI; CI already passes 9/9) — see `docs/audits/FRAGMENTO-READING-MEASURE-LOCAL-CI-DISCREPANCY-2026-09-02.md`.
3. Retired 5 of 6 third-party book claims in `/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/` that failed external fact-checking (wrong year/genre, or unverifiable), corrected the one that held up, added a dated correction note. No invented substitutes.
4. Implemented F.4 (WCAG 2.4.11 Focus Not Obscured) as a real geometric check across 5 curated keyboard journeys × 2 viewports, enforced in CI — `qa/focus-not-obscured-audit.mjs`.
5. Verified (not redesigned) the `/asistente/` visual system: live-tested user/assistant message differentiation, composer, sources, suggestions, mobile 320/360/390, keyboard focus, and the floating widget/embed iframe — all already correctly unified with the editorial blue/gold system from PR #284; corrected an earlier, mistaken claim in this same conversation that it wasn't.
6. Functionally tested all 12 previously load-only-checked tools with real input/output (POV distribution, character map, chapter analyzer, manuscript cleaner, metadata preview, JSON-LD generator, book-page auditor, press-kit ZIP generator, reading card, family-interview generator, dialogue-convention checker, read-aloud timer) — every calculation verified exact.
7. Reconciled the 108-idea authority docs against real git evidence (not assumption): corrected E.8 and Q.3 (falsely marked `mergedMain:false`, actually shipped via #206 and #298 respectively), added G.1 (shipped via #305, was untracked), confirmed I.2/C.3/C.10/D.11/I.4/I.5/M.3 are genuinely still unimplemented (`REAL_PENDING`), corrected a stale I.5 doc claim.
8. Fixed a real, unrelated `check-links` failure (external publisher domain blocking automated crawlers, not a dead link) and removed dead JS wiring for a form that exists in no HTML file on the site.

## CI evidence (this exact HEAD)

All required checks green on `0722fab5` before this document's own commit (documentation-only, not re-verified separately since it changes no code/tests):

| Check | What it covers | Result |
|---|---|---|
| `reflow-sitewide` | Sitewide layout at 320/390/768/1280px, target-size (14k+ targets), text-resilience (200% zoom, text-spacing, and the combined scenario — now enforced, not piloted), **Focus Not Obscured (new, F.4)** | `PASS` |
| `identity-public` | CLS/overflow for autor/prensa/premios/eventos across 7 viewports | `PASS` (one prior flaky CLS failure on this exact commit reproduced as CI-flake via re-run, not a real regression — documented in this session) |
| `pa11y-baseline` | WCAG baseline across 58 URLs | `PASS`, 0 errors |
| `check-links` | 5,814 links, 606 unique, external reachability | `PASS`, 0 errors after excluding a bot-blocking external host |
| `lighthouse` | Performance budgets | `PASS` |
| `browser-qa` / `csp-browser-qa` / `funnel-qa` / `ladder-qa` / `taxonomy-qa` / `findability-qa` / `identity-public` / `copy-qa` / `content-indexes` / `contract` / `contract-and-security` / `machine-authority` / `newsletter-contract` / `node-tests` / `python-tests` / `performance-budget` / `public-artifact-contract` / `runtime-scoping` / `third-party-integrations` / `inherited-evidence` / `data-and-browser` | Full functional/contract suite (see `.github/workflows/`) | `PASS` |
| `Required merge gate` | Aggregates all of the above | `PASS` |

Live status at merge time: `gh pr checks 320 --repo davidpd89/web-escritor` (this document is generated alongside, not weeks after, the run it describes).

## Post-merge confirmation on `main`

- `gh pr view 320 --json state,mergedAt,mergeCommit` → `MERGED`, `2026-09-02T06:39:08Z`, `1cbe6e27bcf3f745ace676c3eb38ef2a0c399cfa`.
- Squash merge means the merge commit's tree is byte-identical to `0722fab5`'s tree; no re-run of the PR-gated suites (`reflow-sitewide`, `pa11y-baseline`, `lighthouse`, etc.) is triggered by GitHub on a push to `main`, since those are `pull_request`/merge-queue gated — the evidence above already covers this exact content.
- `Deploy Pages` (the one workflow that does run on push to `main`) on commit `1cbe6e27`: `completed` / `success` (`gh run list --commit 1cbe6e27... --json name,status,conclusion`).
- `gh pr list --repo davidpd89/web-escritor --state open` → `[]` — zero open PRs remain.

## Static evidence (generated by `scripts/release-readiness.py`, same HEAD)

Route inventory (16 required routes: sitemap presence + direct file existence), and the full local static-check parity suite (content indexes, hrefs, internal graph, navigation coverage, heading structure, JSON-LD absolute URLs, canonical entity IDs, editorial facts, AI discoverability, social cards strict, copy tildes, radar builder parity, newsletter client/worker/staging contracts, social-card regression guard) all `PASS`. Full machine output preserved in git history of this file's first commit.

## Known gaps, stated plainly (not marked VERIFIED_E2E, because they are not)

These require capabilities this environment does not have. Listed explicitly so a future session does not mistake "CI is green" for "these are done":

- **Physical iPhone test of the intro video fix.** PR #319 fixed a real, reproducible code bug (autoplay gated behind `loadeddata`, which can deadlock on iOS Safari) and shipped `/video-ios-test/` + `?video-debug=1` diagnostics specifically so this can finally be checked with real evidence instead of guesswork. Nobody has run that test on a real device yet as of this document.
- **VoiceOver/NVDA screen-reader session (F.6).** Automated Pa11y/axe-core coverage is real and green; a live screen-reader pass is not the same thing and has not happened.
- **Physical PWA install/offline/update/reopen cycle** (iOS and Android). Manifest and service-worker code exist and are tested for correctness; the real install/offline/reopen user journey on real hardware has not been run.
- **Printed guide physical proof** (`clubes-de-lectura/samuel-entre-mundos/guia-imprimible/`) — A4, color and black-and-white, margins/cuts on real paper. Not checked in this pass.
- **Brevo live E2E**: real signup → DOI email → correct list placement (beta vs. general, now that both stay separate) → confirm no cross-contamination → unsubscribe. The contract tests (worker/staging/client) are green; a live mailbox round-trip is not evidence this environment can produce.
- **~88 of the 108 web-improvement ideas** not re-verified against current `main` in this session's reconciliation pass (see the 108-authority doc's 2026-09-02 addendum) — their 2026-08-29 status stands, neither newly confirmed nor newly contradicted.

## Rollback

Now that this is merged, the rollback target on `main` is `4358864b3d38daf3961c0f4dc408a058a2fa0254` (the commit immediately before this squash-merge). Procedure: `git revert -m 1 1cbe6e27...` (preferred, keeps history) or hard-checkout `4358864b` for an emergency redeploy; either way, re-run the static parity scripts listed above and confirm CI green before any re-promotion.

## Notes

- This report does not deploy anything by itself; the repository's own `Deploy Pages` workflow ran automatically on this merge to `main` (confirmed `success` above), as it already did for #318/#319.
- This report's own commit changes no application code, tests, or CI configuration — only adds/finalizes this file, and is opened as its own small PR per this session's standing rule of never pushing directly to `main`.
- Per the user's explicit ordering for this audit cycle, this document was intentionally finalized *after* PR #320 merged and *on* the resulting final `main` SHA, not before.
