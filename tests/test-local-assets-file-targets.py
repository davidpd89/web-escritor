#!/usr/bin/env python3
"""Local asset targets must resolve to files, never directories."""
from __future__ import annotations
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "check-local-assets.py"
spec = importlib.util.spec_from_file_location("qa_local_file_targets", PATH)
assert spec is not None and spec.loader is not None
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def html_audit(root: Path, markup: str) -> list[str]:
    page = root / "case.html"
    page.write_text("<!doctype html>" + markup, encoding="utf-8")
    return checker.audit_file(page, root)


def js_audit(root: Path, code: str) -> list[str]:
    page = root / "assets" / "main.js"
    page.write_text(code, encoding="utf-8")
    return checker.audit_js_imports(root)


def css_audit(root: Path, code: str) -> list[str]:
    page = root / "assets" / "main.css"
    page.write_text(code, encoding="utf-8")
    return checker.audit_css_urls(root)


failures: list[str] = []
with tempfile.TemporaryDirectory(prefix="qa-asset-files-") as temp:
    root = Path(temp)
    assets = root / "assets"
    assets.mkdir()
    (assets / "icons").mkdir()
    (assets / "modules").mkdir()
    (assets / "cover.png").write_bytes(b"fixture")
    (assets / "app.js").write_text("export const ready = true;\n", encoding="utf-8")
    (assets / "site.css").write_text("body {}\n", encoding="utf-8")

    html_good = {
        "existing image": '<img src="/assets/cover.png" alt="">',
        "stylesheet query": '<link rel="stylesheet" href="/assets/site.css?v=1">',
        "script file": '<script src="/assets/app.js"></script>',
        "responsive source": '<source srcset="/assets/cover.png 1x">',
    }
    html_bad = {
        "image directory": '<img src="/assets/icons/" alt="">',
        "script directory": '<script src="/assets/modules/"></script>',
        "stylesheet directory": '<link rel="stylesheet" href="/assets/">',
        "source directory": '<source srcset="/assets/icons/ 1x">',
        "missing file": '<img src="/assets/absent.png" alt="">',
    }
    for name, html in html_good.items():
        if got := html_audit(root, html):
            failures.append(f"GOOD HTML {name}: {got}")
    for name, html in html_bad.items():
        if not (got := html_audit(root, html)):
            failures.append(f"BAD HTML {name}: accepted")

    js_cases = (
        ("valid static import", "import {ready} from './app.js';", False),
        ("directory static import", "import {ready} from './modules/';", True),
        ("valid dynamic import", "import('./app.js')", False),
        ("directory dynamic import", "import('./modules/')", True),
        ("valid worker", "new Worker('./app.js')", False),
        ("directory worker", "new Worker('./modules/')", True),
        ("valid importScripts", "importScripts('./app.js')", False),
        ("directory importScripts", "importScripts('./modules/')", True),
        ("valid re-export", "export {ready} from './app.js'", False),
        ("directory re-export", "export {ready} from './modules/'", True),
    )
    for name, code, should_fail in js_cases:
        got = js_audit(root, code)
        if bool(got) != should_fail:
            failures.append(f"JS {name}: {got}")
    css_cases = (
        ("valid CSS file", 'body {background: url("./cover.png")}', False),
        ("directory in CSS", 'body {background: url("./icons/")}', True),
    )
    for name, code, should_fail in css_cases:
        got = css_audit(root, code)
        if bool(got) != should_fail:
            failures.append(f"CSS {name}: {got}")

if failures:
    for issue in failures:
        print("FAIL", issue)
    raise SystemExit(1)
print("PASS local asset file target mutations: 10 valid + 11 invalid")
