#!/usr/bin/env python3
"""Contrato del selector de Sitewide Reflow: omitir solo si es seguro."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("sel", Path(__file__).resolve().parents[1] / "scripts" / "ci-select-reflow.py")
sel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sel)

CASOS = [
    (["scripts/reading_planeta_source.py", "tests/test-reading-planeta-source.py"], False),  # PR #815
    (["README.md", "docs/x.md", ".ci/informe.md"], False),
    (["assets/styles.css"], True),
    (["assets/script.js"], True),
    (["libros/index.html"], True),
    (["data/navigation.json"], True),
    (["sitemap.xml"], True),
    (["scripts/build-sitemap.py"], True),
    (["scripts/site_shell.py"], True),
    (["qa/sitewide-reflow-browser.mjs"], True),
    (["package-lock.json"], True),
    (["scripts/reading_planeta_source.py", "assets/styles.css"], True),  # mixto
    (["archivo-desconocido.bin"], True),
    ([".github/workflows/sitewide-reflow-qa.yml"], True),
    ([".github/workflows/otro.yml"], False),
    ([], True),
]
fallos = 0
for files, esperado in CASOS:
    run, why = sel.classify(files)
    if run != esperado:
        fallos += 1
        print(f"FALLA {files}: run={run} esperado={esperado} ({why})")
if fallos:
    raise SystemExit(1)
print(f"ok: {len(CASOS)} casos")
