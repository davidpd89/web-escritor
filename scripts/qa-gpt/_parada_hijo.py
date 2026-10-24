"""Hijo de test_qa_lote.SenalDeParadaReal: instala la parada real y ejecuta un test largo con run_cmd."""
import sys
import qa_lote as L


class Lo:
    parando = None
    pedir_parada = L.Lote.pedir_parada


lo = Lo()
L.instalar_parada(lo)
L.ABORTAR = lambda: bool(lo.parando)
print("LISTO", flush=True)
rc, out = L.run_cmd([sys.executable, "-c", "import time; time.sleep(120)"], ".", timeout=300)
print("RC", rc, lo.parando, flush=True)
