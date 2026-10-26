import copy
import unittest

from test_atlas_contract_schema import full, mod


class ImageOwnershipTransition(unittest.TestCase):
    def test_image_approval_requires_reverse_reference(self):
        data = copy.deepcopy(full())
        place = data['places'][0]
        image = data['images'][0]
        self.assertEqual(mod.problems(data), [], 'Atlas base: referencias de imagen incoherentes')
        place['image_ids'] = []
        errors = mod.problems(data)
        self.assertTrue(any('images/img-a' in e and 'vínculo inverso' in e for e in errors), f'images/img-a: aprobación sin referencia inversa; errores={errors}')
        image['status'] = 'candidate'
        errors = mod.problems(data)
        self.assertFalse(any('images/img-a' in e and 'vínculo inverso' in e for e in errors), f'images/img-a: candidato bloqueado; errores={errors}')
        image['status'] = 'approved'
        place['image_ids'] = ['img-a']
        self.assertEqual(mod.problems(data), [], 'images/img-a: restaurar vínculo inverso no recupera catálogo válido')


if __name__ == '__main__':
    unittest.main()
