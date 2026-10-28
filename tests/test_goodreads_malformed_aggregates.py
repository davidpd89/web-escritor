import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reading_goodreads import select_goodreads_rating

BOOK={'id':'lib-0001','isbn13':'9788498382372','titulo':'Coraline','autores':['Neil Gaiman']}
ITEM={'@type':'Book','isbn':'9788498382372','name':'Coraline','author':[{'name':'Neil Gaiman'}],'aggregateRating':{'ratingValue':'4.13','ratingCount':'809434'}}
URL='https://www.goodreads.com/book/show/6785288-coraline'

class AggregateBoundaries(unittest.TestCase):
    def test_invalid_aggregate_shapes_are_rejected(self):
        for aggregate in ([], '4.5', 12, True, {'ratingValue':4.5,'ratingCount':{}}, {'ratingValue':{},'ratingCount':100}):
            with self.subTest(aggregate=aggregate):
                item=copy.deepcopy(ITEM)
                item['aggregateRating']=aggregate
                self.assertIsNone(select_goodreads_rating(BOOK,{'books':[item],'url':URL}))
    def test_bad_item_cannot_hide_later_verified_edition(self):
        malformed=copy.deepcopy(ITEM)
        malformed['aggregateRating']=[]
        rated=select_goodreads_rating(BOOK,{'books':[malformed,copy.deepcopy(ITEM)],'url':URL})
        self.assertIsNotNone(rated)
        self.assertEqual(rated['numero_valoraciones'],809434)

if __name__=='__main__': unittest.main()
