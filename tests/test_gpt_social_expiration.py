"""Test absolute UTC expiry metadata that survives an interrupted updater."""
import importlib.util
from datetime import datetime,timezone,timedelta
from pathlib import Path
import unittest

MODULE=Path(__file__).resolve().parents[1]/'scripts/research/gpt_social_compose.py'
spec=importlib.util.spec_from_file_location('expiry_composer',MODULE)
sc=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)
NOW=datetime(2026,10,22,12,0,tzinfo=timezone.utc)

def bluesky():
    return {"id":"bluesky","followers":9,"source":"bluesky-public-appview","status":"ok","observed_at":"2026-10-22T11:00:00Z"}

def threads():
    return {"id":"threads","followers":0,"source":"metricool-mcp-export","status":"ok","observed_at":"2026-10-21"}

class ExpirationTests(unittest.TestCase):
    def test_bluesky_absolute_deadline(self):
        item=sc.compose([bluesky()],now=NOW)['networks'][0]
        self.assertEqual(item['valid_until'],'2026-10-24T11:00:00Z')

    def test_threads_dayend_deadline_in_madrid(self):
        item=sc.compose([threads()],now=NOW)['networks'][2]
        self.assertEqual(item['valid_until'],'2026-10-23T21:59:59Z')

    def test_earliest_deadline_for_total(self):
        result=sc.compose([bluesky(),threads()],now=NOW)
        self.assertEqual(result['totals']['valid_until'],'2026-10-23T21:59:59Z')
        self.assertEqual(result['totals']['follower_relationships'],9)
        self.assertEqual(result['totals']['coverage'],2)

    def test_expired_count_not_displayable(self):
        sample=bluesky();sample['observed_at']='2026-10-18T11:00:00Z'
        item=sc.compose([sample],now=NOW)['networks'][0]
        self.assertEqual(item['status'],'stale')
        self.assertIsNone(item['followers'])
        self.assertEqual(item['valid_until'],'2026-10-20T11:00:00Z')

    def test_missing_sample_has_no_deadline(self):
        result=sc.compose([],now=NOW)
        self.assertTrue(all(item['valid_until'] is None for item in result['networks']))
        self.assertIsNone(result['totals']['valid_until'])

    def test_zero_count_gets_deadline(self):
        item=sc.compose([threads()],now=NOW)['networks'][2]
        self.assertEqual(item['followers'],0)
        self.assertIsNotNone(item['valid_until'])

    def test_madrid_dst_ends_oct_25(self):
        sample=threads();sample['observed_at']='2026-10-25'
        now=datetime(2026,10,26,12,0,tzinfo=timezone.utc)
        item=sc.compose([sample],now=now)['networks'][2]
        self.assertEqual(item['valid_until'],'2026-10-27T22:59:59Z')

class PublicIntegerSafetyTests(unittest.TestCase):
    def test_reject_count_that_javascript_cannot_represent_exactly(self):
        item=bluesky()
        item['followers']=2**53
        with self.assertRaisesRegex(ValueError, 'nonnegative integer'):
            sc.compose([item],now=NOW)

    def test_reject_combined_total_over_safe_integer_limit(self):
        a=bluesky();a['followers']=2**53-1
        b=threads();b['followers']=1
        with self.assertRaisesRegex(ValueError, 'exact JavaScript integer range'):
            sc.compose([a,b],now=NOW)

if __name__=='__main__':unittest.main()
