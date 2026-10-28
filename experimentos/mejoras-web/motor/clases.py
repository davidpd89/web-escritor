"""clases: clasificacion de la salida de UN test (local y en Actions comparten criterio; solo stdlib para poder correr en el runner).

PROCEDENCIA: scripts/qa-gpt/qa_clases.py @ fe131c8ce6a663b54ab067ea5bc123318ececbb0, blob d26c90d1bc8cf3d4fc8269da246f2bef7728df2c.
CAMBIOS: las expresiones y `clasificar_salida` son literales; `estado_por_categoria` se sustituye por `estado_remoto` (el laboratorio no tiene
tests "descubre_defecto/exploratoria": un test de aceptacion de una mejora que falla es un FALLO DEL PARCHE, no un hallazgo de producto).

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


def estado_remoto(clases):
    """Clases de los tests de una mejora -> veredicto del grupo: valido | fallo_parche | fallo_test | infra | sin_entorno.
    Precedencia: un test que no pudo ejecutarse (invalido/infra/sin_entorno) NUNCA cuenta como aprobado y nunca se confunde con un fallo del parche."""
    cs = list(clases)
    if not cs: return "fallo_test"
    if "invalido" in cs: return "fallo_test"
    if "infra" in cs: return "infra"
    if "sin_entorno" in cs: return "sin_entorno"
    if "hallazgo" in cs: return "fallo_parche"
    return "valido"
