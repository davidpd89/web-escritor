# Rendimiento (PageSpeed Insights / Lighthouse) — auditoría 2026-09-09

Fecha de revisión: 2026-09-09

Estado: `LCP_RENDER_DELAY_CONFIRMED · INTRO_GATE_SUSPECTED · CAUSAL_TEST_PENDING · PRIORITY_HINTS_CORRECTED_NO_MEASURABLE_LCP_IMPACT · PRODUCT_DECISION_NEEDED · CACHE_LIFETIMES_PENDING · IMAGE_DELIVERY_PENDING · AGENTIC_NAV_EXPERIMENTAL_LOW_PRIORITY`

**Corrección importante (2026-09-10, v3)**: una segunda revisión externa (GPT) señaló que el punto anterior sobreafirmaba la causa raíz como "confirmada". Lo único demostrado con evidencia es que `Render Delay` domina el LCP (79-97% del tiempo, tabla más abajo); el vínculo causal específico con el `setTimeout` de 9,6s de la intro es la explicación más probable pero **no está probado**, porque el CSS mantiene el vídeo visible desde el arranque de la página (no hay un `display:none` que se levante al pasar la intro) y no se ha ejecutado ninguna prueba A/B controlada que aísle esa variable. El estado correcto es `INTRO_GATE_SUSPECTED`, no confirmado, hasta completar la prueba causal descrita en "Próximos pasos".

**Corrección importante (2026-09-09, v2)**: el cierre original de esta auditoría diagnosticó mal la causa del LCP de 17,3s y lo marcó `LCP_FIXED`. Una revisión externa (GPT) señaló, con razón, varios problemas reales en ese cierre — que a su vez llevaron a un diagnóstico más profundo que cambia la conclusión por completo. Ver "Historial de la investigación" más abajo para la trazabilidad completa. **El fix de prioridad de carga es correcto y se mantiene, pero no explica el LCP malo — la causa real es otra y sigue sin resolverse.**

## Por qué esto importa para posicionamiento

Google usa las Core Web Vitals (LCP, INP, CLS) como señal de "page experience" en el ranking. No es el factor dominante, pero a paridad de contenido puede inclinar la balanza, y un LCP muy malo también empeora la percepción real de velocidad para cualquier visitante que llega desde una búsqueda.

## Causa sospechada (pendiente de prueba causal): la propia intro cinemática podría bloquear el contenido hasta 9,6s

`assets/v1-shell.js`, función `initIntro()`:

```js
let fallback = setTimeout(doEnter, reduced ? 5000 : 9600);
```

La intro a pantalla completa de Home (`<div class="intro">`, `z-index:900`, `background:#000`, cubre todo el viewport) se cierra automáticamente al pulsar "Entrar" **o pasados 9,6 segundos reales sin pulsar nada** (5s con `prefers-reduced-motion`). Lighthouse/PageSpeed nunca interactúan con la página — cargan y esperan — así que en toda auditoría automatizada (y en cualquier visitante real que no haga clic de inmediato) la intro permanece bloqueando la vista durante esos 9,6s completos, más ~820ms de la transición de salida, antes de que aparezca cualquier contenido real. **Esta es la hipótesis más probable, no un hecho demostrado**: el CSS del vídeo lo mantiene visible desde el arranque de la página (no está oculto y revelado al terminar la intro), así que la relación causa-efecto exacta entre el temporizador y el `Render Delay` medido abajo sigue sin aislarse con una prueba controlada — ver "Próximos pasos".

### Qué se demostró y qué no (evidencia real, sin sobreinterpretar)

Se ejecutó Lighthouse localmente (`node_modules/.bin/lighthouse`, sin CLI de terceros) contra producción y contra una copia local con el fix de prioridad aplicado, inspeccionando el desglose de fases del audit `largest-contentful-paint-element` en el JSON crudo (no solo el resumen visual de PageSpeed Insights, que no expone esta tabla con suficiente detalle):

| Ejecución | LCP total | TTFB | Load Delay | Load Time | **Render Delay** |
|---|---|---|---|---|---|
| Producción, sin fix | 18,2 s | 742 ms (4%) | 820 ms (5%) | 2274 ms (12%) | **14 388 ms (79%)** |
| Local, CON el fix de prioridad ya aplicado | 22,9 s | 463 ms (2%) | 24 ms (0%) | 212 ms (1%) | **22 232 ms (97%)** |

