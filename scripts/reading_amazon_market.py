"""Bounded Creators API prices; no browser session or invented ASINs."""
import json
import re
import time
from datetime import date,datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

from reading_ratings_refresh import isbn13, title_matches, author_matches, key

RESOURCES=['itemInfo.title','itemInfo.byLineInfo','itemInfo.externalIds',
           'itemInfo.classifications','offersV2.listings.price',
           'offersV2.listings.condition','offersV2.listings.availability',
           'offersV2.listings.dealDetails','offersV2.listings.type']
# Amazon's own cap for a new Creators API account (api-rates): 1 request per
# second and 8640 per day. Not a choice of ours, just the ceiling.
AMAZON_DAILY_LIMIT=8640
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


def select_offers(book,payload,tag,now):
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
            expires=now+timedelta(hours=24)
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

    def items(self,asins):
        # One request prices up to ten ASINs, whichever books they belong to.
        return self.post('https://creatorsapi.amazon/catalog/v1/getItems',{
            'marketplace':'www.amazon.es','partnerTag':self.tag,'condition':'New',
            'currencyOfPreference':'EUR','resources':RESOURCES,
            'itemIds':list(asins)[:10],'itemIdType':'ASIN'},self.headers())

    def discover(self,book):
        # Title + author across all departments finds the Kindle/Audible editions.
        return self.post('https://creatorsapi.amazon/catalog/v1/searchItems',{
            'marketplace':'www.amazon.es','partnerTag':self.tag,'condition':'New',
            'currencyOfPreference':'EUR','resources':RESOURCES+['itemInfo.contentInfo'],
            'keywords':book['titulo']+' '+book['autores'][0],'searchIndex':'All','itemCount':10},
            self.headers())


def store_prices(book,offers,day):
    """Prices live in formatos_compra and stay on the page until a newer one arrives."""
    options=[dict(o) for o in book.get('formatos_compra',[])]
    by_format={o['formato']:o for o in options}
    added=0
    for offer in offers:
        asin=asin_from_url(offer['url'])
        current=by_format.get(offer['formato'])
        if current is None:
            current={'formato':offer['formato'],'url':offer['url'],
                     'fuente_url':f'https://www.amazon.es/dp/{asin}','fecha_verificacion':day}
            options.append(current); by_format[offer['formato']]=current
            added+=1
        elif asin_from_url(current['url'])!=asin:
            continue  # An already verified edition is never replaced by another ASIN.
        current.update(url=offer['url'],precio_centimos=offer['precio_centimos'],fecha_verificacion=day)
    order=list(FORMAT_ORDER)
    book['formatos_compra']=sorted(options,key=lambda o:order.index(o['formato']))
    return added


FORMAT_ORDER=('tapa-blanda','tapa-dura','ebook','audiolibro')
# Kindle/audiobook editions often appear months after the print one: look again
# after this long, so books without a digital edition do not spend quota nightly.
REDISCOVER_AFTER=timedelta(days=90)


def needs_discovery(book,now):
    formats={o['formato'] for o in book.get('formatos_compra',[])}
    if {'ebook','audiolibro'}<=formats:
        return False
    if not formats:
        # Nothing to buy yet (new release, ISBN Amazon does not list): search by
        # title on every sweep; it is a handful of requests against 8640 a day.
        return True
    searched=book.get('formatos_amazon_buscados')
    return not searched or now.date()-date.fromisoformat(searched)>=REDISCOVER_AFTER


def only_items(payload,asins):
    """The share of a batched getItems answer that belongs to one book."""
    container=next((v for f in ('itemsResult','itemResults','searchResult')
                    if isinstance((v:=amazon_dict(payload).get(f)),dict)),{})
    return {'itemsResult':{'items':[i for i in amazon_list(container.get('items'))
                                    if isinstance(i,dict) and i.get('asin') in asins]}}


