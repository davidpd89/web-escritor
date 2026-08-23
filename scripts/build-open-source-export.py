#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, shutil, sys
from pathlib import Path
from urllib.parse import urlparse

BLOCKED_NAMES={'.env','script.js','editorial-facts.json','private-tools-privacy-manifest.example.json'}
BLOCKED_FRAGMENTS=('api_key','apikey','secret','password','authorization: bearer','xkeysib-','private manus','@davidpuede')
ALLOWED_EXT={'.js','.mjs','.css','.html','.json','.md','.py'}

# P.2 (2026-08-23): cierre de dependencias locales. Un tool.files incompleto
# (declara el motor pero no un modulo local que ese motor importa de verdad)
# produce un export que no funciona fuera de este repo -- el caso real
# encontrado fue legibilidad-engine.js -> silabajs-lite-2.1.0.js. Solo
# seguimos imports relativos locales ('./x' o '../x'); imports de paquetes
# npm no existen en este repo y no se contemplan aqui.
LOCAL_IMPORT_RE=re.compile(r"""(?:import\s+(?:[^'"();]*?from\s+)?|export\s+(?:[^'"();]*?from\s+)?|require\(\s*)['"](\.{1,2}/[^'"]+)['"]""")

# Marcadores heuristicos de que un fichero es una adaptacion/copia de codigo
# de terceros y por tanto DEBE aparecer en third_party. Basado en el patron
# real ya usado en este repo (silabajs-lite-2.1.0.js declara "Adaptación
# ... Upstream: ... Licencia upstream: ..." en su cabecera).
ADAPTATION_MARKERS=('adaptación','adaptacion','upstream:','adapted from','licencia upstream')

def sha256(p):
    h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()

def local_imports(path):
    try: text=path.read_text(encoding='utf-8',errors='ignore')
    except OSError: return []
    return [m.group(1) for m in LOCAL_IMPORT_RE.finditer(text)]

def closure_files(entry_files, source):
    """BFS sobre imports relativos locales a partir de entry_files (Path
    resueltos). Devuelve el conjunto completo de ficheros locales alcanzados
    (incluidos los propios entry_files). Ignora imports que resuelven fuera
    de source (no deberian existir en este repo; si aparecen, se ignoran en
    vez de fallar aqui -- el confinamiento de path ya se valida por separado
    para los ficheros declarados)."""
    source_resolved=source.resolve()
    seen={f.resolve() for f in entry_files}
    queue=list(seen)
    while queue:
        current=queue.pop()
        for rel in local_imports(current):
            resolved=(current.parent/rel).resolve()
            if source_resolved!=resolved and source_resolved not in resolved.parents: continue
            if not resolved.is_file(): continue
            if resolved not in seen:
                seen.add(resolved); queue.append(resolved)
    return seen

def looks_like_adaptation(path):
    try: head=path.read_text(encoding='utf-8',errors='ignore')[:2000].lower()
    except OSError: return False
    return any(marker in head for marker in ADAPTATION_MARKERS)

def validate(data, source):
    if data.get('license') not in {None,'MIT','Apache-2.0'}: raise ValueError('license debe ser null, MIT o Apache-2.0')
    topics=data.get('topics') or []
    if len(topics)>20 or any(not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,49}',x) for x in topics): raise ValueError('topics inválidos')
    tools=[];seen=set()
    for t in data.get('tools',[]):
        if not t.get('export'): continue
        slug=t.get('slug','')
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,60}',slug): raise ValueError(f'slug inválido {slug!r}')
        if slug in seen: raise ValueError(f'slug duplicado {slug}')
        seen.add(slug)
        if not t.get('name') or len(t.get('description',''))<40: raise ValueError(f'{slug}: metadata insuficiente')
        p=urlparse(t.get('demo_url',''))
        if p.scheme!='https' or p.netloc!='davidportodiaz.com' or not p.path.startswith('/herramientas/'): raise ValueError(f'{slug}: demo_url inválida')
        files=[]
        for rel in t.get('files',[]):
            if Path(rel).name in BLOCKED_NAMES or Path(rel).suffix not in ALLOWED_EXT: raise ValueError(f'{slug}: archivo no permitido {rel}')
            f=(source/rel).resolve()
            if source.resolve() not in f.parents: raise ValueError(f'{slug}: path sale de source')
            if not f.is_file(): raise ValueError(f'{slug}: no existe {rel}')
            low=f.read_text(encoding='utf-8',errors='ignore').lower()
            if any(x in low for x in BLOCKED_FRAGMENTS): raise ValueError(f'{slug}: posible secreto/dato privado en {rel}')
            files.append((rel,f))
        if not files: raise ValueError(f'{slug}: sin archivos')

        # Cierre de dependencias locales (P.2): cualquier import relativo
        # estatico alcanzable desde los ficheros declarados debe estar EL
        # MISMO declarado en 'files'. No se auto-incluye en silencio: se
        # exige declaracion explicita humana en el manifest.
        declared_resolved={f.resolve() for _,f in files}
        full_closure=closure_files([f for _,f in files], source)
        missing=full_closure-declared_resolved
        if missing:
            missing_rel=sorted(str(m.relative_to(source.resolve())) for m in missing)
            raise ValueError(f"{slug}: faltan en 'files' dependencias locales importadas: {', '.join(missing_rel)}")

        # Adaptaciones de terceros (P.2): si algun fichero del cierre (declarado
        # o transitivo) declara en su propia cabecera que es una adaptacion de
        # codigo de terceros, esa adaptacion debe reflejarse en third_party.
        third_party_text=' | '.join(t.get('third_party') or []).lower()
        for resolved_file in full_closure:
            if looks_like_adaptation(resolved_file):
                name=resolved_file.name
                if name.lower() not in third_party_text:
                    raise ValueError(f"{slug}: {name} parece una adaptación de código de terceros (cabecera con 'Upstream'/'Adaptación') pero no está declarada en third_party")

        tools.append((t,files))
    if not tools: raise ValueError('no hay herramientas export=true')
    return tools

