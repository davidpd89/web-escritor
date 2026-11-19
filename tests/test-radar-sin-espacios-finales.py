#!/usr/bin/env python3
"""El HTML del radar no debe llevar espacios al final de linea, ni con 0 fichas
en seguimiento (el refresco fallaba en `git diff --check`, 19/11)."""
import importlib.util, pathlib, sys
root = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("brad", root / "scripts/build-radar-opportunities.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
out = m.strip_trailing_space("a  \n    \nb\t\n")
assert out == "a\n\nb\n", repr(out)
print("OK: sin espacios finales")
