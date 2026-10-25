import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / 'qa/cls-trace.mjs').read_text(encoding='utf-8')


class CLSProfileCoverageTests(unittest.TestCase):
    def test_both_public_identity_routes_are_measured(self):
        self.assertIn("'/autor.html'", SOURCE)
        self.assertIn("'/prensa.html'", SOURCE)

    def test_mobile_and_desktop_profiles_exist(self):
        self.assertIn("name: 'lh-mobile'", SOURCE)
        self.assertIn("name: 'desktop'", SOURCE)
        self.assertIn('width: 412', SOURCE)
        self.assertIn('width: 1350', SOURCE)

    def test_each_profile_is_exercised_for_each_route(self):
        self.assertIn('for (const route of routes)', SOURCE)
        self.assertIn('for (const profile of profiles)', SOURCE)
        self.assertIn('viewport: { width: profile.width, height: profile.height }', SOURCE)


if __name__ == '__main__':
    unittest.main()
