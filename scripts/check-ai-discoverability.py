#!/usr/bin/env python3
"""Static preflight for AI/search discoverability on davidportodiaz.com.

This deliberately does NOT impersonate verified AI crawlers against production:
CDNs such as Cloudflare may validate bot identity by IP/signature, so a synthetic
User-Agent from CI would create false positives/negatives. The script checks the
published policy and indexability of key local pages. Edge access is verified in
Cloudflare AI Crawl Control with real crawler traffic.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.robotparser
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

CANONICAL_ORIGIN = "https://davidportodiaz.com"
REQUIRED_SITEMAP = f"{CANONICAL_ORIGIN}/sitemap.xml"

SEARCH_AGENTS = {
    "OAI-SearchBot": "ChatGPT Search indexing/search visibility",
    "ChatGPT-User": "ChatGPT user-directed fetches",
    "Claude-SearchBot": "Claude search visibility",
    "Claude-User": "Claude user-directed fetches",
    "PerplexityBot": "Perplexity search visibility",
    "Googlebot": "Google Search / AI features use Google Search index",
    "bingbot": "Bing/Copilot search index",
}

TRAINING_AGENTS = {
    "GPTBot": "OpenAI model-development crawling",
    "ClaudeBot": "Anthropic model-development crawling",
    "Google-Extended": "Google generative-AI training/grounding control, separate from Googlebot",
}

DEFAULT_PATHS = [
    "/",
    "/las-manecillas-del-recuerdo/",
    "/cuaderno/",
    "/autor.html",
    "/prensa.html",
]

@dataclass
class Finding:
    level: str
    message: str


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--robots", default="robots.txt", help="Path to robots.txt")
    p.add_argument("--site-root", help="Static site root; enables key-page checks")
    p.add_argument("--path", action="append", dest="paths", help="Public path to test; repeatable")
    p.add_argument("--strict-pages", action="store_true", help="Fail if a requested local page is missing")
    return p.parse_args()


def public_to_file(root: Path, public_path: str) -> Path:
    clean = public_path.split("?", 1)[0].split("#", 1)[0]
    if clean == "/":
        return root / "index.html"
    rel = clean.lstrip("/")
    if rel.endswith("/"):
        return root / rel / "index.html"
    return root / rel


def meta_robots_content(html: str) -> str:
    # Attribute order can vary; inspect all meta tags instead of one brittle regex.
    for tag in re.findall(r"<meta\b[^>]*>", html, flags=re.I):
        if re.search(r"\bname\s*=\s*([\"'])robots\1", tag, flags=re.I):
            m = re.search(r"\bcontent\s*=\s*([\"'])(.*?)\1", tag, flags=re.I | re.S)
            return (m.group(2) if m else "").strip().lower()
    return ""


def canonical_href(html: str) -> str | None:
    for tag in re.findall(r"<link\b[^>]*>", html, flags=re.I):
        if re.search(r"\brel\s*=\s*([\"'])canonical\1", tag, flags=re.I):
            m = re.search(r"\bhref\s*=\s*([\"'])(.*?)\1", tag, flags=re.I | re.S)
            return (m.group(2).strip() if m else None)
    return None


def check_robots(path: Path, public_paths: Iterable[str]) -> list[Finding]:
    findings: list[Finding] = []
    if not path.exists():
        return [Finding("FAIL", f"Missing robots.txt: {path}")]

    text = path.read_text(encoding="utf-8")
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(text.splitlines())

    sitemaps = re.findall(r"(?im)^\s*Sitemap\s*:\s*(\S+)\s*$", text)
    if REQUIRED_SITEMAP not in sitemaps:
        findings.append(Finding("FAIL", f"Canonical sitemap missing: {REQUIRED_SITEMAP}"))
    else:
        findings.append(Finding("OK", f"Canonical sitemap declared: {REQUIRED_SITEMAP}"))

    for agent, purpose in SEARCH_AGENTS.items():
        blocked = [p for p in public_paths if not rp.can_fetch(agent, p)]
        if blocked:
            findings.append(Finding("FAIL", f"{agent} blocked on {', '.join(blocked)} — {purpose}"))
        else:
            findings.append(Finding("OK", f"{agent} can crawl all key paths — {purpose}"))

    # Training access is a policy choice, not a search-ranking gate.
    for agent, purpose in TRAINING_AGENTS.items():
        status = "allowed" if rp.can_fetch(agent, "/") else "blocked"
        findings.append(Finding("INFO", f"Training-policy bot {agent}: {status} — {purpose}"))

    # Explain stale aliases without failing: current official Anthropic docs list
    # ClaudeBot, Claude-SearchBot and Claude-User.
    for alias in ("Claude-Web", "anthropic-ai"):
        if re.search(rf"(?im)^\s*User-agent\s*:\s*{re.escape(alias)}\s*$", text):
            findings.append(Finding("INFO", f"Legacy/non-current Anthropic alias still present: {alias}; harmless, not used as a readiness gate"))

    return findings


def check_pages(root: Path, public_paths: Iterable[str], strict: bool) -> list[Finding]:
    findings: list[Finding] = []
    for public_path in public_paths:
        f = public_to_file(root, public_path)
        if not f.exists():
            level = "FAIL" if strict else "WARN"
            findings.append(Finding(level, f"Local page missing for {public_path}: {f}"))
            continue
        html = f.read_text(encoding="utf-8", errors="replace")
        robots = meta_robots_content(html)
        if "noindex" in {x.strip() for x in robots.split(",")} or "noindex" in robots.split():
            findings.append(Finding("FAIL", f"{public_path} is noindex"))
        else:
            findings.append(Finding("OK", f"{public_path} is not marked noindex"))

        canonical = canonical_href(html)
        expected = CANONICAL_ORIGIN + public_path
        if canonical is None:
            findings.append(Finding("WARN", f"{public_path} has no canonical link"))
        elif canonical.rstrip("/") != expected.rstrip("/"):
            findings.append(Finding("FAIL", f"{public_path} canonical mismatch: {canonical} != {expected}"))
        else:
            findings.append(Finding("OK", f"{public_path} canonical is self-referential"))

        if not re.search(r"<h1\b[^>]*>.*?</h1>", html, flags=re.I | re.S):
            findings.append(Finding("WARN", f"{public_path} has no detectable H1"))

    return findings


def main() -> int:
    args = parse_args()
    paths = args.paths or DEFAULT_PATHS
    findings = check_robots(Path(args.robots), paths)
    if args.site_root:
        findings.extend(check_pages(Path(args.site_root), paths, args.strict_pages))

    for f in findings:
        print(f"[{f.level}] {f.message}")

    failures = [f for f in findings if f.level == "FAIL"]
    print(f"\nAI discoverability preflight: {'FAIL' if failures else 'PASS'} ({len(failures)} failure(s))")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
