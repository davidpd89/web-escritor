import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import catalogo_amazon as ca
import reading_taxonomy as taxonomy
from reading_intake_pipeline import classify
spec=importlib.util.spec_from_file_location('build',ROOT/'scripts/build-reading-catalogue.py')
build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)

class ClassificationTests(unittest.TestCase):
 def test_reference_node_is_not_an_essay(self):
  self.assertEqual(ca.SUBJECT_OF_NODE['enciclopedias y obras de consulta'],'Guías y referencia')
 def test_visual_reference_guide_is_repaired_without_an_isbn_exception(self):
  data={'categorias':[{'id':'ensayo','nombre':'Ensayo','tipo':'genero'}], 'libros':[{'id':'isbn-nuevo','titulo':'Mundos imaginarios. La guía visual definitiva','descripcion_breve':'La editorial la incluye en ensayo.'}], 'libro_categorias':[{'libro_id':'isbn-nuevo','categoria_id':'ensayo'}]}
  taxonomy.repair_classification(data)
  self.assertNotIn('ensayo',{r['categoria_id'] for r in data['libro_categorias']})
  self.assertIn('guias-y-referencia',{r['categoria_id'] for r in data['libro_categorias']})
  self.assertNotIn('ensayo',data['libros'][0]['descripcion_breve'])
  before=copy.deepcopy(data);taxonomy.repair_classification(data);self.assertEqual(data,before)
 def test_a_novel_with_dictionary_in_its_title_is_not_reclassified(self):
  data={'categorias':[],'libros':[{'id':'isbn-novela','titulo':'El diccionario de las palabras perdidas'}],'libro_categorias':[{'libro_id':'isbn-novela','categoria_id':'narrativa'}]}
  before=copy.deepcopy(data);taxonomy.repair_classification(data);self.assertEqual(data,before)
 def test_new_visual_guide_does_not_inherit_essay(self):
  record={'titulo':'Otro universo. Guía visual','materias':['Ensayo'],'palabras_clave':[]}
  result=classify(record,{'categorias':[]})
  self.assertIn('guias-y-referencia',result);self.assertNotIn('ensayo',result)
 def test_reference_guides_feed_nonfiction_text_generation(self):
  spec=importlib.util.spec_from_file_location('reference_texts',ROOT/'scripts/reading-texts.py')
  texts=importlib.util.module_from_spec(spec);spec.loader.exec_module(texts)
  self.assertEqual(texts.family({'guias-y-referencia'},'Una obra de consulta. '*20),'no_ficcion')
 def test_comic_is_visible_even_when_it_is_the_third_category(self):
  cats=[{'id':ident,'nombre':name,'tipo':'genero','activa':True,'orden':i} for i,(ident,name) in enumerate([('terror','Terror'),('aventuras','Aventuras'),('comic-y-novela-grafica','Cómic y novela gráfica')])]
  html=build.tags(cats,compact=True)
  self.assertIn('Cómic y novela gráfica',html)
  self.assertLess(html.index('Cómic'),html.index('Terror'))

if __name__=='__main__': unittest.main()
