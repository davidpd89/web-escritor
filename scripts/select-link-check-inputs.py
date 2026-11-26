"""Check changed HTML on publication; retain full scheduled/manual audits.

Unchanged remote maintenance must not stall unrelated book updates. No HTTP
status is waived: Lychee and its independent recheck keep their existing rules.
"""
import json
import os
import re
import subprocess
from urllib.parse import quote
from pathlib import Path

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arbol_publicado  # noqa: E402  (árbol publicado: versionado + generado en disco)


# Lo que ninguna página enlaza: borrarlo no rompe enlaces (Pagefind carga sus trozos por JS, no por <a>/<img>).
NOT_LINKED = ('scripts/', 'tests/', '.github/', '.ci/', 'docs/', 'data/', 'pagefind/', 'lychee/', 'qa/')


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root).decode('utf-8')


def public_html(paths):
    result=[]
    for path in paths:
        if not path.endswith('.html') or path.startswith(('scripts/', 'tests/')):
            continue
        # These values become CLI arguments, never arbitrary shell text.
        if not re.fullmatch(r'[\w./-]+\.html', path) or '..' in path.split('/'):
            raise ValueError('Unsafe HTML input path: '+repr(path))
        result.append(path)
    return sorted(set(result))


def select(root, event_name, event, ref, full_scan=False):
    all_files=public_html(arbol_publicado.listar(root, '*.html'))
    if not all_files:
        raise ValueError('No HTML inputs; refusing an empty link check')  # el sitio sin páginas sí es un fallo
    base=None
    if not full_scan:
        if event_name=='pull_request':
            base=event.get('pull_request',{}).get('base',{}).get('sha')
        elif event_name=='push':
            base=event.get('before')
        elif event_name=='workflow_dispatch' and ref!='refs/heads/main':
            try:
                base=git(root,'merge-base','origin/main','HEAD').strip()
            except subprocess.CalledProcessError:
                base=None
    reason='full audit requested or no reliable comparison'
    if isinstance(base,str) and re.fullmatch(r'[a-f0-9]{40}',base) and base!='0'*40:
        try:
            status=git(root,'diff','--find-renames','--name-status','-z',base,'HEAD').split('\0')
        except subprocess.CalledProcessError:
            status=None
            reason='comparison unavailable; checking all pages'
        if status is not None:
            removed,changed=set(),set()
            i=0
            while i<len(status)-1:
                kind=status[i]
                if not kind:
                    i+=1;continue
                if kind[0] in 'RC':
                    old,new=status[i+1],status[i+2];i+=3
                    if kind[0]=='R':removed.add(old)
                    changed.add(new)
                else:
                    path=status[i+1];i+=2
                    (removed if kind[0]=='D' else changed).add(path)
            # 26/11: cambiar el propio comprobador ya no manda a la web entera (no cabe en el job de una PR);
            # sus reglas nuevas las audita el programado semanal, que tiene más tiempo.
            removed=set(public_html(removed))|{p for p in removed if not p.endswith('.html') and not p.startswith(NOT_LINKED)}
            pages=set(public_html(changed))
            if COVER_MANIFEST in changed:
                # 26/11 (revisión de #1602): cambiar el almacén cambia URLs de portadas sin tocar el HTML.
                removed|=moved_covers(root,base)
            if removed:
                # 26/11 (carga 45868423421): borrar o renombrar páginas mandaba a revisar las 9.482 y el job
                # agotaba sus 40 min. Un borrado (página, portada, CSS) solo puede romper los enlaces que apuntan a él:
                # se revisan las páginas que lo nombran (por su último tramo, que también casa con enlaces relativos).
                pages|=set(referencing(root,removed,all_files))
            if not pages:
                # 26/11: una PR de datos que solo reindexa pagefind no trae HTML; antes caía a la web entera.
                return {'scope':'none','base':base,'files':[],
                        'reason':'no public HTML added, modified or removed; nothing to check'}
            return {'scope':'changed-html','base':base,'files':sorted(pages),
                    'reason':'every added or modified HTML page'+(' and every page naming a removed file' if removed else '')}
    return {'scope':'full-site','base':base,'files':all_files,'reason':reason}


def link_tail(path):
    """Último tramo con el que otra página enlaza a `path` (carpeta/ para index.html)."""
    parts=path.split('/')
    if parts[-1]=='index.html':
        return (parts[-2]+'/') if len(parts)>1 else None
    return parts[-1]


def referencing(root,removed,candidates):
    """Páginas publicadas que nombran un fichero borrado. Lee el árbol publicado (también lo generado sin
    versionar): `git grep` no veía las fichas generadas en disco."""
    tails={link_tail(p) for p in removed}
    if None in tails:
        return list(candidates)  # se borró la portada del sitio: cualquier página puede enlazarla
    # Un enlace puede ir codificado (ni%C3%B1o.html) o no; se buscan las dos formas.
    needles={v.encode('utf-8') for t in tails for v in (t,quote(t,safe='/'))}
    # Un index.html borrado se enlaza también sin nombrar su carpeta (index.html, ./, ../ desde dentro):
    # toda página de esa carpeta o de sus subcarpetas puede enlazarlo.
    folders=tuple(p[:-len('index.html')] for p in removed if p.endswith('/index.html'))
    found=[]
    for page in candidates:
        if folders and page.startswith(folders):
            found.append(page);continue
        try:
            content=(Path(root)/page).read_bytes()
        except OSError:
            continue
        if any(n in content for n in needles):
            found.append(page)
    return found


COVER_MANIFEST='data/reading-covers-store.json'


def moved_covers(root,base):
    """Portadas cuya URL publicada cambia con el manifiesto del almacén: el despliegue reescribe sus rutas
    /assets/reading-covers/ sin tocar el HTML versionado, así que se tratan como si se hubieran movido."""
    def urls(rev):
        try:
            data=json.loads(git(root,'show',f'{rev}:{COVER_MANIFEST}'))
        except (subprocess.CalledProcessError,ValueError):
            return {}
        where=data.get('almacen') or {};extra=data.get('almacenes') or []
        def url(name):
            k=where.get(name)
            return extra[k-1] if k and 0<k<=len(extra) else data.get('base_url','')
        return {n:url(n) for n in data.get('archivos') or []}
    before,after=urls(base),urls('HEAD')
    return {'assets/reading-covers/'+n for n in set(before)|set(after) if before.get(n)!=after.get(n)}


if __name__=='__main__':
    event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
    full=event.get('inputs',{}).get('full_scan',False)
    result=select(Path.cwd(),os.environ.get('GITHUB_EVENT_NAME',''),event,
                  os.environ.get('GITHUB_REF',''),full is True or str(full).lower()=='true')
    report=Path('lychee/input-selection.json');report.parent.mkdir(exist_ok=True)
    report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    # The list goes in a file, not on the command line: a data PR with ~2.500 new pages
    # exceeded the kernel's per-argument limit ("Argument list too long") before lychee started.
    inputs=Path('lychee/inputs.txt')
    inputs.write_text(''.join('./'+p+'\n' for p in result['files']),encoding='utf-8')
    with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as output:
        output.write('files=--files-from '+inputs.as_posix()+'\n')
        output.write('skip='+('true' if not result['files'] else 'false')+'\n')
    message=f"Link scope: {result['scope']}; {len(result['files'])} HTML pages. {result['reason']}."
    print(message)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as summary:
            summary.write(message+'\nFull-site audits run on schedule, on manual main dispatch, or with full_scan=true.\n')
