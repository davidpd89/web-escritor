"""Bounded Creators API prices; no browser session or invented ASINs."""
import json
import re
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from reading_ratings_refresh import isbn13, title_matches, author_matches, key

RESOURCES=['itemInfo.title','itemInfo.byLineInfo','itemInfo.externalIds',
           'itemInfo.classifications','offersV2.listings.price',
           'offersV2.listings.condition','offersV2.listings.availability',
           'offersV2.listings.dealDetails','offersV2.listings.type']


def asin_from_url(url):
    match=re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})(?:[/?]|$)',url or '')
    return match.group(1) if match else None


def money_cents(money):
    if not isinstance(money,dict) or money.get('currency')!='EUR' or isinstance(money.get('amount'),bool):
        return None
    try:
        cents=Decimal(str(money['amount']))*100
        return int(cents) if cents.is_finite() and cents==cents.to_integral_value() and 0<cents<100000000 else None
    except (InvalidOperation,ValueError,KeyError,TypeError):
        return None


def verified_formats(book):
    known={asin_from_url(o['url']):o['formato'] for o in book.get('formatos_compra',[])}
    direct=asin_from_url(book.get('url_amazon_afiliada'))
    if direct and book.get('formato_edicion'):
        known.setdefault(direct,book['formato_edicion'])
    return {asin:fmt for asin,fmt in known.items() if asin}


def select_offers(book,payload,tag,now):
    if not re.fullmatch(r'[A-Za-z0-9-]+',tag):
        raise ValueError('Invalid partner tag')
    now=now.astimezone(timezone.utc)
    container=payload.get('searchResult') or payload.get('itemsResult') or payload.get('itemResults') or {}
    offers={}
    wanted=isbn13(book.get('isbn13'))
    if not wanted:
        return []
    known=verified_formats(book)
    for item in container.get('items',[]):
        if not isinstance(item,dict):
            continue
        asin=item.get('asin','')
        if not re.fullmatch(r'[A-Z0-9]{10}',asin):
            continue
        info=item.get('itemInfo') or {}
        if not title_matches((info.get('title') or {}).get('displayValue',''),book['titulo']):
            continue
        authors=[c.get('name','') for c in (info.get('byLineInfo') or {}).get('contributors',[]) if key(c.get('role','')) in {'author','autor'}]
        if not any(author_matches(author,name) for author in authors for name in book['autores']):
            continue
        identifiers=(info.get('externalIds') or {}).get('eans') or {}
        isbn_match=wanted in {isbn13(value) for value in identifiers.get('displayValues',[])}
        binding=key(((info.get('classifications') or {}).get('binding') or {}).get('displayValue',''))
        fmt=known.get(asin) or {'paperback':'tapa-blanda','tapa blanda':'tapa-blanda',
            'hardcover':'tapa-dura','tapa dura':'tapa-dura','kindle':'ebook','formato kindle':'ebook',
            'audio cd':'audiolibro','audible audiobook':'audiolibro'}.get(binding)
        if not fmt or (asin not in known and not isbn_match):
            continue
        for listing in (item.get('offersV2') or {}).get('listings',[]):
            if not isinstance(listing,dict):
                continue
            if (listing.get('condition') or {}).get('value')!='New' or listing.get('type'):
                continue  # Exclude subscriptions, lightning/limited and conditional deals.
            access=(listing.get('dealDetails') or {}).get('accessType')
            if access and access!='ALL':
                continue
            expires=now+timedelta(hours=24)
            deal=listing.get('dealDetails') or {}
            try:
                if deal.get('startTime') and datetime.fromisoformat(deal['startTime'].replace('Z','+00:00'))>now:
                    continue
                if deal.get('endTime'):
                    expires=min(expires,datetime.fromisoformat(deal['endTime'].replace('Z','+00:00')))
                if expires<=now:
                    continue
            except (ValueError,TypeError):
                continue
            availability=(listing.get('availability') or {}).get('type')
            if availability not in {'IN_STOCK','INSTOCK','INSTOCKSCARCE','LEADTIME','PREORDER'}:
                continue
            price=listing.get('price') or {}
            cents=money_cents(price.get('money'))
            if cents is None:
                continue
            offer={'libro_id':book['id'],'formato':fmt,'tipo':'compra','moneda':'EUR',
                   'precio_centimos':cents,'url':f'https://www.amazon.es/dp/{asin}?tag={tag}',
                   'actualizado_en':now.isoformat(timespec='seconds').replace('+00:00','Z'),
                   'caduca_en':expires.isoformat(timespec='seconds').replace('+00:00','Z')}
            reference=money_cents((price.get('savingBasis') or {}).get('money'))
            if reference and reference>cents:
                offer['precio_referencia_centimos']=reference
            if fmt not in offers or offers[fmt]['precio_centimos']>cents:
                offers[fmt]=offer
    return list(offers.values())


