"""qa_clases: clasificacion de la salida de UN test (local y en Actions comparten criterio; solo stdlib para poder correr en el runner).

Clases:
  ok            exit 0
  sin_entorno   falta navegador/paquete en este equipo (se valida en Actions)
  invalido      el test no es ejecutable: sintaxis, importacion rota, ejecutor inexistente, excepcion propia sin asercion
  infra         el entorno no permite un resultado fiable (red, timeout, puerto)
  hallazgo      el test se ejecuto y una asercion/comprobacion FALLA: es evidencia sobre el producto
"""
import re

INFRA = re.compile(r"ECONNRESET|ETIMEDOUT|ENOTFOUND|EADDRINUSE|rate limit|\b50[234]\b|\b429\b|Could not resolve host|runner.*lost|npm ERR! network|socket hang up|Timeout .*exceeded.*launch|TimeoutExpired", re.I)
SIN_ENTORNO = re.compile(r"Cannot find package '(playwright|@playwright)|Executable doesn't exist|browserType\.launch.*(not found|doesn't exist)|WinError 1314", re.I)  # 1314: sin privilegio de symlink en este Windows; no es culpa del test
INVALIDO = re.compile(r"SyntaxError|IndentationError|TabError|ModuleNotFoundError|ImportError|Cannot find module|ERR_MODULE_NOT_FOUND|ERR_REQUIRE_ESM|ERR_UNKNOWN_FILE_EXTENSION|"
                      r"can't open file|is not recognized as an internal|spawn .* ENOENT", re.I)
ASERCION = re.compile(r"AssertionError|ERR_ASSERTION|^FAIL\b|^\s*FAIL[: ]|^FAILED \(failures|\d+ (fallos?|failures?|failed)\b|^not ok\b", re.M | re.I)


def clasificar_salida(rc, out):
    if rc == 0: return "sin_entorno" if out.startswith("SIN_ENTORNO") else "ok"
    if SIN_ENTORNO.search(out): return "sin_entorno"
    if INVALIDO.search(out): return "invalido"  # antes que las aserciones: un import roto no es un hallazgo aunque el traceback cite 'assert'
    if ASERCION.search(out): return "hallazgo"
    if INFRA.search(out): return "infra"
    return "invalido"  # exit != 0 sin ninguna comprobacion fallida identificable: el test se rompe por si mismo


def estado_por_categoria(clase, categoria):
    """Clase de un test -> estado del item segun la intencion del test."""
    if clase == "ok": return "local_ok"
    if clase == "sin_entorno": return "sin_entorno"
    if clase == "infra": return "infra"
    if clase == "hallazgo":
        return "defecto_demostrado" if categoria == "descubre_defecto" else "a_triar" if categoria == "exploratoria" else "fallo_test"
    return "fallo_test"  # invalido
