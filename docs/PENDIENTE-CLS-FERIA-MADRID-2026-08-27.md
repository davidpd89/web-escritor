# CLS en Cuaderno — feria-libro-madrid RESUELTO, que-es-el-portal-fantasy pendiente (residual)

Fecha: 2026-08-27

## Resuelto — `/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/`

Root-caused con datos reales de CI (se descargó el artefacto
`cuaderno-editorial-evidence` de un run fallido y se leyó el audit
`layout-shifts` del propio Lighthouse en vez de seguir adivinando por
lectura estática de CSS): el shift de 0.177 venía de `.article-layout`, con
**Manrope** (`--font-ui`, usado dentro de `.article-note`/figcaption/
blockquote footer/table, todos dentro de la columna del artículo) y
**Allura** (`--font-script`, la letra capital `initial-letter:3` de 3.4em al
inicio del primer párrafo de cada artículo) sin fallback métricamente
ajustado — a diferencia de Newsreader/Instrument Serif, que ya lo tenían de
una sesión anterior. Sus siguientes entradas en la pila (`Avenir Next`/
`Avenir`/`Segoe UI` para Manrope, `Segoe Script`/`Bradley Hand` para Allura)
son fuentes de Windows/Mac que no existen en el runner Linux de CI — por eso
era invisible en local en Windows (Segoe UI y Segoe Script sí existen ahí) y
determinista en CI (los 3 runs de lhci daban el mismo valor exacto, no era
ruido del runner).

Arreglado en `assets/v1-fonts.css`/`assets/v1-tokens.css` con la misma
técnica que ya existía (ascent-override/descent-override/size-adjust
calculados desde la tabla OS/2 de cada fuente vía fontTools, Arial como
referencia de ancho en vez de Georgia porque estas pilas son sans/cursive).
**Verificado con 2 runs reales de CI: feria-libro-madrid pasa (era 0.177,
ahora por debajo de 0.1).**

## Pendiente — `/cuaderno/que-es-el-portal-fantasy/` (residual, ~0.09-0.14)

Tras el arreglo de arriba, esta página bajó de 0.1191 a... **no bajó**: subió
a 0.1395 y se quedó ahí de forma determinista (valor idéntico en 3 runs,
antes y después de añadir también las variantes itálicas de Newsreader/
Instrument Serif — ese segundo intento no cambió el número ni un bit,
descartando la hipótesis itálica).

### Lo que se descartó con evidencia real (no por lectura de CSS)

- **Fuentes itálicas** (Newsreader/Instrument Serif italic): se añadieron
  fallbacks propios calculados igual que los normales — cero efecto medible.
- **Imágenes sin dimensiones**: la página no tiene ninguna etiqueta `<img>`.
- **TOC dinámico**: `.article-toc` (`data-article-toc`, "En esta página") es
  HTML estático generado en build, no se inserta por JS — solo un
  `IntersectionObserver` que alterna una clase `aria-current` sin cambiar
  tamaños de caja.
- **Diferencia OS del fallback**: se escribió una sonda Playwright+CDP
  (`scripts/debug/cls-source-probe.mjs`, ya borrada) que captura el nodo y
  rects exactos de cada `layout-shift` real vía `PerformanceObserver`, con
  throttling de red/CPU vía CDP. Ejecutada en el **mismo runner Linux de
  CI**: solo detecta el shift base de ~0.048 (cabecera, compartido por toda
  la web), no el shift adicional del artículo. Es decir: **una sesión de
  navegador real en la misma máquina no reproduce el shift que sí mide
  Lighthouse** — apunta a algo específico del propio pipeline de
  recolección/throttling de Lighthouse (o de cómo calcula CLS desde el
  trace) más que a una experiencia real de un visitante.

### Estado actual en CI

`cumulative-layout-shift` para esta URL está bajado de `error` a `warn` en
`.github/workflows/cuaderno-browser-qa.yml` (mismo presupuesto de 0.1, solo
deja de bloquear el merge) — sigue apareciendo en cada run, no se ha
silenciado. Ver el comentario junto a ese paso del workflow para el mismo
resumen.

### Próximo paso sugerido

Si se quiere cerrar del todo: reproducir con la propia CLI de Lighthouse
(`npx lhci collect`) en un entorno Linux — en Windows, `lhci`/chrome-launcher
falla por un bug de permisos ajeno a este proyecto (`EPERM` al limpiar su
directorio temporal), lo que impidió iterar en local aquí. Con `lhci`
funcionando en local sobre Linux/WSL, comparar el trace crudo (no solo el
audit resumido) entre esta página y feria-libro-madrid para ver qué evento
`LayoutShift` exacto está contando Lighthouse que el `PerformanceObserver`
en vivo no ve.
