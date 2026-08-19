#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def run_validate(file):
    p = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'validate_jsonld.py'), str(file)], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr

def main():
    report_lines = []
    sitemap = ROOT / 'sitemap.xml'
    report_lines.append('Sitemap: ' + ('FOUND' if sitemap.exists() else 'MISSING'))
    html_files = list(ROOT.rglob('*.html'))
    report_lines.append(f'HTML files scanned: {len(html_files)}')
    for f in sorted(html_files):
        code, out = run_validate(f)
        status = 'OK' if code==0 else 'ERROR'
        report_lines.append(f'[{status}] {f}')
        if out.strip():
            report_lines.append(out.strip())
    outdir = ROOT / 'herramientas' / 'auditor-web'
    outdir.mkdir(parents=True, exist_ok=True)
    report_path = outdir / 'report.txt'
    report_path.write_text('\n'.join(report_lines), encoding='utf-8')
    print('REPORT GENERATED', report_path)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
