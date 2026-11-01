"""Price identity, format, currency and expiry; no Amazon calls in CI tests."""
import copy
import io
import sys
import unittest
from datetime import datetime,timedelta,timezone
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
        with patch('reading_amazon_market.time.sleep') as sleep,\
             patch('reading_amazon_market.urlopen',side_effect=[throttled(),throttled(),ok]):
            self.assertEqual(client.post('https://creatorsapi.amazon/catalog/v1/searchItems',{}),{'searchResult':{'items':[]}})
        self.assertIn(3.0,[c.args[0] for c in sleep.call_args_list])
        with patch('reading_amazon_market.time.sleep'),\
             patch('reading_amazon_market.urlopen',side_effect=[throttled() for _ in range(4)]):
            with self.assertRaisesRegex(RuntimeError,'^Amazon Creators HTTP 429$'):
                client.post('https://creatorsapi.amazon/catalog/v1/searchItems',{})


def kindle(title='Coraline',language='Español',asin='B08CYCPBZN',amount=6.64):
    payload=response(); item=payload['searchResult']['items'][0]
    item.update(asin=asin)
    item['itemInfo'].update(title={'displayValue':title},externalIds={},
                            classifications={'binding':{'displayValue':'Versión Kindle'}},
                            contentInfo={'languages':{'displayValues':[{'displayValue':language,'type':'Publicado'}]}})
    item['offersV2']['listings'][0]['price']={'money':{'amount':amount,'currency':'EUR'}}
    return payload


