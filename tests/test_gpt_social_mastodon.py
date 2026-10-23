"""Offline tests. No network, credentials, Actions or writes outside temp directories."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "scripts/research/gpt_social_mastodon.py"
spec = importlib.util.spec_from_file_location("gpt_social_mastodon", MODULE)
ms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ms)

ACCOUNT = {"id": "123456", "username": "davidportodiaz", "acct": "davidportodiaz",
           "url": "https://mastodon.social/@davidportodiaz", "followers_count": 23, "statuses_count": 0}
VALID = {"accounts": [ACCOUNT], "statuses": [], "hashtags": []}


class MastodonContractTests(unittest.TestCase):
    def test_valid_and_no_impressions(self):
        result = ms.normalize_search(VALID, expected_id="123456", observed_at="2026-10-22T12:00:00Z")
        self.assertEqual((result["followers"], result["posts"], result["status"]), (23, 0, "ok"))
        self.assertIsNone(result["impressions_30d"])
        self.assertEqual(result["observed_at"], "2026-10-22T12:00:00Z")

    def test_missing_followers_is_null(self):
        result = ms.normalize_search({"accounts": [{k:v for k,v in ACCOUNT.items() if k!="followers_count"}]})
        self.assertIsNone(result["followers"])
        self.assertEqual(result["status"], "partial")

    def test_zero_is_valid(self):
        self.assertEqual(ms.count_or_none(0), 0)

    def test_invalid_counters(self):
        for value in (-1, True, "3", 3.5, [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ms.normalize_search({"accounts": [{**ACCOUNT, "followers_count": value}]})

    def test_accounts_array_required(self):
        for response in ([], {}, {"accounts": None}, {"accounts": "bad"}):
            with self.subTest(response=response), self.assertRaises(ValueError):
                ms.normalize_search(response)

    def test_ignore_similarly_named_account(self):
        another = {**ACCOUNT, "url": "https://mastodon.example/@davidportodiaz", "acct": "davidportodiaz@mastodon.example"}
        self.assertEqual(ms.normalize_search({"accounts": [another, ACCOUNT]})["account_id"], "123456")

    def test_no_exact_match_fails(self):
        with self.assertRaises(ValueError):
            ms.normalize_search({"accounts": [{**ACCOUNT, "url": "https://evil.example/@davidportodiaz"}]})

    def test_malformed_identity_fields_rejected(self):
        for key, value in (("username", None), ("acct", 5), ("url", [])):
            with self.subTest(field=key), self.assertRaises(ValueError):
                ms.normalize_search({"accounts": [{**ACCOUNT, key: value}]})

    def test_duplicate_canonical_fails(self):
        with self.assertRaises(ValueError):
            ms.normalize_search({"accounts": [ACCOUNT, ACCOUNT]})

    def test_changed_id_fails(self):
        with self.assertRaises(ValueError):
            ms.normalize_search(VALID, expected_id="other")

    def test_unexpected_url_parameters_fail(self):
        for suffix in ("?x=1", "#foo", ":99", "/impersonator"):
            with self.subTest(suffix=suffix):
                obj={**ACCOUNT,"url":ACCOUNT["url"]+suffix}
                with self.assertRaises(ValueError):
                    ms.normalize_search({"accounts":[obj]})

    def test_one_get_no_auth_no_resolve(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, n): return json.dumps(VALID).encode()
        with patch.object(ms, "urlopen", return_value=Response()) as caller:
            self.assertEqual(ms.request_public_search(), VALID)
            self.assertEqual(caller.call_count, 1)
            request=caller.call_args.args[0]
            self.assertIn("type=accounts",request.full_url)
            self.assertNotIn("resolve",request.full_url)
            self.assertNotIn("Authorization",request.headers)

    def test_oversize_rejected(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,n): return b"x"*n

        with patch.object(ms, "urlopen", return_value=Response()), self.assertRaises(ValueError):
            ms.request_public_search()

    def test_preserve_last_good_on_identity_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/"metrics.json"
            target.write_text('{"previous": true}')
            with patch.object(ms,"request_public_search",return_value={"accounts": [{**ACCOUNT,"id":"changed"}]}), redirect_stderr(io.StringIO()):
                self.assertEqual(ms.main(["--expected-id","123456","--output",str(target)]),1)
            self.assertEqual(json.loads(target.read_text()),{"previous":True})

    def test_preserve_on_missing_metric(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/"metrics.json"
            target.write_text('{"previous": true}')
            altered={k:v for k,v in ACCOUNT.items() if k!="followers_count"}
            with patch.object(ms,"request_public_search",return_value={"accounts":[altered]}), redirect_stderr(io.StringIO()):
                self.assertEqual(ms.main(["--expected-id","123456","--output",str(target)]),1)
            self.assertEqual(json.loads(target.read_text()),{"previous":True})

    def test_output_requires_verified_id(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            ms.main(["--output","/tmp/not-created.json"])

    def test_fixture_no_output(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture=Path(temp)/"fixture.json"
            fixture.write_text(json.dumps(VALID))
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(ms.main(["--fixture",str(fixture)]),0)
            self.assertEqual(json.loads(output.getvalue())["followers"],23)
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                ms.main(["--fixture",str(fixture),"--output",str(Path(temp)/"no.json")])

    def test_atomic_output_from_mock(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/"metrics.json"
            with patch.object(ms,"request_public_search",return_value=VALID):
                self.assertEqual(ms.main(["--expected-id","123456","--output",str(target)]),0)
            self.assertEqual(json.loads(target.read_text())["followers"],23)

if __name__ == "__main__":
    unittest.main()
