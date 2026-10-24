import importlib.util
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('feed_timezone_qa',ROOT/'scripts/build-feed.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
cases=[
    '2026-10-23T13:30:00+02:00',
    '2026-10-23T06:30:00-05:00',
    '2026-10-23T11:30:00Z',
    '2026-10-23T11:30:00+00:00',
    '2026-10-23',
]
for source in cases:
    result=mod.iso_to_rfc2822(source)
    assert result is not None, source
    parsed=parsedate_to_datetime(result)
    assert parsed.tzinfo is not None
    expected=datetime.fromisoformat(source.replace('Z','+00:00'))
    if expected.tzinfo is None:
        expected=expected.replace(tzinfo=timezone.utc)
    assert parsed.astimezone(timezone.utc)==expected.astimezone(timezone.utc),(source,result,expected)
assert mod.iso_to_rfc2822('fecha-invalida') is None
print('OK: pubDate conserva los instantes de origen')
