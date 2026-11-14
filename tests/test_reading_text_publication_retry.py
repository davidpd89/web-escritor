import contextlib,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_reading_branch_retry import load
texts=load('texts_concurrent_publication','scripts/reading-texts.py')
publisher=load('publisher_concurrent_publication','scripts/publish-reading-refresh.py')
class Stale(RuntimeError):pass

class TextPublicationRetryTests(unittest.TestCase):
 def exercise(self,outcomes):
  with tempfile.TemporaryDirectory() as tmp,contextlib.ExitStack() as stack:
   root=Path(tmp);out=root/'saved';out.mkdir();(out/'book.json').write_text('{}')
   tree=root/'main';(tree/'data').mkdir(parents=True)
   pub=types.SimpleNamespace(publication=types.SimpleNamespace(gh=lambda *a:'[]',StaleMerge=Stale),
     clean_main_tree=Mock(return_value=tree),allowed_path=lambda p:True,run=Mock(side_effect=outcomes))
   book={'id':'book','estado':'publicado'}
   patches=[(texts,'load_module',lambda *a:pub),(texts,'ROOT',root),
    (texts,'read_json',lambda p,*a:{'id':'book','bloques':[{}]*10}),
    (texts,'published',lambda d:[book]),(texts,'payload',lambda *a:{}),
    (texts,'valid_blocks',lambda *a:[{}]*10),(texts,'write_json',lambda *a:None),
    (texts,'git',lambda *a,**k:' M data/reading-texts/book.json\n' if k.get('capture') else None),
    (texts,'git_add',lambda *a,**k:None),(texts.git_estado,'rutas',lambda *a,**k:['data/reading-texts/book.json']),(texts.catalogue,'index_categories',lambda *a:None),
    (texts.subprocess,'run',lambda *a,**k:None),(texts,'chat',lambda *a,**k:self.fail('Saved texts must not be regenerated'))]
   for owner,name,value in patches:stack.enter_context(patch.object(owner,name,value))
   try:return texts.publish(out),pub
   except Exception as exc:return exc,pub
 def test_main_advancing_rebuilds_saved_texts_and_then_publishes(self):
  result,pub=self.exercise([Stale('main advanced'),Stale('main advanced again'),None])
  self.assertIs(result,True)
  self.assertEqual(pub.run.call_count,3)
  self.assertEqual(pub.clean_main_tree.call_count,3)
 def test_concurrent_changes_stop_after_three_attempts(self):
  result,pub=self.exercise([Stale('1'),Stale('2'),Stale('3'),None])
  self.assertIsInstance(result,Stale)
  self.assertEqual(pub.run.call_count,3)
 def test_real_ci_failure_is_not_retried_as_a_stale_branch(self):
  result,pub=self.exercise([RuntimeError('genuine test failure'),None])
  self.assertIsInstance(result,RuntimeError)
  self.assertEqual(pub.run.call_count,1)

class PublisherPreflightTests(unittest.TestCase):
 def test_conflicted_generated_branch_does_not_start_obsolete_ci(self):
  state=json.dumps({'number':9,'headRefOid':'abc','mergeStateStatus':'DIRTY','mergeable':'CONFLICTING'})
  with patch.object(publisher.publication,'gh',return_value=state),patch.object(publisher.publication,'publish_generated') as launch:
   with self.assertRaises(publisher.publication.StaleMerge):publisher.run('automation/reading-catalogue-textos-test')
   launch.assert_not_called()

if __name__=='__main__':unittest.main()
