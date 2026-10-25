from pathlib import Path
from urllib.parse import urlsplit
import re

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'


def check():
    text = (ROOT / 'robots.txt').read_text(encoding='utf-8')
    lines = text.splitlines()
    sitemaps = [line.split(':', 1)[1].strip() for line in lines if re.match(r'^\s*Sitemap\s*:', line, re.I)]
    assert sitemaps == [ORIGIN + '/sitemap.xml'], sitemaps
    assert (ROOT / 'sitemap.xml').is_file()
    references = re.findall(r'https://davidportodiaz\.com/llms(?:-full)?\.txt', text)
    assert len(references) == 2, references
    for url in references:
        parsed = urlsplit(url)
        assert parsed.scheme == 'https' and parsed.netloc == 'davidportodiaz.com'
        assert (ROOT / parsed.path.lstrip('/')).is_file(), url
    assert re.search(r'(?im)^User-agent:\s*\*\s*$', text)
    assert re.search(r'(?im)^Allow:\s*/\s*$', text)


if __name__ == '__main__':
    check()
    print('PASS robots discovery contract')