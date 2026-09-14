# Rendimiento (PageSpeed Insights / Lighthouse) — auditoría 2026-09-09

Fecha de revisión: 2026-09-14 (auditoría original 2026-09-09; ver "Historial de la investigación" — el documento se ha rehecho materialmente varias veces desde entonces)

Estado: `VIDEO_LCP_RENDER_DELAY_CONFIRMED · TIMEOUT_EFFECT_NOT_OBSERVED_N5 · PLAYBACK_STATE_NOT_OBSERVED_AS_CAUSE_N5 · NAIVE_INTRO_REMOVAL_REGRESSES_LCP_VIA_HERO_DISCOVERY_PATH · ROOT_CAUSE_OPEN · PRIORITY_HINTS_CORRECTED_NO_MEASURABLE_LCP_IMPACT · CACHE_LIFETIMES_PENDING · IMAGE_DELIVERY_PENDING · AGENTIC_NAV_EXPERIMENTAL_LOW_PRIORITY`

**Corrección importante (2026-09-14, v5 — la v4 sobreafirmaba lo demostrado; prueba repetida con rigor real)**: una revisión externa (GPT) señaló, con razón, tres problemas concretos en la v4 de este documento: (a) una sola medición por variante no sostiene la expresión "evidencia directa y repetida"; (b) la variante C de la v4 ("intro omitida") solo ocultaba la intro por JS después de cargar — el `<video>` seguía en el HTML inicial y seguía siendo el elemento LCP reportado, así que no aislaba nada; (c) la variante D ("sin autoplay") solo quitaba el atributo HTML mientras `initHeroVideo()` seguía llamando a `video.play()` por script, así que tampoco aislaba la reproducción real. Además, la v4 afirmaba que "web.dev desaconseja explícitamente `<video>` como elemento LCP" — comprobado directamente contra la documentación oficial, eso es **falso**: web.dev lista `<video>` (tiempo de carga del poster o de presentación del primer frame, lo que ocurra antes) como uno de los tipos de elemento candidatos a LCP, sin desaconsejarlo.

Se repitió la prueba con las tres variables realmente aisladas y 5 ejecuciones por variante (mediana + rango, no una muestra). Resultado, con el nivel de certeza que corresponde a n=5 en un entorno local: **el timeout de la intro y el estado de reproducción del vídeo siguen sin mostrar un efecto observable sobre el `Render Delay` ni sobre el LCP total** — la diferencia entre medianas de variantes que cambian esas dos variables es menor que el rango de ruido intra-variante. Pero la variante que sí aísla de verdad "intro ausente del markup" reveló algo que la v4 nunca pudo ver, porque nunca aisló nada: quitar el `<video>` de la candidatura a LCP no mejora el LCP, lo **empeora en ~4×** (mediana 21,7s vs ~5,1-5,4s), porque la imagen de hero real de Home solo se descubre tras una cadena de dos scripts secuenciales y el script de preload condicional de esta página sigue asumiendo que la intro existe. Ver "Prueba causal ejecutada" para metodología y tabla completa. **La causa raíz del `Render Delay` del `<video>` sigue sin identificarse** — solo se ha descartado qué NO la causa.

**Corrección importante (2026-09-09, v2)**: el cierre original de esta auditoría diagnosticó mal la causa del LCP de 17,3s y lo marcó `LCP_FIXED`. Una revisión externa (GPT) señaló, con razón, varios problemas reales en ese cierre — que a su vez llevaron a un diagnóstico más profundo que cambia la conclusión por completo. Ver "Historial de la investigación" más abajo para la trazabilidad completa. **El fix de prioridad de carga es correcto y se mantiene, pero no explica el LCP malo — la causa real es otra y sigue sin resolverse.**

## Por qué esto importa para posicionamiento

Google usa las Core Web Vitals (LCP, INP, CLS) como señal de "page experience" en el ranking. No es el factor dominante, pero a paridad de contenido puede inclinar la balanza, y un LCP muy malo también empeora la percepción real de velocidad para cualquier visitante que llega desde una búsqueda.

