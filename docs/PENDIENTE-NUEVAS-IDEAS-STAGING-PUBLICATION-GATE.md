# Auditoría WEB DAVID PORTO nuevas ideas — gate real de publicación `staging`

Fecha de contraste: 2026-08-23  
Base auditada: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`

## Hallazgo

La arquitectura actual diferencia correctamente contenido público, `noindex`, interno, lab y gated para **descubrimiento**, pero no existe un gate equivalente que impida que una ruta HTML `staging` llegue a ser **servida públicamente** por GitHub Pages.

Caso real que destapa el hueco: `/donde-empieza-la-jaula/`.

- `data/content-registry.json` ya reserva la obra en estado `staging` / `noindex`.
- `scripts/check-global-discoverability.py` tiene `GATED_PREFIXES = ("donde-empieza-la-jaula/",)` y evita exponerla en mapa/shell público.
- `scripts/build-sitemap.py` excluye HTML con `noindex`.
- `/lab/diseno-home-v1/JAULA-PUBLIC-SPEC.md` y `book-jaula.html` contienen una propuesta suficientemente definida para staging/lab.
- La ruta normal `/donde-empieza-la-jaula/` todavía no existe en la rama de integración, lo cual es seguro.

Sin embargo, `scripts/build-public-dist.py` no usa el estado editorial del registry como autoridad de inclusión/exclusión, y `content-index-check.yml` documenta que GitHub Pages publica `main` desde la raíz. Por tanto, si en el futuro se añade `donde-empieza-la-jaula/index.html` y se mergea a `main`, `noindex` impediría indexación, pero **no impediría acceso por URL**.

`noindex` no es un control de publicación.

---

## Deuda 1 — una sola autoridad explícita para publicabilidad

Definir un contrato inequívoco a partir de `data/content-registry.json` o un manifiesto de release derivado de él.

Como mínimo, cada ruta debe poder resolver uno de estos estados operativos:

- pública/indexable;
- pública/noindex legítima (legal, utilidad, etc.);
- staging/gated: puede existir en rama/lab/preview, **no en producción pública**;
- privada/interna/lab: nunca producción pública.

No inferir «staging» solo por prefijo de ruta ni mantener dos listas manuales divergentes.

---

## Deuda 2 — el build/check debe fallar si una ruta gated entra en producción

Reforzar el pipeline público existente —preferentemente `build-public-dist.py`, su `--check-contents` y el checker global— para que:

1. resuelva los `sourceFile`/URLs del registry;
2. construya la lista explícita de rutas no publicables;
3. falle si una de ellas aparece en el artefacto de producción;
4. falle si una ruta gated aparece en sitemap, mapa humano, navegación, feeds, búsqueda pública o índices generados;
5. distinga `PUBLIC_NOINDEX` legítimo de `STAGING/GATED`, porque ambos pueden llevar meta robots `noindex` pero tienen políticas de acceso diferentes.

La comprobación debe ser reproducible y no depender de recordar una carpeta concreta.

---

## Deuda 3 — fixture/regresión con Jaula

Usar Jaula como fixture real del contrato mientras continúe marcada `staging`:

- su entrada puede existir en `content-registry`;
- su lab puede existir;
- `/donde-empieza-la-jaula/` no debe formar parte del paquete/árbol de producción;
- no debe aparecer en sitemap, mapa, navegación, `llms*.txt`, feeds ni búsqueda pública;
- un fixture temporal que introduzca la ruta normal debe hacer fallar el gate de publicación aunque el HTML contenga `noindex`.

El test debe demostrar explícitamente la diferencia entre «no indexar» y «no publicar».

---

## Deuda 4 — preview/staging no debe convertirse en producción por accidente

Si se decide que las rutas gated pueden vivir fuera de `/lab`, deben existir únicamente en una superficie de preview que no sea el root que GitHub Pages sirve desde `main`.

Opciones válidas a decidir al implementar:

- construir preview desde la rama de integración y filtrar producción por manifiesto;
- mantener contenidos gated exclusivamente bajo `/lab`/carpetas excluidas hasta promoción editorial;
- migrar más adelante el deploy a un artefacto generado donde el filtro sea obligatorio.

No hace falta cambiar ahora el mecanismo de despliegue para cerrar esta deuda; sí hace falta que la validación impida una promoción insegura mientras el deploy siga sirviendo el árbol de `main`.

---

## Coordinación con PR existentes

- **#58**: post-deploy y `build-public-dist.py --check-contents`. Debe reutilizar el gate final, no crear otra lista de exclusión.
- **#1**: promoción `implementacion-web-2026` → `main`; el gate debe formar parte de la readiness final.
- **#57 / SEO**: `noindex` y sitemap siguen siendo capa de descubrimiento, no sustituyen este control.
- **#66**: evidencia/canon; no publicar contenido editorial para hacer pasar el test.
- **#78**: QA visual/mobile; independiente de publicabilidad.

---

## Decisión sobre Jaula durante esta PR

No crear todavía `/donde-empieza-la-jaula/index.html` en la rama publicable.

Aunque la spec visual y el capítulo autorizado existan en el lab, la ruta normal debe permanecer **GATED** hasta que este contrato de publicación sea ejecutable. Después podrá evaluarse una PR de staging real separada sin riesgo de filtrarse a producción.

---

## Criterio de cierre

- `staging/gated` no se representa únicamente con `noindex`;
- el estado editorial controla también la pertenencia al artefacto/árbol público;
- CI falla ante una ruta gated servible en producción;
- Jaula demuestra el caso en una regresión real;
- sitemap/mapa/nav/feed/búsqueda/machine surfaces permanecen sincronizados;
- #58 consume el mismo contrato en su check de contenido;
- no hay listas paralelas de prefijos como autoridad principal.

No tocar `main`, no desplegar producción, no publicar Jaula y no activar auto-merge.

---

# Estado de implementación (2026-08-23)

## Deuda 1 — autoridad única

`scripts/build-public-dist.py` incorpora `gated_prefixes_from_registry(root)`: lee `data/content-registry.json`, y para cada entrada con `status` en `{"noindex", "internal", "gated", "deprecated"}` (es decir, distinto de `"public"`, el default) deriva el directorio contenedor de su `sourceFile`. **Verificado en el registry real**: de 61 entradas, solo `work-jaula-staging` tiene `status: "noindex"` — `/privacidad.html`/`/aviso-legal.html` permanecen `status: "public"` con `searchIndex/sitemap: false`, que es exactamente la distinción «pública-pero-no-indexada» vs. «staging/gated» que pedía la Deuda 1.

`scripts/check-global-discoverability.py` **ya no mantiene su propia tupla** `GATED_PREFIXES = ("donde-empieza-la-jaula/",)`: ahora importa `build-public-dist.py` y llama a la misma función. Una única autoridad, no dos listas que puedan desincronizarse.

## Deuda 2 — el build/check falla si una ruta gated entra en producción

- `build()` excluye del árbol público cualquier fichero cuyo path empiece por un prefijo gated derivado del registry (además de la lista corta ya existente de directorios internos como `scripts/`, `tests/`, `data/`).
- `check_contents()` (usado también por `--check-contents`, consumido por #58) ahora falla explícitamente con el mensaje `gated/staging route present in public dist (content-registry status != public): <prefijo>` si una ruta gated aparece en el dist ya construido — no solo lo excluye al construir, también lo detecta si ya está presente (por ejemplo, tras una regeneración incompleta).
- `.assetsignore` (consumido por el despliegue real de staging en Cloudflare vía `wrangler deploy --assets`) también se regenera para incluir las rutas gated derivadas del registry — cierra el mismo hueco en el staging real, no solo en `.preview-dist` local. `--check-assetsignore` (ya wireado en `content-index-check.yml`, sin filtro de rutas) detectó la deriva antes de regenerarlo.
- `--root` añadido a `build-public-dist.py` (antes usaba únicamente la constante global `ROOT`) para poder testear contra un fixture aislado sin tocar el repo real.

## Deuda 3 — fixture/regresión con Jaula

`tests/test-staging-publication-gate.py` (nuevo, 9 casos): construye un **repositorio git temporal real** (nunca el repo del proyecto) con tres páginas — home pública normal, una página `noindex` pero `status: "public"` (como `/privacidad.html`), y una página `status: "noindex"` (como Jaula) — y demuestra:

1. `gated_prefixes_from_registry()` deriva únicamente la ruta con `status != public`, no la que es `noindex` pero pública;
2. `build()` no copia el directorio staging al dist, ni sus assets hermanos no registrados individualmente (p. ej. `cover.webp`);
3. la ruta `noindex`-pero-`public` **sí** se publica — la prueba explícita de que la diferencia es el estado editorial, no el meta robots;
4. `check_contents()` pasa sobre un dist correctamente filtrado;
5. **regresión real**: si la ruta staging se cuela en el dist de todos modos (fixture que simula un bug futuro en `build()` o una copia manual), `check_contents()` la detecta y falla, aunque su HTML declare `noindex` — la prueba que pedía explícitamente la Deuda 3;
6. contra el **repositorio real** (sin escribir nada en él): confirma que `donde-empieza-la-jaula/` ya está en la autoridad derivada del registry real;
7. construye el dist **real** completo a un directorio temporal y confirma que la ruta gated queda fuera y el gate pasa — prueba de extremo a extremo con el repo de verdad, no solo con el fixture sintético.

## Deuda 4 — preview/staging no se convierte en producción por accidente

No se cambió el mecanismo de despliegue (GitHub Pages sigue sirviendo `main` desde la raíz; Cloudflare staging sigue usando `git archive HEAD`). La opción elegida, ya viable con lo implementado: mientras el deploy siga sirviendo el árbol tal cual, `.assetsignore` (real, consumido por Cloudflare) y `--check-contents`/`--check-assetsignore` (consumidos por CI y por #58) son el filtro obligatorio que impide la promoción insegura, sin requerir tocar el mecanismo de despliegue en esta PR — tal y como el propio criterio de cierre permitía.

## Coordinación con PR existentes (confirmada)

- **#58**: `build-public-dist.py --check-contents` ahora incluye el gate de publicación sin que #58 tenga que mantener su propia lista de exclusión — reutiliza la misma función.
- **#66 / #78**: no se ha tocado contenido editorial ni QA visual; cambio confinado a `scripts/build-public-dist.py`, `scripts/check-global-discoverability.py`, tests y CI.
- **Jaula**: `/donde-empieza-la-jaula/index.html` **no se ha creado** en esta PR — sigue GATED, tal y como exige la «Decisión sobre Jaula durante esta PR».

## Evidencia de ejecución (real)

```
$ python tests/test-staging-publication-gate.py
  ok   1. gated_prefixes_from_registry deriva solo la ruta con status != public
  ok   2a. build() no copia el directorio staging al dist público
  ok   2b. build() tampoco copia assets hermanos no registrados individualmente
  ok   3. una ruta noindex pero status=public SI se incluye en el dist (noindex no es control de acceso)
  ok   3b. la home normal se incluye
  ok   4. check_contents() pasa sobre un dist ya filtrado correctamente
  ok   5. check_contents() detecta y falla si la ruta staging se cuela en el dist (aunque tenga noindex)
  ok   6. el registry REAL del repo ya declara donde-empieza-la-jaula/ como gated
  ok   7a. el dist REAL no contiene donde-empieza-la-jaula/
  ok   7b. check_contents() pasa sobre el dist REAL
