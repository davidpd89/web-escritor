import importlib.util
import importlib.util as _iu
import unittest
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('local_ci', ROOT / 'scripts' / 'local-ci.py')
local_ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local_ci)


class Lotes(unittest.TestCase):
    @unittest.skipUnless(_iu.find_spec('yaml'), 'sin PyYAML no se leen los workflows')
    def test_la_suite_completa_se_reparte_en_lotes(self):
        commands = [c for c, _, _ in local_ci.collect(set(), True)]
        self.assertNotIn(local_ci.SUITE, commands)
        lotes = [c for c in commands if '--unittest-shard' in c]
        self.assertEqual(len(lotes), local_ci.SHARDS)

    def test_los_lotes_cubren_cada_fichero_una_vez(self):
        files = sorted(p.name for p in (ROOT / 'tests').glob('test_*.py'))
        repartidos = [f for i in range(local_ci.SHARDS) for f in files[i::local_ci.SHARDS]]
        self.assertEqual(sorted(repartidos), files)




class ScopedTest(unittest.TestCase):
    ci = local_ci

    def test_script_suelto_corre_solo_sus_tests(self):
        refs = {'rebase-regenerando': {'scripts/rebase-regenerando.py', 'tests/test_rebase_regenerando.py'}}
        items = self.ci.scoped({'scripts/rebase-regenerando.py'}, refs=lambda s: refs[s])
        self.assertEqual([c for c, *_ in items], [
            'python -m py_compile scripts/rebase-regenerando.py',
            'python -m unittest discover -s tests -p test_rebase_regenerando.py'])

    def test_script_usado_por_un_workflow_va_por_la_via_completa(self):
        refs = {'build-sitemap': {'.github/workflows/content-index-check.yml', 'tests/test_sitemap.py'}}
        self.assertIsNone(self.ci.scoped({'scripts/build-sitemap.py'}, refs=lambda s: refs[s]))

    def test_otro_fichero_va_por_la_via_completa(self):
        self.assertIsNone(self.ci.scoped({'scripts/x.py', 'data/reading-books.json'}, refs=lambda s: set()))


class ServidoresVigilados(unittest.TestCase):
    def test_un_servidor_caido_se_relanza(self):
        import tempfile
        with tempfile.TemporaryDirectory() as root, local_ci.Servers(root) as servers:
            port = servers.ports[4173]
            self.assertTrue(servers.alive(port))
            servers.procs[4173].kill()
            servers.procs[4173].wait()
            servers.ensure()
            self.assertEqual(servers.restarts, 1)
            self.assertTrue(servers.alive(port))

    def test_dos_puertas_a_la_vez_no_comparten_puertos(self):
        """10/11: con 4173/4175 fijos solo cabía una puerta por máquina y las demás esperaban en cola."""
        import tempfile
        with tempfile.TemporaryDirectory() as root, local_ci.Servers(root) as a, local_ci.Servers(root) as b:
            self.assertFalse(set(a.ports.values()) & set(b.ports.values()))
            self.assertNotIn(4173, a.ports.values())
        for servers in (a, b):
            self.assertFalse(any(servers.alive(p) for p in servers.ports.values()))

    def test_remap_lleva_el_puerto_real_al_comando_y_al_entorno(self):
        import tempfile
        with tempfile.TemporaryDirectory() as root:
            qa = Path(root, 'qa')
            qa.mkdir()
            Path(qa, 'x.mjs').write_text("const B = process.env.FERIAS_BASE_URL || 'http://127.0.0.1:4173';\n"
                                         "const C = process.env.QA_BASE_URL||'http://127.0.0.1:4175';\n", encoding='utf-8')
            servers = local_ci.Servers(root)
            servers.ports = {4173: 50001, 4175: 50002}
            command, env = servers.remap('node qa/x.mjs http://127.0.0.1:4173/a/', {'QA_ORIGIN': 'http://127.0.0.1:4173'})
        self.assertEqual(command, 'node qa/x.mjs http://127.0.0.1:50001/a/')
        self.assertEqual(env, {'QA_ORIGIN': 'http://127.0.0.1:50001', 'FERIAS_BASE_URL': 'http://127.0.0.1:50001',
                               'QA_BASE_URL': 'http://127.0.0.1:50002'})

    def test_toda_prueba_que_cita_el_puerto_lo_lee_del_entorno(self):
        """Trinquete: un literal 127.0.0.1:4173 sin variable de entorno en su línea ignoraría el puerto real."""
        fijos = []
        for pattern in ('qa/**/*.mjs', 'tests/**/*.mjs', 'scripts/*.mjs'):
            for path in local_ci.ROOT.glob(pattern):
                for n, line in enumerate(path.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
                    code = line.split('//')[0] if not line.lstrip().startswith('//') else ''
                    if local_ci.LITERAL.search(code) and not local_ci.ENV_NAME.search(code) and 'argv' not in code:
                        fijos.append(f'{path.relative_to(local_ci.ROOT)}:{n}')
        self.assertEqual(fijos, [])


class EntornoDelCI(unittest.TestCase):
    def test_un_entorno_a_medias_se_rehace(self):
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'scripts').mkdir()
            (root / 'scripts/requirements.txt').write_text('Pillow==12.3.0\n', encoding='utf-8')
            pips = []

            def run(cmd, **_):
                if 'venv' in cmd:
                    exe = Path(cmd[-1]) / ('Scripts/python.exe' if local_ci.os.name == 'nt' else 'bin/python')
                    exe.parent.mkdir(parents=True)
                    exe.write_text('')
                elif 'pip' in cmd:
                    pips.append(cmd)
                    if len(pips) == 1:
                        raise KeyboardInterrupt  # puerta cortada a mitad del pip install

            with mock.patch.object(local_ci, 'ROOT', root), mock.patch.object(local_ci.subprocess, 'run', run):
                with self.assertRaises(KeyboardInterrupt):
                    local_ci.ci_python()
                local_ci.ci_python()                    # python.exe existe pero sin marca: se rehace
                self.assertEqual(len(pips), 2)
                local_ci.ci_python()                    # con la marca no se reinstala
                self.assertEqual(len(pips), 2)


