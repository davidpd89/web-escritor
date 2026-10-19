#!/usr/bin/env python3
"""Independently recheck only Lychee TIMEOUT results; require actual HTTP 2xx."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import subprocess

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'


def timeout_urls(report: str) -> list[str]:
    failures = re.findall(r'^\* \[([^\]]+)\] <(https?://[^>]+)>', report, re.M)
    # Never hide HTTP errors, unsupported URLs or an unexpected report format.
    if not failures or any(status != 'TIMEOUT' for status, _ in failures):
        raise ValueError('Only reports containing exclusively TIMEOUT failures can be rechecked')
    for line in report.splitlines():
        if re.search(r'\b(?:Errors|Unknown|Unsupported)\b', line):
            cells = line.split('|')
            if len(cells) >= 3 and cells[2].strip().isdigit() and int(cells[2]) != 0:
                raise ValueError('Report also contains non-timeout failures')
    return sorted({url for _, url in failures})


def check_url(url: str) -> dict:
    # A second network stack and IPv4 route, not another scan of 1,495 URLs.
    # Keep HTTP failures/redirect loops fatal; no accepted status expansion.
    result = subprocess.run([
        'curl', '--ipv4', '--location', '--max-redirs', '10', '--fail',
        '--silent', '--show-error', '--connect-timeout', '10', '--max-time', '45',
        '--retry', '1', '--retry-delay', '2', '--user-agent', UA,
        '--output', os.devnull, '--write-out', '%{http_code}', '--url', url,
    ], capture_output=True, text=True, timeout=110)
    status = result.stdout.strip()
    ok = result.returncode == 0 and bool(re.fullmatch(r'2\d\d', status))
    return {'url': url, 'ok': ok, 'status': status, 'exit': result.returncode,
            'error': result.stderr.strip()[:300] if not ok else ''}


def run(report: Path, output: Path) -> int:
    try:
        urls = timeout_urls(report.read_text(encoding='utf-8'))
    except (ValueError, OSError) as error:
        print(f'FAIL: {error}')
        return 1

    def guarded(url):
        try:
            return check_url(url)
        except (OSError, subprocess.TimeoutExpired) as error:
            return {'url': url, 'ok': False, 'error': str(error)}

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(guarded, urls))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for result in results:
        print(f'{"PASS" if result["ok"] else "FAIL"} native recheck: {result["url"]} HTTP {result.get("status", "unavailable")}')
    return 0 if all(result['ok'] for result in results) else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.report, args.output))