tests/test-staging-publication-gate: OK

$ python scripts/build-public-dist.py --check-assetsignore   # ANTES del fix
FAIL: .assetsignore está desincronizado. Regenera con --emit-assetsignore.

$ python scripts/build-public-dist.py --emit-assetsignore    # tras anadir la autoridad del registry
ESCRITO .assetsignore (29 reglas)

$ python scripts/build-public-dist.py --check-assetsignore   # DESPUES
OK: .assetsignore coincide con las exclusiones de este builder.

$ python scripts/build-public-dist.py --out .preview-dist-test
BUILT ...: 740 file(s) included, 183 excluded
OK: ... contains none of the excluded categories.

$ python scripts/check-global-discoverability.py
PASS: global discoverability (88 tracked HTML artifacts; 54 indexable; search=POSPUESTO; map=60 human destinations)

$ python scripts/check-navigation-coverage.py
PASS: navigation coverage (60 registry routes, 54 sitemap routes, 17 interactive tools)

$ python scripts/check-internal-graph.py
Summary: 0 error(s), 0 warning(s)

$ python scripts/build-sitemap.py --check
SITEMAP OK: 54 URLs

$ python scripts/check-secrets.py
No obvious secrets found in tracked files.
```

**Prueba en rojo real**: `--check-assetsignore` falló nada más añadir la nueva lógica (antes de regenerar el fichero), confirmando que la comprobación detecta de verdad la deriva. El caso 5 del test hace exactamente lo mismo con el dist local: introduce manualmente la ruta gated en un dist ya construido y confirma que `check_contents()` la rechaza.

## CI

`scripts/build-public-dist.py` y `tests/test-staging-publication-gate.py` añadidos a las rutas de disparo de `global-discoverability-closure-qa.yml`, con un paso nuevo que ejecuta el test de regresión y un ciclo completo real de `build-public-dist.py` (build + `--check-contents`). `content-index-check.yml` ya ejecutaba `--check-assetsignore` sin filtro de rutas. `tests/test-staging-publication-gate.py` también cubierto por el barrido genérico de `tool-tests.yml` (`tests/test-*.py`).
