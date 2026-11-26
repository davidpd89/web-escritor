"""Las auditorías de paridad con producción comparan contra la vista publicada (almacén de portadas), no contra el fuente crudo."""
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
node = shutil.which("node")
if node:
    for script in ("qa/cover-store-view-test.mjs", "qa/cover-store-route-test.mjs"):
        done = subprocess.run([node, script], cwd=ROOT, capture_output=True, text=True)
        assert done.returncode == 0, done.stdout + done.stderr
# Clase: la QA de navegador sobre el dist (portadas con URL del almacén) no depende de la red de Pages.
for path in sorted((ROOT / "qa").glob("*.mjs")):
    text = path.read_text(encoding="utf-8")
    if "build-public-dist" in text and "newContext(" in text:
        assert "withCoverStore(" in text, f"{path.name}: abre el dist publicado sin withCoverStore (portadas por la red de Pages)"
# Método: una auditoría de producción solo lee ficheros del repo con readPublished (la vista que publica el
# despliegue, con las portadas del almacén reescritas). Leer el fuente crudo hace que una portada ya movida al
# almacén parezca rota (404 en el dominio) o distinta en producción, sea cual sea la comprobación que la use.
# Solo la configuración de data/ (que no se compara con producción) se lee directamente.
RAW_READ = re.compile(r"\b(?:readFileSync|readFile|createReadStream)\s*\(\s*(?![\"'`]data/)([^,)]*)")
# Regresión: un espacio antes del paréntesis o las comillas dobles no esconden una lectura cruda.
for sample, hit in (("readFileSync(p)", True), ("readFileSync (p)", True), ("fs.readFile\t(x, cb)", True),
                    ("readFileSync('data/a.json')", False), ('readFileSync("data/a.json")', False)):
    assert bool(RAW_READ.search(sample)) is hit, sample
bad = []
for path in sorted((ROOT / "qa").glob("production-*.mjs")):
    text = path.read_text(encoding="utf-8")
    bad += [f"{path.name}: lectura cruda de {m.group(1).strip() or '?'}" for m in RAW_READ.finditer(text)]
assert not bad, "usar readPublished (qa/lib/cover-store-view.mjs):\n" + "\n".join(bad)
if node:
    # readPublished reescribe texto publicado, deja binarios intactos y es idempotente.
    probe = (
        "import fs from 'node:fs';import os from 'node:os';import path from 'node:path';"
        "import {readPublished} from './qa/lib/cover-store-view.mjs';"
        "const d=fs.mkdtempSync(path.join(os.tmpdir(),'rp-'));"
        "const store={base:'https://s.example/p',stored:new Set(['isbn-1.webp']),extra:[],where:{}};"
        "const h=path.join(d,'a.html');fs.writeFileSync(h,'<img src=\"/assets/reading-covers/isbn-1.webp\">');"
        "const b=path.join(d,'a.webp');fs.writeFileSync(b,'/assets/reading-covers/isbn-1.webp');"
        "const v=readPublished(h,{store});"
        "if(!v.includes('https://s.example/p/isbn-1.webp'))throw new Error('html sin reescribir '+v);"
        "if(readPublished(b,{store,encoding:null}).toString()!=='/assets/reading-covers/isbn-1.webp')throw new Error('binario tocado');"
        "fs.writeFileSync(h,v);if(readPublished(h,{store})!==v)throw new Error('no idempotente');"
    )
    done = subprocess.run([node, "--input-type=module", "-e", probe], cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr
print("PASS: auditorías de producción con vista del almacén de portadas")
