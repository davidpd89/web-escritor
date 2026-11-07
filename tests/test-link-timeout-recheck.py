#!/usr/bin/env python3
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('recheck', ROOT/'scripts/recheck-link-timeouts.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
url = 'https://example.org/bases.pdf'
report = f'| Errors | 0 |\n| Unknown | 0 |\n| Unsupported | 0 |\n* [TIMEOUT] <{url}>\n* [TIMEOUT] <{url}>\n'
assert module.timeout_urls(report) == [url]
assert module.timeout_urls('| Errors | 1 |\n## Errors per input\n### Errors in page.html\n* [503] <https://example.org/busy>') == ['https://example.org/busy']
for invalid in ['', '* [404] <https://example.org/missing>', '* [301] <https://example.org/loop>', '* [500] <file:///private>', report+'* [403] <https://example.org/blocked>', report.replace('Errors | 0','Errors | 1')]:
    try:
        module.timeout_urls(invalid)
        raise AssertionError('must not accept non-timeout failures or unknown output')
    except ValueError:
        pass
# Transport [ERROR]s from the 2026-11-02 weekly scan: retried, still need 2xx.
refused = ('| Errors | 2 |\n'
           '* [ERROR] <https://example.org/bases/> (at 924:88) | Connection refused - server may be down or port blocked\n'
           '* [ERROR] <https://example.org/originales/> (at 200:100) | Error (cached)\n')
assert module.timeout_urls(refused) == ['https://example.org/bases/', 'https://example.org/originales/']
assert module.timeout_urls(refused.replace('\n', '\r\n')) == ['https://example.org/bases/', 'https://example.org/originales/']
# lychee's generic connect error (unesco.org, 2026-11-04 full scan).
failed = '| Errors | 1 |\n* [ERROR] <https://www.unesco.org/en/creative-cities> (at 132:3253) | Connection failed. Check network connectivity and firewall settings\n'
assert module.timeout_urls(failed) == ['https://www.unesco.org/en/creative-cities']
for invalid in ['| Errors | 1 |\n* [ERROR] <https://example.org/x> | Failed to resolve DNS name',
                '| Errors | 1 |\n* [ERROR] <https://example.org/x> | TLS handshake failed',
                '| Errors | 1 |\n* [ERROR] <https://example.org/x> | Connection refusedness',
                '| Errors | 1 |\n* [ERROR] <https://example.org/x> | Connection failedover',
                '| Errors | 1 |\n* [ERROR] <https://example.org/x>',
                '| Errors | 1 |\n* [ERROR] <file:///x> | Connection refused',
                refused.replace('Errors | 2', 'Errors | 3')]:
    try:
        module.timeout_urls(invalid)
        raise AssertionError('only transport [ERROR]s may be rechecked')
    except ValueError:
        pass
for code, status, expected in [(0,'200',True),(0,'204',True),(22,'404',False),(0,'301',False),(28,'000',False),(1,'200',False)]:
    with patch.object(module.subprocess, 'run', return_value=SimpleNamespace(returncode=code,stdout=status,stderr='')) as execute:
        assert module.check_url(url)['ok'] is expected
        args = execute.call_args.args[0]
        assert '--fail' in args and '--location' in args and '--ipv4' in args
        assert args[-2:] == ['--url',url]
# Quarantine (2026-11-07): exact host, <=14 days, only unreachable/5xx.
import io, json, os, tempfile
from contextlib import redirect_stdout
from datetime import date
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    def run_with(entries, results, today=date(2026, 11, 10)):
        (tmp/'q.json').write_text(json.dumps(entries), encoding='utf-8')
        report = '| Errors | 0 |\n' + ''.join(f'* [TIMEOUT] <{r["url"]}>\n' for r in results)
        (tmp/'out.md').write_text(report, encoding='utf-8')
        by_url = {r['url']: r for r in results}
        with patch.object(module, 'check_url', side_effect=lambda u: dict(by_url[u])), patch.dict(os.environ, {'GITHUB_STEP_SUMMARY': str(tmp/'summary.md')}), redirect_stdout(io.StringIO()):
            return module.run(tmp/'out.md', tmp/'res.json', tmp/'q.json', today)
    entry = {'host': 'down.example.org', 'reason': 'TCP sin respuesta', 'added': '2026-11-07', 'expires': '2026-11-21'}
    down = {'url': 'https://down.example.org/manuscritos/', 'ok': False, 'status': '000', 'exit': 28}
    assert run_with([entry], [down]) == 0
    saved = json.loads((tmp/'res.json').read_text(encoding='utf-8'))
    assert saved[0]['quarantine']['host'] == 'down.example.org'
    assert 'down.example.org/manuscritos/' in (tmp/'summary.md').read_text(encoding='utf-8')
    assert run_with([entry], [dict(down, status='503', exit=22)]) == 0
    assert run_with([], [down]) == 1, 'without quarantine an unreachable host fails'
    assert run_with([entry], [down], today=date(2026, 11, 22)) == 1, 'expired quarantine fails again'
    assert run_with([entry], [dict(down, status='404', exit=22)]) == 1, 'a 4xx is never quarantined'
    assert run_with([entry], [dict(down, status='301', exit=47)]) == 1, 'redirect loops are never quarantined'
    assert run_with([entry], [dict(down, url='https://sub.down.example.org/x')]) == 1, 'host must match exactly'
    assert run_with([entry], [dict(down, url='https://down.example.org.evil.test/x')]) == 1
    other = {'url': 'https://other.example.org/', 'ok': False, 'status': '000', 'exit': 28}
    assert run_with([entry], [down, other]) == 1, 'quarantine never covers other hosts'
    for bad in [dict(entry, expires='2026-11-22'), dict(entry, expires='2026-11-06'), dict(entry, host='*.example.org'),
                dict(entry, host='https://down.example.org'), dict(entry, reason=''), dict(entry, added=20261107),
                {k: v for k, v in entry.items() if k != 'expires'}, 'down.example.org']:
        assert run_with([bad], [down]) == 1, f'invalid quarantine must fail: {bad!r}'
    (tmp/'q.json').write_text('{not json', encoding='utf-8')
    with redirect_stdout(io.StringIO()):
        assert module.run(tmp/'out.md', tmp/'res.json', tmp/'q.json') == 1
# The committed quarantine itself must be valid.
module.load_quarantine(ROOT/'.linkcheck-quarantine.json', date.today())
print('PASS link timeout recheck: only actual 2xx clears timeout/transport errors; HTTP errors, loops and unknown reports stay fatal; quarantine only excuses listed unreachable hosts until it expires')
