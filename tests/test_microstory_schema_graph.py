from pathlib import Path
from html.parser import HTMLParser
import json

ROOT=Path(__file__).resolve().parents[1]
raw=(ROOT/'al-otro-lado/index.html').read_text(encoding='utf-8')
class Head(HTMLParser):
    def __init__(self):super().__init__();self.meta={};self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='meta':self.meta[a.get('property') or a.get('name')]=a.get('content')
        if tag=='link':self.links.append(a)
h=Head();h.feed(raw)
canonical=[x['href'] for x in h.links if x.get('rel')=='canonical']
url='https://davidportodiaz.com/al-otro-lado/'
assert canonical==[url]
assert h.meta['og:url']==url
assert h.meta['og:type']=='article'
assert h.meta['twitter:card']=='summary_large_image'
assert h.meta['og:image']==h.meta['twitter:image']
assert h.meta['og:image:alt'] and h.meta['twitter:image:alt']
assert (ROOT/h.meta['og:image'].removeprefix('https://davidportodiaz.com/')).is_file()
graph=json.loads(raw.split('<script type="application/ld+json">',1)[1].split('</script>',1)[0])['@graph']
by_type={x['@type']:x for x in graph}
assert {'WebPage','ShortStory','Book','Person'}<=set(by_type)
page,story,book,author=(by_type[x] for x in ['WebPage','ShortStory','Book','Person'])
assert page['url']==story['url']==url
assert page['about']['@id']==story['@id']
assert story['author']['@id']==author['@id']
assert story['isPartOf']['@id']==book['@id']
assert story['@id']!=book['@id']
assert story['award'] and 'Primer Premio' in story['award']
assert book['publisher']['name']=='Letras Como Espada'
assert book['contributor']['@id']==author['@id']
assert author['name']=='David Porto Díaz'
print('PASS microstory schema graph')
