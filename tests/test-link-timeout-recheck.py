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
for invalid in ['| Errors | 1 |\n* [ERROR] <https://example.org/x> | Failed to resolve DNS name',
                '| Errors | 1 |\n* [ERROR] <https://example.org/x> | TLS handshake failed',
                '| Errors | 1 |\n* [ERROR] <https://example.org/x> | Connection refusedness',
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
print('PASS link timeout recheck: only actual 2xx clears timeout/transport errors; HTTP errors, loops and unknown reports stay fatal')
