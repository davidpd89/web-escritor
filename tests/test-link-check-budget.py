#!/usr/bin/env python3
"""The full link scan must fit its job limit: bound lychee's per-URL retry cost.

Each unreachable URL costs --timeout x (1 + --max-retries) seconds of a worker.
With 5 retries the weekly scan's ~32 timeouts alone took ~18 min of the
8 workers and full scans hit the 40 min limit. Transient failures are
rechecked by scripts/recheck-link-timeouts.py, so lychee need not retry much.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
wf = (ROOT / '.github/workflows/broken-links.yml').read_text(encoding='utf-8')


def flag(name):
    m = re.search(rf'--{name}\s+(\d+)', wf)
    assert m, f'--{name} missing from broken-links.yml'
    return int(m.group(1))


timeout, retries, workers = flag('timeout'), flag('max-retries'), flag('max-concurrency')
job_limit = int(re.search(r'timeout-minutes:\s*(\d+)', wf).group(1))
per_url = timeout * (1 + retries)
assert per_url <= 150, f'one dead URL costs {per_url}s (timeout {timeout} x {1 + retries} attempts)'
# 32 timeouts in the 2026-11-02 weekly scan; leave most of the job for real checks.
assert 32 * per_url / workers <= job_limit * 60 / 3, 'timeout retries alone would use over a third of the job'
assert 'recheck-link-timeouts.py' in wf and "steps.lychee.outcome == 'failure'" in wf, \
    'fewer lychee retries rely on the independent curl recheck step'
print(f'PASS link check budget: {per_url}s per dead URL, recheck step present, job limit {job_limit} min')
