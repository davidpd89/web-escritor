import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = (ROOT / '.github/workflows/reading-pinterest-rss-qa.yml').read_text(encoding='utf-8')


class PinterestFrozenClock(unittest.TestCase):
    def test_every_generation_uses_same_date(self):
        commands = [line.strip() for line in TEXT.splitlines() if re.search(r'python\s+scripts/(?:build-reading-pinterest-rss|export-reading-pinterest-plan)\.py\s', line)]
        self.assertGreaterEqual(len(commands), 4)
        dates = []
        for command in commands:
            match = re.search(r'--today\s+(\d{4}-\d{2}-\d{2})', command)
            self.assertIsNotNone(match, f'Fecha implícita: {command}')
            dates.append(match.group(1))
        self.assertEqual(len(set(dates)), 1, f'Fechas distintas: {dates}')


if __name__ == '__main__':
    unittest.main()