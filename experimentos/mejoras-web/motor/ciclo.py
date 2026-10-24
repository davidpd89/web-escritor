#!/usr/bin/env python3
"""Director de mejoras: descubrimiento vivo -> GPT -> Claude -> parche -> PR de laboratorio.
Base real: qa_gpt.py/qa_claude.py/qa_pr.py de automation/qa-gpt.
Estado independiente fuera de Git. Nunca fusiona PRs ni despliega.
"""
import argparse, datetime as dt, hashlib, json, os, sqlite3, subprocess, sys, time
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
ROOT=HERE.parents[1]
sys.path[:0]=[str(HERE),str(Path(__file__).parent)]
import rotacion, descubrimiento, claude_cli, gpt_browser, pr_laboratorio, verificar_upstream

FINAL={"sin_fuente","rechazada","pendiente_revision","pr_borrador","validado_local"}
CLAUDE_SCHEMA={"type":"object","required":["decision","motivo","criterio_aceptacion","riesgo"],
 "properties":{"decision":{"type":"string","enum":["aprobar","rechazar","investigar_mas"]},
 "motivo":{"type":"string","minLength":30},"criterio_aceptacion":{"type":"string","minLength":15},
 "riesgo":{"type":"string","enum":["bajo","medio","alto"]},"duplicado":{"type":"boolean"}}}
GPT_KEYS=("problema","baseline","novedad","fuente_url","fuente_sha","licencia",
          "codigo_original","propuesta","alternativa_a","alternativa_b","pruebas","riesgos")


