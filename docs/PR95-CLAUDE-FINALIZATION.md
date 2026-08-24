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

## 5. Materialidad editorial — no dejar la Home plana

La referencia LRB tiene profundidad visual sin recurrir a tarjetas pesadas. La PR incorpora una primera capa en `assets/v1-lrb-material-v2.css`; Claude debe validarla visualmente con el navegador y ajustar valores si el asset real del logo cambia las proporciones.

### Capas superiores

- Barra de utilidad: casi blanca y limpia.
- Separación inferior: hairline + sombra muy leve.
- Masthead/logo: papel cálido/crudo, claramente distinto del blanco superior.
- Navegación editorial: un tono ligeramente más profundo que el masthead.
- La suma debe leerse como `blanco → sombra/regla → papel cálido → nav algo más oscura`, no como cuatro cajas.

### River / cuadrícula de periódico

- El fondo de esta zona debe extenderse a todo el ancho del viewport.
- La cuadrícula de lectura sigue limitada a `layout-max` por dentro.
- No volver a una isla blanca centrada sobre blanco puro.
- Desktop: 3 columnas; tablet: 2; móvil: 1.
- Recalcular reglas por breakpoint: nunca conservar bordes de tres columnas cuando ya hay dos o una.
- Separadores finos y coherentes colocados en los bordes de celda; evitar rayas que atraviesen visualmente el copy.
- Más respiración entre regla y texto.
- Variaciones de papel muy sutiles entre módulos para romper la uniformidad sin convertirlo en un mosaico de tarjetas.
- El módulo `Del cuaderno` debe ser el acento azul: fondo azul claro con variación tonal, título petrol más oscuro y metadatos/copy en azul-gris.
- Título, byline y resumen deben tener jerarquías distintas. El subtítulo/byline se percibe más pequeño, más bajo y más gris que el título.
- Las imágenes de lead/Feria deben respetar exactamente la geometría de su columna y sangrar solo hasta su borde de celda.
- Usar sombras a nivel de capa/sección, no una sombra independiente fuerte en cada noticia.

### Criterio visual

La prueba no es “hay colores”. La zona debe dejar de sentirse plana incluso en una captura sin interacción. Debe haber profundidad por diferencias pequeñas de luminancia, espaciado, hairlines, tipografía y una interrupción azul controlada.

## 6. Importante: integrar la estructura en el generador

La PR actual puede mejorar el DOM en runtime desde `v1-shell.js`, pero antes de mergear Claude debe preferentemente consolidar la estructura definitiva en:

`scripts/build-site-shell.py`

Actualizar `render_header()` para generar directamente el grupo izquierdo con Asistente + Inicio + hamburger y el grupo derecho con Comprar. Después ejecutar el builder del shell para regenerar todas las páginas V1 y comprobar `--check`.

Motivo: evitar que, durante la carga, el hamburger nazca a la derecha y JavaScript lo mueva después. Para una cabecera de producción y diseño de alto nivel, el DOM inicial debe ser ya el definitivo; JavaScript debe gestionar estados/interacciones, no corregir la composición básica tras el paint.

Si al comparar con LRB el hamburger debe ocultarse en Estado A de Home y mostrarse solo en Estado C, mantenerlo en el DOM y resolver visibilidad por estado/CSS, no moviéndolo entre contenedores.

## 7. QA obligatorio antes de merge

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
- diferencia perceptible pero sobria entre blanco de utility bar, papel del masthead y tono de navegación;
- sombra/regla entre capas sin aspecto de tarjeta flotante;
- river de ancho completo con contenido interior correctamente limitado;
- gutters coherentes y reglas alineadas;
- módulo azul integrado y jerarquía tonal de título/byline/resumen;
- geometría correcta 3 → 2 → 1 columnas;
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

## 8. Criterio de aceptación

No dar la PR por terminada por “parecerse” a LRB en una captura estática. Se acepta cuando los tres estados de scroll, la composición, el asset central exacto, la navegación, la materialidad del bloque editorial y las interacciones reproducen el mismo patrón de uso con la identidad de David Porto Díaz.

La referencia manda en comportamiento, proporciones y sensación de profundidad; el contenido, enlaces y branding siguen siendo propios de David.
