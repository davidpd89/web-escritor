# H.6 · Revalidación de producción — CTA de reenvío/compartir newsletter

**Fecha:** 2026-08-30  
**Base:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `CONDITIONAL · BASE_NEWSLETTER_JOURNEY_NOT_READY_FOR_GROWTH_EXPERIMENT · LOW_COST_PILOT_ONLY_LATER · NO_CODE`

## Estado real

H.6 sigue siendo técnicamente barata, pero el orden de trabajo importa. H.1/H.2 han confirmado que el journey base todavía necesita reconciliar:

- copy y comportamiento de consentimiento en formularios generales;
- estado live de automatizaciones Brevo;
- templates legacy;
- welcome/entrega E2E.

Además H.3 ha detectado una promesa pública de entrega del primer capítulo de Samuel cuya automatización no está verificada. No tiene sentido añadir una capa de crecimiento/referral sobre un journey base todavía no reconciliado.

## Qué sí podría pilotarse después

Cuando el template y el journey sean estables, H.6 puede probarse como un bloque editorial mínimo:

- invitación humana a reenviar/compartir;
- URL pública de suscripción;
- UTM agregada opcional y no identificable;
- funcionamiento correcto en HTML y plain text;
- sin depender de imágenes o JS.

No requiere plataforma de referrals.

## Privacidad

El enlace compartible no debe contener:

- email;
- contact ID;
- token personal;
- código derivado del destinatario;
- estado de preferencias;
- ningún dato que permita reconstruir identidad.

Reenviar un email tampoco crea consentimiento para el receptor reenviado: la nueva persona debe llegar a una URL pública y completar su propio DOI.

## Hipótesis mínima

Antes de añadir el CTA debe escribirse algo equivalente a:

> «Un CTA discreto de reenvío aumenta visitas y altas confirmadas atribuibles sin empeorar bajas/quejas.»

La evaluación debe distinguir click de conversión confirmada. Un click no demuestra crecimiento de lista.

## Gate

Reabrir solo cuando:

1. consentimiento base reconciliado;
2. DOI/welcome/delivery E2E verificados;
3. template base estable;
4. URL pública de suscripción estable;
5. medición agregada disponible;
6. volumen suficiente para observar señal;
7. criterio KEEP / CHANGE / STOP predefinido.

## No implementar ahora

- No referral codes.
- No SaaS adicional.
- No recompensas.
- No leaderboard.
- No parámetros con PII.
- No CTA insistente en todas las campañas por defecto.

## Cierre

H.6 permanece `CONDITIONAL`, pero está claramente detrás del saneamiento del journey newsletter. Primero confianza y entrega; después adquisición.