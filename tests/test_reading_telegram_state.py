"""Remote delivery claims are durable before Telegram is called; no network."""

import base64
from datetime import date
import json
import hashlib
import hmac
from pathlib import Path
import sys
import sqlite3
import tempfile
from contextlib import closing
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reading_telegram_state import GitHubState
from reading_telegram import run


class Session:
    def __init__(self):
        self.data = {
            "schema_version": 1,
            "deliveries": {},
            "key_check": hmac.new(
                ("private-stable-key-" * 3).encode(),
                b"telegram-delivery-store-v1",
                hashlib.sha256,
            ).hexdigest(),
        }
        self.sha = "initial"
        self.puts = []
        self.fail = False

    def get(self, *args, **kwargs):
        return Mock(
            status_code=200,
            json=lambda: {
                "sha": self.sha,
                "content": base64.b64encode(json.dumps(self.data).encode()).decode(),
            },
        )

    def put(self, *args, **kwargs):
        payload = kwargs["json"]
        if self.fail or payload["sha"] != self.sha:
            return Mock(status_code=409)
        self.data = json.loads(base64.b64decode(payload["content"]))
        self.puts.append(self.data)
        self.sha = str(len(self.puts))
        return Mock(status_code=200, json=lambda: {"content": {"sha": self.sha}})


class RemoteTelegramStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "state.db"
        self.session = Session()
        self.store = GitHubState(
            "owner/repo",
            "test-github-token",
            "private-stable-key-" * 3,
            session=self.session,
        ).load()
        self.catalog = {
            "channels": [{"chat_id": "private-channel", "token_env": "TEST_TOKEN"}],
            "books": [
                {
                    "asin": "B0HC3Y2XLT",
                    "release_date": "2026-11-01",
                    "title": "Book",
                    "author": "Author",
                }
            ],
        }

    def test_identifiers_are_private_and_namespaces_independent(self):
        digest = self.store.key("private-channel", "B0HC3Y2XLT")
        self.assertEqual(len(digest), 64)
        self.assertNotIn("private-channel", digest)
        smoke = GitHubState("owner/repo", "github", "private-stable-key-" * 3, "smoke")
        self.assertNotEqual(digest, smoke.key("private-channel", "B0HC3Y2XLT"))

    def test_durable_claim_then_complete_and_restore_after_restart(self):
        self.store.restore(self.db, self.catalog)

        def sender(*args):
            self.assertEqual(
                list(self.session.data["deliveries"].values()), ["sending"]
            )
            return "sent", 123

        with (
            patch.dict("os.environ", {"TEST_TOKEN": "test"}),
            patch("reading_telegram.time.sleep"),
        ):
            run(
                self.catalog,
                date(2026, 11, 1),
                self.db,
                True,
                sender=sender,
                checkpoint=self.store.checkpoint,
            )
        self.assertEqual(list(self.session.data["deliveries"].values()), ["sent"])
        exported = json.dumps(self.session.data)
        for private in ["private-channel", "B0HC3Y2XLT", "123", "test-github-token"]:
            self.assertNotIn(private, exported)
        fresh_db = self.db.with_name("fresh.db")
        restarted = GitHubState(
            "owner/repo", "github", "private-stable-key-" * 3, session=self.session
        ).load()
        restarted.restore(fresh_db, self.catalog)
        with patch.dict("os.environ", {"TEST_TOKEN": "test"}):
            result = run(
                self.catalog,
                date(2026, 11, 1),
                fresh_db,
                True,
                sender=Mock(side_effect=AssertionError("duplicate")),
                checkpoint=restarted.checkpoint,
            )
        self.assertEqual(result[0]["status"], "skipped:sent")

    def test_digest_delivery_survives_restart(self):
        catalog = {
            "channels": [
                {"chat_id": "private-channel", "token_env": "TEST_TOKEN", "mode": "digest"}
            ],
            "books": [{**self.catalog["books"][0], "isbn13": "9788498382372"}],
            "digests": ["digest-2026-11-01"],
        }
        self.store.restore(self.db, catalog)
        with (
            patch.dict("os.environ", {"TEST_TOKEN": "test"}),
            patch("reading_telegram.time.sleep"),
        ):
            run(catalog, date(2026, 11, 1), self.db, True,
                sender=Mock(return_value=("sent", 9)), checkpoint=self.store.checkpoint)
        restarted = GitHubState(
            "owner/repo", "github", "private-stable-key-" * 3, session=self.session
        ).load()
        fresh_db = self.db.with_name("fresh-digest.db")
        restarted.restore(fresh_db, catalog)
        with patch.dict("os.environ", {"TEST_TOKEN": "test"}):
            result = run(catalog, date(2026, 11, 1), fresh_db, True,
                         sender=Mock(side_effect=AssertionError("duplicate")),
                         checkpoint=restarted.checkpoint)
        self.assertEqual(result[0]["status"], "skipped:sent")

    def test_checkpoint_failure_blocks_http(self):
        self.store.restore(self.db, self.catalog)
        self.session.fail = True
        sender = Mock()
        with (
            patch.dict("os.environ", {"TEST_TOKEN": "test"}),
            self.assertRaises(RuntimeError),
        ):
            run(
                self.catalog,
                date(2026, 11, 1),
                self.db,
                True,
                sender=sender,
                checkpoint=self.store.checkpoint,
            )
        sender.assert_not_called()

    def test_missing_history_is_not_automatically_reset(self):
        bad = Mock(get=Mock(return_value=Mock(status_code=404)))
        with self.assertRaises(RuntimeError):
            GitHubState(
                "owner/repo", "github", "private-stable-key-" * 3, session=bad
            ).load()

    def test_accidental_key_rotation_cannot_reset_delivery_history(self):
        with self.assertRaises(ValueError):
            GitHubState(
                "owner/repo", "github", "different-key-" * 4, session=self.session
            ).load()

    def test_cas_conflict_never_overwrites_newer_state(self):
        self.store.restore(self.db, self.catalog)
        self.session.sha = "changed-by-another-writer"
        with (
            patch.dict("os.environ", {"TEST_TOKEN": "test"}),
            self.assertRaises(RuntimeError),
        ):
            run(
                self.catalog,
                date(2026, 11, 1),
                self.db,
                True,
                checkpoint=self.store.checkpoint,
            )
        self.assertEqual(self.session.puts, [])


    def test_transient_checkpoint_failures_are_retried(self):
        import requests
        self.store.restore(self.db, self.catalog)
        real_put = self.session.put
        failures = [requests.ConnectionError("boom"), Mock(status_code=502)]

        def flaky(*args, **kwargs):
            if failures:
                f = failures.pop(0)
                if isinstance(f, Exception):
                    raise f
                return f
            return real_put(*args, **kwargs)

        self.session.put = flaky
        with (
            patch.dict("os.environ", {"TEST_TOKEN": "test"}),
            patch("reading_telegram_state.time.sleep") as pause,  # same module as reading_telegram.time
        ):
            result = run(self.catalog, date(2026, 11, 1), self.db, True,
                         sender=Mock(return_value=("sent", 1)),
                         checkpoint=self.store.checkpoint)
        self.assertEqual(result[0]["status"], "sent")
        self.assertEqual([c.args for c in pause.call_args_list][:2], [(2,), (5,)])
        self.assertEqual(list(self.session.data["deliveries"].values()), ["sent"])

    def test_lost_response_after_landed_write_is_accepted(self):
        import requests
        self.store.restore(self.db, self.catalog)
        real_put = self.session.put
        calls = []

        def lost(*args, **kwargs):
            calls.append(1)
            if len(calls) == 1:
                real_put(*args, **kwargs)  # the write lands but the response never arrives
                raise requests.Timeout("lost")
            return real_put(*args, **kwargs)  # retry with the old sha -> 409

        self.session.put = lost
        with patch("reading_telegram_state.time.sleep"):
            with closing(sqlite3.connect(self.db)) as db:
                db.execute("CREATE TABLE IF NOT EXISTS deliveries (chat TEXT, asin TEXT, status TEXT, message_id INTEGER, PRIMARY KEY(chat, asin))")
                db.execute("INSERT INTO deliveries VALUES ('@c', 'A', 'sent', 1)")
                db.commit()
            self.store.checkpoint(self.db)
        self.assertEqual(len(calls), 2)
        self.assertEqual(self.store.sha, self.session.sha)

    def test_stale_sending_claim_becomes_uncertain_once_and_is_never_resent(self):
        self.store.restore(self.db, self.catalog)
        with patch.dict("os.environ", {"TEST_TOKEN": "test"}), self.assertRaises(RuntimeError):
            run(self.catalog, date(2026, 11, 1), self.db, True,
                sender=Mock(side_effect=RuntimeError()), checkpoint=self.store.checkpoint)
        self.assertEqual(list(self.session.data["deliveries"].values()), ["sending"])
        restarted = GitHubState("owner/repo", "github", "private-stable-key-" * 3,
                                session=self.session).load()
        fresh = self.db.with_name("after-crash.db")
        restarted.restore(fresh, self.catalog)
        sender = Mock(side_effect=AssertionError("duplicate"))
        with patch.dict("os.environ", {"TEST_TOKEN": "test"}):
            first = run(self.catalog, date(2026, 11, 1), fresh, True, sender=sender,
                        checkpoint=restarted.checkpoint)
            later = run(self.catalog, date(2026, 11, 1), fresh, True, sender=sender,
                        checkpoint=restarted.checkpoint)
        self.assertEqual([r["status"] for r in first], ["uncertain:stale-claim"])
        self.assertEqual([r["status"] for r in later], ["skipped:uncertain"])
        self.assertEqual(list(self.session.data["deliveries"].values()), ["uncertain"])
        sender.assert_not_called()

if __name__ == "__main__":
    unittest.main()
