"""Generated-book boundaries, pagination and branch-policy checks; no mutations."""
import importlib.util
import json
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
             'assets/page-order.generated.js']:
    assert m.allowed_path(path), path
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

deploy = (ROOT / '.github/workflows/deploy-pages.yml').read_text(encoding='utf-8')
assert 'github.event.before || inputs.before_sha' in deploy
assert 'git merge-base --is-ancestor "$BEFORE_SHA" HEAD' in deploy
assert '[[ "$BEFORE_SHA" =~ ^[0-9a-f]{40}$ ]]' in deploy
print('PASS reading publication: branch policy, all file pages, rename origins and bounded IndexNow ancestor')
