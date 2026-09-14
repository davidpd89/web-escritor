# Rendimiento (PageSpeed Insights / Lighthouse) — auditoría 2026-09-09

Fecha de revisión: 2026-09-09

Estado: `INTRO_GATE_HYPOTHESIS_REFUTED · VIDEO_ELEMENT_RENDER_DELAY_CONFIRMED · ROOT_CAUSE_STILL_OPEN · PRIORITY_HINTS_CORRECTED_NO_MEASURABLE_LCP_IMPACT · CACHE_LIFETIMES_PENDING · IMAGE_DELIVERY_PENDING · AGENTIC_NAV_EXPERIMENTAL_LOW_PRIORITY`

**Corrección importante (2026-09-14, v4 — prueba causal ejecutada, hipótesis de la intro descartada)**: se ejecutó por fin la prueba A/B controlada que las versiones v2/v3 de este documento dejaban pendiente. Resultado: **la hipótesis de que el `setTimeout` de la intro (9,6s) causa el `Render Delay` queda refutada por evidencia directa y repetida**. Ver la sección "Prueba causal ejecutada" más abajo para metodología y datos completos. El `Render Delay` es real y sigue dominando el LCP, pero su causa es otra: algo en el propio elemento `<video>` (autoplay + `preload="auto"`, decodificación bajo red móvil limitada) retiene la finalización del LCP durante ~3,2s de forma consistente, **independientemente de si la intro se cierra a los 9,6s, al segundo, o se omite por completo**. Las tres opciones de producto sobre el timeout de la intro (sección de abajo) quedan **sin sustento para mejorar el LCP** — pueden seguir siendo deseables por UX/accesibilidad, pero no resuelven este problema de rendimiento.

**Corrección importante (2026-09-09, v2)**: el cierre original de esta auditoría diagnosticó mal la causa del LCP de 17,3s y lo marcó `LCP_FIXED`. Una revisión externa (GPT) señaló, con razón, varios problemas reales en ese cierre — que a su vez llevaron a un diagnóstico más profundo que cambia la conclusión por completo. Ver "Historial de la investigación" más abajo para la trazabilidad completa. **El fix de prioridad de carga es correcto y se mantiene, pero no explica el LCP malo — la causa real es otra y sigue sin resolverse.**

## Por qué esto importa para posicionamiento

Google usa las Core Web Vitals (LCP, INP, CLS) como señal de "page experience" en el ranking. No es el factor dominante, pero a paridad de contenido puede inclinar la balanza, y un LCP muy malo también empeora la percepción real de velocidad para cualquier visitante que llega desde una búsqueda.

## Prueba causal ejecutada (2026-09-14): la intro NO es la causa

`assets/v1-shell.js`, función `initIntro()`:

```js
let fallback = setTimeout(doEnter, reduced ? 5000 : 9600);
```

La intro a pantalla completa de Home (`<div class="intro">`, `z-index:900`, `background:#000`, cubre todo el viewport) se cierra automáticamente al pulsar "Entrar" o pasados 9,6 segundos reales sin pulsar nada (5s con `prefers-reduced-motion`). Las versiones v2/v3 de este documento planteaban esto como la hipótesis más probable para el `Render Delay` que domina el LCP, pero dejaban explícitamente pendiente una prueba A/B real antes de darlo por confirmado.

### Por qué las medidas anteriores (tabla de la v2) no eran una prueba causal válida

Las medidas de la tabla original se tomaron con `node_modules/.bin/lighthouse` sin especificar `--throttling-method`, que por defecto usa `simulate`: Lighthouse captura un trace SIN throttling real y luego estima ("Lantern") cómo se vería bajo red/CPU móvil simuladas. Esa simulación modela cadenas de dependencia de red y tareas de CPU, pero **no modela de forma fiable un `setTimeout` de UI arbitrario que no depende de ninguna carga de red** — por eso los números de esa tabla (14,4s / 22,2s de Render Delay) resultaron ser un artefacto de la simulación, coincidente en magnitud con el timeout de 9,6s pero no causado por él, como demuestra la prueba siguiente.

### Metodología de la prueba real

Se sirvió el sitio en local (`python -m http.server`) y se ejecutó `node_modules/.bin/lighthouse` contra `http://127.0.0.1:4187/` con **`--throttling-method=devtools`** (throttling real de red/CPU vía DevTools Protocol — 1.6 Mbps de bajada, 150ms RTT, CPU×4 — no una estimación posterior), inspeccionando el JSON crudo del audit `largest-contentful-paint-element` (fases TTFB / Load Delay / Load Time / Render Delay) en cada variante. Cuatro variantes, cada una con una única variable cambiada:

| Variante | Cambio | LCP total | Render Delay |
|---|---|---|---|
| A — actual | `setTimeout(doEnter, 9600)` sin tocar | **5015,9 ms** | 3202,8 ms (64%) |
| B — timeout corto | `setTimeout(doEnter, 1000)` | **5090,3 ms** | 3250,7 ms (64%) |
| C — intro omitida | `sessionStorage.dp-intro-seen` forzado a `true` (visitante recurrente simulado, intro nunca se muestra) | **4997,2 ms** | 3181,5 ms (64%) |
| D — sin autoplay | Atributo `autoplay` retirado del `<video>` (JS igual llama a `.play()`, ver más abajo) | **4699,9 ms** | 2862,8 ms (61%) |