`Render Delay` es el tiempo entre "el recurso ya está listo para pintarse" y "el navegador realmente lo pinta". En ambas ejecuciones domina por completo — la carga del recurso (TTFB + Load Delay + Load Time) nunca pasa de ~3,3s, y en la ejecución con el fix aplicado se redujo a menos de 700ms, tal como se esperaba. **Y aun así el LCP total no mejoró — empeoró.** Esto demuestra de forma concluyente que el cuello de botella nunca fue la prioridad de carga del recurso. Lo que **no** demuestra por sí solo es que la intro sea la causa específica del `Render Delay`: solo confirma que algo posterior a la carga del recurso retrasa el pintado. La intro es la explicación más plausible (su temporizador de 9,6s encaja con el orden de magnitud medido), pero sigue siendo una hipótesis sin una prueba A/B que la aísle de otras posibles causas (por ejemplo, trabajo de JS bloqueante en el hilo principal durante la carga).

(La variación entre 14,4s y 22,2s de Render Delay entre ejecuciones es ruido esperado de la limitación de CPU simulada de Lighthouse sobre temporizadores JS reales — no cambia la conclusión: el `Render Delay` es sistemáticamente el 79-97% del LCP en toda ejecución.)

## Esto requiere una decisión de producto, no solo un fix técnico

La intro cinemática es una decisión de diseño/marca deliberada (vídeo de tinta + "Entrar"), no un bug. Acortar, hacerla no bloqueante o eliminar su espera automática de 9,6s mejoraría el LCP directamente, pero cambia la experiencia que ve todo el mundo en la primera visita — no es algo para decidir unilateralmente en una sesión nocturna sin supervisión. Opciones, de menos a más invasiva (todas benefician a **cualquier** visitante, no solo a los crawlers de medición):

1. **Reducir el timeout de 9,6s** (por ejemplo a 3-4s) manteniendo el vídeo/intro tal cual. Mejora el peor caso sin cambiar el diseño.
2. **Hacer el cierre no bloqueante** — respetar `prefers-reduced-motion` y la señal `Save-Data` reduciendo o saltando la espera automática para quien ya indica esa preferencia en su navegador (ya se hace parcialmente con `prefers-reduced-motion` → 5s; se podría llevar a 0s en ambos casos). Esto es distinto de detectar bots por `User-Agent`: se basa en una preferencia real declarada por el visitante, no en quién hace la petición.
3. **Aceptar el coste como intencional** — mantener la intro tal cual y asumir que el LCP de Home será estructuralmente malo mientras exista, documentándolo como una compensación consciente entre marca/experiencia y rendimiento.

**Descartado explícitamente: saltar la intro solo para user-agents de bots/crawlers (Googlebot, Lighthouse, etc.)**. Una revisión externa (GPT) señaló correctamente que esto es cloaking según la propia definición de Google (servir contenido distinto condicionado al user-agent para mejorar cómo se evalúa la página), con riesgo de penalización. Se retira de las opciones; cualquier fix debe beneficiar también a los visitantes humanos reales.

No se ha aplicado ninguna de las tres opciones restantes porque son decisiones de producto, no correcciones técnicas, y además dependen de confirmar primero la causa real (ver "Próximos pasos", prueba A/B pendiente). Queda pendiente de que David decida.

## Fix de prioridad de carga — correcto, mantenido, pero sin impacto medible en el LCP

Se mantiene porque es una corrección real y bien fundamentada por su cuenta, no porque resuelva el problema anterior:

