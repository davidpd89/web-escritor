"""Mutation tests for scripts/build-public-editorial-facts.py.

Confirms the public projection is actually derived from editorial-facts.json
(not a second hand-maintained copy that happens to match today), that it
never leaks internal-only fields, and that regeneration is byte-idempotent.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GENERATOR = ROOT / "scripts" / "build-public-editorial-facts.py"
REAL_FACTS = json.loads((ROOT / "editorial-facts.json").read_text(encoding="utf-8"))

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


_run_counter = [0]


def run(facts: dict, tmp: Path, *, check_flag: bool = False, existing_output: str | None = None) -> subprocess.CompletedProcess:
    _run_counter[0] += 1
    facts_path = tmp / f"editorial-facts-{_run_counter[0]}.json"
    output_path = tmp / f"editorial-public-facts-{_run_counter[0]}.mjs"
    facts_path.write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")
    if existing_output is not None:
        output_path.write_text(existing_output, encoding="utf-8")
    args = [sys.executable, str(GENERATOR), "--facts", str(facts_path), "--output", str(output_path)]
    if check_flag:
        args.append("--check")
    proc = subprocess.run(args, capture_output=True, text=True)
    proc.output_path = output_path  # type: ignore[attr-defined]
    return proc


with tempfile.TemporaryDirectory() as tmp_name:
    tmp = Path(tmp_name)

    # 1. Idempotent: generate, then --check against the same facts must pass.
    baseline = run(REAL_FACTS, tmp)
    check(baseline.returncode == 0, f"baseline generation failed: {baseline.stderr}")
    baseline_text = baseline.output_path.read_text(encoding="utf-8")
    idempotent = run(REAL_FACTS, tmp, check_flag=True, existing_output=baseline_text)
    check(idempotent.returncode == 0, f"--check against freshly generated output should pass: {idempotent.stdout}{idempotent.stderr}")

    # 2. Changing publicationDate must change the generated output, and a stale
    #    on-disk copy must fail --check until regenerated (the AIII-08 gate).
    mutated_date = copy.deepcopy(REAL_FACTS)
    mutated_date["books"]["lasManecillasDelRecuerdo"]["publicationDate"] = "2027-01-15"
    stale_check = run(mutated_date, tmp, check_flag=True, existing_output=baseline_text)
    check(stale_check.returncode != 0, "stale output (old publicationDate) should fail --check after the fact changes")
    regenerated = run(mutated_date, tmp)
    check(regenerated.returncode == 0, f"regeneration after mutation failed: {regenerated.stderr}")
    mutated_text = regenerated.output_path.read_text(encoding="utf-8")
    check(mutated_text != baseline_text, "changing publicationDate did not change the generated projection")
    check("2027-01-15" in mutated_text, "generated projection did not pick up the mutated publicationDate")
    check("15 de enero de 2027" in mutated_text, "generated projection did not recompute the Spanish human date")

    # 3. Changing publisher must change the derived output.
    mutated_publisher = copy.deepcopy(REAL_FACTS)
    mutated_publisher["books"]["lasManecillasDelRecuerdo"]["publisher"] = "Editorial de Prueba"
    publisher_run = run(mutated_publisher, tmp)
    check(publisher_run.returncode == 0, f"regeneration after publisher mutation failed: {publisher_run.stderr}")
    check("Editorial de Prueba" in publisher_run.output_path.read_text(encoding="utf-8"), "changing publisher did not propagate to the projection")

    # 4. Changing ISBN/pages must not leave a stale literal behind.
    mutated_isbn = copy.deepcopy(REAL_FACTS)
    mutated_isbn["books"]["samuelEntreMundos"]["isbn"] = "0000000000000"
    mutated_isbn["books"]["samuelEntreMundos"]["numberOfPages"] = 999
    isbn_run = run(mutated_isbn, tmp)
    isbn_text = isbn_run.output_path.read_text(encoding="utf-8")
    check("0000000000000" in isbn_text and "999" in isbn_text, "changing Samuel's ISBN/page count did not propagate")
    # Only the standalone "isbn" field is asserted here -- the real ISBN also
    # legitimately appears inside purchaseUrls.casaDelLibro (the retailer URL
    # embeds it in its path), which is copied verbatim and correctly untouched
    # by an ISBN-field-only mutation, so a whole-text absence check would be
    # a false positive.
    check(f'"isbn": "{REAL_FACTS["books"]["samuelEntreMundos"]["isbn"]}"' not in isbn_text, "old ISBN field literal survived the mutation")

    # 5. Internal-only fields must never appear in the generated output, real
    #    facts or mutated.
    for proc in (baseline, regenerated, publisher_run, isbn_run):
        # Only the generated JS object body is checked here, not the header
        # comment -- that comment legitimately names knownEditorialIncident to
        # document that it's excluded, which isn't the leak this guards.
        body = proc.output_path.read_text(encoding="utf-8").split("EDITORIAL_PUBLIC_FACTS = ", 1)[1]
        check('"knownEditorialIncident"' not in body, "internal knownEditorialIncident key leaked into the public projection body")
        check("davidpuede" not in body, "internal editorial-incident detail leaked into the public projection")
        check("editorialCopyNote" not in body, "internal editorialCopyNote leaked into the public projection")

    # 6. The real repo file is checked in and matches editorial-facts.json.
    real_check = subprocess.run([sys.executable, str(GENERATOR), "--check"], cwd=ROOT, capture_output=True, text=True)
    check(real_check.returncode == 0, f"assets/editorial-public-facts.mjs is stale in the repo: {real_check.stdout}{real_check.stderr}")

if failures:
    for f in failures:
        print(f"FAIL: {f}")
    sys.exit(1)
print(f"OK: editorial-public-facts projection mutation tests ({6} scenarios)")
