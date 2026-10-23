"""Keep publisher history while withdrawing confirmed broken submission links."""
import copy
import importlib.util
import unittest
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('unavailable_editoriales',ROOT/'scripts/build-editoriales.py')
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
SITE='https://example.invalid'
# Keep the regression independent of a real publisher's future recovery.
RECORD={
    'slug':'editorial-de-prueba','name':'Editorial de prueba','group':'Grupo de prueba',
    'publisher_type':'por verificar','country':'ES','genres':['narrativa'],
    'status':'unknown','direct_submission':False,'publish':True,
    'submission_channel':'Canal no disponible','submission_email':None,
    'submission_url':'https://editorial.invalid/contacto','website_url':'https://editorial.invalid/',
    'requirements':['Recepcion pendiente de una nueva comprobacion oficial.'],
    'summary':'Una editorial ficticia utilizada exclusivamente en pruebas aisladas para verificar el historial y la disponibilidad de sus fuentes.',
    'public_note':'La disponibilidad del canal se comprueba sin afirmar que la editorial recibe originales.',
    'verified_at':'2026-10-21','page_updated_at':'2026-10-21',
    'sources':[{'label':'Web oficial','url':'https://editorial.invalid/','primary':True}],
    'history':[{'date':'2026-10-03','event':'Comprobacion anterior','source_url':'https://editorial.invalid/contacto'},
               {'date':'2026-10-21','event':'Canal no disponible','source_url':'https://editorial.invalid/contacto'}],
    'unavailable_urls':['https://editorial.invalid/','https://editorial.invalid/contacto'],
}


class UnavailableSourcesTests(unittest.TestCase):
    def test_history_and_canonical_survive_without_broken_links_or_active_submission(self):
        record=copy.deepcopy(RECORD)
        builder.validate_record(record,set(),date(2026,10,21))
        html=builder.render_detail(SITE,record,date(2026,10,21))
        for url in record['unavailable_urls']:
            self.assertNotIn(url,html)
        self.assertIn('/editoriales/editorial-de-prueba/',html)
        self.assertIn('2026-10-03',html)
        self.assertIn('2026-10-21',html)
        self.assertIn('Estado por verificar',html)
        self.assertNotIn('Comprobar las instrucciones oficiales',html)
        self.assertEqual(record,RECORD)

    def test_unknown_status_alone_keeps_unflagged_source_links(self):
        record=copy.deepcopy(RECORD)
        record.pop('unavailable_urls')
        builder.validate_record(record,set(),date(2026,10,21))
        html=builder.render_detail(SITE,record,date(2026,10,21))
        self.assertIn('href="'+record['submission_url']+'"',html)
        self.assertIn('Comprobar las instrucciones oficiales',html)

    def test_unavailable_submission_cannot_claim_open_or_publish_an_email(self):
        for changes in ({'status':'open'},{'direct_submission':True},
                        {'submission_email':'example@example.com'}):
            record=copy.deepcopy(RECORD);record.update(changes)
            with self.subTest(changes=changes),self.assertRaises(builder.ValidationError):
                builder.validate_record(record,set(),date(2026,10,21))

    def test_unavailability_is_limited_to_known_unique_source_urls(self):
        for urls in ('invalid',['https://other.invalid/'],[RECORD['website_url']]*2):
            record=copy.deepcopy(RECORD);record['unavailable_urls']=urls
            with self.subTest(urls=urls),self.assertRaises(builder.ValidationError):
                builder.validate_record(record,set(),date(2026,10,21))

    def test_published_unavailable_pages_avoid_the_production_soft_404_signal(self):
        # qa/production-global-integrity-audit.mjs rejects visible /404|página no encontrada/.
        import json,re
        data=json.loads((ROOT/'data'/'editoriales.json').read_text(encoding='utf-8'))
        records=data['publishers']
        checked=0
        for record in records:
            if not record.get('unavailable_urls'):
                continue
            checked+=1
            page=(ROOT/'editoriales'/record['slug']/'index.html').read_text(encoding='utf-8')
            visible=re.sub(r'<script.*?</script>|<style.*?</style>|<[^>]+>',' ',page,flags=re.S)
            with self.subTest(slug=record['slug']):
                self.assertIsNone(re.search(r'404|página no encontrada|page not found',visible,re.I))
        self.assertGreaterEqual(checked,1)


if __name__=='__main__':
    unittest.main()
