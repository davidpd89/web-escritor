#!/usr/bin/env python3
"""R5-7c: alarma `bypass-usado`. Cada push a main debe venir de una PR fusionada cuyo último commit pasó los checks
requeridos por el ruleset de main. Si no, abre (o comenta) una issue con la etiqueta `bypass-usado`.

Es detección, no bloqueo: el bypass del ruleset sigue existiendo y aquí solo se hace visible cada uso.
Los checks requeridos se leen del ruleset vigente (`rules/branches/main`), no de una lista copiada.

Uso (workflow bypass-usado.yml, en push a main): python scripts/bypass_usado.py --repo OWNER/REPO --sha SHA [--before SHA]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gh_listas  # noqa: E402

OK = {"success", "skipped", "neutral"}
ETIQUETA = "bypass-usado"


def gh(*args: str) -> str:
    r = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise RuntimeError(f"gh {' '.join(args[:3])}: {r.stderr.strip()[:300]}")
    return r.stdout


def gh_json(*args: str):
    return json.loads(gh(*args) or "null")


def evaluar(sha: str, prs: list[dict], requeridos: set[str], resultados: dict[str, str]) -> list[str]:
    """Motivos por los que `sha` no cuenta como fusión por PR con los checks en verde ([] = correcto).

    `prs`: PRs asociadas al commit (API commits/{sha}/pulls). `resultados`: contexto -> conclusión en la cabeza de
    la PR (check runs y estados combinados; el más reciente de cada contexto)."""
    propias = [p for p in prs if p.get("merge_commit_sha") == sha and p.get("merged_at")
               and (p.get("base") or {}).get("ref") == "main"]
    if not propias:
        return [f"{sha[:10]} no es el commit de fusión de ninguna PR a main"]
    pr = propias[0]
    motivos = []
    for contexto in sorted(requeridos):
        conclusion = resultados.get(contexto)
        if conclusion not in OK:
            motivos.append(f"PR #{pr['number']}: check requerido «{contexto}» = {conclusion or 'ausente'}")
    return motivos


def requeridos(repo: str) -> set[str]:
    reglas = gh_json("api", f"repos/{repo}/rules/branches/main", "--paginate", "--slurp")
    planas = [r for pagina in reglas for r in pagina] if reglas and isinstance(reglas[0], list) else reglas or []
    return {c["context"] for r in planas if r.get("type") == "required_status_checks"
            for c in r.get("parameters", {}).get("required_status_checks", [])}


def resultados(repo: str, head: str) -> dict[str, str]:
    """Conclusión más reciente por contexto: check runs (por nombre) y estados de commit."""
    out: dict[str, tuple[str, str]] = {}
    paginas = gh_json("api", f"repos/{repo}/commits/{head}/check-runs?per_page=100", "--paginate", "--slurp")
    for pagina in paginas or []:
        for run in pagina.get("check_runs", []):
            cuando = run.get("completed_at") or run.get("started_at") or ""
            valor = run.get("conclusion") or run.get("status") or ""
            if run["name"] not in out or cuando > out[run["name"]][0]:
                out[run["name"]] = (cuando, valor)
    estado = gh_json("api", f"repos/{repo}/commits/{head}/status") or {}
    for s in estado.get("statuses", []):  # vienen del más reciente al más antiguo
        if s["context"] not in out:
            out[s["context"]] = (s.get("updated_at", ""), s.get("state", ""))
    return {k: v for k, (_, v) in out.items()}


def commits_del_push(repo: str, before: str | None, sha: str) -> list[str]:
    """Primer padre desde `before` hasta `sha`: un push puede traer varios commits sin PR."""
    if not before or set(before) == {"0"}:
        return [sha]
    comp = gh_json("api", f"repos/{repo}/compare/{before}...{sha}")
    shas = [c["sha"] for c in (comp or {}).get("commits", [])]
    return shas or [sha]


def avisar(repo: str, sha: str, motivos: list[str], run_url: str) -> None:
    cuerpo = "\n".join([f"Push a main sin PR verde: `{sha}`", "", *[f"- {m}" for m in motivos], "",
                        f"Detectado por {run_url}", "", "R5-7c: el bypass del ruleset se usó o un check requerido no "
                        "estaba en verde. Revisar quién empujó y por qué; si fue legítimo, cerrar con el motivo."])
    # Una ventana de 1 a propósito: basta saber si hay alguna abierta para comentar en ella.
    abiertas = gh_listas.ultimas(gh_json, "issue", "list", "--repo", repo, "--label", ETIQUETA, "--state", "open",
                                 "--json", "number", n=1)
    if abiertas:
        gh("issue", "comment", str(abiertas[0]["number"]), "--repo", repo, "--body", cuerpo)
        return
    gh("label", "create", ETIQUETA, "--repo", repo, "--color", "B60205", "--force",
       "--description", "Push a main sin PR con checks requeridos en verde (R5-7c)")
    gh("issue", "create", "--repo", repo, "--label", ETIQUETA, "--title", f"bypass-usado: {sha[:10]} en main",
       "--body", cuerpo)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--repo", required=True)
    p.add_argument("--sha", required=True)
    p.add_argument("--before")
    p.add_argument("--dry-run", action="store_true", help="solo informa; no abre issues")
    a = p.parse_args()
    run_url = (f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{a.repo}/actions/runs/"
               f"{os.environ.get('GITHUB_RUN_ID', '?')}")
    req = requeridos(a.repo)
    if not req:
        print("AVISO: el ruleset de main no declara checks requeridos; solo se comprueba la PR", flush=True)
    fallos = 0
    for sha in commits_del_push(a.repo, a.before, a.sha):
        prs = gh_json("api", f"repos/{a.repo}/commits/{sha}/pulls") or []
        propia = next((x for x in prs if x.get("merge_commit_sha") == sha), None)
        res = resultados(a.repo, propia["head"]["sha"]) if propia else {}
        motivos = evaluar(sha, prs, req, res)
        print(f"{sha[:10]}: {'OK' if not motivos else '; '.join(motivos)}", flush=True)
        if motivos:
            fallos += 1
            if not a.dry_run:
                avisar(a.repo, sha, motivos, run_url)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
