import importlib.util
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('atlas_geo_gate', ROOT / 'scripts/atlas_contract_check.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

COLLECTIONS = ('destinations', 'places', 'works', 'authors', 'adaptations', 'sources', 'relationships', 'images', 'routes')


def catalogue(lat, lon):
    data = {'schema_version': 1, **{key: [] for key in COLLECTIONS}}
    data['destinations'] = [{'id': 'dst-example', 'status': 'candidate'}]
    data['places'] = [{'id': 'lug-example', 'status': 'candidate', 'destination_id': 'dst-example', 'geo_precision': 'point', 'latitude': lat, 'longitude': lon}]
    return data


class AtlasGeospatialBoundaries(unittest.TestCase):
    def test_valid_boundaries(self):
        for lat, lon in ((-90, -180), (90, 180), (0, 0), (40.4168, -3.7038)):
            with self.subTest(lat=lat, lon=lon):
                self.assertEqual(mod.problems(catalogue(lat, lon)), [])

    def test_nonfinite_coordinates_are_rejected(self):
        for value in (float('nan'), float('inf'), -float('inf')):
            for field in ('latitude', 'longitude'):
                with self.subTest(value=str(value), field=field):
                    data = catalogue(40, -3)
                    data['places'][0][field] = value
                    self.assertTrue(mod.problems(data), f'{field} acepta {value}')

    def test_invalid_types_and_out_of_range_values(self):
        for lat, lon in ((True, 0), (0, False), ('40', 0), (0, '-3'), (90.0001, 0), (0, -180.0001), (-90.0001, 0), (0, 180.0001)):
            with self.subTest(lat=lat, lon=lon):
                self.assertTrue(mod.problems(catalogue(lat, lon)))


if __name__ == '__main__':
    unittest.main()
