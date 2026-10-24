#!/usr/bin/env python3
"""Fuentes vivas para investigar mejoras. Las coincidencias NO equivalen a soluciones verificadas."""
import argparse, datetime as dt, hashlib, json, os, subprocess, sys, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GOOGLE_RSS = "https://developers.google.com/search/updates/search_docs_updates.rss"
GITHUB = "https://api.github.com/search/repositories"
# Ángulos recombinables: no se agotan ni representan propuestas precocinadas.
ANGULOS = {
  "github": ("static site", "accessibility", "content search", "performance", "book metadata", "publishing"),
  "api": ("books bibliographic", "library catalog", "cultural heritage", "open data", "events"),
  "sector": ("indie authors", "reader engagement", "open publishing", "digital books", "content discovery"),
}
CARPETAS = {"recomendaciones","cuaderno","herramientas","libros","universo","asistente","recursos","assets","scripts","atlas"}


class FuenteError(RuntimeError):
    pass


def hoy():
    return dt.datetime.now(dt.timezone.utc).date()


def stable(s):
    return int(hashlib.sha256(s.encode("utf-8")).hexdigest()[:10], 16)


def get_json(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "web-escritor-lab/1.0"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=15) as r:
        return json.load(r)


def get_rss(url):
    if url != GOOGLE_RSS:
        raise FuenteError("Fuente RSS fuera de permitidos")
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"web-escritor-lab/1.0"}),timeout=15) as r:
        return r.read(2_000_000)


def feed(raw):
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        raise FuenteError(f"Feed inválido: {e}") from e
    out = []
    for item in root.findall("./channel/item"):
        title = item.findtext("title", "").strip()
        url = item.findtext("link", "").strip()
        if not title or not url.startswith("https://developers.google.com/"):
            continue
        fecha = item.findtext("pubDate", "").strip()
        try:
            fecha = parsedate_to_datetime(fecha).date().isoformat()
        except (ValueError, TypeError, OverflowError):
            fecha = ""
        out.append({"titulo":title[:240], "url":url, "publicado":fecha, "origen":GOOGLE_RSS,
                    "tipo":"documentacion", "resumen":item.findtext("description","")[:1000]})
    return out


def github(canal, familia, epoca=0, fetch=get_json):
    semillas = ANGULOS[canal]
    term = semillas[(stable(familia) + epoca) % len(semillas)]
    filtro = {"github":"language:JavaScript", "api":"topic:api", "sector":"topic:website"}[canal]
    cutoff = (hoy() - dt.timedelta(days=365)).isoformat()
    q = f"{term} {filtro} stars:>20 pushed:>={cutoff} archived:false"
    url = GITHUB + "?" + urllib.parse.urlencode({"q":q,"sort":"updated","order":"desc","per_page":12})
    try:
        response = fetch(url)
    except (OSError, ValueError) as exc:
        raise FuenteError(f"GitHub REST: {type(exc).__name__} {str(exc)[:110]}") from exc
    if not isinstance(response, dict) or not isinstance(response.get("items"), list):
        raise FuenteError("GitHub REST no devolvió items")
    out = []
    for r in response["items"]:
        if r.get("fork") or r.get("archived") or not r.get("html_url","").startswith("https://github.com/"):
            continue
        if not r.get("pushed_at"):
            continue
        out.append({"titulo":r.get("full_name","")[:220], "url":r["html_url"], "publicado":r["pushed_at"][:10],
                    "origen":"GitHub REST search", "tipo":"repositorio" if canal!="api" else "api_candidata",
                    "resumen":(r.get("description") or "")[:700], "licencia_declarada":(r.get("license") or {}).get("spdx_id"),
                    "estrellas":r.get("stargazers_count"), "rama":r.get("default_branch")})
    return out


def local(root=ROOT, familia="general", epoca=0):
    try:
        res = subprocess.run(["git","-C",str(root),"ls-files"],capture_output=True,text=True,timeout=12)
        if res.returncode: return []
        folders = sorted({f.split("/")[0] for f in res.stdout.splitlines() if "/" in f and f.split("/")[0] in CARPETAS})
        if not folders: return []
        path = folders[(stable(familia)+epoca) % len(folders)]
        sha = subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],capture_output=True,text=True,timeout=8).stdout.strip()
    except (OSError,subprocess.TimeoutExpired):
        return []
    return [{"titulo":"Auditar capacidad real: "+path, "url":"local://"+path, "publicado":hoy().isoformat(),
             "origen":"git ls-files @ "+sha, "tipo":"codigo_existente",
             "resumen":"Comprobar código y pruebas actuales antes de plantear una mejora."}]


def descubrir(canal, familia, epoca=0, fetch_json=get_json, fetch_rss=get_rss, root=ROOT):
    if canal=="auditoria_local": return local(root,familia,epoca)
    if canal in ANGULOS: return github(canal,familia,epoca,fetch_json)
    if canal=="web":
        try: return feed(fetch_rss(GOOGLE_RSS))
        except (OSError,ValueError) as exc: raise FuenteError(f"Feed no disponible: {exc}") from exc
    raise FuenteError("Canal desconocido")


def huella(item):
    base=item["url"].lower().rstrip("/")+"|"+item.get("publicado","")
    if item["url"].startswith("local://"): base+="|"+item.get("origen","")
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]


def nuevas(fuentes, vistas=(), max_dias=365):
    usadas=set(vistas); out=[]
    for f in fuentes:
        if not f.get("url") or huella(f) in usadas: continue
        try: age=(hoy()-dt.date.fromisoformat(f.get("publicado",""))).days
        except ValueError: continue
        if not -1 <= age <= max_dias: continue
        out.append(f)
    return sorted(out,key=lambda x:(x["publicado"],x["url"]),reverse=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--canal", required=True, choices=("auditoria_local","github","web","api","sector"))
    p.add_argument("--familia",default="general")
    p.add_argument("--epoca",type=int,default=0)
    p.add_argument("--vistos",type=Path)
    p.add_argument("--guardar",type=Path)
    a=p.parse_args()
    try:
        vistos=json.loads(a.vistos.read_text(encoding="utf-8")) if a.vistos else []
        fuentes=descubrir(a.canal,a.familia,a.epoca)
        output={"canal":a.canal,"familia":a.familia,"consultado":dt.datetime.now(dt.timezone.utc).isoformat(),
                "recibidas":len(fuentes),"candidatas":nuevas(fuentes,vistos)[:10],
                "nota":"Resultados para investigar, no diagnósticos aprobados ni código validado"}
        txt=json.dumps(output,ensure_ascii=False,indent=2)
        if a.guardar:
            a.guardar.parent.mkdir(parents=True,exist_ok=True)
            a.guardar.write_text(txt+"\n",encoding="utf-8")
        print(txt)
        return 0
    except (FuenteError,ValueError,OSError) as err:
        print(json.dumps({"error":str(err),"no_hallazgo":True},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=="__main__": raise SystemExit(main())
