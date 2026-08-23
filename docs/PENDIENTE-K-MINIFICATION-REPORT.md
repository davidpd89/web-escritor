# Pendiente K — Medir el ahorro real de minificar script.js/styles.css

Fecha: 2026-08-22 · Rama base: `implementacion-web-2026` · Rama de esta tarea: `pendiente-k-minification-report`

> **Alcance de esta PR y solo esta.** Añade una herramienta de **medición**
> (`scripts/report-minification-savings.py`) + su test. **No minifica nada
> en producción, no cambia `<link>`/`<script>` en ningún HTML, no toca el
> mecanismo de despliegue de GitHub Pages.** Ver "Decisión de alcance" más
> abajo — es deliberado, no un olvido.

---

## El hallazgo original

`script.js` (44 KB) y `styles.css` (122 KB) se sirven sin minificar en
**todas** las páginas del sitio. No hay paso de build ni bundler.

## Decisión de alcance: por qué esto NO minifica nada todavía

`scripts/build-public-dist.py` ya documenta explícitamente que cambiar
cómo se sirve el sitio en producción (hoy: GitHub Pages sirve directo
desde la rama, sin build) es una **decisión humana deliberada**, no un
cambio de infraestructura silencioso:

> "Both require a human decision and a tested rollout plan; neither is
> wired into any workflow by this pass."

Minificar de verdad exige una de estas dos rutas, ninguna trivial:

1. Commitear `script.min.js`/`styles.min.css` como los ficheros realmente
   servidos — pero entonces el fichero legible deja de ser la fuente de
   verdad editada a mano, y cada cambio necesitaría un paso de
   regeneración + verificación de que no hay drift (como ya existe para
   el shell, pero nuevo aquí).
2. Migrar el despliegue de GitHub Pages de "sirve la rama tal cual" a un
   workflow de `actions/deploy-pages` que construya y minifique — un
   cambio real del mecanismo de despliegue, exactamente el tipo de
   decisión que `build-public-dist.py` marca como pendiente de decisión
   humana.

Esta PR se queda deliberadamente en el escalón anterior: **medir con
números reales cuánto valdría la pena, para que esa decisión se tome
informada** — no imponerla.

## La herramienta: `scripts/report-minification-savings.py`

Mide dos cosas, no una — porque la cifra que casi todo el mundo cita
(bytes en crudo) **exagera el beneficio real**:

- **Ahorro en crudo**: cuántos bytes menos si se quitan
  comentarios/espacios.
- **Ahorro tras gzip**: GitHub Pages ya sirve estos ficheros comprimidos,
  y gzip ya comprime muy bien el espacio en blanco repetido — el ahorro
  *marginal* de minificar encima de gzip suele ser mucho menor que la
  cifra en crudo sugiere. Esta es la cifra que de verdad coincide con lo
  que descarga el navegador de un lector.

CSS se minifica con una pasada de regex conservadora (quitar comentarios,
colapsar espacio en blanco, espacios sobrantes alrededor de `{ } : ; ,`) —
la gramática de CSS lo hace fiable. **JS no se minifica aquí**: un
minificador de JS correcto necesita un parser de verdad (template
literals, literales de regex, ASI, comentarios dentro de strings rompen
cualquier regex ingenua), y este repo no tiene todavía una dependencia de
build de JS — inventar un número de "JS minificado" con regex habría sido
peor que no darlo. Se mide igualmente su ahorro real de gzip, que es la
cifra que más importa.

## Resultado real (ejecutado contra el repo, 22/08/2026)

```
$ python scripts/report-minification-savings.py
Minification savings report (raw vs. gzip) -- report-only, nothing written to disk.

styles.css
  raw:     117.6 KB ->   110.2 KB  (6.3% smaller)
  gzip:     22.5 KB ->    19.7 KB  (12.5% smaller)  <- lo que descarga hoy un lector, y tras minificar

script.js
  raw:      42.3 KB (unminified; not safely regex-minifiable, see docstring)
  gzip:     13.3 KB  <- lo que descarga hoy un lector
```

**Conclusión honesta**: minificar `styles.css` sí merece la pena incluso
después de gzip (12,5 % menos, ~2,8 KB por carga de página, en **todas**
las páginas del sitio). Minificar `script.js` probablemente también, pero
esta PR no inventa esa cifra sin una herramienta real (`terser`/`esbuild`)
que requeriría decidir primero cómo se integra un build de JS en el
despliegue — la decisión de arriba.

## Verificación de que el minificador de CSS no rompe nada

No basta con medir bytes; hay que confirmar que el CSS "minificado" sigue
siendo el mismo CSS. Dos capas:

1. **Test unitario** (`tests/test-report-minification-savings.py`) contra
   patrones delicados reales de CSS: `calc()` con espacios internos,
   `url("...")` con espacios entre comillas, selectores múltiples
   separados por coma, `@media` anidada, comentarios.

   ```
   $ python tests/test-report-minification-savings.py
     ok   comentario eliminado sin romper el selector
     ok   calc() conserva sus espacios internos
     ok   url() con espacios en comillas no se corrompe
     ok   selectores multiples separados por coma se conservan
     ok   media query conserva su bloque anidado

   tests/test-report-minification-savings: OK
   ```

2. **Verificación visual real**: se minificó el `styles.css` real del
   repo, se sirvió en un navegador real (Chromium vía Playwright) cargando
   `index.html` una vez con el CSS original y otra con el minificado, y se
   compararon los estilos computados (`getComputedStyle`) de 7 selectores
   reales (`body`, `header.site-header`, `.brand__name`, `main`,
   `footer.site-footer`, `a.brand`, `.social-row`) × 10 propiedades
   (color, tipografía, layout, grid/flex):

   ```
   NO VISUAL/COMPUTED-STYLE DIFFERENCES across 7 selectors x 10 properties.
   ```

## Reglas de la casa

1. No se toca `main`.
2. No se minifica ningún fichero real servido por el sitio.
3. No se cambia el mecanismo de despliegue de GitHub Pages.
4. No se inventa una cifra de JS minificado sin una herramienta real que la respalde.

## Test plan

- [x] `python scripts/report-minification-savings.py` ejecutado en verde, números reales pegados arriba
- [x] `python tests/test-report-minification-savings.py` en verde
- [x] Verificación visual real (Playwright, estilos computados) sin diferencias
- [x] Cero cambios en `script.js`, `styles.css` o cualquier página publicada
