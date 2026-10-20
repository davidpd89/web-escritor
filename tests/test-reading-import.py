import copy
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
imp=module('reading_import_test','import-reading-sheet.py')
discovery=module('reading_discovery_test','discover-reading-books.py')
snapshot=json.loads((ROOT/'data/reading-sheet-snapshot.json').read_text(encoding='utf-8'))
review=json.loads((ROOT/'data/reading-import-review.json').read_text(encoding='utf-8'))
existing=json.loads((ROOT/'data/reading-catalogue.json').read_text(encoding='utf-8'))
data,report=imp.convert(snapshot,review,existing,ROOT)
assert data==existing
assert len(data['libros'])==1 and len(data['libro_categorias'])==6
assert data['libros'][0]['anio_publicacion']==2009 and 'fecha_publicacion' not in data['libros'][0]
assert data['libros'][0]['url_amazon_afiliada'].endswith('tag=davidporto-21')
unapproved=copy.deepcopy(review)
unapproved['reviews']={}
drafts,report=imp.convert(snapshot,unapproved,existing,ROOT)
assert drafts['libros'][0]['estado']=='borrador' and report[0]['needs_review']
assert imp.builder.validate(drafts,ROOT)==[]
seen=set()
payload={'searchResult':{'items':[{'asin':'8498382378','itemInfo':{'title':{'displayValue':'Coraline'}}},{'asin':'bad'}]}}
assert len(discovery.candidates(payload,seen))==1
assert discovery.candidates(payload,seen)==[]
body=discovery.request_body('Salamandra','davidporto-21',1)
assert body['searchIndex']=='Books' and body['sortBy']=='NewestArrivals' and not any('image' in r for r in body['resources'])
assert discovery.is_pending_eligibility(403, {'message':'Your account does not currently meet the eligibility requirements.'})
assert not discovery.is_pending_eligibility(403, {'message':'Access denied'})
assert not discovery.is_pending_eligibility(401, {'message':'Your account does not currently meet the eligibility requirements.'})
try:
    discovery.candidates({'errors':[{'code':'NoCredentials'}]},set())
except ValueError:
    pass
else:
    raise AssertionError('Errores de API no deben aparentar una consulta correcta')
print('PASS importador Sheets, revisión previa, relaciones, fechas conservadoras y descubrimiento Amazon sin publicación.')
