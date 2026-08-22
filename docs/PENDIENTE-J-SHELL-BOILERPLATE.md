# Pendiente J — Quitar el boilerplate de shell duplicado en los builders Python

Fecha: 2026-08-22 · Rama base: `implementacion-web-2026` · Rama de esta tarea: `pendiente-j-shell-boilerplate`

> **Alcance de esta PR y solo esta.** Reduce la cabecera/diálogo/pie
> incrustados a mano en 4 builders Python a placeholders mínimos. **Cero
> cambios en el HTML publicado** — verificado byte a byte, no solo con
> `--check`.

---

## El problema

`build-editoriales.py`, `build-tools-hub.py`, `build-writer-tools.py` y
`build-radar-opportunities.py` incrustaban cada uno ~60-90 líneas literales
de cabecera + diálogo Explorar + pie (con los mismos 7 iconos sociales
copiados 4 veces) dentro de su plantilla HTML en Python.

Esto era código muerto desde el primer commit: los cuatro builders llaman a
`inject_shell_auto()` (`scripts/site_shell.py`) sobre su HTML renderizado
antes de escribirlo a disco, y esa función sustituye cabecera/diálogo/pie
**por completo** vía `HEADER_RE`/`DIALOG_RE`/`FOOTER_RE` en
`build-site-shell.py`. El contenido incrustado nunca llegaba a verse — se
descartaba en memoria antes del `write_text()`. `build-editoriales.py` ya
tenía un comentario reconociéndolo ("las cadenas literales que había debajo
eran una cuarta copia del shell") pero nunca se completó la limpieza.

## La solución

En los 4 builders, la cabecera y el diálogo pasan a:

```html
<header class="site-header" data-header></header>

<dialog class="explore-dialog" id="explore-dialog" aria-labelledby="explore-title" data-explore-dialog></dialog>
```

y el pie a:

```html
<footer class="site-footer"></footer>
```

con un comentario **Python** (no HTML) explicando por qué están vacíos,
justo antes del `return f'''...'''` de cada plantilla — un comentario HTML
dentro del propio string sí sobreviviría en el HTML final, porque
`HEADER_RE` solo empieza a capturar desde `<header...`, no desde el
comentario anterior. Aprendido a base de un diff real durante esta misma
PR (ver más abajo).

## Verificación: byte a byte, no solo `--check`

Dos de los cuatro builders (`build-radar-opportunities.py --check`,
parcialmente) no comparan el HTML final contra el fichero ya escrito —
`--check` en ese script solo valida los datos de entrada. Confiar
ciegamente en la salida `--check` habría dejado pasar una regresión real:
en un primer intento, un comentario explicativo colocado dentro del propio
HTML (en vez de como comentario Python fuera del f-string) sobrevivía al
reemplazo de `apply_shell()` y aparecía como 6 líneas nuevas en cada página
generada. Se detectó exactamente por esto — comparando el HTML regenerado
byte a byte contra el ya publicado, no fiándose del exit code de `--check`.

Evidencia real, regenerando y diffing cada builder contra su salida ya
comprometida:

```
$ python scripts/build-editoriales.py --data data/editoriales.json --output . --check
OK: 3 editoriales publicables validadas
$ git status --short -- editoriales/          # sin salida: cero bytes distintos

$ python scripts/build-tools-hub.py data/tools-hub.json herramientas/index.html --check
OK: 17 herramientas, 2 directorios
$ git diff -- herramientas/index.html         # sin salida: cero bytes distintos

$ python scripts/build-writer-tools.py data/writer-tools.json --output recursos/herramientas-para-escritores/index.html --check
PASS: 8 herramientas; salida actualizada
$ git status --short -- recursos/herramientas-para-escritores/   # sin salida

$ python scripts/build-radar-opportunities.py --data data/radar-opportunities.json --out convocatorias-escritores
built active=2 hidden=1
$ git diff -- convocatorias-escritores/index.html   # sin salida: cero bytes distintos
   (opportunities.json cambió solo el campo generated_for=hoy, ajeno a esta PR — revertido)
```

## Batería sitewide (sin regresión)

```
$ python scripts/check-heading-structure.py
Heading/skip-link structure: 68 ficheros HTML revisados; 0 problema(s).

$ python scripts/check-local-assets.py
Local asset check: 88 HTML files scanned; 0 broken local reference(s).

$ python scripts/check-internal-graph.py
Summary: 0 error(s), 0 warning(s)

$ python scripts/check-canonical-entity-ids.py
CANONICAL ENTITY IDs: OK (4 entidades con @id, todas consistentes)

$ python tests/test-editoriales-builder-parity-v1.py   # exit 0
$ python tests/test-radar-builder-parity-v1.py
  ok   convocatorias-escritores/index.html está sincronizado
  ok   convocatorias-escritores/opportunities.json está sincronizado
  ok   convocatorias-escritores/deadlines.ics está sincronizado
  ok   el HTML generado mantiene shell V1
  ok   el HTML generado carga CSS V1
  ok   el HTML generado no vuelve al CSS legacy
tests/test-radar-builder-parity-v1: OK
```

## Resultado

```
scripts/build-editoriales.py         | 88 ++------------------------------
scripts/build-radar-opportunities.py | 76 ++++------------------------
scripts/build-tools-hub.py           | 97 ++++--------------------------------
scripts/build-writer-tools.py        | 94 ++++------------------------------
4 files changed, 31 insertions(+), 324 deletions(-)
```

**293 líneas netas de código muerto eliminadas**, sin ningún cambio en las
páginas publicadas.

## Reglas de la casa

1. No se toca `main`.
2. Cero cambios en HTML ya publicado — verificado byte a byte, no solo `--check`.
3. No se toca ningún dato (`data/*.json`) ni contenido editorial.

## Test plan

- [x] Los 4 builders regenerados y comparados byte a byte contra su salida ya comprometida: cero diferencias
- [x] Batería de `content-index-check.yml` relevante re-ejecutada en local sin regresiones
- [x] `tests/test-editoriales-builder-parity-v1.py` y `tests/test-radar-builder-parity-v1.py` en verde
