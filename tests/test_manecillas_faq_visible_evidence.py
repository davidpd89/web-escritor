import html
import json
import re
import unicodedata
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'las-manecillas-del-recuerdo/kindle/index.html').read_text(encoding='utf-8')


def normalise(value):
    value = html.unescape(re.sub(r'<[^>]*>', ' ', value)).casefold()
    value = ''.join(c for c in unicodedata.normalize('NFD', value) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', ' ', value).strip()


class FAQEvidence(unittest.TestCase):
    def test_schema_questions_have_visible_counterparts(self):
        scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>', SOURCE, re.S)
        pages = [node for script in scripts for node in json.loads(script).get('@graph', []) if node.get('@type') == 'WebPage']
        self.assertEqual(len(pages), 1)
        faq = pages[0]['mainEntity']
        self.assertEqual(faq['@type'], 'FAQPage')
        questions = faq['mainEntity']
        block = re.search(r'<section[^>]+id="preguntas".*?</section>', SOURCE, re.S)
        self.assertIsNotNone(block)
        visible_questions = [normalise(value) for value in re.findall(r'<dt>(.*?)</dt>', block.group(), re.S)]
        self.assertEqual(len(questions), len(visible_questions))
        for question in questions:
            self.assertEqual(question['@type'], 'Question')
            self.assertIn(normalise(question['name']), visible_questions, f"Pregunta estructurada sin evidencia visible: {question['name']}")
            self.assertTrue(question['acceptedAnswer']['text'].strip())


if __name__ == '__main__':
    unittest.main()
