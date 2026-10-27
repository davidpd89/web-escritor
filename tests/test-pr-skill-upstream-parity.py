#!/usr/bin/env python3
"""Contract for the pinned, repo-local upstream `pr` skill (Codex + Claude).

Tests normalized Git blob identities, not the skills.sh computedHash; the
latter is not a verified integrity guarantee (vercel-labs/skills #781/#806).
Update both agents from the same reviewed upstream commit and change these
pins together in a dedicated pull request.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_REPO = "mattpocock/skills"
UPSTREAM_COMMIT = "b0618bc436ad893b3c5e84e55fba86586d34a404"
# Git blob SHAs read directly from upstream at UPSTREAM_COMMIT.
SKILL_BLOBS = {
    "SKILL.md": "84dd4fb2f068e9f6282690235d20dd505b418119",
    "CREDITS.md": "5314bda2fa6005e264c9b5c1de7c425e719dc91f",
    "agents/openai.yaml": "48286f48f53b937cc19c0e39899b5f956271a98d",
}
LICENSE_BLOB = "f1dd2c09108dde1a5f56097cee8461b3ea834499"


def git_blob(path: Path) -> str:
    # Normalize checkout's CRLF to upstream's LF (Windows-safe).
    payload = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()


def main() -> None:
    for root_dir in (".agents/skills/pr", ".claude/skills/pr"):
        folder = ROOT / root_dir
        actual_files = {
            f.relative_to(folder).as_posix()
            for f in folder.rglob("*")
            if f.is_file()
        }
        assert actual_files == set(SKILL_BLOBS), (
            f"{root_dir}: expected {sorted(SKILL_BLOBS)}, got {sorted(actual_files)}"
        )
        for relpath, expected in SKILL_BLOBS.items():
            path = folder / relpath
            actual = git_blob(path)
            assert actual == expected, (
                f"{path.relative_to(ROOT)}: expected upstream {UPSTREAM_COMMIT} "
                f"blob {expected}, got {actual}"
            )

    license_path = ROOT / ".agents/skills/LICENSE.mattpocock-skills"
    assert git_blob(license_path) == LICENSE_BLOB, "Pinned MIT license diverged"
    print("PASS pinned upstream pr skill: 2 agents x 3 files + MIT license")


if __name__ == "__main__":
    main()
