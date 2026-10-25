"""Metrica unica del flujo: correcciones integradas por hora (y su embudo). Uso: python qa_metricas.py [horas=6]"""
import sqlite3, sys, datetime as dt
def main(horas=6):
    c = sqlite3.connect("C:/GIT/qa-gpt-state/estado.db"); c.row_factory = sqlite3.Row
    desde = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=horas)).isoformat()
    emb = c.execute("SELECT pr_estado e, COUNT(*) n FROM triaje GROUP BY 1").fetchall()
    ok = c.execute("SELECT COUNT(*) FROM triaje WHERE pr_estado IN ('integrada','integrada_auto') AND actualizado>=?", (desde,)).fetchone()[0]
    print(f"integradas en {horas} h: {ok} -> {ok/horas:.2f}/h (base 1,75/h)")
    print("embudo:", {r["e"]: r["n"] for r in emb})
if __name__ == "__main__": main(float(sys.argv[1]) if len(sys.argv) > 1 else 6)
