#!/usr/bin/env python3
"""PR95 optional media gate.

Empty slots are valid while the PR is in design/staging. As soon as a final
banner is added under assets/banners/, its dimensions become contractual.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BANNERS = ROOT / "assets" / "banners"
EXPECTED = (2400, 900)
NAMES = (
    "manecillas-home-banner",
    "samuel-home-banner",
    "memoria-tierras-norte-home-banner",
    "herramientas-home-banner",
)

errors = []
found = 0
for stem in NAMES:
    candidates = [BANNERS / f"{stem}.webp", BANNERS / f"{stem}.jpg"]
    existing = [path for path in candidates if path.exists()]
    if not existing:
        print(f"PENDING: {stem} — slot remains valid without final image")
        continue
    if len(existing) > 1:
        errors.append(f"{stem}: keep only one final format (.webp preferred), found {', '.join(p.name for p in existing)}")
        continue
    path = existing[0]
    found += 1
    try:
        with Image.open(path) as image:
            size = image.size
    except Exception as exc:
        errors.append(f"{path}: cannot open image: {exc}")
        continue
    if size != EXPECTED:
        errors.append(f"{path}: {size[0]}x{size[1]}, expected exactly {EXPECTED[0]}x{EXPECTED[1]}")
    else:
        print(f"OK: {path.relative_to(ROOT)} — {size[0]}x{size[1]}")

if errors:
    print("PR95 design asset gate FAILED:")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)

print(f"PR95 design asset gate: OK ({found}/{len(NAMES)} final banners present; missing files are allowed in draft/staging)")
