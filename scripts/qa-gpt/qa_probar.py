"""Probador para el desarrollador Claude: `python <este fichero> <test> [<test>...]` desde el worktree de desarrollo.
Regenera los derivados (como hara la validacion real), ejecuta cada test con su servidor estatico y devuelve el arbol al estado de antes de
regenerar: Claude ve el resultado real sin que pagefind/?v=/HTML generado entren en su diff. Es el UNICO comando que Claude puede ejecutar."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qa_lote, qa_pr  # noqa: E402


class _Q:  # lo minimo que usa Pr._test
    CFG = {}
    ROOT = Path.cwd()
    STATE = Path.cwd()


def main(tests):
    wt = Path.cwd()
    run = qa_lote.run_cmd
    git = lambda *a, cwd=None: run(["git", "-c", "core.autocrlf=false", *a], str(cwd or wt))
    if git("rev-parse", "--show-toplevel")[1].strip().replace("\\", "/").rstrip("/").lower() != str(wt).replace("\\", "/").rstrip("/").lower():
        print("ejecutar desde la raiz del worktree"); return 2
    tests = [t.replace("\\", "/") for t in tests]
    if not tests or any(qa_pr.ruta_segura(t) or not qa_pr.Pr.comando_test(t) or not (wt / t).is_file() for t in tests):
        print("uso: qa_probar.py tests/x.py|qa/x.mjs ... (rutas relativas existentes)"); return 2
    propios = qa_pr.cambiados(git, wt)
    copia = {p: (wt / p).read_bytes() for p in propios if (wt / p).is_file()}
    pr = qa_pr.Pr(_Q, None, run, out=lambda *a: None)
    rc_total = 0
    try:
        regen = qa_pr.regenerar(run, wt, sorted(propios))
        if regen: print("derivados regenerados (no forman parte de tu cambio):", ", ".join(regen))
        for t in tests:
            rc, o = pr._test(wt, t)
            print(f"== {t}: {'PASA' if rc == 0 else f'FALLA (exit {rc})'}")
            if rc: print(o[-2500:]); rc_total = 1
    finally:
        git("checkout", "-q", "--", "."); git("clean", "-fdq", "-e", "node_modules")
        for p, b in copia.items(): (wt / p).parent.mkdir(parents=True, exist_ok=True); (wt / p).write_bytes(b)
    return rc_total


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
