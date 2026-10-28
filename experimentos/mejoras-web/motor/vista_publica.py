"""vista_publica: servidor TEMPORAL con la web de la rama de laboratorio (lab/mejoras-web-*), para revisar las mejoras integradas SIN pasar por main.

Cada pocos minutos: `git fetch` de la rama de laboratorio -> si cambio, worktree desacoplado -> `scripts/build-public-dist.py` (el MISMO artefacto allowlist que publica
produccion: nada interno se sirve) -> se sirve en 127.0.0.1:<puerto> con X-Robots-Tag noindex y robots.txt Disallow. Un tunel gratuito y sin cuenta
(cloudflared "quick tunnel" si esta instalado; si no, `ssh` -> localhost.run, que trae Windows 10+) la expone en una URL https temporal que se escribe en
<estado>/vista/vista.json y se muestra en ESTADO. La pagina /_lab/ lista las mejoras integradas (titulo, necesidad, criterio, fuentes, commit y fecha).
Solo LEE el repositorio y la base del laboratorio; no publica en ningun sitio permanente, no toca main ni Pages ni Cloudflare. La URL cambia cada vez que se reinicia el tunel.
"""
import functools, html, http.server, json, os, re, shutil, subprocess, sys, threading, time
from pathlib import Path

import mw

URL_TUNEL = re.compile(r"https://[a-z0-9-]+\.(?:trycloudflare\.com|lhr\.life|localhost\.run)\b[^\s\"']*", re.I)
ESTADOS_VISIBLES = ("integrado", "pr_borrador")


def carpeta(): return mw.STATE / "vista"


def extraer_url(linea):
    """URL publica del tunel en una linea de salida de cloudflared / ssh localhost.run (None si no hay)."""
    m = URL_TUNEL.search(linea or "")
    return m.group(0).rstrip(".,") if m else None


# ---------- pagina de cambios ----------
def pagina_cambios(c, cfg_rama, sha):
    filas = c.execute("SELECT id, titulo, area, necesidad, contraste, datos, estado, actualizado FROM expedientes WHERE estado IN (%s) ORDER BY actualizado DESC" % ",".join("?" * len(ESTADOS_VISIBLES)), ESTADOS_VISIBLES).fetchall()
    e = html.escape
    items = []
    for r in filas:
        d = json.loads(r["datos"] or "{}"); cont = json.loads(r["contraste"] or "{}")
        fuentes = "".join(f'<li><a href="{e(f.get("url", ""), quote=True)}" rel="noopener noreferrer">{e(f.get("titulo", f.get("url", "")))}</a></li>' for f in d.get("fuentes", []) if str(f.get("url", "")).startswith("https://"))
        items.append(f'<article><h2>{e(r["id"])} · {e(r["titulo"])}</h2><p class="meta">{e(r["area"])} · {e(r["estado"])} · {e(str(r["actualizado"])[:16].replace("T", " "))}</p>'
                     f'<p><strong>Necesidad.</strong> {e((r["necesidad"] or "")[:600])}</p><p><strong>Criterio.</strong> {e((cont.get("criterio_aceptacion") or d.get("criterio_aceptacion", ""))[:500])}</p>'
                     f'<p><strong>Cambio.</strong> {e(d.get("propuesta", "")[:600])}</p>' + (f"<details><summary>Fuentes</summary><ul>{fuentes}</ul></details>" if fuentes else "") + "</article>")
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">'
            f'<title>Mejoras del laboratorio</title><style>body{{font:16px/1.5 system-ui,sans-serif;max-width:46rem;margin:2rem auto;padding:0 1rem}}article{{border-top:1px solid #8884;padding:1rem 0}}.meta{{color:#666;font-size:.9rem}}</style></head><body>'
            f'<h1>Mejoras integradas en {e(cfg_rama)}</h1><p>Vista previa temporal, no es la web publicada. Commit <code>{e((sha or "")[:12])}</code>. {len(filas)} mejora(s).</p>'
            + ("".join(items) or "<p>Todavia no hay mejoras integradas.</p>") + "</body></html>")


