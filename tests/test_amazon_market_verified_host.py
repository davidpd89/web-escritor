import sys
import unittest
from datetime import datetime,timezone
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reading_amazon_market import asin_from_url,select_offers,verified_formats

NOW=datetime(2026,10,21,tzinfo=timezone.utc)
ASIN='B08CYCPBZN'
BASE={'id':'lib-test','titulo':'Coraline','autores':['Neil Gaiman'],'isbn13':'9788498382372','estado':'publicado'}
ITEM={'asin':ASIN,'itemInfo':{'title':{'displayValue':'Coraline'},'byLineInfo':{'contributors':[{'name':'Neil Gaiman','role':'Author'}]},'externalIds':{},'classifications':{'binding':{'displayValue':'Kindle'}}},'offersV2':{'listings':[{'condition':{'value':'New'},'availability':{'type':'IN_STOCK'},'price':{'money':{'amount':5.99,'currency':'EUR'}}}]}}

class HostValidation(unittest.TestCase):
    def test_untrusted_hosts_never_supply_verified_asins(self):
        for url in [
            'https://evil.example/dp/'+ASIN,
            'https://www.amazon.es.evil.example/dp/'+ASIN,
            'http://www.amazon.es/dp/'+ASIN,
            'https://usuario@www.amazon.es/dp/'+ASIN
        ]:
            with self.subTest(url=url):
                self.assertIsNone(asin_from_url(url))
                book={**BASE,'formatos_compra':[{'url':url,'formato':'ebook'}]}
                self.assertEqual(verified_formats(book),{})
                self.assertEqual(select_offers(book,{'searchResult':{'items':[ITEM]}},'davidporto-21',NOW),[])
    def test_real_amazon_format_stays_recognised(self):
        url='https://www.amazon.es/dp/'+ASIN+'?tag=davidporto-21'
        self.assertEqual(asin_from_url(url),ASIN)

if __name__=='__main__': unittest.main()
