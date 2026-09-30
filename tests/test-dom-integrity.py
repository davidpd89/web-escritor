#!/usr/bin/env python3
"""Regression and mutation test for DOM integrity, ARIA resolution, and interactive nesting rules.

Proves:
1. Current repository passes all DOM integrity checks (unique IDs, valid label targets, valid ARIA refs).
2. Mutation tests fail loudly:
   a. Duplicate id within document -> FAIL
   b. <label for="unknown_id"> -> FAIL
   c. aria-labelledby pointing to missing ID -> FAIL
   d. <button> inside <a> -> FAIL
   e. <a> inside <button> -> FAIL
"""
from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "scripts" / "check-dom-integrity.py"

_spec = importlib.util.spec_from_file_location("check_dom", CHECKER_PATH)
checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checker)

# 1. Base run on real repository
issues = checker.check_dom_integrity_sitewide()
assert not issues, f"check-dom-integrity failed on current repository:\n" + "\n".join(issues)
print("  ok   1. Current repository satisfies all DOM integrity contracts")

# 2. Mutation testing: duplicate IDs
with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write("""<!DOCTYPE html><html lang="es"><body>
    <div id="duplicate-target">First</div>
    <div id="duplicate-target">Second</div>
    </body></html>""")
    tmp_path = Path(f.name)

try:
    mut_issues = checker.check_html_file(tmp_path)
    assert any("duplicate id='duplicate-target'" in err for err in mut_issues), f"Failed to detect duplicate ID: {mut_issues}"
    print("  ok   2. Mutation test: duplicate ID detected")
finally:
    tmp_path.unlink(missing_ok=True)

# 3. Mutation testing: broken label[for]
with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write("""<!DOCTYPE html><html lang="es"><body>
    <label for="non-existent-input">Etiqueta huérfana</label>
    <input id="real-input" type="text" />
    </body></html>""")
    tmp_path = Path(f.name)

try:
    mut_issues = checker.check_html_file(tmp_path)
    assert any("for='non-existent-input'" in err for err in mut_issues), f"Failed to detect broken label: {mut_issues}"
    print("  ok   3. Mutation test: broken label[for] detected")
finally:
    tmp_path.unlink(missing_ok=True)

# 4. Mutation testing: broken aria-describedby
with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write("""<!DOCTYPE html><html lang="es"><body>
    <button type="button" aria-describedby="missing-help-text">Botón</button>
    </body></html>""")
    tmp_path = Path(f.name)

try:
    mut_issues = checker.check_html_file(tmp_path)
    assert any("aria-describedby='missing-help-text'" in err for err in mut_issues), f"Failed to detect broken aria ref: {mut_issues}"
    print("  ok   4. Mutation test: broken aria reference detected")
finally:
    tmp_path.unlink(missing_ok=True)

# 5. Mutation testing: interactive element nesting (<button> inside <a>)
with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write("""<!DOCTYPE html><html lang="es"><body>
    <a href="/test/"><button type="button">Botón anidado en enlace</button></a>
    </body></html>""")
    tmp_path = Path(f.name)

try:
    mut_issues = checker.check_html_file(tmp_path)
    assert any("invalid interactive nesting <button> inside <a>" in err for err in mut_issues), f"Failed to detect invalid nesting: {mut_issues}"
    print("  ok   5. Mutation test: invalid interactive nesting (<button> in <a>) detected")
finally:
    tmp_path.unlink(missing_ok=True)

# 6. Mutation testing: interactive select inside <button>
with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write("""<!DOCTYPE html><html lang="es"><body>
    <button type="button"><select><option>1</option></select></button>
    </body></html>""")
    tmp_path = Path(f.name)

try:
    mut_issues = checker.check_html_file(tmp_path)
    assert any("invalid interactive nesting <select> inside <button>" in err for err in mut_issues), f"Failed to detect invalid nesting: {mut_issues}"
    print("  ok   6. Mutation test: invalid interactive nesting (<select> in <button>) detected")
finally:
    tmp_path.unlink(missing_ok=True)

# 7. Mutation testing: broken aria-owns reference
with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write("""<!DOCTYPE html><html lang="es"><body>
    <div role="list" aria-owns="missing-listitem-id"></div>
    </body></html>""")
    tmp_path = Path(f.name)

try:
    mut_issues = checker.check_html_file(tmp_path)
    assert any("aria-owns='missing-listitem-id'" in err for err in mut_issues), f"Failed to detect broken aria-owns: {mut_issues}"
    print("  ok   7. Mutation test: broken aria-owns detected")
finally:
    tmp_path.unlink(missing_ok=True)

print("test-dom-integrity: OK")
