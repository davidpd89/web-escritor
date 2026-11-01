"""Bounded Creators API prices; no browser session or invented ASINs."""
import json
import re
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

from reading_ratings_refresh import isbn13, title_matches, author_matches, key

RESOURCES=['itemInfo.title','itemInfo.byLineInfo','itemInfo.externalIds',
           'itemInfo.classifications','offersV2.listings.price',
           'offersV2.listings.condition','offersV2.listings.availability',
           'offersV2.listings.dealDetails','offersV2.listings.type']
# Prices are refreshed in rotation, not hourly: an offer stays usable for a week
# and the whole catalogue cycles before it expires.
PRICE_MAX_AGE=timedelta(days=7)
# Kindle/audiobook editions have their own ASIN and no ISBN; look for them again
# only after this long, so books without a digital edition do not spend quota daily.
REDISCOVER_AFTER=timedelta(days=90)
BINDINGS={'paperback':'tapa-blanda','tapa blanda':'tapa-blanda','mass market paperback':'tapa-blanda',
          'libro de bolsillo':'tapa-blanda','hardcover':'tapa-dura','tapa dura':'tapa-dura',
          'kindle':'ebook','formato kindle':'ebook','kindle edition':'ebook','version kindle':'ebook',
          'edicion kindle':'ebook','ebook kindle':'ebook','audio cd':'audiolibro','cd de audio':'audiolibro',
          'audible audiobook':'audiolibro','audiolibro de audible':'audiolibro','audiolibro':'audiolibro'}


def asin_from_url(url):
    if not isinstance(url,str):
        return None
    try:
        parsed=urlsplit(url)
        if (parsed.scheme!='https'
                or parsed.netloc not in {'amazon.es','www.amazon.es'}
                or parsed.username is not None
                or parsed.password is not None):
            return None
    except ValueError:
        return None
    match=re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})(?:/|$)',parsed.path)
    return match.group(1) if match else None


def offer_url(item,asin,tag):
    # Amazon's own detailPageURL keeps our tag plus its linkCode, so the sale
    # also counts towards the Creators API quota; anything else falls back.
    url=item.get('detailPageURL')
    if asin_from_url(url)==asin and parse_qs(urlsplit(url).query).get('tag')==[tag]:
        return url
    return f'https://www.amazon.es/dp/{asin}?tag={tag}'


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


def same_title(title,canonical):
    # Without an ISBN a prefix match is not enough ("Dune" vs "Dune Mesías"):
    # only subtitles in brackets or after a colon may differ.
    bare=lambda t: key(re.sub(r'\s*[\(\[].*?[\)\]]','',t).split(':')[0])
    return bool(bare(canonical)) and bare(title)==bare(canonical)


def in_spanish(info):
    languages=amazon_list(amazon_dict(amazon_dict(info.get('contentInfo')).get('languages')).get('displayValues'))
    return any(isinstance(l,dict) and isinstance(l.get('displayValue'),str)
               and key(l['displayValue']) in {'espanol','spanish','castellano'} for l in languages)


def amazon_dict(value):
    return value if isinstance(value,dict) else {}


def amazon_list(value):
    return value if isinstance(value,list) else []


