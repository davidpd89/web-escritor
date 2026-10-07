# Pilot: adapted code-review skill on PR #574

> Status: **EXPERIMENT · STACKED ON #577 · DO NOT MERGE TO MAIN YET**

## What is being tested

A single idea from `mattpocock/skills`: review a change on two independent axes instead of treating "CI green" as the whole review.

Upstream reference:
https://github.com/mattpocock/skills/tree/main/skills/engineering/code-review

OpenAI also documents `.agents/skills/` as the repository-local location for Codex skills, so the pilot lives there intentionally rather than in a project-specific ad hoc folder.

Official reference:
https://developers.openai.com/blog/skills-agents-sdk

This pilot deliberately does **not** install the upstream skill unchanged because its own documentation notes two practical risks:

- name collision with Claude Code's built-in `/code-review`;
- recursive sub-agent fan-out reported by users.

The local pilot is therefore renamed `web-escritor-review`, has an explicit recursion guard, and is scoped to this repository.

## Target

PR #574: `test(typography): blindar carga de fuentes V1`

The PR adds `tests/test-v1-typography-font-loading-contract.py`.

Its stated contract is to protect:

- `Manrope` → `font-display: optional`;
- `Manrope Display` → `font-display: swap`;
- `Yellowtail` → `font-display: swap`;
- four canonical font-family tokens.

## Baseline before the review

At commit `81064b482ca7986c561c9478b84a1625ea990a55`, GitHub Actions reported **success** for all observed PR workflows, including:

- Required merge gate;
- Lighthouse CI;
- Visual regression;
- Accessibility baseline (Pa11y);
- Sitewide Reflow QA;
- Runtime scoping QA;
- CSP public shell QA;
- Public artifact contract;
- Tool engine tests;
- Analytics taxonomy QA;
- Check content indexes.

So this is a useful pilot: the change is green, and the question is whether an independent review can still find a real maintainability/regression-testing weakness.

## Pilot review

### Regression / Repo Safety

**REAL_IMPROVEMENT — the test couples semantic assertions to minified CSS formatting.**

The helper:

`pattern = rf"@font-face\\{{font-family:'{re.escape(family)}';.*?\\}}"`

only recognises an `@font-face` when `{` is immediately followed by `font-family:`, using single quotes and no harmless whitespace. Reformatting the CSS to:

```css
@font-face {
  font-family: 'Manrope';
  ...
}
```

would make the regression test fail even though the protected `font-display` behaviour is unchanged.

The token assertions have the same property:

`needle = f"{token}:{stack_start}"`

They require the current exact no-whitespace serialization around `:`. A formatter or manual cleanup could trigger a false regression.

**Smallest correction:** make the test parse/normalise CSS declarations enough to compare declaration values semantically, or at minimum tolerate CSS whitespace and quote style. The contract is font behaviour/token values, not minification.

No unrelated production change was observed in the PR diff.

### Intent / Spec

**PASS.**

The diff does target every behaviour named in the PR body. The concern above is not missing scope; it is that the implementation also accidentally enforces formatting that the PR never declared as part of the contract.

### CI evidence

All observed workflows for the reviewed commit were green, including `Required merge gate`.

### Verdict

**Needs one small improvement before treating this test as a durable regression contract.**

- Regression / Repo Safety: 1 real improvement.
- Intent / Spec: 0 findings.
- Added value beyond CI: **yes**. CI proved the test passes the current minified file; this review exposed a plausible false-positive path caused by harmless CSS reformatting.

## What would count as success for the skill

This pilot is useful if, when run from a fresh Codex session on future PRs, it repeatedly does at least one of these without generating noise:

1. catches a real gap or brittleness not visible from CI;
2. confirms a green PR with evidence and no invented findings;
3. separates "the code is tidy" from "the PR actually does what it says";
4. produces findings specific enough to turn directly into a fix/test.

If it mostly repeats CI, invents style preferences, or causes review loops, discard it.

## Next step

Do **not** expand to the rest of Matt Pocock's skills yet.

First run `web-escritor-review` on 2–3 small PRs from a fresh Codex context and compare:

- findings against the existing review process;
- false positives;
- token/time overhead;
- whether any finding changes the resulting code.

Only then decide whether to keep, alter, or remove this pilot.
