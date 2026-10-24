from pathlib import Path
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
class Evidence(HTMLParser):
    def __init__(self):super().__init__();self.items=[];self.active=None;self.caption=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='figure' and 'microstory-shot' in a.get('class','').split():self.active={'src':'','alt':'','caption':''}
        elif tag=='img' and self.active is not None:self.active['src']=a.get('src','');self.active['alt']=a.get('alt','')
        elif tag=='figcaption' and self.active is not None:self.caption=True
    def handle_data(self,data):
        if self.caption and self.active is not None:self.active['caption']+=data
    def handle_endtag(self,tag):
        if tag=='figcaption':self.caption=False
        if tag=='figure' and self.active is not None:self.items.append(self.active);self.active=None
p=Evidence();p.feed((ROOT/'al-otro-lado/index.html').read_text(encoding='utf-8'))
assert len(p.items)==2
expected=[('prologo','4','prólogo'),('microrrelato-ganador','67','ganador')]
for item,(slug,page,subject) in zip(p.items,expected):
    assert slug in item['src']
    assert 'página '+page in item['caption'].lower(),item['caption']
    assert subject.lower() in (item['alt']+' '+item['caption']).lower()
    assert 'Al otro lado' in item['alt']
    assert 'David Porto Díaz' in item['alt'] or 'David Porto Díaz' in item['caption']
print('PASS microstory documentary captions')
