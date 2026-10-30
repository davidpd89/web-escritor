"""El informe de preflight debe concordar con su estado: BLOCKED nunca certifica éxito."""
import importlib.util
from pathlib import Path
import tempfile
from unittest import mock

path = Path(__file__).resolve().parents[1] / "scripts/release-readiness.py"
spec = importlib.util.spec_from_file_location("release_readiness", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

CERT = "certifica el estado STATIC_CHECKS_PASSED"


def report(checks, routes, run_result, route_exists):
    with tempfile.TemporaryDirectory() as tmp, \
        mock.patch.object(module, "CHECKS", checks), \
        mock.patch.object(module, "ROUTE_CHECKS", routes), \
        mock.patch.object(module, "run", return_value=run_result), \
        mock.patch.object(module, "git_output", return_value="deadbeef"), \
        mock.patch.object(module, "load_sitemap_urls", return_value=set()), \
        mock.patch.object(module, "route_in_sitemap", return_value=route_exists), \
        mock.patch.object(Path, "exists", return_value=route_exists):
        out = Path(tmp) / "report.md"
        code = module.build_report(out)
        return code, out.read_text(encoding="utf-8")


code, text = report([("synthetic failing check", "python bad.py")], [], (1, "synthetic failure"), True)
assert code == 1
assert "## Status: `BLOCKED`" in text
assert CERT not in text
assert "NO certifica" in text and "synthetic failing check" in text

code, text = report([("ok check", "python ok.py")], [("/falta/", "file")], (0, "ok"), False)
assert code == 1
assert "## Status: `BLOCKED`" in text
assert CERT not in text
assert "Ruta `/falta/`" in text

code, text = report([("ok check", "python ok.py")], [("/existe/", "file")], (0, "ok"), True)
assert code == 0
assert "## Status: `STATIC_CHECKS_PASSED`" in text
assert CERT in text and "NO certifica" not in text
assert "No sustituye la ejecución completa de los gates requeridos de CI" in text

print("PASS release readiness report truth")
