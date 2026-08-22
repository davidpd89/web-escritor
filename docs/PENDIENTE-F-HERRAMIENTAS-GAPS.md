# Pendiente F — Herramientas: bugs y gaps de código en features ya investigadas

Fecha: 2026-08-22 · Rama base: `implementacion-web-2026` · Rama de esta tarea: `pendiente-f-herramientas-gaps`

> **Alcance de esta PR y solo esta.** Cuatro sub-tareas independientes entre
> sí (F.1–F.4), cada una en su propio fichero/carpeta, sin tocar
> `script.js`, el Worker, ni contenido de `/cuaderno/` — otras PRs (A–E)
> cubren eso. Ninguna de las cuatro es bloqueante para el 3/09; ábrelas en
> el orden F.1 → F.4 → F.2 → F.3 si el tiempo aprieta.
>
> **No requiere claves ni acceso externo.**
>
> **No es diseño final** ni contenido editorial: F.2 y F.3 tienen un
> componente de "feature nueva", pero aquí solo se pide el código/motor, no
> el contenido real que lo llenaría (artículos del Atlas literario, etc.) —
> eso lo decide David en otra sesión.

---

## F.1 — `scripts/build-autores-red.py` crashea (prioridad más alta de las cuatro)

### El problema

```bash
$ python scripts/build-autores-red.py --data data/autores-red.json --check
Traceback (most recent call last):
  ...
build_site_shell.BuildError: autores/index.html: no se encontró pie para inyectar shell
```

El error viene de `apply_shell()` en `scripts/build-site-shell.py`
(alrededor de la línea 421). Esa función inserta cabecera, diálogo "Explorar"
y pie en el HTML que le pasa cada builder. Para cabecera y diálogo hay lógica
de *fallback* si no encuentra el marcador exacto (busca el final de la
cabecera e inserta ahí). **Para el pie no existe ese fallback** — si el HTML
generado por `build-autores-red.py` no tiene un `<footer>` que encaje con
`FOOTER_RE`/los marcadores esperados, `apply_shell()` lanza directamente
`BuildError` sin intentar nada más.

Esto no bloquea nada hoy (no hay contenido real de `/autores/` — solo un
registro de ejemplo marcado `"status": "draft"` y `"NO PUBLICAR"` en
`data/autores-red.json`), pero bloqueará la feature en cuanto haya un autor
real que publicar.

### Qué hacer

Diagnostica cuál de las dos causas es la real antes de tocar nada:

1. **Si la plantilla HTML que genera `build-autores-red.py` simplemente no
   incluye un `<footer>`** (o lo incluye sin los marcadores/estructura que
   `FOOTER_RE` espera en `build-site-shell.py`): añade un `<footer>` mínimo a
   la plantilla, igual que tienen las demás páginas generadas por builders
   hermanos que sí pasan por `apply_shell()` sin error (revisa cómo lo hace,
   por ejemplo, `scripts/build-tools-hub.py` o `scripts/build-editoriales.py`
   antes de invocar `inject_shell_auto()` — deben tener un placeholder de pie
   coherente).
2. **Si el problema es más general** (varios builders podrían tropezar con
   esto igual en el futuro): considera si `apply_shell()` merece el mismo
   fallback que ya tiene el diálogo "Explorar" para el pie. Si tomas esta
   vía, hazlo con cuidado — es un cambio en código compartido por todos los
   builders que usan el shell, no solo por `build-autores-red.py`. Añade test
   de regresión que cubra el caso que fallaba.

No inventes contenido de `/autores/` ni lo publiques — el objetivo es
solamente que el comando `--check` deje de crashear.

### Criterio de aceptación

```bash
python scripts/build-autores-red.py --data data/autores-red.json --check
```
termina sin traceback (puede seguir rechazando el registro de ejemplo por
`"status": "draft"` — eso es comportamiento correcto, no un bug).

---

## F.2 — "Revisor de diálogo en español" nunca se construyó (prioridad media)

### El problema

`herramientas/dialogo/` existe pero es una herramienta **distinta**: mide qué
porcentaje del texto está en bloques de diálogo (`assets/dialogo-espanol.js`).
El comprobador de convenciones de diálogo en español que pedía la
investigación original
(`WEB DAVID PORTO nuevas ideas/30_INVESTIGACION_RANDOM_CRECIMIENTO_ORGANICO_IA_COMUNIDAD_2026-08-17.md`,
punto 2.B) — guion vs. raya, comillas rectas vs. angulares, acotaciones
sospechosas — no tiene ningún código.

