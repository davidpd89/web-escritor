"""Tests aislados del auditor de enlaces; no requieren servicios externos."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit-reader-engagement-links.py"
spec = importlib.util.spec_from_file_location("reader_engagement_audit", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class AuditLinksTest(unittest.TestCase):
    def test_real_review_calls_are_detected(self):
        html = """
        <a href="https://www.amazon.es/dp/ASIN#customerReviews">
          Dejar reseña en Amazon
        </a>
        <a href="https://www.goodreads.com/book/show/123">Valorar en Goodreads</a>
        <a href="https://www.casadellibro.com/libro-x/123">
          Escribir reseña
        </a>"""
        r = module.analyse_html(html)
        self.assertEqual(len(r["ctas"]["amazon_review"]), 1)
        self.assertEqual(len(r["ctas"]["goodreads_review"]), 1)
        self.assertEqual(len(r["ctas"]["casa_review"]), 1)
        self.assertEqual(len(r["amazon_review_links_also_match_purchase_listener"]), 1)

    def test_product_link_and_profile_link_not_reviews(self):
        html = """
        <a href="https://www.amazon.es/dp/ASIN">Comprar libro</a>
        <a href="https://www.goodreads.com/author/show/123">Goodreads</a>
        <a href="https://www.amazon.es/dp/ASIN#customerReviews">Ver reseñas</a>"""
        r = module.analyse_html(html)
        self.assertFalse(r["ctas"]["amazon_review"])
        self.assertFalse(r["ctas"]["goodreads_review"])
        self.assertFalse(r["amazon_review_links_also_match_purchase_listener"])

    def test_follow_requires_real_author_destination_and_call_to_action(self):
        html = """
        <a href="https://www.amazon.es/stores/author/B0GZFP1JV3">
          Seguir al autor en Amazon
        </a>
        <a href="https://www.amazon.es/stores/author/B0GZFP1JV3">Ver autor</a>
        <a href="https://example.com/stores/author/B0GZFP1JV3">Seguir autor</a>"""
        r = module.analyse_html(html)
        self.assertEqual(len(r["ctas"]["amazon_follow"]), 1)

    def test_aria_label_used_when_anchor_has_icon(self):
        html = (
            '<a href="https://www.amazon.es/dp/ASIN#customerReviews" '
            'aria-label="Dejar reseña en Amazon"><svg></svg></a>'
        )
        r = module.analyse_html(html)
        self.assertEqual(len(r["ctas"]["amazon_review"]), 1)


if __name__ == "__main__":
    unittest.main()
