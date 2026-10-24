from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
class Pictures(HTMLParser):
    def __init__(self):super().__init__();self.pictures=[];self.current=None;self.figures=0;self.captions=0;self.in_caption=False;self.caption_text=''
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='picture':self.current={'sources':[],'image':None}
        elif tag=='source' and self.current is not None:self.current['sources'].append(a)
        elif tag=='img' and self.current is not None:self.current['image']=a
        elif tag=='figure':self.figures+=1
        elif tag=='figcaption':self.in_caption=True;self.caption_text=''
    def handle_data(self,data):
        if self.in_caption:self.caption_text+=data
    def handle_endtag(self,tag):
        if tag=='picture':self.pictures.append(self.current);self.current=None
        if tag=='figcaption':
            assert len(self.caption_text.strip())>=25,'Leyenda documental insuficiente'
            self.captions+=1;self.in_caption=False
p=Pictures();p.feed((ROOT/'al-otro-lado/index.html').read_text(encoding='utf-8'))
assert len(p.pictures)==3
assert p.figures==3 and p.captions==2
for item in p.pictures:
    img=item['image'];assert img
    assert img.get('alt') and len(img['alt'])>=40
    assert int(img['width'])>0 and int(img['height'])>0
    assert img.get('loading')=='lazy'
    assert img.get('decoding')=='async'
    assert img['src'].endswith('.webp')
    assert (ROOT/img['src'].lstrip('/')).is_file()
    assert len(item['sources'])>=1
    assert any(s.get('type')=='image/avif' for s in item['sources'])
    for s in item['sources']:
        for candidate in s['srcset'].split(','):
            asset=candidate.strip().split(' ')[0]
            assert (ROOT/asset.lstrip('/')).is_file(),asset
print('PASS microstory documentary image assets')
