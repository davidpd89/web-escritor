# E.7 — Compresión HTTP real del origen (Brotli/Zstd/gzip)

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`  
Estado histórico final humano: **`NOT_APPLICABLE`**  
Estado efectivo tras revalidación independiente: **`PARTIAL_AUDIT`**

## 1. Por qué E.7 necesita una reconciliación explícita

E.7 es una de las pocas ideas de #135 cuyo estado machine-readable/final humano quedó **desfasado respecto a una revalidación independiente posterior**.

La secuencia fue:

1. idea original: comprobar/activar Brotli en hosting/CDN;
2. se verifica que Cloudflare está en **DNS-only**;
3. se concluye que Cloudflare no está en el camino HTTP y por tanto no puede aportar compresión edge;
4. autoridad final marca `NOT_APPLICABLE`;
5. revalidación independiente detecta que esa conclusión responde a una pregunta demasiado estrecha;
6. DNS-only demuestra que **Cloudflare no comprime**, pero no demuestra qué compresión sirve el **origen/hosting**;
7. estado efectivo correcto: **`PARTIAL_AUDIT`** para observar `Content-Encoding` real, sin tocar proxy.

Este documento preserva ambos estados y explica por qué el segundo es la conclusión más reciente.

## 2. Veredicto operativo

**`PARTIAL_AUDIT`**.

No activar proxy naranja para “conseguir Brotli”.

No configurar Cloudflare compression mientras el tráfico siga DNS-only.

Sí verificar, sobre respuestas públicas reales:

- HTML;
- CSS;
- JavaScript;
- JSON/XML si es relevante;

qué `Content-Encoding` entrega el origen cuando el cliente anuncia soporte para compresión.

Si ya entrega gzip/Brotli/Zstd apropiadamente, cerrar como no-op documentado.

Si entrega texto sin compresión, investigar el hosting/origen real y sus capacidades antes de prescribir una solución.

## 3. Hipótesis original

La lista inicial decía, en esencia:

> si Cloudflare ya está configurado, confirmar que Brotli esté activo para HTML/CSS/JS, no solo gzip.

Era una hipótesis razonable pero contenía una suposición: que Cloudflare era el CDN/proxy que servía el tráfico HTTP.

La investigación posterior demostró que esa suposición no era correcta.

## 4. Evolución completa

| Fase | Estado | Razón |
|---|---|---|
| Idea original | comprobar Brotli Cloudflare | Se asume posible CDN/proxy activo. |
| Revisión 108/108 | `NOT_APPLICABLE` | Cloudflare DNS-only; edge compression requiere tráfico proxied. |
| Matriz intermedia | `VERIFICAR, NO “CONFIGURAR BROTLI”` | Comprobar `Content-Encoding` real; no activar proxy solo por compresión. |
| Autoridad final | `NOT_APPLICABLE` | Mantiene el foco estrecho en Cloudflare. |
| JSON machine-readable | `NOT_APPLICABLE` | Replica autoridad final, antes de la corrección independiente. |
| Revalidación independiente | **`PARTIAL_AUDIT`** | DNS-only no dice qué compresión sirve GitHub Pages/origen. |
| Reconciliación 2026-08-29 | **`PARTIAL_AUDIT`** | Sigue faltando evidencia fiable del header live. |

## 5. Qué estaba bien en `NOT_APPLICABLE`

La parte correcta era:

> “Configurar Brotli en Cloudflare” no aplica mientras Cloudflare sea DNS-only.

En DNS-only:

- Cloudflare resuelve DNS;
- el navegador conecta al origen indicado por DNS;
- el tráfico HTTP no termina en el edge proxy de Cloudflare;
- features de compresión/caching/WAF de proxy no gobiernan esa respuesta.

Por tanto, **no** se debe activar proxy naranja solo para cumplir E.7.

## 6. Qué estaba mal/incompleto

La idea E.7 no tenía por qué responder únicamente a:

> ¿Cloudflare comprime?

La pregunta útil de rendimiento es:

> ¿las respuestas textuales públicas se entregan comprimidas por quien realmente las sirve?

La revalidación independiente corrigió exactamente este punto.

Cloudflare fuera del camino no implica:

- HTML sin gzip;
- CSS sin Brotli;
- JS sin compresión.

El origen puede negociar compresión por su cuenta.

## 7. La matriz intermedia ya anticipaba la corrección

Antes de la autoridad final, `IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` ya decía:

**`VERIFICAR, NO “CONFIGURAR BROTLI”`**

Y proponía comprobar `Content-Encoding` real.

Esto muestra que la revalidación independiente no inventó una dirección nueva: recuperó una distinción que el cierre final había simplificado demasiado.

## 8. Revalidación independiente

`PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` dice expresamente que **solo E.7** necesita cambiar el estado machine-readable dentro de las 108 ideas.

Cambio:

```text
NOT_APPLICABLE → PARTIAL_AUDIT
```

Motivo:

- Cloudflare DNS-only: hecho mantenido;
- compresión Cloudflare edge: no aplicable;
- compresión del origen real: no observada todavía;
- acción correcta: verificar, no reconfigurar infraestructura.

Esta es la autoridad histórica más reciente sobre E.7.

## 9. Pasada undécima de Cloudflare

La investigación `IDEAS-MEJORA-WEB-UNDECIMA-PASADA-CLOUDFLARE-GRATUITA-2026-08-28.md` reafirma que:

- la migración DNS estaba terminada;
- no se debía reabrir #131/#132;
- no se proponía activar proxy naranja;
- funciones HTTP como Always Use HTTPS/TLS de edge no gobiernan el tráfico DNS-only;
- el HTTPS público correspondía al hosting/origen, no a Cloudflare proxy.

Aunque R.58/R.59 trataban CT Monitoring y DNSSEC, el contexto confirma el boundary de E.7.

## 10. Estado actual de la web

La web pública `https://davidportodiaz.com/` responde y es accesible actualmente.

