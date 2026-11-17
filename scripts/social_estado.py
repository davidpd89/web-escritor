#!/usr/bin/env python3
"""R5-6: la instantánea de seguidores vive en la rama `social-estado`, no en main.

La tarea social del PC de David escribe en esa rama (sin reglas, mismo patrón que `catalogo-estado`) y main solo
recibe cambios por PR. El deploy de Pages construye desde main y aquí superpone en el artefacto la instantánea más
reciente que sea válida: la de la rama o, si falta o no valida, la copia de main. Caducada no se descarta si es la más
reciente: el panel ya muestra su caducidad y una más vieja sería peor.

Uso (deploy-pages.yml, tras construir y antes del contrato): python scripts/social_estado.py --out .preview-dist
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "research"))
import gpt_social_publish as pub  # noqa: E402

ORIGEN = datetime(1970, 1, 1, tzinfo=timezone.utc)  # la caducidad no descarta aquí; se compara entre copias


def leer_rama(root: Path = ROOT) -> str | None:
    """La instantánea de origin/social-estado, o None si la rama o el fichero no existen."""
    ref = f"refs/remotes/origin/{pub.BRANCH}"
    fetch = subprocess.run(["git", "-C", str(root), "fetch", "--quiet", "--depth=1", "origin",
                            f"+refs/heads/{pub.BRANCH}:{ref}"], capture_output=True, text=True)
    if fetch.returncode:
        print(f"AVISO social-estado: no se pudo traer la rama ({fetch.stderr.strip()[:200]})", flush=True)
        return None
    show = subprocess.run(["git", "-C", str(root), "show", f"{ref}:{pub.REL}"],
                          capture_output=True, text=True, encoding="utf-8")
    return show.stdout if show.returncode == 0 else None


def elegir(rama: str | None, main: str | None) -> tuple[str, str] | None:
    """(origen, texto) de la copia válida con `valid_until` más tardío; la rama gana el empate."""
    candidatas = []
    for prioridad, origen, texto in ((1, pub.BRANCH, rama), (0, "main", main)):
        if not texto:
            continue
        try:
            data = pub.validate(texto, ORIGEN)
        except pub.PublishError as exc:
            print(f"AVISO social-estado: la copia de {origen} no valida ({exc}); no se usa", flush=True)
            continue
        candidatas.append((pub._t(data["totals"]["valid_until"]), prioridad, origen, texto))
    if not candidatas:
        return None
    _, _, origen, texto = max(candidatas)
    return origen, texto


def superponer(out: Path, rama: str | None, root: Path = ROOT) -> str:
    principal = root / pub.REL
    eleccion = elegir(rama, principal.read_text(encoding="utf-8") if principal.exists() else None)
    if eleccion is None:
        return "ninguna"
    origen, texto = eleccion
    if origen == pub.BRANCH:
        destino = out / pub.REL
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8", newline="")
    return origen


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    print(f"Instantánea social publicada desde: {superponer(a.out, leer_rama())}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
