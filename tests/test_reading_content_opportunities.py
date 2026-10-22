"""Contratos sintéticos de auditoría, preparados sin ejecutar."""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reading_content_opportunities import audit, parse_day, parse_instant


class ContentOpportunitiesTest(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 10, 21)
        self.catalogue = {"libros": [
            {"id": "lib-1", "titulo": "Libro nuevo", "estado": "publicado",
             "autores": ["Ana Autora"], "editorial": "Ejemplo",
             "editorial_slug": "editorial-ejemplo", "fecha_publicacion": "2026-10-28"},
            {"id": "lib-2", "titulo": "Libro pendiente", "estado": "publicado",
             "autores": ["Autor Pendiente"], "editorial": "Sello ausente",
             "editorial_slug": "sello-ausente", "fecha_publicacion_parcial": "2026-11"},
            {"id": "lib-3", "estado": "borrador", "autores": ["Invisible"],
             "editorial_slug": "editorial-ejemplo", "fecha_publicacion": "2026-10-31"}
        ]}
        self.authors = {"autores": [
            {"nombre": "Ana Autora", "slug": "ana-autora", "tipo": "bibliografico",
             "descripcion": "Descripción editorial sin biografía externa"}
        ]}
        self.publishers = {"publishers": [
            {"slug": "editorial-ejemplo", "name": "Editorial Ejemplo",
             "publish": True, "status": "open", "verified_at": "2026-05-01"},
            {"slug": "oculta", "name": "No pública",
             "publish": False, "status": "closed", "verified_at": "2026-01-01"},
        ]}
        self.market = {"offers": [], "ratings": [
            {"libro_id": "lib-1", "fuente": "goodreads", "puntuacion": 4.5}
        ]}

    def test_flags_enrichment_gaps_without_inventing_bios_or_editorial_status(self):
        state = repr((self.catalogue, self.authors, self.publishers, self.market))
        out = audit(self.catalogue, self.authors, self.publishers, self.market, self.today)
        stats = out["resumen"]
        self.assertEqual(stats["libros_publicados"], 2)
        self.assertEqual(stats["autores_con_libros"], 2)
        self.assertEqual(stats["autores_bibliograficos_sin_bio_verificada"], 1)
        self.assertEqual(stats["referencias_a_autores_sin_ficha"], 1)
        self.assertEqual(stats["libros_sin_editorial_enlazable"], 1)
        self.assertEqual(stats["editoriales_con_verificacion_caducada"], 1)
        self.assertEqual(stats["lanzamientos_con_fecha_exacta_30_dias"], 1)
        self.assertEqual(stats["fechas_de_publicacion_parciales"], 1)
        self.assertEqual(out["prioridades"]["editoriales_con_revision_pendiente"][0]["estado_publicado"], "open")
        self.assertEqual(repr((self.catalogue, self.authors, self.publishers, self.market)), state)

    def test_unknown_publisher_remains_unknown_and_unpublished_is_not_listed(self):
        out = audit(self.catalogue, self.authors, self.publishers, self.market, self.today)
        self.assertEqual(out["prioridades"]["desvinculados_editoriales"][0]["slug"], "sello-ausente")
        self.assertNotIn("lib-3", repr(out["prioridades"]))

    def test_price_expiration_never_uses_untrusted_text_as_offer(self):
        self.market["offers"] = [
            {"libro_id": "lib-1", "caduca_en": "2026-10-20T11:00:00Z"},
            {"libro_id": "lib-2", "caduca_en": "no es una fecha"},
        ]
        stats = audit(self.catalogue, self.authors, self.publishers, self.market, self.today)["resumen"]
        self.assertEqual(stats["ofertas_caducadas_o_invalidas"], 2)
        self.assertEqual(stats["ofertas_vigentes_al_inicio_del_dia_utc"], 0)
        self.assertEqual(stats["libros_sin_ofertas"], 0)

    def test_invalid_dates_and_timestamps_are_ignored(self):
        self.assertIsNone(parse_day("2026-10"))
        self.assertIsNone(parse_day("2026-11-31"))
        self.assertIsNone(parse_instant("2026-10-21"))
        self.assertIsNotNone(parse_instant("2026-10-21T10:00:00Z"))
