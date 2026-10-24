#!/usr/bin/env python3
"""Selector de investigaciones: rotacion determinista, offline, sin APIs ni secretos.

Es el adaptador de ENTRADA al futuro orquestador local GPT/Claude, no su sustituto.
No hace llamadas a LLM, no crea PR, no dispara Actions y no modifica main.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOGO = ROOT / "catalogo.json"
ORDEN_CANALES = ("auditoria_local", "github", "web", "api", "sector")
CIERRES = ("investigada", "descartada", "sin_evidencia", "pendiente_revision")
PRIORIDAD = {"P1": 0, "P2": 1, "P3": 2}


def ubicacion_estado() -> Path:
    """Estado local fuera de Git, separado por ruta del worktree."""
    raiz = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "state"))
    slug = hashlib.sha256(str(ROOT.resolve()).encode("utf-8")).hexdigest()[:16]
    return raiz / "web-escritor-mejoras" / slug / "rotacion.json"


def leer(path: Path, defecto):
    if not path.exists():
        return defecto
    return json.loads(path.read_text(encoding="utf-8"))


def catalogo(path: Path = CATALOGO) -> dict:
    datos = leer(path, {})
    if datos.get("schema_version") != 1 or not isinstance(datos.get("ideas"), list):
        raise ValueError("Catalogo sin contrato válido")
    ids = set()
    for idea in datos["ideas"]:
        if idea.get("id") in ids:
            raise ValueError("ID duplicado")
        ids.add(idea["id"])
        if idea.get("canal") not in ORDEN_CANALES or not idea.get("familia"):
            raise ValueError(f"Sin familia o canal válido: {idea['id']}")
    return datos


def estado(path: Path) -> dict:
    st = leer(path, {"schema": 1, "pendiente": None, "historial": []})
    if st.get("schema") != 1 or not isinstance(st.get("historial"), list):
        raise ValueError("Estado incompatible. No se modifica ni reinicia.")
    if "pendiente" not in st:
        raise ValueError("Estado sin clave pendiente")
    return st


@contextmanager
def bloqueo(path: Path):
    """Exclusión entre dos lanzadores: no duplica reservas al ejecutar a la vez."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix(".lock")
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise ValueError(f"Selector en uso: {lock}. No borrar mientras esté activo.") from exc
    try:
        yield
    finally:
        lock.rmdir()


