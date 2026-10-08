#!/usr/bin/env python3
"""Mutation fixtures for exact label[for], labelable targets and ARIA IDREFs."""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-dom-integrity.py"
spec = importlib.util.spec_from_file_location("dom_labelable", CHECKER)
assert spec is not None and spec.loader is not None
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def findings(fragment: str) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="qa-dom-labelable-") as folder:
        page = Path(folder) / "fixture.html"
        page.write_text('<!doctype html><html lang="es"><body>' + fragment +
                        '</body></html>', encoding="utf-8")
        return checker.check_html_file(page)


GOOD = {
    "forward input": '<label for="q">Consulta</label><input id="q">',
    "backward textarea": '<textarea id="q"></textarea><label for="q">Consulta</label>',
    "select": '<label for="q">Filtro</label><select id="q"></select>',
    "button": '<label for="q">Acción</label><button id="q">Enviar</button>',
    "meter": '<label for="q">Nivel</label><meter id="q"></meter>',
    "output": '<label for="q">Salida</label><output id="q"></output>',
    "progress": '<label for="q">Avance</label><progress id="q"></progress>',
    "uppercase text input": '<label for="q">Nombre</label><input id="q" type="TEXT">',
    "custom element conservatively allowed": '<label for="q">Custom</label><x-input id="q"></x-input>',
    "entity in for": '<label for="q&#49;">Número</label><input id="q1">',
    "nonbreaking space in ARIA ID": '<span id="nombre\u00a0completo">N</span><input aria-labelledby="nombre\u00a0completo">',
    "nonbreaking space label target": '<label for="a\u00a0b">N</label><input id="a\u00a0b">',
}
BAD = {
    "div target": ('<label for="q">L</label><div id="q">X</div>', 'non-labelable <div>'),
    "span target": ('<label for="q">L</label><span id="q">X</span>', 'non-labelable <span>'),
    "image target": ('<label for="q">L</label><img id="q" alt="">', 'non-labelable <img>'),
    "hidden input": ('<label for="q">L</label><input id="q" type="hidden">', "non-labelable <input type='hidden'>"),
    "uppercase hidden": ('<label for="q">L</label><input id="q" type="HIDDEN">', "non-labelable <input type='hidden'>"),
    "missing id": ('<label for="absent">L</label>', 'non-existent id'),
    "leading whitespace in for": ('<label for=" q">L</label><input id="q">', 'non-existent id'),
    "trailing whitespace in for": ('<label for="q ">L</label><input id="q">', 'non-existent id'),
    "leading whitespace in id": ('<label for="q">L</label><input id=" q">', 'non-existent id'),
    "case sensitive": ('<label for="Q">L</label><input id="q">', 'non-existent id'),
    "empty for": ('<label for="">L</label><input id="q">', 'non-existent id'),
    "leading whitespace in aria id": ('<span id=" nombre">N</span><input aria-labelledby="nombre">', "aria-labelledby='nombre' points to non-existent id"),
    "non-breaking space in aria ref": ('<span id="nombre">N</span><input aria-labelledby="nomb\u00a0re">', "aria-labelledby='nomb\u00a0re' points to non-existent id"),
    "ASCII whitespace splits refs": ('<span id="uno">U</span><input aria-labelledby="uno dos">', "aria-labelledby='dos' points to non-existent id"),
    "different id with whitespace": ('<div id=" abc"></div><div id="abc"></div><label for=" abc">L</label>', 'non-labelable <div>'),
    "first duplicate is not labelable": ('<label for="q">L</label><div id="q"></div><input id="q">', 'non-labelable <div>'),
}
failures = []
for name, markup in GOOD.items():
    issues = findings(markup)
    if issues:
        failures.append(f"GOOD {name}: {issues!r}")
for name, (markup, expected) in BAD.items():
    issues = findings(markup)
    if not any(expected in issue for issue in issues):
        failures.append(f"BAD {name}: expected {expected!r}, got {issues!r}")
if failures:
    for failure in failures:
        print("FAIL", failure)
    raise SystemExit(1)
print(f"PASS DOM labelable: {len(GOOD)} positive + {len(BAD)} negative")
