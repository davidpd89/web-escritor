import json
import re
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/radar-opportunities.json'
TODAY = date.today()

CURRENT = re.compile(
    r'\b(?:convocatoria oficial vigente|convocatoria vigente|'
    r'convocatoria oficial en plazo|en plazo de presentaci[oó]n)\b',
    re.IGNORECASE,
)
HISTORICAL = re.compile(
    r'\b(?:figuraba|constaba|estaba|estuvo|indicaba|indic[oó]|'
    r'cuando se verific[oó]|en su momento)\b',
    re.IGNORECASE,
)

class RadarEditorialDeadlineLanguage(unittest.TestCase):
    def test_closed_opportunities_do_not_claim_current_open_status(self):
        data = json.loads(DATA.read_text(encoding='utf-8'))
        failures = []
        checked = 0
        for item in data['items']:
            if not item.get('published'):
                continue
            deadline = date.fromisoformat(item['deadline'])
            if deadline >= TODAY:
                continue
            checked += 1
            note = item.get('editorial_note') or ''
            for sentence in re.split(r'(?<=[.!?])\s+', note):
                if CURRENT.search(sentence) and not HISTORICAL.search(sentence):
                    failures.append(
                        f"{item['id']}: deadline={deadline}; "
                        f"editorial_note={sentence!r}"
                    )
        self.assertGreater(checked, 0, 'No se han revisado convocatorias cerradas')
        self.assertFalse(
            failures,
            'data/radar-opportunities.json presenta convocatorias cerradas '
            'como vigentes:\n' + '\n'.join(failures),
        )

if __name__ == '__main__':
    unittest.main()
