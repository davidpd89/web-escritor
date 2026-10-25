import sys
import unittest
from datetime import datetime,timezone
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reading_ratings_refresh import refresh

NOW=datetime(2026,10,21,tzinfo=timezone.utc)
LIVE={'id':'live','titulo':'Coraline','autores':['Neil Gaiman'],'isbn13':'9788498382372','estado':'publicado'}
REMOVED={'id':'removed','titulo':'Obra retirada','autores':['Autor'],'isbn13':'9788425374012','estado':'borrador'}

def rating(identifier):
    return {'libro_id':identifier,'fuente':'goodreads','puntuacion':4.2,'numero_valoraciones':10,'url':'https://www.goodreads.com/book/show/123','actualizado_en':'2026-10-20T00:00:00Z'}

class RatingLifecycle(unittest.TestCase):
    def test_retired_books_do_not_remain_in_public_market(self):
        calls=[]
        def missing(isbn):
            calls.append(isbn)
            raise RuntimeError('provider offline')
        original={'ratings':[rating('live'),rating('removed'),rating('deleted')],'offers':[]}
        result,stats=refresh({'libros':[LIVE,REMOVED]},original,missing,now=NOW,budget=100,source='goodreads')
        ids={r['libro_id'] for r in result['ratings'] if r.get('fuente')=='goodreads'}
        self.assertEqual(ids,{'live'})
        self.assertEqual(calls,[LIVE['isbn13']])
        self.assertEqual(stats['updated'],0)
        self.assertEqual(next(r for r in result['ratings'] if r['libro_id']=='live')['actualizado_en'],'2026-10-20T00:00:00Z')

if __name__=='__main__': unittest.main()
