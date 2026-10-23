#!/usr/bin/env python3
"""Focused regression tests for the repo -> public artifact boundary."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "scripts" / "build-public-dist.py"

spec = importlib.util.spec_from_file_location("build_public_dist", BUILDER_PATH)
assert spec and spec.loader
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def assert_public(path: str) -> None:
    assert builder.is_publishable(path, ROOT), f"expected public: {path}"


def assert_private(path: str) -> None:
    assert not builder.is_publishable(path, ROOT), f"expected private: {path}"


def main() -> None:
    # Known runtime families must survive an allowlist-first build.
    for path in (
        "index.html",
        "ai/index.html",
        "assets/v1-shell.css",
        "assets/assistant-local-knowledge.mjs",
        "pagefind/pagefind-ui.js",
        "press-kit/david-porto-diaz.json",
        "press-kit/las-manecillas-del-recuerdo.json",
        "press-kit/samuel-entre-mundos.json",
        "manifest.json",
        "service-worker.js",
        "offline.html",
        "robots.txt",
        "sitemap.xml",
        "llms.txt",
        "llms-full.txt",
    ):
        assert_public(path)

    # Operational material is private by default. The final six cases prove
    # defense in depth even when a technical file is placed under /assets/.
    for path in (
        "docs/new-runbook.md",
        "apoyar/index.html",  # Inactivo: no es publicable por una simple carpeta
        "apoyar/README.md",  # Never expose deployment/activation notes
        "apoyar/.env",
        "apoyar/private.key",
        "qa/new-browser-check.mjs",
        "lab/new-prototype/index.html",
        "migrations/future.sql",
        "scripts/new-build-step.py",
        "tests/new-fixture.json",
        "data/new-internal-contract.json",
        "cloudflare-worker-assistant.js",
        "wrangler.assistant.jsonc",
        "wrangler.assistant.example.jsonc",
        "package.json",
        "package-lock.json",
        "lighthouserc.json",
        "lighthouserc-pro-resources.json",
        "editorial-facts.json",
        "press-kit/package-manifest.json",
        "donde-empieza-la-jaula/index.html",
        "assets/internal.sql",
        "assets/wrangler.future.jsonc",
        "assets/cloudflare-worker-future.js",
        "assets/package.json",
        "assets/private.key",
        "assets/terraform.tfstate",
    ):
        assert_private(path)

    rendered = builder.render_assetsignore(ROOT)
    current = (ROOT / ".assetsignore").read_text(encoding="utf-8")
    assert rendered == current, ".assetsignore must be generated from builder policy"
    assert "/*\n" in rendered, "assetsignore must start from a root deny"
    assert "!/assets/" in rendered
    assert "!/apoyar/" in rendered, "El namespace existe pero está protegido"
    assert "\n/apoyar/\n" in rendered, (
        "Cloudflare no debe publicar apoyos antes de que el registry los autorice"
    )

    # El builder y .assetsignore usan la MISMA fuente de verdad para pasar de
    # "cerrado" a "abierto". Simularlo solo en un directorio temporal.
    with tempfile.TemporaryDirectory() as tmp:
        fixture = Path(tmp)
        (fixture / "data").mkdir()
        subprocess.run(["git", "init", "-q"], cwd=fixture, check=True, capture_output=True)
        registry_path = fixture / "data" / "content-registry.json"
        registry = {"defaults": {"status": "public"}, "entries": []}

        def write_registry() -> None:
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

        def assetsignore_blocks(path: str) -> bool:
            # .assetsignore usa sintaxis gitignore: evaluar reglas reales con git.
            (fixture / ".gitignore").write_text(
                builder.render_assetsignore(fixture), encoding="utf-8"
            )
            result = subprocess.run(
                ["git", "check-ignore", "--no-index", "--quiet", path],
                cwd=fixture, capture_output=True, text=True,
            )
            assert result.returncode in (0, 1), result.stderr
            return result.returncode == 0

        write_registry()
        assert not builder.is_publishable("apoyar/index.html", fixture)
        assert "\n/apoyar/\n" in builder.render_assetsignore(fixture)
        assert assetsignore_blocks("apoyar/index.html")
        assert assetsignore_blocks("apoyar/preview.html")

        support = {"id": "support-project", "url": "/apoyar/",
                   "sourceFile": "apoyar/index.html", "status": "gated"}
        registry["entries"].append(support)
        write_registry()
        assert not builder.is_publishable("apoyar/index.html", fixture)
        support["status"] = "public"
        support["sourceFile"] = "otra-ruta/index.html"
        write_registry()
        assert not builder.is_publishable("apoyar/index.html", fixture)
        support["sourceFile"] = "apoyar/index.html"
        write_registry()
        assert builder.is_publishable("apoyar/index.html", fixture)
        for incidental in (
            "apoyar/preview.html", "apoyar/debug.json", "apoyar/otra/index.html"
        ):
            assert not builder.is_publishable(incidental, fixture), incidental
        policy = builder.render_assetsignore(fixture)
        assert "\n/apoyar/*\n!/apoyar/index.html\n" in policy
        assert not assetsignore_blocks("apoyar/index.html")
        for incidental in (
            "apoyar/preview.html", "apoyar/debug.json", "apoyar/otra/index.html",
            "apoyar/private.key",
        ):
            assert assetsignore_blocks(incidental), incidental
        assert not assetsignore_blocks("assets/v1-shell.css")
        # El registry tiene public por defecto: no abrir por herencia.
        del support["status"]
        write_registry()
        assert not builder.is_publishable("apoyar/index.html", fixture)
        assert "\n/apoyar/\n" in builder.render_assetsignore(fixture)
        assert assetsignore_blocks("apoyar/index.html")
        support["status"] = "public"
        write_registry()
        assert builder.is_publishable("apoyar/index.html", fixture)
        assert "\n/apoyar/\n" not in builder.render_assetsignore(fixture)
        registry["entries"].append(dict(support))
        write_registry()
        assert not builder.is_publishable("apoyar/index.html", fixture)
        assert assetsignore_blocks("apoyar/index.html")

        # URL incorrecta y registros malformados: siempre cerrado, nunca abierto.
        registry["entries"] = [dict(support, url="/apoyar")]
        write_registry()
        assert not builder.is_publishable("apoyar/index.html", fixture)
        registry["entries"] = [dict(support, url="https://example.com/apoyar/")]
        write_registry()
        assert not builder.is_publishable("apoyar/index.html", fixture)
        for malformed in ('{"entries": "apoyar"}', '{"entries": ["x", 1, null]}', '[]'):
            registry_path.write_text(malformed, encoding="utf-8")
            assert builder.support_page_authorized(fixture) is False, malformed

    assert "!/pagefind/" in rendered
    assert "/press-kit/package-manifest.json" in rendered
    assert "**/wrangler*.jsonc" in rendered
    assert "**/*.sql" in rendered

    print("OK: public artifact contract regression tests passed.")


if __name__ == "__main__":
    main()
