---
name: web-escritor-review
description: "Review a web-escritor PR or branch before merge using two separate axes: Regression/Repo Safety and Intent/Spec. Use when a change is green in CI but still needs an independent check that the tests and implementation are robust, scoped, and actually prove what the PR claims."
---

# Web Escritor Review

Small pilot adapted from Matt Pocock's `code-review` skill:
https://github.com/mattpocock/skills/tree/main/skills/engineering/code-review

Source reviewed for this adaptation: commit `dd400c3ad65e57c06f05e832e0aac92c7992f34d`.
Upstream license: MIT.

This is intentionally renamed and narrowed for `web-escritor`. Do not invoke another code-review skill from inside this skill and do not recursively spawn reviewers.

## Goal

A green CI run proves that the current checks passed. It does not prove that a new check is well-designed, that a test is sensitive to the intended regression, or that the diff exactly matches the PR's stated intent.

Review those questions separately.

## Input

Prefer a PR number. Otherwise use a branch plus its fixed base.

For a PR:
- fixed point = the PR base branch;
- spec = PR title/body plus any explicitly linked issue/spec;
- change = PR diff and commits.

Do not invent requirements that are absent from the PR/spec.

## Pass 1: Regression / Repo Safety

Review only the changed code plus the minimum nearby context needed to judge it.

Check:

1. **Scope**: no unrelated production/content/config changes.
2. **Test sensitivity**: a regression test should fail when the promised contract breaks.
3. **False-positive resistance**: it should not fail for irrelevant formatting/refactors unless those are explicitly part of the contract.
4. **False-negative resistance**: obvious ways of breaking the promised behaviour should not still pass.
5. **Local consistency**: compare with nearby tests and the files the change protects.
6. **Executable evidence**: inspect relevant CI/check results and run focused checks when the harness can do so.
7. **Heuristic smells**: duplication, speculative generality, brittle string matching, unnecessary coupling, or a test that checks representation instead of behaviour.

Treat heuristics as judgement calls, not hard violations.

## Pass 2: Intent / Spec

Read the PR/spec independently of Pass 1, then map every material claim to the diff.

Report:

- missing or partial requirements;
- behaviour added but not requested;
- claims that the implementation appears not to prove;
- claims that are correctly implemented.

Do not let a clean implementation compensate for a missed requirement, or vice versa.

## Evidence rules

Every finding must include:

- severity: `BLOCKER`, `REAL_IMPROVEMENT`, or `NIT`;
- the exact PR/spec claim affected;
- the file/hunk or code shape that supports the finding;
- the smallest practical correction.

If there is no finding on an axis, say so explicitly.

Do not report a generic concern without evidence.

## Stop rule

One review pass, then at most one verification pass after fixes. Do not loop until the model invents new findings.

## Output

Use exactly:

### Regression / Repo Safety
[findings or PASS]

### Intent / Spec
[findings or PASS]

### CI evidence
[relevant checks actually observed]

### Verdict
- Ready / Needs changes
- findings count per axis
- one sentence on whether this review added information beyond CI
