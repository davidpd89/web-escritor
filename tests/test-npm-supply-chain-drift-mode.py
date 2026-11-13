"""Un aviso npm publicado de madrugada no debe tumbar PR que no tocan dependencias (carga nocturna 13/11),
pero sí bloquea en modo estricto (PR que cambia package*.json o vigilante diario npm-supply-chain-watch.yml)."""
import importlib.util
import io
import os
import contextlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("baseline", ROOT / "tests" / "test-npm-supply-chain-baseline.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

FAKE = {"vulnerabilities": {"basic-ftp": {"severity": "moderate", "nodes": ["node_modules/basic-ftp"], "fixAvailable": True,
        "via": [{"url": "https://github.com/advisories/GHSA-5pm8-86m8-9m6r", "severity": "moderate", "title": "x"}]}},
        "metadata": {"vulnerabilities": {"moderate": 0}}}
mod.run_audit = lambda npm, args: FAKE
mod.shutil.which = lambda name: "npm"

errors, drift = mod.check_supply_chain_split("npm", __import__("json").loads(mod.BASELINE_PATH.read_text(encoding="utf-8")))
assert not errors, errors
assert any("GHSA-5pm8-86m8-9m6r" in d for d in drift), drift
print("  ok   aviso nuevo clasificado como deriva externa")

os.environ["NPM_SUPPLY_CHAIN_STRICT"] = "0"
out = io.StringIO()
with contextlib.redirect_stdout(out):
    mod.main()
assert "WARN (deriva externa" in out.getvalue()
print("  ok   PR sin cambios de dependencias: avisa sin bloquear")

os.environ["NPM_SUPPLY_CHAIN_STRICT"] = "1"
try:
    mod.main()
except AssertionError as exc:
    assert "GHSA-5pm8-86m8-9m6r" in str(exc)
    print("  ok   modo estricto: bloquea")
else:
    raise AssertionError("strict mode must fail on a new advisory")

os.environ.pop("NPM_SUPPLY_CHAIN_STRICT")
mod.dependency_files_changed = lambda base_ref="origin/main": None
assert mod.strict_mode() is True, "sin git comprobable debe ser estricto (fail-closed)"
mod.dependency_files_changed = lambda base_ref="origin/main": True
assert mod.strict_mode() is True
mod.dependency_files_changed = lambda base_ref="origin/main": False
assert mod.strict_mode() is False
print("  ok   estricto si cambian dependencias o git no responde")
print("test-npm-supply-chain-drift-mode: OK")
