#!/usr/bin/env python3
"""Vista separada de un worktree hijo, exclusivamente en localhost. No hace commits ni merge."""
import argparse, functools, http.server, json, sys, webbrowser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import rotacion


def carpeta_ciclo():
    return rotacion.ubicacion_estado().parent/"ciclo"


def destino(estado):
    d=Path(estado).resolve()
    actual=d/"actual.json"
    if not actual.is_file():
        raise ValueError("No hay expediente: ejecuta primero el ciclo del laboratorio")
    registro=json.loads(actual.read_text(encoding="utf-8"))
    info=registro.get("validacion") or {}
    raw=info.get("worktree")
    if not raw:
        raise ValueError("No existe un worktree validado para el expediente actual")
    wt=Path(raw).resolve()
    previsto=(d/"worktrees").resolve()
    if not wt.is_relative_to(previsto) or not wt.is_dir():
        raise ValueError("Worktree de preview fuera del estado del laboratorio")
    if not (wt/"index.html").is_file():
        raise ValueError("No se puede previsualizar una web sin index.html")
    return wt


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--puerto",type=int,default=8766)
    p.add_argument("--estado-dir",type=Path,default=carpeta_ciclo())
    p.add_argument("--sin-abrir",action="store_true")
    args=p.parse_args()
    try:
        root=destino(args.estado_dir)
        if not 1024<=args.puerto<=65535: raise ValueError("Puerto local inválido")
        handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root))
        with http.server.ThreadingHTTPServer(("127.0.0.1",args.puerto),handler) as servidor:
            url=f"http://127.0.0.1:{args.puerto}/"
            print(f"Worktree de PR: {root}\nPreview: {url}\nCtrl+C para cerrar.",flush=True)
            if not args.sin_abrir: webbrowser.open(url)
            servidor.serve_forever()
    except (ValueError,OSError,json.JSONDecodeError) as err:
        print(f"ERROR: {err}",file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Vista detenida.")
    return 0


if __name__=="__main__": raise SystemExit(main())
