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
from reading_amazon_market import select_offers,refresh_offers,CreatorsPrices,money_cents,discovery_index,miss_reason,discover_page_formats,swatch_formats,discover_real_covers,page_cover_url,isbn10,store_prices,prune_foreign_editions
import tempfile

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

    def test_exact_ean_tolerates_series_order_and_longer_names(self):
        # Con el EAN exacto: «Saga 1. Título» frente a «Título (Saga 1)», un segundo apellido
        # o el crédito como ilustrador no dejan el libro sin precio.
        book=dict(BOOK,titulo='Indomables 1. El despertar de la magia',autores=['Diego Arboleda'])
        for title,contributor in [('El despertar de la magia (Indomables 1)',{'name':'Diego Arboleda Rodríguez','role':'Author'}),
                                  ('Indomables 1: El despertar de la magia (Spanish Edition)',{'name':'Diego Arboleda','role':'Illustrator'})]:
            payload=response(); info=payload['searchResult']['items'][0]['itemInfo']
            info['title']={'displayValue':title}; info['byLineInfo']={'contributors':[contributor]}
            self.assertEqual(len(select_offers(book,payload,'contrato-21',NOW)),1,title)
            self.assertEqual(miss_reason(book,[payload]),'sin_oferta_nueva')

    def test_tolerance_needs_the_exact_ean(self):
        book=dict(BOOK,titulo='Indomables 1. El despertar de la magia',autores=['Diego Arboleda'])
        payload=response(); info=payload['searchResult']['items'][0]['itemInfo']
        info['title']={'displayValue':'El despertar de la magia (Indomables 1)'}
        info['byLineInfo']={'contributors':[{'name':'Diego Arboleda Rodríguez','role':'Author'}]}
        info['externalIds']={'eans':{'displayValues':['9788425374012']}}
        self.assertEqual(select_offers(book,payload,'contrato-21',NOW),[])
        # Ni con el EAN exacto pasa otro libro de la serie u otra persona con un nombre en común.
        for title,name in [('Indomables 2. El despertar de la magia','Diego Arboleda'),
                           ('Indomables 1. El despertar de la magia','Diego Pérez')]:
            payload=response(); info=payload['searchResult']['items'][0]['itemInfo']
            info['title']={'displayValue':title}; info['byLineInfo']={'contributors':[{'name':name,'role':'Author'}]}
            self.assertEqual(select_offers(book,payload,'contrato-21',NOW),[],title+name)

    def test_known_asin_of_another_edition_in_the_same_binding_is_not_priced(self):
        # «Mentiras y secretos» (Penguin Bolsillo) guardaba el ASIN de la rústica de Montena:
        # 18,95 € contra un PVP de 10,95 €. El ASIN conocido no basta si es otro ISBN-10.
        url='https://www.amazon.es/dp/8418057610?tag=contrato-21'
        book=dict(BOOK,formatos_compra=[{'formato':'tapa-blanda','url':url,'precio_centimos':1895}])
        payload=response(); item=payload['searchResult']['items'][0]
        item['asin']='8418057610'; item['itemInfo']['externalIds']={'eans':{'displayValues':['9788418057618']}}
        self.assertEqual(select_offers(book,payload,'contrato-21',NOW),[])
        self.assertEqual(prune_foreign_editions(book),1)
        self.assertEqual(book['formatos_compra'],[])
        # Otra encuadernación con otro ISBN sí es legítima (la tapa dura de una edición en rústica).
        other=dict(BOOK,formatos_compra=[{'formato':'tapa-dura','url':url}])
        self.assertEqual(prune_foreign_editions(other),0)
        own=dict(BOOK,formatos_compra=[{'formato':'tapa-blanda','url':'https://www.amazon.es/dp/8498382378'}])
        self.assertEqual(prune_foreign_editions(own),0)

    def test_used_subscription_and_prime_prices_are_not_general_prices(self):
        for update in [{'condition':{'value':'Used'}},{'type':'SUBSCRIBEAND_SAVE'},
                       {'dealDetails':{'accessType':'PRIME_EXCLUSIVE'}},
                       {'availability':{'type':'OUTOFSTOCK'}}]:
            payload=response(); payload['searchResult']['items'][0]['offersV2']['listings'][0].update(update)
            self.assertEqual(select_offers(BOOK,payload,'contrato-21',NOW),[])

    def test_only_eur_and_finite_decimal_amounts(self):
        for amount,currency in [('11,35','EUR'),(True,'EUR'),('nan','EUR'),('1.111','EUR'),(5,'USD'),(0,'EUR')]:
            self.assertIsNone(money_cents({'amount':amount,'currency':currency}))

    def test_prices_outside_the_published_range_are_dropped(self):
        for amount in [0.99,1000.01]:
            payload=response(); payload['searchResult']['items'][0]['offersV2']['listings'][0]['price']['money']['amount']=amount
            self.assertEqual(select_offers(BOOK,payload,'contrato-21',NOW),[],amount)
        for amount,cents in [(1,100),(1000,100000)]:
            payload=response(); payload['searchResult']['items'][0]['offersV2']['listings'][0]['price']['money']['amount']=amount
            self.assertEqual(select_offers(BOOK,payload,'contrato-21',NOW)[0]['precio_centimos'],cents)

    def test_edition_specific_known_formats_keep_independent_prices(self):
        book=copy.deepcopy(BOOK)
        book['formatos_compra']=[{'formato':'ebook','url':'https://www.amazon.es/dp/B08CYCPBZN?tag=contrato-21'}]
        payload=response(); item=payload['searchResult']['items'][0]
        item['asin']='B08CYCPBZN'; item['itemInfo']['externalIds']={}
        item['itemInfo']['classifications']['binding']['displayValue']='Versión Kindle'
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
    def test_report_says_why_a_book_still_has_no_offer(self):
        empty={'searchResult':{'items':[]}}
        self.assertEqual(miss_reason(BOOK,[empty]),'sin_resultados')
        self.assertEqual(miss_reason(BOOK,[kindle('Otra cosa')]),'titulo_distinto')
        other=response(); other['searchResult']['items'][0]['itemInfo']['byLineInfo']['contributors'][0]['name']='Otra Persona'
        self.assertEqual(miss_reason(BOOK,[empty,other]),'autor_distinto')
        print_no_isbn=response(); print_no_isbn['searchResult']['items'][0]['itemInfo']['externalIds']={}
        self.assertEqual(miss_reason(BOOK,[print_no_isbn]),'sin_isbn_ni_edicion_digital')
        no_listing=response(); no_listing['searchResult']['items'][0]['offersV2']={'listings':[]}
        self.assertEqual(miss_reason(BOOK,[no_listing]),'sin_oferta_nueva')
        book=dict(BOOK,formatos_compra=[])
        _,stats=refresh_offers({'libros':[book]},{'offers':[]},lambda b:no_listing,'contrato-21',NOW)
        self.assertEqual(stats['sin_oferta'],[{'book_id':'lib-1','motivo':'sin_oferta_nueva'}])
        _,stats=refresh_offers({'libros':[dict(BOOK,formatos_compra=[])]},{'offers':[]},lambda b:response(),'contrato-21',NOW)
        self.assertEqual(stats['sin_oferta'],[])

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

    def test_books_without_ebook_are_searched_in_the_kindle_store(self):
        # Ten results across all departments miss the Kindle of a saga's fourth volume.
        self.assertEqual(discovery_index(dict(BOOK,formatos_compra=[{'formato':'tapa-blanda'}])),'KindleStore')
        self.assertEqual(discovery_index(dict(BOOK,formatos_compra=[{'formato':'ebook'}])),'All')
        class Provider:
            def __init__(self): self.searched=[]
            def __call__(self,book): return response()
            def discover(self,book): self.searched.append(book['id']); return {'searchResult':{'items':[]}}
        books=[dict(BOOK,id=f'lib-{i}',precios_amazon_revision='2026-10-20',formatos_amazon_buscados='2026-10-20',formatos_compra=[{'formato':'tapa-blanda'}]) for i in range(14)]
        # An entry without url (written by hand) is no ASIN, not the end of the night.
        books[9].pop('formatos_amazon_buscados')
        provider=Provider()
        refresh_offers({'libros':books},{'offers':[]},provider,'contrato-21',NOW)
        self.assertEqual(provider.searched,['lib-9'],'el libro sin buscar no espera a su turno de precio')

    def test_known_asins_are_priced_ten_per_request_and_formats_searched_once(self):
        class Provider:
            def __init__(self): self.calls=[]
            def __call__(self,book): self.calls.append('isbn'); return response()
            def discover(self,book): self.calls.append('discover'); return {'searchResult':{'items':[]}}
            def items(self,asins):
                self.calls.append(len(asins))
                payload=response(); item=payload['searchResult']['items'][0]
                def priced(a):
                    clone=copy.deepcopy(item); clone['asin']=a
                    clone['itemInfo']['classifications']['binding']['displayValue']='Hardcover' if a.startswith('84983824') else 'Paperback'
                    return clone
                return {'itemsResult':{'items':[priced(a) for a in asins]}}
        # ASIN ficticios: sin formato_edicion no se toman por otra edición de la misma encuadernación.
        books=[dict(BOOK,id=f'lib-{i}',isbn13='9788498382372',formato_edicion=None,formatos_compra=[
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

    def test_books_without_any_offer_search_formats_every_sweep(self):
        class Provider:
            def __init__(self): self.calls=[]
            def __call__(self,book): self.calls.append('isbn'); return {'searchResult':{'items':[]}}
            def discover(self,book): self.calls.append('discover'); return {'searchResult':{'items':[]}}
        books=[dict(BOOK,id='lib-sin',formatos_compra=[])]
        provider=Provider()
        refresh_offers({'libros':books},{'offers':[]},provider,'contrato-21',NOW)
        provider.calls.clear()
        refresh_offers({'libros':books},{'offers':[]},provider,'contrato-21',NOW+timedelta(days=7),sweep_days=1)
        self.assertEqual(provider.calls,['isbn','discover'],'sin ninguna oferta no se esperan 90 días para buscar por título')

    def test_a_cut_off_night_still_moves_the_sweep_forward(self):
        many={'libros':[dict(BOOK,id=f'lib-{i}',formatos_compra=[]) for i in range(20)]}
        _,stats=refresh_offers(many,{'offers':[]},lambda b:response(),'contrato-21',NOW,budget=7)
        self.assertEqual(stats['updated'],5,'el primer grupo de 5 queda guardado')
        _,stats=refresh_offers(many,{'offers':[]},lambda b:response(),'contrato-21',NOW+timedelta(days=1),budget=7)
        self.assertEqual({b['id'] for b in many['libros'] if b.get('precios_amazon_revision')=='2026-10-22'},
                         {f'lib-{i}' for i in range(5,10)},'la noche siguiente sigue por los pendientes')

    def test_a_book_amazon_does_not_list_does_not_stop_the_sweep(self):
        # HTTP 200 with only errors cut the whole night after five books.
        many={'libros':[dict(BOOK,id=f'lib-{i}',formatos_compra=[]) for i in range(12)]}
        def provider(book):
            return {'errors':[{'code':'NoResults','message':'No results'}]} if book['id']=='lib-0' else response()
        _,stats=refresh_offers(many,{'offers':[]},provider,'contrato-21',NOW)
        self.assertNotIn('status',stats)
        self.assertEqual(stats['updated'],12)
        self.assertEqual(stats['errores_amazon'],{'NoResults':1})
        self.assertEqual([m['book_id'] for m in stats['sin_oferta']],['lib-0'])
        self.assertTrue(all(b.get('formatos_compra') for b in many['libros'][1:]))


SWATCH_PAGE=('<ul><li id="tmm-grid-swatch-KINDLE" class="a-column swatchElement unselected"><a href="/Coraline/dp/B00EBOOK01/ref=tmm">Kindle</a></li>'
             '<li id="tmm-grid-swatch-AUDIO_DOWNLOAD" class="a-column swatchElement unselected"><a href="/dp/B0AUDIO001?ref=tmm">Audiolibro</a></li>'
             '<li id="tmm-grid-swatch-PAPERBACK" class="a-column swatchElement selected"><a href="javascript:void(0)">Tapa blanda</a></li></ul>')


class AmazonPageFormatTests(unittest.TestCase):
    def test_swatches_map_to_formats_and_selected_is_own_asin(self):
        self.assertEqual(swatch_formats(SWATCH_PAGE,'8498382378'),
                         {'ebook':'B00EBOOK01','audiolibro':'B0AUDIO001','tapa-blanda':'8498382378'})

    def test_missing_formats_are_added_without_price(self):
        book={**BOOK,'formatos_compra':[{'formato':'tapa-blanda','url':'https://www.amazon.es/dp/8498382378?tag=davidporto-21'}]}
        stats=discover_page_formats({'libros':[book]},lambda url:SWATCH_PAGE,'davidporto-21',NOW)
        self.assertEqual(stats['formats_added'],2)
        self.assertEqual([o['formato'] for o in book['formatos_compra']],['tapa-blanda','ebook','audiolibro'])
        self.assertNotIn('precio_centimos',book['formatos_compra'][2])
        self.assertEqual(book['formatos_pagina_buscados'],'2026-10-21')
        # Not asked again until the rediscovery window passes.
        self.assertEqual(discover_page_formats({'libros':[book]},lambda url:SWATCH_PAGE,'davidporto-21',NOW)['checked'],0)

    def test_bot_check_page_stops_the_run(self):
        books=[{**BOOK,'id':f'lib-{i}','formatos_compra':[{'formato':'tapa-blanda','url':'https://www.amazon.es/dp/8498382378'}]} for i in range(3)]
        calls=[]
        stats=discover_page_formats({'libros':books},lambda url:calls.append(url) or '<form action="/errors/validateCaptcha">',
                                    'davidporto-21',NOW)
        self.assertEqual((stats['blocked'],len(calls)),(1,1))
        self.assertNotIn('formatos_pagina_buscados',books[0])

COVER_PAGE=('<img alt="x" src="https://m.media-amazon.com/images/I/51qFSR41gJL._SY342_.jpg" '
            'data-a-dynamic-image="{&quot;https://m.media-amazon.com/images/I/51qFSR41gJL._SY342_.jpg&quot;:[342,225]}" id="landingImage">')


class AmazonRealCoverTests(unittest.TestCase):
    def test_cover_url_drops_size_suffix(self):
        self.assertEqual(page_cover_url(COVER_PAGE),'https://m.media-amazon.com/images/I/51qFSR41gJL.jpg')
        self.assertIsNone(page_cover_url('<html></html>'))
        self.assertEqual(isbn10('9788498382372'),'8498382378')
        self.assertIsNone(isbn10('9791388147302'))

    def test_typographic_cover_is_replaced_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'assets').mkdir()
            book={**BOOK,'portada_local':'/assets/isbn-9788498382372.webp',
                  'portada_fuente_url':'https://www.todostuslibros.com/libros/coraline_978-84-9838-237-2'}
            pages=[]
            stats=discover_real_covers({'libros':[book,{**BOOK,'id':'lib-2','portada_fuente_url':'https://editorial.example/c.jpg'}]},
                                       root,lambda url:pages.append(url) or COVER_PAGE,lambda url:b'raw',
                                       lambda raw:(b'big',b'small',(650,988)),NOW)
            self.assertEqual((stats['covers_replaced'],pages),(1,['https://www.amazon.es/dp/8498382378']))
            self.assertEqual((root/'assets/isbn-9788498382372-320.webp').read_bytes(),b'small')
            self.assertEqual((book['portada_ancho'],book['portada_sustituida']),(650,True))
            self.assertEqual(discover_real_covers({'libros':[book]},root,lambda url:COVER_PAGE,lambda url:b'',
                                                  lambda raw:(b'',b'',(1,1)),NOW)['checked'],0)

    def test_rejected_image_keeps_generated_cover(self):
        book={**BOOK,'portada_local':'/assets/x.webp','portada_fuente_url':'https://www.todostuslibros.com/libros/x'}
        def reject(raw):
            raise ValueError('pequeña')
        stats=discover_real_covers({'libros':[book]},Path('.'),lambda url:COVER_PAGE,lambda url:b'',reject,NOW)
        self.assertEqual((stats['covers_replaced'],stats['errors']),(0,1))
        self.assertNotIn('portada_sustituida',book)



class AmazonPriceDropTests(unittest.TestCase):
    URL='https://www.amazon.es/dp/B000000001?tag=davidporto-21'
    def option(self,**extra):
        return {'formato':'ebook','url':self.URL,'fuente_url':'https://www.amazon.es/dp/B000000001','fecha_verificacion':'2026-11-01','precio_centimos':1000,**extra}
    def offer(self,price,reference=None):
        return {'formato':'ebook','url':self.URL,'precio_centimos':price,**({'precio_referencia_centimos':reference} if reference else {})}

    def test_drop_against_our_old_price_is_not_an_offer(self):
        # 2026-11-05: 17,96 -> 17,95 € appeared as an offer; only Amazon's own reference price counts.
        book={'formatos_compra':[self.option(precio_anterior_centimos=1200,bajada_fecha='2026-11-01')]}
        store_prices(book,[self.offer(799)],'2026-11-03')
        self.assertEqual(book['formatos_compra'][0]|{},self.option(precio_centimos=799,fecha_verificacion='2026-11-03'))

    def test_reference_price_only_when_higher(self):
        book={'formatos_compra':[self.option()]}
        store_prices(book,[self.offer(1000,1500)],'2026-11-03')
        self.assertEqual(book['formatos_compra'][0]['precio_referencia_centimos'],1500)
        store_prices(book,[self.offer(1000,1000)],'2026-11-04')
        self.assertNotIn('precio_referencia_centimos',book['formatos_compra'][0])

    def test_kindle_print_price_is_not_a_discount(self):
        # 2026-11-04: Amazon gives the print edition price as the ebook savingBasis; 12 ebooks showed -50 %.
        book={'pvp_centimos':2390,'formatos_compra':[
            {'formato':'tapa-dura','url':'https://www.amazon.es/dp/8400000001?tag=davidporto-21','precio_centimos':2270,'precio_referencia_centimos':2390},
            self.option()]}
        store_prices(book,[self.offer(1234,2390)],'2026-11-04')
        self.assertNotIn('precio_referencia_centimos',book['formatos_compra'][1])
        store_prices(book,[self.offer(950,1000)],'2026-11-05')  # a real ebook list price still counts
        self.assertEqual(book['formatos_compra'][1]['precio_referencia_centimos'],1000)


if __name__=='__main__':
    unittest.main()
