import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('amazon_audit_extra',ROOT/'scripts/audit-amazon-links.py')
assert SPEC and SPEC.loader
module=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

class IsbnDestinationAudit(unittest.TestCase):
    def audit_book(self,query):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'data').mkdir()
            (root/'index.html').write_text('<main>Catálogo</main>',encoding='utf-8')
            payload={'libros':[{'id':'lib-1','slug':'coraline','titulo':'Coraline','estado':'publicado','isbn13':'9788498382372','amazon_busqueda_isbn':query}]}
            (root/'data/reading-catalogue.json').write_text(json.dumps(payload),encoding='utf-8')
            return module.audit(root,'davidporto-21')
    def test_wrong_isbn_is_reported_even_with_correct_tag(self):
        report=self.audit_book('https://www.amazon.es/s?k=9788425374012&tag=davidporto-21')
        self.assertTrue(report['errors'] or report['manual_review'],'ISBN de otro libro no detectado')
    def test_valid_isbn_search_is_clean(self):
        report=self.audit_book('https://www.amazon.es/s?k=9788498382372&tag=davidporto-21')
        self.assertEqual(report['errors'],[])

if __name__=='__main__': unittest.main()