### Qué hacer

Esto es una herramienta nueva, no un fix. Sigue el patrón ya establecido por
las herramientas hermanas de manuscrito (`herramientas/repeticiones/`,
`herramientas/manuscrito/`, `herramientas/dialogo/` como referencia de
estructura):

1. Procesamiento **100% local**, sin red — el contrato transversal de
   `WEB DAVID PORTO nuevas ideas/49_CONTRATO_PRIVACIDAD_HERRAMIENTAS_MANUSCRITO_2026-08-19.md`
   (ya movido a `COMPLETADO/` porque está aplicado) es de obligado
   cumplimiento aquí también: CSP `connect-src 'none'`, sin scripts de
   terceros, sin `localStorage`/`sessionStorage`/`indexedDB` con el texto del
   manuscrito.
2. Detecta como mínimo:
   - guion (`-`) usado donde correspondería raya (`—`) al abrir/cerrar
     intervención de diálogo;
   - comillas rectas (`"`) donde el resto del texto usa angulares (`«»`) o
     viceversa, si hay mezcla inconsistente;
   - acotaciones que rompen la puntuación esperada (p. ej. mayúscula tras
     coma de acotación cuando no toca).
3. Página nueva `herramientas/dialogo-convenciones/` (o el slug que no
   choque con `herramientas/dialogo/` existente) con su propia entrada en
   `data/tools-hub.json` y verificación con
   `scripts/audit-private-tools.py herramientas/dialogo-convenciones/index.html`.
4. Test siguiendo el patrón de los tests existentes en `tests/` para
   herramientas hermanas.

### Criterio de aceptación

- `scripts/audit-private-tools.py herramientas/dialogo-convenciones/index.html`
  pasa (contrato de privacidad).
- `tests/test-tools-hub-public-registry.py` sigue en verde con la nueva
  entrada añadida al registro.
- Casos de prueba con texto de ejemplo real (guion vs. raya, comillas
  mixtas) detectados correctamente.

---

## F.3 — Atlas literario: scaffolding completo, cero contenido, sin tests (prioridad baja)

### El problema

`scripts/build-atlas-literario.py` + `data/atlas-literario.json` +
`assets/atlas-literario.{js,css}` existen y funcionan — validación estricta
de metadatos por imagen tal como especifica el dossier
(`WEB DAVID PORTO nuevas ideas/46_ATLAS_LITERARIO_INVESTIGACION_E_IMPLEMENTACION_2026-08-18.md`).
Los 12 ítems piloto están todos en `status:"planned"` (ninguno publicado), no
existe `/atlas-literario/` generada en el sitio, y no hay ningún test para el
builder — a diferencia de builders hermanos que sí tienen su
`tests/test-<builder>.py`.

### Qué hacer

Solo la parte de test/código, no contenido:

1. `tests/test-atlas-literario.py` siguiendo el patrón de los tests de otros
   builders del repo (fixtures con datos de ejemplo, comprobar que rechaza
   `status:"published"` sin `verified_date`/`credit`/`license`/`source_url`,
   comprobar que `status:"planned"` no genera output publicable).
2. No cambies ningún ítem de `data/atlas-literario.json` a `"published"` — eso
   requiere contenido/investigación real que no es parte de esta tarea.
3. No generes ni enlaces `/atlas-literario/` desde ninguna página del sitio
   todavía — el propio dossier especifica no añadirlo a navegación hasta
   tener 12-15 piezas reales.

### Criterio de aceptación

- `python tests/test-atlas-literario.py` (o como se invoque según el patrón
  del repo) pasa.
- Cero cambios en contenido/publicación real del Atlas.

---

## F.4 — Sin test para `validate-video-to-article.py` (prioridad media, rápido)

### El problema

`scripts/templates/video-to-article.template.md` y
`scripts/validate-video-to-article.py` existen y funcionan, pero no tienen
test — a diferencia de los pipelines editoriales hermanos (`reader-question`,
`decision-escritura`), que sí siguen el patrón completo de tres piezas
(plantilla + validador + test). Ejemplo de referencia ya existente en el
repo: `tests/test-validate-reader-question.py`.