- **`fetchpriority="high"` en `<video>` retirado**: no es un atributo válido para `<video>` según el estándar HTML (MDN documenta que `fetchpriority` solo aplica a `<img>`, `<link>` y `<script>`) — señalado correctamente en revisión externa. No tenía ningún efecto garantizado y se ha quitado para no documentar una optimización inexistente.
- **Preload condicional del poster/hero**: la versión anterior de este fix añadía DOS `<link rel="preload" ... fetchpriority="high">` incondicionales (poster de la intro + hero de Home), que se solicitan siempre los dos sin importar cuál se vaya a usar realmente — contradiciendo el propio objetivo de "priorizar", ya que compiten entre sí por el mismo ancho de banda limitado (web.dev advierte explícitamente de este patrón). Corregido con un script síncrono en el `<head>` que lee `sessionStorage.dp-intro-seen` y emite mediante `document.write()` solo el `<link rel="preload">` que corresponde a esa visita — nunca los dos. Regenerado el CSP del sitio (`python scripts/build-site-shell.py`) para incluir el hash del nuevo script inline; verificado en local que no genera ninguna violación de CSP y que cada ruta de visitante recibe exactamente un preload.
- Verificado con Lighthouse local (tabla de arriba) que este fix sí reduce el tiempo de carga del propio recurso a menos de 700ms — funciona exactamente como se pretendía — pero no mueve el LCP total porque el cuello de botella real está en otra fase completamente distinta (`Render Delay`, no `Load Time`).

## Otros hallazgos de la misma auditoría (sin tocar todavía)

- **Cachear con más agresividad activos estáticos** — ahorro estimado 3399-3608 KiB. Depende de las cabeceras `Cache-Control`/`Expires` del hosting/CDN (Cloudflare Pages), no de nada editable en el HTML.
- **Mejorar la entrega de imágenes** — ahorro estimado 2260 KiB. Candidatas: imágenes servidas más grandes de lo necesario para el viewport móvil, o sin `srcset`/formatos modernos en todas partes.
- **Solicitudes que bloquean el renderizado** — ahorro estimado 1790-2120 ms. Candidatas probables: hojas de estilo `<link rel="stylesheet">` síncronas en `<head>`.
- **Preconectar con `gc.zgo.at` y `tracker.metricool.com`** — ahorro estimado de LCP de 470ms y 310ms respectivamente, según el propio árbol de dependencias de PageSpeed Insights. Menor que la causa raíz, pero fácil y sin riesgo de aplicar. **Corrección (2026-09-10)**: solo el preconnect de `gc.zgo.at` está realmente en `main` (ya existía antes de esta auditoría); el de `tracker.metricool.com` se discutió pero nunca llegó a añadirse al HTML — una versión anterior de este documento afirmaba erróneamente que ambos estaban aplicados. Sigue pendiente.
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
4. **Tercera pasada (esta, 2026-09-10)**: una nueva revisión externa (GPT) señaló que "confirmado" era una sobreafirmación — la intro es la hipótesis más plausible, no un hecho demostrado — y además que la opción de "saltar la intro para bots" era cloaking. Se corrigió el estado a `INTRO_GATE_SUSPECTED · CAUSAL_TEST_PENDING`, se retiró esa opción, y se definió la prueba A/B pendiente para confirmar o descartar la causa antes de tomar ninguna decisión de producto.

## Próximos pasos

1. **Prueba causal A/B pendiente (antes de decidir nada más)**: medir el LCP con Lighthouse local en al menos cuatro variantes controladas — timeout de intro en 9600ms (actual), 1000ms, 0ms, y vídeo oculto desde el arranque (`display:none` hasta pasar la intro) o sustituido por solo el póster estático. Si el LCP cae de forma proporcional al reducir el timeout, la causa queda confirmada; si no, hay que seguir investigando (JS bloqueante, otra causa). Solo entonces pasa el estado de `INTRO_GATE_SUSPECTED` a confirmado.
2. **David decide** una de las opciones de la sección "requiere una decisión de producto" de arriba (o ninguna, si el coste se acepta conscientemente) — una vez confirmada la causa en el paso 1.
3. Una vez decidido y desplegado, volver a medir con PageSpeed Insights (varias ejecuciones, mediana, no una sola) para confirmar el LCP real antes de marcar cualquier estado como `_FIXED`.
4. Revisar cabeceras de caché del hosting (Cloudflare) para el ahorro de ~3,4-3,6 MB.
5. Añadir `<link rel="preconnect">` para `tracker.metricool.com` (bajo riesgo, ahorro estimado ~310ms de LCP; `gc.zgo.at` ya está aplicado en `main`).
6. Auditar qué hojas de estilo síncronas en `<head>` pueden diferirse sin causar FOUC.
7. Revisar compresión/dimensionado de imágenes pesadas de Home.