def select_offers(book,payload,tag,now,max_age=PRICE_MAX_AGE):
    if not re.fullmatch(r'[A-Za-z0-9-]+',tag):
        raise ValueError('Invalid partner tag')
    now=now.astimezone(timezone.utc)
    payload=amazon_dict(payload)
    container=next((value for field in ('searchResult','itemsResult','itemResults')
                    if isinstance((value:=payload.get(field)),dict)),{})
    offers={}
    wanted=isbn13(book.get('isbn13'))
    if not wanted:
        return []
    known=verified_formats(book)
    for item in amazon_list(container.get('items')):
        if not isinstance(item,dict):
            continue
        asin=item.get('asin','')
        if not isinstance(asin,str) or not re.fullmatch(r'[A-Z0-9]{10}',asin):
            continue
        info=amazon_dict(item.get('itemInfo'))
        title=amazon_dict(info.get('title')).get('displayValue','')
        if not isinstance(title,str) or not title_matches(title,book['titulo']):
            continue
        contributors=amazon_list(amazon_dict(info.get('byLineInfo')).get('contributors'))
        authors=[c.get('name','') for c in contributors
                 if isinstance(c,dict) and isinstance(c.get('name'),str)
                 and isinstance(c.get('role'),str)
                 and key(c['role']) in {'author','autor'}]
        if not any(author_matches(author,name) for author in authors for name in book['autores']):
            continue
        identifiers=amazon_dict(amazon_dict(info.get('externalIds')).get('eans'))
        isbn_match=wanted in {isbn13(value) for value in amazon_list(identifiers.get('displayValues'))
                              if isinstance(value,str)}
        binding_value=amazon_dict(amazon_dict(info.get('classifications')).get('binding')).get('displayValue','')
        binding=key(binding_value) if isinstance(binding_value,str) else ''
        fmt=known.get(asin) or BINDINGS.get(binding)
        digital=fmt in {'ebook','audiolibro'} and same_title(title,book['titulo']) and in_spanish(info)
        if not fmt or (asin not in known and not isbn_match and not digital):
            continue
        for listing in amazon_list(amazon_dict(item.get('offersV2')).get('listings')):
            if not isinstance(listing,dict):
                continue
            if amazon_dict(listing.get('condition')).get('value')!='New' or listing.get('type'):
                continue  # Exclude subscriptions, lightning/limited and conditional deals.
            if listing.get('dealDetails') is not None and not isinstance(listing['dealDetails'],dict):
                continue
            deal=amazon_dict(listing.get('dealDetails'))
            access=deal.get('accessType')
            if access and access!='ALL':
                continue
            expires=now+max_age
            try:
                if deal.get('startTime') and datetime.fromisoformat(deal['startTime'].replace('Z','+00:00'))>now:
                    continue
                if deal.get('endTime'):
                    expires=min(expires,datetime.fromisoformat(deal['endTime'].replace('Z','+00:00')))
                if expires<=now:
                    continue
            except (ValueError,TypeError):
                continue
            availability=amazon_dict(listing.get('availability')).get('type')
            if not isinstance(availability,str) or availability not in {'IN_STOCK','INSTOCK','INSTOCKSCARCE','LEADTIME','PREORDER'}:
                continue
            price=amazon_dict(listing.get('price'))
            cents=money_cents(price.get('money'))
            if cents is None:
                continue
            offer={'libro_id':book['id'],'formato':fmt,'tipo':'compra','moneda':'EUR',
                   'precio_centimos':cents,'url':offer_url(item,asin,tag),
                   'actualizado_en':now.isoformat(timespec='seconds').replace('+00:00','Z'),
                   'caduca_en':expires.isoformat(timespec='seconds').replace('+00:00','Z')}
            reference=money_cents(amazon_dict(price.get('savingBasis')).get('money'))
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

    def post(self,url,payload,headers=None,retries=3):
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
            if not isinstance(error,dict):
                error={}
            if exc.code==429 and retries:
                # Throttling is per second: wait what Amazon asks (bounded) and retry.
                wait=error.get('retryAfterSeconds') or (exc.headers or {}).get('Retry-After')
                try:
                    wait=min(60.0,max(1.0,float(wait)))
                except (TypeError,ValueError):
                    wait=2.0*2**(3-retries)
                time.sleep(wait)
                return self.post(url,payload,headers,retries-1)
            if exc.code==403 and ('eligib' in str(error.get('message','')).lower() or any(e.get('code')=='AssociateNotEligible' for e in error.get('errors',[]) if isinstance(e,dict))):
                raise RuntimeError('pending_amazon_eligibility') from exc
            raise RuntimeError(f'Amazon Creators HTTP {exc.code}') from exc
        except (URLError,TimeoutError) as exc:
            raise RuntimeError('Amazon Creators unavailable') from exc
        if not isinstance(result,dict):
            raise RuntimeError('Invalid Amazon Creators response')
        return result

    def headers(self):
        if not self.token:
            self.token=self.post('https://api.amazon.co.uk/auth/o2/token',{
                'grant_type':'client_credentials','client_id':self.client_id,
                'client_secret':self.secret,'scope':'creatorsapi::default'})['access_token']
        return {'Authorization':'Bearer '+self.token,'x-marketplace':'www.amazon.es'}

    def __call__(self,book):
        headers=self.headers()
        common={'marketplace':'www.amazon.es','partnerTag':self.tag,'condition':'New',
                'currencyOfPreference':'EUR','resources':RESOURCES}
        known=verified_formats(book)
        if known:
            operation='getItems'
            common.update(itemIds=list(known)[:10],itemIdType='ASIN')
        else:
            operation='searchItems'
            common.update(keywords=book['isbn13'],searchIndex='Books',itemCount=10)
        return self.post('https://creatorsapi.amazon/catalog/v1/'+operation,common,headers)

    def discover(self,book):
        # Title + author across all departments finds the Kindle/Audible editions.
        return self.post('https://creatorsapi.amazon/catalog/v1/searchItems',{
            'marketplace':'www.amazon.es','partnerTag':self.tag,'condition':'New',
            'currencyOfPreference':'EUR','resources':RESOURCES+['itemInfo.contentInfo'],
            'keywords':book['titulo']+' '+book['autores'][0],'searchIndex':'All','itemCount':10},
            self.headers())


