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
print('PASS social inventory: tracked source and hidden-free export, no private browser or worktree copies')