Sin embargo, la herramienta web utilizada en esta revisión expone contenido de la página, **no el header de negociación `Content-Encoding`**. Un intento de `curl` desde el runtime local no pudo resolver el dominio por las restricciones de red del entorno.

Por tanto, sería incorrecto afirmar aquí:

- “Brotli está activo”;
- “solo usa gzip”;
- “está sin compresión”.

El estado sigue siendo **live check pendiente**.

## 11. Verificación live correcta

Desde un entorno con acceso de red normal:

```bash
curl -I --compressed https://davidportodiaz.com/
curl -I --compressed https://davidportodiaz.com/assets/v1-base.css
curl -I --compressed https://davidportodiaz.com/script.js
```

O de forma más explícita:

```bash
curl -sSI \
  -H 'Accept-Encoding: br, zstd, gzip' \
  https://davidportodiaz.com/
```

Registrar:

- status;
- `Content-Type`;
- `Content-Encoding`;
- `Vary`;
- `Content-Length` cuando sea interpretable;
- servidor/CDN headers relevantes solo como evidencia, no como objetivo.

## 12. Muestra mínima

No basta una única URL.

Comprobar al menos:

```text
/
/assets/v1-base.css
/script.js
/cuaderno/
/cuaderno/feed.xml  (si el tamaño hace la prueba relevante)
```

Y, si existen diferencias de hosting/path, una ruta representativa adicional.

## 13. Qué resultados serían aceptables

### Caso A — Brotli/Zstd

Si texto moderno se entrega con `br`/`zstd` y funciona correctamente:

- registrar evidencia;
- no cambiar infraestructura;
- cerrar auditoría.

### Caso B — gzip

No convertir automáticamente “gzip” en fallo.

Comparar:

- tamaños reales;
- capacidad del hosting;
- coste/riesgo de cambiar arquitectura;
- diferencia material de transferencia.

Un sitio estático pequeño no justifica activar un proxy completo solo por unos puntos de compresión.

### Caso C — sin compresión

Si HTML/CSS/JS relevantes se entregan sin compresión:

1. confirmar con varias peticiones/clientes;
2. identificar origen real;
3. revisar configuración/capacidad del hosting;
4. cuantificar bytes potencialmente evitables;
5. proponer la solución mínima compatible con la arquitectura.

## 14. `Vary: Accept-Encoding`

Cuando hay negociación de codificación, revisar que caches/intermediarios distingan variantes correctamente.

No obsesionarse con un header aislado: el objetivo es una respuesta correcta y eficiente.

## 15. No hacer

