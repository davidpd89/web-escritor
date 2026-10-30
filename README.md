# Web de David Porto Díaz

Sitio de autor en español: libros, artículos, recomendaciones, Atlas literario,
herramientas, prensa y suscripción. Producción: <https://davidportodiaz.com/>.

## Arquitectura

HTML/CSS/JavaScript estáticos. Node se usa para QA, no como servidor de
producción. Datos y constructores: `data/` y `scripts/`, no publicables completos.
La navegación común procede de `data/navigation.json` y
`scripts/build-site-shell.py`. El service worker ofrece recuperación offline.
Los formularios usan servicios externos: simularlos en QA, no crear suscriptores reales.

## Entorno y validación

CI usa Node 22 y Python 3.12. Mantener un entorno Python propio del repositorio.

```sh
npm ci
python -m pip install --requirement scripts/requirements.txt
python scripts/release-readiness.py --output .ci/release-readiness-local.md
python scripts/build-site-shell.py --check
python scripts/build-sitemap.py --check
python scripts/check-asset-versions.py
```

Ambas convenciones de nombres Python son obligatorias: ejecutar individualmente
`tests/test-*.py` y cargar `tests/test_*.py` con
`python -m unittest discover -s tests -p 'test_*.py'`. Los motores Node son
`tests/*.mjs`; el smoke HTTP necesita un origen configurado. Los workflows
contienen los comandos completos de cada suite.

## Vista previa pública

No publicar el árbol de trabajo entero. Construir primero la allowlist:

```sh
python scripts/build-public-dist.py --out .preview-dist
python scripts/build-public-dist.py --check-contents --out .preview-dist
python -m http.server 4173 --bind 127.0.0.1 --directory .preview-dist
```

Abrir <http://127.0.0.1:4173/>. Playwright usa `QA_ORIGIN` y, cuando se necesita
un navegador local concreto, `QA_CHROMIUM_EXECUTABLE_PATH`.

## Publicación y seguridad

1. Abrir PR contra `main`, sin saltarse las protecciones ni checks requeridos.
2. `Required merge gate` verifica contratos, ambas suites Python, motores Node,
	generadores y aislamiento del artefacto. Otros flujos cubren navegador,
	accesibilidad y rendimiento.
3. La fusión dispara `.github/workflows/deploy-pages.yml`: construye el artefacto,
	verifica su contenido, añade identidad del SHA y publica en GitHub Pages.
4. El flujo comprueba **ese SHA exacto** en producción antes de enviar IndexNow.
	Un merge por sí solo no equivale a despliegue verificado.

No incluir credenciales, `.env`, scripts privados ni datos internos en el
artefacto. Los Workers de Cloudflare requieren un despliegue independiente.
Al cambiar un recurso registrado, mantener sincronizadas sus versiones y hashes
con `scripts/check-asset-versions.py`.

`npm audit --omit=dev` debe mantener cero vulnerabilidades. Los avisos transitivos
de QA se contrastan con `data/npm-supply-chain-baseline.json`; no aplicar
`npm audit fix --force` sin verificar compatibilidad.

## Nota operativa: Bookdala e imagen de prensa

Bookdala publicó el artículo `Fantasía juvenil con voz propia en la Feria del Libro de Madrid`:
https://bookdala.com/bnews/2026/06/10/fantasia-juvenil-con-voz-propia-en-la-feria-del-libro-de-madrid/

Bookdala incrusta la foto directamente desde la fuente original de davidportodiaz.com. Si se borra la imagen del kit de prensa, desaparecerá también en Bookdala. Si se sustituye manteniendo exactamente el mismo nombre de fichero y ruta, la actualización se reflejará también allí.
