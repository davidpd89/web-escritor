#!/usr/bin/env python3
"""Generate safe, provider-neutral SPARQL query BATCHES for Wikidata P840/P915/P551.

No HTTP calls, no packages, no automatic publishing, no AI.
The returned coordinates refer to the Wikidata PLACE, not to a novel scene.
Selected QIDs must be curated beforehand; all output rows remain candidates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

QID = re.compile(r"^Q[1-9][0-9]*$")
PREDICATES = {
    "narrative": "P840",        # location of narrative (subject must be a work)
    "filming": "P915",          # filming location (subject is adaptation)
    "author_residence": "P551", # residence (subject is author)
}
PREFIXES = ("PREFIX wd: <http://www.wikidata.org/entity/>\n"
            "PREFIX wdt: <http://www.wikidata.org/prop/direct/>\n")


def chunks(qids: list[str], *, batch_size: int = 20) -> list[list[str]]:
    if not 1 <= batch_size <= 50:
        raise ValueError("batch_size debe estar entre 1 y 50")
    unique = list(dict.fromkeys(qids))
    if not unique or any(not isinstance(q, str) or not QID.fullmatch(q) for q in unique):
        raise ValueError("QIDs inválidos: solo Q123, no texto SPARQL arbitrario")
    return [unique[i:i + batch_size] for i in range(0, len(unique), batch_size)]


def make_query(kind: str, qids: list[str]) -> str:
    if kind not in PREDICATES:
        raise ValueError(f"Tipo de vínculo no soportado: {kind}")
    if len(qids) > 50:
        raise ValueError("Lote mayor de 50 QIDs")
    chunks(qids, batch_size=50)  # valida identificadores y vacíos
    values = " ".join("wd:" + q for q in qids)
    return (PREFIXES
            + "SELECT DISTINCT ?subject ?place ?coordinate WHERE {\n"
            + "  VALUES ?subject { " + values + " }\n"
            + f"  ?subject wdt:{PREDICATES[kind]} ?place .\n"
            + "  OPTIONAL { ?place wdt:P625 ?coordinate . }\n"
            + "}\nLIMIT 10000\n")


def plan(kind: str, qids: list[str], batch_size: int = 20) -> list[dict]:
    result = []
    for batch in chunks(qids, batch_size=batch_size):
        sparql = make_query(kind, batch)
        result.append({
            "schema_version": 1, "kind": kind, "qids": batch,
            "predicate": PREDICATES[kind],
            "query_sha256": hashlib.sha256(sparql.encode("utf-8")).hexdigest(),
            "sparql": sparql, "status": "UNEXECUTED_CANDIDATE_QUERY",
            "provider": "wikidata", "endpoint_policy": "configure_separately",
        })
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kind", required=True, choices=sorted(PREDICATES))
    p.add_argument("--qids", required=True, nargs="+", help="IDs Q, nunca nombres de personas")
    p.add_argument("--batch-size", type=int, default=20)
    p.add_argument("--out-dir", required=True, type=Path,
                   help="Carpeta solo de propuestas .rq y .json sin ejecutar")
    args = p.parse_args()
    if args.out_dir.exists():
        p.error("Carpeta de salida ya existe; no sobrescribir históricos/versiones")
    batches = plan(args.kind, args.qids, args.batch_size)
    args.out_dir.mkdir(parents=True)
    for i, item in enumerate(batches, start=1):
        stem = f"{args.kind}-{i:04d}"
        (args.out_dir / (stem + ".rq")).write_text(item["sparql"], encoding="utf-8")
        (args.out_dir / (stem + ".json")).write_text(
            json.dumps({k: v for k, v in item.items() if k != "sparql"},
                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"batches": len(batches), "kind": args.kind,
                      "status": "queries_saved_not_executed"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
