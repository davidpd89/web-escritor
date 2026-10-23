"""Monitor de fuentes del radar: banderas, presupuesto y tolerancia a fallos; sin red."""
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import radar_source_monitor as m

PAGE_2026 = '<html><body><h1>Premio de Poesía</h1><p>Bases de la edición 2026. Plazo hasta el 9 de octubre de 2026.</p>' + '<p>Texto estable de las bases ' + 'palabra ' * 5 + '</p>' * 1 + ''.join(f'<p>cláusula{i} detalle{i}</p>' for i in range(60)) + '</body></html>'
PAGE_2027 = PAGE_2026.replace('2026', '2027').replace('edición 2027', 'edición 2027 abierta') + ''.join(f'<p>novedad{i} extra{i}</p>' for i in range(60))
DATA = {'items': [{'id': 'a', 'title': 'Premio A', 'source_url': 'https://a.example/bases', 'published': True},
                  {'id': 'b', 'title': 'Premio B', 'source_url': 'https://b.example/bases', 'published': True},
                  {'id': 'c', 'title': 'No publicado', 'source_url': 'https://c.example/', 'published': False}],
        'watchlist': []}
TODAY = date(2026, 10, 21)


class MonitorTests(unittest.TestCase):
    def test_first_visit_records_a_fingerprint_and_flags_nothing(self):
        state = {}
        report = m.run(DATA, state, lambda url: PAGE_2026, TODAY)
        self.assertEqual((report['checked'], report['flagged']), (2, []))
        self.assertIn('2026', state['https://a.example/bases']['years'])
        self.assertNotIn('https://c.example/', state)

    def test_new_year_and_substantial_change_are_flagged(self):
        state = {}
        m.run(DATA, state, lambda url: PAGE_2026, TODAY)
        report = m.run(DATA, state, lambda url: PAGE_2027, TODAY)
        flags = {f['id']: f['flags'] for f in report['flagged']}
        self.assertIn('anio-nuevo', flags['a'])
        self.assertIn('cambio', flags['a'])

    def test_identical_page_is_quiet(self):
        state = {}
        m.run(DATA, state, lambda url: PAGE_2026, TODAY)
        self.assertEqual(m.run(DATA, state, lambda url: PAGE_2026, TODAY)['flagged'], [])

    def test_a_source_must_fail_twice_before_it_is_flagged_and_does_not_stop_the_others(self):
        state = {}
        m.run(DATA, state, lambda url: PAGE_2026, TODAY)
        def flaky(url):
            if 'a.example' in url:
                raise OSError('timeout')
            return PAGE_2026
        first = m.run(DATA, state, flaky, TODAY)
        self.assertEqual(first['flagged'], [])
        second = m.run(DATA, state, flaky, TODAY)
        self.assertEqual([f['id'] for f in second['flagged']], ['a'])
        self.assertEqual(second['checked'], 2)

    def test_budget_checks_the_least_recent_first(self):
        state = {'https://a.example/bases': {'checked_at': '2026-10-20T00:00:00+00:00', 'hash': 'x', 'words': [], 'years': [], 'dates': []}}
        seen = []
        m.run(DATA, state, lambda url: seen.append(url) or PAGE_2026, TODAY, max_sources=1)
        self.assertEqual(seen, ['https://b.example/bases'])

    def test_markdown_lists_each_flag(self):
        text = m.markdown({'generated_at': 'x', 'checked': 1, 'ok': 0, 'flagged': [{'id': 'a', 'title': 'Premio A', 'url': 'https://a.example', 'flags': ['anio-nuevo']}]})
        self.assertIn('Premio A', text)
        self.assertIn('año nuevo', text)


if __name__ == '__main__':
    unittest.main()
