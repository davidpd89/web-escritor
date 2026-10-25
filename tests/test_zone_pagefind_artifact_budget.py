#!/usr/bin/env python3
"""Presupuesto preventivo del índice Pagefind publicado.

Los límites deben calibrarse con las mediciones del artefacto de referencia.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'pagefind'
MAX_TOTAL = 32 * 1024 * 1024
MAX_ENTRY = 512 * 1024


class PagefindArtifactBudget(unittest.TestCase):
    def test_index_has_bounded_disk_size(self):
        self.assertTrue(INDEX.is_dir(), 'pagefind/: falta el directorio del índice generado')
        files = [p for p in INDEX.rglob('*') if p.is_file()]
        self.assertTrue(files, 'pagefind/: el índice no contiene archivos')
        total = sum(p.stat().st_size for p in files)
        self.assertLessEqual(
            total, MAX_TOTAL,
            f'pagefind/: peso total {total} bytes; presupuesto {MAX_TOTAL} bytes',
        )

    def test_entry_module_has_bounded_size(self):
        entry = INDEX / 'pagefind.js'
        self.assertTrue(entry.is_file(), 'pagefind/pagefind.js: falta el módulo de búsqueda')
        size = entry.stat().st_size
        self.assertLessEqual(
            size, MAX_ENTRY,
            f'pagefind/pagefind.js: {size} bytes; presupuesto {MAX_ENTRY} bytes',
        )


if __name__ == '__main__':
    unittest.main()
