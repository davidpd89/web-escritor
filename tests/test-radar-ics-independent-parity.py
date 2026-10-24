import json
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'convocatorias-escritores'

def read_events(raw):
    logical = raw.replace('\r\n ', '').replace('\n ', '')
    events = []
    current = None
    for line in logical.replace('\r\n','\n').split('\n'):
        if line == 'BEGIN:VEVENT':
            current = {}
        elif line == 'END:VEVENT':
            if current is not None:
                events.append(current)
            current = None
        elif current is not None and ':' in line:
            key, value = line.split(':', 1)
            current[key] = value
    return events

class IndependentRadarCalendar(unittest.TestCase):
    def test_public_json_and_ics_agree(self):
        data = json.loads((BASE / 'opportunities.json').read_text(encoding='utf-8'))
        ics = (BASE / 'deadlines.ics').read_text(encoding='utf-8')
        self.assertIn('BEGIN:VCALENDAR', ics)
        events = read_events(ics)
        expected = {item['id']: item for item in data['items']}
        self.assertEqual(len(events), len(expected))
        actual_ids = set()
        for event in events:
            uid = event['UID']
            self.assertTrue(uid.endswith('@davidportodiaz.com'))
            identifier = uid.removesuffix('@davidportodiaz.com')
            self.assertNotIn(identifier, actual_ids)
            actual_ids.add(identifier)
            self.assertIn(identifier, expected)
            item = expected[identifier]
            day = date.fromisoformat(item['deadline'])
            verified = date.fromisoformat(item['verified_at'])
            self.assertEqual(event['DTSTART;VALUE=DATE'], day.strftime('%Y%m%d'))
            self.assertEqual(event['DTEND;VALUE=DATE'],
                             (day+timedelta(days=1)).strftime('%Y%m%d'))
            self.assertEqual(event['DTSTAMP'],verified.strftime('%Y%m%d')+'T000000Z')
        self.assertEqual(actual_ids, set(expected))

if __name__ == '__main__':
    unittest.main()
