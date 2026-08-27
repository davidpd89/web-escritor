# Reflow 200% + WCAG text spacing en /mapa-del-sitio/ — residual (~30px)

Fecha: 2026-08-27

## Resuelto en esta pasada

`qa/global-discoverability-browser.mjs` prueba `/` y `/mapa-del-sitio/` a
320px + `documentElement.style.fontSize:200%` + un `letter-spacing`/
`word-spacing`/`line-height` inyectado (simulación de WCAG 1.4.10 Reflow +
1.4.12 Text Spacing combinados). `/` fallaba en 366/320; ahora pasa. Tres
causas reales, cada una un patrón distinto (documentado en
`assets/v1-reflow-hardening-v7.css`):

1. `.masthead__brand-row`/`.masthead__logo-image` — el logo usaba unidades
   de viewport sin contar el avatar+gap. (Ya en el PR original.)
2. `.social-row .text-action` (footer, "Goodreads") y
   `[data-lrb-home] .yale-text-link` ("Todas las herramientas") — ambos
   `display:inline-flex` con la flecha `::after` como segundo ítem flex sin
   `flex-wrap`. El texto puede envolver a 2 líneas dentro de su propio ítem,
   pero sin `flex-wrap:wrap` en el contenedor la flecha no baja con él y el
   conjunto se sale por la derecha aunque el propio `<a>` mida menos que el
   viewport. `min-width:0` + `flex-wrap:wrap` lo arregla en ambos casos,
   verificado con Playwright directo (no solo lectura de CSS).
3. `.intro__enter` (botón "Entrar" de la cinemática) — `position:absolute;
   left:50%` + `transform:translate(-50%,Ypx)`. El *layout box* (antes del
   transform: `offsetLeft`+`offsetWidth`, lo que cuenta para
   `scrollWidth`) no es el mismo que la posición *visual* (después del
   transform, lo que devuelve `getBoundingClientRect()`) — por eso
   `getBoundingClientRect().right` puede estar dentro del viewport mientras
   `scrollWidth` ya no. Confirmado directamente (no por sospecha): con
   `.intro{display:none}` puesto, `scrollWidth` no bajó nada, así que en un
   primer intento pensé que no era la causa — luego medí `offsetLeft`/
   `offsetWidth` manualmente (ignorando el transform) y sí daba
   `offsetRight:430` en 320px. Reducir el padding a este breakpoint lo trae
   dentro de rango.

## Pendiente — `/mapa-del-sitio/` (residual, ~30px: 350/320)

Encontrado un cuarto caso del mismo patrón #2 en
`.directory-group__label` (las cabeceras "01 Orientación", "02 Obras"...
del índice): `display:flex;justify-content:space-between` sin
`min-width:0` en los dos `<span>` hijos, y "Orientación" es una sola
palabra que no puede envolver sin `overflow-wrap:anywhere`. Se añadió el
mismo arreglo (`flex-wrap:wrap` + `min-width:0` + `overflow-wrap:anywhere`)
en `v1-reflow-hardening-v7.css` y, verificado con Playwright directo, las
7 instancias de `.directory-group__label` en la página quedan con todos
sus `<span>` dentro del viewport (`getBoundingClientRect().right <= 288`
en los 7 casos, viewport de 320px).

**Pero `document.documentElement.scrollWidth` se queda exactamente en 350
antes y después de ese arreglo** — es decir, no era la causa (o no toda).
Un barrido completo de `[...document.querySelectorAll('*')].filter(el =>
el.getBoundingClientRect().right > 321)` sobre la página entera, con el
arreglo puesto, no devuelve ningún elemento — ninguna caja *visual* se sale
del viewport, igual que pasaba con `.intro__enter` antes de medir el layout
box a mano. Sospecho que es el mismo patrón #3 (algo con `transform` o
`position` que desacopla layout box de posición visual) en otro
componente de la página, pero no lo he localizado: revisar
`offsetLeft+offsetWidth` (ignorando transforms) de cada elemento de la
página en vez de `getBoundingClientRect()`, igual que se hizo con
`.intro__enter`, es el siguiente paso lógico, no algo ya descartado.

No lo he dejado bloqueando: es un check sintético (200% zoom + espaciado
extra simultáneos, no una combinación real que un usuario normal
encuentre) sobre una sola página, y el resto de arreglos de esta pasada sí
son mejoras reales verificadas para usuarios con zoom real. Si se retoma,
empezar por el barrido `offsetLeft+offsetWidth` de arriba en vez de
`getBoundingClientRect()`.
