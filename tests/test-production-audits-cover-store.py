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
    # Misma transformación sobre el cuerpo de producción y sobre una variable leída cruda del repo
    # (p. ej. semantic(body) frente a semantic(localHtml)): el fuente no lleva las URL del almacén.
    raw_vars = re.findall(r"(?:const|let)\s+(\w+)\s*=\s*(?:read|fs\.readFileSync)\(", text)
    on_body = set(re.findall(r"\b(\w+)\((?:r\.)?body\b", text))
    for var in raw_vars:
        for fn in set(re.findall(rf"\b(\w+)\({var}\b", text)) & on_body:
            assert fn == "expectedPublished", f"{path.name}: {fn}() compara producción con el fuente crudo `{var}`; pasar por expectedPublished"
    # JSON de producción frente a JSON del repo: el esperado también pasa por la vista publicada.
    for match in re.finditer(r"deepEqual\(JSON\.parse\((?:r\.)?body\),\s*([^;]+?),\s*\w+\)", text):
        assert "expectedPublished" in match.group(1), f"{path.name}: JSON de producción frente a {match.group(1)} crudo"
print("PASS: auditorías de producción con vista del almacén de portadas")
