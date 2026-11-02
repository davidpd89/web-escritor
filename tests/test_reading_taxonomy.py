"""Categorías adicionales y PVP a partir de la ficha oficial; sin red."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_editorial_sources import _pvp_centimos
from reading_taxonomy import extra_categories, keyword_list


class TaxonomyTests(unittest.TestCase):
    def ids(self, **record):
        return [c[0] for c in extra_categories(record)]

    def test_keywords_map_to_genre_and_themes(self):
        ids = self.ids(palabras_clave=keyword_list('novela,thriller politico,corrupcion,familia'), titulo='X')
        self.assertIn('misterio-y-thriller', ids)
        self.assertIn('tema-poder-y-politica', ids)
        self.assertIn('tema-familia', ids)

    def test_gift_season_claims_do_not_create_seasonal_tags(self):
        self.assertNotIn('navidad', self.ids(palabras_clave=['libros para regalar en navidad'], titulo='Los escalones'))
        self.assertIn('navidad', self.ids(palabras_clave=[], titulo='Cuento de Navidad'))

    def test_plant_based_theme_needs_cooking_context(self):
        self.assertNotIn('tema-cocina-vegetal', self.ids(palabras_clave=['vegetal'], titulo='Poemas'))
        self.assertIn('tema-cocina-vegetal', self.ids(palabras_clave=['recetas', 'vegetal'], titulo='Verde'))

    def test_no_signal_means_no_extra_category_and_cap_applies(self):
        self.assertEqual(self.ids(palabras_clave=['otros'], titulo='Algo'), [])
        many = keyword_list('thriller,fantasia,romance,terror,aventura,humor,poesia,familia,amistad,venganza')
        self.assertLessEqual(len(extra_categories({'palabras_clave': many, 'titulo': ''})), 6)

    def test_keywords_about_other_books_do_not_classify(self):
        # Penguin promociona obras vecinas en las palabras clave: «virginia woolf una biografia» en La señora Dalloway
        # o el título truncado de otro tebeo en Ibáñez Mítico 2.
        dalloway = self.ids(titulo='La señora Dalloway', autores=['Virginia Woolf'],
                            palabras_clave=['virginia woolf una biografia', 'novela'])
        self.assertNotIn('biografias-y-memorias', dalloway)
        ibanez = self.ids(titulo='Ibáñez Mítico 2', autores=['Francisco Ibáñez'],
                          palabras_clave=['hachís... ¡qué malo para la salud!'])
        self.assertNotIn('nutricion-y-bienestar', ibanez)
        self.assertIn('biografias-y-memorias', self.ids(titulo='Virginia Woolf. Una biografía', autores=['Quentin Bell'],
                                                        palabras_clave=['virginia woolf una biografia', 'biografia']))

    def test_pvp_is_the_fixed_price_not_the_store_discount(self):
        self.assertEqual(_pvp_centimos({'price_without_reduction': '22.89976', 'has_discount': 'True', 'price_amount': '21.75'}), 2290)
        self.assertEqual(_pvp_centimos({'price_amount': '18.9', 'has_discount': 'False'}), 1890)
        self.assertIsNone(_pvp_centimos({'price_amount': 'abc'}))
        self.assertIsNone(_pvp_centimos({'price_amount': '0.5'}))


if __name__ == '__main__':
    unittest.main()