class NodeModulesDelWorktree(unittest.TestCase):
    def test_un_worktree_nuevo_enlaza_los_del_checkout_principal(self):
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            principal, wt = Path(d) / 'principal', Path(d) / 'wt'
            principal.mkdir()
            git = lambda *a, cwd=principal: subprocess.run(['git', *a], cwd=cwd, check=True, capture_output=True)
            git('init', '-q')
            (principal / 'package-lock.json').write_text('{}', encoding='utf-8')
            git('add', '.')
            git('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'x')
            (principal / 'node_modules/playwright').mkdir(parents=True)
            git('worktree', 'add', '-q', '--detach', str(wt))
            local_ci.node_modules_listos(wt)
            self.assertTrue((wt / 'node_modules/playwright').exists())
            local_ci.node_modules_listos(wt)            # ya están: no hace nada
            if local_ci.os.name == 'nt':                # quitar la unión sin borrar el destino
                subprocess.run(['cmd', '/c', 'rmdir', str(wt / 'node_modules')], check=True)
            else:
                (wt / 'node_modules').unlink()


class EntornoCiego(unittest.TestCase):
    """10/11: venv sin Pillow ni requests y worktree sin node_modules → 27 comprobaciones «ya fallan en main»."""

    def test_el_servidor_aguanta_muchas_conexiones_a_la_vez(self):
        import tempfile
        from concurrent.futures import ThreadPoolExecutor
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'index.html').write_text('ok', encoding='utf-8')
            with local_ci.Servers(tmp) as servers:
                port = servers.ports[4173]
                fetch = lambda _: local_ci.urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=20).status
                with ThreadPoolExecutor(64) as pool:
                    self.assertEqual(set(pool.map(fetch, range(400))), {200})

    def test_cada_comando_construye_su_propia_distribucion(self):
        a = local_ci.private_dist('node tests/test-seo-discoverability-smoke.mjs', ROOT)
        b = local_ci.private_dist('node qa/sitewide-console-errors-browser.mjs', ROOT)
        self.assertNotEqual(a, b)
        code, output, _ = local_ci.run_one('echo "$SITEWIDE_DIST"', {}, ROOT)
        self.assertEqual(output.strip().replace('\\', '/'), str(local_ci.private_dist('echo "$SITEWIDE_DIST"', ROOT)).replace('\\', '/'))

    def test_un_fallo_del_entorno_no_se_da_por_conocido_aunque_main_falle_igual(self):
        for output in ("ModuleNotFoundError: No module named 'PIL'",
                       "Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'playwright'",
                       'npm error npx canceled due to missing packages and no YES option: ["pagefind@1.6.0"]'):
            self.assertFalse(local_ci.same_failure((1, output, 0), (1, output, 0)), output)

    def test_un_fallo_real_igual_en_main_sigue_siendo_conocido(self):
        output = 'AssertionError: 3 != 4'
        self.assertTrue(local_ci.same_failure((1, output, 0), (1, output, 0)))


