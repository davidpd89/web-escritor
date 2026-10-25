import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('picture_checker',ROOT/'scripts/check-responsive-images.py')
checker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

with TemporaryDirectory() as d:
    root=Path(d)
    assets=root/'assets';assets.mkdir()
    for name in ('small.webp','large.webp'):(assets/name).write_bytes(b'fixture')
    page=root/'index.html'
    def run(source):
        page.write_text('<picture>'+source+'<img src="/assets/small.webp" width="400" height="600" alt="Portada"></picture>',encoding='utf-8')
        return checker.audit_file(page,root)
    missing=run('<source media="(min-width: 700px)" srcset="/assets/small.webp 400w, /assets/large.webp 800w">')
    assert any('SRCSET_WITHOUT_SIZES' in item for item in missing),f'Undetected source without sizes: {missing}'
    correct=run('<source media="(min-width: 700px)" srcset="/assets/small.webp 400w, /assets/large.webp 800w" sizes="50vw">')
    assert not any('SRCSET_WITHOUT_SIZES' in item for item in correct),f'False positive: {correct}'
    density=run('<source media="(min-width: 700px)" srcset="/assets/small.webp 1x, /assets/large.webp 2x">')
    assert not any('SRCSET_WITHOUT_SIZES' in item for item in density),f'Density descriptors must not require sizes: {density}'
print('PASS responsive picture source sizes')
