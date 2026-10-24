import copy
import html
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=json.loads((ROOT/'data/editoriales.json').read_text(encoding='utf-8'))

class UnicodeIdentityRoundtrip(unittest.TestCase):
    def test_visible_and_structured_identity(self):
        fixture=copy.deepcopy(RAW)
        record=copy.deepcopy(fixture['publishers'][0])
        name='Editorial Ñandú, Áurea & «Órbita»'
        record['name']=name
        record['slug']='editorial-nandu-aurea'
        fixture['publishers']=[record]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source=root/'fixture.json'
            output=root/'dist'
            source.write_text(json.dumps(fixture,ensure_ascii=False),encoding='utf-8')
            result=subprocess.run(['python3','scripts/build-editoriales.py','--data',str(source),'--output',str(output),'--today','2026-10-24'],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            detail=(output/'editoriales'/record['slug']/'index.html').read_text(encoding='utf-8')
            index=(output/'editoriales/index.html').read_text(encoding='utf-8')
            self.assertIn('<h1>'+html.escape(name,quote=True)+'</h1>',detail)
            self.assertIn('data-name="'+html.escape(name,quote=True)+'"',index)
            match=re.search('<script type="application/ld\\+json">(.*?)</script>',detail,re.S)
            self.assertIsNotNone(match)
            graph=json.loads(match.group(1))['@graph']
            webpage=next(x for x in graph if x['@type']=='WebPage')
            self.assertEqual(webpage['about']['name'],name)
            self.assertIn(name,webpage['name'])

if __name__=='__main__':
    unittest.main()