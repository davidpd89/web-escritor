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
           'offersV2.listings.dealDetails','offersV2.listings.type','browseNodeInfo.websiteSalesRank',
           # La cubierta viene en la misma respuesta: sin ella, 1398 libros seguían con la tipográfica (08/11).
           'images.primary.large']
PRINT_FORMATS={'tapa-blanda','tapa-dura'}
SALES_RANK_SOURCE='amazon_es_books'
# Contrato con assets/reading-catalogue.js (validRank, 216 h): un puesto nunca vive más de 8 días.
SALES_RANK_MAX_DAYS=8
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


def foreign_edition(book,fmt,asin):
    """A paper ASIN in the book's own binding that is another ISBN-10 is another edition
    (bolsillo vs. rústica, otra editorial): its price is not this edition's price."""
    own=isbn10(isbn13(book.get('isbn13')) or '')
    return (fmt in ('tapa-blanda','tapa-dura') and fmt==book.get('formato_edicion') and bool(own)
            and isinstance(asin,str) and bool(re.fullmatch(r'\d{9}[\dX]',asin)) and asin!=own)


BINDING_LABELS={'tapa-dura':'Tapa dura','tapa-blanda':'Tapa blanda'}


def reconcile_edition_binding(book):
    """Amazon's binding for the edition's own ISBN-10 overrides the publisher's when they differ.

    Some publisher pages declare one bookFormat for every title (Anagrama's JSON-LD says
    Paperback even for hardcovers, «Tres cuentos» 2026-11), so the card offered «tapa blanda»
    beside Amazon's «tapa dura» for the very same EAN. Returns True when it corrected the book."""
    own=isbn10(isbn13(book.get('isbn13')) or '')
    found={o.get('formato') for o in book.get('formatos_compra') or []
           if own and asin_from_url(o.get('url'))==own and o.get('formato') in BINDING_LABELS}
    current=book.get('formato_edicion')
    if len(found)!=1 or current not in BINDING_LABELS or current in found:
        return False
    fmt=found.pop()
    label,_,publisher=(book.get('edicion') or '').partition(' · ')
    book['formato_edicion']=fmt
    if publisher:
        book['edicion']=BINDING_LABELS[fmt]+' · '+publisher
    if label and isinstance(book.get('descripcion_breve'),str):
        book['descripcion_breve']=book['descripcion_breve'].replace(f'en {label.lower()}.',f'en {BINDING_LABELS[fmt].lower()}.')
    if book.get('encuadernacion'):
        book['encuadernacion']=BINDING_LABELS[fmt]
    return True


def prune_foreign_editions(book):
    """Drops stored offers of another edition in the book's own binding; returns how many."""
    options=book.get('formatos_compra') or []
    kept=[o for o in options if not foreign_edition(book,o.get('formato'),asin_from_url(o.get('url')))]
    if len(kept)!=len(options):
        book['formatos_compra']=kept
    return len(options)-len(kept)


def verified_formats(book):
    known={asin:fmt for o in book.get('formatos_compra',[])
           if not foreign_edition(book,(fmt:=o['formato']),(asin:=asin_from_url(o.get('url'))))}
    direct=asin_from_url(book.get('url_amazon_afiliada'))
    if direct and book.get('formato_edicion'):
        known.setdefault(direct,book['formato_edicion'])
    return {asin:fmt for asin,fmt in known.items() if asin}


def same_title(title,canonical):
    # Without an ISBN a prefix match is not enough ("Dune" vs "Dune Mesías"):
    # only subtitles in brackets or after a colon may differ.
    bare=lambda t: key(re.sub(r'\s*[\(\[].*?[\)\]]','',t).split(':')[0])
    return bool(bare(canonical)) and bare(title)==bare(canonical)


# Con el EAN exacto la edición ya está identificada; título y autor solo descartan un EAN mal
# asignado. Por eso se toleran el orden de serie («El despertar de la magia (Indomables 1)»),
# el sufijo de idioma y un nombre más largo («Diego Arboleda Rodríguez»), pero no otro libro
# ni otra persona.
_TITLE_NOISE={'spanish','edition','edicion','espanol','espanola','castellano','version'}


def _title_words(value):
    return {w for w in key(value).split() if w not in _TITLE_NOISE}


def isbn_title_matches(title,canonical):
    a,b=_title_words(title),_title_words(canonical)
    short,long_=sorted((a,b),key=len)
    return len(short)>=2 and short<=long_


# Palabras que distinguen una edición de otra del mismo libro: la ficha de una edición especial agrupa en sus
# formatos los de la normal («Neuromante (Edición especial)» frente a «Neuromante (NE)»), y su precio no es este.
EDITION_MARKS={'especial','limitada','ilustrada','coleccionista','aniversario','lujo','bolsillo','conmemorativa'}


