import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('research_validator', ROOT / 'scripts/validate-research-log.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

def document(claim_status, public):
    return ('---\nstatus: published\nresearch_id: RL-QA-001\ntopic: investigacion\nlast_verified: 2026-10-20\n---\n\n'
            '## Afirmaciones\n\n### C01 — Dato editorial\n'
            f'status: {claim_status}\nsource: fuente oficial\nbasis: n/a\nchecked: 2026-10-20\n'
            f'attempts: consulta documentada\nnotes: pendiente de confirmacion\npublic: {public}\n')

with tempfile.TemporaryDirectory() as directory:
    file = Path(directory) / 'research.md'
    file.write_text(document('verified', 'true'), encoding='utf-8')
    assert validator.validate(file) == [], 'Una afirmacion verificada y publica debe aceptarse'
    file.write_text(document('unconfirmed', 'false'), encoding='utf-8')
    assert validator.validate(file) == [], 'Una investigacion publicada puede conservar notas internas no confirmadas'
    file.write_text(document('unconfirmed', 'true'), encoding='utf-8')
    errors = validator.validate(file)
    assert errors, 'FALSO POSITIVO: public:true admite afirmaciones no confirmadas'
print('PASS: publication and verification states remain consistent')
