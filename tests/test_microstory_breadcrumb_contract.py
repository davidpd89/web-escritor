from pathlib import Path
from html.parser import HTMLParser
from html import unescape
import json
import re

ROOT=Path(__file__).resolve().parents[1]
raw=(ROOT/'al-otro-lado/index.html').read_text(encoding='utf-8')
class Breadcrumb(HTMLParser):
    def __init__(self):
        super().__init__();self.nav=False;self.items=[];self.current=None;self.in_li=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='nav' and a.get('aria-label')=='Ruta de navegación':self.nav=True
        elif self.nav and tag=='li':self.current={'href':None,'current':a.get('aria-current'),'text':''};self.in_li=True
        elif self.in_li and tag=='a':self.current['href']=a.get('href')
    def handle_data(self,data):
        if self.in_li:self.current['text']+=data
    def handle_endtag(self,tag):
        if tag=='li' and self.in_li:self.items.append(self.current);self.in_li=False
        if tag=='nav' and self.nav:self.nav=False
p=Breadcrumb();p.feed(raw)
assert len(p.items)==3
assert [x['href'] for x in p.items]==['/','/premios.html',None]
assert p.items[-1]['current']=='page'
assert [x['text'].strip() for x in p.items]==['Inicio','Premios y reconocimientos','Al otro lado']
graph=json.loads(raw.split('<script type="application/ld+json">',1)[1].split('</script>',1)[0])['@graph']
webpage=next(x for x in graph if x['@type']=='WebPage')
items=webpage['breadcrumb']['itemListElement']
assert [x['position'] for x in items]==[1,2,3]
assert [x['item'] for x in items]==['https://davidportodiaz.com/','https://davidportodiaz.com/premios.html','https://davidportodiaz.com/al-otro-lado/']
registry=json.loads((ROOT/'data/content-registry.json').read_text(encoding='utf-8'))
entry=next(x for x in registry['entries'] if x['id']=='microstory-al-otro-lado')
assert entry['parentId']=='awards'
print('PASS microstory breadcrumb contract')