def same_work(title,canonical):
    """Título de un ASIN ya verificado para el libro escrito de otra manera: mismas palabras en otro orden o con la
    serie entre paréntesis («Montando un pollo: Diario de Greg 21» = «Diario de Greg 21 - Montando un pollo»). No vale
    otra edición (marcas de edición distintas) ni otro tomo (números distintos)."""
    if _title_words(title)&EDITION_MARKS!=_title_words(canonical)&EDITION_MARKS:
        return False
    numbers=lambda t:set(re.findall(r'\d+',t))
    if numbers(title) and numbers(canonical) and not numbers(title)&numbers(canonical):
        return False
    bare=lambda t:_title_words(re.sub(r'[\(\[][^\)\]]*[\)\]]',' ',t))-EDITION_MARKS
    short,long_=sorted((bare(title),bare(canonical)),key=len)
    return len(short)>=2 and short<=long_


def isbn_author_matches(source,catalogued):
    a,b=key(source).split(),key(catalogued).split()
    if len(a)<2 or len(b)<2:
        return False
    short,long_=sorted((a,b),key=len)
    return set(short)<=set(long_)


def edition_matches(info,book,isbn_match):
    """Título y autor de un resultado de Amazon frente al libro: estricto sin ISBN,
    tolerante con el EAN exacto. Lo comparten select_offers y miss_reason."""
    title=amazon_dict(info.get('title')).get('displayValue','')
    if not isinstance(title,str):
        return False,False
    title_ok=title_matches(title,book['titulo']) or (isbn_match and isbn_title_matches(title,book['titulo']))
    contributors=[c for c in amazon_list(amazon_dict(info.get('byLineInfo')).get('contributors'))
                  if isinstance(c,dict) and isinstance(c.get('name'),str)]
    # Sin ISBN solo cuentan los autores; con el EAN exacto vale cualquier rol (ilustrador,
    # editor) para no perder ediciones en las que Amazon reparte los créditos de otro modo.
    authors=[c['name'] for c in contributors if isinstance(c.get('role'),str) and key(c['role']) in {'author','autor'}]
    author_ok=any(author_matches(a,n) for a in authors for n in book['autores'])
    if isbn_match and not author_ok:
        author_ok=any(author_matches(c['name'],n) or isbn_author_matches(c['name'],n)
                      for c in contributors for n in book['autores'])
    if isbn_match and not author_ok:
        # «Varios autores» frente a «AA. VV.»: la misma obra colectiva, no otra persona (08/11: 6 novedades sin precio).
        # Si nosotros solo tenemos un autor colectivo no hay persona que comprobar: basta el EAN con el título (Amazon
        # acredita a veces a la editorial, «¡Ya es Navidad!»). Un «AA. VV.» de Amazon no vale por una persona nuestra.
        ours=[n for n in book['autores'] if n]
        author_ok=bool(ours) and all(collective(n) for n in ours) and title_ok
    return title_ok,author_ok


def collective(name):
    return re.sub(r'[^a-z]','',key(name)) in {'variosautores','autoresvarios','aavv','vvaa','varios'}


def item_isbn_match(info,wanted):
    eans=amazon_list(amazon_dict(amazon_dict(info.get('externalIds')).get('eans')).get('displayValues'))
    return bool(wanted) and wanted in {isbn13(v) for v in eans if isinstance(v,str)}


def in_spanish(info):
    languages=amazon_list(amazon_dict(amazon_dict(info.get('contentInfo')).get('languages')).get('displayValues'))
    return any(isinstance(l,dict) and isinstance(l.get('displayValue'),str)
               and key(l['displayValue']) in {'espanol','spanish','castellano'} for l in languages)


def amazon_dict(value):
    return value if isinstance(value,dict) else {}


def amazon_list(value):
    return value if isinstance(value,list) else []


