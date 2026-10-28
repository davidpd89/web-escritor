import unittest
from test_atlas_contract_schema import full, mod


class ImageReverseLinksTest(unittest.TestCase):
    def test_approved_image_cannot_lack_place_backlink(self):
        data = full()
        self.assertEqual(mod.problems(data), [])
        self.assertIn('img-a', data['places'][0]['image_ids'])
        for replacement in ([], None):
            with self.subTest(image_ids=replacement):
                changed = full()
                if replacement is None:
                    changed['places'][0].pop('image_ids')
                else:
                    changed['places'][0]['image_ids'] = replacement
                self.assertTrue(
                    mod.problems(changed),
                    'Imagen aprobada sin vínculo inverso aceptada'
                )


if __name__ == '__main__':
    unittest.main()
