import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('responsive_image_checker',ROOT/'scripts/check-responsive-images.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def audit(html,root):
    p=root/'fixture.html'
    p.write_text(html,encoding='utf-8')
    return module.audit_file(p,root)

with TemporaryDirectory() as d:
    root=Path(d)
    cases=[
        ('single-quoted dimensions',"<img src='/foto.webp' alt='Portada' width='400' height='600'>",lambda e:not any('MISSING_DIMENSIONS' in v for v in e)),
        ('single-quoted missing sizes',"<img src='/foto.webp' width='400' height='600' srcset='/foto.webp 400w'>",lambda e:any('SRCSET_WITHOUT_SIZES' in v for v in e)),
        ('reordered robots attributes','<meta content="noindex,follow" name="robots"><img src="/foto.webp" alt="Portada">',lambda e:e==[]),
        ('uppercase robots',"<meta NAME='ROBOTS' CONTENT='NOINDEX'><img src='/foto.webp'>",lambda e:e==[]),
        ('mixed-case lazy priority','<img src="/foto.webp" width="400" height="600" loading="LAZY" fetchpriority="HIGH">',lambda e:any('INCOHERENT_LOADING' in v for v in e)),
    ]
    failures=[]
    for label,html,expect in cases:
        actual=audit(html,root)
        if not expect(actual):failures.append(f'{label}: {actual}')
    assert not failures,'\n'.join(failures)
print('PASS responsive image parser adversarial cases')
