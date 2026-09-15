# Zoom/text-resilience — hallazgos pendientes tras revivir CI muerta

Fecha: 2026-09-15

Estado: `MASTHEAD_NAV_ZOOM_OVERFLOW_CONFIRMED_NOT_FIXED · HOME_CLS_768_CONFIRMED_PREEXISTING_NOT_FIXED`

## Contexto

Al revisar la web en busca de fallos reales, se encontró que dos workflows
de CI (`home-map-interaction-qa`, `tools-events-memory-browser-qa`)
llevaban ~3 semanas apuntando a una rama (`implementacion-web-2026`) que
ya no existe, así que nunca se habían vuelto a ejecutar contra cambios
reales. Se corrigió el trigger (PR #508) y, al ejecutarlas de verdad
contra `main`, salieron dos fallos reales. Uno (el overflow del footer al
200% de zoom) se arregló en esa misma PR. Estos dos quedan documentados
aquí para una PR futura, sin tocarlos todavía: son de un componente
distinto (el nav superior) o de severidad marginal (CLS al borde del
umbral), y merecen su propio análisis con calma en vez de una corrección
apresurada sobre un componente con lógica de hover/dropdown ya delicada.

## 1. Overflow horizontal en el masthead-nav al 200% de zoom

Igual que el footer (ya arreglado en PR #508), el nav superior de
escritorio (`.masthead-nav__list`, las "territorios" Obra/Autor/Cuaderno/
Herramientas/Prensa) y el nombre del autor en el masthead
(`.masthead__name-text`) desbordan horizontalmente cuando el texto se
zoomea al 200% (`html{font-size:200%}`, la misma simulación que usa
`qa/tools-events-memory-text-resilience.css`), en anchos donde el nav de
escritorio sigue visible (no ha pasado aún al hamburger/Explorar):

| Ancho de viewport | Overflow medido al 200% zoom |
|---|---|
| 1280px | 95px |
| 1024px | 223px |
| 900px | 285px |

Confirmado con Playwright contra `main` (con el fix del footer ya
aplicado, para descartar que fuera la misma causa): `document.documentElement.scrollWidth - clientWidth` no es 0 en ninguno de esos tres
anchos al zoomear el texto.

**Causa probable**: el mismo patrón que tenía el footer — el nav de
escritorio depende de un breakpoint de ancho de viewport (`assets/v1-shell-lrb-v2.css`, oculta el nav a favor del hamburger a partir de
cierto ancho) para colapsar, pero un zoom de solo texto no cambia el
ancho de viewport, así que ese breakpoint nunca se dispara aunque el
contenido real ya no quepa.

**Por qué no se arregló ya**: a diferencia del footer (una fila plana de
5 elementos independientes), el masthead-nav tiene lógica de disclosure
por hover/foco y un botón de toggle explícito con `aria-expanded`
(documentado en los comentarios de `qa/home-map-interaction.mjs`), así
que convertirlo a flex-wrap sin más podría romper esa interacción o el
posicionamiento de los submenús desplegables. Necesita su propio análisis
y verificación con Playwright antes de tocarlo, igual que se hizo con el
footer, no una copia mecánica del mismo fix.

**Siguiente paso**: nueva PR dedicada, reproducir con
`qa/home-map-interaction.mjs` como base (añadiéndole una aserción de
zoom-200% análoga a la que ya tiene `tools-events-memory-browser.mjs`),
diseñar el fix específico para esta estructura con dropdowns, y verificar
que el hover/foco/teclado siguen funcionando igual después.

## 2. CLS marginal en Home a 768px (preexistente, no introducido ahora)

Al revivir `home-map-interaction-qa`, además del hallazgo anterior salió
un fallo ya existente e independiente: `qa/home-map-interaction.mjs`
falla la aserción `768: CLS <= 0.1` — Cumulative Layout Shift medido en
`0.1001570625`, justo por encima del umbral "good" de Core Web Vitals
(0.1), específicamente en el ancho 768px tras descartar el overlay de
introducción (vídeo + botón "Entrar").

Reproducido 3 veces: 2 de 3 dieron exactamente ese mismo valor
(0.1001570625), 1 de 3 dio 0 — es decir, es una carrera de timing real
(probablemente una fuente web que termina de cargar/intercambiar justo
después del primer pintado en ese ancho concreto), no ruido aleatorio.

**Fuente del shift** (via `PerformanceObserver` con `sources`):
`DIV.yale-lead__copy` y `ASIDE.yale-rail` (la columna de texto y la
barra lateral de la sección hero de Home, `assets/v1-home.css`).

**Por qué no se arregló ya**: es un problema de timing de carga de
fuentes (FOUT/FOIT) al borde del umbral, no un desbordamiento visible
claro como el del footer/nav — diagnosticar la fuente exacta responsable
y decidir el tratamiento correcto (`font-display`, precarga, o `size-adjust`
para que la fuente de respaldo no cambie el layout al intercambiar)
merece su propia investigación específica de rendimiento, no un parche
a ciegas sobre una sección hero ya muy afinada (ver los comentarios de
`assets/v1-home.css` sobre esta misma sección).

**Siguiente paso**: perfilar qué fuente interviene en `.yale-lead__copy`/
`.yale-rail` en ese rango de ancho y aplicar el tratamiento de carga de
fuente adecuado; volver a medir con `qa/home-map-interaction.mjs`.

## Nota

Ninguno de los dos está en la lista de checks obligatorios del ruleset
`main-production-integrity` (`Required merge gate`,
`public-artifact-contract`, `reflow-sitewide`, `pa11y-baseline`,
`lighthouse`, `Compare against committed baselines`), así que no bloquean
merges — pero ahora que el trigger de CI está vivo de nuevo, aparecerán
en rojo en cualquier PR futura que tome esas rutas hasta que se arreglen
de verdad.
