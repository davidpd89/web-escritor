#!/usr/bin/env python3
"""Focused regression tests for the repo -> public artifact boundary."""
from __future__ import annotations

import importlib.util
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
    assert "!/pagefind/" in rendered
    assert "/press-kit/package-manifest.json" in rendered
    assert "**/wrangler*.jsonc" in rendered
    assert "**/*.sql" in rendered

    print("OK: public artifact contract regression tests passed.")


if __name__ == "__main__":
    main()