def select_offers(book,payload,tag,now,mismatches=None):
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
        isbn_match=item_isbn_match(info,wanted)
        title_ok,author_ok=edition_matches(info,book,isbn_match)
        if asin in known and not (title_ok and author_ok) and isinstance(title,str):
            # ASIN ya guardado para este libro: basta el mismo título en otro orden (sin cambiar edición ni tomo), y
            # con su EAN exacto y el título bien no hace falta que Amazon escriba el autor igual. Sin esto, 31 de 39
            # formatos quedaban en «Ver precio» con precio en la API (08/11).
            title_ok=title_ok or same_work(title,book['titulo'])
            author_ok=author_ok or (isbn_match and title_ok)
        if not (title_ok and author_ok):
            continue
        binding_value=amazon_dict(amazon_dict(info.get('classifications')).get('binding')).get('displayValue','')
        binding=key(binding_value) if isinstance(binding_value,str) else ''
        # Con el EAN exacto el ASIN es esta edición: si Amazon la encuaderna con un nombre que no traducimos («Libro
        # de cartón», «Libro de tela», «Estuche»), su formato es el de la edición (08/11: 9 novedades sin precio).
        fmt=known.get(asin) or BINDINGS.get(binding) or (isbn_match and book.get('formato_edicion')) or None
        if fmt and foreign_edition(book,fmt,asin) and not isbn_match:
            continue  # Otra edición en la misma encuadernación: su precio no es el de esta.
        if asin in known and BINDINGS.get(binding,fmt)!=fmt:
            # Amazon manda sobre el formato de su ASIN: un precio de tapa dura no se publica como tapa blanda.
            if mismatches is not None:
                mismatches.append({'libro_id':book['id'],'asin':asin,'guardado':fmt,'amazon':BINDINGS[binding]})
            continue
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
            # Creators devuelve IN_STOCK_SCARCE («solo quedan 2»); PA-API lo escribía sin guiones bajos. AVAILABLE_DATE
            # es la preventa con fecha de llegada: la mitad de las novedades sin precio del 08/11.
            if not isinstance(availability,str) or availability.replace('_','') not in {'INSTOCK','INSTOCKSCARCE','LEADTIME','PREORDER','AVAILABLEDATE'}:
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


class NotFound(RuntimeError):
    """404 de Creators: la búsqueda no tiene resultados (no es una caída)."""


# Reintentos tomados de sergioteula/python-amazon-paapi (MIT, amazon_creatorsapi/core/retry.py):
# 429 y 5xx con espera exponencial o la que pida Retry-After; un 401 renueva el token una vez.
RETRY_STATUS = frozenset({429, 500, 502, 503, 504})
TOKEN_URL = 'https://api.amazon.co.uk/auth/o2/token'


class CreatorsPrices:
    def __init__(self,client_id,secret,tag):
        self.client_id,self.secret,self.tag=client_id,secret,tag
        self.token=None
        self.expires=0.0
        self.last=0

    def post(self,url,payload,headers=None,retries=3):
        attempt,refreshed=0,False
        while True:
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
                except (ValueError,AttributeError,TypeError):
                    error={}
                if not isinstance(error,dict):
                    error={}
                if exc.code==401 and headers and 'Authorization' in headers and not refreshed:
                    # Token caducado a mitad de un recorrido largo: uno nuevo y se repite la petición.
                    refreshed=True
                    self.token=None
                    headers={**headers,**self.headers()}
                    continue
                if exc.code in RETRY_STATUS and attempt<retries:
                    wait=error.get('retryAfterSeconds') or (exc.headers or {}).get('Retry-After')
                    try:
                        wait=min(60.0,max(1.0,float(wait)))
                    except (TypeError,ValueError):
                        wait=min(30.0,2.0*2**attempt)
                    attempt+=1
                    time.sleep(wait)
                    continue
                if exc.code==403 and ('eligib' in str(error.get('message','')).lower() or any(e.get('code')=='AssociateNotEligible' for e in error.get('errors',[]) if isinstance(e,dict))):
                    raise RuntimeError('pending_amazon_eligibility') from exc
                if exc.code==404:
                    raise NotFound('Amazon Creators HTTP 404') from exc
                raise RuntimeError(f'Amazon Creators HTTP {exc.code}') from exc
            except (URLError,TimeoutError,ConnectionError) as exc:
                if attempt<retries:
                    attempt+=1
                    time.sleep(min(30.0,2.0*2**attempt))
                    continue
                raise RuntimeError('Amazon Creators unavailable') from exc
            if not isinstance(result,dict):
                raise RuntimeError('Invalid Amazon Creators response')
            return result

    def headers(self):
        # El token dura ~1 h: se renueva 30 s antes de caducar, como hace python-amazon-paapi.
        if not self.token or time.time()>=self.expires:
            data=self.post(TOKEN_URL,{
                'grant_type':'client_credentials','client_id':self.client_id,
                'client_secret':self.secret,'scope':'creatorsapi::default'})
            self.token=data['access_token']
            try:
                life=float(data.get('expires_in') or 3600)
            except (TypeError,ValueError):
                life=3600.0
            self.expires=time.time()+max(60.0,life-30)
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
    reconcile_edition_binding(book)
    prune_foreign_editions(book)
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
    reconcile_edition_binding(book)  # The own ASIN may have just been priced for the first time.
    return added


def print_prices(book):
    """PVP y precios en papel: Amazon da el de la versión impresa como savingBasis de los ebooks."""
    out={book.get('pvp_centimos')}
    for o in book.get('formatos_compra',[]):
        if o.get('formato') not in ('ebook','audiolibro'):
            out|={o.get('precio_centimos'),o.get('precio_referencia_centimos')}
    return out-{None}


