#!/usr/bin/env python3
"""One-shot cache-version regeneration for assets/v1-shell.js v14 -> v15.

Used by the post-deploy audit branch after a real shell JS change. It updates
all tracked textual references (authored HTML and builder/test sources), bumps
the canonical version contract, then records the new content hash through the
repository's existing checker.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD_REF = "v1-shell.js?v=15"
NEW_REF = "v1-shell.js?v=15"
CHECKER = ROOT / "scripts" / "check-asset-versions.py"
TEXT_EXTS = {
    ".html", ".py", ".js", ".mjs", ".json", ".yml", ".yaml", ".md", ".xml",
    ".txt", ".css"
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line]


def main() -> int:
    changed: list[str] = []
    for path in tracked_files():
        if path.suffix.lower() not in TEXT_EXTS or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if OLD_REF not in text:
            continue
        updated = text.replace(OLD_REF, NEW_REF)
        path.write_text(updated, encoding="utf-8")
        changed.append(path.relative_to(ROOT).as_posix())

    checker = CHECKER.read_text(encoding="utf-8")
    old_contract = '"v1-shell.js": "14"'
    new_contract = '"v1-shell.js": "15"'
    if old_contract in checker:
        CHECKER.write_text(checker.replace(old_contract, new_contract, 1), encoding="utf-8")
        rel = CHECKER.relative_to(ROOT).as_posix()
        if rel not in changed:
            changed.append(rel)
    elif new_contract not in checker:
        raise SystemExit("v1-shell.js version contract not found")

    subprocess.run(
        ["python", "scripts/check-asset-versions.py", "--update-hashes"],
        cwd=ROOT,
        check=True,
    )

    print(f"Updated {len(changed)} tracked reference/contract file(s) to v1-shell.js?v=15")
    for rel in changed:
        print(f" - {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
