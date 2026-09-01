# E.3 — `fetchpriority="high"` y candidato LCP

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`  
Estado efectivo: **`CONDITIONAL`**

## 1. Alcance

E.3 nació como una propuesta para asegurar `fetchpriority="high"` en el elemento que suele ser LCP de cada plantilla. La investigación de #135 redujo esa formulación: la prioridad de fetch solo aporta cuando existe un **candidato LCP estable y medido** cuya descarga necesita ser descubierta/priorizada antes.

Esta PR reconstruye esa evolución y contrasta el estado actual. No modifica HTML ni añade hints.

## 2. Veredicto

**`CONDITIONAL`**.

No existe una regla “toda hero image lleva `fetchpriority=high`”.

Aplicar únicamente cuando:

- la medición identifica una imagen LCP estable;
- no está lazy-loaded;
- la prioridad actual es insuficiente o el recurso se descubre tarde;
- el cambio mejora el waterfall/LCP sin competir con recursos más importantes.

## 3. Hipótesis original

La idea original proponía:

- confirmar el candidato LCP por plantilla;
- añadir `fetchpriority="high"`;
- evitar que dependa de JavaScript;
- evitar lazy-loading en ese candidato.

La hipótesis era razonable, pero podía degenerar fácilmente en un atributo repetido sin evidencia.

## 4. Evolución histórica

| Fase | Estado | Interpretación |
|---|---|---|
| Idea original | aplicar al LCP candidate | Mejora potencial de descubrimiento/prioridad. |
| Revisión 108/108 | `CONDITIONAL` | Solo para imagen LCP estable descubierta tarde; medir before/after. |
| Matriz intermedia | `PILOTAR MEDIDO` | Nada de `high` en todas las imágenes. |
| Autoridad final | `CONDITIONAL` | Comprobar waterfall y candidato real. |
| Revalidación independiente | mantenida | Sin evidencia para convertirlo en política global. |
| `main` actual | condicional con aplicación parcial | Home ya precarga una imagen con `fetchpriority="high"`; no implica cobertura sitewide. |

## 5. Fuente primaria

#135 consolidó como referencia principal:

- web.dev — Optimize LCP.

La idea clave no es el atributo en sí, sino las partes de LCP:

- TTFB;
- resource load delay;
- resource load duration;
- element render delay.

`fetchpriority` solo puede ayudar en determinados contributors, principalmente cuando el recurso correcto necesita prioridad/discovery mejor.

## 6. Qué puede salir mal al usarlo por checklist

### 6.1 Priorizar demasiadas imágenes

Si varias imágenes reciben `high`, la señal pierde valor y compiten entre sí.

### 6.2 Priorizar el elemento equivocado

Una hero visual no siempre es el LCP real en todos los viewports.

### 6.3 Ocultar el problema verdadero

Si el LCP se descubre tarde porque el markup se genera con JS, añadir un hint puede ser inferior a hacer el recurso visible en HTML inicial.

### 6.4 Ignorar otros recursos críticos

Subir prioridad a una imagen puede competir con CSS/font/script necesarios para pintar el contenido.

## 7. Reconciliación con `main`

La Home actual contiene una evidencia real de aplicación selectiva:

```html
<link rel="preload"
      as="image"
      href="assets/david-porto-foto-portada-sinfondo.webp"
      fetchpriority="high" />
