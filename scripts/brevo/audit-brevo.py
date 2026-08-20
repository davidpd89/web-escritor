#!/usr/bin/env python3
"""Read-only Brevo account audit: lists, contact attributes, campaigns,
templates, automation. No writes, no sends, no deletes.

Reads BREVO_API_KEY from the environment or a local, git-ignored
.env.local at the repo root (same convention as
scripts/openai/generate-image.py). Never prints the key.

Usage:
  python scripts/brevo/audit-brevo.py

Known gate (2026-08-20): Brevo blocks API calls - including this
read-only audit - from IP addresses not on the account's authorized-IP
allowlist, returning 401 "unrecognised IP address" for every endpoint.
This is an account security setting, not a bug here. It must be resolved
by the account owner at https://app.brevo.com/security/authorised_ips
(or by disabling IP allowlisting) before this script can return real
data. There is nothing to retry from the calling side - a 401 with that
exact message means the request never reached authentication logic.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API = "https://api.brevo.com/v3"


def load_env_local() -> None:
    if os.environ.get("BREVO_API_KEY"):
        return
    env_path = ROOT / ".env.local"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def call(key: str, path: str):
    req = urllib.request.Request(
        API + path,
        method="GET",
        headers={"api-key": key, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = {}
        return e.code, body
    except urllib.error.URLError as e:
        return None, {"message": str(e.reason)}


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    load_env_local()
    key = os.environ.get("BREVO_API_KEY")
    if not key:
        print("BREVO_API_KEY not configured in environment or .env.local. Aborting.")
        return 1

    section("ACCOUNT")
    status, data = call(key, "/account")
    print(status)
    if status == 200:
        print(json.dumps({k: data.get(k) for k in ("email", "companyName", "plan")}, ensure_ascii=False))
    else:
        print(json.dumps(data, ensure_ascii=False)[:1000])
        if status == 401 and "unrecognised IP" in json.dumps(data):
            print(
                "\nGATE: this IP is not authorized on the Brevo account. "
                "Authorize it at https://app.brevo.com/security/authorised_ips "
                "then re-run this script. Aborting rest of audit.",
                file=sys.stderr,
            )
            return 2

    section("LISTS")
    status, data = call(key, "/contacts/lists?limit=50&offset=0")
    print(status)
    for l in data.get("lists", []) if status == 200 else []:
        print(f"  id={l.get('id')} name={l.get('name')!r} totalSubscribers={l.get('totalSubscribers')} folderId={l.get('folderId')}")

    section("CONTACT ATTRIBUTES")
    status, data = call(key, "/contacts/attributes")
    print(status)
    for a in data.get("attributes", []) if status == 200 else []:
        print(f"  name={a.get('name')!r} category={a.get('category')} type={a.get('type')}")

    section("EMAIL CAMPAIGNS")
    status, data = call(key, "/emailCampaigns?limit=50")
    print(status)
    for c in data.get("campaigns", []) if status == 200 else []:
        print(f"  id={c.get('id')} name={c.get('name')!r} status={c.get('status')}")

    section("TEMPLATES")
    status, data = call(key, "/smtp/templates?limit=50")
    print(status)
    for t in data.get("templates", []) if status == 200 else []:
        print(f"  id={t.get('id')} name={t.get('name')!r} isActive={t.get('isActive')}")

    section("AUTOMATION")
    for path in ("/automation/emails", "/automation/workflows"):
        status, data = call(key, path)
        print(path, "->", status, json.dumps(data, ensure_ascii=False)[:400])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
