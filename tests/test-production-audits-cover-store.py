"""Las auditorías de paridad con producción comparan contra la vista publicada (almacén de portadas), no contra el fuente crudo."""
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
node = shutil.which("node")
if node:
    done = subprocess.run([node, "qa/cover-store-view-test.mjs"], cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr
# Clase: toda auditoría que compare producción con un fichero del repo pasa por expectedPublished.
for path in sorted((ROOT / "qa").glob("production-*.mjs")):
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r"norm\(r\.body\),\s*norm\((\w+)\(", text):
        assert match.group(1) == "expectedPublished", f"{path.name}: compara producción con el fuente crudo ({match.group(0)})"
print("PASS: auditorías de producción con vista del almacén de portadas")
