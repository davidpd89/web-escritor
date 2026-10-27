import copy
import sys
import unittest
from datetime import datetime,timezone
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reading_amazon_market import select_offers

NOW=datetime(2026,10,21,tzinfo=timezone.utc)
BOOK={'id':'lib-test','titulo':'Coraline','autores':['Neil Gaiman'],'isbn13':'9788498382372','estado':'publicado','formato_edicion':'tapa-blanda'}
ITEM={'asin':'8498382378','itemInfo':{'title':{'displayValue':'Coraline'},'byLineInfo':{'contributors':[{'name':'Neil Gaiman','role':'Author'}]},'externalIds':{'eans':{'displayValues':['9788498382372']}},'classifications':{'binding':{'displayValue':'Paperback'}}},'offersV2':{'listings':[{'condition':{'value':'New'},'availability':{'type':'IN_STOCK'},'price':{'money':{'amount':11.35,'currency':'EUR'}}}]}}

class MalformedCreatorsResults(unittest.TestCase):
    def test_bad_items_do_not_suppress_valid_item(self):
        payload={'searchResult':{'items':[None,[],copy.deepcopy(ITEM)]}}
        result=select_offers(BOOK,payload,'davidporto-21',NOW)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['precio_centimos'],1135)
    def test_bad_listing_does_not_suppress_valid_listing(self):
        item=copy.deepcopy(ITEM)
        item['offersV2']['listings']=[None,'broken',{},item['offersV2']['listings'][0]]
        result=select_offers(BOOK,{'searchResult':{'items':[item]}},'davidporto-21',NOW)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['precio_centimos'],1135)
    def test_empty_response_does_not_invent_offers(self):
        self.assertEqual(select_offers(BOOK,{},'davidporto-21',NOW),[])

if __name__=='__main__': unittest.main()
