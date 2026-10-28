import importlib.util
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('feed_robots_qa',ROOT/'scripts/build-feed.py')
feed=importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)
variants=[
    '<meta name="robots" content="noindex,follow">',
    '<meta content="NOINDEX,follow" name="robots">',
    "<META CONTENT='index, noindex' NAME='ROBOTS'>",
    '<meta name=robots content=noindex>',
]
with tempfile.TemporaryDirectory() as tmp:
    page=Path(tmp)/'index.html'
    for markup in variants:
        document='<html><head>'+markup+'<title>QA</title></head></html>'
        page.write_text(document,encoding='utf-8')
        assert feed.is_noindex(document),markup
        assert feed.extract_metadata(str(page))['skip'] is True,markup
    false_positive='<html><head><title>QA</title><script>const sample=\'<meta name="robots" content="noindex">\';</script></head></html>'
    page.write_text(false_positive,encoding='utf-8')
    assert not feed.is_noindex(false_positive),'Una cadena JS no debe imponer noindex'
    assert feed.extract_metadata(str(page))['skip'] is False
print('OK: exclusión RSS sin falsos positivos de HTML')