class AmazonFormatDiscoveryTests(unittest.TestCase):
    def test_spanish_kindle_without_isbn_is_accepted_by_exact_title(self):
        offers=select_offers(BOOK,kindle('Coraline (Edición ilustrada)'),'contrato-21',NOW)
        self.assertEqual([(o['formato'],o['precio_centimos']) for o in offers],[('ebook',664)])

    def test_other_language_or_longer_title_is_not_our_edition(self):
        self.assertEqual(select_offers(BOOK,kindle(language='Inglés'),'contrato-21',NOW),[])
        self.assertEqual(select_offers(BOOK,kindle('Coraline y la otra madre'),'contrato-21',NOW),[])
        payload=kindle(); payload['searchResult']['items'][0]['itemInfo']['classifications']['binding']['displayValue']='Tapa blanda'
        self.assertEqual(select_offers(BOOK,payload,'contrato-21',NOW),[],'una edición impresa exige ISBN')

    def test_prices_are_stored_per_format_and_kept_until_a_new_one_arrives(self):
        class Provider:
            def __init__(self): self.discovered=0
            def __call__(self,book): return response()
            def discover(self,book):
                self.discovered+=1
                return kindle()
        book=dict(BOOK,formatos_compra=[])
        catalogue={'libros':[book]}
        provider=Provider()
        market,stats=refresh_offers(catalogue,{'offers':[]},provider,'contrato-21',NOW)
        self.assertEqual(market,{'offers':[]},'los precios viven en el catálogo, no en market')
        self.assertEqual([(o['formato'],o['precio_centimos'],o['url']) for o in book['formatos_compra']],
                         [('tapa-blanda',1135,'https://www.amazon.es/dp/8498382378?tag=contrato-21'),
                          ('ebook',664,'https://www.amazon.es/dp/B08CYCPBZN?tag=contrato-21')])
        self.assertEqual((stats['requests'],stats['formats_added'],book['precios_amazon_revision']),(2,2,'2026-10-21'))
        # Weeks later Amazon returns nothing: the published prices stay.
        refresh_offers(catalogue,market,lambda b:{'searchResult':{'items':[]}},'contrato-21',NOW+timedelta(days=30))
        self.assertEqual([o['precio_centimos'] for o in book['formatos_compra']],[1135,664])
        # A new price replaces the old one; the verified edition is not swapped for another ASIN.
        refresh_offers(catalogue,market,lambda b:kindle(amount=5.99),'contrato-21',NOW+timedelta(days=31))
        self.assertEqual(book['formatos_compra'][1]['precio_centimos'],599)
        refresh_offers(catalogue,market,lambda b:kindle(asin='B000000000',amount=1.99),'contrato-21',NOW+timedelta(days=32))
        self.assertEqual(book['formatos_compra'][1]['precio_centimos'],599)

    def test_nightly_sweep_covers_the_catalogue_oldest_first(self):
        many={'libros':[dict(BOOK,id=f'lib-{i}',formatos_compra=[]) for i in range(70)]}
        _,stats=refresh_offers(many,{'offers':[]},lambda b:response(),'contrato-21',NOW)
        self.assertEqual(stats['updated'],70,'los libros sin precio entran todos la primera noche')
        seen=[]
        for night in range(1,8):
            _,stats=refresh_offers(many,{'offers':[]},lambda b:(seen.append(b['id']) or response()),
                                   'contrato-21',NOW+timedelta(days=night))
            self.assertEqual(stats['attempted'],10,'70 libros en un barrido de 7 noches: 10 por noche')
        self.assertEqual(sorted(seen),sorted(b['id'] for b in many['libros']),'cada libro una vez por barrido')
        _,stats=refresh_offers(many,{'offers':[]},lambda b:response(),'contrato-21',NOW,budget=3)
        self.assertEqual(stats['requests'],3,'nunca por encima del límite de Amazon')

    def test_known_asins_are_priced_ten_per_request_and_formats_searched_once(self):
        class Provider:
            def __init__(self): self.calls=[]
            def __call__(self,book): self.calls.append('isbn'); return response()
            def discover(self,book): self.calls.append('discover'); return {'searchResult':{'items':[]}}
            def items(self,asins):
                self.calls.append(len(asins))
                payload=response(); item=payload['searchResult']['items'][0]
                return {'itemsResult':{'items':[dict(item,asin=a) for a in asins]}}
        books=[dict(BOOK,id=f'lib-{i}',isbn13='9788498382372',formatos_compra=[
            {'formato':'tapa-blanda','url':f'https://www.amazon.es/dp/84983823{i:02d}?tag=contrato-21'},
            {'formato':'tapa-dura','url':f'https://www.amazon.es/dp/84983824{i:02d}?tag=contrato-21'}]) for i in range(10)]
        provider=Provider()
        _,stats=refresh_offers({'libros':books},{'offers':[]},provider,'contrato-21',NOW)
        self.assertEqual(provider.calls.count('isbn'),0,'con ASIN no hace falta buscar por ISBN')
        self.assertEqual([c for c in provider.calls if isinstance(c,int)],[10,10],'20 ASIN en 2 peticiones')
        self.assertEqual(stats['requests'],12,'10 búsquedas de formatos + 2 lotes')
        self.assertTrue(all(o.get('precio_centimos')==1135 for b in books for o in b['formatos_compra']),
                        'cada formato recibe el precio de su propio ASIN dentro del lote')
        provider.calls.clear()
        refresh_offers({'libros':books},{'offers':[]},provider,'contrato-21',NOW+timedelta(days=7),sweep_days=1)
        self.assertNotIn('discover',provider.calls,'la búsqueda de formatos no se repite cada noche')
        provider.calls.clear()
        refresh_offers({'libros':books},{'offers':[]},provider,'contrato-21',NOW+timedelta(days=91),sweep_days=1)
        self.assertEqual(provider.calls.count('discover'),10,'se vuelve a buscar a los 90 días')

    def test_a_cut_off_night_still_moves_the_sweep_forward(self):
        many={'libros':[dict(BOOK,id=f'lib-{i}',formatos_compra=[]) for i in range(20)]}
        _,stats=refresh_offers(many,{'offers':[]},lambda b:response(),'contrato-21',NOW,budget=7)
        self.assertEqual(stats['updated'],5,'el primer grupo de 5 queda guardado')
        _,stats=refresh_offers(many,{'offers':[]},lambda b:response(),'contrato-21',NOW+timedelta(days=1),budget=7)
        self.assertEqual({b['id'] for b in many['libros'] if b.get('precios_amazon_revision')=='2026-10-22'},
                         {f'lib-{i}' for i in range(5,10)},'la noche siguiente sigue por los pendientes')

if __name__=='__main__':
    unittest.main()
