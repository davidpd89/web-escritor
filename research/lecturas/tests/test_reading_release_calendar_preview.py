"""Synthetic release calendar tests. NO network / no execution in this PR."""
import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

FILE = Path(__file__).resolve().parents[2] / "scripts/reading_release_calendar_preview.py"
spec = importlib.util.spec_from_file_location("reading_release_cal", FILE)
cal = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cal
spec.loader.exec_module(cal)


def book(*, when="2026-11-15", isbn="9788432251436", status="publicado"):
    return {"id": "isbn-" + isbn, "isbn13": isbn,
            "slug": "cosamala-9788432251436", "titulo": "Cosamala",
            "autores": ["Alana S. Portero"], "estado": status,
            "fecha_publicacion": when, "precision_fecha": "dia"}


class ReleaseCalendarTest(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 10, 21)

    def test_exact_future_published_edition_has_stable_calendar_uid(self):
        a = cal.entries([book()], self.today)
        b = cal.entries([book()], self.today)
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0]["uid"], b[0]["uid"])
        self.assertEqual(a[0]["url"],
                         "https://davidportodiaz.com/recomendaciones/libros/cosamala-9788432251436/")

    def test_no_draft_past_or_partial_date(self):
        self.assertEqual(cal.entries([book(status="borrador")], self.today), [])
        self.assertEqual(cal.entries([book(when="2026-10-20")], self.today), [])
        self.assertEqual(cal.entries([book(when="2026-11")], self.today), [])

    def test_ical_has_all_day_interval_and_day_before_alert(self):
        row = cal.entries([book()], self.today)[0]
        text = cal.calendar([row], generated_day=self.today)
        self.assertIn("DTSTART;VALUE=DATE:20261115\r\n", text)
        self.assertIn("DTEND;VALUE=DATE:20261116\r\n", text)
        self.assertIn("BEGIN:VALARM\r\n", text)
        self.assertIn("TRIGGER:-P1D\r\n", text)
        self.assertTrue(text.endswith("END:VCALENDAR\r\n"))

    def test_calendar_utf8_octet_folding_and_injection_escaping(self):
        line = "SUMMARY:" + "Á" * 95
        self.assertTrue(all(len(p.encode("utf-8")) <= 75
                            for p in cal.fold(line).split("\r\n")))
        self.assertEqual(cal.escape("Línea\nX;otra,\r\nUID:TRAMPA"),
                         r"Línea\nX\;otra\,\nUID:TRAMPA")

    def test_google_calendar_link_uses_own_web_and_dates(self):
        row = cal.entries([book()], self.today)[0]
        link = cal.google_link(row)
        self.assertTrue(link.startswith("https://calendar.google.com/calendar/render?"))
        self.assertIn("20261115%2F20261116", link)
        self.assertIn("davidportodiaz.com", link)

    def test_duplicate_isbn_stops_publication(self):
        books = [book(), dict(book(), id="another-duplicate")]
        with self.assertRaisesRegex(ValueError, "mismo ISBN"):
            cal.entries(books, self.today)

    def test_calendar_does_not_change_daily_without_editorial_update(self):
        item = book()
        item["fecha_actualizacion"] = "2026-10-20"
        first = cal.entries([item], date(2026, 10, 21))
        second = cal.entries([item], date(2026, 10, 22))
        self.assertEqual(cal.calendar(first, generated_day=date(2026, 10, 21)),
                         cal.calendar(second, generated_day=date(2026, 10, 22)))


if __name__ == "__main__":
    unittest.main()