class ContextoDeGitHubEnLocal(unittest.TestCase):
    CTX = {'github.event.pull_request.base.sha': 'b4se', 'github.sha': 'h3ad', 'github.event_name': 'pull_request'}

    def test_la_base_de_la_pr_llega_a_la_prueba(self):
        env = local_ci.plain_env({'BASE_SHA': '${{ github.event.pull_request.base.sha }}', 'X': 'y'}, self.CTX)
        self.assertEqual(env, {'BASE_SHA': 'b4se', 'X': 'y'})

    def test_alternativas_y_condiciones(self):
        env = local_ci.plain_env({
            'A': "${{ github.event.workflow_run.head_sha || github.sha }}",
            'B': "${{ github.event.inputs.mode || 'auto' }}",
            'C': "${{ github.event_name == 'pull_request' && 'http://127.0.0.1:4173' || 'https://x.com' }}",
            'D': "${{ github.event.pull_request.body }}"}, self.CTX)
        self.assertEqual(env, {'A': 'h3ad', 'B': 'auto', 'C': 'http://127.0.0.1:4173'})

    def test_toda_base_de_pr_de_los_workflows_se_resuelve_en_local(self):
        """Trinquete: ninguna variable que un workflow saca de la base o la cabeza de la PR se queda sin valor."""
        sin_valor = []
        for wf in (ROOT / '.github/workflows').glob('*.yml'):
            for k, v in re.findall(r'^\s+([A-Z_]+):\s*(\$\{\{.*?\}\})\s*$', wf.read_text(encoding='utf-8'), re.M):
                if re.search(r'pull_request\.(base|head)\.sha|github\.(sha|event_name|head_ref)', v):
                    if not local_ci.plain_env({k: v}, {**self.CTX, 'github.event.pull_request.head.sha': 'h3ad',
                                                        'github.head_ref': 'r', 'github.ref_name': 'r'}):
                        sin_valor.append(f'{wf.name}: {k}')
        self.assertEqual(sin_valor, [])


class PuertaPorImpacto(unittest.TestCase):
    WORKFLOW = [('python scripts/check-reading-data.py', {}, 'carga.yml'),
                ('node qa/otra-cosa.mjs', {}, 'otra.yml'),
                ('python tests/test-lector.py', {}, 'gate.yml')]
    REFS = {'modulo': {'scripts/lector.py', 'tests/test_modulo.py'},
            'lector': {'tests/test-lector.py'},
            'datos.json': {'scripts/check-reading-data.py'},
            'check-reading-data': set(),
            'test_modulo': set(), 'huerfano.json': set()}

    def impacto(self, changed):
        return local_ci.impacto(changed, refs=lambda s: set(self.REFS.get(s, set())), workflow=self.WORKFLOW)

    def test_un_cambio_global_va_por_la_via_completa(self):
        self.assertIsNone(self.impacto(['.github/workflows/x.yml']))
        self.assertIsNone(self.impacto(['scripts/local-ci.py']))

    def test_un_modulo_arrastra_sus_tests_y_los_de_quien_lo_importa(self):
        cmds = [c for c, _, _ in self.impacto(['scripts/modulo.py'])]
        self.assertIn('python -m unittest discover -s tests -p test_modulo.py', cmds)
        self.assertIn('python tests/test-lector.py', cmds)  # en la forma del workflow
        self.assertNotIn('node qa/otra-cosa.mjs', cmds)

    def test_un_dato_arrastra_el_paso_que_lo_lee(self):
        cmds = [c for c, _, _ in self.impacto(['data/datos.json'])]
        self.assertIn('python scripts/check-reading-data.py', cmds)

    def test_un_dato_que_nada_nombra_va_por_la_via_completa(self):
        self.assertIsNone(self.impacto(['data/huerfano.json']))

    def test_un_fichero_central_va_por_la_via_completa(self):
        self.REFS = {**self.REFS, 'modulo': {f'scripts/s{i}.py' for i in range(local_ci.CENTRAL + 1)}}
        self.assertIsNone(self.impacto(['scripts/modulo.py']))


if __name__ == '__main__':
    unittest.main()
