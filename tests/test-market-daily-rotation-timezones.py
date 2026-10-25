import sys
import unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import reading_amazon_market as amazon
import reading_ratings_refresh as ratings

ISBNS = ['9788498382372','9788425371967','9788425374012']
BOOKS = [{'id':str(i),'titulo':'Libro '+str(i),'autores':['Autor'],
          'isbn13':isbn,'estado':'publicado'} for i,isbn in enumerate(ISBNS)]
CATALOG = {'libros':BOOKS}
MARKET = {'schema_version':1,'offers':[],'ratings':[]}

class RotationInvariance(unittest.TestCase):
    def selected_ratings(self, now):
        calls=[]
        ratings.refresh(CATALOG,MARKET,
            lambda isbn:(calls.append(isbn) or {'items':[]}),
            now=now,budget=1,source='google_books')
        return calls

    def selected_amazon(self, now):
        calls=[]
        def provider(book):
            calls.append(book['id'])
            return {'searchResult':{'items':[]}}
        amazon.refresh_offers(CATALOG,MARKET,provider,'contrato-21',now,budget=1)
        return calls

    def test_provider_selection_is_instant_based(self):
        utc = datetime(2026,7,1,23,30,tzinfo=timezone.utc)
        equivalents = [utc,utc.astimezone(timezone(timedelta(hours=2))),
                       utc.astimezone(timezone(timedelta(hours=-7)))]
        for selector in (self.selected_ratings,self.selected_amazon):
            baseline = selector(utc)
            self.assertEqual(len(baseline),1)
            for instant in equivalents:
                with self.subTest(provider=selector.__name__,zone=str(instant.tzinfo)):
                    self.assertEqual(selector(instant),baseline)

if __name__ == '__main__':
    unittest.main()
