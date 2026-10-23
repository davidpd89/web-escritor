"""Verified brand identity gate: Metricool matches public author URLs for 4 networks."""
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
import unittest

SRC = Path(__file__).resolve().parents[1] / 'scripts/research/gpt_social_compose.py'
spec = importlib.util.spec_from_file_location('verified_social', SRC)
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)
NOW = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)


def batch():
    names = ('bluesky', 'threads', 'instagram', 'facebook',
             'tiktok', 'pinterest', 'youtube', 'twitter')
    return {'kind': 'metricool-follower-candidates', 'schema_version': 1,
            'requested_day': '2026-10-21', 'generated_at': '2026-10-22T12:00:00Z',
            'records': [{'id': name, 'followers': 100 + i,
                         'source': 'metricool-mcp-export',
                         'observed_at': '2026-10-21', 'status': 'ok'}
                        for i, name in enumerate(names)]}


class VerifiedSocialTests(unittest.TestCase):
    def test_four_confirmed_metricool_networks_selected(self):
        public = sc.compose([batch()], now=NOW)
        self.assertEqual(public['totals']['coverage'], 4)
        self.assertEqual(public['totals']['eligible'], 6)
        self.assertEqual(public['totals']['follower_relationships'], 101 + 102 + 104 + 105)

    def test_uncorroborated_pages_excluded(self):
        public = sc.compose([batch()], now=NOW)
        names = [item['id'] for item in public['networks']]
        self.assertEqual(names, ['bluesky', 'mastodon', 'threads',
                                 'instagram', 'tiktok', 'pinterest'])
        for unverified in ('facebook', 'twitter', 'youtube'):
            self.assertNotIn(unverified, names)

    def test_bluesky_not_doubled_with_metricool_field(self):
        appview = {'id': 'bluesky', 'followers': 8,
                   'source': 'bluesky-public-appview', 'status': 'ok',
                   'observed_at': '2026-10-22T11:00:00Z'}
        public = sc.compose([batch(), appview], now=NOW)
        self.assertEqual(public['totals']['follower_relationships'], 420)
        self.assertEqual(public['totals']['coverage'], 5)

    def test_explicit_providers_for_each_new_network(self):
        for network in ('instagram', 'tiktok', 'pinterest'):
            source = {'id': network, 'followers': 3, 'observed_at': '2026-10-21',
                      'status': 'ok', 'source': 'metricool-mcp-export'}
            self.assertEqual(sc.compose([source], now=NOW)['totals']['coverage'], 1)

    def test_reject_mislabelled_provider(self):
        source = {'id': 'instagram', 'followers': 3,
                  'observed_at': '2026-10-21', 'status': 'ok',
                  'source': 'bluesky-public-appview'}
        with self.assertRaisesRegex(ValueError, 'wrong provider'):
            sc.compose([source], now=NOW)

    def test_urls_pinned_to_author_website(self):
        self.assertEqual(sc.PROFILES['instagram'], 'https://www.instagram.com/davidportodiaz/')
        self.assertEqual(sc.PROFILES['tiktok'], 'https://www.tiktok.com/@davidportoescritor')
        self.assertEqual(sc.PROFILES['pinterest'], 'https://www.pinterest.com/davidportodiaz/')

    def test_reject_wrong_url(self):
        source = {'id': 'tiktok', 'followers': 3,
                  'profile_url': 'https://www.tiktok.com/@another',
                  'observed_at': '2026-10-21', 'status': 'ok',
                  'source': 'metricool-mcp-export'}
        with self.assertRaisesRegex(ValueError, 'official link'):
            sc.compose([source], now=NOW)

    def test_ignored_metrics_do_not_become_visits(self):
        source = batch()
        source['records'][4]['views_30d'] = 99999
        with self.assertRaisesRegex(ValueError, 'Unverified period'):
            sc.compose([source], now=NOW)

    def test_null_one_network_keeps_three_others(self):
        source = batch()
        source['records'][2]['followers'] = None
        source['records'][2]['observed_at'] = None
        public = sc.compose([source], now=NOW)
        self.assertEqual(public['totals']['coverage'], 3)
        self.assertEqual(public['totals']['follower_relationships'], 101 + 104 + 105)

    def test_expired_accounts_drop_out_independently(self):
        source = batch()
        source['records'][5]['observed_at'] = '2026-10-17'
        source['requested_day'] = '2026-10-21'
        with self.assertRaisesRegex(ValueError, 'date differs'):
            sc.compose([source], now=NOW)


if __name__ == '__main__':
    unittest.main()
