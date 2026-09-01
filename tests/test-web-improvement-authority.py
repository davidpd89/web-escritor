#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ROOT / "data" / "web-improvement-decisions-2026-08-28.json"
EXECUTION = ROOT / "data" / "web-improvement-execution-plan-2026-08-28.json"
AUTHORITY = ROOT / "docs" / "web-improvements" / "01-FINAL-AUTHORITY-108.md"
SOURCES = ROOT / "docs" / "web-improvements" / "02-PRIMARY-SOURCES-2026-08-28.md"

CATEGORY_COUNTS = {
    "A": 12, "B": 9, "C": 10, "D": 12, "E": 8, "F": 6,
    "G": 5, "H": 6, "I": 5, "J": 6, "K": 5, "L": 4,
    "M": 5, "N": 3, "O": 4, "P": 4, "Q": 4,
}
EXPECTED_IDS = [f"{letter}.{n}" for letter, count in CATEGORY_COUNTS.items() for n in range(1, count + 1)]
VALID_STATUSES = {
    "IMPLEMENT_NOW", "IMPLEMENT_AFTER_CURRENT_DEBT", "ALREADY_COVERED",
    "PARTIAL_AUDIT", "CONDITIONAL", "EXTERNAL_OPERATION", "DEFER", "REJECT",
}
EXECUTABLE_STATUSES = {"IMPLEMENT_NOW", "IMPLEMENT_AFTER_CURRENT_DEBT", "PARTIAL_AUDIT", "EXTERNAL_OPERATION"}

payload = json.loads(DECISIONS.read_text(encoding="utf-8"))
items = payload["items"]
ids = [item["id"] for item in items]
assert len(items) == 108, f"expected 108 decisions, got {len(items)}"
assert len(set(ids)) == 108, "duplicate decision ids"
assert set(ids) == set(EXPECTED_IDS), f"missing/extra ids: {set(EXPECTED_IDS)^set(ids)}"
assert all(item["status"] in VALID_STATUSES for item in items), "unknown decision status"

by_id = {item["id"]: item for item in items}
# Safety / freshness corrections that must not regress.
assert by_id["A.7"]["status"] == "REJECT", "FAQPage must not return as a generic rich-result tactic"
assert by_id["A.12"]["status"] == "REJECT", "third-party review aggregation must remain rejected"
assert by_id["E.7"]["status"] == "PARTIAL_AUDIT", "compression must be measured live, not inferred from DNS/Cloudflare"
assert by_id["F.2"]["status"] == "IMPLEMENT_NOW", "true 200% text resilience must remain an active contract"
assert by_id["L.1"]["status"] == "REJECT", "web push is intentionally rejected at current scale"
assert by_id["O.1"]["status"] == "ALREADY_COVERED", "the existing feed must not be reimplemented"

plan = json.loads(EXECUTION.read_text(encoding="utf-8"))
plan_ids = [item_id for phase in plan["phases"] for item_id in phase["items"]]
assert len(plan_ids) == len(set(plan_ids)), "execution plan contains duplicate ids"
for item_id in plan_ids:
    assert item_id in by_id, f"execution plan references unknown id {item_id}"
    assert by_id[item_id]["status"] in EXECUTABLE_STATUSES, (
        f"{item_id} with status {by_id[item_id]['status']} must not be executable without a trigger"
    )

text = AUTHORITY.read_text(encoding="utf-8")
source_text = SOURCES.read_text(encoding="utf-8")

# Human and machine authorities must agree exactly, not merely mention every ID.
rows = re.findall(
    r"^\|\s*([A-Q]\.\d+)\s*\|\s*(IMPLEMENT_NOW|IMPLEMENT_AFTER_CURRENT_DEBT|ALREADY_COVERED|PARTIAL_AUDIT|CONDITIONAL|EXTERNAL_OPERATION|DEFER|REJECT)\s*\|",
    text,
    flags=re.MULTILINE,
)
markdown_by_id = dict(rows)
assert len(rows) == 108, f"expected 108 decision table rows, got {len(rows)}"
assert len(markdown_by_id) == 108, "duplicate decision rows in human authority"
assert set(markdown_by_id) == set(EXPECTED_IDS), f"human authority missing/extra ids: {set(EXPECTED_IDS)^set(markdown_by_id)}"
for item_id, item in by_id.items():
    assert markdown_by_id[item_id] == item["status"], (
        f"human/machine status mismatch for {item_id}: {markdown_by_id[item_id]} != {item['status']}"
    )

lower = (text + "\n" + source_text).lower()
assert "clarity mcp fue retirado" not in lower
assert "clarity mcp está retirado" not in lower
assert "clarity mcp server retired" not in lower
assert "microsoft/clarity-mcp-server" in lower, "current official Clarity MCP repo must be documented"
assert "feed.xml" in text, "repo feed must be named feed.xml"
assert "content-encoding" in lower, "compression audit must require observed Content-Encoding"
assert "professional/enterprise" in lower or "professional y enterprise" in lower, (
    "Brevo Consent Groups plan gate must remain explicit"
)
assert "https://developers.google.com/search/docs/appearance/structured-data/review-snippet" in source_text
assert "https://www.w3.org/TR/WCAG22/" in source_text
assert "https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance" in source_text

print("web-improvement-authority: OK (108 decisions, markdown/JSON parity, execution gates, freshness corrections)")
