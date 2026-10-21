"""Keep publisher history while withdrawing confirmed broken submission links."""
import copy
import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('unavailable_editoriales',ROOT/'scripts/build-editoriales.py')
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
DATA=json.loads((ROOT/'data/editoriales.json').read_text(encoding='utf-8'))
RECORD=next(r for r in DATA['publishers'] if r['slug']=='editorial-amarante')


class UnavailableSourcesTests(unittest.TestCase):
    def test_history_and_canonical_survive_without_broken_links_or_active_submission(self):
        record=copy.deepcopy(RECORD)
        builder.validate_record(record,set(),date(2026,10,21))
        html=builder.render_detail(DATA['site'].rstrip('/'),record,date(2026,10,21))
        for url in record['unavailable_urls']:
            self.assertNotIn(url,html)
        self.assertIn('/editoriales/editorial-amarante/',html)
        self.assertIn('2026-10-03',html)
        self.assertIn('2026-10-21',html)
        self.assertIn('Por verificar',html)
        self.assertNotIn('Comprobar las instrucciones oficiales',html)
        self.assertEqual(record,RECORD)

    def test_unknown_status_alone_does_not_remove_working_source_links(self):
        record=copy.deepcopy(RECORD)
        record.pop('unavailable_urls')
        builder.validate_record(record,set(),date(2026,10,21))
        html=builder.render_detail(DATA['site'].rstrip('/'),record,date(2026,10,21))
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


if __name__=='__main__':
    unittest.main()
