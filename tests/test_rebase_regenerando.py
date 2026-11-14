import importlib.util
import unittest
import subprocess
import tempfile
from unittest.mock import patch
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    'rebase_regenerando', Path(__file__).resolve().parents[1] / 'scripts' / 'rebase-regenerando.py')
rr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rr)


class ClasificarTest(unittest.TestCase):
    def test_nuevo_no_generado_no_se_versiona(self):
        cambios, sueltos = rr.clasificar([
            (' M', 'recomendaciones/index.html'),
            (' M', 'data/reading-books.json'),
            ('??', 'pagefind/fragment/nuevo.pf_fragment'),
            ('??', 'reports/performance-budget.json'),
        ])
        self.assertEqual(cambios, ['recomendaciones/index.html', 'data/reading-books.json',
                                   'pagefind/fragment/nuevo.pf_fragment'])
        self.assertEqual(sueltos, ['reports/performance-budget.json'])

    def test_generado(self):
        self.assertTrue(rr.generado('sitemap-libros.xml'))
        self.assertTrue(rr.generado('assets/page-order.generated.js'))
        self.assertFalse(rr.generado('data/reading-books.json'))
        self.assertFalse(rr.generado('scripts/build-sitemap.py'))


class RealGitConflictsTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        root_patch=patch.object(rr,'ROOT',self.root);root_patch.start();self.addCleanup(root_patch.stop)
        self.git('init','-q','-b','main')
        self.git('config','user.name','test');self.git('config','user.email','test@example.test')
        self.git('config','core.autocrlf','false')
        self.write('pagefind/fragment/old.pf_fragment','base')
        self.write('scripts/source.py','base')
        self.commit('base')
    def git(self,*args):
        return subprocess.run(['git',*args],cwd=self.root,check=True,capture_output=True,text=True).stdout.strip()
    def write(self,name,value):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value)
    def commit(self,label):
        self.git('add','-A');self.git('commit','-qm',label)
    def test_main_deleted_an_old_generated_hash_changed_by_the_branch(self):
        self.git('switch','-qc','feature')
        self.write('pagefind/fragment/old.pf_fragment','feature')
        self.write('data/new.json','{}');self.commit('source addition')
        self.git('switch','-q','main');self.git('rm','-q','pagefind/fragment/old.pf_fragment')
        self.write('pagefind/fragment/new.pf_fragment','main');self.commit('new generated hash')
        self.git('switch','-q','feature');rr.rebasar('main')
        self.assertFalse((self.root/'pagefind/fragment/old.pf_fragment').exists())
        self.assertEqual((self.root/'pagefind/fragment/new.pf_fragment').read_text(),'main')
        self.assertTrue((self.root/'data/new.json').exists())
        self.assertEqual(self.git('status','--porcelain'),'')
    def test_real_source_conflict_aborts_without_overwriting_the_branch(self):
        self.git('switch','-qc','feature');self.write('scripts/source.py','feature');self.commit('source feature')
        original=self.git('rev-parse','HEAD')
        self.git('switch','-q','main');self.write('scripts/source.py','main');self.commit('source main')
        self.git('switch','-q','feature')
        with self.assertRaisesRegex(SystemExit,'no son generados'):rr.rebasar('main')
        self.assertEqual(self.git('rev-parse','HEAD'),original)
        self.assertEqual((self.root/'scripts/source.py').read_text(),'feature')
        self.assertEqual(self.git('status','--porcelain'),'')
    def test_many_generated_paths_are_staged_without_windows_argv_limit(self):
        def generated():
            for i in range(400):self.write('pagefind/fragment/'+str(i)+'-'+'x'*75+'.pf_fragment','generated')
        with patch.object(rr,'rebasar'),patch.object(rr,'regenerar',side_effect=generated),patch.object(rr.sys,'argv',['rebase-regenerando','--sin-fetch','--onto','main']):
            self.assertEqual(rr.main(),0)
        self.assertEqual(len(self.git('ls-tree','-r','--name-only','HEAD','--','pagefind/fragment').splitlines()),401)


if __name__ == '__main__':
    unittest.main()
