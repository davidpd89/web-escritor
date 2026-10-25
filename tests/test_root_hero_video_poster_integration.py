import unittest
from pathlib import Path
from urllib.parse import urlsplit, unquote
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

class MediaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.videos = []
        self.active = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'video':
            self.active = {'attrs': a, 'sources': []}
            self.videos.append(self.active)
        elif tag == 'source' and self.active is not None:
            self.active['sources'].append(a)

    def handle_endtag(self, tag):
        if tag == 'video':
            self.active = None

def local_file(url):
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith('/'):
        raise AssertionError(f'Recurso no local: {url}')
    path = (ROOT / unquote(parsed.path).lstrip('/')).resolve()
    if not path.is_relative_to(ROOT):
        raise AssertionError(f'Recurso fuera del repositorio: {url}')
    return path

class HeroVideoIntegration(unittest.TestCase):
    def test_video_and_poster(self):
        parser = MediaParser()
        parser.feed((ROOT / 'index.html').read_text(encoding='utf-8'))
        heroes = [v for v in parser.videos if 'data-hero-video' in v['attrs']]
        self.assertEqual(len(heroes), 1, 'index.html: debe existir exactamente un vídeo introductorio')
        hero = heroes[0]
        attrs = hero['attrs']
        self.assertEqual(attrs.get('aria-hidden'), 'true', 'index.html: vídeo decorativo expuesto a lectores de pantalla')
        self.assertIn('muted', attrs, 'index.html: vídeo introductorio sin silencio')
        self.assertIn('playsinline', attrs, 'index.html: vídeo introductorio sin reproducción integrada')
        poster_url = attrs.get('poster', '')
        self.assertTrue(poster_url, 'index.html: falta el poster del vídeo')
        poster = local_file(poster_url)
        self.assertTrue(poster.is_file(), f'index.html: poster inexistente {poster_url}')
        self.assertEqual(poster.read_bytes()[:4], b'RIFF', f'index.html: poster no parece WebP: {poster_url}')
        self.assertEqual(poster.read_bytes()[8:12], b'WEBP', f'index.html: poster WebP inválido: {poster_url}')
        mp4_sources = [s for s in hero['sources'] if s.get('type') == 'video/mp4']
        self.assertTrue(mp4_sources, 'index.html: vídeo sin fuente MP4')
        for source in mp4_sources:
            url = source.get('src', '')
            path = local_file(url)
            self.assertTrue(path.is_file(), f'index.html: fuente MP4 inexistente {url}')
            with path.open('rb') as stream:
                header = stream.read(32)
            self.assertEqual(header[4:8], b'ftyp', f'index.html: archivo sin cabecera MP4: {url}')
            self.assertGreater(path.stat().st_size, 32, f'index.html: MP4 vacío: {url}')

if __name__ == '__main__':
    unittest.main()