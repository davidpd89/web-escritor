import json
import unittest
from test_atlas_facets_snapshot import fixture, mod


class FacetPayloadIsolationTest(unittest.TestCase):
    def test_manifest_contains_aggregates_not_place_details(self):
        manifest, shards = mod.facet_shards(fixture())
        self.assertTrue(shards, 'Atlas: no se generaron recursos de destino')
        encoded = json.dumps(manifest, ensure_ascii=False)
        for slug, shard in shards.items():
            with self.subTest(destination=slug):
                self.assertIn(slug, encoded, f'{slug}: destino ausente del índice')
                self.assertTrue(shard['places'], f'{slug}: recurso de destino sin lugares')
                for place in shard['places']:
                    self.assertNotIn(place['id'], encoded, f'{slug}: el índice global contiene el ID del lugar {place["id"]}')
                    self.assertNotIn(place['name'], encoded, f'{slug}: el índice global contiene el nombre del lugar {place["name"]}')
                    for relation in place['relations']:
                        self.assertNotIn(relation['subject_id'], encoded, f'{slug}: relación detallada incluida en el índice global')
        for country in manifest['countries']:
            for destination in country['destinations']:
                self.assertNotIn('places', destination, f'{destination["slug"]}: lugares incrustados en el índice')
                self.assertNotIn('relations', destination, f'{destination["slug"]}: relaciones incrustadas en el índice')


if __name__ == '__main__':
    unittest.main()