def price_drop(current,offer,day):
    """Keep only Amazon's list price (savingBasis): a drop against our own earlier price is not shown as an offer."""
    price=offer['precio_centimos']
    reference=offer.get('precio_referencia_centimos')
    if reference and reference>price:
        current['precio_referencia_centimos']=reference
    else:
        current.pop('precio_referencia_centimos',None)
    current.pop('precio_anterior_centimos',None); current.pop('bajada_fecha',None)  # legacy fields


FORMAT_ORDER=('tapa-blanda','tapa-dura','ebook','audiolibro')
# Kindle/audiobook editions often appear months after the print one: look again
# after this long, so books without a digital edition do not spend quota nightly.
REDISCOVER_AFTER=timedelta(days=90)
# A book with nothing to buy yet is looked for by title weekly; its printed edition
# is still asked for every night by ISBN-10 in the shared getItems batches.
UNLISTED_REDISCOVER_AFTER=timedelta(days=7)
# Books priced together: their ASINs fill getItems batches of ten across books.
PRICE_GROUP=50


def discovery_index(book):
    return 'All' if 'ebook' in {o['formato'] for o in book.get('formatos_compra',[])} else 'KindleStore'


def needs_discovery(book,now):
    formats={o['formato'] for o in book.get('formatos_compra',[])}
    if {'ebook','audiolibro'}<=formats:
        return False
    searched=book.get('formatos_amazon_buscados')
    wait=REDISCOVER_AFTER if formats else UNLISTED_REDISCOVER_AFTER
    return not searched or now.date()-date.fromisoformat(searched)>=wait


RELEASE_WATCH_DAYS=3


def releases_soon(book,now):
    """Out today (the run starts before midnight UTC) or in the next few days."""
    try:
        published=date.fromisoformat(str(book.get('fecha_publicacion') or ''))
    except ValueError:
        return False
    return now.date()<=published<=now.date()+timedelta(days=RELEASE_WATCH_DAYS)


def price_asins(book,batched=True):
    """ASINs that price this book: the verified ones or, for a 978 book still without
    one, its ISBN-10 (the ASIN of the printed edition; the ISBN check in select_offers
    rejects anything else). {asin: formato or None}."""
    known=verified_formats(book)
    if known or not batched:
        return known
    alt=isbn10(isbn13(book.get('isbn13')) or '')
    return {alt:None} if alt else {}


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
            if fmt in have or found in known or foreign_edition(book,fmt,found):
                continue
            options.append({'formato':fmt,'url':f'https://www.amazon.es/dp/{found}?tag={tag}',
                            'fuente_url':f'https://www.amazon.es/dp/{found}','fecha_verificacion':day})
            stats['formats_added']+=1
        options.sort(key=lambda o:FORMAT_ORDER.index(o['formato']))
    return stats


COVER_HOSTS=('www.todostuslibros.com',)
GENERATED_BASIS='Portada tipográfica propia'
AMAZON_COVER_BASIS='Cubierta de la edición tomada de su ficha de Amazon.es para su identificación bibliográfica'


def generated_cover(book):
    """Portada tipográfica nuestra aún sin sustituir: la de todostuslibros y la de la ingesta de Amazon, que no trae
    imagen y la guarda con la URL de la ficha (www.amazon.es/dp/…). Mirar solo el host dejaba fuera estas últimas:
    el 08/11 eran 1398 libros con portada predefinida que nunca se cambiaban por la real."""
    if book.get('portada_sustituida'):
        return False
    return urlsplit(book.get('portada_fuente_url') or '').hostname in COVER_HOSTS or         (book.get('autorizacion_o_base_uso') or '').startswith(GENERATED_BASIS)


def cover_taken(root,path,image):
    """¿Otra portada del catálogo ya tiene exactamente estos bytes? Amazon da a veces la misma imagen de serie a
    varios tomos (ingesta 42588397174: «La luna en una noche de lluvia» 1 y 9); publicarla dos veces rompe la
    validación «portada duplicada». Solo se comparan los ficheros del mismo tamaño."""
    folder=path.parent
    if not folder.is_dir():
        return False
    for other in folder.iterdir():
        if other!=path and not other.name.endswith('-320.webp') and other.is_file() and other.stat().st_size==len(image) and other.read_bytes()==image:
            return True
    return False