```

Esto demuestra que el proyecto ya utiliza el mecanismo donde se consideró apropiado.

No demuestra:

- que ese recurso siga siendo el LCP en todos los viewports;
- que todas las familias tengan su candidato optimizado;
- que deban añadirse hints a páginas interiores;
- que el atributo actual sea suficiente para cerrar E.3 sin waterfall.

Por eso el estado permanece `CONDITIONAL`, no `ALREADY_COVERED` ni `IMPLEMENT_AFTER_CURRENT_DEBT`.

## 8. Auditoría correcta por familia

Rutas representativas:

- `/`;
- `/las-manecillas-del-recuerdo/`;
- `/libros/samuel-entre-mundos/`;
- `/cuaderno/`;
- artículo largo del Cuaderno;
- `/herramientas/`;
- una herramienta pesada;
- `/autor.html`.

Por cada una:

1. medir LCP móvil y desktop;
2. identificar elemento LCP;
3. repetir varias veces para comprobar estabilidad;
4. revisar initiator/discovery;
5. comprobar loading/priority actual;
6. revisar waterfall;
7. solo si existe resource-load delay accionable, pilotar cambio;
8. comparar before/after.

## 9. Candidato de imagen correcto

Si el LCP es imagen:

- debe estar en HTML inicial siempre que sea razonable;
- no debe tener `loading="lazy"` si es above-the-fold/LCP;
- debe tener dimensiones para evitar layout shift;
- debe servirse en tamaño/formato razonables;
- `fetchpriority="high"` es una señal adicional, no sustituto de lo anterior.

## 10. Si el LCP es texto

No añadir `fetchpriority` a una imagen solo porque la plantilla tiene hero.

En ese caso revisar:

- CSS render-blocking;
- fuentes;
- TTFB;
- render delay;
- JS que retrasa paint.

Esto enlaza con E.4 pero no lo convierte automáticamente en preload de todas las fonts.

## 11. Relación con E.1

E.1 reduce bytes/formatos de imagen. E.3 controla prioridad del recurso que ya existe.

Una imagen AVIF muy ligera puede seguir descubrirse tarde. Una imagen priorizada puede seguir ser demasiado pesada.

Ambas ideas requieren medición diferente.

## 12. Relación con E.4

Una fuente crítica y una imagen LCP pueden competir en la misma ventana de red. Añadir simultáneamente preloads sin waterfall puede empeorar ambos.

Por eso #135 estableció “menos preloads es mejor” como principio de E.4 y medición para E.3.

## 13. Relación con E.5

Los hints no deben introducirse sin límite. E.5 puede controlar bytes/requests agregados, pero no decide prioridades automáticamente.

## 14. No hacer

- añadir `fetchpriority="high"` a toda imagen hero;
- usarlo en imágenes below-the-fold;
- combinar `loading="lazy"` con intención LCP;
- precargar versiones que luego el navegador no consume;
- duplicar descarga por `href`/`srcset` incompatibles;
- alterar todas las plantillas en una sola PR sin baseline;
- declarar mejora por Lighthouse de una única ejecución;
- convertir una recomendación web.dev en regla ciega del repositorio.

## 15. Gate de implementación

Un nuevo hint solo entra si:

```text
LCP_IMAGE_STABLE
AND RESOURCE_LOAD_DELAY_MEASURABLE
AND CURRENT_PRIORITY_INSUFFICIENT
AND NO_DUPLICATE_FETCH
AND BEFORE_AFTER_IMPROVES
```

Si el problema está en otra subparte de LCP, resolver esa causa.

## 16. Prueba before/after

Registrar como mínimo:

- viewport/device profile;
- elemento LCP;
- LCP total;
- resource load delay;
- request start/priority;
- bytes/format;
- screenshot o trace cuando ayude;
- mediana de varias ejecuciones, no una sola.

Cuando haya suficiente field data, comprobar que el cambio no contradice experiencia real.

## 17. Contratos de accesibilidad/visual

E.3 no debe cambiar:

- `alt`;
- dimensiones semánticas;
- crop editorial;
- estructura de lectura;
- layout estable.

Optimizar prioridad no justifica degradar contenido.

## 18. Pasadas tardías

No se encontró una pasada posterior que cambie el estado de E.3. Las pasadas de CrUX/RUM refuerzan medir efectos reales, pero no convierten `fetchpriority` en regla universal.

## 19. Estado de verdad

- `DOCUMENTED`: sí.
- aplicación selectiva en `main`: sí, Home.
- `IMPLEMENTED_IN_PR`: no.
- cobertura sitewide verificada: no.
- `CONFIGURED_LIVE`: no se verifica waterfall live aquí.
- `VERIFIED_E2E`: no.

## 20. DoD de esta reconstrucción

- [x] idea original recuperada;
- [x] estado condicional preservado;
- [x] fuente primaria relevante recuperada;
- [x] límites con lazy/discovery/waterfall documentados;
- [x] aplicación actual en Home reconocida;
- [x] no se infiere cobertura global;
- [x] no se modifica runtime.

## 21. Fuentes históricas

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`.

Evidencia actual:

- `index.html` en `main` `291c8c677aaa7df635142687d1a6848e80ffcaa2`.

## 22. Conclusión

E.3 sigue **`CONDITIONAL`**. El proyecto ya demuestra que sabe aplicar `fetchpriority="high"` selectivamente; lo que #135 rechaza es convertir ese ejemplo en una política indiscriminada. Cada nueva aplicación debe partir de un LCP estable y de un waterfall que muestre un retraso que esa prioridad pueda corregir.