#!/usr/bin/env python3
"""Fail when a Python test_* function is accidentally nested in another function.

A nested unittest method is syntactically valid Python but is never discovered,
which makes the suite look greener than it really is.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
issues: list[str] = []

for path in sorted(ROOT.glob("test-*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test_"):
            continue
        parent = parents.get(node)
        while parent is not None:
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                issues.append(f"{path.name}:{node.lineno}: nested test function {node.name}")
                break
            parent = parents.get(parent)

if issues:
    print("FAIL Python test discovery structure:")
    for issue in issues:
        print(" -", issue)
    raise SystemExit(1)

print("PASS Python test discovery structure: no nested test_* functions")
