# Rendimiento (PageSpeed Insights / Lighthouse) — auditoría 2026-09-09

Fecha de revisión: 2026-09-09

Estado: `LCP_FIXED_INTRO_VIDEO_PRIORITY · CACHE_LIFETIMES_PENDING · IMAGE_DELIVERY_PENDING · AGENTIC_NAV_EXPERIMENTAL_LOW_PRIORITY`

## Por qué esto importa para posicionamiento

Google usa las Core Web Vitals (LCP, INP, CLS) como señal de "page experience" en el ranking. No es el factor dominante, pero a paridad de contenido puede inclinar la balanza, y un LCP muy malo también empeora la percepción real de velocidad para cualquier visitante que llega desde una búsqueda.

## Hallazgo principal: LCP de 17,3 s en Home (móvil) — corregido

Auditoría en [PageSpeed Insights](https://pagespeed.web.dev/) sobre `https://davidportodiaz.com/`, perfil móvil (Moto G Power emulado, Lighthouse 13.4.1, 4G lenta):

| Métrica | Valor |
|---|---|
| Rendimiento (score) | 66/100 |
| Accesibilidad | 100/100 |
| Prácticas recomendadas | 100/100 |
| SEO | 100/100 |
| FCP | 2,3 s |
| **LCP** | **17,3 s** |
| TBT | 20 ms |
| CLS | 0 |
| Speed Index | 6,9 s |

El elemento de LCP identificado por Lighthouse era `body > div.intro > div.intro__stage > video.intro__video` — el vídeo de la intro cinemática de Home, no el hero real de la página. El propio comentario existente en `index.html` (línea ~65, sobre el preload de `manecillas-del-recuerdo-3d-transparent.png`) documentaba correctamente cuál es el LCP **para un visitante que repite** (con `dp-intro-seen` ya en `sessionStorage`, la intro se oculta al instante) — pero no contemplaba que un visitante **nuevo** (la mayoría del tráfico real, y lo único que Lighthouse/PageSpeed miden siempre, porque arrancan con almacenamiento limpio) ve primero la intro a pantalla completa, y su vídeo/poster es el elemento más grande pintado.

Ese vídeo/poster no tenía ninguna pista de prioridad de carga (`fetchpriority`) ni preload dedicado — competía por ancho de banda con otros dos recursos que sí llevaban `fetchpriority="high"` (el preload del hero de Home y el logo del masthead), ninguno de los cuales es siquiera visible durante la intro. Bajo esa contención, cargar el poster tardaba lo suficiente para arrastrar el LCP a los 17,3 s medidos.

### Corrección aplicada

En `index.html`:
- Añadido `fetchpriority="high"` al propio `<video class="intro__video">`.
- Añadido `<link rel="preload" as="image" href="/assets/hero-tinta-poster.jpg?v=2" fetchpriority="high">` en `<head>`, junto al preload ya existente para el visitante que repite, con un comentario explicando por qué ambos coexisten (dos rutas de visitante distintas, cada preload solo se consume en una de ellas).

Verificado localmente: el poster ahora se solicita de inmediato junto con el vídeo, con la prioridad correcta reflejada en el DOM. No se ha podido volver a ejecutar PageSpeed Insights contra producción todavía porque el fix está en una rama sin desplegar — pendiente medir el LCP real tras el despliegue.

## Otros hallazgos de la misma auditoría (sin tocar todavía)

- **Cachear con más agresividad activos estáticos** — ahorro estimado 3608 KiB. Esto depende de las cabeceras `Cache-Control`/`Expires` que sirve el hosting/CDN (Cloudflare Pages), no de nada editable en el HTML. Pendiente de revisar la configuración de caché del hosting.
- **Solicitudes que bloquean el renderizado** — ahorro estimado ~2120 ms. Candidatas probables: las hojas de estilo `<link rel="stylesheet">` síncronas en `<head>` (algunas ya usan `<link rel="preload" as="style">` pero eso no las hace no-bloqueantes). Requeriría revisar cuáles pueden diferirse con el patrón `media="print" onload="this.media='all'"` sin romper el primer pintado real.
- **Mejorar la entrega de imágenes** — ahorro estimado 2260 KiB. Candidatas: imágenes servidas más grandes de lo necesario para el viewport móvil, o sin `srcset`/formatos modernos en todas partes.
- **Minificar CSS/JS** — ahorros pequeños (11-17 KiB), baja prioridad.
- **Imágenes sin `width`/`height` explícitos** — puede afectar a CLS en condiciones reales aunque aquí midió 0; revisar cuáles.
- **Tamaño total de red: 3980 KiB** en la carga inicial de Home — cifra a vigilar si sigue creciendo.

Ninguno de estos bloquea CI hoy: `lighthouserc.json` ya vigila performance/LCP en Home y otras rutas clave, pero como `warn`, no `error` (`categories:performance` con `minScore: 0.85` y `largest-contentful-paint` con `maxNumericValue: 3500` — este mismo LCP de 17,3s ya debería estar generando ese warning en cada build, simplemente sin bloquear el merge).

## Hallazgo menor: categoría "Navegación agéntica" (2/3)

PageSpeed Insights ahora incluye una categoría experimental ("aún está en desarrollo y puede cambiar", según su propio texto) que valida si `llms.txt` sigue ciertas recomendaciones para que agentes de IA naveguen el sitio. Salió en 2/3, con el aviso "llms.txt no sigue las recomendaciones" pero sin detalle expandido capturado en esta sesión. Dado que la propia categoría se declara inestable/experimental y no forma parte de Core Web Vitals ni de señales de ranking establecidas, se deja documentado como pendiente de baja prioridad — no se ha tocado `llms.txt` por esto todavía. Revisar de nuevo cuando la categoría salga de fase experimental o si `docs/ai-discoverability/` ya cubre este mismo punto en detalle.

## Próximos pasos

1. Desplegar el fix de LCP y volver a medir con PageSpeed Insights para confirmar la mejora real (objetivo: LCP por debajo de 3,5s, el umbral que ya usa `lighthouserc.json`).
2. Revisar cabeceras de caché del hosting (Cloudflare) para el ahorro de 3608 KiB.
3. Auditar qué hojas de estilo síncronas en `<head>` pueden diferirse sin causar FOUC.
4. Revisar compresión/dimensionado de imágenes pesadas de Home.