# ---------- construccion ----------
class Vista:
    def __init__(self, q=mw, run=None):
        self.q, self.run = q, run or q.run
        self.dir = carpeta(); self.dir.mkdir(parents=True, exist_ok=True)
        self.actual = self.dir / "sitio"          # lo que se sirve (se sustituye entero tras cada build correcto)
        self.src = self.dir / "src"

    def _git(self, *a, cwd=None, check=True):
        r = self.run(["git", "-c", "core.autocrlf=false", *a], cwd=cwd or self.q.REPO, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        if check and r.returncode: raise RuntimeError(f"git {' '.join(a)[:60]}: {(r.stderr or r.stdout).strip()[:200]}")
        return r.stdout.strip()

    def sha_remoto(self):
        self._git("fetch", "-q", "origin", self.q.CFG["rama_base"], check=False)
        return self._git("rev-parse", self.q.fuente_ref())

    def construido(self):
        try: return json.loads((self.dir / "vista.json").read_text(encoding="utf-8")).get("sha")
        except (OSError, ValueError): return None

    def refrescar(self, c=None, forzar=False):
        """-> True si se reconstruyo. Un build fallido NO sustituye al sitio anterior (la vista previa sigue sirviendo lo ultimo bueno)."""
        sha = self.sha_remoto()
        if sha == self.construido() and not forzar and self.actual.is_dir(): return False
        if (self.src / ".git").exists(): self._git("checkout", "-q", "--detach", sha, cwd=self.src)
        else:
            self._git("worktree", "prune", check=False)
            self._git("worktree", "add", "--detach", "-f", str(self.src), sha)
        nuevo = self.dir / "sitio.nuevo"; shutil.rmtree(nuevo, ignore_errors=True)
        script = self.src / "scripts" / "build-public-dist.py"
        if not script.is_file(): raise RuntimeError("scripts/build-public-dist.py no existe en la rama de laboratorio")
        for extra in ([], ["--check-contents"]):  # construye y verifica el contrato publico (allowlist)
            r = self.run([sys.executable, str(script), *extra, "--out", str(nuevo)], cwd=self.src, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
            if r.returncode: raise RuntimeError(f"build-public-dist {' '.join(extra)}: {(r.stderr or r.stdout).strip()[-300:]}")
        (nuevo / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
        (nuevo / "_lab").mkdir(exist_ok=True)
        cc = c or self.q.db()
        try: (nuevo / "_lab" / "index.html").write_text(pagina_cambios(cc, self.q.CFG["rama_base"], sha), encoding="utf-8")
        finally:
            if c is None: cc.close()
        viejo = self.dir / "sitio.viejo"; shutil.rmtree(viejo, ignore_errors=True)
        if self.actual.exists(): os.replace(self.actual, viejo)
        os.replace(nuevo, self.actual); shutil.rmtree(viejo, ignore_errors=True)
        self.escribir(sha=sha, construido=self.q.now())
        return True

    def escribir(self, **kw):
        f = self.dir / "vista.json"
        try: cur = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError): cur = {}
        cur.update(kw, actualizado=self.q.now())
        tmp = f.with_suffix(".tmp"); tmp.write_text(json.dumps(cur, ensure_ascii=False), encoding="utf-8"); os.replace(tmp, f)


# ---------- servidor ----------
class Manejador(http.server.SimpleHTTPRequestHandler):
    raiz = None  # callable -> Path actual (se sustituye tras cada build sin reiniciar el servidor)

    def __init__(self, *a, **k): super().__init__(*a, directory=str(type(self).raiz()), **k)
    def log_message(self, *a): pass
    def end_headers(self):
        self.send_header("X-Robots-Tag", "noindex, nofollow"); self.send_header("Cache-Control", "no-cache"); super().end_headers()


def servir(vista, puerto):
    """Servidor en 127.0.0.1 (el tunel se conecta a el). -> (servidor, hilo)."""
    M = type("M", (Manejador,), {"raiz": staticmethod(lambda: vista.actual)})
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", puerto), M); srv.daemon_threads = True
    th = threading.Thread(target=srv.serve_forever, name="vista-http", daemon=True); th.start()
    return srv, th


# ---------- tunel ----------
def comando_tunel(puerto, which=shutil.which):
    """cloudflared (quick tunnel, sin cuenta) si esta instalado; si no, ssh -> localhost.run (sin cuenta ni instalacion en Windows 10+). None si no hay ninguno."""
    if which("cloudflared"): return "cloudflared", [which("cloudflared"), "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{puerto}"]
    if which("ssh"):
        return "localhost.run", [which("ssh"), "-T", "-o", "StrictHostKeyChecking=accept-new", "-o", "ServerAliveInterval=30", "-o", "ExitOnForwardFailure=yes", "-o", "BatchMode=yes",
                                 "-R", f"80:127.0.0.1:{puerto}", "nokey@localhost.run"]
    return None


class Tunel:
    def __init__(self, vista, puerto, popen=None, which=None):
        self.vista, self.puerto, self.popen, self.which, self.p, self.url = vista, puerto, popen or mw.popen, which or (lambda n: shutil.which(n)), None, None

    def vivo(self): return self.p is not None and self.p.poll() is None

    def asegurar(self):
        if self.vivo(): return True
        cmd = comando_tunel(self.puerto, self.which)
        if not cmd:
            self.vista.escribir(url=None, tunel="ninguno: instala cloudflared (winget install Cloudflare.cloudflared) o usa el cliente ssh de Windows"); return False
        nombre, args = cmd; self.url = None
        self.vista.escribir(url=None, tunel=f"{nombre}: arrancando")
        self.p = self.popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        def leer():
            for linea in self.p.stdout:
                u = extraer_url(linea)
                if u and not self.url: self.url = u; self.vista.escribir(url=u, tunel=nombre)
        threading.Thread(target=leer, name="vista-tunel", daemon=True).start()
        return True

    def cerrar(self):
        if self.vivo():
            try: self.p.terminate()
            except OSError: pass


def bucle(q=mw, vista=None, cada_s=None, popen=None, sleep=time.sleep, una_vez=False):
    """Proceso `mw.py vista-publica`: refresca, sirve y mantiene el tunel hasta que se pida parar (bandera stop_vista)."""
    cfg = q.CFG.get("vista_publica", {}); puerto = int(cfg.get("puerto", 8780)); cada_s = cada_s or int(cfg.get("refresco_s", 180))
    vista = vista or Vista(q); tunel = Tunel(vista, puerto, popen=popen)
    lock = q.Lock("vista")
    with lock:
        q.set_flag("stop_vista", False); c = q.db()
        try:
            srv = None
            while not q.flag("stop_vista"):
                lock.latido()
                try: cambio = vista.refrescar(c)
                except Exception as e:
                    vista.escribir(error=f"{q.now()} {str(e)[:200]}"); print(f"{q.now()} vista: {e}"); cambio = False
                else:
                    if cambio: vista.escribir(error=None); print(f"{q.now()} vista reconstruida @ {vista.construido()[:10]}")
                if srv is None and vista.actual.is_dir(): srv, _ = servir(vista, puerto); vista.escribir(local=f"http://127.0.0.1:{puerto}/")
                if srv is not None: tunel.asegurar()
                if una_vez: break
                q.dormir_flag(cada_s, "stop_vista", lock) if hasattr(q, "dormir_flag") else sleep(cada_s)
        finally:
            tunel.cerrar()
            if srv: srv.shutdown(); srv.server_close()
            c.close()
    return 0
