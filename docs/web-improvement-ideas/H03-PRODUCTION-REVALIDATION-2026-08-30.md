# H.3 · Revalidación de producción — contenido exclusivo de newsletter

**Fecha:** 2026-08-30  
**Base:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `CONDITIONAL · EXISTING_EXCLUSIVE_PROMISE_NOT_DELIVERY_VERIFIED · DO_NOT_ADD_NEW_PROMISE · RIGHTS_AND_JOURNEY_GATE · NO_CODE`

## Hallazgo principal

Home ya contiene una promesa de valor concreta: suscribirse para recibir novedades y **«el primer capítulo de Samuel entre mundos gratis»**.

Sin embargo, el propio `script.js` documenta que no existe en el repositorio una automatización Brevo confirmada que entregue ese capítulo tras el alta. Por esa razón, el mensaje de estado posterior al DOI evita prometer entrega automática de contenido concreto.

Antes de inventar un nuevo lead magnet/exclusivo, hay que reconciliar la promesa existente.

## Qué activa H.3 de verdad

No basta con «queremos aumentar conversión». Deben existir simultáneamente:

1. material exclusivo real;
2. derechos claros para distribuirlo por email/descarga;
3. valor distinto del contenido ya público;
4. journey de entrega probado;
5. copy que describa exactamente qué y cuándo recibe la persona;
6. consentimiento compatible;
7. medición no invasiva suficiente para saber si aporta valor.

## Prioridad actual

Primero decidir una de estas dos cosas sobre Samuel:

- **cumplir la promesa:** verificar/crear de forma deliberada el journey que entrega el capítulo, con rights y E2E; o
- **retirar/corregir la promesa:** si no se desea mantener ese beneficio.

No añadir una segunda promesa de Manecillas u otro recurso encima de una entrega no verificada.

## Guardrails

- No llamar «exclusivo» a contenido ya público sin explicar la diferencia.
- No usar manuscritos no autorizados como incentivo.
- No afirmar disponibilidad comercial para Manecillas sin destino verificado.
- No hacer content upgrade distinto por cada artículo.
- No ocultar que el alta requiere DOI.
- No condicionar una herramienta gratuita a newsletter si no es necesario.
- No reutilizar consentimiento beta para marketing general.

## Posibles formatos futuros

Solo después de superar el gate podrían valorarse: fragmento autorizado, nota de proceso no publicada, mini-guía de club, material de contexto o recurso editorial propio. La elección depende de derechos y valor, no de que sea técnicamente fácil adjuntar un PDF.

## Cierre

H.3 permanece `CONDITIONAL`, pero el trabajo neto actual no es producir otro regalo. Es reconciliar la promesa ya publicada y demostrar el delivery. Hasta entonces, `NO_CODE`.