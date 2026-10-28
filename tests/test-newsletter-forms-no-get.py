#!/usr/bin/env python3
"""Sin JavaScript un formulario sin method envía por GET y el email acaba en la URL, el historial y el Referer.

Todo <form data-newsletter-source> debe declarar method="post" (con JS lo intercepta el worker; sin JS no filtra el email).
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
files = subprocess.check_output(["git", "ls-files", "-z", "*.html"], cwd=ROOT).decode().split("\0")
errors, checked = [], 0
for rel in files:
    if not rel or rel.startswith(("tests/", "qa/", "lab/", "pagefind/")):
        continue
    html = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
    for tag in re.findall(r"<form\b[^>]*>", html):
        if "data-newsletter-source" not in tag:
            continue
        checked += 1
        if not re.search(r'\bmethod\s*=\s*["\']post["\']', tag, re.I):
            errors.append(f"{rel}: formulario de newsletter sin method=\"post\" (filtraría el email por GET sin JS)")
assert checked, "No se encontró ningún formulario de newsletter"
assert not errors, "\n".join(errors[:50])
print(f"PASS newsletter forms POST-only sin JS: {checked} formularios")
