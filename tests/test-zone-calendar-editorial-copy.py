import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('calendar_copy', ROOT / 'scripts/build-event-calendars.py')
cal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cal)

class CalendarEditorialCopy(unittest.TestCase):
    def test_downloadable_calendars_preserve_official_copy(self):
        html = (ROOT / 'eventos.html').read_text(encoding='utf-8')
        events = cal.extract_events(html)
        expected, errors = cal.expected_calendars(html)
        self.assertFalse(errors, f'eventos.html: errores de calendario {errors}')
        by_fragment = {cal._event_fragment(event): event for event in events if event.get('eventStatus') == cal.EVENT_SCHEDULED}
        for filename, generated in expected.items():
            fragment = filename.removesuffix('.ics')
            event = by_fragment[fragment]
            text = generated.decode('utf-8').replace('\r\n ', '')
            self.assertEqual(text.count('BEGIN:VEVENT'), 1, f'{filename}: número incorrecto de eventos')
            summary = 'SUMMARY:' + cal._escape_text(event['name'].strip())
            self.assertIn(summary + '\r\n', text, f'{filename}: nombre distinto de eventos.html')
            description = event.get('description')
            if isinstance(description, str) and description.strip():
                value = 'DESCRIPTION:' + cal._escape_text(description.strip())
                self.assertIn(value + '\r\n', text, f'{filename}: descripción distinta de eventos.html')
            published = ROOT / 'assets/events/calendar' / filename
            self.assertTrue(published.is_file(), f'{filename}: falta calendario publicado')
            self.assertEqual(published.read_bytes(), generated, f'{filename}: contenido publicado desactualizado')

if __name__ == '__main__':
    unittest.main()
