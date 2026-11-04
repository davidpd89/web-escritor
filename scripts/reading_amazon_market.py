"""Bounded Creators API prices; no browser session or invented ASINs."""
import gzip
import html
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
# Same bounds build-reading-catalogue.py enforces on formatos_compra: an offer outside
# them is dropped here, so one odd Amazon price cannot fail the whole publication.
PRICE_MIN_CENTS,PRICE_MAX_CENTS=100,100000
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


class DailyLimitReached(Exception):
    """Amazon's 8640 requests a day are spent. Not a LookupError: a KeyError in the
    data must not pass for the end of the night."""


def verified_formats(book):
    known={asin_from_url(o.get('url')):o['formato'] for o in book.get('formatos_compra',[])}
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
            if cents is None or not PRICE_MIN_CENTS<=cents<=PRICE_MAX_CENTS:
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
        # Title + author finds the Kindle/Audible editions. Ten results across all
        # departments miss the Kindle of a saga's later volumes, so a book without
        # an ebook is searched in the Kindle store itself.
        return self.post('https://creatorsapi.amazon/catalog/v1/searchItems',{
            'marketplace':'www.amazon.es','partnerTag':self.tag,'condition':'New',
            'currencyOfPreference':'EUR','resources':RESOURCES+['itemInfo.contentInfo'],
            'keywords':book['titulo']+' '+book['autores'][0],'searchIndex':discovery_index(book),'itemCount':10},
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
        elif asin_from_url(current.get('url')) not in (None,asin):
            continue  # An already verified edition is never replaced by another ASIN.
        if offer['formato'] in ('ebook','audiolibro') and offer.get('precio_referencia_centimos') in print_prices(book):
            offer={k:v for k,v in offer.items() if k!='precio_referencia_centimos'}  # Kindle «versión impresa», no descuento
        price_drop(current,offer,day)
        current.update(url=offer['url'],precio_centimos=offer['precio_centimos'],fecha_verificacion=day)
    order=list(FORMAT_ORDER)
    book['formatos_compra']=sorted(options,key=lambda o:order.index(o['formato']))
    return added


def print_prices(book):
    """PVP y precios en papel: Amazon da el de la versión impresa como savingBasis de los ebooks."""
    out={book.get('pvp_centimos')}
    for o in book.get('formatos_compra',[]):
        if o.get('formato') not in ('ebook','audiolibro'):
            out|={o.get('precio_centimos'),o.get('precio_referencia_centimos')}
    return out-{None}


def price_drop(current,offer,day):
    """Keep the list price (savingBasis) and the last drop so the site and a deals feed can show offers."""
    price=offer['precio_centimos']
    reference=offer.get('precio_referencia_centimos')
    if reference and reference>price:
        current['precio_referencia_centimos']=reference
    else:
        current.pop('precio_referencia_centimos',None)
    previous=current.get('precio_centimos')
    if previous and price<previous:
        current.update(precio_anterior_centimos=previous,bajada_fecha=day)
    elif previous and price>previous or current.get('precio_anterior_centimos',0)<=price:
        current.pop('precio_anterior_centimos',None); current.pop('bajada_fecha',None)


FORMAT_ORDER=('tapa-blanda','tapa-dura','ebook','audiolibro')
# Kindle/audiobook editions often appear months after the print one: look again
# after this long, so books without a digital edition do not spend quota nightly.
REDISCOVER_AFTER=timedelta(days=90)


def discovery_index(book):
    return 'All' if 'ebook' in {o['formato'] for o in book.get('formatos_compra',[])} else 'KindleStore'


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


# Format selector (twister) of an Amazon product page. Creators search hardly ever
# returns Audible audiobooks and misses many Kindle/hardcover siblings; the page of
# an ASIN already verified for the book lists them all with their own ASIN.
SWATCHES={'KINDLE':'ebook','AUDIO_DOWNLOAD':'audiolibro','AUDIOBOOK':'audiolibro',
          'HARDCOVER':'tapa-dura','PAPERBACK':'tapa-blanda','MASS_MARKET_PAPERBACK':'tapa-blanda'}
PAGE_REDISCOVER_AFTER=timedelta(days=30)


def swatch_formats(document,asin):
    """{formato: ASIN} from a product page; the selected swatch is the page's own ASIN."""
    found={}
    for m in re.finditer(r'id="tmm-grid-swatch-([A-Z_]+)"(.*?)(?=id="tmm-grid-swatch-|</ul>)',document,re.S):
        fmt=SWATCHES.get(m.group(1))
        if not fmt or fmt in found:
            continue
        block=m.group(2)[:4000]
        if re.match(r'[^>]*\bselected\b',block):
            found[fmt]=asin
        elif (link:=re.search(r'/dp/([A-Z0-9]{10})',block)):
            found[fmt]=link.group(1)
    return found


def needs_page_formats(book,now):
    formats={o['formato'] for o in book.get('formatos_compra',[])}
    if not verified_formats(book) or {'ebook','audiolibro'}<=formats:
        return False
    searched=book.get('formatos_pagina_buscados')
    return not searched or now.date()-date.fromisoformat(searched)>=PAGE_REDISCOVER_AFTER


def discover_page_formats(catalogue,fetch,tag,now,limit=60):
    """Adds the missing formats a product page offers. Prices come later from the API sweep,
    which prices every verified ASIN; the page itself is only read for the ASINs."""
    day=now.astimezone(timezone.utc).date().isoformat()
    books=[b for b in catalogue['libros'] if b.get('estado')=='publicado' and needs_page_formats(b,now)]
    books.sort(key=lambda b:b.get('formatos_pagina_buscados',''))
    stats={'checked':0,'formats_added':0,'blocked':0,'errors':0}
    for book in books[:limit]:
        asin=next(iter(verified_formats(book)))
        try:
            document=fetch(f'https://www.amazon.es/dp/{asin}')
        except (OSError,ValueError):
            stats['errors']+=1
            continue
        if 'tmm-grid-swatch' not in document:
            stats['blocked']+=1
            if 'captcha' in document.lower():
                break  # Amazon is asking for a captcha: try again on the next run.
            continue
        stats['checked']+=1
        book['formatos_pagina_buscados']=day
        options=book.setdefault('formatos_compra',[])
        have={o['formato'] for o in options}
        known=set(verified_formats(book))
        for fmt,found in swatch_formats(document,asin).items():
            if fmt in have or found in known:
                continue
            options.append({'formato':fmt,'url':f'https://www.amazon.es/dp/{found}?tag={tag}',
                            'fuente_url':f'https://www.amazon.es/dp/{found}','fecha_verificacion':day})
            stats['formats_added']+=1
        options.sort(key=lambda o:FORMAT_ORDER.index(o['formato']))
    return stats


COVER_HOSTS=('www.todostuslibros.com',)


def page_cover_url(document):
    """Full-size cover of a product page: the largest image of `landingImage`, without size suffix."""
    tag=re.search(r'<img[^>]*id="landingImage"[^>]*>',document) or re.search(r'<img[^>]*id="(?:ebooksImgBlkFront|imgBlkFront)"[^>]*>',document)
    found=re.findall(r'https://m\.media-amazon\.com/images/I/([A-Za-z0-9+%-]+)\.[^&"]*?(jpg|png)',tag.group(0).replace('&quot;','"')) if tag else []
    return f'https://m.media-amazon.com/images/I/{found[0][0]}.{found[0][1]}' if found else None


def isbn10(value):
    if not str(value).startswith('978'):
        return None
    body=str(value)[3:12]
    check=(11-sum((10-i)*int(d) for i,d in enumerate(body))%11)%11
    return body+('X' if check==10 else str(check))


def discover_real_covers(catalogue,root,fetch,fetch_bytes,convert,now,limit=20):
    """Swaps generated typographic covers for the edition's real cover from its Amazon page.
    `convert` validates and resizes the image (same rules as editorial covers)."""
    day=now.astimezone(timezone.utc).date().isoformat()
    books=[b for b in catalogue['libros'] if urlsplit(b.get('portada_fuente_url') or '').hostname in COVER_HOSTS
           and b.get('portadas_amazon_buscadas','')<(now-PAGE_REDISCOVER_AFTER).date().isoformat()]
    books.sort(key=lambda b:b.get('portadas_amazon_buscadas',''))
    stats={'checked':0,'covers_replaced':0,'blocked':0,'errors':0}
    for book in books[:limit]:
        formats=verified_formats(book)
        asin=next((a for a,f in formats.items() if f!='ebook'),None) or isbn10(book.get('isbn13')) or next(iter(formats),None)
        if not asin:
            continue
        try:
            document=fetch(f'https://www.amazon.es/dp/{asin}')
        except (OSError,ValueError):
            stats['errors']+=1
            continue
        if 'captcha' in document.lower() and 'landingImage' not in document:
            stats['blocked']+=1
            break
        stats['checked']+=1
        book['portadas_amazon_buscadas']=day
        image_url=page_cover_url(document)
        if not image_url:
            continue
        try:
            image,small,dimensions=convert(fetch_bytes(image_url))
        except Exception:  # Placeholder, tiny or odd-shaped image: keep the typographic cover.
            stats['errors']+=1
            continue
        path=root/book['portada_local'].lstrip('/')
        path.write_bytes(image)
        path.with_name(path.name.replace('.webp','-320.webp')).write_bytes(small)
        book.update(portada_fuente_url=image_url,portada_ancho=dimensions[0],portada_alto=dimensions[1],
                    portada_fecha_revision=day,portada_sustituida=True)
        stats['covers_replaced']+=1
    return stats


def page_title(document):
    m=re.search(r'id="productTitle"[^>]*>(.*?)<',document,re.S)
    return html.unescape(' '.join(m.group(1).split())) if m else ''


def cover_kind(book):
    if book.get('portada_sustituida'):
        return 'amazon'
    return 'generada' if urlsplit(book.get('portada_fuente_url') or '').hostname in COVER_HOSTS else 'editorial'


def audit_asin(book):
    """Ficha que se audita: un ASIN ya verificado del libro (mejor el impreso) o, sin ninguno, el ISBN-10 de su ISBN."""
    formats=verified_formats(book)
    return next((a for a,f in formats.items() if f!='ebook'),None) or next(iter(formats),None) or isbn10(book.get('isbn13'))


def audit_book(book,fetch,day):
    """Registro de un libro: formatos que vende Amazon (con su ASIN) frente a los que mostramos, y su portada.
    None si Amazon pide captcha: eso no dice nada del libro y se reintenta después."""
    asin=audit_asin(book)
    shown=[f for f in FORMAT_ORDER if f in {o['formato'] for o in book.get('formatos_compra',[])}]
    record={'fecha':day,'asin':asin,'amazon':{},'mostrados':shown,'faltan':[],'sin_confirmar':[],'portada':cover_kind(book)}
    if not asin:
        return {**record,'estado':'sin_asin'}
    try:
        document=fetch(f'https://www.amazon.es/dp/{asin}')
    except HTTPError as exc:
        return {**record,'estado':'sin_ficha' if exc.code==404 else f'http_{exc.code}'}
    except (OSError,ValueError):
        return {**record,'estado':'error'}
    if ('captcha' in document.lower() or 'bm-verify' in document) and 'tmm-grid-swatch' not in document and 'landingImage' not in document:
        return None
    if not verified_formats(book) and not title_matches(re.sub(r'\s*[\(\[].*?[\)\]]','',page_title(document)),book.get('titulo','')):
        # El ISBN-10 no siempre lleva a la misma obra: sin título coincidente no se añade nada.
        return {**record,'estado':'otra_obra','titulo_amazon':page_title(document)}
    amazon=swatch_formats(document,asin)
    if not amazon and book.get('formato_edicion') in FORMAT_ORDER:
        amazon={book['formato_edicion']:asin}  # ficha de un solo formato, sin selector
    record['amazon']={f:amazon[f] for f in FORMAT_ORDER if f in amazon}
    record['faltan']=[f for f in record['amazon'] if f not in shown]
    record['sin_confirmar']=[f for f in shown if f not in record['amazon']]
    return {**record,'estado':'ok','portada_amazon':page_cover_url(document)}


def apply_audit(book,record,tag):
    """Añade al libro los formatos que Amazon vende y no mostramos; el barrido de la API les pone precio."""
    if record.get('estado')!='ok':
        return 0
    options=book.setdefault('formatos_compra',[])
    have={o['formato'] for o in options}
    known=set(verified_formats(book))
    added=0
    for fmt,found in record['amazon'].items():
        if fmt in have or found in known:
            continue
        options.append({'formato':fmt,'url':f'https://www.amazon.es/dp/{found}?tag={tag}',
                        'fuente_url':f'https://www.amazon.es/dp/{found}','fecha_verificacion':record['fecha']})
        added+=1
    options.sort(key=lambda o:FORMAT_ORDER.index(o['formato']))
    book['formatos_pagina_buscados']=record['fecha']
    return added


def fetch_amazon_image(url):
    request=Request(url,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'})
    if urlsplit(url).hostname!='m.media-amazon.com':
        raise ValueError('Imagen fuera del CDN de Amazon')
    with urlopen(request,timeout=30) as response:
        return response.read(10_000_000)


def fetch_amazon_page(url):
    # Without gzip, or with an Accept-Language header, Amazon answers a short bot-check page.
    request=Request(url,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36',
                                 'Accept-Encoding':'gzip','Accept':'*/*'})
    time.sleep(2)
    with urlopen(request,timeout=30) as response:
        body=response.read(8_000_000)
        if response.headers.get('Content-Encoding')=='gzip':
            body=gzip.decompress(body)
    return body.decode('utf-8','replace')


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
    share=max(unpriced,-(-len(books)//max(1,sweep_days)))
    due=books[:share]
    if hasattr(provider,'discover'):
        # A missing Kindle or audiobook is looked for the first night, not when the price turn comes.
        due+=[b for b in books[share:] if needs_discovery(b,now)]
    stats={'attempted':0,'updated':0,'prices':0,'requests':0,'formats_added':0,'failures':[],'sin_oferta':[],'errores_amazon':{}}
    answers={}

    def ask(call,*args):
        if stats['requests']>=budget:
            raise DailyLimitReached
        stats['requests']+=1
        payload=call(*args)
        if payload.get('errors') and not any(payload.get(key) for key in ['searchResult','itemsResult','itemResults']):
            # HTTP 200 with only errors (NoResults, an ISBN Amazon does not list) is
            # this book's miss, not an outage: count the code and keep sweeping.
            for error in amazon_list(payload.get('errors')):
                code=str(amazon_dict(error).get('code') or 'desconocido')[:60]
                stats['errores_amazon'][code]=stats['errores_amazon'].get(code,0)+1
            return {}
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
        except DailyLimitReached:
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