def replace_cover(book,root,image,small,dimensions,source,day,basis=AMAZON_COVER_BASIS):
    """Pone la cubierta real en lugar de la tipográfica: ficheros, medidas, fuente y base de uso.
    Devuelve False sin tocar nada si esa imagen ya es la portada de otro libro."""
    path=root/book['portada_local'].lstrip('/')
    if cover_taken(root,path,image):
        book['portadas_amazon_buscadas']=day
        return False
    path.write_bytes(image)
    path.with_name(path.name.replace('.webp','-320.webp')).write_bytes(small)
    book.update(portada_fuente_url=source,portada_ancho=dimensions[0],portada_alto=dimensions[1],portada_fecha_revision=day,
                portada_sustituida=True,autorizacion_o_base_uso=basis,portadas_amazon_buscadas=day)
    return True


API_COVER=re.compile(r'https://m\.media-amazon\.com/images/I/([A-Za-z0-9+%-]+)(?:\.[^/?#]*?)?\.(jpg|png)')


def api_cover_url(item):
    """Cubierta a tamaño completo de un resultado de la Creators API (images.primary.large), sin el sufijo
    de tamaño (._SL500_): la misma imagen que page_cover_url saca de la ficha, sin pasar por la página."""
    large=amazon_dict(amazon_dict(amazon_dict(amazon_dict(item).get('images')).get('primary')).get('large'))
    found=API_COVER.fullmatch(large.get('url')) if isinstance(large.get('url'),str) else None
    return f'https://m.media-amazon.com/images/I/{found.group(1)}.{found.group(2)}' if found else None


def item_cover_url(book,payload):
    """Cubierta de la API para este libro: la de su edición impresa; la Kindle solo si no hay impresa."""
    payload=amazon_dict(payload)
    container=next((value for field in ('searchResult','itemsResult','itemResults')
                    if isinstance((value:=payload.get(field)),dict)),{})
    wanted=isbn13(book.get('isbn13'))
    known=verified_formats(book)
    best=None
    for item in amazon_list(container.get('items')):
        item=amazon_dict(item)
        info=amazon_dict(item.get('itemInfo'))
        if not (item.get('asin','') in known or (wanted and item_isbn_match(info,wanted))):
            continue
        url=api_cover_url(item)
        if not url:
            continue
        binding=amazon_dict(amazon_dict(info.get('classifications')).get('binding')).get('displayValue','')
        fmt=known.get(item.get('asin','')) or BINDINGS.get(key(binding) if isinstance(binding,str) else '')
        if fmt in PRINT_FORMATS:
            return url
        best=best or url
    return best


def swap_cover(book,root,url,fetch_bytes,convert,day):
    """Cambia la tipográfica por la cubierta descargada; si la imagen no vale (marcador, pequeña, rara), no toca nada."""
    try:
        image,small,dimensions=convert(fetch_bytes(url))
    except Exception:  # noqa: BLE001 - la tipográfica se queda; el monitor la sigue contando
        return False
    return replace_cover(book,root,image,small,dimensions,url,day)


COVER_FALLBACK_BASIS='Cubierta de la edición localizada por su ISBN en {fuente} para su identificación bibliográfica'
COVER_IMAGE_HOSTS={'m.media-amazon.com','covers.openlibrary.org','books.google.com','books.googleusercontent.com'}


def fallback_cover_urls(book,fetch_json):
    """Otras fuentes por ISBN cuando Amazon no tiene imagen (su marcador es un GIF de 60x49):
    Open Library (devuelve 404 si no la tiene) y Google Books (solo el volumen con ese mismo ISBN)."""
    isbn=isbn13(book.get('isbn13'))
    if not isbn:
        return []
    found=[('Open Library',f'https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false')]
    try:
        data=fetch_json(f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}')
    except Exception:  # noqa: BLE001 - cuota o red: esa fuente se salta hoy y se repite mañana
        data={}
    for item in amazon_list(amazon_dict(data).get('items')):
        info=amazon_dict(amazon_dict(item).get('volumeInfo'))
        ids={amazon_dict(x).get('identifier') for x in amazon_list(info.get('industryIdentifiers'))}
        thumb=amazon_dict(info.get('imageLinks')).get('thumbnail')
        if isbn in ids and isinstance(thumb,str) and urlsplit(thumb).hostname in COVER_IMAGE_HOSTS:
            thumb=thumb.replace('http://','https://').replace('&edge=curl','')
            found.append(('Google Books',thumb+'&fife=w800'))
            break
    return found


