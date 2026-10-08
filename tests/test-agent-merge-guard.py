#!/usr/bin/env python3
"""Regressions for Claude Code's agent-only merge/unsafe-git hook."""
import json
import subprocess
import sys
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
    "git checkout .",
    "git restore .",
    "git status && git push origin main",
]
ALLOWED = [
    "git status",
    "python scripts/release-readiness.py --help",
    "git push -u origin skills/new-guard",
    "git push origin feature:feature",
    "git push origin refs/heads/feature:refs/heads/feature",
    "git fetch origin main",
    "git pull --ff-only origin main",
    "git reset --soft HEAD~1",
    "git clean -nd",
    "git clean -nfd",
    "git clean --dry-run -fd",
    "git branch -d old-branch",
    "git checkout -- file.txt",
    "git restore file.txt",
    "printf 'gh pr merge 593'",
    "git push -u origin feature && gh pr view 593",
]

for should_deny, cases in [(True, DENIED), (False, ALLOWED)]:
    for command in cases:
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
            text=True,
            capture_output=True,
            check=False,
        )
        expected = 2 if should_deny else 0
        assert result.returncode == expected, (
            f"{command!r}: expected {expected}, got {result.returncode}, "
            f"stdout={result.stdout!r}, stderr={result.stderr!r}"
        )
        if should_deny:
            assert "BLOCKED:" in result.stderr, command

print(f"PASS Claude agent Git guard: {len(DENIED)} denies; {len(ALLOWED)} allows")
