"""Pruebas pendientes de ejecutar para la auditoría no destructiva de sellos."""
import unittest

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reading_publisher_audit import publisher_audit, BLOCK_REASON


class PublisherAliasReportTest(unittest.TestCase):
    def setUp(self):
        self.registry = {"publishers": [
            {"name": "Aguilar", "slug": "aguilar", "publish": True,
             "publisher_type": "tradicional"},
            {"name": "Editorial Ejemplo", "slug": "editorial-ejemplo", "publish": True,
             "publisher_type": "independiente"},
        ]}
        self.config = {"publisher_aliases": []}

    def entry(self, isbn, *, name="Aguilar", reason=BLOCK_REASON, status="pendiente_datos"):
        return {"isbn13": isbn, "estado_ingesta": status, "motivo": reason,
                "datos": {"editorial": name, "titulo": "Libro ficticio"}}

    def test_counts_distinct_blocked_isbns_and_never_changes_input(self):
        state = {"items": {
            "uno": self.entry("9780000000001"),
            "dos": self.entry("9780000000001"),
            "tres": self.entry("9780000000002"),
            "cuatro": self.entry("9780000000003", reason="Sin portada"),
        }}
        before = repr(state)
        report = publisher_audit(state, self.registry, self.config)
        self.assertEqual(report["isbn_bloqueados"], 2)
        self.assertEqual(report["sellos_pendientes"], 1)
        self.assertEqual(report["grupos"][0]["candidatos_para_revision_manual"][0]["slug"], "aguilar")
        self.assertEqual(report["grupos"][0]["decision"], "pendiente_revision_humana")
        self.assertEqual(repr(state), before)

    def test_no_auto_accept_even_with_exact_alias(self):
        config = {"publisher_aliases": [{"slug": "editorial-ejemplo", "aliases": ["Sello Inventado"]}]}
        report = publisher_audit(
            {"items": {"p": self.entry("9780000000007", name="Sello Inventado")}},
            self.registry, config)
        self.assertEqual(report["grupos"][0]["decision"], "pendiente_revision_humana")
        self.assertEqual(report["grupos"][0]["candidatos_para_revision_manual"][0]["slug"], "editorial-ejemplo")

    def test_nonblocked_items_are_excluded(self):
        report = publisher_audit(
            {"items": {"p": self.entry("9780000000008", status="publicado")}},
            self.registry, self.config)
        self.assertEqual(report["isbn_bloqueados"], 0)
        self.assertEqual(report["grupos"], [])
