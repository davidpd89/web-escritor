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
