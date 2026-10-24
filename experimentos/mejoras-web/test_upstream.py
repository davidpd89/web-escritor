#!/usr/bin/env python3
import base64, sys, unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent/"motor"))
import verificar_upstream

class Upstream(unittest.TestCase):
    def test_codigo_original_real_y_licencia(self):
        sha="a"*40
        item={"url":"https://github.com/org/project"}
        data={"fuente_sha":sha,"codigo_original":"def apply_patch():\n    return True","licencia":"MIT"}
        fuente=data["codigo_original"]+"\n"
        def fetch(url):
            if "/git/blobs/" in url:
                return {"sha":sha,"encoding":"base64","content":base64.b64encode(fuente.encode()).decode()}
            if url.endswith("/license"): return {"license":{"spdx_id":"MIT"}}
            raise AssertionError(url)
        r=verificar_upstream.verificar(data,item,fetch)
        self.assertTrue(r["upstream_verificado"])
    def test_falso_fragmento_rechazado(self):
        sha="b"*40
        data={"fuente_sha":sha,"codigo_original":"import inexistente","licencia":"MIT"}
        def fetch(url):
            return {"sha":sha,"encoding":"base64","content":base64.b64encode(b"texto diferente").decode()}
        with self.assertRaises(verificar_upstream.FuenteNoVerificada):
            verificar_upstream.verificar(data,{"url":"https://github.com/org/repo"},fetch)
    def test_sha_corto_no_aceptado(self):
        with self.assertRaises(verificar_upstream.FuenteNoVerificada):
            verificar_upstream.verificar({"fuente_sha":"abc","codigo_original":"texto realmente copiado"},
                                        {"url":"https://github.com/org/repo"},lambda _: {})
    def test_documentacion_no_simula_codigo(self):
        r=verificar_upstream.verificar({},{"url":"https://developers.google.com/search/updates"})
        self.assertFalse(r["upstream_verificado"])
if __name__=="__main__": unittest.main()
