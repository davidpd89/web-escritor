# J.6 · Revalidación de producción — lectores beta

Fecha: 2026-08-30  
Base: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`

## Veredicto

`PARTIAL_AUDIT · PUBLIC_SURFACE_EXISTS · BETA_LIST_FAIL_CLOSED · EXTERNAL_E2E_NOT_VERIFIED · NO_CODE`

## Evidencia directa

- `/lectores-beta/` existe, está `noindex, follow` y declara un propósito separado de la newsletter general.
- `cloudflare-worker-subscribe.js` mapea `source="lectores-beta"` a `BREVO_BETA_LIST_ID`, nunca a `BREVO_LIST_ID`.
- Si la variable/lista beta no está configurada, el Worker falla cerrado; no mezcla silenciosamente el alta con la newsletter general.
- El propio Worker documenta que el estado externo de listas/workflows debe verificarse en Brevo y no puede inferirse del repo.

## Lo que falta para declarar LIVE

Smoke E2E real contra la cuenta autorizada:

1. alta DOI desde `/lectores-beta/`;
2. contacto termina únicamente en la lista beta correcta;
3. `SOURCE=lectores-beta` correcto;
4. no aparece alta paralela en lista general;
5. baja/preferencias funcionan según el proceso real;
6. cualquier workflow/template asociado coincide con el propósito beta.

Hasta obtener esa evidencia, el estado no es `fully operational`.

## Decisión editorial

No reabrir artificialmente una beta de Las manecillas del recuerdo a pocos días de su publicación del 3/09/2026. El valor de esta infraestructura es quedar como proceso reusable para una obra futura que sí necesite lectores beta.

No se modifica runtime en esta PR.