def recheck_generated_covers(catalogue,root,provider,fetch_bytes,convert,now,fetch_json=None,limit=3000,max_requests=600):
    """Pasada propia de portadas, cada noche y aparte del barrido de precios (que solo veía los libros a los que
    tocaba precio ese día): todo libro con portada tipográfica se pregunta a la Creators API (diez ASIN por
    petición; por ISBN si no tiene ASIN) y, si Amazon no tiene imagen o no vale, a otras fuentes por ISBN.
    Los que siguen sin portada se vuelven a mirar la noche siguiente: una preventa recibe su cubierta días después."""
    day=now.astimezone(timezone.utc).date().isoformat()
    books=[b for b in catalogue['libros'] if generated_cover(b) and b.get('portada_local') and b.get('portadas_amazon_buscadas','')<day]
    books.sort(key=lambda b:b.get('portadas_amazon_buscadas',''))
    books=books[:limit]
    stats={'revisadas':0,'amazon':0,'otras_fuentes':0,'sin_imagen':0,'imagen_no_valida':0,'peticiones':0,'error':''}
    urls={}

    def ask(call,arg):
        if stats['peticiones']>=max_requests:
            raise DailyLimitReached
        stats['peticiones']+=1
        return amazon_dict(call(arg))

    try:
        with_asin=[b for b in books if verified_formats(b)]
        if hasattr(provider,'items'):
            pairs=[(b,a) for b in with_asin for a in verified_formats(b)]
            for i in range(0,len(pairs),10):
                chunk=pairs[i:i+10]
                payload=ask(provider.items,[a for _,a in chunk])
                for book in {b['id']:b for b,_ in chunk}.values():
                    if book['id'] not in urls and (url:=item_cover_url(book,payload)):
                        urls[book['id']]=url
        for book in books:
            if book['id'] not in urls and (not verified_formats(book) or not hasattr(provider,'items')) and isbn13(book.get('isbn13')):
                if url:=item_cover_url(book,ask(provider,book)):
                    urls[book['id']]=url
    except DailyLimitReached:
        stats['error']='cupo de la pasada agotado'
    except Exception as exc:  # noqa: BLE001 - Amazon caído: se usa lo ya leído y las otras fuentes
        stats['error']=f'{type(exc).__name__}: {str(exc)[:120]}'
    for book in books:
        stats['revisadas']+=1
        url=urls.get(book['id'])
        if url and swap_cover(book,root,url,fetch_bytes,convert,day):
            stats['amazon']+=1
            continue
        replaced=False
        for source,candidate in (fallback_cover_urls(book,fetch_json) if fetch_json else []):
            try:
                image,small,dimensions=convert(fetch_bytes(candidate))
            except Exception:  # noqa: BLE001 - 404, marcador o tamaño raro: siguiente fuente
                continue
            if replace_cover(book,root,image,small,dimensions,candidate,day,COVER_FALLBACK_BASIS.format(fuente=source)):
                stats['otras_fuentes']+=1
                replaced=True
                break
        if not replaced:
            stats['imagen_no_valida' if url else 'sin_imagen']+=1
            book['portadas_amazon_buscadas']=day
    return stats


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
    books=[b for b in catalogue['libros'] if generated_cover(b)
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
        if replace_cover(book,root,image,small,dimensions,image_url,day):
            stats['covers_replaced']+=1
    return stats


def page_title(document):
    m=re.search(r'id="productTitle"[^>]*>(.*?)<',document,re.S)
    return html.unescape(' '.join(m.group(1).split())) if m else ''


STAR_TEXT=re.compile(r'([1-5](?:[.,]\d)?)\s+de\s+5\s+estrellas',re.I)
REVIEW_COUNT=re.compile(r'\d{1,3}(?:[.\s\u00a0]\d{3})+|\d+')


def page_rating(document):
    """Nota media y número de valoraciones que muestra la ficha (`acrPopover` y `acrCustomerReviewText`).
    None si la ficha no las muestra: una novedad sin valoraciones no tiene nota, ni 0 ni vacía."""
    popover=re.search(r'<span[^>]*id="acrPopover"[^>]*>',document)
    stars=STAR_TEXT.search(html.unescape(popover.group(0))) if popover else None
    if not stars:
        block=re.search(r'id="averageCustomerReviews"(.{0,4000})',document,re.S)
        stars=STAR_TEXT.search(html.unescape(block.group(1))) if block else None
    count=re.search(r'<span[^>]*id="acrCustomerReviewText"([^>]*)>([^<]*)<',document)
    if not stars or not count:
        return None
    label=re.search(r'aria-label="([^"]*)"',count.group(1))
    number=REVIEW_COUNT.search(html.unescape(label.group(1) if label else count.group(2)))
    if not number:
        return None
    value,total=float(stars.group(1).replace(',','.')),int(re.sub(r'\D','',number.group(0)))
    return {'puntuacion':value,'numero_valoraciones':total} if 1<=value<=5 and total>0 else None


def cover_kind(book):
    if book.get('portada_sustituida'):
        return 'amazon'
    return 'generada' if generated_cover(book) else 'editorial'


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
    rating=page_rating(document)
    return {**record,'estado':'ok','portada_amazon':page_cover_url(document),**({'valoracion':rating} if rating else {})}


def apply_audit(book,record,tag):
    """Añade al libro los formatos que Amazon vende y no mostramos; el barrido de la API les pone precio."""
    if record.get('estado')!='ok':
        return 0
    options=book.setdefault('formatos_compra',[])
    have={o['formato'] for o in options}
    known=set(verified_formats(book))
    added=0
    for fmt,found in record['amazon'].items():
        if fmt in have or found in known or foreign_edition(book,fmt,found):
            continue
        options.append({'formato':fmt,'url':f'https://www.amazon.es/dp/{found}?tag={tag}',
                        'fuente_url':f'https://www.amazon.es/dp/{found}','fecha_verificacion':record['fecha']})
        added+=1
    options.sort(key=lambda o:FORMAT_ORDER.index(o['formato']))
    book['formatos_pagina_buscados']=record['fecha']
    return added


def fetch_amazon_image(url):
    request=Request(url,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'})
    if urlsplit(url).hostname not in COVER_IMAGE_HOSTS:
        raise ValueError('Imagen fuera de las fuentes de cubiertas')
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


def item_sales_rank(book,payload):
    """Mejor puesto en Libros de Amazon.es de la edición impresa de este libro, o None. Kindle y Audible
    tienen su propia lista y su número no se compara con el de papel."""
    payload=amazon_dict(payload)
    container=next((value for field in ('searchResult','itemsResult','itemResults')
                    if isinstance((value:=payload.get(field)),dict)),{})
    wanted=isbn13(book.get('isbn13'))
    known=verified_formats(book)
    best=None
    for item in amazon_list(container.get('items')):
        item=amazon_dict(item)
        info=amazon_dict(item.get('itemInfo'))
        binding=amazon_dict(amazon_dict(info.get('classifications')).get('binding')).get('displayValue','')
        fmt=known.get(item.get('asin','')) or BINDINGS.get(key(binding) if isinstance(binding,str) else '')
        if fmt not in PRINT_FORMATS or not (item.get('asin','') in known or (wanted and item_isbn_match(info,wanted))):
            continue
        rank=amazon_dict(amazon_dict(item.get('browseNodeInfo')).get('websiteSalesRank')).get('salesRank')
        if isinstance(rank,str) and rank.strip().isdigit():
            rank=int(rank)
        if isinstance(rank,int) and not isinstance(rank,bool) and 0<rank<10**8:
            best=rank if best is None else min(best,rank)
    return best


def valid_sales_rank(entry,now):
    """Puesto publicable: fuente conocida, entero positivo y vigente ahora."""
    if not isinstance(entry,dict) or entry.get('fuente')!=SALES_RANK_SOURCE or not isinstance(entry.get('libro_id'),str):
        return False
    rank=entry.get('posicion')
    if not isinstance(rank,int) or isinstance(rank,bool) or not 0<rank<10**8:
        return False
    try:
        start=datetime.fromisoformat(str(entry['actualizado_en']).replace('Z','+00:00'))
        end=datetime.fromisoformat(str(entry['caduca_en']).replace('Z','+00:00'))
    except (KeyError,ValueError):
        return False
    return start.tzinfo is not None and end.tzinfo is not None and start<=now<end


def merge_sales_ranks(market,ranks,catalogue_ids,now,ttl_days):
    """Puestos nuevos sobre los vigentes; los caducados o de libros fuera del catálogo desaparecen."""
    stamp=lambda d:d.isoformat(timespec='seconds').replace('+00:00','Z')
    kept={e['libro_id']:e for e in market.get('sales_ranks',[]) if valid_sales_rank(e,now) and e['libro_id'] in catalogue_ids}
    for book_id,rank in ranks.items():
        kept[book_id]={'libro_id':book_id,'posicion':rank,'fuente':SALES_RANK_SOURCE,
                       'actualizado_en':stamp(now),'caduca_en':stamp(now+timedelta(days=ttl_days))}
    entries=sorted(kept.values(),key=lambda e:(e['posicion'],e['libro_id']))
    if entries or 'sales_ranks' in market:
        market['sales_ranks']=entries
    return market


def refresh_offers(catalogue,market,provider,tag,now,budget=AMAZON_DAILY_LIMIT,sweep_days=7,cover=None):
    """Nightly sweep: books never priced plus the ones checked longest ago, so the
    whole catalogue comes round every sweep_days. ASINs are priced ten per request
    across PRICE_GROUP books (a 978 book without ASIN goes by its ISBN-10); books
    without ASIN are searched by ISBN on 979 or on their format-search nights. Prices go into the books;
    market only keeps the Amazon.es sales rank of the printed editions seen, for sweep_days+1 days.
    `cover(book,url)` swaps a still typographic cover for the one the same answer brings (images.primary.large)."""
    if not 0<=budget<=AMAZON_DAILY_LIMIT:
        raise ValueError('Price refresh budget outside the Amazon daily limit')
    now=now.astimezone(timezone.utc)
    day=now.date().isoformat()
    books=[b for b in catalogue['libros'] if b.get('estado')=='publicado' and isbn13(b.get('isbn13'))]
    books.sort(key=lambda b:b.get('precios_amazon_revision',''))
    unpriced=sum(not b.get('precios_amazon_revision') for b in books)
    share=max(unpriced,-(-len(books)//max(1,sweep_days)))
    # Un lote encadenado la misma noche no repite lo que otro ya revisó hoy.
    due=[b for b in books[:share] if b.get('precios_amazon_revision')!=day]
    # A book coming out these days is re-read every night, not on its weekly turn:
    # its release-day announcement only links an Amazon product checked in the last two days.
    due+=[b for b in books[share:] if b.get('precios_amazon_revision')!=day and releases_soon(b,now)]
    if hasattr(provider,'discover'):
        # A missing Kindle or audiobook is looked for the first night, not when the price turn comes.
        taken={b['id'] for b in due}
        due+=[b for b in books[share:] if b['id'] not in taken and needs_discovery(b,now)]
    stats={'attempted':0,'updated':0,'prices':0,'requests':0,'formats_added':0,'failures':[],'sin_oferta':[],'errores_amazon':{},'formato_discrepante':[],'portadas_api':0}
    answers={}
    covers={}
    ranks={}

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
        if book['id'] not in covers and (url:=item_cover_url(book,payload)):
            covers[book['id']]=url
        rank=item_sales_rank(book,payload)
        if rank and (book['id'] not in ranks or rank<ranks[book['id']]):
            ranks[book['id']]=rank
        for offer in select_offers(book,payload,tag,now,stats['formato_discrepante']):
            best=found.get(offer['formato'])
            if not best or best['precio_centimos']>offer['precio_centimos']:
                found[offer['formato']]=offer

    # A group fills its getItems batches of ten across books and is saved as soon
    # as it is complete, so a cut-off night still moves the sweep forward.
    batched=hasattr(provider,'items')
    for start in range(0,len(due),PRICE_GROUP):
        group=due[start:start+PRICE_GROUP]
        found={b['id']:{} for b in group}
        current,priced=group[0],False
        try:
            for current in group:
                if not verified_formats(current) and (not price_asins(current,batched) or needs_discovery(current,now)):
                    # No ASIN yet: the ISBN search finds the printed edition. A 978 book is also
                    # asked by its ISBN-10 every night; the search, on its format-search nights,
                    # finds the listing Amazon sells it under when that ASIN has no offer
                    # (9788491459866 sells as 8497174585). The ASIN found is kept for getItems.
                    keep(found[current['id']],current,ask(provider,current))
                if hasattr(provider,'discover') and needs_discovery(current,now):
                    # Kindle and audiobook editions have their own ASIN and no ISBN.
                    keep(found[current['id']],current,ask(provider.discover,current))
                    current['formatos_amazon_buscados']=day
            priced=True
            pending=[(b,asin) for b in group for asin,fmt in price_asins(b,batched).items()
                     if fmt not in found[b['id']] and (fmt or not found[b['id']])]
            if batched:
                asins=list(dict.fromkeys(asin for _,asin in pending))
                for i in range(0,len(asins),10):
                    batch=set(asins[i:i+10])
                    owners={b['id']:b for b,asin in pending if asin in batch}
                    current=next(iter(owners.values()))
                    payload=ask(provider.items,asins[i:i+10])
                    for book in owners.values():
                        keep(found[book['id']],book,only_items(payload,set(price_asins(book))))
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
            if cover and covers.get(book['id']) and generated_cover(book):
                stats['portadas_api']+=bool(cover(book,covers[book['id']]))
            if not book.get('formatos_compra'):
                stats['sin_oferta'].append({'book_id':book['id'],'motivo':miss_reason(book,answers.get(book['id'],[]))})
    # Solo cuentan los grupos guardados: el cortado a medias vuelve mañana entero.
    saved={b['id'] for b in books if b.get('precios_amazon_revision')==day}
    ranks={i:r for i,r in ranks.items() if i in saved}
    stats['puestos_ventas']=len(ranks)
    market=merge_sales_ranks(market,ranks,{b['id'] for b in books},now,min(sweep_days+1,SALES_RANK_MAX_DAYS))
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
            isbn_match=item_isbn_match(info,wanted)
            title_ok,author_ok=edition_matches(info,book,isbn_match)
            stage=1
            if title_ok:
                stage=2
                if author_ok:
                    stage=3
                    if isbn_match or in_spanish(info):
                        stage=4
            best=max(best,stage)
    return MISS_STAGES[best]