def guardar(path: Path, st: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporal = path.with_suffix(".tmp")
    with temporal.open("w", encoding="utf-8") as archivo:
        json.dump(st, archivo, ensure_ascii=False, indent=2)
        archivo.write("\n")
        archivo.flush()
        os.fsync(archivo.fileno())
    os.replace(temporal, path)


def seleccionar(datos: dict, st: dict, familia: str | None = None,
               canal: str | None = None, elegir: str | None = None) -> dict | None:
    """Elige UN expediente; un pendiente previo es idempotente o bloquea override."""
    if st["pendiente"]:
        actual = st["pendiente"]["id"]
        if elegir and actual != elegir:
            raise ValueError(f"Pendiente {actual}; cerrar/liberar antes de elegir {elegir}")
        if familia and st["pendiente"]["familia"] != familia:
            raise ValueError(f"Pendiente {actual} pertenece a otra familia")
        if canal and st["pendiente"]["canal"] != canal:
            raise ValueError(f"Pendiente {actual} pertenece a otro canal")
        return st["pendiente"]
    completados = {h["id"] for h in st["historial"]}
    candidates = [i for i in datos["ideas"]
                  if i["estado"] == "candidata" and i["id"] not in completados
                  and (not familia or i["familia"] == familia)
                  and (not canal or i["canal"] == canal)]
    if elegir:
        candidates = [i for i in candidates if i["id"] == elegir]
        if not candidates:
            raise ValueError(f"No elegible o ya investigada: {elegir}")
    if not candidates:
        return None
    cuenta_c = Counter(h["canal"] for h in st["historial"])
    cuenta_f = Counter(h["familia"] for h in st["historial"])
    # Con canal/ID concreto se respeta elección. Si no, se escoge el canal
    # menos explorado y luego la familia menos explorada de ese canal.
    if not canal and not elegir:
        minimo = min(cuenta_c[i["canal"]] for i in candidates)
        candidatos_c = [c for c in ORDEN_CANALES
                        if cuenta_c[c] == minimo and any(i["canal"] == c for i in candidates)]
        canal_elegido = candidatos_c[0]
        candidates = [i for i in candidates if i["canal"] == canal_elegido]
    if not familia and not elegir:
        menor = min(cuenta_f[i["familia"]] for i in candidates)
        candidates = [i for i in candidates if cuenta_f[i["familia"]] == menor]
    # Los empates se resuelven establemente por prioridad, después por ID.
    return min(candidates, key=lambda x: (PRIORIDAD[x["prioridad"]], x["id"]))


def tarea(item: dict) -> dict:
    return {
        "id": item["id"], "titulo": item["titulo"], "familia": item["familia"],
        "canal": item["canal"], "hipotesis": item["hipotesis"],
        "antiduplicacion": item["antiduplicacion"],
        "criterio_medicion": item["criterio_medicion"],
        "base_pr": "lab/mejoras-web-20261024",
        "prompt_investigador": "experimentos/mejoras-web/contratos/GPT-INVESTIGAR.md",
        "prompt_revisor": "experimentos/mejoras-web/contratos/CLAUDE-REVISAR.md",
    }


def ejecutar(args) -> dict:
    datos = catalogo(args.catalogo)
    cambiar = args.siguiente or bool(args.elegir or args.resultado or args.liberar or args.reactivar)
    if cambiar:
        with bloqueo(args.estado_archivo):
            st = estado(args.estado_archivo)
            result, modificar = accion(datos, st, args)
            if modificar:
                guardar(args.estado_archivo, st)
            return result
    return accion(datos, estado(args.estado_archivo), args)[0]


def accion(datos, st, args):
    if args.reactivar:
        if st["pendiente"] and st["pendiente"]["id"] == args.reactivar:
            raise ValueError("No reactivar una tarea pendiente")
        anteriores = len(st["historial"])
        st["historial"] = [x for x in st["historial"] if x["id"] != args.reactivar]
        return {"reactivada": args.reactivar, "existia": len(st["historial"]) != anteriores}, len(st["historial"]) != anteriores
    if args.resultado:
        p = st["pendiente"]
        if not p:
            raise ValueError("No hay investigación pendiente para cerrar")
        st["historial"].append({**{k: p[k] for k in ("id", "familia", "canal")},
                               "resultado": args.resultado, "cerrada_utc": datetime.now(timezone.utc).isoformat()})
        st["pendiente"] = None
        return {"cerrada": p["id"], "resultado": args.resultado}, True
    if args.liberar:
        p = st["pendiente"]
        if not p:
            return {"liberada": None}, False
        st["pendiente"] = None
        return {"liberada": p["id"], "nota": "Vuelve a quedar elegible"}, True
    if args.ver_estado:
        return {"pendiente": st["pendiente"], "cerradas": len(st["historial"]),
                "por_canal": dict(Counter(x["canal"] for x in st["historial"])),
                "por_familia": dict(Counter(x["familia"] for x in st["historial"]))}, False
    item = seleccionar(datos, st, args.familia, args.canal, args.elegir)
    if item is None:
        return {"disponible": False, "mensaje": "Sin candidatos elegibles en este filtro"}, False
    # Idempotencia: el mismo item pendiente se devuelve sin reescribir el estado.
    if st["pendiente"]:
        return {"disponible": True, "tarea": st["pendiente"], "recuperada": True}, False
    payload = tarea(item)
    if args.siguiente or args.elegir:
        st["pendiente"] = payload
    return {"disponible": True, "tarea": payload,
            "reservada": bool(args.siguiente or args.elegir)}, bool(args.siguiente or args.elegir)


def main():
    parser = argparse.ArgumentParser(description="Rotador local, independiente de main y del QA-GPT")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--vista", action="store_true", help="simular sin cambiar estado")
    group.add_argument("--siguiente", action="store_true", help="reservar siguiente investigación")
    group.add_argument("--elegir", metavar="ID", help="reservar una idea concreta")
    group.add_argument("--resultado", choices=CIERRES, help="cerrar pendiente")
    group.add_argument("--liberar", action="store_true", help="liberar pendiente sin historia")
    group.add_argument("--reactivar", metavar="ID", help="hacer elegible una investigación cerrada")
    group.add_argument("--ver-estado", action="store_true", help="historial y reserva")
    parser.add_argument("--familia", help="acotar familia solo en vista/siguiente")
    parser.add_argument("--canal", choices=ORDEN_CANALES, help="acotar canal en vista/siguiente")
    parser.add_argument("--catalogo", type=Path, default=CATALOGO)
    parser.add_argument("--estado-archivo", type=Path, default=ubicacion_estado())
    args = parser.parse_args()
    try:
        result = ejecutar(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
