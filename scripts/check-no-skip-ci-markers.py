#!/usr/bin/env python3
"""Fail when a PR targeting main carries a CI-skip marker.

GitHub squash-merges concatenate every branch commit message into the body of
the squash commit, and a push whose head commit message contains a marker such
as "[skip ci]" starts no push workflows. Deploy Pages then never runs and the
merged change stays out of production until someone dispatches it by hand
(seen on #692, #703, #724 and #669, 2026-10-23).
"""
import os
import re
import subprocess
import sys

MARKER = re.compile(
    r"\[(?:skip ci|ci skip|skip actions|actions skip)\]|\bskip-checks:\s*true\b",
    re.IGNORECASE,
)


def find_markers(texts):
    """Return (label, marker) for every text that contains a skip marker."""
    hits = []
    for label, text in texts:
        match = MARKER.search(text or "")
        if match:
            hits.append((label, match.group(0)))
    return hits


def commit_messages(base, head):
    out = subprocess.run(
        ["git", "log", "--format=%H%x1f%B%x1e", f"{base}..{head}"],
        check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout
    for record in out.split("\x1e"):
        if record.strip():
            sha, _, body = record.strip().partition("\x1f")
            yield f"commit {sha[:8]}", body


def main():
    base, head = os.environ.get("BASE_SHA"), os.environ.get("HEAD_SHA")
    if not base or not head:
        print("SKIP: BASE_SHA/HEAD_SHA not set (not a pull_request run)")
        return 0
    texts = list(commit_messages(base, head))
    texts.append(("PR title", os.environ.get("PR_TITLE", "")))
    texts.append(("PR body", os.environ.get("PR_BODY", "")))
    hits = find_markers(texts)
    for label, marker in hits:
        print(f"::error::{label} contains {marker!r}; it would stop Deploy Pages after the squash merge")
    if hits:
        print("Reword the commit (git rebase -i / commit --amend) and remove the marker.")
        return 1
    print("PASS no CI-skip markers in PR commits, title or body")
    return 0


if __name__ == "__main__":
    sys.exit(main())
