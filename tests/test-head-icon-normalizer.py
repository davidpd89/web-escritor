#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"scripts"/"check-head-icons.py"
spec=importlib.util.spec_from_file_location("head_icons",path)
module=importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)

source='''<link href="/assets/icon-512.png" sizes="32x32" rel="shortcut icon">
<link rel="apple-touch-icon" href="/assets/david-porto-favicon.png" />'''
normalized=module.normalize(source)
assert '<link rel="icon" href="/favicon.ico" sizes="any" />' in normalized
assert '/assets/icon-512.png' not in normalized
assert '<link rel="apple-touch-icon" href="/assets/david-porto-favicon.png" />' in normalized
assert module.normalize(normalized)==normalized
assert path not in module.tracked_targets(),"normalizer must not scan its own constants/docstring"

# Repository-wide regression guard: any future browser favicon declaration in
# a tracked HTML page or Python generator must already be canonical. This is
# intentionally broader than the historical david-porto-favicon.png bug.
dirty=[]
for target in module.tracked_targets():
    original=target.read_text(encoding="utf-8")
    if module.normalize(original)!=original:
        dirty.append(target.relative_to(ROOT).as_posix())
assert not dirty, "non-canonical browser favicon declarations: "+", ".join(dirty[:50])

print("PASS head icon normalizer: browser favicon canonical sitewide; Apple touch brand preserved")
