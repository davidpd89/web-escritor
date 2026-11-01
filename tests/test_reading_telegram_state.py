"""Remote delivery claims are durable before Telegram is called; no network."""

import base64
from datetime import date
import json
import hashlib
import hmac
from pathlib import Path
import sys
import tempfile
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


if __name__ == "__main__":
    unittest.main()
