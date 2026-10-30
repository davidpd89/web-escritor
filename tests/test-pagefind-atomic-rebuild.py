"""Una reconstruccion fallida de Pagefind conserva byte a byte el indice anterior.

Antes, run_pagefind() hacia rmtree(out_dir) antes de lanzar npx: sin la
dependencia instalada o con el proceso caido desaparecia /pagefind/. Ahora
build() genera en un directorio hermano, valida y solo entonces promueve.
Sin npx ni red: se simula subprocess.run.
"""
import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pagefind_builder", ROOT / "scripts/build-pagefind-index.py")
bpi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bpi)

PAGES = ["a.html"]
SENTINEL = b"last good index\r\n"


def fixture(tmp: Path) -> tuple[Path, Path, Path]:
    (tmp / "data").mkdir()
    (tmp / "data" / "content-registry.json").write_text(json.dumps({"entries": []}), encoding="utf-8")
    (tmp / "a.html").write_text("<html><head></head><body>Hola</body></html>", encoding="utf-8")
    out = tmp / "pagefind"
    out.mkdir()
    (out / "pagefind.js").write_bytes(SENTINEL)
    (out / "sentinel.txt").write_bytes(SENTINEL)
    return tmp, out, tmp / ".pagefind-src"


def snapshot(out: Path) -> dict[str, bytes]:
    return {p.relative_to(out).as_posix(): p.read_bytes() for p in sorted(out.rglob("*")) if p.is_file()}


def fake_pagefind(files: dict[str, str]):
    def run(cmd, **kwargs):
        dest = Path(cmd[cmd.index("--output-path") + 1])
        dest.mkdir(parents=True, exist_ok=True)
        for name, body in files.items():
            (dest / name).write_text(body, encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0)
    return run


def leftovers(tmp: Path) -> list[str]:
    return sorted(p.name for p in tmp.iterdir() if p.name.startswith(".pagefind"))


def scenario(label, side_effect, expect_rc=1, extra=None):
    with tempfile.TemporaryDirectory() as d:
        root, out, src = fixture(Path(d))
        before = snapshot(out)
        patches = [
            mock.patch.object(bpi, "eligible_pages", return_value=PAGES),
            mock.patch.object(bpi.subprocess, "run", side_effect=side_effect),
        ] + (extra or [])
        for p in patches:
            p.start()
        try:
            try:
                rc = bpi.build(root, out, src)
            except Exception as exc:  # fallo propagado: tambien es fallo
                rc = f"raised {type(exc).__name__}"
        finally:
            for p in reversed(patches):
                p.stop()
        assert rc != 0 if expect_rc else rc == 0, f"{label}: rc={rc}"
        if expect_rc:
            assert snapshot(out) == before, f"{label}: el indice anterior cambio"
        assert leftovers(root) == [], f"{label}: temporales huerfanos {leftovers(root)}"
        print(f"PASS {label}")
        return root, out


scenario("proceso fallido", subprocess.CalledProcessError(1, ["npx"]))
scenario("dependencia ausente", FileNotFoundError("npx"))
scenario("salida incompleta (sin pagefind.js)", fake_pagefind({"other.js": "x"}))
scenario(
    "manifiesto invalido",
    fake_pagefind({"pagefind.js": "export const ok = 1;"}),
    extra=[mock.patch.object(bpi, "check", return_value=1)],
)
scenario(
    "fallo al escribir el manifiesto",
    fake_pagefind({"pagefind.js": "export const ok = 1;"}),
    extra=[mock.patch.object(bpi, "write_manifest", side_effect=OSError("disk full"))],
)

real_replace = os.replace
calls = {"n": 0}


def replace_fails_on_promotion(src, dst):
    calls["n"] += 1
    if calls["n"] == 2:  # 1: indice vivo -> backup; 2: staging -> vivo
        raise PermissionError("locked")
    return real_replace(src, dst)


scenario(
    "promocion fallida restaura el indice",
    fake_pagefind({"pagefind.js": "export const ok = 1;"}),
    extra=[mock.patch.object(bpi.os, "replace", side_effect=replace_fails_on_promotion)],
)

# Build concurrente: el lock existe -> falla sin tocar nada (y no borra el lock ajeno).
with tempfile.TemporaryDirectory() as d:
    root, out, src = fixture(Path(d))
    before = snapshot(out)
    lock = bpi._lock_path(out)
    lock.write_text("999\n", encoding="utf-8")
    with mock.patch.object(bpi, "eligible_pages", return_value=PAGES), \
        mock.patch.object(bpi.subprocess, "run", side_effect=AssertionError("no debe ejecutarse")):
        assert bpi.build(root, out, src) == 1
    assert snapshot(out) == before and lock.exists()
    print("PASS build concurrente bloqueado por lock")

# Exito: se promueve una salida nueva con manifiesto coherente y --check pasa.
root_ok = None
with tempfile.TemporaryDirectory() as d:
    root, out, src = fixture(Path(d))
    with mock.patch.object(bpi, "eligible_pages", return_value=PAGES), \
        mock.patch.object(bpi.subprocess, "run", side_effect=fake_pagefind({"pagefind.js": "export const ok = 1;"})):
        assert bpi.build(root, out, src) == 0
        assert bpi.check(root, out) == 0
    files = snapshot(out)
    assert "sentinel.txt" not in files, "la salida vieja no se sustituyo"
    assert bpi.MANIFEST_NAME in files and files["pagefind.js"] == b"export const ok = 1;".replace(b"\n", os.linesep.encode())
    assert leftovers(root) == [], leftovers(root)
    print("PASS reconstruccion correcta promueve salida y manifiesto")

# Sin indice previo tambien funciona.
with tempfile.TemporaryDirectory() as d:
    root, out, src = fixture(Path(d))
    import shutil
    shutil.rmtree(out)
    with mock.patch.object(bpi, "eligible_pages", return_value=PAGES), \
        mock.patch.object(bpi.subprocess, "run", side_effect=fake_pagefind({"pagefind.js": "x"})):
        assert bpi.build(root, out, src) == 0
    assert (out / "pagefind.js").is_file() and leftovers(root) == []
    print("PASS primera construccion sin indice previo")

print("test-pagefind-atomic-rebuild: OK")