## Prueba causal ejecutada (2026-09-14, v5 — variables realmente aisladas, n=5)

`assets/v1-shell.js`, función `initIntro()`:

```js
let fallback = setTimeout(doEnter, reduced ? 5000 : 9600);
```

La intro a pantalla completa de Home (`<div class="intro">`, `z-index:900`, `background:#000`, cubre todo el viewport) se cierra automáticamente al pulsar "Entrar" o pasados 9,6 segundos reales sin pulsar nada (5s con `prefers-reduced-motion`). Las versiones v2/v3 de este documento planteaban esto como la hipótesis más probable para el `Render Delay` que domina el LCP, pero dejaban explícitamente pendiente una prueba A/B real antes de darlo por confirmado.

### Por qué las medidas anteriores (tabla de la v2) no eran una prueba causal válida

Las medidas de la tabla original se tomaron con `node_modules/.bin/lighthouse` sin especificar `--throttling-method`, que por defecto usa `simulate`: Lighthouse captura un trace SIN throttling real y luego estima ("Lantern") cómo se vería bajo red/CPU móvil simuladas. Esa simulación modela cadenas de dependencia de red y tareas de CPU, pero **no modela de forma fiable un `setTimeout` de UI arbitrario que no depende de ninguna carga de red** — por eso los números de esa tabla (14,4s / 22,2s de Render Delay) resultaron ser un artefacto de la simulación, coincidente en magnitud con el timeout de 9,6s pero no causado por él, como demuestra la prueba siguiente.

### Metodología de la prueba real

Se sirvió el sitio en local (`python -m http.server`, puerto 4187) y se ejecutó `node_modules/.bin/lighthouse 12.6.1` contra `http://127.0.0.1:4187/` con **`--throttling-method=devtools`** (throttling real de red/CPU vía DevTools Protocol — 1.6 Mbps de bajada, 150ms RTT, CPU×4), misma máquina y mismo Chrome para las cuatro variantes, **5 ejecuciones por variante** (20 en total), extrayendo del JSON crudo de cada run: el audit `largest-contentful-paint-element` (elemento LCP + fases TTFB/Load Delay/Load Time/Render Delay), `network-requests` (fin de descarga del póster) y `user-timings` (marcas `performance.mark()` añadidas temporalmente en `assets/v1-shell.js` en `doEnter`, `intro.hidden = true`, y los eventos `loadedmetadata`/`loadeddata`/`playing` del vídeo — reveladas solo como diagnóstico, revertidas junto con el resto de cambios de esta prueba). A diferencia de la v4, cada variante aísla de verdad la variable que dice aislar:

- **A — baseline**: sin tocar nada.
- **B — timeout corto**: `setTimeout(doEnter, 1000)` en vez de `9600` (línea real de código, no un flag de sessionStorage).
- **C — intro ausente del markup inicial**: el bloque `<div class="intro">…</div>` completo eliminado del HTML servido — el `<video>` no existe en el DOM en ningún momento, no solo oculto por JS después.
- **D — vídeo realmente sin reproducción**: atributo `autoplay` retirado del `<video>` **y** `initHeroVideo()` neutralizada con un `return` inmediato, de forma que `video.play()` nunca se invoca.

Cada variante se sirvió, se confirmó con `curl` que el HTML/JS servido reflejaba el cambio esperado (para C, cero coincidencias de `class="intro"` en el HTML; para D, el `<video>` servido sin el atributo `autoplay`), se midió 5 veces, y se revirtió con `git checkout --` antes de pasar a la siguiente — no se ha desplegado ningún cambio de comportamiento a `main` a partir de esta investigación.

### Resultados (mediana de 5 ejecuciones, rango entre paréntesis)

| Variante | Elemento LCP | LCP total | Render Delay |
|---|---|---|---|
| A — baseline (timeout 9600ms) | `<video>` | **5366,6 ms** (4993–5461) | 3496,6 ms (3163–3634) |
| B — timeout 1000ms | `<video>` | **5080,4 ms** (5071–5396) | 3276,4 ms (3236–3544) |
| C — intro ausente del markup | `<img>` (hero real de Home) | **21686,7 ms** (21308–22160) | 21,9 ms (11–31) |
| D — vídeo sin reproducción (no autoplay, no `.play()`) | `<video>` | **5120,7 ms** (5028–5495) | 3299,1 ms (3208–3654) |