def root_readme(data,tools):
    rows='\n'.join(f'- **{t["name"]}** — {t["description"]} [Demo]({t["demo_url"]})' for t,_ in tools)
    lic=data.get('license') or 'PENDIENTE DE ELECCIÓN — este staging no debe publicarse como open source todavía'
    return f'''# {data['repository_name']}\n\n{data['repository_description']}\n\n## Herramientas\n\n{rows}\n\n## Principios\n\n- Utilidades pequeñas y comprensibles.\n- Sin backlinks insertados en resultados.\n- Privacidad explícita cuando se procesa texto.\n- Sin promesas de calidad literaria ni SEO.\n\n## Licencia\n\n{lic}\n\nLa web de demostración y el contenido editorial de davidportodiaz.com no forman parte automáticamente de esta licencia.\n'''

def tool_readme(t):
    third='\n'.join(f'- {x}' for x in t.get('third_party',[])) or '- Sin dependencias de terceros declaradas en este export.'
    return f'''# {t['name']}\n\n{t['description']}\n\nDemo: {t['demo_url']}\n\n## Dependencias / avisos\n\n{third}\n\n## Alcance\n\nConsulta la documentación de la demo para límites y metodología. Este código no asigna una nota universal de calidad al manuscrito.\n'''

def main():
    ap=argparse.ArgumentParser();ap.add_argument('manifest',type=Path);ap.add_argument('--source',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);ap.add_argument('--check',action='store_true');a=ap.parse_args()
    d=json.loads(a.manifest.read_text(encoding='utf-8'));source=a.source.resolve();tools=validate(d,source)
    if a.check:
        manifest_file=a.output/'EXPORT-MANIFEST.json'
        if not manifest_file.exists(): print('FAIL: staging no existe',file=sys.stderr);return 1
        current=json.loads(manifest_file.read_text(encoding='utf-8'))
        for item in current.get('files',[]):
            p=a.output/item['path']
            if not p.exists() or sha256(p)!=item['sha256']: print(f'FAIL: deriva {item["path"]}',file=sys.stderr);return 1
        # P.2, requisito 7: --check tambien debe detectar que el manifest
        # fuente actual (que herramientas tienen export:true ahora mismo) ya
        # no corresponde con lo que el staging tiene generado, no solo que
        # los ficheros ya copiados no hayan cambiado de contenido.
        current_slugs=set(current.get('tools',[]))
        expected_slugs={t['slug'] for t,_ in tools}
        if current_slugs!=expected_slugs:
            print(f'FAIL: el staging no corresponde al manifest actual (staging={sorted(current_slugs)}, manifest={sorted(expected_slugs)}); regenera con build-open-source-export.py sin --check',file=sys.stderr);return 1
        print(f'PASS: staging íntegro ({len(tools)} herramientas)');return 0
    if a.output.exists(): shutil.rmtree(a.output)
    a.output.mkdir(parents=True)
    records=[]
    (a.output/'README.md').write_text(root_readme(d,tools),encoding='utf-8')
    for t,files in tools:
        dst=a.output/'tools'/t['slug'];dst.mkdir(parents=True)
        (dst/'README.md').write_text(tool_readme(t),encoding='utf-8')
        for rel,f in files:
            out=dst/Path(rel).name;shutil.copy2(f,out);records.append({'path':str(out.relative_to(a.output)),'sha256':sha256(out)})
    notices=[]
    for t,_ in tools:
        for n in t.get('third_party',[]): notices.append(f'{t["slug"]}: {n}')
    (a.output/'THIRD_PARTY_NOTICES.md').write_text('# Third-party notices\n\n'+('\n'.join(f'- {x}' for x in notices) if notices else 'Ninguno declarado.')+'\n',encoding='utf-8')
    if d.get('license') is None:
        (a.output/'LICENSE-REQUIRED.txt').write_text('No publicar este staging como open source hasta elegir y añadir una licencia explícita (recomendación a decidir: MIT o Apache-2.0).\n',encoding='utf-8')
    export={'repository':d['repository_name'],'license':d.get('license'),'tools':[t['slug'] for t,_ in tools],'files':records}
    (a.output/'EXPORT-MANIFEST.json').write_text(json.dumps(export,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'GENERATED: {len(tools)} herramientas, {len(records)} archivos')
    return 0
if __name__=='__main__':
    try: raise SystemExit(main())
    except ValueError as e: print(f'FAIL: {e}',file=sys.stderr);raise SystemExit(1)
