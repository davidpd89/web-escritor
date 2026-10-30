"""Preflight children must use the interpreter selected for the parent."""
import importlib.util
from pathlib import Path
import subprocess
import sys
from unittest import mock

path = Path(__file__).resolve().parents[1] / "scripts/release-readiness.py"
spec = importlib.util.spec_from_file_location("release_readiness", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with mock.patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "ok", "")) as run:
    assert module.run("python scripts/check-image-format-ladder.py --check") == (0, "ok")
    assert run.call_args.args[0] == [sys.executable, "scripts/check-image-format-ladder.py", "--check"]
    assert run.call_args.kwargs.get("shell", False) is False
    module.run("node tests/test-newsletter-client-contract.mjs")
    assert run.call_args.args[0] == ["node", "tests/test-newsletter-client-contract.mjs"]

print("PASS release readiness interpreter isolation")