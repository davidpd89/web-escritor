#!/usr/bin/env python3
"""Vista separada de un worktree hijo, exclusivamente en localhost. No hace commits ni merge."""
import argparse, functools, hashlib, http.server, json, sys, webbrowser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import rotacion


def carpeta_ciclo():
    return rotacion.ubicacion_estado().parent/"ciclo"


def destino(estado,expediente_id=None):
    d=Path(estado).resolve()
    if expediente_id:
        if not all(ch.isascii() and (ch.isalnum() or ch in "-_") for ch in expediente_id):
            raise ValueError("ID de expediente inválido")
        key=hashlib.sha256(expediente_id.encode("utf-8")).hexdigest()[:16]
        ruta=d/"propuestas"/(key+".json")
    else:
        ruta=d/"actual.json"
        if ruta.is_file():
            actual=json.loads(ruta.read_text(encoding="utf-8"))
            if not (actual.get("validacion") or {}).get("worktree"):
                ruta=d/"ultima_propuesta.json"
        else:
            ruta=d/"ultima_propuesta.json"
    if not ruta.is_file():
        raise ValueError("No hay propuestas guardadas; el ciclo debe validar primero un parche")
    registro=json.loads(ruta.read_text(encoding="utf-8"))
    raw=(registro.get("validacion") or {}).get("worktree")
    if not raw: raise ValueError("Esta propuesta no tiene worktree validado")
    wt=Path(raw).resolve()
    if not wt.is_relative_to((d/"worktrees").resolve()) or not wt.is_dir():
        raise ValueError("Worktree fuera del estado del laboratorio o ya inexistente")
    if not (wt/"index.html").is_file():
        raise ValueError("Worktree sin página principal")
    return wt


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--puerto",type=int,default=8766)
    p.add_argument("--estado-dir",type=Path,default=carpeta_ciclo())
    p.add_argument("--sin-abrir",action="store_true")
    p.add_argument("--id",help="ID exacto de una propuesta anterior, como SEO-01")
    args=p.parse_args()
    try:
        root=destino(args.estado_dir,args.id)
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
