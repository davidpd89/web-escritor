"""Contrato de RSS Pinterest con datos ficticios y sin llamadas remotas."""
import importlib.util
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
mod = importlib.util.spec_from_file_location(
    "reading_pinterest_rss", ROOT / "scripts/build-reading-pinterest-rss.py"
)
rss = importlib.util.module_from_spec(mod)
mod.loader.exec_module(rss)
BOARDS = json.loads((ROOT / "data/reading-pinterest-boards.json").read_text(encoding="utf-8"))


def book(id, slug, cats, published=None):
    item = {"id": id, "slug": slug, "titulo": slug.capitalize(),
            "autores": ["Autora de prueba"], "estado": "publicado",
            "descripcion_breve": f"Descripción ficticia de {slug} sobre viajes y personajes.",
            "fecha_actualizacion": "2026-10-20",
            "portada_local": f"/assets/reading-covers/{slug}.webp"}
    if published:
        item["fecha_publicacion"] = published
    return item


class RSSPublisherTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "assets/reading-covers").mkdir(parents=True)
        self.today = date(2026, 10, 20)

    def add_book(self, b):
        (self.root / "assets/reading-covers" / (b["slug"] + ".webp")).write_bytes(b"WEBP fake only for path contract")
        parent = self.root / "recomendaciones" / "libros" / b["slug"]
        parent.mkdir(parents=True)
        (parent / "index.html").write_text("página ficticia", encoding="utf-8")

    def test_single_primary_board_and_exact_destination(self):
        b = book("lib-0001", "coraline", ["halloween", "fantasia-juvenil"])
        self.add_book(b)
        dataset = {"libros": [b], "libro_categorias": [
            {"libro_id": "lib-0001", "categoria_id": c}
            for c in ["halloween", "fantasia-juvenil"]]}
        eligible = rss.suitable_books(self.root, dataset, BOARDS, self.today)
        self.assertEqual(len(eligible), 1)
        self.assertEqual(eligible[0]["board"]["slug"], "terror-fantasia-oscura")
        state = {"schema_version": 1, "pins": {}}
        self.assertTrue(rss.assign_queue(eligible, state, self.today, budget=2))
        rss_text = rss.build_feed(eligible[0]["board"], eligible, state, self.today,
                                  BOARDS["site"], 30)
        tree = ET.fromstring(rss_text)
        items = tree.findall("./channel/item")
        self.assertEqual(len(items), 1)
        self.assertIn("davidportodiaz.com/recomendaciones/libros/coraline/",
                      items[0].findtext("link"))
        self.assertIn("utm_source=pinterest", items[0].findtext("link"))
        self.assertNotIn("amazon", items[0].findtext("link").lower())
        media = items[0].find("{http://search.yahoo.com/mrss/}content")
        self.assertEqual(media.attrib["url"], "https://davidportodiaz.com/assets/reading-covers/coraline.webp")
        self.assertEqual(media.attrib["type"], "image/webp")
        self.assertLessEqual(len(items[0].findtext("title")), 100)
        self.assertLessEqual(len(items[0].findtext("description")), 800)
        self.assertEqual(len(tree.findall(".//item")), 1)
        before = json.dumps(state, sort_keys=True)
        self.assertFalse(rss.assign_queue(eligible, state, self.today, budget=2))
        self.assertEqual(json.dumps(state, sort_keys=True), before)
        self.assertEqual(rss.build_feed(eligible[0]["board"], eligible, state, self.today,
                                       BOARDS["site"], 30), rss_text)

    def test_releases_are_budgeted_across_boards(self):
        dataset = {"libros": [], "libro_categorias": []}
        for i in range(5):
            slug = f"obra-{i}"
            b = book(f"lib-{i}", slug, ["fantasia-juvenil"], "2026-10-18")
            self.add_book(b)
            dataset["libros"].append(b)
            dataset["libro_categorias"].append({
                "libro_id": b["id"], "categoria_id": "fantasia-juvenil"})
        entries = rss.suitable_books(self.root, dataset, BOARDS, self.today)
        self.assertTrue(all(e["board"]["slug"] == "novedades-fantasia" for e in entries))
        state = {"schema_version": 1, "pins": {}}
        rss.assign_queue(entries, state, self.today, budget=2)
        self.assertEqual(sorted(p["scheduled_date"] for p in state["pins"].values()), [
            "2026-10-20", "2026-10-20", "2026-10-21", "2026-10-21", "2026-10-22"
        ])
        feed = rss.build_feed(entries[0]["board"], entries, state, self.today,
                              BOARDS["site"], 30)
        self.assertEqual(len(ET.fromstring(feed).findall("./channel/item")), 2)

    def test_novelty_book_keeps_board_when_90_day_window_expires(self):
        b = book("lib-reciente", "reciente", ["fantasia-juvenil"], "2026-10-18")
        self.add_book(b)
        data = {"libros": [b], "libro_categorias": [
            {"libro_id": b["id"], "categoria_id": "fantasia-juvenil"}]}
        state = {"schema_version": 1, "pins": {}}
        recent = rss.suitable_books(self.root, data, BOARDS, self.today, state=state)
        self.assertEqual(recent[0]["board"]["slug"], "novedades-fantasia")
        rss.assign_queue(recent, state, self.today, budget=2)
        later = rss.suitable_books(self.root, data, BOARDS, date(2027, 3, 10), state=state)
        self.assertEqual(later[0]["board"]["slug"], "novedades-fantasia")
        xml = rss.build_feed(later[0]["board"], later, state, date(2027, 3, 10),
                             BOARDS["site"], 150)
        self.assertEqual(len(ET.fromstring(xml).findall("./channel/item")), 1)

    def test_recent_non_fantasy_book_does_not_enter_fantasy_novelties(self):
        b = book("lib-poesia", "libro-poesia", ["clasicos"], "2026-10-18")
        self.add_book(b)
        data = {"libros": [b], "libro_categorias": [
            {"libro_id": b["id"], "categoria_id": "clasicos"}]}
        self.assertEqual(rss.suitable_books(self.root, data, BOARDS, self.today), [])

    def test_recent_romantasy_book_enters_novelty_board(self):
        b = book("lib-romantasy", "libro-romantasy", ["romantasy"], "2026-10-18")
        self.add_book(b)
        data = {"libros": [b], "libro_categorias": [
            {"libro_id": b["id"], "categoria_id": "romantasy"}]}
        entries = rss.suitable_books(self.root, data, BOARDS, self.today)
        self.assertEqual(entries[0]["board"]["slug"], "novedades-fantasia")

    def test_never_enqueues_draft_or_missing_page_or_cover(self):
        published = book("lib-1", "libro-listo", ["fantasia-juvenil"])
        draft = book("lib-2", "libro-borrador", ["fantasia-juvenil"])
        draft["estado"] = "borrador"
        self.add_book(published)
        draft["portada_local"] = "/assets/reading-covers/nonexistent.webp"
        data = {"libros": [published, draft], "libro_categorias": [
            {"libro_id": b["id"], "categoria_id": "fantasia-juvenil"}
            for b in (published, draft)]}
        self.assertEqual([b["book"]["id"] for b in rss.suitable_books(
            self.root, data, BOARDS, self.today)], ["lib-1"])

    def test_only_real_dates_count_as_new_releases(self):
        b = book("lib-1", "libro-con-anio", ["fantasia-juvenil"])
        b["fecha_publicacion"] = "2026"
        self.add_book(b)
        data = {"libros": [b], "libro_categorias": [
            {"libro_id": "lib-1", "categoria_id": "fantasia-juvenil"}]}
        entry = rss.suitable_books(self.root, data, BOARDS, self.today)[0]
        self.assertEqual(entry["board"]["slug"], "fantasia-juvenil")

    def test_xml_escapes_unicode_and_title(self):
        bookdata = book("lib-1", "ejemplo", ["terror"])
        bookdata["titulo"] = "Niñez & misterios <de verdad>"
        self.add_book(bookdata)
        dataset = {"libros": [bookdata], "libro_categorias": [
            {"libro_id": "lib-1", "categoria_id": "terror"}]}
        ent = rss.suitable_books(self.root, dataset, BOARDS, self.today)
        state = {"schema_version": 1, "pins": {}}
        rss.assign_queue(ent, state, self.today, 2)
        txt = rss.build_feed(ent[0]["board"], ent, state, self.today,
                              BOARDS["site"], 150)
        self.assertIn("Niñez &amp; misterios &lt;de verdad&gt;", txt)
        self.assertIn("Ñ", "Ñ")  # script and text are UTF-8
        self.assertEqual(len(ET.fromstring(txt).findall("./channel/item")), 1)


if __name__ == "__main__":
    unittest.main()
