#!/usr/bin/env python3
"""Regression tests for the sanitized Brevo account snapshot."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "brevo" / "snapshot-brevo.py"
spec = importlib.util.spec_from_file_location("brevo_snapshot", SCRIPT)
assert spec and spec.loader
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)


def main() -> None:
    calls: list[str] = []

    def fake_get(path: str, _api_key: str):
        calls.append(path)
        if path == "contacts/lists?limit=50":
            # This deliberately models Brevo's 2026 deprecation: collection
            # totalSubscribers can be 0 even when the detail endpoint is not.
            return {
                "count": 2,
                "lists": [
                    {"id": 3, "name": "Lectores web", "totalSubscribers": 0},
                    {"id": 6, "name": "Lectores beta", "totalSubscribers": 0},
                ],
            }
        if path == "contacts/lists/3":
            return {"id": 3, "name": "Lectores web", "totalSubscribers": 2}
        if path == "contacts/lists/6":
            return {"_error": True, "status": 503, "body": "temporary"}
        raise AssertionError(f"unexpected API call: {path}")

    original = snapshot.api_get
    snapshot.api_get = fake_get
    try:
        rows = snapshot.collect_lists("test-key", include_contacts=True)
        assert isinstance(rows, list)
        assert rows[0]["totalSubscribers"] == 2
        assert rows[0]["subscriberCountStatus"] == "verified-list-detail"
        assert rows[1]["totalSubscribers"] is None
        assert rows[1]["subscriberCountStatus"] == "unavailable"
        assert "contacts/lists/3" in calls and "contacts/lists/6" in calls

        rendered = snapshot.render_sanitized({
            "generatedAt": "2026-08-27T00:00:00+00:00",
            "account": {},
            "lists": rows,
            "domains": [],
            "senders": [],
            "templates": [],
            "recentCampaigns": [],
            "recentCampaignsCount": 0,
            "webhooks": {"note": "none configured"},
            "crmPipelines": [],
            "contactAttributes": [],
        })
        assert "Lectores web — 2 suscriptores (detalle de lista)" in rendered
        assert "Lectores beta — suscriptores: desconocido" in rendered
        assert "Lectores beta — 0 suscriptores" not in rendered

        calls.clear()
        rows_without_counts = snapshot.collect_lists("test-key", include_contacts=False)
        assert all(row["subscriberCountStatus"] == "omitted" for row in rows_without_counts)
        assert all(not path.startswith("contacts/lists/") for path in calls if path != "contacts/lists?limit=50")
    finally:
        snapshot.api_get = original

    print("OK: Brevo snapshot count contract regression tests passed.")


if __name__ == "__main__":
    main()
