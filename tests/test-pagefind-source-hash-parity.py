import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pagefind_builder', ROOT / 'scripts/build-pagefind-index.py')
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)

class HashParity(unittest.TestCase):
    def test_real_page_content_and_registry_label(self):
        registry = builder.load_registry_by_source(ROOT)
        candidates = [p for p in builder.eligible_pages(ROOT) if registry.get(p, {}).get('label')]
        self.assertTrue(candidates, 'No existen páginas indexables con título registrado')
        rel = candidates[0]
        original = (ROOT / rel).read_bytes()
        label = registry[rel]['label']
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(original)
            data = root / 'data'
            data.mkdir(exist_ok=True)
            registry_file = data / 'content-registry.json'
            payload = {'defaults': {'status': 'public', 'searchIndex': True}, 'entries': [{'sourceFile': rel, 'label': label}]}
            registry_file.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
            first = builder.source_hashes(root, [rel])[rel]
            target.write_bytes(original.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
            self.assertEqual(builder.source_hashes(root, [rel])[rel], first, f'{rel}: CRLF altera incorrectamente la huella')
            target.write_bytes(original + b'\n<!-- cambio de contenido publicado -->\n')
            self.assertNotEqual(builder.source_hashes(root, [rel])[rel], first, f'{rel}: cambio HTML no detectado')
            target.write_bytes(original)
            payload['entries'][0]['label'] = label + ' actualizado'
            registry_file.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
            self.assertNotEqual(builder.source_hashes(root, [rel])[rel], first, f'{rel}: cambio de título del registro no detectado')

if __name__ == '__main__':
    unittest.main()
