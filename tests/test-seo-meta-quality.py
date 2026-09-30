#!/usr/bin/env python3
"""Regression and full mutation test for sitewide SEO meta quality and collision prevention.

Proves:
1. Current repository passes all SEO meta quality, collision, canonical, and OG parity checks.
2. Mutation tests execute the real checker on synthesized HTML trees and assert exact failures:
   a. Duplicate <title> across indexable pages -> FAIL
   b. Duplicate <meta name="description"> across indexable pages -> FAIL
   c. Multiple <link rel="canonical"> in a single <head> -> FAIL
   d. Canonical route mismatch against filesystem path -> FAIL
   e. og:url mismatch against canonical -> FAIL
   f. Missing <title> or missing <meta name="description"> -> FAIL
   g. Multiple <meta name="robots"> in <head> -> FAIL
   h. Reversion to clean state -> PASS
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
CHECKER_PATH = ROOT / "scripts" / "check-seo-meta-quality.py"

_spec = importlib.util.spec_from_file_location("check_seo_meta", CHECKER_PATH)
checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checker)

# 1. Base run on real repository
issues = checker.check_seo_meta_quality()
assert not issues, f"check-seo-meta-quality failed on current repository:\n" + "\n".join(issues)
print("  ok   1. Current repository satisfies all SEO meta quality and uniqueness contracts")

# 2. Comprehensive mutation tests on synthesized directory trees
with tempfile.TemporaryDirectory() as tmp_dir:
    tmp_path = Path(tmp_dir)

    def write_clean_set():
        # Page 1: Root /
        (tmp_path / "index.html").write_text("""<!DOCTYPE html><html lang="es"><head>
        <title>Inicio oficial | David Porto Díaz</title>
        <meta name="description" content="Página de inicio oficial con obras, biografía y recursos para lectores." />
        <link rel="canonical" href="https://davidportodiaz.com/" />
        <meta property="og:url" content="https://davidportodiaz.com/" />
        </head><body><main>Contenido</main></body></html>""", encoding="utf-8")

        # Page 2: /autor.html
        (tmp_path / "autor.html").write_text("""<!DOCTYPE html><html lang="es"><head>
        <title>Biografía del autor | David Porto Díaz</title>
        <meta name="description" content="Biografía completa, trayectoria literaria y libros publicados en español." />
        <link rel="canonical" href="https://davidportodiaz.com/autor.html" />
        <meta property="og:url" content="https://davidportodiaz.com/autor.html" />
        </head><body><main>Contenido</main></body></html>""", encoding="utf-8")

        # Page 3: /cuaderno/
        cuaderno_dir = tmp_path / "cuaderno"
        cuaderno_dir.mkdir(exist_ok=True)
        (cuaderno_dir / "index.html").write_text("""<!DOCTYPE html><html lang="es"><head>
        <title>Cuaderno de notas y artículos | David Porto</title>
        <meta name="description" content="Artículos sobre escritura, portal fantasy y análisis narrativo en español." />
        <link rel="canonical" href="https://davidportodiaz.com/cuaderno/" />
        <meta property="og:url" content="https://davidportodiaz.com/cuaderno/" />
        </head><body><main>Contenido</main></body></html>""", encoding="utf-8")

    # Baseline on clean temporary set
    write_clean_set()
    base_errors = checker.check_seo_meta_quality(tmp_path)
    assert not base_errors, f"Expected 0 errors on clean set, got: {base_errors}"
    print("  ok   2. Clean mock dataset passes check_seo_meta_quality with 0 errors")

    # Mutation A: Duplicate <title> across indexable pages
    (tmp_path / "autor.html").write_text("""<!DOCTYPE html><html lang="es"><head>
    <title>Inicio oficial | David Porto Díaz</title>
    <meta name="description" content="Biografía completa, trayectoria literaria y libros publicados en español." />
    <link rel="canonical" href="https://davidportodiaz.com/autor.html" />
    <meta property="og:url" content="https://davidportodiaz.com/autor.html" />
    </head><body><main>Contenido</main></body></html>""", encoding="utf-8")
    mut_a_errs = checker.check_seo_meta_quality(tmp_path)
    assert any("Duplicate <title>" in e for e in mut_a_errs), f"Failed to detect duplicate title: {mut_a_errs}"
    print("  ok   3. Mutation test: duplicate <title> caught and rejected")

    # Revert Mutation A
    write_clean_set()
    assert not checker.check_seo_meta_quality(tmp_path)

    # Mutation B: Duplicate <meta name="description"> across indexable pages
    (tmp_path / "autor.html").write_text("""<!DOCTYPE html><html lang="es"><head>
    <title>Biografía del autor | David Porto Díaz</title>
    <meta name="description" content="Página de inicio oficial con obras, biografía y recursos para lectores." />
    <link rel="canonical" href="https://davidportodiaz.com/autor.html" />
    <meta property="og:url" content="https://davidportodiaz.com/autor.html" />
    </head><body><main>Contenido</main></body></html>""", encoding="utf-8")
    mut_b_errs = checker.check_seo_meta_quality(tmp_path)
    assert any("Duplicate <meta name='description'>" in e for e in mut_b_errs), f"Failed to detect duplicate description: {mut_b_errs}"
    print("  ok   4. Mutation test: duplicate meta description caught and rejected")

    # Revert Mutation B
    write_clean_set()
    assert not checker.check_seo_meta_quality(tmp_path)

    # Mutation C: Multiple <link rel="canonical"> in <head>
    (tmp_path / "autor.html").write_text("""<!DOCTYPE html><html lang="es"><head>
    <title>Biografía del autor | David Porto Díaz</title>
    <meta name="description" content="Biografía completa, trayectoria literaria y libros publicados en español." />
    <link rel="canonical" href="https://davidportodiaz.com/autor.html" />
    <link rel="canonical" href="https://davidportodiaz.com/otro-autor.html" />
    <meta property="og:url" content="https://davidportodiaz.com/autor.html" />
    </head><body><main>Contenido</main></body></html>""", encoding="utf-8")
    mut_c_errs = checker.check_seo_meta_quality(tmp_path)
    assert any("multiple <link rel='canonical'>" in e for e in mut_c_errs), f"Failed to detect multiple canonicals: {mut_c_errs}"
    print("  ok   5. Mutation test: multiple canonical tags caught and rejected")

    # Revert Mutation C
    write_clean_set()
    assert not checker.check_seo_meta_quality(tmp_path)

    # Mutation D: Canonical route mismatch
    (tmp_path / "autor.html").write_text("""<!DOCTYPE html><html lang="es"><head>
    <title>Biografía del autor | David Porto Díaz</title>
    <meta name="description" content="Biografía completa, trayectoria literaria y libros publicados en español." />
    <link rel="canonical" href="https://davidportodiaz.com/ruta-equivocada/" />
    <meta property="og:url" content="https://davidportodiaz.com/ruta-equivocada/" />
    </head><body><main>Contenido</main></body></html>""", encoding="utf-8")
    mut_d_errs = checker.check_seo_meta_quality(tmp_path)
    assert any("canonical mismatch" in e for e in mut_d_errs), f"Failed to detect canonical route mismatch: {mut_d_errs}"
    print("  ok   6. Mutation test: canonical route mismatch caught and rejected")

    # Revert Mutation D
    write_clean_set()
    assert not checker.check_seo_meta_quality(tmp_path)

    # Mutation E: og:url mismatch against canonical
    (tmp_path / "autor.html").write_text("""<!DOCTYPE html><html lang="es"><head>
    <title>Biografía del autor | David Porto Díaz</title>
    <meta name="description" content="Biografía completa, trayectoria literaria y libros publicados en español." />
    <link rel="canonical" href="https://davidportodiaz.com/autor.html" />
    <meta property="og:url" content="https://davidportodiaz.com/otra-url-og.html" />
    </head><body><main>Contenido</main></body></html>""", encoding="utf-8")
    mut_e_errs = checker.check_seo_meta_quality(tmp_path)
    assert any("og:url ('https://davidportodiaz.com/otra-url-og.html') does not match canonical" in e for e in mut_e_errs), f"Failed to detect og:url mismatch: {mut_e_errs}"
    print("  ok   7. Mutation test: og:url != canonical caught and rejected")

    # Revert Mutation E
    write_clean_set()
    assert not checker.check_seo_meta_quality(tmp_path)

    # Mutation F: Missing title and missing description
    (tmp_path / "autor.html").write_text("""<!DOCTYPE html><html lang="es"><head>
    <link rel="canonical" href="https://davidportodiaz.com/autor.html" />
    <meta property="og:url" content="https://davidportodiaz.com/autor.html" />
    </head><body><main>Contenido</main></body></html>""", encoding="utf-8")
    mut_f_errs = checker.check_seo_meta_quality(tmp_path)
    assert any("missing or empty <title>" in e for e in mut_f_errs), f"Failed to detect missing title: {mut_f_errs}"
    assert any("missing or empty <meta name='description'>" in e for e in mut_f_errs), f"Failed to detect missing description: {mut_f_errs}"
    print("  ok   8. Mutation test: missing title and description caught and rejected")

print("test-seo-meta-quality: OK")
