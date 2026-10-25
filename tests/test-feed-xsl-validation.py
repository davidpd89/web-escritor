#!/usr/bin/env python3
"""Validación de la dependencia XSL del RSS."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_xsl_qa', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class XSLValidation(unittest.TestCase):
    def test_committed_xsl_is_valid(self):
        errors = []
        feed.validate_xsl_asset(errors)
        self.assertEqual(errors, [])

    def test_missing_xsl_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(feed, 'XSL_PATH', str(Path(tmp) / 'missing.xsl')):
                errors = []
                feed.validate_xsl_asset(errors)
                self.assertTrue(errors)

    def test_malformed_xsl_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'broken.xsl'
            path.write_text('<xsl:stylesheet><broken>', encoding='utf-8')
            with patch.object(feed, 'XSL_PATH', str(path)):
                errors = []
                feed.validate_xsl_asset(errors)
                self.assertTrue(errors)

    def test_valid_xml_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'valid.xsl'
            path.write_text('<stylesheet/>', encoding='utf-8')
            with patch.object(feed, 'XSL_PATH', str(path)):
                errors = []
                feed.validate_xsl_asset(errors)
                self.assertEqual(errors, [])

if __name__ == '__main__':
    unittest.main()
