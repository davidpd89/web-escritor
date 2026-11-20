import contextlib,importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_reading_branch_retry import Repo,CATALOGUE,books,refresh as default_refresh
refresh=default_refresh
if os.environ.get('READING_REFRESH_TEST_MODULE'):
 spec=importlib.util.spec_from_file_location('before_refresh',os.environ['READING_REFRESH_TEST_MODULE'])
 refresh=importlib.util.module_from_spec(spec);spec.loader.exec_module(refresh)

class RecoveryTests(unittest.TestCase):
 def test_concurrent_book_additions_keep_main_and_pending_source_data(self):
  with tempfile.TemporaryDirectory() as tmp:
   repo=Repo(tmp);branch='automation/reading-catalogue-2026-11-12-test'
   repo.bot_batch(branch)
   repo.main_moves({CATALOGUE:books('a','b','c','d','e','f','main-book')})
   self.assertEqual(refresh.carry(branch,root=repo.work),['nuevo1','nuevo2'])
   result=json.loads((repo.work/CATALOGUE).read_text(encoding='utf-8'))
   self.assertEqual({b['id'] for b in result['libros']},set('abcdef')|{'main-book','nuevo1','nuevo2'})
   self.assertEqual((repo.work/'assets/reading-covers/nuevo1.webp').read_bytes(),bytes(range(256))*4)
   self.assertIn('9788400000000',(repo.work/'data/reading-intake-state.json').read_text())
   self.assertEqual((repo.work/'pagefind/index.txt').read_text(),'v1\n')
 def test_squashed_published_checkpoint_has_no_new_source_changes(self):
  with tempfile.TemporaryDirectory() as tmp:
   repo=Repo(tmp);branch='automation/reading-catalogue-2026-11-12-squashed'
   repo.bot_batch(branch)
   # main contains the same published data through a different commit.
   commit=repo.git('commit-tree',branch+'^{tree}','-p','origin/main','-m','squashed publication')
   repo.git('push','-q','origin',commit+':refs/heads/main')
   self.assertIsNone(refresh.carry(branch,root=repo.work))
   self.assertEqual(repo.git('status','--porcelain'),'')
 def test_new_pending_candidates_survive_even_if_all_books_are_already_published(self):
  with tempfile.TemporaryDirectory() as tmp:
   repo=Repo(tmp);branch='automation/reading-catalogue-2026-11-12-pending-only'
   repo.bot_batch(branch)
   repo.main_moves({CATALOGUE:books('a','b','c','d','e','f','nuevo1','nuevo2','main-book')})
   self.assertEqual(refresh.carry(branch,root=repo.work),[])
   state=json.loads((repo.work/'data/reading-intake-state.json').read_text())
   self.assertEqual(state['pending'],['9788400000000'])
   self.assertEqual(repo.git('diff','--name-only','HEAD'),'data/reading-intake-state.json')
 def test_published_state_does_not_reactivate_a_book_main_quarantined(self):
  with tempfile.TemporaryDirectory() as tmp:
   repo=Repo(tmp);branch='automation/reading-catalogue-2026-11-12-held'
   repo.git('switch','-q','-c',branch,'origin/main')
   data=json.loads(books('a','b','c','d','e','f'))
   book={'id':'isbn-9780241838044','isbn13':'9780241838044','titulo':'Visual'};data['libros'].append(book)
   repo.write({CATALOGUE:json.dumps(data),'data/reading-intake-state.json':json.dumps({'items':{'isbn13:9780241838044':{'estado_ingesta':'publicado','libro_id':book['id']}}})})
   repo.commit('source');repo.git('push','-q','origin',branch);repo.git('switch','-q','--detach','origin/main')
   repo.main_moves({CATALOGUE:books('a','b','c','d','e','f','main-book'),'data/reading-quarantine.json':json.dumps({'libros':[{'libro':book}]})})
   self.assertIsNone(refresh.carry(branch,root=repo.work))
   self.assertEqual(repo.git('status','--porcelain'),'')
 def test_original_provenance_is_carried_and_other_records_are_not_replaced(self):
  with tempfile.TemporaryDirectory() as tmp:
   repo=Repo(tmp);branch='automation/reading-catalogue-2026-11-12-evidence'
   repo.git('switch','-q','-c',branch,'origin/main')
   data=json.loads(books('a','b','c','d','e','f'));data['libros'].append({'id':'isbn-9780241838044','isbn13':'9780241838044','titulo':'Visual'})
   item={'estado_ingesta':'publicado','libro_id':'isbn-9780241838044','fuente':'original'}
   repo.write({CATALOGUE:json.dumps(data),'data/reading-intake-state.json':json.dumps({'schema_version':1,'items':{'isbn13:9780241838044':item}})})
   repo.commit('source');repo.git('push','-q','origin',branch);repo.git('switch','-q','--detach','origin/main')
   repo.main_moves({CATALOGUE:books('a','b','c','d','e','f','main-book'),'data/reading-intake-state.json':json.dumps({'schema_version':1,'items':{'keep':{'estado_ingesta':'pendiente','fuente':'main'}}})})
   self.assertEqual(refresh.carry(branch,root=repo.work),['isbn-9780241838044'])
   state=json.loads((repo.work/'data/reading-intake-state.json').read_text())
   self.assertEqual(state['items']['isbn13:9780241838044'],item)
   self.assertEqual(state['items']['keep']['fuente'],'main')
 def test_store_manifest_registrations_travel_with_recovered_books(self):
  # CodeRabbit #1495: una alta cuya portada vive en el almacén externo conserva su registro; main gana en los suyos.
  with tempfile.TemporaryDirectory() as tmp:
   repo=Repo(tmp);branch='automation/reading-catalogue-2026-11-12-store'
   store='data/reading-covers-store.json';base='https://example.github.io/portadas'
   repo.git('switch','-q','-c',branch,'origin/main')
   data=json.loads(books('a','b','c','d','e','f'));data['libros'].append({'id':'isbn-9780241838044','isbn13':'9780241838044','portada_local':'/assets/reading-covers/isbn-9780241838044.webp'})
   item={'estado_ingesta':'publicado','libro_id':'isbn-9780241838044'}
   repo.write({CATALOGUE:json.dumps(data),'data/reading-intake-state.json':json.dumps({'schema_version':1,'items':{'isbn13:9780241838044':item}}),
               store:json.dumps({'base_url':base,'archivos':['isbn-9780241838044.webp','compartida.webp'],'sha256':{'isbn-9780241838044.webp':'1'*64,'compartida.webp':'2'*64}})})
   repo.commit('source');repo.git('push','-q','origin',branch);repo.git('switch','-q','--detach','origin/main')
   repo.main_moves({CATALOGUE:books('a','b','c','d','e','f','main-book'),store:json.dumps({'base_url':base,'archivos':['compartida.webp','main.webp'],'sha256':{'compartida.webp':'3'*64,'main.webp':'4'*64}})})
   self.assertEqual(refresh.carry(branch,root=repo.work),['isbn-9780241838044'])
   manifest=json.loads((repo.work/store).read_text(encoding='utf-8'))
   self.assertEqual(manifest['archivos'],['compartida.webp','isbn-9780241838044.webp','main.webp'])
   self.assertEqual(manifest['sha256'],{'compartida.webp':'3'*64,'isbn-9780241838044.webp':'1'*64,'main.webp':'4'*64})
 def test_a_legacy_manifest_without_digests_sets_its_books_aside_instead_of_failing(self):
  # #1500: el punto de guardado de una carga cuyo runner murió registró nombres sin huella y sin bytes subidos.
  with tempfile.TemporaryDirectory() as tmp:
   repo=Repo(tmp);branch='automation/reading-atascado-2026-11-20-legacy'
   store='data/reading-covers-store.json';base='https://example.github.io/portadas'
   repo.git('switch','-q','-c',branch,'origin/main')
   data=json.loads(books('a','b','c','d','e','f'))
   data['libros']+=[{'id':'isbn-9780241838044','isbn13':'9780241838044','portada_local':'/assets/reading-covers/isbn-9780241838044.webp'},
                    {'id':'isbn-9780241838051','isbn13':'9780241838051'}]
   items={'isbn13:'+i[5:]:{'estado_ingesta':'publicado','libro_id':i} for i in ('isbn-9780241838044','isbn-9780241838051')}
   repo.write({CATALOGUE:json.dumps(data),'data/reading-intake-state.json':json.dumps({'schema_version':1,'items':items}),
               store:json.dumps({'base_url':base,'archivos':['isbn-9780241838044.webp','isbn-9780241838044-320.webp']})})
   repo.commit('source');repo.git('push','-q','origin',branch);repo.git('switch','-q','--detach','origin/main')
   repo.main_moves({CATALOGUE:books('a','b','c','d','e','f','main-book')})
   skipped=[]
   self.assertEqual(refresh.carry(branch,root=repo.work,skipped=skipped),['isbn-9780241838051'])
   self.assertEqual(skipped,['isbn-9780241838044'])
   ids={b['id'] for b in json.loads((repo.work/CATALOGUE).read_text())['libros']}
   self.assertIn('isbn-9780241838051',ids);self.assertNotIn('isbn-9780241838044',ids)
   manifest=repo.work/store
   self.assertTrue(not manifest.exists() or 'isbn-9780241838044.webp' not in json.loads(manifest.read_text(encoding='utf-8'))['archivos'])
 def test_missing_provenance_fails_before_writing_a_conflicting_recovery(self):
  with tempfile.TemporaryDirectory() as tmp:
   repo=Repo(tmp);branch='automation/reading-catalogue-2026-11-12-invalid'
   repo.git('switch','-q','-c',branch,'origin/main')
   data=json.loads(books('a','b','c','d','e','f'));data['libros'].append({'id':'isbn-9780241838044','isbn13':'9780241838044'})
   repo.write({CATALOGUE:json.dumps(data)});repo.commit('source');repo.git('push','-q','origin',branch);repo.git('switch','-q','--detach','origin/main')
   repo.main_moves({CATALOGUE:books('a','b','c','d','e','f','main-book')})
   with self.assertRaisesRegex(ValueError,'procedencia'):
    refresh.carry(branch,root=repo.work)
   self.assertEqual(repo.git('status','--porcelain'),'')

 def test_a_book_without_provenance_is_set_aside_and_the_rest_is_recovered(self):
  # CodeRabbit #1397: una sola alta sin procedencia no retira todo el punto de guardado.
  with tempfile.TemporaryDirectory() as tmp:
   repo=Repo(tmp);branch='automation/reading-catalogue-2026-11-12-mixed'
   repo.git('switch','-q','-c',branch,'origin/main')
   data=json.loads(books('a','b','c','d','e','f'))
   data['libros']+= [{'id':'isbn-9780241838044','isbn13':'9780241838044'},{'id':'isbn-9780241838051','isbn13':'9780241838051'}]
   item={'estado_ingesta':'publicado','libro_id':'isbn-9780241838051'}
   repo.write({CATALOGUE:json.dumps(data),'data/reading-intake-state.json':json.dumps({'schema_version':1,'items':{'isbn13:9780241838051':item}})})
   repo.commit('source');repo.git('push','-q','origin',branch);repo.git('switch','-q','--detach','origin/main')
   repo.main_moves({CATALOGUE:books('a','b','c','d','e','f','main-book')})
   skipped=[]
   self.assertEqual(refresh.carry(branch,root=repo.work,skipped=skipped),['isbn-9780241838051'])
   self.assertEqual(skipped,['isbn-9780241838044'])
   ids={b['id'] for b in json.loads((repo.work/CATALOGUE).read_text())['libros']}
   self.assertIn('isbn-9780241838051',ids);self.assertNotIn('isbn-9780241838044',ids)
   self.assertIn('main-book',ids)

 def test_existing_book_updates_survive_a_conflicting_main(self):
  """#1312 (CodeRabbit): con choque, solo se trasladaban altas y los cambios de libros existentes se perdían."""
  with tempfile.TemporaryDirectory() as tmp:
   repo=Repo(tmp);branch='automation/reading-catalogue-2026-11-14-updates'
   repo.git('switch','-q','-c',branch,'origin/main')
   data=json.loads(books('a','b','c','d','e','f'))
   data['libros'][0]['titulo']='A corregido';data['libros'][1]['titulo']='B de la carga'
   repo.write({CATALOGUE:json.dumps(data),'assets/reading-covers/a.webp':b'portada nueva'})
   repo.commit('source');repo.git('push','-q','origin',branch);repo.git('switch','-q','--detach','origin/main')
   moved=json.loads(books('a','b','c','d','e','f','main-book'));moved['libros'][1]['titulo']='B de main'
   repo.main_moves({CATALOGUE:json.dumps(moved)})
   self.assertEqual(refresh.carry(branch,root=repo.work),[])
   result={b['id']:b['titulo'] for b in json.loads((repo.work/CATALOGUE).read_text(encoding='utf-8'))['libros']}
   self.assertEqual(result['a'],'A corregido')
   self.assertEqual(result['b'],'B de main')
   self.assertIn('main-book',result)
   self.assertEqual((repo.work/'assets/reading-covers/a.webp').read_bytes(),b'portada nueva')
 def test_existing_book_dependencies_and_asset_only_changes_survive(self):
  """CodeRabbit #1320: editorial y categoría nuevas de un libro actualizado, y la portada nueva de un libro cuya
  ficha no cambió, se perdían al recuperar con choque."""
  with tempfile.TemporaryDirectory() as tmp:
   repo=Repo(tmp);branch='automation/reading-catalogue-2026-11-14-deps'
   repo.git('switch','-q','-c',branch,'origin/main')
   data=json.loads(books('a','b','c','d','e','f'))
   data['libros'][0]['editorial_catalogo_slug']='nueva';data['libros'][1]['titulo']='B de la carga'
   data['categorias']=[{'id':'cat-x'}];data['libro_categorias']=[{'libro_id':'a','categoria_id':'cat-x'}]
   repo.write({CATALOGUE:json.dumps(data),'assets/reading-covers/c.webp':b'portada de c',
               'assets/reading-covers/b.webp':b'portada de b','data/reading-publishers.json':json.dumps({'editoriales':[{'slug':'nueva','nombre':'Nueva'}]})})
   repo.commit('source');repo.git('push','-q','origin',branch);repo.git('switch','-q','--detach','origin/main')
   moved=json.loads(books('a','b','c','d','e','f','main-book'));moved['libros'][1]['titulo']='B de main'
   repo.main_moves({CATALOGUE:json.dumps(moved)})
   self.assertEqual(refresh.carry(branch,root=repo.work),[])
   result=json.loads((repo.work/CATALOGUE).read_text(encoding='utf-8'))
   self.assertEqual({b['id']:b.get('editorial_catalogo_slug') for b in result['libros']}['a'],'nueva')
   self.assertIn({'libro_id':'a','categoria_id':'cat-x'},result['libro_categorias'])
   publishers=json.loads((repo.work/'data/reading-publishers.json').read_text(encoding='utf-8'))
   self.assertEqual([p['slug'] for p in publishers['editoriales']],['nueva'])
   self.assertEqual((repo.work/'assets/reading-covers/c.webp').read_bytes(),b'portada de c')
   # b lo cambió main: su portada del origen no se trae.
   self.assertFalse((repo.work/'assets/reading-covers/b.webp').exists())

