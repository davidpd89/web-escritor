"""Aplicación acotada de cambios propuestos por GPT, adaptada del patrón de qa_pr.py.
Origen: scripts/qa-gpt/qa_pr.py @ automation/qa-gpt (ruta_segura, validar_parche, verificadores).
Nada de ejecutar comandos redactados por GPT. La PR siempre apunta a la rama lab.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = "davidpd89/web-escritor"
BASE = "lab/mejoras-web-20261024"
PROHIBIDO = re.compile(r"(^|/)(\.github|\.git|node_modules|scripts/qa-gpt|experimentos/mejoras-web|\.ci)(/|$)|(^|/)(package(-lock)?\.json|wrangler[\w.-]*|\.env[\w.]*|\.dev\.vars)$|secret|credential|stripe|paypal|(^|[/_.-])pagos?([/_.-]|$)", re.I)
SECRETO = re.compile(r"sk_(live|test)_\w+|AKIA[0-9A-Z]{12,}|ghp_\w{20,}|(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{8,}", re.I)
MAX_FICHEROS=5
MAX_REEMPLAZOS=8
MAX_BYTES=50000


class PreparacionError(RuntimeError):
    pass


def ruta_segura(ruta):
    if not isinstance(ruta,str) or not ruta or ruta.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:",ruta):
        return False
    path=ruta.replace("\\","/")
    if "\\" in ruta or "//" in ruta or ".." in path.split("/") or any(p in ("", ".") for p in path.split("/")):
        return False
    if PROHIBIDO.search(path) or not re.fullmatch(r"[\w./-]+\.(?:py|mjs|js|css|html|json|txt|md)",path):
        return False
    return True


def comprobar_parche(parche, raiz):
    """Solo JSON con reemplazos exactos o ficheros nuevos. No se ejecuta código."""
    if not isinstance(parche,dict) or not isinstance(parche.get("ficheros"),list):
        raise PreparacionError("Falta lista ficheros")
    files=parche["ficheros"]
    if not 1<=len(files)<=MAX_FICHEROS: raise PreparacionError("Máximo 5 ficheros por PR")
    vistos=set()
    for f in files:
        ruta=f.get("ruta") if isinstance(f,dict) else None
        if not ruta_segura(ruta) or ruta in vistos: raise PreparacionError(f"Ruta duplicada o bloqueada: {ruta}")
        vistos.add(ruta)
        dest=Path(raiz)/ruta
        if not dest.resolve().is_relative_to(Path(raiz).resolve()): raise PreparacionError("Ruta sale del worktree")
        if f.get("crear") is True:
            texto=f.get("contenido")
            if dest.exists() or not isinstance(texto,str) or not texto.strip() or len(texto.encode("utf-8"))>MAX_BYTES:
                raise PreparacionError(f"Creación inválida: {ruta}")
            if SECRETO.search(texto): raise PreparacionError("Posible secreto detectado")
            continue
        if not dest.is_file() or dest.is_symlink(): raise PreparacionError(f"No existe archivo: {ruta}")
        texto=dest.read_text(encoding="utf-8")
        repl=f.get("reemplazos")
        if not isinstance(repl,list) or not 1<=len(repl)<=MAX_REEMPLAZOS:
            raise PreparacionError(f"Reemplazos inválidos: {ruta}")
        for change in repl:
            antes=change.get("buscar") if isinstance(change,dict) else None
            despues=change.get("por") if isinstance(change,dict) else None
            if not isinstance(antes,str) or not antes or not isinstance(despues,str) or antes==despues:
                raise PreparacionError("Reemplazo inválido")
            if SECRETO.search(despues) or texto.count(antes)!=1: raise PreparacionError("Reemplazo ambiguo/secreto")
            texto=texto.replace(antes,despues,1)
    return [x["ruta"] for x in files]


def aplicar_parche(parche,raiz):
    tocados=comprobar_parche(parche,raiz)
    for item in parche["ficheros"]:
        destino=Path(raiz)/item["ruta"]
        if item.get("crear") is True:
            destino.parent.mkdir(parents=True,exist_ok=True)
            destino.write_text(item["contenido"],encoding="utf-8",newline="")
        else:
            texto=destino.read_text(encoding="utf-8")
            for r in item["reemplazos"]:
                texto=texto.replace(r["buscar"],r["por"],1)
            destino.write_text(texto,encoding="utf-8",newline="")
    return tocados


def comandos_test(parche):
    """No permite argumentos arbitrarios/shell. Un test propio o preexistente obligatorio."""
    checks=parche.get("tests",[])
    if not isinstance(checks,list) or not checks: raise PreparacionError("La propuesta no incluye tests")
    out=[]
    for t in checks:
        if not isinstance(t,str) or not re.fullmatch(r"(tests|qa)/[\w./-]+\.(py|mjs|js)",t) or ".." in Path(t).parts:
            raise PreparacionError(f"Ruta test inválida: {t!r}")
        out.append(["python" if t.endswith(".py") else "node",t])
    return out


def run(args,cwd,timeout=240,extra_env=None):
    try:
        r=subprocess.run(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,
                         encoding="utf-8",errors="replace",timeout=timeout,env={**os.environ,**(extra_env or {}),
                         "GIT_TERMINAL_PROMPT":"0","GH_PROMPT_DISABLED":"1"})
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise PreparacionError(f"Proceso no ejecutable/timeout: {args[0]}: {exc}") from exc
    if r.returncode:
        raise PreparacionError(f"Error (exit {r.returncode}) {args[:3]}: {r.stdout[-1300:]}")
    return r.stdout.strip()


def _node_test(wt,cmd):
    """Reuso del contrato QA Pr._test: servidor del worktree + dependencia fijada."""
    import socket, time
    dest=wt/"node_modules"
    src=Path(__file__).resolve().parents[3]/"node_modules"
    if not dest.exists():
        if src.exists():
            if os.name=="nt":
                run(["cmd","/c","mklink","/J",str(dest),str(src)],wt,timeout=30)
            else:
                dest.symlink_to(src,target_is_directory=True)
        else:
            run(["npm","ci"],wt,timeout=240)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0)); port=sock.getsockname()[1]
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(port),
         "--bind","127.0.0.1","-d",str(wt)],cwd=wt,
         stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        if srv.poll() is not None: raise PreparacionError("Servidor Playwright no arranco")
        return run(cmd,wt,timeout=300,extra_env={"QA_ORIGIN":f"http://127.0.0.1:{port}"})
    finally:
        srv.terminate()
        try: srv.wait(timeout=10)
        except subprocess.TimeoutExpired: srv.kill()


def ejecutar_tests(worktree,patch):
    logs=[]
    for test in comandos_test(patch):
        if not (worktree/test[1]).is_file(): raise PreparacionError(f"Test no existe: {test[1]}")
        output=run(test,worktree,timeout=300) if test[0]=="python" else _node_test(worktree,test)
        logs.append((test[1],output[-800:]))
    tocados=[f["ruta"] for f in patch["ficheros"]]
    if any(f.endswith(".html") for f in tocados):
        for check in ("scripts/check-hrefs.py","scripts/check-heading-structure.py"):
            if (worktree/check).exists():
                logs.append((check,run(["python",check],worktree,timeout=300)[-800:]))
    return logs


def validar_contexto(root):
    rama=run(["git","branch","--show-current"],root)
    if not rama.startswith(("lab/mejoras-","research/mejoras-","feature/mejoras-")):
        raise PreparacionError(f"No se opera desde esta rama: {rama}")
    run(["git","diff","--quiet"],root)
    run(["git","diff","--cached","--quiet"],root)
    run(["git","fetch","origin",BASE],root,timeout=180)
    return rama



def verificar_divergencia(root,parche):
    """No aplicar sobre lab un fichero modificado también en main desde la base común."""
    run(["git","fetch","origin","main"],root,timeout=180)
    origen=run(["git","merge-base","origin/"+BASE,"origin/main"],root)
    cambiados=set(run(["git","diff","--name-only",origen,"origin/main"],root).splitlines())
    propuestos={item["ruta"] for item in parche["ficheros"]}
    colisiones=sorted(cambiados & propuestos)
    if colisiones:
        raise PreparacionError("Lab está desactualizada respecto de main para: "+
                               ", ".join(colisiones[:8])+". Actualizar lab y revalidar.")
    return len(cambiados)


def identificador(expediente):
    raw=(str(expediente.get("id"))+"|"+str(expediente.get("fuente",{}).get("url",""))).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:12]


def abrir_pr(root,estado_dir,expediente,parche,publicar=False):
    """Prepara worktree temporal y prueba. Con publicar=True hace push + PR draft; jamás merge."""
    root=Path(root).resolve()
    if not root.is_dir(): raise PreparacionError("Falta repositorio")
    validar_contexto(root)
    if expediente.get("veredicto")!="aprobar":
        raise PreparacionError("Sin aprobación previa de Claude")
    tag=identificador(expediente)
    rama=f"feature/mejoras-web/{tag}"
    wt=Path(estado_dir).resolve()/"worktrees"/tag
    if wt.exists():
        if not publicar:
            raise PreparacionError(f"Worktree existente, no se duplica: {wt}")
        # Si GitHub aceptó la PR antes del corte, vincularla sin reenviar.
        listado=run(["gh","pr","list","-R",REPO,"--state","open","--head",rama,
                     "--json","url,baseRefName,headRefOid"],root)
        correctas=[x for x in json.loads(listado) if x.get("baseRefName")==BASE]
        if correctas:
            return {"rama":rama,"worktree":str(wt),"estado":"pr_existente","tests":[],
                    "pr":correctas[0]["url"],"nota":"PR ya creada"}
        # Si se cortó entre commit/push y PR, continuar únicamente con un commit
        # propio y limpio sobre lab. Un parche sin commit exige inspección humana.
        if run(["git","branch","--show-current"],wt)!=rama:
            raise PreparacionError("Worktree reutilizado en rama incorrecta")
        if run(["git","status","--porcelain","--untracked-files=all"],wt):
            raise PreparacionError("Recuperación insegura: cambios sin commit")
        if run(["git","rev-list","--count","origin/"+BASE+"..HEAD"],wt)!="1":
            raise PreparacionError("Recuperación requiere exactamente un commit hijo de lab")
        esperadas={x["ruta"] for x in parche.get("ficheros",[])}
        cambiadas=set(run(["git","diff","--name-only","origin/"+BASE+"...HEAD"],wt).splitlines())
        if cambiadas!=esperadas:
            raise PreparacionError("Archivos del commit distintos de la propuesta validada")
        logs=ejecutar_tests(wt,parche)
        run(["git","push","origin","HEAD:refs/heads/"+rama],wt,timeout=180)
        titulo=f"feat(lab): {str(expediente.get('titulo') or expediente.get('id'))[:60]}"
        body=(f"Recuperada tras interrupción. Base {BASE}. Sin merge automático.\n"
              f"Expediente: {expediente.get('id')}\n"
              f"Fuente: {expediente.get('fuente',{}).get('url')}\n"
              f"Tests reejecutados: {json.dumps(logs,ensure_ascii=False)}")
        url=run(["gh","pr","create","-R",REPO,"--base",BASE,"--head",rama,
                 "--draft","--title",titulo,"--body",body],wt,timeout=120)
        return {"rama":rama,"worktree":str(wt),"estado":"pr_borrador",
                "archivos":sorted(esperadas),"tests":logs,"pr":url}
    # Las ramas divergen. No mezclar silenciosamente cambios obsoletos.
    verificar_divergencia(root,parche)
    wt.parent.mkdir(parents=True,exist_ok=True)
    # Comprobación previa de tests sin ejecutar los cambios.
    comandos_test(parche)
    run(["git","worktree","add","-b",rama,str(wt),"origin/"+BASE],root,timeout=120)
    try:
        tocados=aplicar_parche(parche,wt)
        logs=ejecutar_tests(wt,parche)
        # Evitar que generación de tests u otros procesos modifique archivos imprevistos.
        changed=run(["git","status","--porcelain","--untracked-files=all"],wt)
        extras=[]
        for line in changed.splitlines():
            path=line[3:].strip().strip('"')
            if path and path not in tocados: extras.append(path)
        if extras: raise PreparacionError(f"Archivos fuera de alcance: {extras[:10]}")
        run(["git","add","--",*tocados],wt)
        if not run(["git","diff","--cached","--name-only"],wt): raise PreparacionError("Parche vacío")
        titulo=f"feat(lab): {str(expediente.get('titulo') or expediente.get('id'))[:60]}"
        body=(f"Laboratorio aislado; base {BASE}. NO MERGEAR a main.\n\n"
              f"Expediente: {expediente.get('id')}\n"
              f"Fuente: {expediente.get('fuente',{}).get('url')}\n"
              f"Revisión Claude: aprobar. Tests locales: {json.dumps(logs,ensure_ascii=False)}\n"
              f"Validar CI, cambios visuales y decisión humana antes de integrar.")
        if not publicar:
            return {"rama":rama,"worktree":str(wt),"archivos":tocados,"tests":logs,"estado":"validado_local","pr":None}
        # Ninguna modificación remota si falta github CLI o los tests no pasan.
        run(["git","-c","user.name=lab-mejoras","-c","user.email=lab-mejoras@users.noreply.github.com",
             "commit","-m",titulo],wt)
        previa=run(["gh","pr","list","-R",REPO,"--state","open","--head",rama,"--json","url"],wt)
        prs=json.loads(previa)
        if prs:
            return {"rama":rama,"worktree":str(wt),"tests":logs,"estado":"pr_existente","pr":prs[0]["url"]}
        run(["git","push","origin","HEAD:refs/heads/"+rama],wt,timeout=180)
        url=run(["gh","pr","create","-R",REPO,"--base",BASE,"--head",rama,
                 "--draft","--title",titulo,"--body",body],wt,timeout=120)
        return {"rama":rama,"worktree":str(wt),"archivos":tocados,"tests":logs,"estado":"pr_borrador","pr":url}
    except Exception:
        # Mantiene el worktree para inspección y recuperación; nunca un borrado automático.
        raise
