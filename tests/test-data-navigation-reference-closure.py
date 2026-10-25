import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class NavigationReferenceClosure(unittest.TestCase):
    def test_public_navigation_targets(self):
        nav = json.loads((ROOT / 'data/navigation.json').read_text(encoding='utf-8'))
        registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
        entries = {entry['id']: entry for entry in registry['entries']}
        targets = []
        for field in ('header', 'homeMap', 'exploreShortcuts', 'exploreUtilities'):
            for item in nav.get(field, []):
                targets.append((field, item if isinstance(item, str) else item.get('targetId', item.get('id'))))
        for section in ('footer', 'localNavSets', 'menu'):
            for group, items in nav.get(section, {}).items():
                for item in items:
                    targets.append((section + '/' + group, item if isinstance(item, str) else item.get('targetId', item.get('id'))))
        for item in nav.get('exploreTerritories', []):
            targets.append(('exploreTerritories', item['id']))
        self.assertTrue(targets, 'data/navigation.json: no se encontraron destinos navegables')
        for location, target in targets:
            with self.subTest(location=location, target=target):
                self.assertIn(target, entries, f'data/navigation.json {location}: destino {target!r} inexistente')
                self.assertTrue(entries[target].get('url', '').startswith('/'), f'data/content-registry.json {target}: URL pública ausente')

if __name__ == '__main__':
    unittest.main()