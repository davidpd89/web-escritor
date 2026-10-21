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
                                ('push',{'before':'0'*40},False),('push',{'before':self.base},False),
                                ('push',{'before':self.base},True)]:
            with self.subTest(name=name,event=event,full=full):
                result=selector.select(self.root,name,event,'refs/heads/main',full)
                self.assertEqual(result['scope'],'full-site')
                self.assertEqual(result['files'],['books/index.html','index.html'])

    def test_deletion_or_rename_checks_all_remaining_pages(self):
        self.git('mv','books/index.html','renamed.html');self.commit()
        result=selector.select(self.root,'push',{'before':self.base},'refs/heads/main')
        self.assertEqual(result['scope'],'full-site')
        self.assertEqual(result['files'],['index.html','renamed.html'])
        self.git('rm','renamed.html');self.commit()
        self.assertEqual(selector.select(self.root,'push',{'before':self.base},'refs/heads/main')['scope'],'full-site')

    def test_shell_metacharacters_and_parent_traversal_cannot_be_emitted(self):
        for name in ['bad;command.html','$(bad).html','../outside.html','bad name.html']:
            with self.subTest(name=name),self.assertRaises(ValueError):
                selector.public_html([name])


if __name__=='__main__':
    unittest.main()
