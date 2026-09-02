# Release Readiness Evidence V2

- Generated: 2026-09-02 (finalized post-merge, updated after PR #322)
- Source branches: `fix/sitewide-reflow-combined-spacing-2026-09-01` (PR #320) and `fix/108-reconciliation-and-explore-gdpr-2026-09-02` (PR #322)
- Verified pre-merge HEAD for #320 (all CI evidence in the first half of this document was produced on this commit): `0722fab5994785be48f377de7880d03604511f54`
- Verified pre-merge HEAD for #322: `74a392ea...` (full evidence in the "PR #322" section below)
- **`FINAL_STABLE_MAIN = 34fd2c3411fead3412c5932214705012244500dc`** — this is the SHA this document now certifies, not `1cbe6e27` (that was #320's merge commit, superseded the same day by #321 docs-only and then #322). Confirmed via `gh pr view 322 --json state,mergedAt,mergeCommit` and `gh api repos/.../commits/main`.
- Chain since the previous `main` tip: `4358864b` (#317) → `1cbe6e27` (#320) → `cbeb146e` (#321, docs-only) → `34fd2c34` (#322) → `FINAL_STABLE_MAIN`.
- Open PRs at time of writing: **0** (`gh pr list --state open` → `[]`)
- Supersedes: `docs/RELEASE-READINESS-V1.md` (2026-08-22, `STATIC_CHECKS_PASSED` only) and this document's own first version (finalized on `1cbe6e27`, before #322 landed).

## Final Status: `CI_VERIFIED_GREEN` on `FINAL_STABLE_MAIN`

> This is **not** `WEB_READY=true` for the full 108-idea backlog, and does not claim that. It certifies exactly one thing: **the code/repository state at `34fd2c34` passes every automated gate this repository has** — static checks, sitewide browser QA, Lighthouse, Pa11y, the full text-resilience/reflow gate (including the enforced 200%+text-spacing combined scenario), target-size, Focus Not Obscured (F.4), check-links, and (as of #322) a corrected 108-idea classification pass and a real tablet-layout CSS fix. At this level — code and CI — this is treated as a stable version. It does **not** certify five specific things that need a human with real hardware/accounts, not more code review: a physical iPhone test of the intro-video fix, a real VoiceOver/NVDA session, a physical PWA install/offline/reopen/update cycle on iOS/Android, a live Brevo E2E (signup → DOI → correct list → unsubscribe), and a physical print check of the Samuel guide. These are distinct from open-ended exploratory/random testing — see "Known gaps, stated plainly" below for why that distinction matters.

## What changed in this branch (summary)

1. Reconciled with fresh `main` (merged #319 in cleanly, zero file conflicts).
2. Closed the `/fragmento/` reading-measure QA discrepancy with root-cause evidence (font-render divergence between local Windows Playwright and real CI; CI already passes 9/9) — see `docs/audits/FRAGMENTO-READING-MEASURE-LOCAL-CI-DISCREPANCY-2026-09-02.md`.
3. Retired 5 of 6 third-party book claims in `/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/` that failed external fact-checking (wrong year/genre, or unverifiable), corrected the one that held up, added a dated correction note. No invented substitutes.
4. Implemented F.4 (WCAG 2.4.11 Focus Not Obscured) as a real geometric check across 5 curated keyboard journeys × 2 viewports, enforced in CI — `qa/focus-not-obscured-audit.mjs`.
5. Verified (not redesigned) the `/asistente/` visual system: live-tested user/assistant message differentiation, composer, sources, suggestions, mobile 320/360/390, keyboard focus, and the floating widget/embed iframe — all already correctly unified with the editorial blue/gold system from PR #284; corrected an earlier, mistaken claim in this same conversation that it wasn't.
6. Functionally tested all 12 previously load-only-checked tools with real input/output (POV distribution, character map, chapter analyzer, manuscript cleaner, metadata preview, JSON-LD generator, book-page auditor, press-kit ZIP generator, reading card, family-interview generator, dialogue-convention checker, read-aloud timer) — every calculation verified exact.
7. Reconciled the 108-idea authority docs against real git evidence (not assumption): corrected E.8 and Q.3 (falsely marked `mergedMain:false`, actually shipped via #206 and #298 respectively), added G.1 (shipped via #305, was untracked). **This step's own classification of I.2/C.3/C.10/D.11/I.4/M.3 as `REAL_PENDING` was itself wrong and got corrected two commits later, in PR #322 — see that section below. Do not trust this bullet; trust the PR #322 section instead.** I.5 remains genuinely `REAL_PENDING` (the one of the six that actually is).
8. Fixed a real, unrelated `check-links` failure (external publisher domain blocking automated crawlers, not a dead link) and removed dead JS wiring for a form that exists in no HTML file on the site.

## PR #322 — corrected 108-idea classification + explore-form fix + Samuel tablet layout fix

Merged 2026-09-02T07:58:59Z, squash commit `34fd2c3411fead3412c5932214705012244500dc`. This PR exists because an external review (GPT, verified independently against the repo rather than taken on faith) caught that item 7 above had applied "no `feat(ID)` commit found = `REAL_PENDING`" too literally, without reading each idea's own revalidation verdict.

1. **Corrected classification for 5 of the 6 ideas wrongly marked `REAL_PENDING`** in `data/web-improvement-individual-prs-2026-08-29.json` → `practicalOverrides`, each now with an explicit `classification` field:
   - **M.3 → `SUPERSEDED`**: its own PR (#246) was conditioned on M.1/#244 landing; #244 is `MERGED` and its live auditor already covers M.3's obsolete-header check by design (no code of its own was ever supposed to exist).
   - **C.3 → `IMPLEMENTED_MAIN`**: its four pilot surfaces already exist in `main`; the only remainder is an external Drive-backlog governance contract, not repo code.
   - **D.11 → `CONDITIONAL`**: critical journeys are already covered per its own verdict; code only if a reproducible defect appears.
   - **I.4 → `CONDITIONAL`**: infra already exists; its own contract forbids automating until manual review demonstrates repeated need.
   - **I.2 → `SUPERSEDED`**: both of its blocking conditions (E.8/#206 landing; the consent-checkbox drift it flagged) are independently resolved.
   - **C.10** relabeled `CONDITIONAL` for consistency (its prose reasoning was already correct, just missing the explicit tag).
   - **I.5 stays `REAL_PENDING`** — correctly, this is the one of the six where that classification was right.
2. Added a matching correction section to `docs/web-improvements/01-FINAL-AUTHORITY-108.md`'s addendum, and updated H.1/H.2/E.8/I.2's revalidation docs (all still cited the pre-#319 consent-checkbox drift as an open blocker).
3. Fixed a real bug the same review surfaced: `script.js` still called `submitNewsletter` for the Explore-modal form with a non-null `gdprId` (`"nl-gdpr-explore"`), an element removed from every page months ago. Extended `tests/test-newsletter-client-contract.mjs` to cover `explore` in the null-`gdprId` assertion so this can't silently drift again.
4. Fixed a real, independently-found CSS bug from a manual multi-breakpoint visual pass (620-900px): the Samuel book page's cover sat flush-left with a large empty gap once its threshold layout collapsed to one column, because `justify-items:start` (correct for the two-column desktop layout) was never overridden to `center` for the single-column range. One-line fix in `assets/v1-samuel.css`, verified at 360/620/768/900/1280px with no desktop regression, and `qa/samuel-design-browser.mjs` passing 9/9 viewports.

### CI evidence (PR #322 HEAD `74a392ea`, i.e. `main` at `34fd2c34`)

All required checks green: `Required merge gate`, `browser-qa`, `content-indexes`, `csp-browser-qa`, `funnel-qa`, `lighthouse`, `newsletter-contract`, `node-tests`, `pa11y-baseline`, `performance-budget`, `privacy-legal`, `public-artifact-contract`, `python-tests`, `reflow-sitewide`, `runtime-scoping`, `smoke`, `taxonomy-qa`, `third-party-integrations`. `mergeStateStatus: CLEAN`, `mergeable: MERGEABLE` before merge. `gh pr list --state open` → `[]` after merge.

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

Five specific things need a human with real hardware/accounts, not more code review, and are being tracked as five named items — not folded into vague "testing left to do." None of them blocks calling `34fd2c34` a stable version at the code/CI level; they block claiming every external/hardware journey is 100% verified. Listed explicitly so a future session does not mistake "CI is green" for "these are done":

1. **Physical iPhone test of the intro video fix.** PR #319 fixed a real, reproducible code bug (autoplay gated behind `loadeddata`, which can deadlock on iOS Safari) and shipped `/video-ios-test/` + `?video-debug=1` diagnostics specifically so this can finally be checked with real evidence instead of guesswork. Nobody has run that test on a real device yet as of this document.
2. **VoiceOver/NVDA screen-reader session (F.6).** Automated Pa11y/axe-core coverage is real and green; a live screen-reader pass is not the same thing and has not happened.
3. **Physical PWA install/offline/update/reopen cycle** (iOS and Android). Manifest and service-worker code exist and are tested for correctness; the real install/offline/reopen user journey on real hardware has not been run.
4. **Brevo live E2E**: real signup → DOI email → correct list placement (beta vs. general, now that both stay separate) → confirm no cross-contamination → unsubscribe. The contract tests (worker/staging/client) are green; a live mailbox round-trip is not evidence this environment can produce.
5. **Printed guide physical proof** (`clubes-de-lectura/samuel-entre-mundos/guia-imprimible/`) — A4, color and black-and-white, margins/cuts on real paper. Not checked in this pass.

Separately, **~88 of the 108 web-improvement ideas** were not re-verified against current `main` in the 2026-09-02 reconciliation passes (see the 108-authority doc's addenda) — their 2026-08-29 status stands, neither newly confirmed nor newly contradicted. This is real remaining work, but it is backlog verification, not a release blocker: most of those 88 are `REJECT`/`DEFER`/`CONDITIONAL`/`EXTERNAL_OPERATION`/residual-audit by design, not features waiting to be built. Re-verifying all 88 should happen as its own bounded pass when there's reason to, not as a precondition for calling `34fd2c34` stable.

After this document, the intended next steps are the five physical/manual tests above, whenever they can be run — not another general code/documentation audit. Exploratory or random testing (different browsers, odd viewport sizes, clicking around as a normal user) is welcome at any time after this point, but any bug it finds should be treated as ordinary maintenance on a stable site, not as "the site is still being finished."

## Rollback

Rollback target on `main` is `4358864b3d38daf3961c0f4dc408a058a2fa0254` (the commit immediately before PR #320's squash-merge, i.e. before this entire chain of work). Procedure: `git revert -m 1 <SHA>` for the specific commit(s) to undo (preferred, keeps history) or hard-checkout `4358864b` for an emergency full redeploy; either way, re-run the static parity scripts listed above and confirm CI green before any re-promotion.

## Notes

- This report does not deploy anything by itself; the repository's own `Deploy Pages` workflow ran automatically on each of these merges to `main` (confirmed `success` for #320 above; same workflow, same guarantee for #321/#322).
- This report's own commits change no application code, tests, or CI configuration in themselves — only add/finalize this file, and are opened as their own small PRs per this session's standing rule of never pushing directly to `main`.
- Per the user's explicit ordering for this audit cycle, this document was intentionally finalized *after* PR #320 merged and *on* the resulting final `main` SHA at that time — then updated again after #322 corrected a factual error in this same document (§ "What changed in this branch", item 7) and added its own real fixes. `FINAL_STABLE_MAIN = 34fd2c34` is the SHA that should be cited going forward, not `1cbe6e27`.
