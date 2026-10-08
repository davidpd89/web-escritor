#!/usr/bin/env python3
"""Regressions for Claude Code's agent-only merge/unsafe-git hook."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude/hooks/guard-main.py"

DENIED = [
    "gh pr merge 593",
    "gh pr -R davidpd89/web-escritor merge 593",
    "gh --repo davidpd89/web-escritor pr merge 593 --squash",
    "npm test && gh pr merge 593",
    "gh api repos/davidpd89/web-escritor/pulls/593/merge -X PUT",
    "gh api -X PUT repos/davidpd89/web-escritor/pulls/593/merge",
    "gh api -X PUT /repos/davidpd89/web-escritor/pulls/593/merge",
    "gh api -X PUT https://api.github.com/repos/davidpd89/web-escritor/pulls/593/merge",
    "git push",
    "git push origin",
    "git push origin # publish branch",
    "git push --receive-pack git-receive-pack origin",
    "git push --receive-pack=git-receive-pack origin",
    "git push origin --receive-pack git-receive-pack",
    "git push --exec git-receive-pack origin",
    "git push origin --exec git-receive-pack",
    "git push --push-option audit origin",
    "git push -o audit origin",
    "git push origin -o audit",
    "git push --push-option=audit origin",
    "git push -oaudit origin",
    "git push --unknown-option origin topic",
    "git push -- origin",
    "git push origin --",
    "git push --receive-pack origin",
    "git push --push-option origin",
    "git push -- -unknown feature",
    "git update-ref -d refs/heads/old-branch",
    "git update-ref --stdin",
    "git symbolic-ref --delete refs/heads/old-branch",
    "git push -u origin # accidental default push",
    "git push origin feature # trailing comment",
    "git push origin main",
    "git push origin HEAD:main",
    "git push origin HEAD:refs/heads/main",
    "git -C . push origin feature:main",
    "git push --force-with-lease origin feature",
    "git push origin +feature:feature",
    "git push -u origin main",
    "git status\ngh pr merge 593",
    "git push --all origin",
    "git push origin :feature",
    "git push origin :",
    "git push origin --delete feature",
    "git push origin feature --prune",
    "git push origin feature --tags",
    "git merge topic",
    "git checkout main && git merge topic",
    "git pull origin main",
    "git reset --hard HEAD",
    "git clean -fd",
    "git branch -D other",
    "git branch -d old-branch",
    "git branch --delete old-branch",
    "git branch -dr origin/old-branch",
    "git branch --delete --force other",
    "git branch -d -f other",
    "git branch -df other",
    "git checkout .",
    "git restore .",
    "git status && git push origin main",
]
ALLOWED = [
    "git status",
    "python scripts/release-readiness.py --help",
    "git push -u origin skills/new-guard",
    "git push --receive-pack git-receive-pack origin feature",
    "git push origin --receive-pack=git-receive-pack feature",
    "git push --exec git-receive-pack origin feature",
    "git push origin --exec=git-receive-pack feature",
    "git push -o audit origin feature",
    "git push origin --push-option audit feature",
    "git push --push-option=audit origin feature",
    "git push -oaudit origin feature",
    "git push -- origin feature",
    "git push origin -- feature",
    "git push -u -- origin feature",
    "git update-ref refs/heads/topic 1234567890123456789012345678901234567890",
    "git push origin feature:feature",
    "git push origin refs/heads/feature:refs/heads/feature",
    "git fetch origin main",
    "git pull --ff-only origin main",
    "git reset --soft HEAD~1",
    "git clean -nd",
    "git clean -nfd",
    "git clean --dry-run -fd",
    "git checkout -- file.txt",
    "git restore file.txt",
    "printf 'gh pr merge 593'",
    "git push -u origin feature && gh pr view 593",
]

# Exercise every command against the exact hook module without restarting the
# interpreter for every fixture. Process-level exit codes remain checked below.
spec = importlib.util.spec_from_file_location("claude_git_guard", HOOK)
assert spec is not None and spec.loader is not None
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)
for should_deny, cases in [(True, DENIED), (False, ALLOWED)]:
    for command in cases:
        reasons = [hook.unsafe_command(part) for part in hook.split_commands(command)]
        assert any(reasons) == should_deny, (command, reasons, should_deny)

# Preserve the real Python CLI contract (JSON transport, exit 2 on blocked,
# exit 0 on allowed), rather than relying exclusively on in-process calls.
for command, expected in [
    ("gh pr merge 593", 2),
    ("git push --receive-pack git-receive-pack origin", 2),
    ("git push -u origin skills/new-guard", 0),
    ("git status", 0),
]:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
        text=True, capture_output=True, check=False,
    )
    assert result.returncode == expected, (command, result.returncode, result.stderr)
    if expected == 2:
        assert "BLOCKED:" in result.stderr, command

# Invalid hook JSON must be denied explicitly (exit 2), not crash (exit 1)
# or silently allow the Bash call (exit 0). The shell fallback also denies
# crashes, but the direct Python hook should be predictable independently.
for invalid in [
    "[]", "null", "{}", '{"tool_input": null}', '{"tool_input": []}',
    '{"tool_input": {"command": 42}}', '{"tool_input": {"command": ""}}',
    "not json",
]:
    result = subprocess.run(
        [sys.executable, str(HOOK)], input=invalid, text=True,
        capture_output=True, check=False,
    )
    assert result.returncode == 2 and "BLOCKED:" in result.stderr, (
        invalid, result.returncode, result.stderr
    )

# Also exercise the actual command in .claude/settings.json, not just the
# Python implementation. Claude PreToolUse exits other than 2 FAIL OPEN.
config = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
assert config["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == (
    'sh "${CLAUDE_PROJECT_DIR}/.claude/hooks/guard-main.sh"'
)

# A second independent layer uses Claude Code’s built-in deny rules; it does
# not rely on Python, hook exit status or CI and never denies branch PR pushes.
assert config["permissions"]["deny"] == [
    "Bash(gh pr merge *)",
    "Bash(git merge *)",
    "Bash(git branch -d *)",
    "Bash(git branch -D *)",
    "Bash(git branch --delete *)",
]
assert all("git push" not in rule for rule in config["permissions"]["deny"])

if os.name != "nt":
    LAUNCHER = ROOT / ".claude/hooks/guard-main.sh"

    def run_launcher(command: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["/bin/sh", str(LAUNCHER)],
            input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    base_env = dict(os.environ, CLAUDE_PROJECT_DIR=str(ROOT))
    for command, expected in [
        ("gh pr merge 593", 2),
        ("git push origin main", 2),
        ("git push -u origin feature", 0),
        ("git status", 0),
    ]:
        actual = run_launcher(command, base_env)
        assert actual.returncode == expected, (command, actual.returncode, actual.stderr)
    without_python = run_launcher("git status", dict(base_env, PATH=""))
    assert without_python.returncode == 2
    assert "BLOCKED" in without_python.stderr
    without_root = run_launcher("git status", {key: val for key, val in base_env.items() if key != "CLAUDE_PROJECT_DIR"})
    assert without_root.returncode == 2

    with tempfile.TemporaryDirectory() as tmp:
        fake_python = Path(tmp) / "python3"
        fake_python.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        fake_python.chmod(0o755)
        broken = run_launcher("git status", dict(base_env, PATH=tmp))
        assert broken.returncode == 2, broken.stderr

print(f"PASS Claude agent Git guard: {len(DENIED)} denies; {len(ALLOWED)} allows")

