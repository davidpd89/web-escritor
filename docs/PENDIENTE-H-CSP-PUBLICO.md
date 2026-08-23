# Pendiente H — CSP real para las páginas públicas del shell

Fecha: 2026-08-22 · Rama base: `implementacion-web-2026` · Rama de esta tarea: `pendiente-h-csp-publico`

> **Alcance de esta PR y solo esta.** Extiende `scripts/build-site-shell.py`
> para inyectar un `Content-Security-Policy` en las páginas públicas que hoy
> no declaran ninguno. **No toca el CSP ya existente de las herramientas de
> manuscrito** (más estricto, `connect-src 'none'`, escrito a mano) — se
> detecta y se deja intacto explícitamente.

---

## El problema

Las 29 páginas de herramientas de manuscrito llevan un CSP estricto por su
contrato de privacidad. El resto del sitio (`index.html`, `autor.html`, y el
resto de páginas editoriales servidas por el shell V1) **no declaraba
ningún CSP, `Referrer-Policy` ni `Permissions-Policy`** — ni meta tag ni
cabecera (GitHub Pages no permite cabeceras custom, así que el meta tag es
la única vía real disponible aquí). Precisamente las páginas con
formularios de newsletter y scripts de terceros.

## La solución: el CSP se gestiona igual que cabecera/pie/diálogo

`scripts/build-site-shell.py` ya generaba tres bloques por contrato
(cabecera, diálogo Explorar, pie). Esta PR añade un cuarto: un bloque CSP
con marcadores `<!-- site-shell:csp:start/end -->`, gestionado por
`apply_public_csp()`:

- Si la página **ya declara un CSP fuera de esos marcadores** (las
  herramientas de manuscrito) → se deja completamente intacto.
- Si ya tiene el bloque marcado de una ejecución anterior → se regenera
  (mismo patrón que cabecera/pie: una sola fuente de verdad, se puede
  actualizar la política central y todas las páginas la heredan).
- Si no tiene ningún CSP → se inserta uno nuevo justo después de
  `<meta charset>`.

Como todos los builders de páginas (`build-editoriales.py`,
`build-radar-opportunities.py`, `build-topic-collections.py`,
`build-tools-hub.py`, `build-writer-tools.py`) ya pasan por el mismo puente
(`scripts/site_shell.py` → `inject_shell_auto()`), **heredan el CSP nuevo
automáticamente**, sin tocar ninguno de esos ficheros.

## Metodología: verificado con navegador real, no solo leyendo código

La primera versión de la política se construyó leyendo `script.js` y
`assistant.js` a mano. Un smoke test de Playwright cargando las páginas
reales (no solo re-analizando el HTML generado) encontró **tres cosas que
la lectura manual no vio**:

1. **`tracker.metricool.com`** — hay un script de analítica de Metricool
   (`script.js`, función "Metricool web analytics") que ni siquiera
   apareció al buscar "goatcounter". Carga un script y un píxel de imagen
   (`c3po.jpg`); ambos bloqueados hasta añadir el origen a `script-src`,
   `connect-src` e `img-src`.
2. **`gc.zgo.at` por protocolo relativo** — el script de GoatCounter se
   carga como `//gc.zgo.at/count.js`. Sobre `https://` resuelve a
   `https://gc.zgo.at`, pero listar el origen con `https://` explícito
   rompía las pruebas locales por `http://`. Solución: listar el host sin
   esquema (`gc.zgo.at`), que CSP resuelve contra el esquema real de cada
   página.
3. **Los bloques `<script type="speculationrules">` SÍ están sujetos a
   `script-src`** (8 páginas) — al contrario que
   `<script type="application/ld+json">`, que los navegadores probados
   exentan. La opción fácil era añadir `'unsafe-inline'` a `script-src`,
   pero eso también habilitaría cualquier script inyectado por un XSS real.
   En su lugar, `apply_public_csp()` calcula el hash `sha256` exacto de
   **cada** `<script>` inline ejecutable de la página (función
   `inline_script_hashes()`) y lo añade como `'sha256-...'` — cubre tanto
   `speculationrules` como el bloque de configuración inline de GoatCounter
   (`window.goatcounter={...}`, presente en 13 páginas), sin abrir la
   puerta a scripts arbitrarios.