class CreatorsPrices:
    def __init__(self,client_id,secret,tag):
        self.client_id,self.secret,self.tag=client_id,secret,tag
        self.token=None
        self.last=0

    def post(self,url,payload,headers=None):
        time.sleep(max(0,1.1-(time.monotonic()-self.last)))
        self.last=time.monotonic()
        request=Request(url,data=json.dumps(payload).encode(),method='POST',
                        headers={'Content-Type':'application/json',**(headers or {})})
        try:
            with urlopen(request,timeout=20) as response:
                result=json.load(response)
        except HTTPError as exc:
            try:
                error=json.loads(exc.read(20000))
            except ValueError:
                error={}
            if exc.code==403 and ('eligib' in str(error.get('message','')).lower() or any(e.get('code')=='AssociateNotEligible' for e in error.get('errors',[]) if isinstance(e,dict))):
                raise RuntimeError('pending_amazon_eligibility') from exc
            raise RuntimeError(f'Amazon Creators HTTP {exc.code}') from exc
        except (URLError,TimeoutError) as exc:
            raise RuntimeError('Amazon Creators unavailable') from exc
        if not isinstance(result,dict):
            raise RuntimeError('Invalid Amazon Creators response')
        return result

    def __call__(self,book):
        if not self.token:
            self.token=self.post('https://api.amazon.co.uk/auth/o2/token',{
                'grant_type':'client_credentials','client_id':self.client_id,
                'client_secret':self.secret,'scope':'creatorsapi::default'})['access_token']
        common={'marketplace':'www.amazon.es','partnerTag':self.tag,'condition':'New',
                'currencyOfPreference':'EUR','resources':RESOURCES}
        known=verified_formats(book)
        if known:
            operation='getItems'
            common.update(itemIds=list(known)[:10],itemIdType='ASIN')
        else:
            operation='searchItems'
            common.update(keywords=book['isbn13'],searchIndex='Books',itemCount=10)
        return self.post('https://creatorsapi.amazon/catalog/v1/'+operation,common,
                         {'Authorization':'Bearer '+self.token,'x-marketplace':'www.amazon.es'})


def refresh_offers(catalogue,market,provider,tag,now,budget=100):
    if not 0<=budget<=100:
        raise ValueError('Price refresh budget outside 0..100')
    books=[b for b in catalogue['libros'] if b.get('estado')=='publicado' and isbn13(b.get('isbn13'))]
    after=list(market.get('offers',[]))
    stats={'attempted':0,'updated':0,'offers':0,'failures':[]}
    offset=(now.astimezone(timezone.utc).date().toordinal()*max(1,budget))%len(books) if books else 0
    for book in (books[offset:]+books[:offset])[:budget]:
        stats['attempted']+=1
        try:
            payload=provider(book)
            if payload.get('errors') and not any(payload.get(key) for key in ['searchResult','itemsResult','itemResults']):
                raise RuntimeError('Amazon returned only errors')
            fresh=select_offers(book,payload,tag,now)
            after=[o for o in after if o.get('libro_id')!=book['id']]+fresh
            stats['updated']+=1
            stats['offers']+=len(fresh)
        except (RuntimeError,OSError,ValueError,KeyError,TypeError) as exc:
            stats['failures'].append({'book_id':book['id'],'error':str(exc)[:140]})
            stats['status']='pending_amazon_eligibility' if str(exc)=='pending_amazon_eligibility' else 'provider_unavailable'
            break
    return {**market,'offers':after},stats
