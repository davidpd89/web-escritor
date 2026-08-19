#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from datetime import datetime

def to_ics(dt_str):
    # expect YYYY-MM-DDTHH:MM
    dt = datetime.fromisoformat(dt_str)
    return dt.strftime('%Y%m%dT%H%M00')

def main():
    p=argparse.ArgumentParser(); p.add_argument('json'); p.add_argument('--output', required=True); p.add_argument('--uid', default='event-1'); args=p.parse_args()
    data=json.loads(Path(args.json).read_text(encoding='utf-8'))
    uid=args.uid
    dtstart=to_ics(data['dtstart'])
    dtend=to_ics(data.get('dtend') or data['dtstart'])
    lines=[
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//davidportodiaz//EN',
        'BEGIN:VEVENT',
        f'UID:{uid}',
        f'DTSTAMP:{datetime.utcnow().strftime("%Y%m%dT%H%M00Z")}',
        f'DTSTART:{dtstart}',
        f'DTEND:{dtend}',
        f'SUMMARY:{data.get("title","Evento")}',
        f'DESCRIPTION:{data.get("description","")}',
        f'LOCATION:{data.get("location","")}',
        'END:VEVENT',
        'END:VCALENDAR'
    ]
    Path(args.output).write_text('\n'.join(lines), encoding='utf-8')
    print('ICS GENERATED', args.output)

if __name__=='__main__':
    main()