def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def carpeta_estado(): return rotacion.ubicacion_estado().parent/"ciclo"
def leer(path,default): return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def guardar(path, obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(".tmp")
    with temp.open("x",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2)
        f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(temp,path)


def anotar(s,evento):
    s.setdefault("eventos",[]).append({"fecha":utc(),"evento":evento})
    s["actualizado"]=utc()


def comando_rotacion(carpeta,*args):
    p=subprocess.run([sys.executable,str(HERE/"rotacion.py"),"--estado-archivo",str(carpeta/"rotacion.json"),*args],
                     capture_output=True,text=True,encoding="utf-8",timeout=20)
    if p.returncode: raise RuntimeError("Rotacion: "+p.stderr[-500:])
    return json.loads(p.stdout)


def reservar(carpeta):
    res=comando_rotacion(carpeta,"--siguiente")
    if res.get("disponible"): return res["tarea"],"catalogo"
    # El catalogo es solo una semilla. Tras agotarse, se repite la exploracion
    # sobre familias y canales; la novedad se decide por las fuentes reales.
    historico=leer(carpeta/"historial.json",[])
    n=len(historico)
    fam=sorted({x["familia"] for x in rotacion.catalogo()["ideas"]})
    canal=rotacion.ORDEN_CANALES[n%len(rotacion.ORDEN_CANALES)]
    familia=fam[(n//len(rotacion.ORDEN_CANALES))%len(fam)]
    return {"id":f"SONDEO-{n+1:07d}","titulo":f"Descubrir novedades de {familia}",
            "familia":familia,"canal":canal,
            "hipotesis":"Encontrar una mejora reciente y demostrablemente aplicable al sitio",
            "antiduplicacion":"Verificar fuentes, PR abiertas e historial previo",
            "criterio_medicion":"Definir y comprobar antes/despues"}, "sondeo"


def empezar(d):
    task,tipo=reservar(d)
    return {"id":task["id"],"tarea":task,"tipo":tipo,"fase":"seleccionado","chats":{},
            "creado":utc(),"eventos":[],"errores":0}


def cerrar(s,d):
    hist=leer(d/"historial.json",[])
    if any(x["id"]==s["id"] for x in hist): return
    if s["tipo"]=="catalogo":
        estado={"sin_fuente":"sin_evidencia","rechazada":"descartada",
                "pendiente_revision":"pendiente_revision"}.get(s["fase"],"investigada")
        comando_rotacion(d,"--resultado",estado)
    hist.append({"id":s["id"],"fase":s["fase"],"fecha":utc(),
                 "familia":s["tarea"]["familia"],"canal":s["tarea"]["canal"]})
    guardar(d/"historial.json",hist)
    if s.get("fuente") and s["fase"]!="sin_fuente":
        vistos=leer(d/"vistos.json",[])
        huella=descubrimiento.huella(s["fuente"])
        if huella not in vistos: guardar(d/"vistos.json",vistos+[huella])


def json_respuesta(raw):
    texto=raw.strip()
    if texto.startswith(chr(96)*3):
        texto="\n".join(texto.splitlines()[1:-1])
    return json.loads(texto)


def validar_investigacion(data,fuente):
    if not isinstance(data,dict): raise ValueError("Investigacion no es JSON objeto")
    for campo in GPT_KEYS:
        if not isinstance(data.get(campo),str) or len(data[campo].strip())<10:
            raise ValueError("Investigacion sin evidencia: "+campo)
    if data["fuente_url"].rstrip("/")!=fuente["url"].rstrip("/"):
        raise ValueError("Fuente inventada o distinta de la consultada")
    if data["fuente_sha"].lower() in ("desconocido","sin_verificar","no aplica","ninguno"):
        raise ValueError("No se identifica versión/commit")
    return data


def llamar_gpt(s,d,etapa,prompt):
    def on_chat(cid):
        s["chats"][etapa]=cid
        guardar(d/"actual.json",s)
    res=gpt_browser.ask(prompt,wait_min=25,stall_min=12,on_chat=on_chat,
                        resume_cid=s["chats"].get(etapa))
    return json_respuesta(res.texto)


class ConfigClaude:
    def __init__(self,d):
        self.STATE=d
        self.CFG={"claude":{"max_usd_llamada":0.5,"max_turnos":2,"esfuerzo":"low"}}
    @staticmethod
    def now(): return utc()


def revisar(s,d,simular):
    if simular:
        return {"decision":"investigar_mas","motivo":"Prueba simulada sin contrastar repositorio completo ni comportamiento.",
                "criterio_aceptacion":"Exigir evidencias reales","riesgo":"medio","duplicado":False}
    c=sqlite3.connect(d/"claude.sqlite3")
    try:
        claude_cli.migrar(c)
        sistema=(HERE/"contratos/CLAUDE-REVISAR.md").read_text(encoding="utf-8")
        entrada=json.dumps({"investigacion":s["investigacion"],"fuente":s["fuente"],
                            "tarea":s["tarea"],"verificacion_upstream":s.get("verificacion_upstream")},ensure_ascii=False)
        return claude_cli.llamar(ConfigClaude(d),c,s["id"],"revision",sistema,entrada,
                                  CLAUDE_SCHEMA,herramientas="Read,Grep,Glob",cwd=ROOT)[0]
    finally: c.close()


def prompt_investigar(s):
    instrucciones=(HERE/"contratos/GPT-INVESTIGAR.md").read_text(encoding="utf-8")
    return (instrucciones+"\nTrabaja a fondo UN tema, lee fuentes primarias y codigo existente. "
            "Si no hay mejora demostrable, concluyelo. Solo JSON con estas claves: "+
            ", ".join(GPT_KEYS)+". codigo_original debe ser un fragmento upstream literal, "
            "fuente_sha su commit/tag real, licencia comprobada; NO inventar.\n"+
            json.dumps({"tarea":s["tarea"],"fuente":s["fuente"]},ensure_ascii=False))


def prompt_desarrollar(s):
    return ("Implementa solo la mejora revisada, conservando identidad editorial. "
            "Solo JSON: ficheros=[{ruta,crear:true,contenido} o {ruta,reemplazos:[{buscar,por}]}], "
            "tests=[rutas de tests/ o qa/ ejecutables]. Maximo 5 archivos, sin comandos arbitrarios. "
            "Incluye pruebas nuevas o existentes, preserva licencia upstream. "
            "No toques main, workflow, pagos ni credenciales.\n"+
            json.dumps({"investigacion":s["investigacion"],"revision":s["revision"]},ensure_ascii=False))


def paso(d,simular=False,publicar=False):
    d.mkdir(parents=True,exist_ok=True)
    path=d/"actual.json"
    s=leer(path,None)
    if s is not None and s["fase"] in FINAL: cerrar(s,d)
    if s is None or s["fase"] in FINAL:
        s=empezar(d); guardar(path,s); return s
    try:
        etapa=s["fase"]
        if etapa=="seleccionado":
            if simular:
                src=[{"titulo":"fixture","url":"https://github.com/Pagefind/pagefind",
                      "publicado":descubrimiento.hoy().isoformat(),"origen":"fixture"}]
            else:
                src=descubrimiento.descubrir(s["tarea"]["canal"],s["tarea"]["familia"],
                                            len(leer(d/"historial.json",[])))
            nuevas=descubrimiento.nuevas(src,leer(d/"vistos.json",[]))
            if nuevas: s["fuente"]=nuevas[0]; s["fase"]="fuente"
            else: s["fase"]="sin_fuente"
        elif etapa=="fuente":
            if simular:
                s["investigacion"]={k:"Dato simulado para probar estado, NO es fuente verificable" for k in GPT_KEYS}
                s["investigacion"]["fuente_url"]=s["fuente"]["url"]
            else:
                s["investigacion"]=validar_investigacion(llamar_gpt(s,d,"investigacion",prompt_investigar(s)),s["fuente"])
                s["verificacion_upstream"]=verificar_upstream.verificar(s["investigacion"],s["fuente"])
            s["fase"]="gpt_completo"
        elif etapa=="gpt_completo":
            s["revision"]=revisar(s,d,simular)
            s["fase"]={"aprobar":"aprobado","rechazar":"rechazada",
                       "investigar_mas":"pendiente_revision"}[s["revision"]["decision"]]
        elif etapa=="aprobado":
            if simular: raise RuntimeError("Simulacion no publica código")
            s["parche"]=llamar_gpt(s,d,"parche",prompt_desarrollar(s))
            pr_laboratorio.comandos_test(s["parche"])
            s["fase"]="parche_listo"
        elif etapa=="parche_listo":
            if simular: raise RuntimeError("Simulacion no prepara PR")
            exped={"id":s["id"],"titulo":s["tarea"]["titulo"],"fuente":s["fuente"],
                   "veredicto":s["revision"]["decision"]}
            s["validacion"]=pr_laboratorio.abrir_pr(ROOT,d,exped,s["parche"],publicar)
            s["fase"]="pr_borrador" if s["validacion"]["pr"] else "validado_local"
        else: raise RuntimeError("Fase no reconocida: "+etapa)
        anotar(s,"Completada etapa "+etapa)
        guardar(path,s)
        if s["fase"] in FINAL: cerrar(s,d)
        return s
    except Exception as exc:
        s["errores"]=s.get("errores",0)+1
        s["error"]=f"{type(exc).__name__}: {str(exc)[:450]}"
        anotar(s,"Error recuperable en "+s["fase"])
        guardar(path,s)
        raise


def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--paso",action="store_true")
    g.add_argument("--continuo",action="store_true")
    g.add_argument("--simular",action="store_true")
    g.add_argument("--estado",action="store_true")
    p.add_argument("--publicar-pr",action="store_true",help="Solo PR draft con base lab; nunca merge")
    p.add_argument("--estado-dir",type=Path,default=carpeta_estado())
    a=p.parse_args()
    if a.estado:
        print(json.dumps(leer(a.estado_dir/"actual.json",{"fase":"sin_iniciar"}),ensure_ascii=False,indent=2))
        return 0
    try:
        if a.simular:
            d=a.estado_dir/"simulacion"
            for _ in range(3): s=paso(d,True)
            print(json.dumps({"id":s["id"],"fase":s["fase"],"simulada":True},ensure_ascii=False))
        elif a.paso:
            s=paso(a.estado_dir,publicar=a.publicar_pr)
            print(json.dumps({"id":s["id"],"fase":s["fase"],"pr":s.get("validacion",{}).get("pr")},ensure_ascii=False))
        else:
            while True:
                s=paso(a.estado_dir,publicar=a.publicar_pr)
                print(f"{utc()} {s['id']} {s['fase']}",flush=True)
                time.sleep(180 if s["fase"]=="sin_fuente" else 2)
        return 0
    except KeyboardInterrupt:
        print("Parada controlada. Estado guardado para reanudar."); return 130
    except Exception as exc:
        print(f"ERROR: {exc}",file=sys.stderr); return 2


if __name__=="__main__": raise SystemExit(main())
