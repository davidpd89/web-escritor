import unittest
from html.parser import HTMLParser
from test_atlas_static_preview import fixture, mod


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.preloads = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('img', 'picture', 'source'):
            self.images.append((tag, a))
        if tag == 'link' and 'preload' in (a.get('rel') or '').split():
            self.preloads.append(a)


class AtlasImageRequestsTest(unittest.TestCase):
    def test_preview_does_not_request_documentary_images(self):
        data = fixture()
        for path, html in mod.pages_from(data).items():
            with self.subTest(page=path):
                parser = Resources()
                parser.feed(html)
                self.assertEqual(parser.images, [], f'{path}: imágenes descargables inesperadas: {parser.images}')
                image_preloads = [a for a in parser.preloads if a.get('as') == 'image']
                self.assertEqual(image_preloads, [], f'{path}: precargas de imagen inesperadas: {image_preloads}')


if __name__ == '__main__':
    unittest.main()