class CheckpointLifetimeTests(unittest.TestCase):
 def check(self,fail):
  with tempfile.TemporaryDirectory() as tmp,contextlib.ExitStack() as stack:
   order=[];root=Path(tmp)
   def run(branch):
    order.append('publish')
    if fail: raise RuntimeError('CI failed')
   patches=[(refresh,'ROOT',root),(refresh,'command',lambda *a:None),(refresh,'bot_identity',lambda:None),
    (refresh,'read_json',lambda p:{'rss_enabled':False}),(refresh,'quarantine_summary',lambda *a:''),
    (refresh,'data_contract_failures',lambda:[]),(refresh.reading_quarantine,'apply',lambda *a:[]),
    (refresh.materializar,'construir',lambda *a,**k:None),(refresh.materializar,'comprobar',lambda *a,**k:None),
    (refresh.subprocess,'check_output',lambda *a,**k:' M data/reading-catalogue.json\n'),
    (refresh.git_estado,'rutas',lambda *a,**k:['data/reading-catalogue.json']),
    (refresh.git_estado,'preparar',lambda *a,**k:None),
    (refresh.publisher,'allowed_path',lambda p:True),(refresh.publisher,'run',run),
    (refresh.publisher.publication,'fresh_branch',lambda *a,**k:'automation/reading-catalogue-test'),
    (refresh.publisher.publication,'gh',lambda *a:None),(refresh,'drop_checkpoint',lambda b:order.append('drop'))]
   for owner,name,value in patches:stack.enter_context(patch.object(owner,name,value))
   if fail:
    with self.assertRaisesRegex(RuntimeError,'CI failed'):
     refresh.assemble({'new_books':['new'],'updated_books':[],'stats':{}},changed=True,checkpoint='saved')
    self.assertEqual(order,['publish'])
   else:
    refresh.assemble({'new_books':['new'],'updated_books':[],'stats':{}},changed=True,checkpoint='saved')
    self.assertEqual(order,['publish','drop'])
 def test_failed_publication_keeps_the_durable_checkpoint(self):self.check(True)
 def test_checkpoint_is_removed_only_after_verified_publication(self):self.check(False)