También falta, según el dossier
(`WEB DAVID PORTO nuevas ideas/54_VIDEO_A_ACTIVO_EDITORIAL_TRANSCRIPCIONES_UTILES_2026-08-19.md`,
sección 11), el componente `video-source.component.html` reutilizable
("vídeo original / plataforma / fecha / aviso de versión editada") — no
existe en ningún sitio del repo fuera de la carpeta del dossier.

### Qué hacer

1. `tests/test-validate-video-to-article.py` siguiendo exactamente el patrón
   de `tests/test-validate-reader-question.py`: casos `draft` → PASS,
   `review` sin fuente → FAIL esperado, entrada completa → PASS.
2. Construye `video-source.component.html` (o el nombre/ubicación que siga la
   convención de otros componentes reutilizables del repo, revisa dónde viven
   los `.example.html`/componentes similares) con los campos que especifica
   la sección 11 del documento 54: vídeo original, plataforma, fecha, aviso
   de versión editada.

### Criterio de aceptación

- `python tests/test-validate-video-to-article.py` pasa con los tres casos.
- `video-source.component.html` existe y es HTML válido, sin depender de
  contenido de vídeo real (usa placeholders explícitos tipo `[[YOUTUBE_ID]]`
  como hace el resto de plantillas "dormidas" del repo).

---

## Reglas de la casa

1. No se toca `main`.
2. No publiques contenido nuevo (Atlas, autores, dialogo) — solo el código
   que falta para que la feature funcione cuando haya contenido real.
3. Cualquier herramienta nueva que reciba texto de manuscrito (F.2) debe
   pasar `scripts/audit-private-tools.py` sin excepciones.
4. No debilites ningún test existente para que pasen los nuevos.
5. No inventes un PASS: pega salidas reales de cada comando en la PR.

## Test plan

- [x] F.1: `build-autores-red.py --check` sin traceback
- [x] F.4: `test-validate-video-to-article.py` en verde + `video-source.component.html` creado
- [x] F.2: herramienta nueva con contrato de privacidad verificado + tests
- [x] F.3: `test-atlas-literario.py` creado y en verde, sin tocar contenido/publicación

---

## Estado de implementación (rama `pendiente-f-herramientas-gaps`)

- [x] F.1: corregido el crash de shell en `build-autores-red.py` ajustando el
   placeholder del pie al patrón reconocido por `build-site-shell.py`.
- [x] F.2: creada herramienta nueva `herramientas/dialogo-convenciones/` +
   motor `assets/dialogo-convenciones.js` + test `tests/test-dialogo-convenciones.mjs`.
- [x] F.2: registrada en `data/tools-hub.json`, `data/content-registry.json` y
   regenerado `herramientas/index.html`.
- [x] F.3: creado `tests/test-atlas-literario.py` con casos published inválido
   y planned sin salida publicable.
- [x] F.4: creado `tests/test-validate-video-to-article.py` y componente
   `scripts/templates/video-source.component.html`.

### Evidencia de ejecución

F.1 (sin traceback):

```text
Desactualizados:
- autores\index.html
```

F.4:

```text
tests/test-validate-video-to-article: OK
```

F.2:

```text
test-dialogo-convenciones: all assertions passed
PASS — 1 file(s) satisfy the static private-tool preflight
PASS tools-hub boundary: 18 public tools, 2 public directories
```

F.3:

```text
tests/test-atlas-literario: OK
```

### Correcciones de merge readiness tras CI

- Se regeneró `autor.html` y `data/site-human-stats.generated.*` para alinear
   "Esta web, en cifras" con el nuevo total público (18 herramientas),
   resolviendo `python-tests`/`content-indexes`.
- Se añadió `/herramientas/dialogo-convenciones/` en
   `mapa-del-sitio/index.html` para cerrar el contrato de discoverability.
- Se añadió `robots noindex` a
   `scripts/templates/video-source.component.html` para evitar que se trate
   como HTML público indexable en `check-global-discoverability.py`.
- Se regeneró shell en `herramientas/dialogo-convenciones/index.html` para
   pasar `build-site-shell.py --check`.
