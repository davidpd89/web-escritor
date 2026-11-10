"""Check changed HTML on publication; retain full scheduled/manual audits.

Unchanged remote maintenance must not stall unrelated book updates. No HTTP
status is waived: Lychee and its independent recheck keep their existing rules.
"""
import json
import os
import re
import subprocess
from pathlib import Path

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arbol_publicado  # noqa: E402  (árbol publicado: versionado + generado en disco)


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
        raise ValueError('No HTML inputs; refusing an empty link check')
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
            removed=git(root,'diff','--find-renames','--name-only','-z','--diff-filter=DR',base,'HEAD','--','*.html')
            changed=public_html(git(root,'diff','--name-only','-z','--diff-filter=ACMT',base,'HEAD','--','*.html').split('\0'))
            if not removed and changed:
                return {'scope':'changed-html','base':base,'files':changed,
                        'reason':'every added or modified HTML page; no deletions or renames'}
            reason='HTML removed/renamed or no changed public HTML; checking all remaining pages'
        except subprocess.CalledProcessError:
            reason='comparison unavailable; checking all pages'
    return {'scope':'full-site','base':base,'files':all_files,'reason':reason}


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
    message=f"Link scope: {result['scope']}; {len(result['files'])} HTML pages. {result['reason']}."
    print(message)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as summary:
            summary.write(message+'\nFull-site audits run on schedule, on manual main dispatch, or with full_scan=true.\n')
