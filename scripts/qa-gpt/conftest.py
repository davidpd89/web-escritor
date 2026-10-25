"""Aislamiento entre tests: muchos setUp redirigen los globales de qa_gpt (ROOT, STATE, DB_PATH, WT, Lock.path, CFG) a un temporal y no los
restauraban. El test siguiente heredaba un ROOT ya borrado y fallaba segun el orden (NotADirectoryError en test_qa_gpt/test_qa_contratos).
Este fixture guarda y restaura esos globales alrededor de CADA test, incluidos los que se escriban en el futuro."""
import copy

import pytest

import qa_gpt

GLOBALES = ("ROOT", "STATE", "DB_PATH", "WT", "AUTORIZ")


@pytest.fixture(autouse=True)
def _aislar_globales_qa_gpt():
    previos = {n: getattr(qa_gpt, n) for n in GLOBALES if hasattr(qa_gpt, n)}
    lock = getattr(qa_gpt.Lock, "path", None)
    cfg = copy.deepcopy(qa_gpt.CFG)
    yield
    for n, v in previos.items(): setattr(qa_gpt, n, v)
    if lock is not None: qa_gpt.Lock.path = lock
    qa_gpt.CFG.clear(); qa_gpt.CFG.update(cfg)
