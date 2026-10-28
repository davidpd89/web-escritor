import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class VideoDocument(HTMLParser):
    def __init__(self):
        super().__init__()
        self.video = []
        self.sources = []
        self.policies = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'video':
            self.video.append(attrs)
        elif tag == 'source':
            self.sources.append(attrs)
        elif tag == 'meta' and (attrs.get('http-equiv') or '').lower() == 'content-security-policy':
            self.policies.append(attrs.get('content', ''))

class VideoResourceContract(unittest.TestCase):
    def test_video_resources_and_csp(self):
        page = 'video-ios-test/index.html'
        parser = VideoDocument()
        parser.feed((ROOT / page).read_text(encoding='utf-8'))
        self.assertEqual(len(parser.video), 1, f'{page}: se esperaba un vídeo de diagnóstico')
        self.assertTrue(parser.sources, f'{page}: falta source de vídeo')
        self.assertEqual(len(parser.policies), 1, f'{page}: falta CSP única')
        policy = {}
        for raw in parser.policies[0].split(';'):
            parts = raw.strip().split()
            if parts:
                policy[parts[0]] = parts[1:]
        for directive in ('media-src', 'img-src', 'connect-src'):
            self.assertIn("'self'", policy.get(directive, []), f'{page}: {directive} impide recursos locales')
        resources = [(parser.video[0].get('poster'), 'cartel')]
        for source in parser.sources:
            self.assertEqual(source.get('type'), 'video/mp4', f'{page}: tipo MIME audiovisual inesperado')
            resources.append((source.get('src'), 'vídeo'))
        for url, kind in resources:
            self.assertTrue(url, f'{page}: falta URL del {kind}')
            parsed = urlsplit(url)
            self.assertFalse(parsed.scheme or parsed.netloc, f'{page}: {kind} externo {url}')
            self.assertTrue(parsed.path.startswith('/assets/'), f'{page}: {kind} fuera de assets: {url}')
            self.assertTrue((ROOT / parsed.path.lstrip('/')).is_file(), f'{page}: no existe el {kind} {url}')

if __name__ == '__main__':
    unittest.main()
