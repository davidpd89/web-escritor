"""No-token metadata enrichment with public identity and taxonomy contracts."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_editorial_sources import editorial_excerpt, publisher_author_bio, SourceError
from reading_intake_pipeline import classify, enrich_author_bios, update_authors, builder, author_identity_conflicts
from reading_intake_publishers import relevant_publisher


class EnrichmentTests(unittest.TestCase):
    def test_excerpt_is_bounded_and_prefers_subject_over_advertising(self):
        source = '<p>EL GRAN ÉXITO INTERNACIONAL QUE TODO EL MUNDO ESTABA ESPERANDO DESDE HACE AÑOS.</p><p>Una viajera encuentra una carta perdida y sigue sus pistas hasta una ciudad abandonada, donde conoce la historia de una familia separada por la guerra y decide buscar a sus descendientes.</p>'
        excerpt = editorial_excerpt(source)
        self.assertTrue(excerpt.startswith('Una viajera'))
        self.assertLessEqual(len(excerpt.split()), 24)
        self.assertNotIn('<', excerpt)
        self.assertTrue(excerpt.endswith('…'))

    def test_missing_synopsis_never_fabricates_plot(self):
        self.assertEqual(editorial_excerpt('<p>Comprar ahora</p>'), '')

    def test_author_requires_matching_public_identity(self):
        url = 'https://www.penguinlibros.com/es/12-autora-tecnica'
        source = '<link rel="canonical" href="'+url+'"><meta property="og:title" content="Autora Técnica | Penguin Libros"><meta name="description" content="Autora Técnica nació en una ciudad y escribe novelas sobre familias viajeras que exploran mundos nuevos y comparten sus experiencias con los demás habitantes.">'
        bio = publisher_author_bio(source, url, 'Autora Técnica')
        self.assertLessEqual(len(bio.split()), 24)
        with self.assertRaises(SourceError):
            publisher_author_bio(source, url, 'Otra persona')

    def test_all_subjects_can_enter_without_age_only_fallback(self):
        for subject in ['Nutrición, belleza y fitness', 'Poesía', 'Cómic', 'Divulgación científica', 'Historia', 'Cocina']:
            data = {'categorias': []}
            ids = classify({'materias': [subject], 'edad_recomendada': 'Adultos'}, data)
            thematic = [c for c in data['categorias'] if c['tipo'] in {'genero', 'tematica'}]
            self.assertTrue(thematic, subject)
            self.assertIn(thematic[0]['id'], ids)
        with self.assertRaises(SourceError):
            classify({'materias': [''], 'edad_recomendada': 'Adultos'}, {'categorias': []})

    def test_publisher_selection_does_not_restrict_genres(self):
        for genre in ['Cocina', 'Poesía', 'Ciencia', 'Infantil', 'Fantasía']:
            self.assertTrue(relevant_publisher({'slug':'editorial', 'name':'Editorial',
                'publish':True, 'publisher_type':'tradicional', 'genres':[genre]}))

    def test_long_subjects_do_not_collide_after_truncation(self):
        data={'categorias':[]}
        prefix='Una materia editorial muy extensa con muchos términos repetidos para identificar contenidos '
        a=classify({'materias':[prefix+'primero']},data)
        b=classify({'materias':[prefix+'segundo']},data)
        self.assertNotEqual(a,b)

    def test_homonymous_author_profiles_require_review(self):
        state={'items':{'known':{'estado_ingesta':'publicado','datos':{'fuentes_autores':{
            'Juan Sánchez':'https://www.penguinlibros.com/es/12-juan-sanchez'}}}}}
        record={'fuentes_autores':{'Juan Sánchez':'https://www.penguinlibros.com/es/99-juan-sanchez'}}
        self.assertEqual(author_identity_conflicts(record,state),['Juan Sánchez'])
        record['fuentes_autores']['Juan Sánchez']='https://www.penguinlibros.com/es/12-juan-sanchez'
        self.assertEqual(author_identity_conflicts(record,state),[])

    def test_author_bio_uses_profile_not_pending_book_fallback(self):
        profile = 'https://www.penguinlibros.com/es/12-autora-tecnica'
        author = {'nombre':'Autora Técnica', 'slug':'autora-tecnica', 'tipo':'bibliografico'}
        state = {'items': {'published':{'datos':{'fuentes_autores':{'Autora Técnica':profile}}},
                           'pending':{'datos':{'fuentes_autores':{'Autora Técnica':'https://www.penguinlibros.com/es/libros/1-libro-9780140328721'}}}}}
        class HTTP:
            requests=0
            budget=10
            def get(self, url, **kwargs):
                self.url = url
                return ('<meta property="og:title" content="Autora Técnica"><meta name="description" content="Autora Técnica escribe relatos desde hace muchos años y ha publicado obras acerca de viajes y aventuras en distintas ciudades del mundo.">').encode()
        http=HTTP()
        payload={'autores':[author]}
        self.assertEqual(enrich_author_bios(payload,state,http,'2026-10-21'),1)
        self.assertEqual(http.url,profile)
        self.assertEqual(enrich_author_bios(payload,state,http,'2026-10-22'),0)

    def test_manual_biographies_are_pinned(self):
        original=json.loads((ROOT/'data/reading-authors.json').read_text(encoding='utf-8'))['autores'][0]
        self.assertNotEqual(original.get('tipo'), 'bibliografico')
        authors={'autores':[copy.deepcopy(original)]}
        books=json.loads((ROOT/'data/reading-catalogue.json').read_text(encoding='utf-8'))
        update_authors(authors,books,books['libros'],'2026-10-22')
        self.assertEqual(authors['autores'][0],original)

    def test_public_reviews_are_escaped_and_private_fields_rejected(self):
        review={'review_id':'r1','libro_id':'book','isbn13':'9780140328721',
                'nombre_publico':'Alias público','puntuacion':5,'titulo_resena':'<script>no</script>',
                'texto_resena':'Texto de prueba <img src=x onerror=alert(1)>','fecha_envio':'2026-10-21'}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'data').mkdir()
            path=root/'data/reading-reviews-approved.json'
            path.write_text(json.dumps({'schema_version':1,'reviews':[review]}),encoding='utf-8')
            rows=builder.approved_reviews_for({'id':'book','isbn13':'9780140328721'},root)
            html=builder.render_approved_reviews(rows)
            self.assertNotIn('<script>',html)
            self.assertIn('&lt;script&gt;',html)
            self.assertNotIn('<img src=x',html)
            review['nota_interna']='Privada'
            path.write_text(json.dumps({'schema_version':1,'reviews':[review]}),encoding='utf-8')
            with self.assertRaises(builder.ValidationError):
                builder.approved_reviews_for({'id':'book','isbn13':'9780140328721'},root)


if __name__ == '__main__':
    unittest.main()