def needs_discovery(book,now):
    options=book.get('formatos_compra',[])
    if {'ebook','audiolibro'}<={o['formato'] for o in options}:
        return False
    checked=max((o['fecha_verificacion'] for o in options),default='')
    return not checked or now.date()-datetime.fromisoformat(checked).date()>=REDISCOVER_AFTER


def remember_formats(book,offers,tag,now):
    # ASINs may be kept indefinitely: next refreshes use one getItems for every
    # format, and the static filters/links know the format without prices.
    options=list(book.get('formatos_compra',[]))
    have={o['formato'] for o in options}
    found={o['formato']:asin_from_url(o['url']) for o in offers}
    direct=asin_from_url(book.get('url_amazon_afiliada'))
    if direct and book.get('formato_edicion'):
        found.setdefault(book['formato_edicion'],direct)
    day=now.date().isoformat()
    added=[{'formato':fmt,'url':f'https://www.amazon.es/dp/{asin}?tag={tag}',
            'fuente_url':f'https://www.amazon.es/dp/{asin}','fecha_verificacion':day}
           for fmt,asin in sorted(found.items()) if asin and fmt not in have]
    if not added and options:
        # Nothing new: the date records that the search ran, retried after REDISCOVER_AFTER.
        options=[dict(o,fecha_verificacion=day) for o in options]
    book['formatos_compra']=options+added


def refresh_offers(catalogue,market,provider,tag,now,budget=100,max_age=PRICE_MAX_AGE):
    """Refresh a slice of the catalogue each day; discovered formats update the books in place."""
    if not 0<=budget<=1000:
        raise ValueError('Price refresh budget outside 0..1000')
    now=now.astimezone(timezone.utc)
    books=[b for b in catalogue['libros'] if b.get('estado')=='publicado' and isbn13(b.get('isbn13'))]
    after=list(market.get('offers',[]))
    stats={'attempted':0,'updated':0,'offers':0,'requests':0,'formats_added':0,'failures':[]}
    # Every book comes round a day before its price expires, with no more requests than that needs.
    per_day=min(len(books),-(-len(books)//max(1,max_age.days-1)))
    offset=(now.date().toordinal()*max(1,per_day))%len(books) if books else 0
    for book in (books[offset:]+books[:offset])[:per_day]:
        if stats['requests']>=budget:
            break
        stats['attempted']+=1
        try:
            payload=provider(book)
            stats['requests']+=1
            if payload.get('errors') and not any(payload.get(key) for key in ['searchResult','itemsResult','itemResults']):
                raise RuntimeError('Amazon returned only errors')
            fresh={o['formato']:o for o in select_offers(book,payload,tag,now,max_age)}
            if hasattr(provider,'discover') and stats['requests']<budget and needs_discovery(book,now):
                stats['requests']+=1
                for offer in select_offers(book,provider.discover(book),tag,now,max_age):
                    if offer['formato'] not in fresh or fresh[offer['formato']]['precio_centimos']>offer['precio_centimos']:
                        fresh[offer['formato']]=offer
                before=len(book.get('formatos_compra',[]))
                remember_formats(book,fresh.values(),tag,now)
                stats['formats_added']+=len(book['formatos_compra'])-before
            after=[o for o in after if o.get('libro_id')!=book['id']]+list(fresh.values())
            stats['updated']+=1
            stats['offers']+=len(fresh)
        except (RuntimeError,OSError,ValueError,KeyError,TypeError) as exc:
            stats['failures'].append({'book_id':book['id'],'error':str(exc)[:140]})
            stats['status']='pending_amazon_eligibility' if str(exc)=='pending_amazon_eligibility' else 'provider_unavailable'
            break
    # Expired prices leave the file even for books outside today's slice.
    stamp=now.isoformat(timespec='seconds').replace('+00:00','Z')
    after=[o for o in after if not isinstance(o.get('caduca_en'),str) or o['caduca_en']>stamp]
    return {**market,'offers':after},stats
