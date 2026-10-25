import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('indexnow', ROOT / 'scripts/indexnow.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_urls():
    valid = ['https://davidportodiaz.com/', 'https://davidportodiaz.com/editoriales/']
    invalid = [
        'http://davidportodiaz.com/',
        'https://davidportodiaz.com.evil.example/',
        'https://evil.example@davidportodiaz.com/',
        'https://user:password@davidportodiaz.com/',
        'https://davidportodiaz.com:444/',
        'https://davidportodiaz.com:443/',
        'https://davidportodiaz.com/a#fragment',
        'https://davidportodiaz.com/a?preview=1',
        'https://www.davidportodiaz.com/',
        'https://evil.example/davidportodiaz.com/'
    ]
    for url in valid:
        module.validate_url(url)
    accepted = []
    for url in invalid:
        try:
            module.validate_url(url)
        except ValueError:
            continue
        accepted.append(url)
    assert not accepted, f'URL no canónicas aceptadas: {accepted}'


if __name__ == '__main__':
    test_urls()
    print('PASS IndexNow adversarial origins')