class QuarantineRoundsTests(unittest.TestCase):
 """Sin tope de rondas: se aparta mientras cada ronda nombre libros nuevos; repetir los mismos para la carga."""
 def run_rounds(self,rounds,apply=lambda *a,**k:[]):
  with tempfile.TemporaryDirectory() as tmp,contextlib.ExitStack() as stack:
   published=[];pending=list(rounds)
   def failures():return [{'test':'contrato','libros':pending.pop(0)}] if pending else []
   patches=[(refresh,'ROOT',Path(tmp)),(refresh,'command',lambda *a:None),(refresh,'bot_identity',lambda:None),
    (refresh,'read_json',lambda p:{'rss_enabled':False}),(refresh,'quarantine_summary',lambda *a:''),
    (refresh,'data_contract_failures',failures),(refresh,'drop_orphan_pages',lambda q:None),
    (refresh.reading_quarantine,'flagged_books',lambda f,c:{b:'motivo' for b in f[0]['libros']}),
    (refresh.reading_quarantine,'apply',apply),
    (refresh.materializar,'construir',lambda *a,**k:None),(refresh.materializar,'comprobar',lambda *a,**k:None),
    (refresh.subprocess,'check_output',lambda *a,**k:' M data/reading-catalogue.json\n'),
    (refresh.git_estado,'rutas',lambda *a,**k:['data/reading-catalogue.json']),
    (refresh.git_estado,'preparar',lambda *a,**k:None),
    (refresh.publisher,'allowed_path',lambda p:True),(refresh.publisher,'run',lambda b:published.append(b)),
    (refresh.publisher.publication,'fresh_branch',lambda *a,**k:'automation/reading-catalogue-test'),
    (refresh.publisher.publication,'gh',lambda *a:None),(refresh,'drop_checkpoint',lambda b:None)]
   for owner,name,value in patches:stack.enter_context(patch.object(owner,name,value))
   refresh.assemble({'new_books':['new'],'updated_books':[],'stats':{}},changed=True,checkpoint='saved')
   return published
 def test_more_than_three_rounds_with_new_books_still_publish(self):
  self.assertEqual(len(self.run_rounds([['a'],['b'],['c'],['d'],['e']])),1)
 def test_a_round_naming_the_same_books_stops_the_load(self):
  with self.assertRaisesRegex(RuntimeError,'no se resuelven apartando libros'):
   self.run_rounds([['a'],['a']])
 def test_a_repeated_book_the_quarantine_can_still_act_on_keeps_the_load_going(self):
  # 16/11: isbn-9791388205675 se repitió en la segunda ronda porque la primera solo pudo revertirlo (un dato
  # ajeno al contrato había cambiado); la segunda ronda ya lo encuentra idéntico a su versión publicada y
  # isolate() lo retira. Repetir el mismo libro no es «regla rota» mientras la cuarentena siga moviendo algo.
  calls=[]
  def apply(*a,**k):
   calls.append(None)
   # La 1ª llamada es la cuarentena inicial (antes del bucle) y la 2ª es la 1ª ronda: ninguna aparta nada
   # todavía. La 3ª es la ronda que repite «a» y por fin lo retira.
   return [] if len(calls)<3 else [{'libro':{'id':'a'},'motivo':'un solo módulo'}]
  self.assertEqual(len(self.run_rounds([['a'],['a']],apply=apply)),1)
  self.assertEqual(len(calls),3)
 def test_unrelated_quarantine_activity_does_not_mask_a_repeated_book_stuck(self):
  # La cuarentena puede seguir moviendo libros de noches anteriores (`held`) sin relación con el que se repite
  # aquí; que `apply` no devuelva una lista vacía no basta para creer que el repetido avanza.
  with self.assertRaisesRegex(RuntimeError,'no se resuelven apartando libros'):
   self.run_rounds([['a'],['a']],apply=lambda *a,**k:[{'libro':{'id':'otro-libro-en-cuarentena'},'motivo':'x'}])

if __name__=='__main__':unittest.main()
