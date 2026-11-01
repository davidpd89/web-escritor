"""Price identity, format, currency and expiry; no Amazon calls in CI tests."""
import copy
import io
import sys
import unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reading_amazon_market import select_offers,refresh_offers,CreatorsPrices,money_cents

NOW=datetime(2026,10,21,10,tzinfo=timezone.utc)
BOOK={'id':'lib-1','titulo':'Coraline','autores':['Neil Gaiman'],
      'isbn13':'9788498382372','estado':'publicado','formato_edicion':'tapa-blanda'}


def response():
    return {'searchResult':{'items':[{'asin':'8498382378','itemInfo':{
        'title':{'displayValue':'Coraline (Spanish Edition)'},
        'byLineInfo':{'contributors':[{'name':'Neil Gaiman','role':'Author'}]},
        'externalIds':{'eans':{'displayValues':['9788498382372']}},
        'classifications':{'binding':{'displayValue':'Paperback'}}},
        'offersV2':{'listings':[{'condition':{'value':'New'},
            'availability':{'type':'IN_STOCK'},'price':{'money':{'amount':11.35,'currency':'EUR'},
                'savingBasis':{'money':{'amount':11.95,'currency':'EUR'}}}}]}}]}}


class AmazonPriceTests(unittest.TestCase):
    def test_verified_edition_and_exact_cents(self):
        offers=select_offers(BOOK,response(),'contrato-21',NOW)
        self.assertEqual(len(offers),1)
        self.assertEqual(offers[0]['precio_centimos'],1135)
        self.assertEqual(offers[0]['precio_referencia_centimos'],1195)
        self.assertEqual(offers[0]['formato'],'tapa-blanda')
        self.assertEqual(offers[0]['url'],'https://www.amazon.es/dp/8498382378?tag=contrato-21')
        self.assertEqual(offers[0]['caduca_en'],'2026-10-22T10:00:00Z')

    def test_wrong_isbn_author_title_or_unknown_binding_is_rejected(self):
        for field,value in [('title',{'displayValue':'Otro libro'}),
                            ('byLineInfo',{'contributors':[{'name':'Otra persona','role':'Author'}]}),
                            ('externalIds',{'eans':{'displayValues':['9788425374012']}}),
                            ('classifications',{'binding':{'displayValue':'Unknown'}})]:
            payload=response(); payload['searchResult']['items'][0]['itemInfo'][field]=value
            self.assertEqual(select_offers(BOOK,payload,'contrato-21',NOW),[])

    def test_used_subscription_and_prime_prices_are_not_general_prices(self):
        for update in [{'condition':{'value':'Used'}},{'type':'SUBSCRIBEAND_SAVE'},
                       {'dealDetails':{'accessType':'PRIME_EXCLUSIVE'}},
                       {'availability':{'type':'OUTOFSTOCK'}}]:
            payload=response(); payload['searchResult']['items'][0]['offersV2']['listings'][0].update(update)
            self.assertEqual(select_offers(BOOK,payload,'contrato-21',NOW),[])

    def test_only_eur_and_finite_decimal_amounts(self):
        for amount,currency in [('11,35','EUR'),(True,'EUR'),('nan','EUR'),('1.111','EUR'),(5,'USD'),(0,'EUR')]:
            self.assertIsNone(money_cents({'amount':amount,'currency':currency}))

    def test_edition_specific_known_formats_keep_independent_prices(self):
        book=copy.deepcopy(BOOK)
        book['formatos_compra']=[{'formato':'ebook','url':'https://www.amazon.es/dp/B08CYCPBZN?tag=contrato-21'}]
        payload=response(); item=payload['searchResult']['items'][0]
        item['asin']='B08CYCPBZN'; item['itemInfo']['externalIds']={}
        self.assertEqual(select_offers(book,payload,'contrato-21',NOW)[0]['formato'],'ebook')

    def test_deal_never_outlives_its_actual_end(self):
        payload=response()
        listing=payload['searchResult']['items'][0]['offersV2']['listings'][0]
        listing['dealDetails']={'accessType':'ALL','endTime':'2026-10-21T11:00:00Z'}
        self.assertEqual(select_offers(BOOK,payload,'contrato-21',NOW)[0]['caduca_en'],'2026-10-21T11:00:00Z')
        listing['dealDetails']['endTime']='2026-10-21T09:00:00Z'
        self.assertEqual(select_offers(BOOK,payload,'contrato-21',NOW),[])

    def test_ineligible_account_stops_after_one_call_without_fake_refresh(self):
        calls=[]
        def unavailable(book):
            calls.append(book['id']); raise RuntimeError('pending_amazon_eligibility')
        market={'schema_version':1,'offers':[],'ratings':[]}
        result,stats=refresh_offers({'libros':[BOOK,dict(BOOK,id='lib-2')]},market,unavailable,'contrato-21',NOW)
        self.assertEqual(result,market)
        self.assertEqual(len(calls),1)
        self.assertEqual(stats['status'],'pending_amazon_eligibility')

    def test_real_eligibility_error_is_classified_without_leaking_credentials(self):
        client=CreatorsPrices('private-client','private-secret','contrato-21')
        error=HTTPError('https://api.amazon.co.uk/auth/o2/token',403,'Forbidden',{},
                        io.BytesIO(b'{"message":"Your account does not currently meet the eligibility requirements."}'))
        with patch('reading_amazon_market.urlopen',side_effect=error):
            with self.assertRaisesRegex(RuntimeError,'^pending_amazon_eligibility$'):
                client.post('https://api.amazon.co.uk/auth/o2/token',{})

    def test_amazon_detail_url_is_kept_only_with_our_tag_and_asin(self):
        payload=response(); item=payload['searchResult']['items'][0]
        item['detailPageURL']='https://www.amazon.es/dp/8498382378?tag=contrato-21&linkCode=ogi&th=1&psc=1'
        self.assertEqual(select_offers(BOOK,payload,'contrato-21',NOW)[0]['url'],item['detailPageURL'])
        for other in ['https://www.amazon.es/dp/8498382378?tag=otro-21&linkCode=ogi',
                      'https://www.amazon.es/dp/B000000000?tag=contrato-21',
                      'https://evil.example/dp/8498382378?tag=contrato-21',None]:
            item['detailPageURL']=other
            self.assertEqual(select_offers(BOOK,payload,'contrato-21',NOW)[0]['url'],
                             'https://www.amazon.es/dp/8498382378?tag=contrato-21')

    def test_throttling_waits_and_retries_before_giving_up(self):
        client=CreatorsPrices('id','secret','contrato-21')
        def throttled():
            return HTTPError('https://creatorsapi.amazon/catalog/v1/searchItems',429,'Too Many Requests',{},
                             io.BytesIO(b'{"retryAfterSeconds":3}'))
        ok=io.BytesIO(b'{"searchResult":{"items":[]}}')
        with patch('reading_amazon_market.time.sleep') as sleep,              patch('reading_amazon_market.urlopen',side_effect=[throttled(),throttled(),ok]):
            self.assertEqual(client.post('https://creatorsapi.amazon/catalog/v1/searchItems',{}),{'searchResult':{'items':[]}})
        self.assertIn(3.0,[c.args[0] for c in sleep.call_args_list])
        with patch('reading_amazon_market.time.sleep'),              patch('reading_amazon_market.urlopen',side_effect=[throttled() for _ in range(4)]):
            with self.assertRaisesRegex(RuntimeError,'^Amazon Creators HTTP 429$'):
                client.post('https://creatorsapi.amazon/catalog/v1/searchItems',{})


if __name__=='__main__':
    unittest.main()
