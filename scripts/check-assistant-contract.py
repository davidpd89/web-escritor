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

need('content="noindex,nofollow"' in page, "draft assistant page must remain noindex until integration review")
need('action="/api/assistant"' not in page, "form must be JS-controlled; do not allow accidental native POST")
need('fetch("/api/assistant"' in client, "client must use same-origin /api/assistant")
need('import("/pagefind/pagefind.js")' in client, "Pagefind local fallback missing")
need('rankLocalSources' in client, "registry fallback missing")
need('PROTOCOL_VERSION = 1' in core, "client protocol version is not pinned to 1")
need('const PROTOCOL_VERSION = 1' in worker, "Worker protocol version is not pinned to 1")
need('ASSISTANT_ENABLED' in worker and '!== "true"' in worker, "Worker kill switch must fail closed")
need('SESSION_RATE_LIMITER' in worker and 'GLOBAL_RATE_LIMITER' in worker, "both rate-limit bindings are required")
need('filters: { visibility: "public" }' in worker, "retrieval must filter public content before search")
need('fusion_method: "rrf"' in worker and 'retrieval_type: "hybrid"' in worker, "hybrid/RRF retrieval contract missing")
need('item?.metadata?.source_id' in worker, "retrieved chunks must resolve through metadata source_id")
need('unknownCitation' in worker and 'retrievedIds' in worker, "model source IDs must be limited to retrieved chunks")
need('missing_source_reference' in worker, "generated answers without citations must fail closed")
need('Cache-Control": "no-store"' in worker, "assistant responses must not be cached")
need('temperature: 0.1' in worker, "generation should stay low-temperature")
need('attributes' not in json.dumps(registry).lower(), "registry must not contain contact attributes")
need(registry.get("policy") == "deny-by-default", "source registry policy must be deny-by-default")
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
    need(source.get("visibility") == "public", f"{source.get('id')}: non-public source in allowlist")
    need(re.fullmatch(r"/[A-Za-z0-9_./-]*", source.get("url", "")) is not None, f"{source.get('id')}: URL must be an internal path")

if errors:
    print("Assistant contract check FAILED:")
    for error in errors: print(f" - {error}")
    sys.exit(1)
print(f"Assistant contract OK: {len(ids)} public sources, protocol v1, fail-closed Worker.")
