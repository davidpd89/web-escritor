"""Casos sintéticos para el calendario; preparar sin ejecutarlos en esta PR."""
import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "reading_release_calendar", ROOT / "scripts/reading_release_calendar.py"
)
calendar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calendar)


def fake_book(ident="isbn-9788408325338", title="Una novela ficticia", **changes):
    item = {
        "id": ident,
        "slug": "una-novela-ficticia",
        "titulo": title,
        "autores": ["Ana Ejemplo", "Luis Ejemplo"],
        "estado": "publicado",
        "fecha_publicacion": "2026-10-28",
        "fecha_actualizacion": "2026-10-21",
    }
    item.update(changes)
    return item


class ReleaseCalendarContract(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 10, 21)

    def test_standalone_and_subscribed_feed(self):
        book = fake_book()
        files = calendar.outputs({"libros": [book]}, self.today)
        self.assertEqual(sorted(files), ["isbn-9788408325338.ics", "proximos-lanzamientos.ics"])
        text = files["isbn-9788408325338.ics"].decode("utf-8")
        self.assertIn("DTSTART;VALUE=DATE:20261028\r\n", text)
        self.assertIn("DTEND;VALUE=DATE:20261029\r\n", text)
        self.assertIn("UID:lectura-isbn-9788408325338@davidportodiaz.com", text)
        self.assertIn("DTSTAMP:20261021T000000Z", text)
        self.assertIn("/recomendaciones/libros/una-novela-ficticia/", text)
        self.assertIn("TRANSP:TRANSPARENT", text)
        self.assertNotIn("VALARM", text)
        self.assertEqual(files["isbn-9788408325338.ics"], files["proximos-lanzamientos.ics"])

    def test_repeat_is_byte_identical(self):
        data = {"libros": [fake_book()]}
        self.assertEqual(calendar.outputs(data, self.today), calendar.outputs(data, self.today))

    def test_partial_or_invalid_dates_never_gain_a_day(self):
        for invalid in ("2026", "2026-10", "2026-10-99", "20261028", "", None):
            with self.subTest(invalid=invalid):
                files = calendar.outputs({"libros": [fake_book(fecha_publicacion=invalid)]}, self.today)
                self.assertEqual(sorted(files), ["proximos-lanzamientos.ics"])
                self.assertNotIn(b"BEGIN:VEVENT", files["proximos-lanzamientos.ics"])

    def test_unpublished_books_not_exposed(self):
        files = calendar.outputs({"libros": [fake_book(estado="borrador")]}, self.today)
        self.assertEqual(sorted(files), ["proximos-lanzamientos.ics"])
        self.assertNotIn(b"BEGIN:VEVENT", files["proximos-lanzamientos.ics"])

    def test_past_release_in_feed_but_not_single_file(self):
        item = fake_book(fecha_publicacion="2026-10-20")
        files = calendar.outputs({"libros": [item]}, self.today)
        self.assertEqual(sorted(files), ["proximos-lanzamientos.ics"])
        self.assertIn(b"DTSTART;VALUE=DATE:20261020", files["proximos-lanzamientos.ics"])

    def test_outside_horizon_not_exposed(self):
        old = fake_book(fecha_publicacion="2026-08-01")
        far = fake_book(ident="isbn-9788408325000", fecha_publicacion="2028-01-01")
        files = calendar.outputs({"libros": [old, far]}, self.today)
        self.assertEqual(len(files), 1)

    def test_escaping_blocks_property_injection(self):
        title = "Libro, difícil; mágico\nBEGIN:VALARM"
        files = calendar.outputs({"libros": [fake_book(title=title)]}, self.today)
        text = files["proximos-lanzamientos.ics"].decode("utf-8")
        self.assertIn(r"Libro\, difícil\; mágico\nBEGIN:VALARM", text)
        self.assertNotIn("\r\nBEGIN:VALARM", text)

    def test_fold_never_splits_utf8_code_point_or_exceeds_75_octets(self):
        files = calendar.outputs({"libros": [fake_book(title="Árbol " * 55)]}, self.today)
        raw = files["proximos-lanzamientos.ics"]
        self.assertTrue(raw.endswith(b"\r\n"))
        for physical_line in raw.split(b"\r\n"):
            self.assertLessEqual(len(physical_line), 75)
            physical_line.decode("utf-8")

    def test_rejects_unsafe_path_component(self):
        with self.assertRaises(ValueError):
            calendar.outputs({"libros": [fake_book(ident="../otro")]}, self.today)

    def test_duplicate_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            calendar.outputs({"libros": [fake_book(), fake_book()]}, self.today)

    def test_only_generator_owned_stale_ics_is_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stale = root / "lib-antiguo.ics"
            stale.write_bytes(calendar.calendar([
                (date(2026, 10, 29), "lib-antiguo",
                 fake_book(ident="lib-antiguo"), date(2026, 10, 21))
            ]))
            (root / "personal.ics").write_text("calendario ajeno", encoding="utf-8")
            (root / "manual.txt").write_text("mantener", encoding="utf-8")
            files = calendar.outputs({"libros": [fake_book()]}, self.today)
            calendar.write_outputs(files, root)
            self.assertFalse(stale.exists())
            self.assertTrue((root / "personal.ics").exists())
            self.assertTrue((root / "manual.txt").exists())
            self.assertEqual((root / "proximos-lanzamientos.ics").read_bytes(), files["proximos-lanzamientos.ics"])
