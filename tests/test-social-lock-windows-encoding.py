"""Localized tasklist output must not break single-instance lock checks."""
import importlib.util
from pathlib import Path
import subprocess
import sys
from unittest import mock

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "scripts/research"))
spec = importlib.util.spec_from_file_location("refresh_encoding", root / "scripts/research/gpt_social_refresh.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

cases = [
    (b'"python.exe","123","Console","1","12,000 K"\r\n', 0, True),
    (b'"python.exe","9123","Console","1","12,000 K"\r\n', 0, False),
    (b'INFORMACI\xd3N: no hay tareas\r\n', 0, False),
    (b'', 1, True),
]
for output, code, expected in cases:
    with mock.patch.object(module.os, "name", "nt"), mock.patch.object(
        module.subprocess, "run", return_value=subprocess.CompletedProcess([], code, output, b"")
    ) as run:
        assert module._pid_alive(123) is expected
        assert not run.call_args.kwargs.get("text", False)

print("PASS Windows lock liveness with localized bytes and exact PID")