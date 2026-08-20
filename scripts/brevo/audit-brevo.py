#!/usr/bin/env python3
"""Read-only Brevo account audit: lists, contact attributes, campaigns,
templates, automation. No writes, no sends, no deletes.

Reads BREVO_API_KEY from the environment or a local, git-ignored
.env.local at the repo root (same convention as
scripts/openai/generate-image.py). Never prints the key.

Usage:
  python scripts/brevo/audit-brevo.py

Estado verificado (20/08/2026): la auditoria SI ha llegado a ejecutarse con
exito desde la maquina de David. Resultado real de esa ejecucion:
lista canonica ID 3 "Lectores web" (2 suscriptores), lista ID 4
"identified_contacts" (0), 8 plantillas incluidas Bienvenida_Samuel_* y
Automatizacion #2_step_*, y se creo el atributo de contacto SOURCE.

Cuidado con el 401 "unrecognised IP address": la cuenta tiene lista blanca de
IPs y la IPv6 domestica de David ROTA el sufijo dentro del mismo prefijo /64
(se han visto 2a0c:5a81:b502:2c00:353a:... y 2a0c:5a81:b502:2c00:dda4:...).
Autorizar una sola IP solo funciona hasta la siguiente rotacion; hay que
autorizar el prefijo /64 en app.brevo.com/security/authorised_ips. Un 401 con
ese mensaje no es un fallo de este script ni algo reintentable: la peticion no
llega siquiera a autenticarse.

Las automatizaciones (Automation) siguen siendo un gate aparte: la API v3 REST
no las expone (probadas /automation/emails y /automation/workflows, ambas 404),
asi que para saber si al alta en la lista 3 se le entrega algo hay que mirarlo
en el panel de Brevo.
"""
from __future__ import annotations

import io
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

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
        # Deliberately minimal: never print marketingAutomation.key, address,
        # or SMTP relay credentials - treat the full /account payload as
        # sensitive even though this key only grants read-mostly access.
        print(json.dumps({"plan": data.get("plan")}, ensure_ascii=False))
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
    list_ids = []
    for l in data.get("lists", []) if status == 200 else []:
        list_ids.append(l.get("id"))
        print(f"  id={l.get('id')} name={l.get('name')!r} folderId={l.get('folderId')}")

    section("LIST DETAIL (reliable subscriber counts)")
    # The /contacts/lists listing endpoint's totalSubscribers has been seen
    # to report a stale/misleading 0 - always confirm via the per-list
    # detail endpoint before treating a count as real.
    for list_id in list_ids:
        status, l = call(key, f"/contacts/lists/{list_id}")
        if status == 200:
            print(f"  id={l.get('id')} name={l.get('name')!r} totalSubscribers={l.get('totalSubscribers')} uniqueSubscribers={l.get('uniqueSubscribers')}")
        else:
            print(f"  id={list_id} -> {status}")

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
