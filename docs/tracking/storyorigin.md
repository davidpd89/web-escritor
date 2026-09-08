# Tracking — StoryOrigin

**Revisión:** 2026-09-08

**Estado:** `NO_GO_PAID_FOR_ACQUISITION · NO_GO_DUPLICATE_FREE_TOOLS · ZERO_SPEND`

## Decisión

Cerrar para el backlog gratuito actual.

StoryOrigin sigue activo y tiene un plan Basic gratuito, pero las funciones que aportarían descubrimiento/adquisición real al proyecto están en el plan Standard de pago. Mantener esta PR abierta obligaría a revisar una herramienta cuyo free tier duplica capacidades que ya tenemos sin aportar una audiencia externa nueva.

## Modelo real actual

Según la página oficial de precios revisada el 2026-09-08:

### Basic Plan — gratis

- integración con servicios de email marketing;
- entrega ilimitada de archivos;
- soporte técnico para lectores;
- universal retail links;
- Facebook tracking pixel;
- Amazon affiliate tags;
- seguimiento de objetivos de palabras.

### Standard Plan — 10 USD/mes o 100 USD/año

Aquí están precisamente las funciones de adquisición que nos interesarían:

- Group Promos;
- newsletter swaps;
- captación de emails de lectores;
- beta copies y feedback;
- review copies + seguimiento de reviewers;
- custom links / website builder;
- venta directa de ebooks;
- otras automatizaciones de promoción.

Fuente oficial: https://storyoriginapp.com/pricing

## Valor para WEB DAVID PORTO

El plan gratuito no supera el filtro de utilidad incremental:

- la web ya entrega muestras/archivos sin depender de StoryOrigin;
- Brevo cubre email/newsletter;
- la web ya enlaza retailers y puede medir clics;
- no necesitamos otro pixel de Facebook;
- los enlaces universales, por sí solos, no aportan una audiencia externa significativa;
- el crecimiento mediante promociones cruzadas, swaps, reader magnets o ARC/review workflows requiere el plan de pago.

Por tanto no tiene sentido mantener una herramienta adicional solo para replicar infraestructura ya disponible.

## Derechos y guardrails

- No subir copias completas de `Samuel entre mundos` ni `Las manecillas del recuerdo` sin autorización del owner editorial/digital correspondiente.
- No contratar Standard ni pruebas que desemboquen en pago para cerrar esta tarea.
- No sustituir Brevo, la entrega propia de muestras o los enlaces canónicos de compra por StoryOrigin sin una ventaja demostrable.
- No instalar Facebook Pixel u otro tracking adicional solo porque el free tier lo permita.

## Reapertura

Reabrir únicamente si cambia materialmente el producto y alguna de estas capacidades pasa a ser permanentemente gratuita:

- Group Promos;
- newsletter swaps;
- reader magnets con captación;
- ARC/review copies con acceso a audiencia;
- otra función que genere descubrimiento externo real sin coste.

Si solo sigue ofreciendo gratis utilidades de infraestructura duplicadas, mantener `NO_GO`.

## Criterio de cierre

`FREE_TIER_REVIEWED · ACQUISITION_FEATURES_CONFIRMED_PAID · DUPLICATE_FREE_FUNCTIONS_IDENTIFIED · RIGHTS_NOT_EXPOSED · ZERO_SPEND · NO_ACCOUNT_REQUIRED`

## Fuentes oficiales

- Pricing y matriz de funciones: https://storyoriginapp.com/pricing
- Producto / promociones cruzadas: https://storyoriginapp.com/
