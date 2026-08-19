#!/usr/bin/env python3
"""Generate herramientas/auditor-web/report.txt: a JSON-LD validity sweep
of every real, published HTML page.

Paths in the report are repo-relative (not absolute) so the published
artifact never leaks the local filesystem layout of whoever regenerated it.
Planning/draft folders are excluded so the report only ever describes the
live site.

Usage:
    python scripts/audit-author-web.py
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_PARTS = {
    ".git", ".github", "node_modules", "tests", "vendor",
    "WEB DAVID PORTO nuevas ideas", "archive", ".codex_work",
}


def run_validate(file):
    p = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'validate_jsonld.py'), str(file)], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def public_html_files():
    for f in ROOT.rglob('*.html'):
        rel = f.relative_to(ROOT)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        yield f


def main():
    report_lines = []
    sitemap = ROOT / 'sitemap.xml'
    report_lines.append('Sitemap: ' + ('FOUND' if sitemap.exists() else 'MISSING'))
    html_files = sorted(public_html_files())
    report_lines.append(f'HTML files scanned: {len(html_files)}')
    for f in html_files:
        rel = f.relative_to(ROOT).as_posix()
        code, out = run_validate(f)
        status = 'OK' if code == 0 else 'ERROR'
        report_lines.append(f'[{status}] {rel}')
        if out.strip():
            # Normalize any absolute paths the sub-tool prints back to relative.
            cleaned = out.strip().replace(str(ROOT) + '\\', '').replace(str(ROOT) + '/', '')
            report_lines.append(cleaned)
    outdir = ROOT / 'herramientas' / 'auditor-web'
    outdir.mkdir(parents=True, exist_ok=True)
    report_path = outdir / 'report.txt'
    report_path.write_text('\n'.join(report_lines) + '\n', encoding='utf-8')
    print('REPORT GENERATED', report_path.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
