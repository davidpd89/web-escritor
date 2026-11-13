from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import telegram_guardian as g


def run(status, conclusion, created, updated):
    return {"status": status, "conclusion": conclusion, "createdAt": created, "updatedAt": updated}


def test_cycle_detection():
    now = datetime(2026, 11, 14, 11, 50, tzinfo=timezone.utc).astimezone()
    day = now.date().isoformat()
    def at(h, m):
        return now.replace(hour=h, minute=m, second=0).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert not g.cycle_done_or_running([], now)
    assert g.cycle_done_or_running([run("in_progress", None, at(9, 30), at(9, 31))], now)
    assert g.cycle_done_or_running([run("completed", "success", at(9, 30), at(11, 34))], now)
    # un éxito anterior a las 11:30 (por ejemplo un ciclo que no envió) no cuenta
    assert not g.cycle_done_or_running([run("completed", "success", at(9, 0), at(9, 10))], now)
    assert not g.cycle_done_or_running([run("completed", "failure", at(11, 30), at(11, 40))], now)
