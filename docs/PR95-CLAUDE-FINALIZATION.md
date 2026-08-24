# PR #95 — Finalización en local por Claude

Objetivo: dejar el header de davidportodiaz.com con el mismo patrón de comportamiento que la cabecera actual de London Review of Books (`https://www.lrb.co.uk/`), adaptado a la identidad y contenido de David Porto Díaz. No copiar código de LRB: reproducir jerarquía, proporciones, estados de scroll e interacción.

## 1. Asset central obligatorio

El asset exacto NO está en GitHub. Claude sí debe leerlo desde el checkout/local indicado por David:

`C:\GIT\web-escritor\WEB DAVID PORTO nuevas ideas\DISEÑO Y DEMÁS\Imagenes generadas para implementar`

Buscar el fichero cuyo nombre/base sea:

`london - david porto logo central`

No reconstruirlo con HTML, CSS, una fuente parecida ni texto escrito. No regenerarlo. Usar ese gráfico exacto.

Copiar/exportar al repositorio como:

`assets/london-david-porto-logo-central.png`

Se puede añadir además WebP si aporta reducción real de peso sin degradación perceptible. Mantener transparencia/fondo según el original.

Después de disponer del fichero, medir sus dimensiones reales y ajustar el CSS del masthead para que su tamaño visual, respiración superior/inferior y relación con la barra de navegación reproduzcan la referencia de LRB en 1440 px, 768 px y 390 px. No asumir que los valores actuales son definitivos: el asset real manda.

## 2. Estados de comportamiento que deben quedar cerrados

### Estado A — parte superior de Home

- Barra superior fija.
- Izquierda: `Asistente`, icono de `Inicio` y la navegación de menú según el estado de referencia.
- Derecha: `Comprar`.
- Debajo: logo gráfico central de David, no texto simulado.
- Debajo del logo: navegación editorial compacta `Obras · Autor · Cuaderno · Herramientas · Prensa`.
- Las opciones deben estar visualmente juntas, con escala y ritmo equivalentes a `The Paper / Subjects / Blog / ...` de LRB, pero usando los nombres de David.

### Estado B — primer tramo de scroll

- La cabecera editorial sigue pegada arriba: logo + navegación continúan visibles mientras el usuario empieza a desplazarse.
- No debe haber salto de layout, flash, reflow brusco ni superposición con el contenido.

### Estado C — scroll más profundo

- La parte grande de marca/navegación desaparece o colapsa con una transición breve y sobria.
- Queda la barra compacta fija.
- Aparece claramente el hamburger a la izquierda, junto al acceso de Asistente/Inicio.
- `Comprar` sigue accesible a la derecha.
- La transición debe recordar funcionalmente a LRB: cabecera grande → cabecera compacta. No convertirlo en una animación decorativa distinta.

## 3. Menú y submenús

- El hamburger abre `Explorar` desde la izquierda.
- Mantener `<dialog>`, focus trap, Escape, backdrop y devolución de foco.
- `Obras`, `Autor`, `Cuaderno`, `Herramientas` y `Prensa` deben tener submenús pequeños y utilizables.
- No usar el antiguo preview que desaparecía al mover el puntero.
- Desktop: hover y focus-within deben permitir mover el ratón desde el label hasta las opciones sin que se cierre el menú.
- Teclado/touch: disclosure explícito con `aria-expanded`, Escape y click exterior.
- Obras debe incluir como mínimo: Todas las obras, Las manecillas del recuerdo, Samuel entre mundos.

## 4. Home persistente

El icono de casa debe existir en el header en páginas interiores para volver siempre a `/` sin tener que abrir Explorar.

## 5. Importante: integrar la estructura en el generador

La PR actual puede mejorar el DOM en runtime desde `v1-shell.js`, pero antes de mergear Claude debe preferentemente consolidar la estructura definitiva en:

`scripts/build-site-shell.py`

Actualizar `render_header()` para generar directamente el grupo izquierdo con Asistente + Inicio + hamburger y el grupo derecho con Comprar. Después ejecutar el builder del shell para regenerar todas las páginas V1 y comprobar `--check`.

Motivo: evitar que, durante la carga, el hamburger nazca a la derecha y JavaScript lo mueva después. Para una cabecera de producción y diseño de alto nivel, el DOM inicial debe ser ya el definitivo; JavaScript debe gestionar estados/interacciones, no corregir la composición básica tras el paint.

Si al comparar con LRB el hamburger debe ocultarse en Estado A de Home y mostrarse solo en Estado C, mantenerlo en el DOM y resolver visibilidad por estado/CSS, no moviéndolo entre contenedores.

## 6. QA obligatorio antes de merge

Comparar lado a lado con `https://www.lrb.co.uk/` y con el preview local/staging en:

- 1440 × 900
- 1024 × 768
- 768 × 1024
- 390 × 844

Verificar:

- posición/tamaño del logo real;
- altura total de cabecera;
- distancia logo ↔ navegación;
- navegación suficientemente junta;
- estado sticky inicial;
- umbral y transición a compacta;
- hamburger izquierdo;
- drawer izquierdo;
- Home persistente;
- Comprar a la derecha;
- submenús sin hueco que los cierre al mover el ratón;
- tabulación completa;
- Escape;
- `prefers-reduced-motion`;
- zoom 200 % / reflow;
- ausencia de CLS perceptible;
- ausencia de errores CSP/console;
- `python scripts/build-site-shell.py --check` (o comando equivalente del repo);
- tests Playwright/pa11y/reflow que ya existan en el repositorio para shell y navegación.

## 7. Criterio de aceptación

No dar la PR por terminada por “parecerse” a LRB en una captura estática. Se acepta cuando los tres estados de scroll, la composición, el asset central exacto, la navegación y las interacciones reproducen el mismo patrón de uso con la identidad de David Porto Díaz.

La referencia manda en comportamiento y proporciones; el contenido, enlaces, colores y branding siguen siendo propios de David.
