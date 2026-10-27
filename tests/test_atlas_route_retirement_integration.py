import copy
import unittest

from test_atlas_contract_schema import full, mod


class RouteRetirementIntegration(unittest.TestCase):
    def test_retired_stops_cannot_remain_in_approved_routes(self):
        for stop_id in ('lug-libreria', 'lug-biblioteca'):
            with self.subTest(stop=stop_id):
                data = copy.deepcopy(full())
                stop = next(p for p in data['places'] if p['id'] == stop_id)
                stop['status'] = 'retired'
                errors = mod.problems(data)
                self.assertTrue(any('routes/rou-a' in e and stop_id in e and 'no aprobado' in e for e in errors), f'routes/rou-a: parada retirada {stop_id} no detectada; errores={errors}')
                data['routes'][0]['status'] = 'candidate'
                errors = mod.problems(data)
                self.assertFalse(any('routes/rou-a' in e and stop_id in e and 'no aprobado' in e for e in errors), f'routes/rou-a: candidato bloqueado por {stop_id}; errores={errors}')


if __name__ == '__main__':
    unittest.main()
