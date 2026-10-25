import importlib.util
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('zone_feed_clock', ROOT / 'scripts/build-feed.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
values = ['2026-10-24T05:30:00+02:00', '2026-10-24T03:30:00Z',
          '2026-10-23T22:30:00-05:00']
target = datetime(2026, 10, 24, 3, 30, tzinfo=timezone.utc)
for iso in values:
    value = mod.iso_to_rfc2822(iso)
    assert value, iso
    assert parsedate_to_datetime(value).astimezone(timezone.utc) == target, (iso, value)
print('RSS offset equivalence: OK')
