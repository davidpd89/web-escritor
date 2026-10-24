"""Consulta a ChatGPT (Project de QA) por el Edge dedicado 9230. Un chat NUEVO por peticion, una peticion a la vez.

Fin de generacion y texto de la respuesta: se leen del BACKEND de la conversacion (/backend-api/conversation/<id>),
no del DOM (los selectores del visor cambian y el visor colapsa el texto: causa del fallo "Thought for 4m" sin respuesta).
No teclea contrasenas: si la sesion esta cerrada lanza LoginRequired.
"""
import os, re, time
from dataclasses import dataclass

PORT = 9230
PROJECT_ID = "g-p-6adb128351e481919fef7901e111d1ac"
PROJECT_URL = f"https://chatgpt.com/g/{PROJECT_ID}/project"
STOP = 'button[data-testid="stop-button"], button[aria-label*="Detener"], button[aria-label*="Stop"]'
SEND = 'button[data-testid="send-button"], button[type="submit"][aria-label="Enviar"], button[type="submit"][aria-label*="Send"]'
SECRETS = re.compile(r"(^\.env|token|secret|credential|password|\.pem$|\.key$)", re.I)
TOKEN_RE = re.compile(r"(EAA[A-Za-z0-9]{25,}|Bearer\s+[A-Za-z0-9_\-]{25,}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,})")
LIMIT_RE = re.compile(r"(too many requests|has alcanzado el l[ií]mite|you.ve reached|l[ií]mite de uso|rate limit|vuelve a intentarlo m[aá]s tarde)", re.I)
CID_RE = re.compile(r"/c/([0-9a-f-]{20,})")
ERROR_CARGA_RE = re.compile(r"(no se ha podido cargar esta conversaci[oó]n|unable to load conversation|couldn.t load (this|the) conversation|conversation not found|no se encontr[oó] la conversaci[oó]n)", re.I)
RECARGAS = 2  # recargas tras el error visible, antes de decidir si la conversacion existe
PARADA = None  # callable -> True cuando hay que abandonar la espera (parada pedida y gracia vencida); la conversacion queda reanudable


class LoginRequired(RuntimeError):
    pass


class RateLimited(RuntimeError):
    pass


class ChatInaccesible(RuntimeError):
    """La conversacion no carga tras las recargas. `perdida`=True solo si el backend confirma que NO existe (404/410);
    con red caida o 5xx es incierta: no se abre otro chat (podria haber respondido)."""
    def __init__(self, msg, cid=None, perdida=False):
        super().__init__(msg)
        self.cid, self.perdida = cid, perdida


class Incompleta(RuntimeError):
    """Generacion sin terminar o sin salida valida; `cid` permite reanudar sin reenviar."""
    def __init__(self, msg, cid=None, estado="incompleta"):
        super().__init__(msg)
        self.cid, self.estado = cid, estado


@dataclass
class Resultado:
    estado: str          # terminada | vacia | generando | sin_respuesta
    texto: str
    cid: str
    herramientas: int    # mensajes de herramienta (lecturas del conector GitHub) = evidencia de que leyo el repo
    nodos: int


_BACKEND_JS = """async (cid) => {
  const s = await (await fetch('/api/auth/session', {credentials: 'include'})).json();
  if (!s.accessToken) return {http: 401};
  const r = await fetch('/backend-api/conversation/' + cid, {headers: {Authorization: 'Bearer ' + s.accessToken}, credentials: 'include'});
  if (!r.ok) return {http: r.status};
  return await r.json();
}"""


def refuse_secrets(paths):
    for p in paths:
        if SECRETS.search(os.path.basename(p)):
            raise ValueError(f"no se adjunta {p}: nombre sospechoso")
        with open(p, encoding="utf-8", errors="replace") as f:
            if TOKEN_RE.search(f.read(400000)):
                raise ValueError(f"{p}: contiene algo con forma de token")


def evaluar(d, after_user=True):
    """Clasifica una conversacion (JSON del backend) -> Resultado parcial (estado, texto, herramientas, nodos). Puro: testeable sin navegador."""
    mp = d.get("mapping") or {}
    chain, node = [], d.get("current_node")
    while node and node in mp:
        chain.append(mp[node]); node = mp[node].get("parent")
    chain.reverse()
    msgs = [n["message"] for n in chain if n.get("message")]
    herr = sum(1 for m in msgs if m["author"]["role"] == "tool")
    last_user = max((i for i, m in enumerate(msgs) if m["author"]["role"] == "user"), default=-1)
    tail = msgs[last_user + 1:]
    finals = [m for m in tail if m["author"]["role"] == "assistant" and (m.get("content") or {}).get("content_type") == "text"]
    if any(m.get("status") == "in_progress" for m in tail):
        return "generando", "", herr, len(mp)
    if finals and finals[-1].get("end_turn") is True and finals[-1].get("status") == "finished_successfully":
        t = "".join(x for x in finals[-1]["content"].get("parts", []) if isinstance(x, str)).strip()
        return ("terminada" if t else "vacia"), t, herr, len(mp)
    if finals and finals[-1].get("end_turn") is True:  # termino con error/parcial: no es exito ni vacia
        return "fallida", "", herr, len(mp)
    if finals and finals[-1].get("end_turn") is False:
        return "generando", "", herr, len(mp)
    return ("generando" if tail or last_user >= 0 else "sin_respuesta"), "", herr, len(mp)