### Lectura honesta de estos datos

**A, B y D — mismo elemento LCP, sin efecto observable de las variables cambiadas.** Las medianas de LCP (5366,6 / 5080,4 / 5120,7 ms) y de Render Delay (3496,6 / 3276,4 / 3299,1 ms) están dentro del rango de ruido intra-variante de cada una (rangos de 325-470ms en LCP). Ni acortar el timeout a 1000ms (B) ni impedir por completo la reproducción real del vídeo — sin `autoplay`, sin `.play()` (D) — mueve el Render Delay de forma perceptible. Esto descarta dos hipótesis a la vez con n=5: ni el timeout de la intro ni el estado de reproducción/decodificación del vídeo son la causa del Render Delay.

El dato de `user-timings` refuerza esto: en A y B, la marca `dp-lcp-test-playing` (el evento `playing` del vídeo) se registra **después** de que el LCP ya se haya finalizado (p. ej., run 1 de A: LCP a 4993ms, `playing` a 5477ms). El LCP de este `<video>` se resuelve antes de que el vídeo llegue siquiera a reproducirse — lo que descarta directamente la hipótesis de que Chrome espera a un estado de reproducción concreto antes de finalizar el LCP. Las marcas `loadedmetadata`/`loadeddata` no llegaron a capturarse: con `preload="auto"`, esos eventos del vídeo ocurren antes de que el script diferido (`v1-shell.js`) llegue a registrar los listeners, así que esta instrumentación concreta no pudo aislar esa fase — queda como limitación conocida de esta prueba, no como dato.

**C — hallazgo nuevo que la v4 nunca pudo ver.** Cuando el `<video>` no existe en el DOM, el LCP no mejora: **empeora ~4×** (mediana 21,7s frente a ~5,1-5,4s), y el elemento LCP pasa a ser la imagen de portada de Home (`manecillas-del-recuerdo-3d-transparent.png`), con un Render Delay casi nulo (~22ms) pero una fase de descubrimiento/carga previa enorme. La razón: el script de preload condicional en `<head>` de `index.html` decide QUÉ imagen precargar según `sessionStorage.dp-intro-seen`, asumiendo que la intro existe; al quitar la intro sin tocar ese script, ninguna de las dos imágenes reales se precarga a tiempo, y la imagen de hero de Home solo se descubre tras que `v1-shell.js` (diferido) importe dinámicamente `v1-home-editorial-v3.js`, que a su vez inserta la imagen — una cadena de dos scripts secuenciales bajo red limitada. **Esto no significa que quitar la intro sea malo para el LCP en general** — significa que esta prueba, al aislar solo esa variable, expone una dependencia real (el preload condicional) que cualquier cambio de producto tendría que arreglar a la vez. Es exactamente el tipo de riesgo que la v4 —al no aislar nada de verdad— nunca pudo detectar.

**Conclusión combinada**: se descarta con razonable confianza (n=5, no n=1) que el timeout de la intro o el estado de reproducción del vídeo expliquen el Render Delay. La causa raíz de por qué Chrome tarda ~3,2-3,6s en finalizar el LCP de este `<video>` concreto —incluso sin reproducirse nunca— **sigue sin identificarse**. El vídeo/poster es un candidato LCP válido según la documentación oficial de web.dev, que no desaconseja su uso — la explicación probablemente esté en otro factor no probado todavía (decodificación del propio poster bajo CPU×4, algún comportamiento de compositing específico de `<video>`, o el tamaño/formato del poster), pendiente de la investigación de "Próximos pasos".

## Decisión de producto sobre el timeout de la intro: sigue siendo válida por UX, ya no por LCP

