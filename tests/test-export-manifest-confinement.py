import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/'scripts/build-open-source-export.py'
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    source=root/'source'
    assets=source/'assets'
    assets.mkdir(parents=True)
    (assets/'core.js').write_text('export const suma=(a,b)=>a+b;\n',encoding='utf-8')
    manifest={
        'repository_name':'qa-open-export',
        'repository_description':'Exportación aislada para comprobar confinamiento.',
        'license':None,
        'topics':['writing-tools'],
        'tools':[{'slug':'qa-core','name':'Core QA','description':'Herramienta sintética con longitud suficiente para validar la exportación.', 'demo_url':'https://davidportodiaz.com/herramientas/qa-core/', 'export':True,'files':['assets/core.js'],'third_party':[]}]
    }
    manifest_file=root/'manifest.json'
    manifest_file.write_text(json.dumps(manifest),encoding='utf-8')
    out=root/'staging'
    command=[sys.executable,str(script),str(manifest_file),'--source',str(source),'--output',str(out)]
    clean=subprocess.run(command,capture_output=True,text=True)
    assert clean.returncode==0,(clean.stdout,clean.stderr)
    check=subprocess.run(command+['--check'],capture_output=True,text=True)
    assert check.returncode==0,(check.stdout,check.stderr)
    outside=root/'outside.txt'
    outside.write_text('contenido ajeno al staging',encoding='utf-8')
    output_manifest=out/'EXPORT-MANIFEST.json'
    payload=json.loads(output_manifest.read_text(encoding='utf-8'))
    payload['files'].append({'path':'../outside.txt','sha256':hashlib.sha256(outside.read_bytes()).hexdigest()})
    output_manifest.write_text(json.dumps(payload),encoding='utf-8')
    attacked=subprocess.run(command+['--check'],capture_output=True,text=True)
    assert attacked.returncode!=0,('El verificador aceptó un manifiesto que sale del staging',attacked.stdout,attacked.stderr)
print('OK: confinamiento del manifiesto de exportación')
