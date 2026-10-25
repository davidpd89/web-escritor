import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TestRegistration(unittest.TestCase):
    def test_registration_contract(self):
        src = (ROOT / 'script.js').read_text(encoding='utf-8')
        register = src.find('navigator.serviceWorker.register(')
        self.assertGreaterEqual(register, 0)
        preceding = src[max(0, register - 350):register]
        following = src[register:register + 120]
        self.assertIn('"serviceWorker" in navigator', preceding)
        self.assertIn('window.addEventListener("load"', preceding)
        self.assertIn('scheduleTask(', preceding)
        self.assertIn('.catch(', following)

if __name__ == '__main__':
    unittest.main()