import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('feed_blocks_qa',ROOT/'scripts/build-feed.py')
feed=importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)
site={'@context':'https://schema.org','@type':'WebSite','name':'Sitio'}
article={'@context':'https://schema.org','@graph':[{'@type':'BreadcrumbList','itemListElement':[]},{'@type':'Article','headline':'Título auténtico','url':'https://davidportodiaz.com/cuaderno/qa/','datePublished':'2026-10-23','description':'Descripción auténtica'}]}
def script(data):
    return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False)+'</script>'
with tempfile.TemporaryDirectory() as tmp:
    page=Path(tmp)/'index.html'
    for first,second in [(site,article),(article,site)]:
        page.write_text('<html><head><title>Título de reserva</title><meta name="description" content="Reserva">'+script(first)+script(second)+'</head></html>',encoding='utf-8')
        meta=feed.extract_metadata(str(page))
        assert meta['title']=='Título auténtico',meta
        assert meta['date']=='2026-10-23',meta
        assert meta['description']=='Descripción auténtica',meta
        assert meta['url']=='https://davidportodiaz.com/cuaderno/qa/',meta
print('OK: metadata RSS independiente del orden de JSON-LD')