Las variantes A, B y C —que cambian radicalmente cuándo o si la intro se cierra— dan un LCP prácticamente idéntico (diferencia máxima de 93ms, dentro del ruido normal entre ejecuciones). Si el timeout de la intro fuera la causa, reducirlo de 9600ms a 1000ms (variante B) o eliminarlo por completo (variante C) debería haber reducido el LCP en varios segundos. No lo hizo. **Esto refuta la hipótesis de forma directa y repetida.**

Cada test cambió una sola línea en un checkout local, se verificó servida (`curl` contra el HTML/JS servido) y se revirtió inmediatamente después de medir — no se ha desplegado ningún cambio de comportamiento a `main` a partir de esta investigación.

### Qué es realmente el `Render Delay`, según esta misma prueba

Inspeccionando `network-requests` del trace de la variante A: el póster (`hero-tinta-poster.jpg`, 53 KB) termina de descargarse a los 1812ms — coincide con el final de la fase `Load Time`. El LCP no se registra hasta los 5016ms: una brecha real de ~3,2s **después** de que el recurso ya esté completamente cargado. El elemento LCP reportado en las cuatro variantes es siempre `body > div.intro > div.intro__stage > video.intro__video` — nunca el hero real de Home visible tras cerrar la intro (consistente con que el vídeo, a pantalla completa, nunca es superado en tamaño por ningún elemento posterior). El vídeo completo (630 KB) tarda ~12,9s en descargarse bajo el throttling de la prueba (empieza a los 2818ms, termina a los 15704ms) — muy por detrás del LCP registrado a los 5016ms, así que la descarga completa del vídeo tampoco es la explicación directa.

La variante D (sin `autoplay`) apenas cambia el resultado porque `assets/v1-shell.js` (`initHeroVideo()`) llama a `video.play()` por script incondicionalmente, así que retirar el atributo HTML no impide la reproducción real. La causa más probable en este punto —sin confirmar todavía— es un comportamiento propio de Chrome para elementos `<video>` con `poster` bajo red limitada: el candidato a LCP parece no finalizarse hasta que el vídeo alcanza cierto estado de reproducción/decodificación, no solo cuando el póster termina de descargarse. web.dev desaconseja explícitamente usar `<video>` como elemento LCP por este tipo de comportamiento poco predecible.

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
- **Preconectar con `gc.zgo.at` y `tracker.metricool.com`** — ahorro estimado de LCP de 470ms y 310ms respectivamente, según el propio árbol de dependencias de PageSpeed Insights. **Resuelto (2026-09-14)**: `tracker.metricool.com` añadido junto al preconnect ya existente de `gc.zgo.at` en las 23 páginas que lo tenían (ver PR de `perf/metricool-preconnect`). Ambos están ahora en `main`.
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
5. **Cuarta pasada (esta, 2026-09-14)**: se ejecutó por fin la prueba A/B con throttling real (`--throttling-method=devtools`, no `simulate`). Resultado: la hipótesis de la intro queda refutada — el LCP es idéntico (±93ms) con timeout de 9600ms, 1000ms o con la intro omitida por completo. Se descubrió además que las medidas anteriores (tabla de la v2) usaban `simulate` por defecto, que no modela de forma fiable un `setTimeout` de UI ajeno a la carga de red — de ahí la coincidencia engañosa entre el timeout de 9,6s y el Render Delay medido entonces. La causa real señalada por esta prueba es el propio elemento `<video>` (autoplay + `preload="auto"`, decodificación bajo red limitada), no la intro. Queda abierta una investigación específica sobre por qué Chrome tarda ~3,2s en finalizar el LCP de este `<video>` incluso con el póster ya cargado.

## Próximos pasos

1. **Investigar el `Render Delay` del `<video>` en sí** (nueva causa identificada 2026-09-14): probar sustituir el elemento LCP-candidato por una `<img>` estática (el póster) en vez de un `<video poster>` — web.dev desaconseja `<video>` como elemento LCP precisamente por este tipo de comportamiento. Si una `<img>` equivalente registra LCP nada más cargar (sin los ~3,2s de Render Delay), confirma que el problema es específico de cómo Chrome trata `<video>` bajo red limitada, no del contenido en sí. Repetir con `--throttling-method=devtools` para que sea comparable con los datos de esta sesión.
2. Si el paso 1 confirma la causa, valorar: reducir `preload` real (más allá del atributo HTML, evitando que `initHeroVideo()` fuerce `play()` antes de que el LCP se resuelva), o servir un poster de mayor calidad como LCP real y diferir el vídeo hasta después del primer paint.
3. Una vez aplicado y verificado localmente, volver a medir con PageSpeed Insights en producción (varias ejecuciones, mediana, no una sola) antes de marcar cualquier estado como `_FIXED`.
4. Revisar cabeceras de caché del hosting (Cloudflare) para el ahorro de ~3,4-3,6 MB.
5. Auditar qué hojas de estilo síncronas en `<head>` pueden diferirse sin causar FOUC.
6. Revisar compresión/dimensionado de imágenes pesadas de Home.
7. (Por UX, no por LCP) Si David quiere acortar o hacer no bloqueante el timeout de la intro, ver la sección de decisión de producto de arriba — sigue siendo una opción válida, solo que ya no se justifica como fix de rendimiento.