La intro cinemática es una decisión de diseño/marca deliberada (vídeo de tinta + "Entrar"), no un bug. La prueba causal de arriba muestra que tocar su timeout **no mueve el LCP** — así que ninguna de las opciones siguientes debe justificarse ya como una mejora de rendimiento. Se mantienen documentadas porque siguen siendo razonables por accesibilidad/UX (una espera de 9,6s sin interacción es larga independientemente del LCP), pero la urgencia/prioridad que tenían como "fix de LCP" desaparece:

1. **Reducir el timeout de 9,6s** (por ejemplo a 3-4s) manteniendo el vídeo/intro tal cual. Mejora el peor caso de espera sin cambiar el diseño, pero no el LCP.
2. **Hacer el cierre no bloqueante** — respetar `prefers-reduced-motion` y la señal `Save-Data` reduciendo o saltando la espera automática para quien ya indica esa preferencia en su navegador (ya se hace parcialmente con `prefers-reduced-motion` → 5s; se podría llevar a 0s en ambos casos). Esto es distinto de detectar bots por `User-Agent`: se basa en una preferencia real declarada por el visitante, no en quién hace la petición.
3. **Aceptar el coste como intencional** — mantener la intro tal cual.

**Descartado explícitamente: saltar la intro solo para user-agents de bots/crawlers (Googlebot, Lighthouse, etc.)**. Una revisión externa (GPT) señaló correctamente que esto es cloaking según la propia definición de Google (servir contenido distinto condicionado al user-agent para mejorar cómo se evalúa la página), con riesgo de penalización. Sigue retirado de las opciones, y ahora doblemente descartado: ni siquiera resolvería el LCP.

No se ha aplicado ninguna de las tres opciones porque siguen siendo decisiones de producto/UX, no correcciones técnicas de rendimiento. Queda pendiente de que David decida si quiere acortar la espera por razones de experiencia de usuario, con la información correcta de que no es un fix de LCP.

## Fix de prioridad de carga — correcto, mantenido, pero sin impacto medible en el LCP

Se mantiene porque es una corrección real y bien fundamentada por su cuenta, no porque resuelva el problema anterior:

- **`fetchpriority="high"` en `<video>` retirado**: no es un atributo válido para `<video>` según el estándar HTML (MDN documenta que `fetchpriority` solo aplica a `<img>`, `<link>` y `<script>`) — señalado correctamente en revisión externa. No tenía ningún efecto garantizado y se ha quitado para no documentar una optimización inexistente.
- **Preload condicional del poster/hero**: la versión anterior de este fix añadía DOS `<link rel="preload" ... fetchpriority="high">` incondicionales (poster de la intro + hero de Home), que se solicitan siempre los dos sin importar cuál se vaya a usar realmente — contradiciendo el propio objetivo de "priorizar", ya que compiten entre sí por el mismo ancho de banda limitado (web.dev advierte explícitamente de este patrón). Corregido con un script síncrono en el `<head>` que lee `sessionStorage.dp-intro-seen` y emite mediante `document.write()` solo el `<link rel="preload">` que corresponde a esa visita — nunca los dos. Regenerado el CSP del sitio (`python scripts/build-site-shell.py`) para incluir el hash del nuevo script inline; verificado en local que no genera ninguna violación de CSP y que cada ruta de visitante recibe exactamente un preload.
- Verificado con Lighthouse local (tabla de arriba) que este fix sí reduce el tiempo de carga del propio recurso a menos de 700ms — funciona exactamente como se pretendía — pero no mueve el LCP total porque el cuello de botella real está en otra fase completamente distinta (`Render Delay`, no `Load Time`).

## Otros hallazgos de la misma auditoría (sin tocar todavía)