def refresh_offers(catalogue,market,provider,tag,now,budget=AMAZON_DAILY_LIMIT,sweep_days=7):
    """Nightly sweep: books never priced plus the ones checked longest ago, so the
    whole catalogue comes round every sweep_days. Known ASINs are priced ten per
    request; ISBN and format searches run once per book. Prices go into the books;
    market is untouched."""
    if not 0<=budget<=AMAZON_DAILY_LIMIT:
        raise ValueError('Price refresh budget outside the Amazon daily limit')
    now=now.astimezone(timezone.utc)
    day=now.date().isoformat()
    books=[b for b in catalogue['libros'] if b.get('estado')=='publicado' and isbn13(b.get('isbn13'))]
    books.sort(key=lambda b:b.get('precios_amazon_revision',''))
    unpriced=sum(not b.get('precios_amazon_revision') for b in books)
    due=books[:max(unpriced,-(-len(books)//max(1,sweep_days)))]
    stats={'attempted':0,'updated':0,'prices':0,'requests':0,'formats_added':0,'failures':[],'sin_oferta':[]}
    answers={}

    def ask(call,*args):
        if stats['requests']>=budget:
            raise LookupError
        stats['requests']+=1
        payload=call(*args)
        if payload.get('errors') and not any(payload.get(key) for key in ['searchResult','itemsResult','itemResults']):
            raise RuntimeError('Amazon returned only errors')
        return payload

    def keep(found,book,payload):
        answers.setdefault(book['id'],[]).append(payload)
        for offer in select_offers(book,payload,tag,now):
            best=found.get(offer['formato'])
            if not best or best['precio_centimos']>offer['precio_centimos']:
                found[offer['formato']]=offer

    # Five books hold about ten ASINs: one getItems each group. A group is saved
    # as soon as it is complete, so a cut-off night still moves the sweep forward.
    for start in range(0,len(due),5):
        group=due[start:start+5]
        found={b['id']:{} for b in group}
        current,priced=group[0],False
        try:
            for current in group:
                if not verified_formats(current):
                    # No ASIN yet: the ISBN search finds the printed edition.
                    keep(found[current['id']],current,ask(provider,current))
                if hasattr(provider,'discover') and needs_discovery(current,now):
                    # Kindle and audiobook editions have their own ASIN and no ISBN.
                    keep(found[current['id']],current,ask(provider.discover,current))
                    current['formatos_amazon_buscados']=day
            priced=True
            pending=[(b,asin) for b in group for asin,fmt in verified_formats(b).items() if fmt not in found[b['id']]]
            if hasattr(provider,'items'):
                asins=list(dict.fromkeys(asin for _,asin in pending))
                for i in range(0,len(asins),10):
                    batch=set(asins[i:i+10])
                    owners={b['id']:b for b,asin in pending if asin in batch}
                    current=next(iter(owners.values()))
                    payload=ask(provider.items,asins[i:i+10])
                    for book in owners.values():
                        keep(found[book['id']],book,only_items(payload,set(verified_formats(book))))
            else:
                for current in {b['id']:b for b,_ in pending}.values():
                    keep(found[current['id']],current,ask(provider,current))
        except LookupError:
            # Only the books that reached Amazon count; the one cut off did not.
            stats['attempted']+=len(group) if priced else group.index(current)
            break  # Daily limit reached: the rest stays due for tomorrow.
        except (RuntimeError,OSError,ValueError,KeyError,TypeError) as exc:
            stats['attempted']+=len(group)
            stats['failures'].append({'book_id':current['id'],'error':str(exc)[:140]})
            stats['status']='pending_amazon_eligibility' if str(exc)=='pending_amazon_eligibility' else 'provider_unavailable'
            break
        stats['attempted']+=len(group)
        for book in group:
            stats['formats_added']+=store_prices(book,found[book['id']].values(),day)
            book['precios_amazon_revision']=day
            stats['updated']+=1
            stats['prices']+=len(found[book['id']])
            if not book.get('formatos_compra'):
                stats['sin_oferta'].append({'book_id':book['id'],'motivo':miss_reason(book,answers.get(book['id'],[]))})
    return market,stats


MISS_STAGES=('sin_resultados','titulo_distinto','autor_distinto','sin_isbn_ni_edicion_digital','sin_oferta_nueva')


def miss_reason(book,payloads):
    """How far the closest Amazon result got before select_offers dropped it, so the
    nightly report says why a book still has no offer instead of a bare count."""
    wanted,best=isbn13(book.get('isbn13')),0
    for payload in payloads:
        container=next((v for f in ('searchResult','itemsResult','itemResults')
                        if isinstance((v:=amazon_dict(payload).get(f)),dict)),{})
        for item in amazon_list(container.get('items')):
            info=amazon_dict(amazon_dict(item).get('itemInfo'))
            title=amazon_dict(info.get('title')).get('displayValue','')
            stage=1
            if isinstance(title,str) and title_matches(title,book['titulo']):
                stage=2
                names=[c.get('name','') for c in amazon_list(amazon_dict(info.get('byLineInfo')).get('contributors'))
                       if isinstance(c,dict) and isinstance(c.get('name'),str)]
                if any(author_matches(n,a) for n in names for a in book['autores']):
                    stage=3
                    eans=amazon_list(amazon_dict(amazon_dict(info.get('externalIds')).get('eans')).get('displayValues'))
                    if wanted in {isbn13(v) for v in eans if isinstance(v,str)} or in_spanish(info):
                        stage=4
            best=max(best,stage)
    return MISS_STAGES[best]
