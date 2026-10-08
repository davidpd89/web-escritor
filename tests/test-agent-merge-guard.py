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
    "git switch --discard-changes feature",
    "git switch --force feature",
    "git switch -f feature",
    "git switch -fc new-feature",
    "git checkout -f feature",
    "git checkout --force feature",
    "git checkout -- :/",
    "git checkout HEAD -- :/",
    "git restore -- :/",
    "git restore --staged -- :/",
    "git checkout -- ':/*'",
    "git restore -- ':(top)**'",
    "git restore -- ':(glob)**'",
    "gh pr merge 593",
    "git symbolic-ref refs/remotes/origin/alias refs/heads/main",
    "git symbolic-ref refs/tags/alias refs/heads/main",
    "git update-ref refs/remotes/origin/alias 1111111111111111111111111111111111111111",
    "git update-ref refs/tags/alias 1111111111111111111111111111111111111111",
    "git update-ref -d refs/tags/alias",
    "git symbolic-ref --delete refs/remotes/origin/alias",
    "git symbolic-ref --quiet HEAD refs/heads/main",
    "git update-ref refs/notes/commits 1111111111111111111111111111111111111111",
    "git update-ref refs/heads/topic 1234567890123456789012345678901234567890",
    "git symbolic-ref refs/heads/topic refs/heads/feature",
    "git update-ref refs/heads/topic HEAD",
    "git symbolic-ref refs/heads/topic refs/heads/main",
    "git update-ref -m 'refs/heads/main' refs/heads/topic HEAD",
    "git update-ref refs/heads/topic 1111111111111111111111111111111111111111 0000000000000000000000000000000000000000",
    "git update-ref -m \"branch creation\" refs/heads/topic 1111111111111111111111111111111111111111 0000000000000000000000000000000000000000",
    "git symbolic-ref -m 'alias' refs/heads/feature refs/heads/main",
    "GH_HOST=github.com gh pr merge 593",
    "GIT_TRACE=1 git push origin main",
    "A=1 B=2 gh api repos/davidpd89/web-escritor/pulls/593/merge -X PUT",
    "TRACE='two words' git branch -D old-branch",
    "git update-ref refs/heads/main 1234567890123456789012345678901234567890",
    "git update-ref HEAD 1234567890123456789012345678901234567890",
    "git symbolic-ref refs/heads/main refs/heads/topic",
    "git update-ref -m 'review note' refs/heads/main 1234567890123456789012345678901234567890",
    "git symbolic-ref -m 'review note' HEAD refs/heads/topic",
    "git symbolic-ref --delete HEAD",
    "git update-ref refs/heads/feature 0000000000000000000000000000000000000000",
    "git update-ref -m \"delete\" refs/heads/old-feature 0000000000000000000000000000000000000000",
    "git update-ref refs/heads/legacy 0000000000000000000000000000000000000000000000000000000000000000",
    "gh \\\npr merge 593",
    "git \\\npush origin main",
    "git push origin fea\\\nture:main",
    "GH_HOST=github.com gh \\\npr merge 593",
    "GIT_TRACE=1 git \\\npush origin main",
    "gh pr -R davidpd89/web-escritor merge 593",
    "gh --repo davidpd89/web-escritor pr merge 593 --squash",
    "npm test && gh pr merge 593",
    "gh api repos/davidpd89/web-escritor/pulls/593/merge -X PUT",
    "gh api -X PUT repos/davidpd89/web-escritor/pulls/593/merge",
    "gh api -X PUT /repos/davidpd89/web-escritor/pulls/593/merge",
    "gh api -X PUT https://api.github.com/repos/davidpd89/web-escritor/pulls/593/merge",
    "gh api repos/davidpd89/web-escritor/pulls/593/merge-async -X PUT",
    "gh api https://api.github.com/repos/davidpd89/web-escritor/pulls/593/merge-async -X PUT",
    "gh api repos/davidpd89/web-escritor/merges -X POST -f base=main -f head=feature",
    "gh api -X POST /repos/davidpd89/web-escritor/merges -f base=main -f head=feature",
    "gh api graphql -f 'query=mutation { mergePullRequest(input: {pullRequestId: \"PR\"}) { clientMutationId } }'",
    "gh api graphql -f 'query=mutation { enablePullRequestAutoMerge(input: {pullRequestId: \"PR\"}) { clientMutationId } }'",
    "gh api graphql -f 'query=mutation { enqueuePullRequest(input: {pullRequestId: \"PR\"}) { clientMutationId } }'",
    "gh api graphql -f 'query=mutation { mergeBranch(input: {repositoryId: \"R\"}) { clientMutationId } }'",
    "gh api /graphql -f 'query=mutation { mergePullRequest(input: {pullRequestId: \"PR\"}) { clientMutationId } }'",
    "gh api https://api.github.com/graphql -f 'query=mutation { enablePullRequestAutoMerge(input: {pullRequestId: \"PR\"}) { clientMutationId } }'",
    "gh api https://git.example.com/api/graphql -f 'query=mutation { mergeBranch(input: {repositoryId: \"R\"}) { clientMutationId } }'",
    "git branch -M source existing-branch",
    "git branch -C source existing-branch",
    "git branch -m source renamed",
    "git branch --move source renamed",
    "git branch -f existing-branch HEAD",
    "git branch --force existing-branch HEAD",
    "git branch -mf source existing-branch",
    "git switch -C existing-branch topic",
    "git switch --force-create existing-branch topic",
    "git switch --force-create=existing-branch topic",
    "git checkout -B existing-branch topic",
    "git checkout -Bexisting-branch topic",
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
    "git switch --merge feature",
    "git checkout -- src/file.txt",
    "git restore -- :/src/file.txt",
    "git restore --staged -- src/file.txt",
    "git checkout -- ':(top)src/file.txt'",
    "git status",
    "GIT_TRACE=1 git status",
    "GH_HOST=github.com gh pr view 593",
    "A=1 B=2 git push origin feature",
    "git symbolic-ref --short HEAD",
    "git symbolic-ref -q HEAD",
    "git symbolic-ref --no-recurse HEAD",
    "git symbolic-ref refs/heads/topic",
    "git show-ref --verify refs/heads/topic",
    "git \\\nstatus",
    "git push \\\norigin feature",
    "printf 'literal \\\n gh pr merge 593'",
    "printf \"quoted \\\n gh pr merge 593\"",
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
    "gh api graphql -f 'query=query { viewer { login } }'",
    "gh api /graphql -f 'query=query { viewer { login } }'",
    "gh api https://api.github.com/graphql -f 'query=query { viewer { login } }'",
    "git branch --list",
    "git branch topic",
    "git branch -c source copy",
    "git switch feature",
    "git switch -c new-feature",
    "git checkout feature",
    "git checkout -b new-feature",
    "gh api repos/davidpd89/web-escritor/pulls/593",
    "gh api graphql -f 'query=mutation { addComment(input: {subjectId: \"PR\", body: \"ok\"}) { clientMutationId } }'",
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
    "Bash(git branch -m *)",
    "Bash(git branch -M *)",
    "Bash(git branch -C *)",
    "Bash(git branch -f *)",
    "Bash(git branch --move *)",
    "Bash(git branch --force *)",
    "Bash(git switch -C *)",
    "Bash(git switch --force-create *)",
    "Bash(git switch --force-create=*)",
    "Bash(git checkout -B *)",
    "Bash(git checkout -B*)",
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