def leer_chat(pg, cid):
    """Resultado actual de un chat por su id. pg: cualquier pagina de chatgpt.com."""
    d = pg.evaluate(_BACKEND_JS, cid)
    if isinstance(d, dict) and d.get("http") in (401, 403):
        raise LoginRequired("sesion de ChatGPT caducada o sin acceso (http %s)" % d["http"])
    if not isinstance(d, dict) or "mapping" not in d:
        raise Incompleta(f"backend sin conversacion (http {d.get('http') if isinstance(d, dict) else '?'})", cid, "backend")
    est, texto, herr, nodos = evaluar(d)
    return Resultado(est, texto, cid, herr, nodos)


def error_carga_visible(pg):
    """Pagina de error de ChatGPT ('No se ha podido cargar esta conversacion. Intentarlo de nuevo')."""
    try: return bool(ERROR_CARGA_RE.search(pg.evaluate("document.body ? document.body.innerText : ''") or ""))
    except Exception: return False


def conversacion_en_dom(pg):
    try: return pg.locator("[data-message-author-role]").count() > 0
    except Exception: return False


def abrir_chat(pg, cid, recargas=None):
    """Abre un chat existente y COMPRUEBA por DOM/backend que cargo. Recarga de forma acotada si hay error visible o la
    navegacion falla. Lanza LoginRequired (sin eludir nada) o ChatInaccesible. Devuelve el Resultado actual del backend si lo hubo."""
    recargas = RECARGAS if recargas is None else recargas
    url, motivo, http = f"https://chatgpt.com/g/{PROJECT_ID}/c/{cid}", "", None
    for i in range(recargas + 1):
        try:
            if i == 0: pg.goto(url, wait_until="domcontentloaded", timeout=40000)
            else: pg.reload(wait_until="domcontentloaded", timeout=40000)
            pg.wait_for_timeout(2500)
        except Exception as e:
            motivo = f"navegacion fallida: {str(e)[:80]}"; continue
        comprobar_sesion(pg, necesita_editor=False)
        if error_carga_visible(pg): motivo = "error de carga visible"
        elif not conversacion_en_dom(pg): motivo = "pagina sin conversacion"
        else: motivo = ""
        try:
            r = leer_chat(pg, cid)  # el backend manda: si responde, el visor es irrelevante
            return r
        except Incompleta as e:
            m = re.search(r"http (\d+)", str(e)); http = int(m.group(1)) if m else None
            motivo = motivo or str(e)
        except LoginRequired: raise
        except Exception as e:
            http, motivo = None, f"backend no alcanzable: {str(e)[:80]}"
    raise ChatInaccesible(f"conversacion {cid[:8]} inaccesible tras {recargas} recargas: {motivo}", cid, perdida=http in (404, 410))


def estado_chat_seguro(pg, cid):
    try:
        return leer_chat(pg, cid).estado
    except Exception:
        return "desconocido"


def limpiar_pestanas(ctx, conservar=(), guardados=()):
    """Cierra pestanas de chats TERMINADOS (o cuyo resultado ya esta guardado) y duplicadas del Project.
    Nunca cierra un chat en generacion ni uno cuyo id esta en `conservar`. Devuelve nº cerradas."""
    gpt = [x for x in ctx.pages if "chatgpt.com" in x.url]
    cerradas, proj = 0, 0
    for x in gpt:
        m = CID_RE.search(x.url)
        try:
            if m:
                cid = m.group(1)
                if cid in conservar: continue
                if cid in guardados or estado_chat_seguro(x, cid) in ("terminada", "vacia"):
                    x.close(); cerradas += 1
            else:
                proj += 1
                if proj > 1: x.close(); cerradas += 1
        except Exception:
            pass
    return cerradas


def _conectar(p):
    browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}", timeout=30000)
    return browser, browser.contexts[0]


