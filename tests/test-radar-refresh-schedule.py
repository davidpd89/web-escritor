#!/usr/bin/env python3
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=(ROOT/'.github/workflows/radar-clock-refresh.yml').read_text(encoding='utf-8')
SITE=ZoneInfo('Europe/Madrid')

crons=[]
for minute,hour in re.findall(r"cron:\s*['\"](\d{1,2})\s+(\d{1,2})\s+\*\s+\*\s+\*['\"]",WORKFLOW):
    crons.append((int(hour),int(minute)))
assert crons, 'radar refresh workflow has no daily cron schedules'

def scheduled_near(midnight_local: datetime) -> bool:
    start=midnight_local.astimezone(timezone.utc)
    end=(midnight_local+timedelta(minutes=30)).astimezone(timezone.utc)
    day=start.date()-timedelta(days=1)
    while day<=end.date()+timedelta(days=1):
        for hour,minute in crons:
            candidate=datetime(day.year,day.month,day.day,hour,minute,tzinfo=timezone.utc)
            if start<=candidate<=end:
                return True
        day+=timedelta(days=1)
    return False

for local_date in [(2026,1,15),(2026,7,15),(2026,3,29),(2026,10,25)]:
    midnight=datetime(*local_date,0,0,tzinfo=SITE)
    assert scheduled_near(midnight), f'no radar refresh within 30 min after Madrid midnight: {midnight.isoformat()}'

assert "from site_clock import site_today" in WORKFLOW, 'workflow must reuse canonical site_clock instead of duplicating timezone logic'
assert "paths:\n      - '.github/workflows/radar-clock-refresh.yml'" in WORKFLOW, 'workflow change must self-trigger one immediate refresh on main'
print(f'PASS radar refresh schedule: {len(crons)} UTC crons cover Madrid midnight in CET/CEST within 30 minutes')