Política final:

```
default-src 'self';
script-src 'self' gc.zgo.at davidportodiaz.goatcounter.com tracker.metricool.com [+ hashes sha256 por página];
connect-src 'self' gc.zgo.at davidportodiaz.goatcounter.com tracker.metricool.com https://subscribe.davidpd89.workers.dev;
img-src 'self' data: tracker.metricool.com;
style-src 'self' 'unsafe-inline';
font-src 'self'; worker-src 'self'; media-src 'self'; object-src 'none';
base-uri 'self'; form-action 'self'; frame-src 'none'; manifest-src 'self'
```

Dos limitaciones documentadas explícitamente en el propio código, no
silenciadas:

- **`style-src` necesita `'unsafe-inline'`**: hay estilos `style="..."`
  puntuales en páginas generadas por builders (p. ej.
  `build-writer-tools.py`). Deuda conocida, no de esta PR.
- **No se declara `frame-ancestors`**: la especificación CSP lo ignora
  explícitamente cuando se entrega por `<meta>` (el propio navegador lo
  avisa en consola) — solo funciona por cabecera HTTP real, que GitHub
  Pages no permite configurar. Añadirlo daría una falsa sensación de
  protección anti-clickjacking que nunca se aplicaría.

## Test

**`qa/csp-public-shell-browser.mjs`** (nuevo, promovido desde el smoke test
usado para descubrir los tres hallazgos de arriba): carga 15 páginas reales
en Chromium (incluida una herramienta de manuscrito, para confirmar que su
CSP propio sigue intacto) y falla si aparece cualquier aviso de CSP en
consola.

```
$ node qa/csp-public-shell-browser.mjs
csp-public-shell-browser: PASS (15 páginas, 0 violaciones de CSP)
```

Wireado en `.github/workflows/csp-public-shell-qa.yml` (dispara en toda PR,
mismo patrón que `sitewide-reflow-qa.yml`).

### Evidencia adicional

```
$ python scripts/build-site-shell.py --check
CHECK: shell en 59 páginas

$ python scripts/build-tools-hub.py data/tools-hub.json herramientas/index.html --check
OK: 17 herramientas, 2 directorios

$ python scripts/build-writer-tools.py data/writer-tools.json --output recursos/herramientas-para-escritores/index.html --check
PASS: 8 herramientas; salida actualizada

$ python scripts/check-heading-structure.py
Heading/skip-link structure: 68 ficheros HTML revisados; 0 problema(s).

$ python scripts/check-local-assets.py
Local asset check: 88 HTML files scanned; 0 broken local reference(s).

$ python scripts/check-internal-graph.py
Summary: 0 error(s), 0 warning(s)

$ python scripts/check-canonical-entity-ids.py
CANONICAL ENTITY IDs: OK (4 entidades con @id, todas consistentes)

$ python scripts/build-article-tools.py --check
ARTICLE TOOLS: OK (0 pagina(s) con el bloque pre-renderizado al dia)

$ python scripts/check-social-cards.py --strict   # exit 0
$ python scripts/check-secrets.py                 # exit 0
$ python tests/test-editoriales-builder-parity-v1.py   # exit 0
$ python tests/test-radar-builder-parity-v1.py         # exit 0
```

Confirmado con `git diff`: `herramientas/legibilidad/index.html` (y el
resto de herramientas de manuscrito) no cambia ni un byte con esta PR — su
CSP propio queda intacto.

## Reglas de la casa

1. No se toca `main`.
2. No se modifica el CSP existente de ninguna herramienta de manuscrito.
3. No se declara ninguna directiva CSP que el navegador vaya a ignorar sin
   decirlo explícitamente en un comentario (ver `frame-ancestors` arriba).

## Test plan

- [x] `python scripts/build-site-shell.py --check` en verde
- [x] `node qa/csp-public-shell-browser.mjs` en verde (15 páginas, incluida 1 herramienta de manuscrito)
- [x] Cero cambios en páginas de herramientas de manuscrito (CSP propio intacto)
- [x] Batería completa de `content-index-check.yml` re-ejecutada en local sin regresiones
