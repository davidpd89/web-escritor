import unittest
from unittest import mock
import util
import mw


class RamaBase(util.Caso):
    def test_base_ausente_da_un_error_claro_con_el_comando_para_arreglarlo(self):
        util.git(self.repo, "update-ref", "-d", "refs/remotes/origin/lab/mejoras-web-20261024"); mw._ULTIMO_FETCH.clear()
        with self.assertRaisesRegex(RuntimeError, r"git fetch origin lab/mejoras-web-20261024"): mw.head_base()

    def test_si_falta_intenta_el_fetch_una_vez_y_se_recupera(self):
        util.git(self.repo, "update-ref", "-d", "refs/remotes/origin/lab/mejoras-web-20261024"); mw._ULTIMO_FETCH.clear()
        real = mw.git
        def git(*a, **k):
            if a[:1] == ("fetch",): util.git(self.repo, "update-ref", "refs/remotes/origin/lab/mejoras-web-20261024", "main"); return ""
            return real(*a, **k)
        with mock.patch.object(mw, "git", git): self.assertRegex(mw.head_base(), "^[0-9a-f]{40}$")

    def test_no_repite_el_fetch_en_cada_paso(self):
        mw._ULTIMO_FETCH.clear(); llamadas = []
        real = mw.git
        def git(*a, **k):
            if a[:1] == ("fetch",): llamadas.append(a)
            return real(*a, **k)
        with mock.patch.object(mw, "git", git):
            for _ in range(5): mw.head_base()
        self.assertLessEqual(len(llamadas), 1)


if __name__ == "__main__":
    unittest.main()
