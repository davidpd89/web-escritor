# E.2 · Revalidación de producción — INP / responsiveness

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **MEASURE_FIRST · LAB_GUARDS_EXIST · FIELD_CONTRIBUTOR_NOT_VERIFIED · NO_BLIND_OPTIMIZATION · NO_CODE**.

## 1. Resultado

E.2 sigue siendo válida como disciplina de rendimiento, pero no existe evidencia actual suficiente para señalar un handler concreto y optimizarlo.

No se modifica JavaScript por intuición. Primero hay que identificar una interacción lenta real y descomponer su latencia; solo entonces se cambia el contributor responsable.

## 2. Guía actual de la plataforma

Fuentes revalidadas el 30/08/2026:

- web.dev — Interaction to Next Paint: https://web.dev/articles/inp
- web.dev — Optimize Interaction to Next Paint: https://web.dev/articles/optimize-inp
- Chrome for Developers — Long Animation Frames API: https://developer.chrome.com/docs/web-platform/long-animation-frames

La guía vigente mantiene:

```text
good INP <= 200 ms
needs improvement > 200 ms and <= 500 ms
poor > 500 ms
```

medido de forma representativa en el percentil 75 de cargas, separando móvil y desktop.

La misma guía insiste en **encontrar primero la interacción lenta en field data** y después diagnosticar en laboratorio; no recomienda aplicar yielding o refactors genéricos sin contributor.

## 3. Componentes de una interacción

Una interacción lenta puede deberse a:

1. input delay;
2. processing duration;
3. presentation delay.

Cada causa exige una solución distinta. Reducir código de un handler no sirve si el problema real es trabajo previo bloqueando main thread o rendering posterior.

## 4. LoAF

Chrome documenta Long Animation Frames como señal de diagnóstico de frames >=50 ms y especialmente útil para relacionar un frame bloqueante con una interacción INP.

LoAF aporta contexto como:

- `duration`;
- `renderStart`;
- `styleAndLayoutStart`;
- `firstUIEventTimestamp`;
- `blockingDuration`;
- scripts/contributors asociados.

No debe instalarse telemetría LoAF porque sí. Es útil cuando existe un problema de field data que necesita atribución.

## 5. Estado del repo

### Scheduling existente

`script.js` ya contiene un helper `scheduleTask()` que usa `scheduler.postTask` cuando está disponible y cae a una Promise. Varios trabajos no críticos se programan como background/user-visible.

Esto demuestra que el runtime ya intenta evitar trabajo innecesariamente bloqueante. No demuestra que el INP sea bueno ni malo.

### Lab QA

El repo dispone de:

- Lighthouse CI;
- browser QA;
- cross-engine smoke;
- Pa11y;
- reflow QA;
- presupuestos de rendimiento/lab en superficies relevantes.

`.github/workflows/lighthouse-ci.yml` documenta correctamente las limitaciones del laboratorio y evita incluso relajar una CSP solo para mejorar una puntuación sintética.

Ese criterio debe conservarse en E.2: lab data ayuda a reproducir; no sustituye field INP.

## 6. Field data

La reconstrucción histórica registró que CrUX no ofrecía una muestra útil y separó la obtención de RUM/Cloudflare como operación externa.

En esta revalidación no se dispone de evidencia autorizada de cuenta que demuestre:

- un p75 INP actual;
- una ruta/journey problemático;
- un interaction target concreto;
- un LoAF/contributor real;
- una regresión temporal.

Por tanto el estado correcto es:

```text
FIELD_CONTRIBUTOR_NOT_VERIFIED
```

No se reconstruyen valores desde memoria ni se inventa una captura RUM.

## 7. Runbook correcto

Cuando exista field signal:

```text
1. identificar route + device class + interaction target
2. confirmar p75 / frecuencia del problema
3. reproducir interacción en DevTools/trace
4. separar input delay / processing / presentation
5. identificar long task/LoAF/script/layout contributor
6. hacer cambio mínimo
7. repetir lab
8. comparar field data después del deploy
```

## 8. Cuándo usar yielding

`yield`/`scheduler.yield()`/task splitting solo procede cuando un contributor real contiene trabajo largo divisible.

No insertar yields dentro de handlers pequeños ni dispersar scheduling por el repo para perseguir una métrica sin evidencia.

La guía actual de web.dev también recuerda que reducir trabajo es preferible a simplemente trocearlo cuando sea posible.

## 9. Qué no hacer

- no optimizar INP desde Lighthouse score agregado;
- no usar TBT como sustituto de INP de campo;
- no añadir `scheduler.yield()` globalmente;
- no refactorizar listeners sin trace;
- no retirar funcionalidades por sospecha;
- no añadir RUM propio sin necesidad/privacidad/owner;
- no afirmar que Cloudflare/CrUX muestra un valor no recuperado;
- no optimizar solo desktop;
- no confundir scroll jank con INP sin identificar interacción.

## 10. Trigger de implementación

E.2 cambia de `MEASURE_FIRST` a una PR de código solo cuando existe:

```text
field or reproducible interaction evidence
+ target/journey identificado
+ contributor atribuible
+ cambio mínimo evaluable
```

Sin esos cuatro elementos, una PR de «optimización INP» sería especulativa.

## 11. Definition of Done

- [x] guía INP actual revalidada;
- [x] umbrales actuales preservados;
- [x] LoAF reconciliado como diagnóstico, no solución automática;
- [x] scheduling existente del repo reconocido;
- [x] lab QA separado de field data;
- [x] ausencia de field contributor declarada sin inventar evidencia;
- [x] runbook de diagnóstico definido;
- [x] sin refactor de JS prematuro.

## Estado para Claude

No tocar runtime por E.2 hasta recuperar una interacción lenta real. Lighthouse y los guards actuales son evidencia de laboratorio; el siguiente paso válido es field signal → trace → contributor → fix mínimo, no una campaña genérica de `yield()`/micro-optimizaciones.