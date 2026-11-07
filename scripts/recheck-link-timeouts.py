#!/usr/bin/env python3
"""Recheck Lychee timeouts/transient 5xx/transport errors independently; require actual HTTP 2xx."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'


def timeout_urls(report: str) -> list[str]:
    lines = re.findall(r'^\* \[([^\]]+)\] <([^>]+)>(.*)$', report, re.M)
    # Never hide HTTP errors, unsupported URLs or an unexpected report format.
    retryable = {'TIMEOUT', '500', '502', '503', '504'}
    # Lychee reports transport failures as [ERROR] with no HTTP status. Only
    # these are as transient as a timeout (a refused/reset connection, or the
    # cached copy of an earlier one; lychee's generic "Connection failed" is the
    # connect error unesco.org gave on 2026-11-04 while serving 200 to curl);
    # the recheck still demands a real 2xx, so a host that stays down keeps
    # failing. Other [ERROR]s (DNS, TLS, invalid URL) are not retried.
    transport = re.compile(r'\|\s*(?:Connection (?:refused|reset|closed|failed)\b|Error \(cached\)\s*$)', re.I)
    failures = [(status, url) for status, url, _ in lines]
    if not lines or any(
        not url.startswith(('https://', 'http://'))
        or (status not in retryable and not (status == 'ERROR' and transport.search(detail)))
        for status, url, detail in lines
    ):
        raise ValueError('Only timeout, transient 5xx or transport failures can be rechecked')
    for line in report.splitlines():
        if line.lstrip().startswith('|') and re.search(r'\b(?:Errors|Unknown|Unsupported)\b', line):
            cells = line.split('|')
            if len(cells) < 3 or not cells[2].strip().isdigit():
                raise ValueError('Unknown failure summary format')
            count = int(cells[2])
            expected = sum(status != 'TIMEOUT' for status, _ in failures) if 'Errors' in line else 0
            if count != expected:
                raise ValueError('Report contains failures not covered by the parsed transient URLs')
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


# Quarantine (2026-11-07): an external host that stays unreachable (TCP never
# answers, like uzanzaeditorial.com since 2026-11-07) kept check-links red on
# main and on every PR. Copied from lychee-action's non-blocking report
# pattern, but scoped: only exact hosts listed in .linkcheck-quarantine.json,
# reviewed by PR, for at most MAX_DAYS, and only for an unreachable host or a
# 5xx. Any HTTP 4xx/3xx from the curl recheck stays fatal, and so does every
# DNS/TLS/invalid-URL error (timeout_urls never lets them through). When the
# entry expires the failure is fatal again: fix the data (website_url,
# submission_url...) or renew it explicitly in a PR.
MAX_DAYS = 14


def load_quarantine(path: Path, today: date) -> dict[str, dict]:
    if not path.exists():
        return {}
    entries = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(entries, list):
        raise ValueError('Quarantine must be a JSON list')
    active = {}
    for entry in entries:
        host = entry.get('host') if isinstance(entry, dict) else None
        reason = entry.get('reason') if isinstance(entry, dict) else None
        if not isinstance(host, str) or not re.fullmatch(r'[a-z0-9.-]+\.[a-z]{2,}', host) or not reason:
            raise ValueError(f'Invalid quarantine entry: {entry!r}')
        added, expires = date.fromisoformat(entry['added']), date.fromisoformat(entry['expires'])
        if not 0 <= (expires - added).days <= MAX_DAYS:
            raise ValueError(f'Quarantine for {host} must expire within {MAX_DAYS} days of being added')
        if added <= today <= expires:
            active[host] = entry
    return active


def quarantined(result: dict, active: dict[str, dict]) -> dict | None:
    status = str(result.get('status', ''))
    unreachable = status in ('', '000') or re.fullmatch(r'5\d\d', status)
    return active.get((urlsplit(result['url']).hostname or '').lower()) if unreachable else None


def run(report: Path, output: Path, quarantine: Path | None = None, today: date | None = None) -> int:
    try:
        urls = timeout_urls(report.read_text(encoding='utf-8'))
        active = load_quarantine(quarantine, today or date.today()) if quarantine else {}
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f'FAIL: {error}')
        return 1

    def guarded(url):
        try:
            return check_url(url)
        except (OSError, subprocess.TimeoutExpired) as error:
            return {'url': url, 'ok': False, 'error': str(error)}

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(guarded, urls))
    warnings = []
    for result in results:
        entry = None if result['ok'] else quarantined(result, active)
        if entry:
            result['quarantine'] = entry
            warnings.append(f'- `{result["url"]}` HTTP {result.get("status") or "000"}: '
                            f'{entry["reason"]} (cuarentena hasta {entry["expires"]})')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for result in results:
        label = 'PASS' if result['ok'] else 'WARN quarantined' if 'quarantine' in result else 'FAIL'
        print(f'{label} native recheck: {result["url"]} HTTP {result.get("status", "unavailable")}')
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if warnings and summary:
        with open(summary, 'a', encoding='utf-8') as handle:
            handle.write('## Hosts externos en cuarentena (no bloquean hasta que caduque)\n\n' + '\n'.join(warnings) + '\n')
    for line in warnings:
        print(f'::warning::{line}')
    return 0 if all(result['ok'] or 'quarantine' in result for result in results) else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--quarantine', type=Path)
    args = parser.parse_args()
    raise SystemExit(run(args.report, args.output, args.quarantine))
