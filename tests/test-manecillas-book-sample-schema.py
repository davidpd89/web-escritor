from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK_PAGE = ROOT / "las-manecillas-del-recuerdo" / "index.html"
SAMPLE_PAGE = ROOT / "las-manecillas-del-recuerdo" / "fragmentos" / "index.html"

BOOK_ID = "https://davidportodiaz.com/#book-manecillas"
SAMPLE_ID = "https://davidportodiaz.com/las-manecillas-del-recuerdo/fragmentos/#sample"
FRAGMENT_IDS = {
    "https://davidportodiaz.com/las-manecillas-del-recuerdo/fragmentos/#fragmento-1",
    "https://davidportodiaz.com/las-manecillas-del-recuerdo/fragmentos/#fragmento-2",
    "https://davidportodiaz.com/las-manecillas-del-recuerdo/fragmentos/#fragmento-3",
}

JSONLD_RE = re.compile(
    r'<script\s+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def jsonld_nodes(path: Path) -> list[dict]:
    html = path.read_text(encoding="utf-8")
    blocks = JSONLD_RE.findall(html)
    assert blocks, f"{path}: no JSON-LD blocks found"

    nodes: list[dict] = []
    for raw in blocks:
        data = json.loads(raw)
        graph = data.get("@graph") if isinstance(data, dict) else None
        if isinstance(graph, list):
            nodes.extend(node for node in graph if isinstance(node, dict))
        elif isinstance(data, dict):
            nodes.append(data)
    return nodes


def ref_ids(value) -> set[str]:
    if isinstance(value, dict):
        ref = value.get("@id")
        return {ref} if isinstance(ref, str) else set()
    if isinstance(value, list):
        out: set[str] = set()
        for item in value:
            out.update(ref_ids(item))
        return out
    return set()


def node_type_is(node: dict, expected: str) -> bool:
    value = node.get("@type")
    if isinstance(value, str):
        return value == expected
    if isinstance(value, list):
        return expected in value
    return False


def main() -> None:
    book_nodes = jsonld_nodes(BOOK_PAGE)
    sample_nodes = jsonld_nodes(SAMPLE_PAGE)
    all_nodes = book_nodes + sample_nodes

    canonical_books = [
        node
        for node in all_nodes
        if node_type_is(node, "Book") and node.get("@id") == BOOK_ID
    ]
    assert len(canonical_books) == 1, (
        "expected exactly one canonical Book node for Manecillas across book/sample pages, "
        f"found {len(canonical_books)}"
    )

    book = canonical_books[0]
    assert ref_ids(book.get("hasPart")) == {SAMPLE_ID}, (
        "canonical Book must link exactly to the canonical free-sample Collection via hasPart"
    )

    samples = [
        node
        for node in sample_nodes
        if node_type_is(node, "Collection") and node.get("@id") == SAMPLE_ID
    ]
    assert len(samples) == 1, f"expected exactly one sample Collection, found {len(samples)}"

    sample = samples[0]
    assert sample.get("isAccessibleForFree") is True, "sample Collection must remain free"
    assert ref_ids(sample.get("isBasedOn")) == {BOOK_ID}, (
        "sample Collection must point back to the canonical Book via isBasedOn"
    )
    assert ref_ids(sample.get("hasPart")) == FRAGMENT_IDS, (
        "sample Collection must keep exactly the three canonical fragment ids"
    )

    fragments = {
        node.get("@id"): node
        for node in sample_nodes
        if node_type_is(node, "CreativeWork") and node.get("@id") in FRAGMENT_IDS
    }
    assert set(fragments) == FRAGMENT_IDS, "all three fragment CreativeWork nodes must exist"

    for fragment_id, fragment in fragments.items():
        assert fragment.get("isAccessibleForFree") is True, f"{fragment_id}: fragment must remain free"
        assert ref_ids(fragment.get("isPartOf")) == {BOOK_ID}, (
            f"{fragment_id}: fragment must belong to the canonical Book"
        )

    print("test-manecillas-book-sample-schema: OK")


if __name__ == "__main__":
    main()
