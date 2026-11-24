import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "check_wikidata_sameas", Path(__file__).resolve().parents[1] / "scripts" / "check-wikidata-sameas.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_author_qid_accepted_only_on_its_own_verified_page(tmp_path):
    report = tmp_path / "r.json"
    report.write_text(json.dumps({
        "agatha-christie": {"qid": "Q35064", "motivo": "escritor"},
        "homonimo": {"qid": "Q1", "motivo": "ambiguo (2)"},
    }), encoding="utf-8")
    authors = module.verified_authors(report)
    assert authors == {"agatha-christie": "Q35064"}
    own = [(Path("recomendaciones/autores/agatha-christie/index.html"), 38)]
    assert module.author_verified("Q35064", own, authors)
    # Wrong QID for the page, another author's page, a non-author page, or no reference: rejected.
    assert not module.author_verified("Q1212", own, authors)
    assert not module.author_verified("Q35064", [(Path("recomendaciones/autores/otra/index.html"), 1)], authors)
    assert not module.author_verified("Q35064", own + [(Path("recomendaciones/index.html"), 5)], authors)
    assert not module.author_verified("Q35064", [], authors)


def test_missing_report_accepts_nothing(tmp_path):
    assert module.verified_authors(tmp_path / "missing.json") == {}
