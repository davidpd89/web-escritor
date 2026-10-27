"""preview: vista previa LOCAL de una mejora (127.0.0.1 solamente). `mw.py vista-previa [ID]`.

Con ID: reconstruye en un worktree efimero el SHA validado de esa mejora (rama mejoras-web/<id>) y lo sirve; sin ID: sirve la rama base del
laboratorio (la web "como si fuera main pero con las mejoras ya aceptadas"). No hace commits, no publica y no abre ninguna PR.
El ENLACE PUBLICO verificable de la rama de laboratorio lo da el workflow manual mejoras-web-preview.yml (documentado en el README, nunca automatico).

PROCEDENCIA: servidor de vista de motor/preview.py de la PR #819 @ e216858c18551cc51f25fa29f809f760c46e6004, reescrito para el nuevo estado.
"""
import functools, http.server, webbrowser
from pathlib import Path

import parches


def raiz(q, exp_id=None):
    if not exp_id: return q.preparar_src(), None
    if not all(ch.isascii() and (ch.isalnum() or ch in "-_") for ch in exp_id): raise ValueError("ID de expediente invalido")
    c = q.db(); e = c.execute("SELECT * FROM expedientes WHERE id=?", (exp_id,)).fetchone()
    if not e or not e["sha"]: raise ValueError("ese expediente no tiene una candidata validada (sin SHA)")
    wt = q.STATE / "preview" / exp_id
    parches.limpiar_wt(wt); wt.parent.mkdir(parents=True, exist_ok=True)
    q.git("worktree", "add", "--detach", str(wt), e["sha"])
    if not (wt / "index.html").is_file(): parches.limpiar_wt(wt); raise ValueError("la candidata no contiene index.html")
    return wt, wt


def main(q, a):
    wt = None
    try:
        if not 1024 <= a.puerto <= 65535: raise ValueError("puerto local invalido")
        carpeta, wt = raiz(q, a.id)
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(carpeta))
        with http.server.ThreadingHTTPServer(("127.0.0.1", a.puerto), handler) as srv:
            url = f"http://127.0.0.1:{a.puerto}/"
            print(f"Vista previa de {a.id or 'la rama base ' + q.CFG['rama_base']}: {url}\nSolo local. Ctrl+C para cerrar.", flush=True)
            if not a.sin_abrir: webbrowser.open(url)
            srv.serve_forever()
    except (ValueError, OSError, RuntimeError) as err:
        print(f"ERROR: {err}"); return 2
    except KeyboardInterrupt:
        print("Vista detenida.")
    finally:
        if wt: parches.limpiar_wt(wt)
    return 0
