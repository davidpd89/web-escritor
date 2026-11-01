"""Durable CAS checkpoints on a dedicated GitHub branch.

Only domain-separated HMAC identifiers and delivery status leave the runner.
Channel IDs, ASINs, tokens, message IDs and invitation links are never exported.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path

import requests


class GitHubState:
    def __init__(
        self, repository, github_token, state_key, namespace="daily", session=None
    ):
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository) or namespace not in {
            "daily",
            "smoke",
        }:
            raise ValueError("Invalid state repository or namespace")
        self.url = f"https://api.github.com/repos/{repository}/contents/state.json"
        self.headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
        }
        self.branch = "automation/telegram-delivery-state"
        if len(state_key) < 32:
            raise ValueError("A stable private state key is required")
        self.secret = state_key.encode()
        self.key_check = hmac.new(
            self.secret, b"telegram-delivery-store-v1", hashlib.sha256
        ).hexdigest()
        self.namespace = namespace
        self.session = session or requests.Session()
        self.sha = None
        self.entries = {}

    def key(self, chat, asin):
        payload = json.dumps(
            ["telegram-delivery-v1", self.namespace, chat, asin], separators=(",", ":")
        ).encode()
        return hmac.new(self.secret, payload, hashlib.sha256).hexdigest()

    def load(self):
        response = self.session.get(
            self.url, headers=self.headers, params={"ref": self.branch}, timeout=30
        )
        if response.status_code != 200:
            # A missing store must never be treated as a fresh, empty delivery history.
            raise RuntimeError("Remote delivery history unavailable")
        payload = response.json()
        data = json.loads(base64.b64decode(payload["content"], validate=False))
        if data.get("schema_version") != 1 or not isinstance(
            data.get("deliveries"), dict
        ):
            raise ValueError("Invalid remote delivery schema")
        if not hmac.compare_digest(data.get("key_check", ""), self.key_check):
            raise ValueError(
                "State key changed; restore the original key before sending"
            )
        for digest, status in data["deliveries"].items():
            if not re.fullmatch(r"[a-f0-9]{64}", digest) or not re.fullmatch(
                r"sent|sending|uncertain|rejected|retry:\d+", status
            ):
                raise ValueError("Invalid remote delivery entry")
        self.entries = data["deliveries"]
        self.sha = payload["sha"]
        return self

    def restore(self, db_path, catalog):
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(db_path)) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS deliveries (chat TEXT, asin TEXT, status TEXT, message_id INTEGER, PRIMARY KEY(chat, asin))"
            )
            for channel in catalog["channels"]:
                for book in catalog["books"]:
                    status = self.entries.get(
                        self.key(channel["chat_id"], book["asin"])
                    )
                    if status:
                        db.execute(
                            "INSERT OR IGNORE INTO deliveries VALUES (?, ?, ?, NULL)",
                            (channel["chat_id"], book["asin"], status),
                        )
            db.commit()

    def checkpoint(self, db_path):
        if not self.sha:
            raise RuntimeError("Load remote state before checkpointing")
        updated = dict(self.entries)
        with closing(sqlite3.connect(db_path)) as db:
            for chat, asin, status in db.execute(
                "SELECT chat, asin, status FROM deliveries"
            ):
                updated[self.key(chat, asin)] = status
        if updated == self.entries:
            return
        content = base64.b64encode(
            json.dumps(
                {
                    "schema_version": 1,
                    "key_check": self.key_check,
                    "deliveries": updated,
                },
                sort_keys=True,
            ).encode()
        ).decode()
        response = self.session.put(
            self.url,
            headers=self.headers,
            json={
                "message": "Checkpoint Telegram delivery state",
                "branch": self.branch,
                "sha": self.sha,
                "content": content,
            },
            timeout=30,
        )
        if response.status_code != 200:
            raise RuntimeError("Remote delivery checkpoint failed; sending is blocked")
        self.sha = response.json()["content"]["sha"]
        self.entries = updated


def remote_state(namespace="daily"):
    return GitHubState(
        os.environ["GITHUB_REPOSITORY"],
        os.environ["GITHUB_TOKEN"],
        os.environ["READING_TELEGRAM_STATE_KEY"],
        namespace,
    ).load()
