"""Changed-page checks must include all changes and keep full audit fallbacks."""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('link_input_selection',ROOT/'scripts/select-link-check-inputs.py')
selector=importlib.util.module_from_spec(spec);spec.loader.exec_module(selector)


class LinkInputSelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='link-selection-')
        self.root=Path(self.tmp.name)
        self.git('init','-q');self.git('config','user.name','QA');self.git('config','user.email','qa@example.invalid')
        for name in ['index.html','books/index.html','tests/fixture.html']:
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('<p>original</p>',encoding='utf-8')
        self.commit();self.base=self.git('rev-parse','HEAD').strip()
        self.git('update-ref','refs/remotes/origin/main',self.base)

    def tearDown(self):
        self.tmp.cleanup()

    def git(self,*args):
        return subprocess.check_output(['git',*args],cwd=self.root,stderr=subprocess.PIPE).decode('utf-8')

    def commit(self):
        self.git('add','.');self.git('commit','-qm','fixture')

    def changed(self):
        (self.root/'books/index.html').write_text('<p>modified</p>',encoding='utf-8')
        (self.root/'new.html').write_text('<p>new</p>',encoding='utf-8');self.commit()

    def test_pr_and_push_check_every_added_or_modified_page(self):
        self.changed()
        for name,event in [('pull_request',{'pull_request':{'base':{'sha':self.base}}}),('push',{'before':self.base})]:
            with self.subTest(name=name):
                result=selector.select(self.root,name,event,'refs/heads/main')
                self.assertEqual(result['scope'],'changed-html')
                self.assertEqual(result['files'],['books/index.html','new.html'])

    def test_branch_dispatch_compares_with_main_but_manual_main_checks_all(self):
        self.changed()
        self.assertEqual(selector.select(self.root,'workflow_dispatch',{},'refs/heads/automation/books')['files'],['books/index.html','new.html'])
        self.assertEqual(selector.select(self.root,'workflow_dispatch',{},'refs/heads/main')['scope'],'full-site')

    def test_schedule_override_missing_comparison_and_empty_diff_check_all(self):
        for name,event,full in [('schedule',{},False),('push',{'before':'invalid'},False),
                                ('push',{'before':'0'*40},False),('push',{'before':self.base},True)]:
            with self.subTest(name=name,event=event,full=full):
                result=selector.select(self.root,name,event,'refs/heads/main',full)
                self.assertEqual(result['scope'],'full-site')
                self.assertEqual(result['files'],['books/index.html','index.html'])

    def test_nothing_public_changed_checks_nothing(self):
        """26/11 (carga 45868423421): la PR de datos #1601 solo reindexaba pagefind y se revisaron las 9.482 páginas;
        el job agotó sus 40 min y la carga salió roja."""
        self.assertEqual(selector.select(self.root,'push',{'before':self.base},'refs/heads/main')['scope'],'none')
        (self.root/'pagefind').mkdir();(self.root/'pagefind/index.pf').write_text('x',encoding='utf-8')
        (self.root/'data').mkdir();(self.root/'data/x.json').write_text('{}',encoding='utf-8');self.commit()
        result=selector.select(self.root,'pull_request',{'pull_request':{'base':{'sha':self.base}}},'refs/heads/main')
        self.assertEqual((result['scope'],result['files']),('none',[]))

    def test_deletion_or_rename_checks_only_pages_naming_it(self):
        """Antes, cualquier borrado o renombrado mandaba a revisar la web entera."""
        (self.root/'index.html').write_text('<a href="books/">libros</a><img src="assets/c/x.webp">',encoding='utf-8')
        (self.root/'other.html').write_text('<p>nada</p>',encoding='utf-8')
        (self.root/'assets/c').mkdir(parents=True);(self.root/'assets/c/x.webp').write_bytes(b'img')
        self.commit();base=self.git('rev-parse','HEAD').strip()
        self.git('mv','books/index.html','renamed.html');self.commit()
        result=selector.select(self.root,'push',{'before':base},'refs/heads/main')
        self.assertEqual((result['scope'],result['files']),('changed-html',['index.html','renamed.html']))
        self.git('rm','-q','renamed.html');self.commit()
        result=selector.select(self.root,'push',{'before':base},'refs/heads/main')
        self.assertEqual((result['scope'],result['files']),('changed-html',['index.html']))
        self.git('rm','-q','assets/c/x.webp');self.commit()
        result=selector.select(self.root,'push',{'before':self.git('rev-parse','HEAD~1').strip()},'refs/heads/main')
        self.assertEqual((result['scope'],result['files']),('changed-html',['index.html']))

    def test_deleted_index_and_encoded_links_are_found(self):
        """Revisión de #1602 (Codex/CodeRabbit): ./, ../, index.html y %C3%B1 no nombran el tramo literal."""
        (self.root/'books/sub').mkdir()
        (self.root/'books/review.html').write_text('<a href="index.html">x</a>',encoding='utf-8')
        (self.root/'books/sub/deep.html').write_text('<a href="../">x</a>',encoding='utf-8')
        (self.root/'other.html').write_text('<a href="books/ni%C3%B1o.html">x</a>',encoding='utf-8')
        (self.root/'books/niño.html').write_text('<p>n</p>',encoding='utf-8')
        self.commit();base=self.git('rev-parse','HEAD').strip()
        self.git('rm','-q','books/index.html','books/niño.html');self.commit()
        result=selector.select(self.root,'push',{'before':base},'refs/heads/main')
        self.assertEqual(result['files'],['books/review.html','books/sub/deep.html','other.html'])

    def test_cover_store_change_checks_pages_with_moved_covers(self):
        """Revisión de #1602: el despliegue reescribe las portadas con el manifiesto; cambiarlo sin HTML no es «nada»."""
        manifest=self.root/'data/reading-covers-store.json';manifest.parent.mkdir()
        def store(base,names):
            manifest.write_text(json.dumps({'base_url':base,'archivos':names,'sha256':{},'almacenes':[],'almacen':{}}),encoding='utf-8')
        (self.root/'index.html').write_text('<img src="/assets/reading-covers/a.webp">',encoding='utf-8')
        (self.root/'other.html').write_text('<img src="/assets/reading-covers/b.webp">',encoding='utf-8')
        store('https://x.github.io/p',['a.webp']);self.commit();base=self.git('rev-parse','HEAD').strip()
        store('https://x.github.io/p',['a.webp','b.webp']);self.commit()
        result=selector.select(self.root,'pull_request',{'pull_request':{'base':{'sha':base}}},'refs/heads/main')
        self.assertEqual(result['files'],['other.html'])
        store('https://y.github.io/q',['a.webp','b.webp']);self.commit()
        result=selector.select(self.root,'pull_request',{'pull_request':{'base':{'sha':base}}},'refs/heads/main')
        self.assertEqual(result['files'],['index.html','other.html'])

    def test_removed_home_page_checks_all_pages(self):
        self.git('rm','-q','index.html');self.commit()
        result=selector.select(self.root,'push',{'before':self.base},'refs/heads/main')
        self.assertEqual(result['files'],['books/index.html'])

    def test_changing_the_checker_does_not_force_the_whole_site_in_a_pr(self):
        """26/11 (run 45891455063): la propia PR del selector revisó las 9.482 páginas y agotó los 40 min.
        Las reglas nuevas las audita el programado, que tiene su propio límite largo."""
        (self.root/'.lycheeignore').write_text('x',encoding='utf-8');self.commit()
        result=selector.select(self.root,'pull_request',{'pull_request':{'base':{'sha':self.base}}},'refs/heads/main')
        self.assertEqual((result['scope'],result['files']),('none',[]))
        workflow=(ROOT/'.github/workflows/broken-links.yml').read_text(encoding='utf-8')
        limit=[l for l in workflow.splitlines() if 'timeout-minutes:' in l][0]
        self.assertIn("github.event_name == 'schedule'",limit)
        self.assertIn('inputs.full_scan',limit)

    def test_workflow_skips_lychee_when_there_is_nothing_to_check(self):
        workflow=(ROOT/'.github/workflows/broken-links.yml').read_text(encoding='utf-8')
        step=workflow[workflow.index('id: lychee'):]
        self.assertIn("if: steps.scope.outputs.skip != 'true'",step[:200])
        self.assertIn("output.write('skip='",(ROOT/'scripts/select-link-check-inputs.py').read_text(encoding='utf-8'))

    def test_shell_metacharacters_and_parent_traversal_cannot_be_emitted(self):
        for name in ['bad;command.html','$(bad).html','../outside.html','bad name.html']:
            with self.subTest(name=name),self.assertRaises(ValueError):
                selector.public_html([name])


if __name__=='__main__':
    unittest.main()
