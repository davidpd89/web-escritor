#!/usr/bin/env python3
"""Fixtures para scripts/check-recommendations-evidence.py (K.1)."""
from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-recommendations-evidence.py"
failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


BASE_WORK = {
    "isbn": "1111111111",
    "title": "Libro registrado",
    "author": "X",
    "evidenceStatus": "verificado",
    "verifiedDate": "2026-08-23",
    "verificationScope": ["title", "author", "isbn", "edition"],
    "editionSource": {"type": "publisher-catalog", "url": "https://publisher.example.org/book/1111111111"},
    "personalReadingStatus": "pendiente",
}


def evidence_with(*works: dict, corrections: list[dict] | None = None) -> dict:
    return {
        "schema_version": 2,
        "evidence_status_enum": ["leido", "consultado", "verificado", "pendiente"],
        "personal_reading_status_enum": ["leido", "pendiente"],
        "corrections": corrections or [],
        "works": list(works),
    }


def make_repo(tmp: Path, guide_html: str, evidence: dict, policy_html: str = "") -> None:
    # Reset fixture content while keeping the temporary git repository valid.
    if not (tmp / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    (tmp / "data").mkdir(exist_ok=True)
    (tmp / "data" / "recommendations-evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    guide = tmp / "recomendaciones" / "guia-test"
    guide.mkdir(parents=True, exist_ok=True)
    (guide / "index.html").write_text(guide_html, encoding="utf-8")
    policy = tmp / "recomendaciones" / "politica-de-recomendaciones"
    policy.mkdir(parents=True, exist_ok=True)
    (policy / "index.html").write_text(policy_html, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "fixture"],
        cwd=tmp, check=True,
    )


def run_checker(tmp: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(tmp), "--check"],
        capture_output=True, text=True,
    )


def run() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)

        make_repo(tmp, '<li class="rec-item" data-isbn="1111111111">Edición verificada · ISBN 1111111111</li>', evidence_with(BASE_WORK))
        result = run_checker(tmp)
        check(result.returncode == 0 and "0 incumplimiento" in result.stdout, "bibliografia verificada con URL reproducible pasa", result.stdout)

        # La autoria no acredita lectura.
        own = dict(BASE_WORK, author="David Porto Díaz", relationship="obra-propia")
        make_repo(tmp, '<li class="rec-item rec-item--self" data-isbn="1111111111">Obra propia · ISBN 1111111111</li>', evidence_with(own))
        result = run_checker(tmp)
        check(result.returncode == 0, "obra propia con lectura pendiente es valida", result.stdout)

        make_repo(tmp, '<li class="rec-item rec-item--self" data-isbn="1111111111">Obra propia — leído · ISBN 1111111111</li>', evidence_with(own))
        result = run_checker(tmp)
        check("afirma lectura personal" in result.stdout, "HTML no puede inferir leido por autoria", result.stdout)

        bad_read = dict(own, evidenceStatus="leido", personalReadingStatus="leido")
        make_repo(tmp, '<li class="rec-item rec-item--self" data-isbn="1111111111">ISBN 1111111111</li>', evidence_with(bad_read))
        result = run_checker(tmp)
        check("sin personalReadingEvidence.reference" in result.stdout, "estado leido exige evidencia humana explicita", result.stdout)

        good_read = dict(bad_read, personalReadingEvidence={"reference": "Declaración editorial fechada 2026-08-23"})
        make_repo(tmp, '<li class="rec-item rec-item--self" data-isbn="1111111111">Leído · ISBN 1111111111</li>', evidence_with(good_read))
        result = run_checker(tmp)
        check(result.returncode == 0, "lectura explicita con referencia humana pasa", result.stdout)

        # Verificado exige fuente concreta; texto vago o placeholder falla.
        no_url = dict(BASE_WORK, editionSource={"type": "publisher-catalog", "url": ""})
        make_repo(tmp, '<li class="rec-item" data-isbn="1111111111">ISBN 1111111111</li>', evidence_with(no_url))
        result = run_checker(tmp)
        check("editionSource reproducible" in result.stdout, "verificado sin URL reproducible falla", result.stdout)

        placeholder = dict(BASE_WORK, editionSource={"type": "publisher-catalog", "url": "https://example.com/todo"})
        make_repo(tmp, '<li class="rec-item" data-isbn="1111111111">ISBN 1111111111</li>', evidence_with(placeholder))
        result = run_checker(tmp)
        check("editionSource reproducible" in result.stdout, "fuente placeholder falla", result.stdout)

        pending = dict(BASE_WORK, evidenceStatus="pendiente")
        pending.pop("verifiedDate")
        pending.pop("verificationScope")
        pending.pop("editionSource")
        make_repo(tmp, '<li class="rec-item" data-isbn="1111111111">Edición verificada · ISBN 1111111111</li>', evidence_with(pending))
        result = run_checker(tmp)
        check("afirma edicion verificada" in result.stdout, "HTML verificado con autoridad pendiente falla", result.stdout)

        # Afiliacion y relacion de obra propia siguen siendo gates independientes.
        make_repo(tmp, '<li class="rec-item" data-isbn="1111111111">ISBN 1111111111</li><a rel="nofollow sponsored">x</a>', evidence_with(BASE_WORK))
        result = run_checker(tmp)
        check("affiliate-disclosure" in result.stdout, "afiliacion sin disclosure falla", result.stdout)

        wrong_relationship = dict(BASE_WORK)
        make_repo(tmp, '<li class="rec-item rec-item--self" data-isbn="1111111111">ISBN 1111111111</li>', evidence_with(wrong_relationship))
        result = run_checker(tmp)
        check("relationship='obra-propia'" in result.stdout, "self marker exige relacion declarada", result.stdout)

        # Corrección sustancial pública: exige nota visible + dateModified/fecha.
        correction = {
            "correction_id": "c1",
            "status": "applied",
            "page_url": "https://site.example.org/recomendaciones/politica/",
            "corrected_at": "2026-08-23",
            "significant_update": True,
            "public_note": True,
            "source": "Auditoría humana K.1",
            "summary": "Se separa autoria de lectura personal.",
        }
        make_repo(
            tmp,
            '<li class="rec-item" data-isbn="1111111111">ISBN 1111111111</li>',
            evidence_with(BASE_WORK, corrections=[correction]),
            '<script>{"dateModified":"2026-08-23"}</script><aside data-correction-id="c1">Corrección 2026-08-23</aside>',
        )
        result = run_checker(tmp)
        check(result.returncode == 0, "correccion sustancial publica trazable pasa", result.stdout)

        make_repo(
            tmp,
            '<li class="rec-item" data-isbn="1111111111">ISBN 1111111111</li>',
            evidence_with(BASE_WORK, corrections=[correction]),
            '<script>{"dateModified":"2026-08-23"}</script>',
        )
        result = run_checker(tmp)
        check("falta nota publica" in result.stdout, "correccion publica sin nota visible falla", result.stdout)

        # Corrección menor privada no fuerza note/dateModified.
        minor_private = dict(correction, correction_id="c2", significant_update=False, public_note=False)
        make_repo(tmp, '<li class="rec-item" data-isbn="1111111111">ISBN 1111111111</li>', evidence_with(BASE_WORK, corrections=[minor_private]), "")
        result = run_checker(tmp)
        check(result.returncode == 0, "correccion menor privada no finge actualizacion publica", result.stdout)

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-check-recommendations-evidence: OK")


if __name__ == "__main__":
    run()