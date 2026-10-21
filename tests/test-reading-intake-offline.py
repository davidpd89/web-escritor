"""Keep the editorial intake contracts inside the required universal merge gate."""
import unittest
from pathlib import Path

suite = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent), pattern='test_reading*.py')
result = unittest.TextTestRunner(verbosity=1).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
