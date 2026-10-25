import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class BrowserServerLifecycle(unittest.TestCase):
    def test_server_startup_has_cleanup(self):
        workflow = (ROOT / '.github/workflows/content-parity-manecillas.yml').read_text(encoding='utf-8')
        self.assertRegex(workflow, r'python3?\s+-m\s+http\.server\s+4173')
        self.assertRegex(workflow, r'curl\s+--fail\s+--silent')
        self.assertRegex(workflow, r'(?m)^\s*timeout-minutes:\s*[1-9][0-9]*')
        self.assertRegex(workflow, r'(?m)^\s*trap\s+.*(?:EXIT|TERM)|(?:kill|pkill)\s+.*(?:SERVER_PID|server_pid)|(?:docker\s+stop)')

if __name__ == '__main__':
    unittest.main()