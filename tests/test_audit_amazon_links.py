#!/usr/bin/env python3
"""Casos offline para scripts/audit-amazon-links.py. Sin peticiones a Amazon.

No ejecutado al abrir la PR. Para QA posterior:
    python -m unittest discover -s tests -p 'test_audit_amazon_links.py'
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("audit_amazon_links", ROOT / "scripts/audit-amazon-links.py")
assert SPEC is not None and SPEC.loader is not None
audit_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_module)


class AuditAmazonLinksTest(unittest.TestCase):
    def test_asin_con_y_sin_slug_titulo(self):
        for url in [
            "https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21",
            "https://www.amazon.es/Nombre-del-libro/dp/B0GB6LGQFH?tag=davidporto-21",
            "https://www.amazon.es/gp/product/B0GB6LGQFH?tag=davidporto-21",
            "https://www.amazon.es/Nombre-del-libro/gp/product/B0GB6LGQFH?tag=davidporto-21",
        ]:
            with self.subTest(url=url):
                self.assertEqual(audit_module.asin_of(url), "B0GB6LGQFH")
        self.assertIsNone(audit_module.asin_of("https://www.amazon.es/s?k=9791387659776"))

    def test_cola_libros_y_diferencia_fuente_formato(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data").mkdir()
            (root / "index.html").write_text(
                '<a href="https://www.amazon.es/Libro/dp/B0GB6LGQFH?tag=davidporto-21">Comprar</a>'
                '<a href="https://www.amazon.es/stores/author/B0GZFP1JV3">Seguir</a>',
                encoding="utf-8",
            )
            catalogue = {
                "libros": [
                    {
                        "slug": "uno",
                        "titulo": "Libro verificado",
                        "estado": "publicado",
                        "isbn13": "9791387659776",
                        "url_amazon_afiliada": "https://www.amazon.es/Libro/dp/B0GB6LGQFH?tag=davidporto-21",
                        "formatos_compra": [{
                            "formato": "ebook",
                            "url": "https://www.amazon.es/dp/B08CYCPBZN?tag=davidporto-21",
                            "fuente_url": "https://www.amazon.es/dp/B0GB6LGQFH",
                        }],
                    },
                    {
                        "slug": "dos",
                        "titulo": "Pendiente",
                        "estado": "publicado",
                        "isbn13": "9788498382372",
                        "amazon_busqueda_isbn": "https://www.amazon.es/s?k=9788498382372&tag=davidporto-21",
                    },
                ]
            }
            (root / "data/reading-catalogue.json").write_text(
                json.dumps(catalogue), encoding="utf-8"
            )
            result = audit_module.audit(root, "davidporto-21")
            self.assertEqual(result["counts"]["published_books"], 2)
            self.assertEqual(result["counts"]["book_only_search"], 1)
            self.assertEqual(result["product_verification_queue"][0]["slug"], "dos")
            self.assertEqual(len(result["errors"]), 0)
            self.assertEqual(len([
                entry for entry in result["manual_review"]
                if entry["type"] == "fuente_ASIN_diferente"
            ]), 1)

    def test_tag_distinto_se_detecta(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data").mkdir()
            (root / "index.html").write_text(
                '<a href="https://www.amazon.es/dp/B0GB6LGQFH?tag=otro-21">Comprar</a>',
                encoding="utf-8",
            )
            (root / "data/reading-catalogue.json").write_text(
                '{"libros":[]}', encoding="utf-8"
            )
            result = audit_module.audit(root, "davidporto-21")
            self.assertEqual(len(result["errors"]), 1)
            self.assertEqual(result["errors"][0]["type"], "missing_or_wrong_tag")


if __name__ == "__main__":
    unittest.main()
