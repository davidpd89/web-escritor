---
name: verify-web-change
description: "Verify a web-escritor code/content change before opening or declaring a PR ready. Use after editing this repo or when asked whether a branch is ready. Select focused checks from the actual changed files, run them, then report evidence and anything that still requires GitHub CI."
---

# Verify Web Escritor Change

Use the repository's existing checks. Do not invent a parallel test stack.

## 1. Pin the change

Resolve the comparison point from the task/PR. Prefer the PR base or merge-base with `main`.

Inspect:

```bash
git diff --name-only <base>...HEAD
git diff --stat <base>...HEAD
```

Keep verification proportional to the diff.

## 2. Run focused checks first

### Python regression contracts

For each changed `tests/test-*.py`, run it directly:

```bash
python tests/<changed-test>.py
```

If the test protects another file, read that file and verify the test can fail on the promised regression rather than only pass the current state.

### Node regression contracts

For each changed `tests/*.mjs`:

```bash
node tests/<changed-test>.mjs
```

Browser QA under `qa/*.mjs` may need a local server / Playwright setup. Use the command or workflow already associated with that QA; do not replace browser evidence with a static guess.

### Runtime asset changes

If a changed file is a versioned runtime asset covered by `scripts/check-asset-versions.py`, run:

```bash
python scripts/check-asset-versions.py
```

If the check proves an asset version/hash is stale, use the repository's existing bumper rather than editing references manually:

```bash
python scripts/bump-asset-version.py --help
```

Follow the script's actual usage.

### Public HTML / registry / discoverability changes

When the diff can change public pages, URLs, generated shell, search corpus, or machine-readable editorial facts, run the applicable existing checks:

```bash
python scripts/build-site-shell.py --check
python scripts/build-sitemap.py --check
python scripts/build-public-editorial-facts.py --check
python scripts/build-pagefind-index.py --check
```

Only regenerate an artifact when its own `--check` proves it is stale.

## 3. Respect the required gate

Before calling a PR ready, read `.github/workflows/required-merge-gate.yml`.

Do not claim local equivalence unless you actually ran its relevant dependencies and commands. GitHub CI remains the authority for environment-dependent checks.

At minimum, confirm that any new universal `tests/test-*.py` or `tests/*.mjs` will be picked up automatically by the required gate.

## 4. Review the evidence

Apply `CODING_STANDARDS.md` when present.

For regression tests, ask:

- What exact change makes this test go red?
- Would harmless formatting/refactoring make it fail?
- Does an existing guardrail already cover the same failure?
- Is the PR still scoped to the problem it claims to solve?

A green command is evidence, not proof of good test design.

## 5. Report

Return:

### Focused checks
- command → PASS/FAIL and the relevant signal

### GitHub-only / not run locally
- checks that still require CI, browser infrastructure, or another environment

### Scope
- changed files and whether anything unrelated is present

### Verdict
- `READY_FOR_CI`, `NEEDS_FIX`, or `NEEDS_ENVIRONMENTAL_VALIDATION`

Never say "all green" while checks are still running or were not executed.