def _pagina_chatgpt(ctx):
    for x in ctx.pages:
        if "chatgpt.com" in x.url: return x, False
    pg = ctx.new_page(); pg.goto(PROJECT_URL, wait_until="domcontentloaded", timeout=40000); pg.wait_for_timeout(3000)
    return pg, True


def comprobar_sesion(pg, necesita_editor=True):
    if "auth" in pg.url or "login" in pg.url or (necesita_editor and pg.locator('[contenteditable="true"]').count() == 0):
        raise LoginRequired("ChatGPT sin sesion en el Edge 9230")


def _esperar(pg, cid, wait_min, stall_min, progreso=None):
    """Sondea el backend hasta 'terminada'/'vacia'. Sin esperas fijas: solo intervalo de sondeo."""
    deadline = time.monotonic() + wait_min * 60
    visto, ultimo_cambio = (-1, ""), time.monotonic()
    fallos_seguidos = 0
    while time.monotonic() < deadline:
        try:
            r = leer_chat(pg, cid)
        except Incompleta as e:
            if e.estado == "backend" and re.search(r"http (429|5\d\d)", str(e)):  # transitorio: espaciar el sondeo, no abandonar
                espera = min(240, 30 * 2 ** fallos_seguidos); fallos_seguidos += 1
                if fallos_seguidos > 6: raise
                pg.wait_for_timeout(espera * 1000); continue
            raise
        fallos_seguidos = 0
        if progreso: progreso(r)
        if r.estado in ("terminada", "vacia", "fallida"): return r
        if PARADA and PARADA(): raise Incompleta("parada solicitada con la generacion en curso", cid, "generando")
        clave = (r.nodos, r.estado)
        if clave != visto: visto, ultimo_cambio = clave, time.monotonic()
        elif time.monotonic() - ultimo_cambio > stall_min * 60 and pg.locator(STOP).count() == 0:
            raise Incompleta(f"chat sin progreso {stall_min} min y sin boton Detener", cid, "estancada")
        pg.wait_for_timeout(8000)
    raise Incompleta(f"plazo de {wait_min} min agotado con la generacion en curso", cid, "generando")


def ask(question, wait_min=25, stall_min=12, on_chat=None, on_result=None, resume_cid=None, registro=None):
    """Envia `question` en chat nuevo (o reanuda `resume_cid` sin reenviar) y devuelve Resultado.

    on_chat(cid): se llama en cuanto existe el chat (persistir para poder reanudar).
    on_result(res): se llama con la respuesta COMPLETA antes de cerrar la pestana (persistir/validar ahi).
    La pestana solo se cierra si la respuesta quedo terminada y on_result no fallo; si no, se deja abierta y se informa en Incompleta.cid.
    """
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    pg = None; cerrar = False
    try:
        browser, ctx = _conectar(p)
        limpiar_pestanas(ctx)
        pg = ctx.new_page()
        if resume_cid:
            try:
                abrir_chat(pg, resume_cid); cid = resume_cid
            except ChatInaccesible as e:
                if not e.perdida: raise Incompleta(str(e), resume_cid, "backend")  # incierto: se reintenta sin abrir otro chat
                if registro: registro(f"conversacion {resume_cid} perdida ({e}): se abre una nueva con el prompt original")
                resume_cid = None
        if not resume_cid:
            pg.goto(PROJECT_URL, wait_until="domcontentloaded", timeout=40000)
            pg.wait_for_selector('[contenteditable="true"]', timeout=20000) if "auth" not in pg.url and "login" not in pg.url else None
            comprobar_sesion(pg)
            if PROJECT_ID not in pg.url:
                raise RuntimeError("no estamos en el Project de QA; no se envia")
            pg.locator('[contenteditable="true"]').first.fill(question)
            pg.locator(SEND).first.wait_for(state='visible', timeout=15000)
            pg.locator(SEND).first.click()
            try:
                pg.wait_for_url(CID_RE, timeout=60000)
            except Exception:
                if LIMIT_RE.search(pg.evaluate("document.body.innerText")): raise RateLimited("limite de uso de ChatGPT")
                raise RuntimeError("envio no confirmado: la URL no cambio a /c/<id>")
            cid = CID_RE.search(pg.url).group(1)
            if on_chat: on_chat(cid)
        res = _esperar(pg, cid, wait_min, stall_min)
        if res.estado == "fallida":
            raise Incompleta("la generacion termino con error del servicio", cid, "fallida")
        if res.estado == "vacia":
            raise Incompleta("generacion terminada pero con salida vacia", cid, "vacia")
        if on_result: on_result(res)
        cerrar = True
        return res
    finally:
        try:
            if pg is not None and cerrar: pg.close()
        finally:
            p.stop()
