#!/usr/bin/env python3
"""Mutation tests for extraction of JSON-LD script blocks."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "check-jsonld-absolute-urls.py"
spec = importlib.util.spec_from_file_location("qa_jsonld_scripts", PATH)
assert spec is not None and spec.loader is not None
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

BAD_URL = '{"@context":"https://schema.org","url":"/libros/"}'
GOOD_URL = '{"@context":"https://schema.org","url":"https://davidportodiaz.com/libros/"}'


def script(attrs: str, data: str = BAD_URL) -> str:
    return f"<script {attrs}>{data}</script>"


def findings(markup: str) -> tuple[int, list[str]]:
    errors: list[str] = []
    blocks = checker.jsonld_blocks(markup)
    for block in blocks:
        checker.walk(json.loads(block), "$", errors)
    return len(blocks), errors


DETECTED = {
    "double quotes": script('type="application/ld+json"'),
    "single quotes": script("type='application/ld+json'"),
    "unquoted": script("type=application/ld+json"),
    "spaces near equals": script('type = "application/ld+json"'),
    "uppercase": '<SCRIPT TYPE=APPLICATION/LD+JSON>' + BAD_URL + '</SCRIPT>',
    "type after attributes": script('id="metadata" data-role="main" type="application/ld+json"'),
    "greater than in attribute": script('data-note="a>b" type="application/ld+json"'),
    "entity in MIME type": script('type="application/ld&#43;json"'),
    "spaces in MIME type": script('type=" application/ld+json "'),
}
IGNORED = {
    "comment": "<!-- " + script('type="application/ld+json"') + " -->",
    "ordinary JS": script('type="text/javascript"'),
    "data-type": script('data-type="application/ld+json"'),
    "similar MIME": script('type="application/ld+json-extra"'),
    "fake script in attribute": (
        "<div data-payload='<script type=\"application/ld+json\">"
        + BAD_URL + "</script>'></div>"
    ),
    "script string": '<script>const str = "' + script('type="application/ld+json"') + '";</script>',
}
failures: list[str] = []
for name, markup in DETECTED.items():
    blocks, errors = findings(markup)
    if blocks != 1 or len(errors) != 1 or "/libros/" not in errors[0]:
        failures.append(f"DETECTED {name}: blocks={blocks} errors={errors}")
for name, markup in IGNORED.items():
    blocks = checker.jsonld_blocks(markup)
    if blocks:
        failures.append(f"IGNORED {name}: {blocks}")
for name, markup, count, expected in (
    ("absolute URL", script('type="application/ld+json"', GOOD_URL), 1, 0),
    ("two actual scripts", script('type="application/ld+json"') + script('type=application/ld+json'), 2, 2),
):
    blocks, errors = findings(markup)
    if blocks != count or len(errors) != expected:
        failures.append(f"MIXED {name}: blocks={blocks} errors={errors}")
if failures:
    for issue in failures:
        print("FAIL", issue)
    raise SystemExit(1)
print(f"PASS JSON-LD scripts: {len(DETECTED)} detected + {len(IGNORED)} ignored + 2 mixed")
