import json
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'assets/reading-market.json'

def parse_utc(raw):
    value = datetime.fromisoformat(raw.replace('Z','+00:00'))
    if value.tzinfo is None:
        raise ValueError('timestamp sin timezone')
    if value.utcoffset() != timedelta(0):
        raise ValueError('timestamp de mercado no normalizado a UTC')
    return value.astimezone(timezone.utc)

class MarketExpirationCorpus(unittest.TestCase):
    def test_every_record_has_bounded_valid_lifecycle(self):
        payload = json.loads(DATA.read_text(encoding='utf-8'))
        checked = 0
        for section,ttl,key_fields in [
            ('offers',timedelta(hours=24),('libro_id','formato','tipo')),
            ('ratings',timedelta(days=7),('libro_id','fuente'))]:
            seen = set()
            for record in payload.get(section,[]):
                identity = tuple(record.get(k) for k in key_fields)
                with self.subTest(section=section,identity=identity):
                    self.assertTrue(all(identity))
                    self.assertNotIn(identity,seen)
                    seen.add(identity)
                    start = parse_utc(record['actualizado_en'])
                    end = parse_utc(record['caduca_en'])
                    self.assertLess(start,end)
                    self.assertLessEqual(end-start,ttl)
                    checked += 1
        self.assertGreater(checked,0)

if __name__ == '__main__':
    unittest.main()
