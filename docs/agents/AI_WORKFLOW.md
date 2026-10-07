# Shared AI workflow

Canonical working rules for coding agents that modify this repository. Provider-specific entry files (`AGENTS.md`, `CLAUDE.md`) should stay thin and point here rather than duplicating these rules.

## Scope first

- Prefer the smallest reversible change that solves one concrete problem.
- One PR should have one primary reason to exist. Split unrelated findings.
- Do not opportunistically edit production/content/config while touching a test or agent workflow.
- For a tiny change, inspect only the files and nearby context needed to make it safely. Do not preload the whole repository.

## Reuse the repository

Before creating a new script, workflow, rule, or abstraction, look for an existing guardrail that can be extended.

Useful authorities include:

- `.github/workflows/required-merge-gate.yml` — required repository gate;
- `scripts/build-public-dist.py` — public artifact boundary;
- existing `tests/test-*.py`, `tests/*.mjs`, and `qa/*.mjs`;
- `CODING_STANDARDS.md`, when present;
- task-specific skills under `.agents/skills/`.

Do not create a parallel testing or release system when the existing one can express the check.

## Bugs and regressions

For a reported bug or flaky test:

1. Build the tightest practical feedback loop that can reproduce the exact symptom.
2. Prefer a failing test/browser assertion/CLI check before changing production code.
3. Distinguish the real contract from incidental serialization, timing, or implementation details.
4. Fix the smallest confirmed cause.
5. Re-run the focused repro and the relevant repository checks.

Do not turn an unverified hypothesis into a production change.

## Verification

Verification must follow the diff, not a generic ritual.

- Run changed regression tests directly when practical.
- Reuse existing check/build scripts for affected generated artifacts.
- Use browser QA for browser behaviour; do not replace it with static inference.
- Treat GitHub CI as authoritative for environment-dependent checks.
- Never say a PR is "all green" while checks are pending, skipped without explanation, or not run.

When `.agents/skills/verify-web-change/SKILL.md` exists and the task is PR/readiness verification, use that workflow.

## Review

Review implementation quality and requested intent separately.

A useful finding must identify:

- the concrete claim or contract affected;
- evidence in the diff/current behaviour;
- the smallest practical correction.

A green CI badge is evidence that the current checks passed; it is not evidence that a new test is sensitive to the intended failure or resistant to obvious false positives.

When `.agents/skills/web-escritor-review/SKILL.md` exists and the task is code review, use it as the repository review workflow.

## Agent portability

Repository policy is provider-neutral. Keep durable rules here, in `CODING_STANDARDS.md`, deterministic checks, or canonical skills.

`AGENTS.md` and `CLAUDE.md` are adapters for their respective tools. Do not let them drift into separate versions of project policy.

If an agent does not auto-discover `.agents/skills/`, it should read the matching `SKILL.md` directly when the task clearly matches its purpose.
