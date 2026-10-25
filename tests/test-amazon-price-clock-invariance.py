import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_amazon_market import select_offers

BOOK = {'id':'test','titulo':'Coraline','autores':['Neil Gaiman'],
        'isbn13':'9788498382372','estado':'publicado'}
PAYLOAD = {'searchResult':{'items':[{
    'asin':'8498382378',
    'itemInfo':{'title':{'displayValue':'Coraline'},
        'byLineInfo':{'contributors':[{'name':'Neil Gaiman','role':'Author'}]},
        'externalIds':{'eans':{'displayValues':['9788498382372']}},
        'classifications':{'binding':{'displayValue':'Paperback'}}},
    'offersV2':{'listings':[{'condition':{'value':'New'},
        'availability':{'type':'IN_STOCK'},
        'price':{'money':{'amount':11.35,'currency':'EUR'}}}]}
}]}}

class AmazonClockTests(unittest.TestCase):
    def test_identical_instants_generate_identical_offers(self):
        utc = datetime(2026,10,21,10,tzinfo=timezone.utc)
        zones = [timezone.utc, timezone(timedelta(hours=2)),
                 timezone(timedelta(hours=-4)), timezone(timedelta(hours=9))]
        baseline = select_offers(BOOK,PAYLOAD,'contrato-21',utc)
        self.assertEqual(len(baseline),1)
        for zone in zones:
            with self.subTest(zone=str(zone)):
                result = select_offers(BOOK,PAYLOAD,'contrato-21',utc.astimezone(zone))
                self.assertEqual(result,baseline)
                self.assertTrue(result[0]['actualizado_en'].endswith('Z'))
                self.assertTrue(result[0]['caduca_en'].endswith('Z'))

if __name__ == '__main__':
    unittest.main()
