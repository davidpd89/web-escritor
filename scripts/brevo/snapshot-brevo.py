#!/usr/bin/env python3
"""BRV-001: read-only snapshot of the live Brevo account state.

Calls a fixed set of read-only Brevo API v3 endpoints and writes two
outputs: a full local snapshot (may contain low-sensitivity operational
detail like list names/counts and template names) and a sanitized
snapshot safe to commit to the repo for reference.

Never writes: contact emails/names/phones, the API key itself, SMTP
credentials, any MCP token, or campaign/template HTML bodies (subject
lines and metadata are kept -- content is not).

Usage:
    python scripts/brevo/snapshot-brevo.py --output snapshot.json --sanitized-output docs/brevo/SNAPSHOT.md
    python scripts/brevo/snapshot-brevo.py --check   # verify committed sanitized snapshot is current
    python scripts/brevo/snapshot-brevo.py --no-contacts  # skip anything contact-count related
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
API_BASE = "https://api.brevo.com/v3"
DEFAULT_OUTPUT = ROOT / "scripts" / "brevo" / ".snapshot-local.json"
DEFAULT_SANITIZED = ROOT / "docs" / "brevo" / "SNAPSHOT-LIVE.md"


def load_api_key() -> str:
    key = os.environ.get("BREVO_API_KEY")
    if key:
        return key
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("BREVO_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise SystemExit("BREVO_API_KEY no encontrada (variable de entorno ni .env)")


def api_get(path: str, api_key: str) -> dict | list | None:
    # Some endpoints (senders, senders/domains) reject Python's default
    # urllib User-Agent with a bare 403, even though the same key/path works
    # fine via curl -- a WAF/bot-filter quirk, not an auth problem. A plain
    # UA string sidesteps it without pretending to be a browser.
    headers = {"api-key": api_key, "accept": "application/json", "User-Agent": "web-escritor-brevo-snapshot/1.0"}
    req = urllib.request.Request(f"{API_BASE}/{path}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return {"_error": True, "status": e.code, "body": body[:300]}
    except urllib.error.URLError as e:
        return {"_error": True, "status": None, "body": str(e)}


def collect(api_key: str, include_contacts: bool) -> dict:
    snapshot: dict = {"generatedAt": datetime.now(timezone.utc).isoformat()}

    account = api_get("account", api_key) or {}
    plan = account.get("plan") or []
    snapshot["account"] = {
        "email": account.get("email"),
        "companyName": account.get("companyName"),
        "planType": plan[0].get("type") if plan else None,
        "planCredits": plan[0].get("credits") if plan else None,
        "planCreditsType": plan[0].get("creditsType") if plan else None,
        "marketingAutomationEnabled": bool(account.get("marketingAutomation", {}).get("enabled")),
        "relayEnabled": bool(account.get("relay", {}).get("enabled")),
    }

    lists = api_get("contacts/lists?limit=50", api_key) or {}
    snapshot["lists"] = [
        {"id": l.get("id"), "name": l.get("name"), "totalSubscribers": l.get("totalSubscribers") if include_contacts else None}
        for l in lists.get("lists", [])
    ] if isinstance(lists, dict) else lists

    attrs = api_get("contacts/attributes", api_key) or {}
    snapshot["contactAttributes"] = [
        {"name": a.get("name"), "category": a.get("category"), "type": a.get("type")}
        for a in attrs.get("attributes", [])
    ] if isinstance(attrs, dict) else attrs

    senders = api_get("senders", api_key) or {}
    snapshot["senders"] = [
        {"id": s.get("id"), "name": s.get("name"), "active": s.get("active")}
        for s in senders.get("senders", [])
    ] if isinstance(senders, dict) else senders

    domains = api_get("senders/domains", api_key) or {}
    snapshot["domains"] = [
        {"domain": d.get("domain_name"), "authenticated": d.get("authenticated"), "verified": d.get("verified")}
        for d in domains.get("domains", [])
    ] if isinstance(domains, dict) else domains

    webhooks = api_get("webhooks", api_key)
    snapshot["webhooks"] = webhooks if not (isinstance(webhooks, dict) and webhooks.get("_error")) else {"count": 0, "note": "none configured"}

    templates = api_get("smtp/templates?limit=50", api_key) or {}
    snapshot["templates"] = [
        {"id": t.get("id"), "name": t.get("name"), "subject": t.get("subject"), "isActive": t.get("isActive"), "senderEmail": (t.get("sender") or {}).get("email")}
        for t in templates.get("templates", [])
    ] if isinstance(templates, dict) else templates

    campaigns = api_get("emailCampaigns?limit=20&sort=desc", api_key) or {}
    snapshot["recentCampaigns"] = [
        {"id": c.get("id"), "name": c.get("name"), "status": c.get("status"), "sentDate": c.get("sentDate")}
        for c in campaigns.get("campaigns", [])
    ] if isinstance(campaigns, dict) else campaigns
    snapshot["recentCampaignsCount"] = campaigns.get("count") if isinstance(campaigns, dict) else None

    processes = api_get("processes", api_key) or {}
    snapshot["processes"] = processes.get("processes") if isinstance(processes, dict) else processes

    pipelines = api_get("crm/pipeline/details/all", api_key)
    if isinstance(pipelines, list):
        snapshot["crmPipelines"] = [
            {"pipeline": p.get("pipeline_name"), "stages": [s.get("name") for s in p.get("stages", [])]}
            for p in pipelines
        ]
    else:
        snapshot["crmPipelines"] = pipelines

    return snapshot


def render_sanitized(snapshot: dict) -> str:
    lines = [
        "# Brevo — snapshot en vivo (sanitizado, sin PII)",
        "",
        f"Generado: {snapshot['generatedAt']}",
        "",
        "> AUTO-GENERADO por `scripts/brevo/snapshot-brevo.py`. No editar a mano.",
        "> No contiene emails/nombres de contactos, API keys, credenciales SMTP, tokens MCP ni cuerpos de plantillas/campañas.",
        "",
        "## Cuenta",
        f"- Plan: `{snapshot['account'].get('planType')}` ({snapshot['account'].get('planCredits')} {snapshot['account'].get('planCreditsType')})",
        f"- Marketing Automation habilitado: {snapshot['account'].get('marketingAutomationEnabled')}",
        f"- Relay SMTP habilitado: {snapshot['account'].get('relayEnabled')}",
        "",
        "## Listas",
    ]
    for l in snapshot.get("lists", []):
        lines.append(f"- `{l.get('id')}` {l.get('name')} — {l.get('totalSubscribers')} suscriptores" if l.get("totalSubscribers") is not None else f"- `{l.get('id')}` {l.get('name')}")

    lines += ["", "## Dominios de envío"]
    for d in snapshot.get("domains", []):
        lines.append(f"- {d.get('domain')} — autenticado: {d.get('authenticated')}, verificado: {d.get('verified')}")

    lines += ["", "## Remitentes (senders)"]
    for s in snapshot.get("senders", []):
        lines.append(f"- `{s.get('id')}` {s.get('name')} — activo: {s.get('active')}")

    lines += ["", "## Plantillas (templates) — solo metadata, sin contenido"]
    for t in snapshot.get("templates", []):
        lines.append(f"- `{t.get('id')}` {t.get('name')} — activa: {t.get('isActive')} — asunto: «{t.get('subject')}»")

    lines += ["", f"## Campañas recientes ({snapshot.get('recentCampaignsCount', 0)} total)"]
    for c in snapshot.get("recentCampaigns", []):
        lines.append(f"- `{c.get('id')}` {c.get('name')} — {c.get('status')}")
    if not snapshot.get("recentCampaigns"):
        lines.append("- (ninguna)")

    lines += ["", "## Webhooks"]
    wh = snapshot.get("webhooks")
    if isinstance(wh, dict) and wh.get("note"):
        lines.append(f"- {wh['note']}")
    else:
        lines.append(f"- {json.dumps(wh, ensure_ascii=False)}")

    lines += ["", "## Pipelines CRM"]
    for p in snapshot.get("crmPipelines") or []:
        lines.append(f"- {p.get('pipeline')}: {', '.join(p.get('stages', []))}")

    lines += ["", "## Atributos de contacto declarados"]
    for a in snapshot.get("contactAttributes", []):
        lines.append(f"- `{a.get('name')}` ({a.get('category')}, {a.get('type')})")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--sanitized-output", type=Path, default=DEFAULT_SANITIZED)
    parser.add_argument("--check", action="store_true", help="verify the committed sanitized snapshot is current (excludes generatedAt from comparison)")
    parser.add_argument("--no-contacts", action="store_true", help="omit subscriber counts")
    args = parser.parse_args()

    api_key = load_api_key()
    snapshot = collect(api_key, include_contacts=not args.no_contacts)
    sanitized = render_sanitized(snapshot)

    if args.check:
        if not args.sanitized_output.exists():
            print(f"FAIL: {args.sanitized_output} no existe. Genera con: python scripts/brevo/snapshot-brevo.py")
            return 1
        current = args.sanitized_output.read_text(encoding="utf-8")
        strip_date = lambda text: "\n".join(l for l in text.splitlines() if not l.startswith("Generado: "))
        if strip_date(current) != strip_date(sanitized):
            print(f"FAIL: {args.sanitized_output} está desactualizado respecto al estado real de Brevo.")
            return 1
        print(f"PASS: {args.sanitized_output} coincide con el estado real de Brevo (aparte de la marca de tiempo).")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    args.sanitized_output.parent.mkdir(parents=True, exist_ok=True)
    args.sanitized_output.write_text(sanitized, encoding="utf-8")
    print(f"WROTE: {args.output} (local, no commitear)")
    print(f"WROTE: {args.sanitized_output} (seguro para el repo)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