- activar Cloudflare proxy naranja solo para E.7;
- migrar hosting sin medir bytes;
- añadir un Worker que recomprima assets por defecto;
- versionar blobs precomprimidos `.br/.gz` si el hosting no los sirve correctamente;
- asumir que DNS provider = HTTP CDN;
- confundir `content-encoding` con formato de archivo;
- medir solo una respuesta cacheada y generalizar;
- declarar `CONFIGURED_LIVE` sin observar headers;
- declarar `VERIFIED_E2E` desde el repo.

## 16. Relación con E.5

E.5 mide artifact determinista. E.7 mide transferencia/negociación live.

Un archivo de 100 KB en repo puede transferirse como 25 KB comprimidos, pero ambos números responden a preguntas distintas.

No usar el valor comprimido live como único budget de CI porque depende de infraestructura externa.

## 17. Relación con Cloudflare

E.7 no autoriza cambiar el modelo DNS-only.

Si en el futuro se decide proxificar por otros motivos, entonces:

- caching;
- WAF;
- compresión;
- SSL edge;
- headers;
- observabilidad;

forman parte de una migración de arquitectura propia y deben probarse juntos. No esconder esa migración dentro de “activar Brotli”.

## 18. Relación con hosting/origen

El origen actual debe evaluarse como sistema real de entrega.

Si el hosting ya comprime automáticamente, no hay backlog técnico aunque Cloudflare no participe.

La conclusión correcta puede ser simplemente:

```text
AUDITED → already compressed by origin → NO_CHANGE
```

## 19. Status machine-readable histórico

El fichero `data/web-improvement-decisions-2026-08-28.json` conserva `NOT_APPLICABLE` porque fue generado antes de la revalidación independiente.

Esta reconstrucción **no reescribe ese fichero histórico**. Hacerlo destruiría evidencia de la secuencia de decisiones.

La resolución es documental:

```text
historical final/machine status = NOT_APPLICABLE
effective latest #135 reasoning = PARTIAL_AUDIT
```

## 20. Autoridad para futuras decisiones

Si otro documento posterior intenta decir simplemente “E.7 no aplica porque Cloudflare es DNS-only”, debe contrastarse con esta corrección:

- Cloudflare compression: no aplica;
- origin compression audit: sí aplica.

## 21. DoD de la auditoría live futura

- [ ] HTML observado con `Accept-Encoding`;
- [ ] CSS observado;
- [ ] JS observado;
- [ ] `Content-Encoding` registrado;
- [ ] `Vary` revisado cuando proceda;
- [ ] origen/proxy efectivo identificado;
- [ ] bytes aproximados cuantificados si hay gap;
- [ ] no se cambia proxy por defecto;
- [ ] si ya está comprimido, no-op documentado;
- [ ] si no, solución mínima propuesta con before/after.

## 22. Pasadas tardías relevantes

Especialmente relevantes:

- matriz final intermedia: `VERIFICAR, NO “CONFIGURAR BROTLI”`;
- undécima pasada Cloudflare: confirma DNS-only y boundary de funciones edge;
- revalidación independiente: corrige a `PARTIAL_AUDIT`;
- decimotercera pasada: vuelve a insistir en observar configuración HTTP live antes de prescribir cambios en otros controles de headers.

Las restantes pasadas no aportan una reversión específica de E.7.

## 23. Estado de verdad

- `DOCUMENTED`: sí.
- `IMPLEMENTED_IN_PR`: no, no hay cambio de infraestructura.
- `MERGED_MAIN`: no.
- Cloudflare DNS configurado: histórico separado, no implica proxy HTTP.
- `CONFIGURED_LIVE` de compresión: **no verificado aquí**.
- `VERIFIED_E2E`: no.

## 24. Fuentes históricas

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`;
- `docs/IDEAS-MEJORA-WEB-UNDECIMA-PASADA-CLOUDFLARE-GRATUITA-2026-08-28.md`;
- `docs/IDEAS-MEJORA-WEB-DECIMOTERCERA-PASADA-REVALIDACION-FINAL-2026-08-28.md`.

## 25. Conclusión

E.7 debe registrarse como **`PARTIAL_AUDIT` efectivo**, preservando que la autoridad humana/JSON anterior decía `NOT_APPLICABLE`. El motivo es preciso: Cloudflare no puede comprimir tráfico que no proxifica, pero eso no responde a si el hosting que realmente entrega davidportodiaz.com comprime HTML/CSS/JS. La acción correcta es observar `Content-Encoding` live y, probablemente, cerrar sin cambios si el origen ya hace un trabajo suficiente. No se debe activar el proxy naranja por esta idea.