- **Cachear con más agresividad activos estáticos** — ahorro estimado 3399-3608 KiB. Depende de las cabeceras `Cache-Control`/`Expires` del hosting/CDN (Cloudflare Pages), no de nada editable en el HTML.
- **Mejorar la entrega de imágenes** — ahorro estimado 2260 KiB. Candidatas: imágenes servidas más grandes de lo necesario para el viewport móvil, o sin `srcset`/formatos modernos en todas partes.
- **Solicitudes que bloquean el renderizado** — ahorro estimado 1790-2120 ms. Candidatas probables: hojas de estilo `<link rel="stylesheet">` síncronas en `<head>`.
- **Preconectar con `gc.zgo.at` y `tracker.metricool.com`** — PageSpeed Insights **estimó** un ahorro de conexión de ~470ms y ~310ms respectivamente en su propio árbol de dependencias (no una mejora medida por nosotros antes/después). **Acción aplicada (2026-09-14)**: `tracker.metricool.com` añadido junto al preconnect ya existente de `gc.zgo.at` en las 23 páginas que lo tenían (PR `perf/metricool-preconnect`, mergeada en `main`). Esto resuelve la discrepancia de que el preconnect se había discutido pero nunca añadido al HTML — no equivale a una mejora de LCP demostrada, y en cualquier caso el LCP real de Home está dominado por el `Render Delay` del `<video>` (ver más arriba), no por el tiempo de conexión a este tracker. Si se quiere cuantificar el beneficio real de este preconnect, haría falta una medición antes/después controlada, aparte de la investigación del vídeo.
- **Minificar CSS/JS** — ahorros pequeños (11-17 KiB), baja prioridad.
- **Imágenes sin `width`/`height` explícitos** — puede afectar a CLS en condiciones reales aunque aquí midió 0.
- **Tamaño total de red: ~3,7-4 MB** en la carga inicial de Home.

Ninguno de estos bloquea CI hoy: `lighthouserc.json` ya vigila performance/LCP en Home y otras rutas clave, pero como `warn`, no `error` (`categories:performance` con `minScore: 0.85` y `largest-contentful-paint` con `maxNumericValue: 3500` — este mismo LCP debería estar generando ese warning en cada build sin bloquear el merge).

## Hallazgo menor: categoría "Navegación agéntica" (2/3)

PageSpeed Insights incluye una categoría experimental ("aún está en desarrollo y puede cambiar") que valida si `llms.txt` sigue ciertas recomendaciones para agentes de IA. Salió en 2/3 ("llms.txt no sigue las recomendaciones"), sin detalle expandido capturado todavía. Dado que la propia categoría se declara inestable y no es parte de Core Web Vitals ni de señales de ranking establecidas, queda documentado como pendiente de baja prioridad.

## Historial de la investigación (para no repetir el mismo error de diagnóstico)

