#!/usr/bin/env python3
"""Contract for the versioned AI discoverability benchmark corpus."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/ai-discoverability-benchmark.json"

data = json.loads(PATH.read_text(encoding="utf-8"))

assert data["schemaVersion"] == 1
assert data["locale"] == "es-ES"
assert re.fullmatch(r"\d{4}-\d{2}-\d{2}\.v\d+", data["corpusVersion"])
assert data["scoring"]["aggregateScore"] is None, "benchmark must not invent one universal AI visibility score"

expected_counts = {
    "entity-facts": 10,
    "discovery": 10,
    "recommendation-samuel": 10,
    "recommendation-manecillas": 10,
    "topic-authority": 5,
    "negative-control": 5,
}
assert data["categoryTargets"] == expected_counts

prompts = data["prompts"]
assert len(prompts) == 50, f"expected 50 benchmark prompts, got {len(prompts)}"
assert Counter(item["category"] for item in prompts) == Counter(expected_counts)

prefixes = {
    "entity-facts": "FACT",
    "discovery": "DISC",
    "recommendation-samuel": "SAM",
    "recommendation-manecillas": "MAN",
    "topic-authority": "TOP",
    "negative-control": "NEG",
}
expected_evaluation = {
    "entity-facts": "factual",
    "discovery": "discovery",
    "recommendation-samuel": "recommendation",
    "recommendation-manecillas": "recommendation",
    "topic-authority": "topic",
    "negative-control": "negative-control",
}

seen_ids: set[str] = set()
seen_prompts: set[str] = set()
for item in prompts:
    prompt_id = item["id"]
    category = item["category"]
    prompt = item["prompt"].strip()

    assert prompt_id not in seen_ids, f"duplicate prompt id: {prompt_id}"
    seen_ids.add(prompt_id)
    assert re.fullmatch(rf"{prefixes[category]}-\d{{3}}", prompt_id), f"bad prompt id/category pair: {prompt_id} / {category}"
    assert item["evaluation"] == expected_evaluation[category]
    assert prompt and len(prompt) <= 240, f"prompt must be concise: {prompt_id}"
    normalized = re.sub(r"\s+", " ", prompt.casefold())
    assert normalized not in seen_prompts, f"duplicate prompt text: {prompt_id}"
    seen_prompts.add(normalized)
    assert isinstance(item.get("trackedEntities"), list) and item["trackedEntities"], f"trackedEntities missing: {prompt_id}"

    if category == "negative-control":
        assert item.get("expectedTargetRecommendation") == "none", f"negative control must forbid target recommendation: {prompt_id}"
    else:
        assert "expectedTargetRecommendation" not in item, f"non-negative prompt must not predetermine recommendation outcome: {prompt_id}"

# Discovery/recommendation/topic/negative prompts must not lead the measured
# system by naming the site's tracked entities in the question itself.
tracked_names = (
    "david porto díaz",
    "samuel entre mundos",
    "las manecillas del recuerdo",
    "noveris",
)
for item in prompts:
    if item["category"] == "entity-facts":
        continue
    folded = item["prompt"].casefold()
    for name in tracked_names:
        assert name not in folded, f"leading benchmark prompt {item['id']} names tracked entity {name!r}"

policy = data["executionPolicy"]
assert policy["defaultReplicas"] == 1
assert policy["strategicReplicas"] == 3
assert policy["deepResearchSeparate"] is True
assert len(policy["tierA"]) >= 5
assert len(set(policy["tierA"])) == len(policy["tierA"])
assert len(set(policy["tierB"])) == len(policy["tierB"])

record_fields = set(policy["recordFields"])
for field in ("runDate", "platform", "surface", "modelAsDisplayed", "locale", "promptId", "response", "citations"):
    assert field in record_fields, f"execution record missing field {field}"
for forbidden in ("cookies", "account", "userId", "sessionToken"):
    assert forbidden not in record_fields, f"benchmark must not prescribe storing personal/session data: {forbidden}"

print("ai-discoverability-benchmark: OK")
