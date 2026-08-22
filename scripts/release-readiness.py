#!/usr/bin/env python3
"""Generate a release-readiness evidence report for pre-main human review.

This script does not deploy and does not merge. It runs the required checks,
captures PASS/FAIL results, records repository HEAD metadata, verifies key
routes from sitemap.xml, and writes a Markdown evidence report.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://davidportodiaz.com"

CHECKS = [
    ("CI parity: content indexes", "python scripts/check-local-assets.py"),
    ("CI parity: hrefs", "python scripts/check-hrefs.py"),
    ("CI parity: internal graph", "python scripts/check-internal-graph.py"),
    ("CI parity: navigation coverage", "python scripts/check-navigation-coverage.py"),
    ("CI parity: heading structure", "python scripts/check-heading-structure.py"),
    ("CI parity: jsonld absolute URLs", "python scripts/check-jsonld-absolute-urls.py"),
    ("CI parity: canonical entity IDs", "python scripts/check-canonical-entity-ids.py"),
    ("CI parity: editorial facts", "python scripts/check-editorial-facts.py"),
    ("CI parity: AI discoverability", "python scripts/check-ai-discoverability.py"),
    ("CI parity: social cards strict", "python scripts/check-social-cards.py --strict"),
    ("CI parity: copy tildes", "python scripts/check-copy-tildes.py"),
    ("Authority: machine-readable contract", "python tests/test-machine-authority.py"),
    ("Builder parity: editoriales", "python tests/test-editoriales-builder-parity-v1.py"),
    ("Builder parity: convocatorias", "python tests/test-radar-builder-parity-v1.py"),
    ("Newsletter: client contract", "node tests/test-newsletter-client-contract.mjs"),
    ("Newsletter: worker contract", "node qa/newsletter-worker-contract.mjs"),
    ("Newsletter: staging gate", "node tests/test-staging-newsletter-disable.mjs"),
    ("Social card regression guard", "python tests/test-social-card-article-specific.py"),
]

ROUTE_CHECKS = [
    ("/", "sitemap"),
    ("/las-manecillas-del-recuerdo/", "sitemap"),
    ("/libros/samuel-entre-mundos/", "sitemap"),
    ("/autor.html", "sitemap"),
    ("/cuaderno/", "sitemap"),
    ("/herramientas/", "sitemap"),
    ("/recomendaciones/", "sitemap"),
    ("/editoriales/", "sitemap"),
    ("/prensa.html", "sitemap"),
    ("/eventos.html", "sitemap"),
    ("/asistente/", "file"),
    ("/privacidad.html", "file"),
    ("/aviso-legal.html", "file"),
    ("/sitemap.xml", "file"),
    ("/llms.txt", "file"),
    ("/robots.txt", "file"),
]


def run(cmd: str) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        shell=True,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def git_output(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return "UNKNOWN"
    return proc.stdout.strip()


def load_sitemap_urls() -> set[str]:
    sitemap = ROOT / "sitemap.xml"
    if not sitemap.exists():
        return set()
    tree = ET.parse(sitemap)
    root = tree.getroot()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = set()
    for node in root.findall("sm:url/sm:loc", ns):
        value = (node.text or "").strip()
        if value:
            urls.add(value)
    return urls


def route_to_repo_path(route: str) -> Path:
    clean = route.lstrip("/")
    if not clean:
        return ROOT / "index.html"
    if route.endswith("/"):
        return ROOT / clean / "index.html"
    return ROOT / clean


def route_in_sitemap(route: str, sitemap_urls: set[str]) -> bool:
    if route == "/":
        return f"{SITE}/" in sitemap_urls or SITE in sitemap_urls
    return f"{SITE}{route}" in sitemap_urls


def status_label(code: int) -> str:
    return "PASS" if code == 0 else "FAIL"


def clip(text: str, limit: int = 900) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... [truncated]"


def build_report(output: Path) -> int:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    head = git_output(["rev-parse", "HEAD"])
    branch = git_output(["branch", "--show-current"])
    prev = git_output(["rev-parse", "HEAD~1"])
    commits = git_output(["log", "--oneline", "-20"])

    checks_data: list[dict[str, str | int]] = []
    failures = 0
    for label, command in CHECKS:
        code, out = run(command)
        checks_data.append(
            {
                "label": label,
                "command": command,
                "status": status_label(code),
                "exit_code": code,
                "output": clip(out),
            }
        )
        if code != 0:
            failures += 1

    sitemap_urls = load_sitemap_urls()
    route_results = []
    for route, mode in ROUTE_CHECKS:
        if mode == "sitemap":
            ok = route_in_sitemap(route, sitemap_urls)
        else:
            ok = route_to_repo_path(route).exists()
        route_results.append((route, mode, "PASS" if ok else "FAIL"))
        if not ok:
            failures += 1

    summary = "READY_FOR_HUMAN_MAIN_REVIEW" if failures == 0 else "BLOCKED"

    lines: list[str] = []
    lines.append("# Release Readiness Evidence V1")
    lines.append("")
    lines.append(f"- Generated: `{now}`")
    lines.append(f"- Branch: `{branch}`")
    lines.append(f"- HEAD: `{head}`")
    lines.append(f"- Previous SHA (rollback candidate): `{prev}`")
    lines.append("")
    lines.append(f"## Final Status: `{summary}`")
    lines.append("")
    lines.append("## Commit Window (latest 20)")
    lines.append("")
    lines.append("```text")
    lines.append(commits or "UNKNOWN")
    lines.append("```")
    lines.append("")
    lines.append("## Required Route Inventory")
    lines.append("")
    lines.append("| Route | Validation | Status |")
    lines.append("|---|---|---|")
    for route, mode, status in route_results:
        lines.append(f"| `{route}` | `{mode}` | `{status}` |")
    lines.append("")
    lines.append("## Automated Evidence Checks")
    lines.append("")
    lines.append("| Check | Command | Status |")
    lines.append("|---|---|---|")
    for item in checks_data:
        lines.append(f"| {item['label']} | `{item['command']}` | `{item['status']}` |")

    lines.append("")
    lines.append("## Output Excerpts")
    lines.append("")
    for item in checks_data:
        lines.append(f"### {item['label']} — {item['status']}")
        lines.append("")
        lines.append("```text")
        lines.append((item["output"] or "(no output)").strip())
        lines.append("```")
        lines.append("")

    lines.append("## Rollback Procedure (Documented, not executed)")
    lines.append("")
    lines.append("1. Identify incident and freeze merges.")
    lines.append(f"2. Checkout rollback target SHA: `{prev}`.")
    lines.append("3. Re-run core checks:")
    lines.append("```bash")
    lines.append("python scripts/check-local-assets.py")
    lines.append("python scripts/check-social-cards.py --strict")
    lines.append("python scripts/check-ai-discoverability.py")
    lines.append("python tests/test-machine-authority.py")
    lines.append("```")
    lines.append("4. Confirm route inventory and CI green before any promotion decision.")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This report does not merge to main.")
    lines.append("- This report does not deploy.")

    output.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return 0 if failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate pre-main release readiness evidence report")
    parser.add_argument(
        "--output",
        default="docs/RELEASE-READINESS-V1.md",
        help="Output markdown file path (relative to repo root)",
    )
    args = parser.parse_args()
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    code = build_report(output)
    print(f"release-readiness: wrote {output.relative_to(ROOT)}")
    if code != 0:
        print("release-readiness: BLOCKED (one or more checks failed)")
    else:
        print("release-readiness: READY_FOR_HUMAN_MAIN_REVIEW")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
