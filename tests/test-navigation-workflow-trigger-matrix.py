import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def paths_for(workflow, event):
    text = (ROOT / '.github/workflows' / workflow).read_text(encoding='utf-8')
    match = re.search(rf'(?m)^  {re.escape(event)}:\s*\n    paths:\s*\n((?:      - [^\n]+\n)+)', text)
    if not match:
        return None
    return set(re.findall(r"(?m)^\s*-\s*['\"]([^'\"]+)['\"]", match.group(1)))


class NavigationWorkflowTriggers(unittest.TestCase):
    def test_home_navigation_runtime_triggers_browser_qa(self):
        paths = paths_for('home-map-interaction-qa.yml', 'pull_request')
        self.assertIsNotNone(paths)
        for dependency in ('index.html', 'assets/v1-home.css', 'assets/v1-shell.js', 'assets/v1-editorial-interior-v4.js', 'qa/home-map-interaction.mjs'):
            with self.subTest(dependency=dependency):
                self.assertIn(dependency, paths)

    def test_reading_navigation_data_triggers_pr_and_push(self):
        for event in ('pull_request', 'push'):
            paths = paths_for('navigation-roundtrip-audit.yml', event)
            self.assertIsNotNone(paths)
            for dependency in ('data/navigation.json', 'data/content-registry.json', 'data/reading-catalogue.json', 'data/reading-authors.json', 'qa/reading-navigation-roundtrips.mjs'):
                with self.subTest(event=event, dependency=dependency):
                    self.assertIn(dependency, paths)


if __name__ == '__main__':
    unittest.main()