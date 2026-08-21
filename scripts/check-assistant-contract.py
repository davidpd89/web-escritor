#!/usr/bin/env python3
from pathlib import Path
import json, re, sys
ROOT = Path(__file__).resolve().parents[1]
errors = []

def need(cond, msg):
    if not cond: errors.append(msg)

page = (ROOT / "asistente/index.html").read_text(encoding="utf-8")
client = (ROOT / "assets/assistant.js").read_text(encoding="utf-8")
core = (ROOT / "assets/assistant-core.mjs").read_text(encoding="utf-8")
worker = (ROOT / "cloudflare-worker-assistant.js").read_text(encoding="utf-8")
registry = json.loads((ROOT / "data/assistant-source-registry.json").read_text(encoding="utf-8"))
lighthouse = json.loads((ROOT / "lighthouserc.json").read_text(encoding="utf-8"))
migration = (ROOT / "migrations/assistant-quota.sql").read_text(encoding="utf-8")

need('content="noindex,nofollow"' in page, "draft assistant page must remain noindex until activation review")
need('/assets/v1-tools.css' in page, "assistant page must load shared tool styles")
need('data-assistant-turnstile' in page, "Turnstile container missing")
need('data-assistant-stop' in page, "explicit stop control missing")
need(page.count('data-assistant-example=') == 3, "assistant must expose exactly three starter questions")
need('action="/api/assistant"' not in page, "form must be JS-controlled; do not allow accidental native POST")
need('fetch("/api/assistant"' in client, "client must use same-origin /api/assistant")
need('fetch("/api/assistant/config"' in client, "client must discover remote activation/config before POSTing a query")
need('import("/pagefind/pagefind.js")' in client, "Pagefind local fallback missing")
need('rankLocalSources' in client, "registry fallback missing")
need('isSafeInternalPath' in client and 'isSafeInternalPath' in core, "internal URL validation missing")
need('formatCitationMarkers' in client and 'formatCitationMarkers' in core, "human citation numbering missing")
need('turnstile_token' in client, "client must send Turnstile token for remote AI")
need('turnstile-callback-timeout' in client and 'turnstile-script-timeout' in client, "Turnstile client must fail instead of hanging indefinitely")
need('PROTOCOL_VERSION = 1' in core, "client protocol version is not pinned to 1")
need('const PROTOCOL_VERSION = 1' in worker, "Worker protocol version is not pinned to 1")
need('assistantConfigured' in worker and 'ASSISTANT_ENABLED' in worker, "Worker kill switch/config guard missing")
need('SESSION_RATE_LIMITER' in worker and 'IP_RATE_LIMITER' in worker and 'GLOBAL_RATE_LIMITER' in worker, "three anti-abuse burst limit bindings are required")
need('ASSISTANT_QUOTA_DB' in worker and 'consumeDailyQuota' in worker, "exact daily quota binding/guard missing")
need('ASSISTANT_DAILY_SESSION_LIMIT' in worker and 'ASSISTANT_DAILY_GLOBAL_LIMIT' in worker, "daily session/global limits missing")
need('FREE_V1_MODELS' in worker and '@cf/qwen/qwen3-30b-a3b-fp8' in worker, "V1 must be pinned to the audited low-neuron free model")
need('assistant_daily_quota' in migration and 'PRIMARY KEY (bucket, day_utc)' in migration, "D1 quota migration missing or non-atomic")
need('verifyTurnstile' in worker and 'TURNSTILE_SECRET_KEY' in worker and 'TURNSTILE_HOSTNAMES' in worker, "server-side Turnstile verification missing")
need('fusion_method: "rrf"' in worker and 'retrieval_type: "hybrid"' in worker, "hybrid/RRF retrieval contract missing")
need('item?.metadata?.source_id' in worker and 'item?.key' in worker, "retrieved chunks must resolve through metadata source_id or canonical item URL")
need('ASSISTANT_REQUIRE_METADATA_FILTER' in worker, "metadata filtering must be opt-in until website metadata is actually deployed")
need('retrievedIds' in worker and 'invalid_source_reference' in worker, "model source IDs must be limited to retrieved chunks")
need('missing_source_reference' in worker, "generated answers without citations must fail closed")
need('unsafe_generation' in worker and 'containsUrlLike' in worker, "generated URLs must fail closed")
need('NO_EVIDENCE' in worker, "explicit abstention sentinel missing")
need('messages: [{ role: "system"' in worker, "generation policy must use a system message")
need('Cache-Control": "no-store"' in worker, "assistant responses must not be cached")
need('temperature: 0.1' in worker, "generation should stay low-temperature")
need('readJsonBodyLimited' in worker, "request body must be capped while reading, not only after request.text()")
need('attributes' not in json.dumps(registry).lower(), "registry must not contain contact attributes")
need(registry.get("policy") == "deny-by-default", "source registry policy must be deny-by-default")
urls = lighthouse.get("ci", {}).get("collect", {}).get("url", [])
need("http://localhost/asistente/" in urls, "Lighthouse must audit /asistente/ before merge")
ids = [s.get("id") for s in registry.get("sources", [])]

content_registry_path = ROOT / "data/content-registry.json"
if content_registry_path.exists():
    content_registry = json.loads(content_registry_path.read_text(encoding="utf-8"))
    entries = {entry.get("id"): entry for entry in content_registry.get("entries", [])}
    defaults = content_registry.get("defaults", {})
    for source in registry.get("sources", []):
        entry = entries.get(source.get("id"))
        need(entry is not None, f"{source.get('id')}: source_id missing from content-registry")
        if entry:
            need(entry.get("url") == source.get("url"), f"{source.get('id')}: URL drifts from content-registry")
            need(entry.get("status", defaults.get("status")) == "public", f"{source.get('id')}: source is not public in content-registry")
need(len(ids) == len(set(ids)), "source IDs must be unique")
for source in registry.get("sources", []):
    url = source.get("url", "")
    need(source.get("visibility") == "public", f"{source.get('id')}: non-public source in allowlist")
    need(re.fullmatch(r"/(?!/)[A-Za-z0-9_./-]*", url) is not None, f"{source.get('id')}: URL must be a same-origin internal path")
    need(".." not in url.split("/"), f"{source.get('id')}: URL must not contain parent traversal")

if errors:
    print("Assistant contract check FAILED:")
    for error in errors: print(f" - {error}")
    sys.exit(1)
print(f"Assistant contract OK: {len(ids)} public sources, protocol v1, fail-closed Worker, exact quotas, Turnstile, Lighthouse and safe URL contract.")
