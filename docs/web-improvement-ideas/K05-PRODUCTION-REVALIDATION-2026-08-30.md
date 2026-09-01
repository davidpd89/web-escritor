# K.5 · Revalidación de producción — mecenazgo / apoyo

Fecha: 2026-08-30  
Base auditada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
Tree: `68d02e1fe8ac2cfa239f4a716929e992abb672fd`

## Veredicto

`DEFER · MEMBERSHIP_VALUE_PROPOSITION_NOT_DEFINED · ONE_TIME_SUPPORT_IS_SEPARATE_HYPOTHESIS · EXTERNAL_PLATFORM_FIRST · NO_PAYMENT_RUNTIME`

K.5 sigue sin ser una deuda técnica, pero la revalidación actual corrige una simplificación histórica: **no todo mecenazgo exige una propuesta recurrente**.

Hay dos productos distintos:

1. **apoyo puntual / tip** — una persona decide apoyar contenido gratuito sin esperar una membresía;
2. **membresía recurrente** — pago periódico a cambio de una relación/beneficios sostenibles.

El segundo sí exige una propuesta recurrente clara. El primero puede existir sin tiers ni contenido exclusivo, aunque sigue siendo una decisión de marca y debe ubicarse sin competir con libros/newsletter.

## Estado de `main`

No se localiza integración Ko-fi/Patreon ni runtime de pagos/membresías. Es coherente con #135.

La web sí ofrece valor gratuito suficiente como para que, en el futuro, una hipótesis de apoyo puntual pueda probarse de forma **contextual** —por ejemplo, tras completar una herramienta útil— sin convertir el sitio entero en un funnel de donación.

Eso no significa que el CTA deba añadirse ahora: primero necesita cuenta/plataforma real, copy de marca y un experimento acotado.

## Mercado actual

### Ko-fi

Ko-fi publica actualmente:

- alta sin cuota mensual;
- modalidad Free con 0 % de service fee en tips puntuales;
- 5 % de service fee en memberships/shop/comisiones y en otras modalidades, más fees del procesador;
- pagos directos a PayPal/Stripe;
- memberships disponibles sin construir billing propio.

Fuentes 2026-08-30:

- https://help.ko-fi.com/hc/en-us/articles/360002506494-Does-Ko-fi-take-a-fee
- https://ko-fi.com/pricing
- https://help.ko-fi.com/hc/en-us/articles/4402945994001-Ko-fi-Memberships-and-Membership-Tiers

### Patreon

Para creadores nuevos publicados después del 4 de agosto de 2025, Patreon aplica actualmente un plan estándar del 10 % de plataforma, más fees de procesamiento aplicables. A cambio incluye una capa más fuerte de membresía/comunidad, productos digitales y contenido alojado.

Fuentes 2026-08-30:

- https://support.patreon.com/hc/es-es/articles/11111747095181-Informaci%C3%B3n-general-sobre-las-comisiones-de-los-creadores
- https://support.patreon.com/hc/en-gb/articles/36426991446797-A-standard-platform-fee-for-new-creators-effective-after-4-August-2025

Conclusión de mercado: si la hipótesis fuese únicamente «quiero permitir que quien valore una herramienta/artículo gratuito me apoye una vez», una plataforma ligera tipo Ko-fi es proporcionalmente más simple. Si el producto fuese comunidad/membresía editorial recurrente, Patreon tiene más superficie, pero esa superficie solo aporta valor si existe contenido/operación para usarla.

## Hipótesis A — apoyo puntual

### Cuándo podría tener sentido

- después de una utilidad gratuita con valor claro;
- al final de un artículo/recurso especialmente trabajado;
- en una página de apoyo voluntario enlazada desde un lugar secundario;
- cuando lectores hayan pedido explícitamente una forma de apoyar.

### Dónde NO ponerlo inicialmente

- header global;
- hero de Home;
- modal/popup;
- junto al CTA principal de compra de libro;
- dentro del consentimiento/newsletter.

### Experimento mínimo

1. Crear/verificar cuenta externa real.
2. Elegir una única superficie contextual.
3. Usar enlace simple; no widget/SDK si no aporta.
4. Copy explícito de apoyo voluntario, sin culpa ni urgencia.
5. Medir clics de forma agregada con la taxonomía existente y conversiones desde la propia plataforma.
6. Revisar si afecta a la conversión principal de la superficie.
7. Retirar si no aporta o distrae.

No prometer beneficios exclusivos para justificar una propina.

## Hipótesis B — membresía recurrente

Permanece bloqueada hasta que exista una propuesta sostenible:

```text
membership_purpose
cadence
benefits
public_vs_paid_boundary
content_owner
support_load
rights
price
platform
expected_demand
retention_signal
brand_decision
```

No degradar Cuaderno/newsletter gratuito para fabricar artificialmente valor de pago.

## Qué plataforma elegir si se reabre

No escoger por popularidad. Comparar:

- propósito: tip vs membership;
- fee total real en EUR;
- payout/procesador;
- VAT/impuestos/obligaciones según configuración;
- exportación de audiencia/datos;
- privacidad;
- moderación/comunidad si aplica;
- dependencia de plataforma;
- experiencia móvil;
- carga editorial.

La web debe enlazar al tercero antes de integrar SDKs o construir billing propio.

## Relación con otros bloques

- **K.1/K.2/K.4**: apoyo no es compra de producto; no mezclar funnels.
- **H/newsletter**: ser supporter no implica consentimiento de marketing.
- **I.2/I.5**: cualquier SDK/widget nuevo reabre inventario de terceros; un enlace externo simple minimiza superficie.
- **G/J**: comunidad gratuita no debe paywallearsе por defecto.
- **Analytics**: medir click/route de forma agregada; no introducir IDs de supporter en la web.

## Qué NO hacer

- CTA global de «apóyame» sin experimento;
- tiers vacíos;
- copiar perks de otros creadores;
- exclusividad artificial;
- prometer capítulos inéditos/eventos/merch sin capacidad real;
- meter un widget pesado cuando basta un enlace;
- construir billing propio;
- mezclar donación, compra y newsletter;
- usar dark patterns de culpa/urgencia;
- presentar el apoyo como necesario para acceder a recursos que ya son gratuitos.

## QA / CI

HEAD auditado antes de esta ampliación: `5835276673484a08a11753e4ae45dad60bec3f75`.

Ocho workflows estaban en `success`: Required merge gate `33313215100`, Check content indexes `33313215082`, Public artifact contract `33313215115`, Analytics taxonomy `33313215083`, Runtime scoping `33313215150`, CSP public shell `33313215129`, Pa11y `33313215079` y Sitewide Reflow `33313215092`.

El nuevo commit debe volver a pasar CI.

## Cierre

K.5 sigue en `DEFER`, pero se divide correctamente en dos hipótesis. **Membresía recurrente** sigue sin propuesta de valor y no debe implementarse. **Apoyo puntual** es más ligero y podría probarse en una superficie contextual si aparece demanda o se decide explorarla, usando plataforma externa y sin convertir la web en un sistema de pagos.

Mantener DRAFT.