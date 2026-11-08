"""Generated-book boundaries, pagination and branch-policy checks; no mutations."""
import importlib.util
import json
import os
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_publication_test', ROOT / 'scripts/publish-reading-refresh.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

for path in ['data/reading-catalogue.json', 'recomendaciones/libros/obra-9780140328721/index.html',
             'recomendaciones/autores/autora/index.html', 'assets/reading-covers/isbn-9780140328721-320.webp',
             'editoriales/salamandra/index.html', 'pagefind/fragment/es_test.pf_fragment',
             'data/reading-publishers.json', 'recomendaciones/editoriales/debate/index.html',
             'recomendaciones/autores/index.html', 'recomendaciones/editoriales/index.html', 'recomendaciones/proximos-lanzamientos.ics', 'recomendaciones/llms.txt',
             'assets/page-order.generated.js', 'recomendaciones/pagina/2/index.html']:
    assert m.allowed_path(path), path
# Contrato: todo lo que escribe build-reading-catalogue debe poder publicarlo la ingesta (la paginación de #1161
# no estaba admitida y la ejecución 41981533719 falló al ensamblar la PR).
builder_spec = importlib.util.spec_from_file_location('reading_builder_contract', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(builder_spec); builder_spec.loader.exec_module(builder)
_, builder_outputs = builder.render_outputs(ROOT, json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8')))
rejected = sorted(p for p in builder_outputs if not m.allowed_path(p))
assert not rejected, 'El publicador rechazaría salidas del builder: ' + ', '.join(rejected)
for path in ['scripts/run.py', '.github/workflows/anything.yml', 'data/editoriales.json',
             'assets/reading-covers/inventada.webp', 'pagefind/../secrets', 'recomendaciones/../../scripts/run.py']:
    assert not m.allowed_path(path), path
with patch.object(m.publication, 'gh') as gh:
    for branch in ['main', 'automation/radar-clock-test', 'someone/reading-catalogue-test']:
        try:
            m.run(branch)
            raise AssertionError('Unexpected publication branch accepted')
        except ValueError:
            pass
    gh.assert_not_called()

for bad in [{'filename': 'scripts/dangerous.py'}, {'filename': 'pagefind/good.js', 'previous_filename': '.github/workflows/secret.yml'}]:
    calls = []
    def gh(*args):
        calls.append(args)
        if args[:2] == ('repo', 'view'):
            return 'owner/repo'
        if args[:2] == ('pr', 'view'):
            return json.dumps({'number': 1, 'headRefOid': 'expected', 'baseRefOid': 'base', 'baseRefName': 'main', 'state': 'OPEN'})
        if args[:3] == ('api', '--paginate', '--slurp'):
            return json.dumps([[{'filename': 'data/reading-catalogue.json'}], [bad]])
        raise AssertionError('No workflows or mutations allowed after rejected paths')
    with patch.object(m.publication, 'gh', gh):
        try:
            m.run('automation/reading-catalogue-test')
            raise AssertionError('Forbidden file on subsequent API page was ignored')
        except ValueError:
            pass
    assert not any(c[:2] == ('workflow', 'run') for c in calls)

# Árbol local de publicación (auditoría de Amazon y textos): un worktree nuevo no trae node_modules y sin él
# Pagefind no corre (07/11). Se enlaza al del checkout principal; repetirlo no hace nada.
import subprocess
import tempfile
with tempfile.TemporaryDirectory() as tmp:
    repo, tree = Path(tmp) / 'repo', Path(tmp) / 'repo/.local/main'
    repo.mkdir()
    quiet = {'cwd': repo, 'check': True, 'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL}
    subprocess.run(['git', 'init', '-q'], **quiet)
    subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'x'], **quiet)
    (repo / 'node_modules/pagefind').mkdir(parents=True)
    (repo / 'node_modules/pagefind/package.json').write_text('{}', encoding='utf-8')
    subprocess.run(['git', 'worktree', 'add', '-q', '--detach', str(tree)], **quiet)
    m.link_node_modules(tree)
    m.link_node_modules(tree)
    assert (tree / 'node_modules/pagefind/package.json').exists()
    assert (repo / 'node_modules/pagefind/package.json').exists()
    if os.name == 'nt':
        os.rmdir(tree / 'node_modules')  # quitar la junction sin tocar su destino antes de borrar el temporal
    subprocess.run(['git', 'worktree', 'remove', '--force', str(tree)], **quiet)

deploy = (ROOT / '.github/workflows/deploy-pages.yml').read_text(encoding='utf-8')
assert 'github.event.before || inputs.before_sha' in deploy
assert 'git merge-base --is-ancestor "$BEFORE_SHA" HEAD' in deploy
assert '[[ "$BEFORE_SHA" =~ ^[0-9a-f]{40}$ ]]' in deploy
print('PASS reading publication: branch policy, all file pages, rename origins and bounded IndexNow ancestor')
