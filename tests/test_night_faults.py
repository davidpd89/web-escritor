"""Simulador de fallos de una noche (ronda 4 de la revisión GPT, 25/11): S06, el runner muere después del checkpoint.

Invariante: unos datos consultados nunca se pierden. El punto de guardado `reading-datos-*` solo se borra cuando sus
datos ya están publicados (publisher.run volvió) o cuando no hay nada que publicar. Si la ejecución muere en
cualquier punto entre el guardado y la publicación (un generador, los contratos, el push, la PR, la CI, el límite de
tiempo del job), la rama sigue y la siguiente ejecución la recupera con `carry` sin consultar las fuentes
(test_reading_checkpoint.py prueba esa recuperación con git real).
"""
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_reading_branch_retry import refresh  # noqa: E402

SAVED = refresh.CHECKPOINT_PREFIX + '2026-11-25-1'
REPORT = {'new_books': ['isbn-1'], 'updated_books': [], 'stats': {}}


class Muere(Exception):
    """El runner muere aquí (en Actions: cancelación, timeout del job o runner perdido)."""


class RunnerMuertoTrasElCheckpoint(unittest.TestCase):
    PUNTOS = ('construir', 'comprobar', 'contratos', 'push', 'pr', 'publicar')

    def noche(self, muere_en=None, report=REPORT, rutas=('data/reading-catalogue.json',)):
        """assemble() con todo lo externo simulado; devuelve la secuencia de pasos hasta morir o terminar."""
        pasos = MagicMock()

        def paso(nombre, valor=None):
            def f(*a, **k):
                getattr(pasos, nombre)(*a)
                if nombre == muere_en:
                    raise Muere(nombre)
                return valor
            return f

        def gh(*args):
            return paso('pr', '')(*args) if args[:2] == ('pr', 'create') else ''

        with tempfile.TemporaryDirectory() as tmp, ExitStack() as s:
            p = lambda obj, name, f: s.enter_context(patch.object(obj, name, side_effect=f))  # noqa: E731
            s.enter_context(patch.object(refresh, 'ROOT', Path(tmp)))
            p(refresh.reading_quarantine, 'apply', lambda *a, **k: [])
            p(refresh, 'command', lambda *a: None)
            p(refresh, 'read_json', lambda *a: {})
            p(refresh.subprocess, 'check_output', lambda *a, **k: '')
            p(refresh.materializar, 'construir', paso('construir'))
            p(refresh.materializar, 'comprobar', paso('comprobar'))
            p(refresh, 'data_contract_failures', paso('contratos', []))
            p(refresh, 'quarantine_alert', lambda *a: None)
            p(refresh, 'quarantine_alert_note', lambda: '')
            p(refresh, 'quarantine_summary', lambda *a: '')
            p(refresh.git_estado, 'rutas', lambda *a: list(rutas))
            p(refresh.git_estado, 'preparar', lambda *a, **k: None)
            p(refresh.publisher.publication, 'fresh_branch', lambda *a, **k: 'automation/reading-catalogue-2026-11-25-1')
            p(refresh, 'bot_identity', lambda *a: None)
            p(refresh.cover_store, 'flush', lambda *a: 0)
            p(refresh, 'push', paso('push'))
            p(refresh.publisher.publication, 'gh', gh)
            p(refresh.publisher, 'run', paso('publicar'))
            p(refresh, 'drop_checkpoint', paso('borrar'))
            try:
                refresh.assemble(report, changed=False, checkpoint=SAVED)
            except Muere:
                pass
        return [c[0] for c in pasos.mock_calls]

    def test_el_checkpoint_sobrevive_a_una_muerte_en_cualquier_punto(self):
        for punto in self.PUNTOS:
            with self.subTest(muere_en=punto):
                pasos = self.noche(muere_en=punto)
                self.assertEqual(pasos[-1], punto, f'la noche no llegó a {punto}: {pasos}')
                self.assertNotIn('borrar', pasos, f'muerta en {punto}, el checkpoint se borró sin publicar')

    def test_solo_se_borra_despues_de_publicar(self):
        pasos = self.noche()
        self.assertEqual(pasos[-2:], ['publicar', 'borrar'])
        self.assertEqual(pasos.count('borrar'), 1)

    def test_sin_nada_que_publicar_se_borra_sin_abrir_pr(self):
        """Lo guardado ya está en main (o no cambió nada): borrar no pierde datos y no se abre una PR vacía."""
        pasos = self.noche(report={'new_books': [], 'updated_books': [], 'stats': {}})
        self.assertEqual(pasos, ['borrar'])

    def test_cambios_fuera_de_lo_permitido_paran_sin_borrar(self):
        with self.assertRaises(ValueError):
            self.noche(rutas=('scripts/otra-cosa.py',))


class ErrorDeRedSuelto(unittest.TestCase):
    """S01 (502 de GitHub): follow_main() hace un fetch justo antes de save_checkpoint, tras ~80 min de ingesta. Un
    502 suelto ahí tiraba todo lo consultado sin guardarlo. Las órdenes git de red se repiten con espera."""

    def test_fetch_y_ls_remote_se_repiten_con_espera(self):
        import subprocess
        real, fallos, esperas = subprocess.run, {'fetch': 2, 'ls-remote': 2}, []

        def run(cmd, *a, **kw):
            orden = cmd[1] if cmd[:1] == ['git'] else None
            if fallos.get(orden):
                fallos[orden] -= 1
                raise subprocess.CalledProcessError(128, cmd, b'', b'fatal: The requested URL returned error: 502')
            return real(cmd, *a, **kw)
        from test_reading_branch_retry import Repo
        with tempfile.TemporaryDirectory() as tmp:
            repo = Repo(tmp)
            repo.main_moves({'otro.txt': 'x\n'})
            with patch.object(refresh.subprocess, 'run', side_effect=run), \
                    patch.object(refresh.time, 'sleep', side_effect=esperas.append):
                self.assertEqual(refresh.follow_main(root=repo.work), repo.git('rev-parse', 'origin/main'))
                self.assertEqual(refresh.checkpoints(root=repo.work), [])
        self.assertEqual(fallos, {'fetch': 0, 'ls-remote': 0})
        self.assertTrue(len(esperas) == 4 and all(s > 0 for s in esperas), esperas)

    def test_un_error_local_no_se_repite(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp, patch.object(refresh.time, 'sleep') as dormir:
            with self.assertRaises(subprocess.CalledProcessError):
                refresh.git('rev-parse', 'HEAD', root=Path(tmp))
            dormir.assert_not_called()


if __name__ == '__main__':
    unittest.main()
