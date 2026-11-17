"""R5-8: fronteras de secretos de los workflows, como tests sobre los YAML.

1. Ningún workflow que se dispare con `pull_request`/`pull_request_target` usa secretos distintos de `GITHUB_TOKEN`,
   y ese token es de solo lectura. La PR de la App nace de una rama del propio repo: sus workflows corren con secretos
   y el parche puede cambiar los scripts que ejecutan.
2. Todo job con modelo (acción de Claude/OpenAI o token de modelo) declara exactamente un secreto y ningún permiso de
   escritura (2.2: `proponer`). No exige `harden-runner`.

Es una regla por forma: cubre cualquier workflow nuevo, no una lista de nombres.
"""
from pathlib import Path
import re
import unittest

import yaml

WORKFLOWS = sorted((Path(__file__).resolve().parents[1] / ".github" / "workflows").glob("*.y*ml"))
PR_EVENTS = {"pull_request", "pull_request_target"}
SECRET = re.compile(r"\$\{\{[^}]*?\bsecrets\.([A-Za-z_][A-Za-z0-9_]*)")
SECRET_INHERIT = re.compile(r"^\s*secrets:\s*inherit\s*$", re.M)
MODEL_USES = re.compile(r"(anthropics/claude-code|anthropics/claude-code-action|openai/codex-action)", re.I)
MODEL_SECRET = re.compile(r"(ANTHROPIC|CLAUDE|OPENAI)", re.I)
# Escrituras permitidas en pull_request, con motivo. Sin entradas muertas (test_allowlist_has_no_dead_entries).
WRITE_ALLOWED = {
    ("codeql.yml", "*:security-events"): "subir resultados a code scanning; no escribe en el repo",
}


def load(path):
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    on = data.get(True, data.get("on")) or {}  # PyYAML lee `on:` como True
    if isinstance(on, str):
        on = {on: None}
    elif isinstance(on, list):
        on = dict.fromkeys(on)
    return data, set(on)


def writes(perms):
    if perms in ("write-all",):
        return ["write-all"]
    if isinstance(perms, dict):
        return sorted(k for k, v in perms.items() if v == "write")
    return []


def escrituras(data):
    """Escrituras del token: `*:<permiso>` a nivel de workflow, `<job>:<permiso>` por job. Sin bloque de workflow, el
    token hereda el valor por defecto del repo (hoy, escritura)."""
    if data.get("permissions") is None:
        out = ["*:sin bloque permissions (hereda el valor por defecto del repo)"]
    else:
        out = [f"*:{w}" for w in writes(data["permissions"])]
    for nombre, job in (data.get("jobs") or {}).items():
        out += [f"{nombre}:{w}" for w in writes((job or {}).get("permissions"))]
    return out


def secrets_in(obj):
    return set(SECRET.findall(yaml.safe_dump(obj, allow_unicode=True, width=10**6)))


class WorkflowSecretBoundaries(unittest.TestCase):
    def test_workflows_found(self):
        self.assertGreater(len(WORKFLOWS), 20)

    def test_pull_request_workflows_use_no_secrets_and_read_only_token(self):
        fallos = []
        for path in WORKFLOWS:
            data, events = load(path)
            if not events & PR_EVENTS:
                continue
            texto = path.read_text(encoding="utf-8")
            extra = set(SECRET.findall(texto)) - {"GITHUB_TOKEN"}
            if extra:
                fallos.append(f"{path.name}: secretos {sorted(extra)} en un workflow de pull_request")
            if SECRET_INHERIT.search(texto):
                fallos.append(f"{path.name}: `secrets: inherit` en un workflow de pull_request")
            if "pull_request_target" in events:
                fallos.append(f"{path.name}: pull_request_target corre con secretos sobre código de la PR")
            escritura = [e for e in escrituras(data) if (path.name, e) not in WRITE_ALLOWED]
            if escritura:
                fallos.append(f"{path.name}: GITHUB_TOKEN con escritura en pull_request: {escritura}")
        self.assertEqual(fallos, [], "\n".join(fallos))

    def test_allowlist_has_no_dead_entries(self):
        vivas = set()
        for path in WORKFLOWS:
            data, events = load(path)
            if events & PR_EVENTS:
                vivas |= {(path.name, e) for e in escrituras(data)}
        self.assertEqual(set(WRITE_ALLOWED) - vivas, set())

    def test_model_jobs_hold_one_secret_and_no_write(self):
        fallos = []
        for path in WORKFLOWS:
            data, _ = load(path)
            for nombre, job in (data.get("jobs") or {}).items():
                job = job or {}
                usa = any(MODEL_USES.search(str(s.get("uses", ""))) for s in job.get("steps") or [])
                secretos = secrets_in(job) | secrets_in(data.get("env") or {})
                if not (usa or any(MODEL_SECRET.search(s) for s in secretos)):
                    continue
                if len(secretos - {"GITHUB_TOKEN"}) != 1:
                    fallos.append(f"{path.name}:{nombre}: job con modelo con secretos {sorted(secretos)}")
                perms = job.get("permissions", data.get("permissions"))
                if perms is None or writes(perms):
                    fallos.append(f"{path.name}:{nombre}: job con modelo con permisos {perms!r}")
        self.assertEqual(fallos, [], "\n".join(fallos))


class RuleShape(unittest.TestCase):
    """La regla detecta las formas que debe detectar (sin depender de que hoy exista un workflow que las tenga)."""

    def test_detects_secret_expressions(self):
        self.assertEqual(SECRET.findall("x: ${{ secrets.TOKEN_X }} y ${{ github.token || secrets.OTRO }}"),
                         ["TOKEN_X", "OTRO"])
        self.assertEqual(SECRET.findall("run: python scripts/secrets.py"), [])

    def test_write_permissions(self):
        self.assertEqual(writes({"contents": "write", "issues": "read"}), ["contents"])
        self.assertEqual(writes("write-all"), ["write-all"])
        self.assertEqual(writes("read-all"), [])


if __name__ == "__main__":
    unittest.main()
