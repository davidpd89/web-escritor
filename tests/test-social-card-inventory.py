"""Social audits must use the same source inventory locally and in CI."""
import importlib.util
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('social_inventory_test', ROOT / 'scripts/check-social-cards.py')
m = importlib.util.module_from_spec(spec); sys.modules[spec.name] = m; spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / 'public.html').write_text('<html></html>')
    for hidden in ['.ci/profile', '.qa-edge-profile', 'node_modules/package']:
        folder = root / hidden; folder.mkdir(parents=True)
        (folder / 'private.html').write_text('<html></html>')
    assert m.html_inventory(root) == [root / 'public.html']
    (root / 'scratch.html').write_text('<html></html>')
    (root / '.git').write_text('gitdir: worktree')
    with patch.object(m.subprocess, 'run', return_value=SimpleNamespace(stdout=b'public.html\0')) as git:
        assert m.html_inventory(root) == [root / 'public.html']
        assert '-z' in git.call_args.args[0]
# Portadas en el almacén externo (#1588): no están en el checkout; el despliegue reescribe la ruta a la URL del almacén.
import json  # noqa: E402
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / 'data').mkdir()
    (root / 'data/reading-covers-store.json').write_text(json.dumps({
        'base_url': 'https://example.github.io/portadas', 'archivos': ['isbn-1.webp'], 'sha256': {'isbn-1.webp': 'a' * 64}}))
    def page(img):
        return ('<html><head><title>t</title><link rel="canonical" href="https://davidportodiaz.com/p">'
                f'<meta property="og:image" content="https://davidportodiaz.com/assets/reading-covers/{img}">'
                f'<meta name="twitter:image" content="https://davidportodiaz.com/assets/reading-covers/{img}">'
                '</head><body></body></html>')
    def missing(img):
        (root / 'p.html').write_text(page(img), encoding='utf-8')
        audit = m.audit_page(root / 'p.html', root, 'https://davidportodiaz.com')
        return [i for i in audit.findings if 'missing-asset' in str(i)]
    assert missing('isbn-1.webp') == [], missing('isbn-1.webp')
    assert len(missing('isbn-2.webp')) == 2, missing('isbn-2.webp')
print('PASS social inventory: tracked source and hidden-free export, no private browser or worktree copies')
