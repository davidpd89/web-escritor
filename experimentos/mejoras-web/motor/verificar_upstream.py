"""Confirma que el código original de GPT EXISTE en un blob real del repositorio upstream.
No ejecuta código externo; solo lee GitHub REST. Para SEO/documentación no se simula código upstream.
"""
import base64, json, os, re, urllib.parse, urllib.request
from pathlib import Path


class FuenteNoVerificada(ValueError):
    pass


def verificar(investigacion,fuente,fetch=None):
    url=fuente.get("url","")
    parsed=urllib.parse.urlparse(url)
    if parsed.netloc.lower()!="github.com":
        return {"tipo":"documentacion","upstream_verificado":False,
                "motivo":"El documento no es un repositorio; Claude debe comprobar autoridad y versión por separado."}
    parts=parsed.path.strip("/").split("/")
    if len(parts)<2 or not all(re.fullmatch(r"[A-Za-z0-9_.-]+",p) for p in parts[:2]):
        raise FuenteNoVerificada("URL GitHub sin owner/repo verificable")
    owner,repo=parts[:2]
    sha=investigacion.get("fuente_sha","").lower().strip()
    literal=investigacion.get("codigo_original","")
    if not re.fullmatch(r"[0-9a-f]{40}",sha):
        raise FuenteNoVerificada("Se exige SHA completo de blob GitHub de 40 hex")
    if not isinstance(literal,str) or len(literal.strip())<12:
        raise FuenteNoVerificada("Falta fragmento de código upstream literal")
    base=f"https://api.github.com/repos/{owner}/{repo}"
    def obtener(ruta):
        headers={"Accept":"application/vnd.github+json","User-Agent":"web-escritor-lab/1.0"}
        if os.environ.get("GH_TOKEN"): headers["Authorization"]="Bearer "+os.environ["GH_TOKEN"]
        try:
            if fetch is not None: return fetch(base+ruta)
            with urllib.request.urlopen(urllib.request.Request(base+ruta,headers=headers),timeout=18) as r:
                return json.load(r)
        except (ValueError,OSError) as exc:
            raise FuenteNoVerificada(f"GitHub API no verificable: {type(exc).__name__}: {str(exc)[:130]}") from exc
    blob=obtener("/git/blobs/"+sha)
    if blob.get("sha","").lower()!=sha or blob.get("encoding")!="base64":
        raise FuenteNoVerificada("Blob SHA distinto o sin datos")
    try: texto=base64.b64decode(blob["content"],validate=False).decode("utf-8")
    except (KeyError,ValueError,UnicodeError) as exc: raise FuenteNoVerificada("Blob ilegible") from exc
    if literal.strip() not in texto:
        raise FuenteNoVerificada("El código literal NO aparece en el blob aportado")
    licencia=obtener("/license")
    spdx=(licencia.get("license") or {}).get("spdx_id")
    indicada=str(investigacion.get("licencia","")).strip().upper().replace(" ","-")
    if not spdx or spdx in ("NOASSERTION","NONE"):
        raise FuenteNoVerificada("Licencia upstream no acreditada automáticamente")
    if indicada not in (spdx.upper(), spdx.upper().replace("-"," ")):
        raise FuenteNoVerificada(f"Licencia declarada {indicada} distinta a GitHub {spdx}")
    return {"tipo":"repositorio","upstream_verificado":True,"blob_sha":sha,
            "licencia":spdx,"repositorio":owner+"/"+repo,"bytes_fuente":len(texto.encode("utf-8")),
            "metodo":"GitHub REST git/blobs + /license, contenido literal presente"}
