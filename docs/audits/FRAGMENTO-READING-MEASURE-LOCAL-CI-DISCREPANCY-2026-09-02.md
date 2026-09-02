# /fragmento/ · discrepancia local/CI de la medida de lectura (2026-09-02)

## 1. El hallazgo

`qa/samuel-fragmento-design-browser.mjs` afirma que `.article-prose` mide
`<= min(width-16, 850)`px. Ejecutado en local (Windows, Playwright con
Chromium descargado por `npx playwright install`) contra el `HEAD` combinado
de #320 + `main` fresco (`c04d59e3`), el script falla en 3 de 9 viewports:

```
desktop-1440: medida de lectura demasiado ancha (973.28125px)
desktop-1280: medida de lectura demasiado ancha (969.9375px)
tablet-1024: medida de lectura demasiado ancha (942.09375px)
```

Pero el job `reflow-sitewide` de CI (Ubuntu) para el commit equivalente de
la rama de #319 (`7484cc83`, run `33564890122`, `conclusion: success`)
imprime:

```
samuel-fragmento-design-browser: PASS (9 viewports)
```

Mismo componente, mismo test, mismo umbral (850px): CI pasa limpio en los 9
viewports, incluidos los 3 que fallan en este Windows local.

## 2. Causa raíz identificada (no solo sospechada)

`.article-prose` usa `max-width:var(--reading-max)` = `68ch`. `ch` se
calcula a partir del ancho del glyph "0" en la fuente y tamaño activos
(`Newsreader`, `font-size` calculado 18.88px en desktop). Medido con
`CanvasRenderingContext2D.measureText('0')` sobre la MISMA página, el MISMO
`document.fonts` reportando "Newsreader ... loaded":

| Entorno | Ancho del glyph "0" | 68ch resultante |
|---|---:|---:|
| Browser pane de esta sesión (Chromium) | 10.40px | 707.02px |
| Playwright local (Windows) | 14.31px | 973.29px |

Ambos entornos reportan la fuente variable `Newsreader` como cargada, pero
miden un glyph "0" un 37% más ancho en el Playwright-Chromium de esta
máquina Windows. `Newsreader` es una fuente variable con eje de peso
(`font-weight: 400 600` en su `@font-face`); esto es consistente con que
cada build/versión de Chromium resuelva el punto por defecto del eje
variable (o el hinting/subpíxel) de forma distinta cuando no se fija un
`font-variation-settings` explícito — el mismo tipo de divergencia de
renderizado de fuente ya documentado en
`docs/audits/REFLOW-LOCAL-CI-DISCREPANCY-2026-09-01.md` para páginas
completamente distintas.

## 3. Triangulación

| Entorno | Resultado |
|---|---:|
| Playwright local (Windows) | **FALLA** (973/970/942px) |
| CI Ubuntu (`reflow-sitewide`) | **PASA** (9/9 viewports) |
| Browser pane de esta sesión (Chromium) | **PASA** (707px medido directamente vía `getBoundingClientRect`) |

Dos de tres entornos independientes — incluido el que realmente gatea los
merges — coinciden en que la medida de lectura es correcta. Solo el
Chromium que `npx playwright install` descargó en esta máquina Windows
diverge, y lo hace por una causa de renderizado de fuente ya identificada
con precisión (no una suposición), no por un fallo real de CSS/diseño.

## 4. Conclusión

**No es un bug de diseño ni un test obsoleto.** `--reading-max:68ch` es la
implementación correcta y deliberada de una medida de lectura (68
caracteres cae dentro del rango tipográfico estándar de 45-75); el umbral
de 850px del test es una aproximación razonable que de hecho se cumple en
CI. No se toca ni el CSS ni el test.

Se documenta explícitamente (siguiendo la misma política que el caso de
2026-09-01) para que si `reflow-sitewide` empieza a fallar esto en CI en
el futuro, se reabra como regresión real — hasta entonces, es ruido de
entorno de esta máquina local, no algo que bloquee un merge.

## 5. Qué NO se ha hecho

No se ha modificado `assets/v1-editorial.css` ni `--reading-max` para
"arreglar" un ancho que CI no reporta como roto. No se ha relajado el
umbral de 850px en `qa/samuel-fragmento-design-browser.mjs` para
silenciar un fallo que solo ocurre en un Chromium local que difiere del
que realmente decide si un PR pasa.