1. **Primera pasada**: PageSpeed Insights identificó el vídeo de la intro como elemento LCP a 17,3s. Se asumió (incorrectamente) que era un problema de prioridad de carga y se aplicó `fetchpriority="high"` al `<video>` más un preload incondicional del hero de Home — cerrado como `LCP_FIXED` sin volver a medir.
2. **Revisión externa (GPT)** señaló, correctamente: (a) `fetchpriority` no existe como atributo válido en `<video>`; (b) los dos preloads incondicionales compiten entre sí; (c) no se puede llamar "arreglado" a algo nunca vuelto a medir; (d) había que investigar el waterfall real (TTFB/discovery/poster/vídeo) antes de seguir con microoptimizaciones, porque un vídeo de 630 KB tardando 17s es demasiado anómalo para asumir que la prioridad por sí sola lo explica.
3. **Segunda pasada**: se investigó con Lighthouse local y el desglose de fases del propio audit de LCP, encontrando que `Render Delay` — no la carga del recurso — es el 79-97% del tiempo total en toda ejecución. Se corrigieron los dos problemas técnicos reales señalados (atributo inválido, preloads en competencia) y se planteó la intro como causa probable, pero el cierre se redactó como "confirmado" sin haber aislado la variable con una prueba real.
4. **Tercera pasada (2026-09-10)**: una nueva revisión externa (GPT) señaló que "confirmado" era una sobreafirmación — la intro es la hipótesis más plausible, no un hecho demostrado — y además que la opción de "saltar la intro para bots" era cloaking. Se corrigió el estado a `INTRO_GATE_SUSPECTED · CAUSAL_TEST_PENDING`, se retiró esa opción, y se definió la prueba A/B pendiente para confirmar o descartar la causa antes de tomar ninguna decisión de producto.
5. **Cuarta pasada (2026-09-14, v4)**: se ejecutó una prueba A/B con throttling real (`--throttling-method=devtools`, no `simulate`), una sola medición por variante. Se concluyó, en exceso de lo que los datos sostenían, que la hipótesis de la intro quedaba "refutada por evidencia directa y repetida". Se descubrió correctamente que las medidas anteriores (tabla de la v2) usaban `simulate` por defecto, que no modela de forma fiable un `setTimeout` de UI ajeno a la carga de red.
6. **Quinta pasada (esta, 2026-09-14, v5)**: una nueva revisión externa (GPT) señaló, con razón, que la v4 sobreafirmaba con n=1 y que dos de sus cuatro variantes no aislaban de verdad lo que decían aislar (C solo ocultaba la intro por JS sin quitar el `<video>` del DOM; D solo quitaba el atributo `autoplay` mientras el JS seguía llamando a `.play()`), además de una afirmación falsa sobre la postura de web.dev respecto a `<video>` como candidato LCP. Se repitió la prueba con las cuatro variables realmente aisladas y 5 ejecuciones por variante (mediana + rango). Resultado: se mantiene, con más confianza, que el timeout y el estado de reproducción del vídeo no mueven el Render Delay — pero se descubre además que quitar el `<video>` de la candidatura a LCP sin arreglar el script de preload condicional **empeora el LCP ~4×** (pasa a depender de una cadena de dos scripts secuenciales para descubrir la imagen de hero real). La causa raíz del Render Delay del `<video>` sigue sin identificarse; solo se ha acotado con más rigor qué no la explica.

## Próximos pasos

1. **Investigar el `Render Delay` del `<video>` en sí** (root cause todavía abierto tras descartar timeout y estado de reproducción, 2026-09-14 v5): probar sustituir el elemento LCP-candidato por una `<img>` estática (el póster) en vez de un `<video poster>`, con la propia intro presente y sin tocar el script de preload condicional — a diferencia de la variante C de esta prueba, que quitó el vídeo por completo y expuso un problema distinto (descubrimiento lento de la imagen de hero real). Si una `<img>` equivalente EN EL MISMO SITIO que el vídeo (mismo timing de preload) registra LCP nada más cargar el recurso, confirma que el problema es específico de cómo Chrome trata `<video poster>`, no del contenido en sí. 5 ejecuciones, mediana + rango, `--throttling-method=devtools`, para ser comparable con los datos de esta sesión.
2. **Antes de proponer quitar o sustituir la intro/vídeo en producción**: arreglar primero el script de preload condicional de `index.html` para que, si algún día no hay intro que mostrar, precargue directamente la imagen de hero de Home en vez de asumir que la intro existe — la variante C de esta prueba demostró que sin ese arreglo el LCP empeora ~4×.
3. Si el paso 1 confirma la causa, valorar: reducir `preload` real (más allá del atributo HTML, evitando que `initHeroVideo()` fuerce `play()` antes de que el LCP se resuelva), o servir un poster de mayor calidad como LCP real y diferir el vídeo hasta después del primer paint.
5. Una vez aplicado y verificado localmente, volver a medir con PageSpeed Insights en producción (varias ejecuciones, mediana, no una sola) antes de marcar cualquier estado como `_FIXED`.
6. Revisar cabeceras de caché del hosting (Cloudflare) para el ahorro de ~3,4-3,6 MB.
7. Auditar qué hojas de estilo síncronas en `<head>` pueden diferirse sin causar FOUC.
8. Revisar compresión/dimensionado de imágenes pesadas de Home.
9. (Por UX, no por LCP) Si David quiere acortar o hacer no bloqueante el timeout de la intro, ver la sección de decisión de producto de arriba — sigue siendo una opción válida, solo que ya no se justifica como fix de rendimiento.

<!-- test/docs-only-skip-check: trivial docs-only change to validate the lighthouse/visual-regression fast-skip path; this branch is closed and deleted without merging -->
