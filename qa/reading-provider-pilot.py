"""Explicit read-only live pilot. Never writes books, pages or credentials."""
import json
import os
import sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from reading_ratings_refresh import refresh,google_response,hardcover_response,write_changed
from reading_goodreads import GoodreadsPublic
from reading_amazon_market import CreatorsPrices,refresh_offers

catalogue=json.loads((ROOT/'data/reading-catalogue.json').read_text(encoding='utf-8'))
market=json.loads((ROOT/'assets/reading-market.json').read_text(encoding='utf-8'))
now=datetime.now(timezone.utc)
reports={}
for source,token,provider in [
    ('goodreads','public',GoodreadsPublic()),
    ('google_books',os.getenv('GOOGLE_BOOKS_API_KEY'),lambda isbn:google_response(isbn,os.environ['GOOGLE_BOOKS_API_KEY'])),
    ('hardcover',os.getenv('HARDCOVER_API_KEY'),lambda isbn:hardcover_response(isbn,os.environ['HARDCOVER_API_KEY']))]:
    if not token:
        reports[source]={'status':'missing_credential'}
        continue
    market,stats=refresh(catalogue,market,provider,now=now,budget=100,source=source)
    reports[source]=stats
client=os.getenv('AMAZON_CREATORS_CLIENT_ID')
secret=os.getenv('AMAZON_CREATORS_CLIENT_SECRET')
if client and secret:
    provider=CreatorsPrices(client,secret,'davidporto-21')
    market,stats=refresh_offers(catalogue,market,provider,'davidporto-21',now,budget=1)
    reports['amazon']=stats
else:
    reports['amazon']={'status':'missing_credential'}
out=ROOT/'.ci/reading-intake'
write_changed(out/'provider-pilot-report.json',{'checked_at':now.isoformat(),'books':len(catalogue['libros']),'providers':reports})
write_changed(out/'provider-pilot-market.json',market)
print(json.dumps(reports,ensure_ascii=True),flush=True)
