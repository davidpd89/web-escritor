# Coding Standards

This file contains review standards that require engineering judgement and are
not cheaper to enforce with an existing deterministic check. Mechanical rules
belong in tests/CI instead.

## Regression tests and QA

1. **Test the contract, not incidental serialization.**
   A regression test should survive harmless refactors or formatting changes
   when observable behaviour is unchanged. Exact HTML/CSS/JSON strings are
   appropriate only when that serialization is itself the contract.

2. **Name the regression the test can catch.**
   A new regression test must have a concrete failure mode: describe what
   change would make it go red. "Adds coverage" is not sufficient on its own.

3. **Prefer the highest stable seam available.**
   Verify behaviour through the closest stable public/file contract that
   represents the real failure. Avoid testing helper internals merely because
   they are easier to assert.

4. **Do not duplicate an existing guardrail without a distinct gap.**
   When a nearby test or CI job already covers the area, state the uncovered
   case the new test adds. If no distinct failure mode exists, extend or reuse
   the existing check instead.

5. **Test-only PRs stay test-only unless a failure is proved.**
   Do not mix opportunistic production/content changes into a regression-test
   PR. If the new test exposes a real defect, fix that defect in a separate,
   clearly-scoped change or document why the same PR must contain both.

6. **Evidence beats a green badge.**
   CI success proves the current suite passed. Review must still check that the
   new test is sensitive to its promised regression and resistant to obvious
   false positives.
