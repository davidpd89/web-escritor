import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class Cards(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.book=None
        self.depth=0
        self.links=[]
        self.active=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='li' and 'catalogue-card' in a.get('class','').split():
            self.book=a.get('data-title')
            self.depth=1
        elif self.book is not None and tag=='li':
            self.depth+=1
        if tag=='a' and self.book and 'catalogue-card__buy' in a.get('class','').split():
            self.active={'book':self.book,'attrs':a,'text':''}
            self.links.append(self.active)
    def handle_data(self,data):
        if self.active is not None: self.active['text']+=data
    def handle_endtag(self,tag):
        if tag=='a': self.active=None
        if tag=='li' and self.book is not None:
            self.depth-=1
            if self.depth==0: self.book=None

class AccessibleBuying(unittest.TestCase):
    def test_every_card_buy_action_identifies_the_book(self):
        parser=Cards()
        parser.feed((ROOT/'recomendaciones/index.html').read_text(encoding='utf-8'))
        self.assertGreater(len(parser.links),10)
        for link in parser.links:
            with self.subTest(book=link['book']):
                a=link['attrs']
                name=a.get('aria-label') or a.get('title') or link['text'].strip()
                self.assertIn(link['book'].casefold(),name.casefold())
                self.assertEqual(a.get('target'),'_blank')
                self.assertTrue({'sponsored','nofollow','noopener','noreferrer'} <= set(a.get('rel','').split()))

if __name__=='__main__': unittest.main()
