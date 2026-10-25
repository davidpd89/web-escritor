"""Check changed HTML on publication; retain full scheduled/manual audits.

Unchanged remote maintenance must not stall unrelated book updates. No HTTP
status is waived: Lychee and its independent recheck keep their existing rules.
"""
import json
import os
import re
import subprocess
from pathlib import Path


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root).decode('utf-8')


def public_html(paths):
    result=[]
    for path in paths:
        if not path.lower().endswith('.html') or path.startswith(('scripts/', 'tests/')):
            continue
        # These values become CLI arguments, never arbitrary shell text.
        if not re.fullmatch(r'[\w./-]+\.html', path, re.IGNORECASE) or '..' in path.split('/'):
            raise ValueError('Unsafe HTML input path: '+repr(path))
        result.append(path)
    return sorted(set(result))


def select(root, event_name, event, ref, full_scan=False):
    all_files=public_html(git(root,'ls-files','-z','--',':(icase)*.html').split('\0'))
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
            removed=git(root,'diff','--find-renames','--name-only','-z','--diff-filter=DR',base,'HEAD','--',':(icase)*.html')
            changed=public_html(git(root,'diff','--name-only','-z','--diff-filter=ACMT',base,'HEAD','--',':(icase)*.html').split('\0'))
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
    with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as output:
        output.write('files='+' '.join('./'+p for p in result['files'])+'\n')
    message=f"Link scope: {result['scope']}; {len(result['files'])} HTML pages. {result['reason']}."
    print(message)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as summary:
            summary.write(message+'\nFull-site audits run on schedule, on manual main dispatch, or with full_scan=true.\n')
