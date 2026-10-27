"""A lease timeout must never evict a process that still owns the PID."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/research'))
import gpt_social_refresh as refresh


class LockLivenessTests(unittest.TestCase):
    def test_age_does_not_evict_live_owner(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {'SOCIAL_STATE_DIR': d}):
            first = refresh.acquire_lock()
            self.assertIsNotNone(first)
            self.addCleanup(first.unlink, missing_ok=True)
            old = refresh.time.time() - refresh.STALE_LOCK_SECONDS - 5
            os.utime(first, (old, old))
            with mock.patch.object(refresh, '_pid_alive', return_value=True):
                self.assertIsNone(refresh.acquire_lock(), 'A second worker stole a live PID lock')
            self.assertEqual(first.read_text().strip(), str(os.getpid()))


if __name__ == '__main__':
    unittest.main()
