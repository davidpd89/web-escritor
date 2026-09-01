# I.2 · Revalidación de producción — inventario de analítica, terceros y consentimiento

**Fecha:** 2026-08-30  
**Base:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `IMPLEMENTED_IN_E8_PR · SHARED_AUTHORITY_EXISTS · DO_NOT_DUPLICATE · MAIN_STILL_WAITS_FOR_PR206 · CONSENT_DRIFT_OPEN · NO_DUPLICATE_CODE`

## Corrección de estado

La reconstrucción histórica de I.2 era correcta al decir que `main` no tenía el inventario perdido de #135. Pero desde entonces la revalidación E.8 ya ha realizado el trabajo técnico neto en **PR #206**.

#206 añade una única autoridad compartible:

- `data/third-party-integrations.json`;
- `scripts/check-third-party-integrations.py`;
- tests;
- workflow específico;
- ejecución dentro del Required merge gate.

Por tanto I.2 no debe volver a crear `privacy-vendors.json`, otro registry o un segundo checker.

## Estado efectivo

La capacidad está `IMPLEMENTED_IN_PR` en #206, no `MERGED_MAIN`. Mientras #206 siga DRAFT/no mergeada, `main@291c8c...` continúa sin ese registro.

Esto no autoriza duplicarlo en #225 para «hacer que I.2 quede implementada». La arquitectura correcta es que E.8 e I.2 compartan exactamente la misma fuente técnica cuando #206 se revise/integre.

## Cobertura actual de #206

El registro/checker de E.8 modela actualmente:

- GoatCounter;
- Metricool;
- Worker propio de suscripción;
- Brevo DOI server-side;
- Cloudflare Turnstile + AI Search/Workers AI condicionales;
- Groq/OpenRouter como proveedores opcionales deshabilitados, con activation gate.

También separa hosts browser/CSP de integraciones server-side y exige evidencia/disclosure según status.

Eso cubre la infraestructura central que I.2 reclamaba.

## Gap todavía abierto: consentimiento factual

#206 detectó y dejó correctamente sin ocultar una divergencia:

- `privacidad.html` afirma que los formularios generales exigen aceptar la política;
- Home/Fragmento inspeccionados no presentan ese checkbox;
- `submitNewsletter(..., gdprId, ...)` recibe el ID pero el handler genérico no lo valida;
- lectores beta sí valida su consentimiento propio.

El registry no puede «resolver» esa divergencia. Debe corregirse mediante una edición segura y una decisión factual del contrato de consentimiento; no mediante una conclusión jurídica improvisada.

## Qué queda para I.2 después de #206

I.2 actúa como **vista/privacy contract** sobre la autoridad E.8, no como segundo sistema. Trabajo futuro legítimo:

1. revisar periódicamente evidencia de vendors;
2. completar campos privacy/retention cuando exista fuente fiable;
3. reconciliar política pública con runtime real;
4. añadir auditor browser live seguro si hace falta comprobar storage/network;
5. actualizar el mismo registry cuando entre o salga un tercero.

## Guardrails

- No duplicar registry/checker.
- No copiar el código de #206 a esta rama mientras ambas PR sigan independientes.
- No declarar «cumple RGPD» desde un checker técnico.
- No asumir `cookieless = no consentimiento en toda jurisdicción`.
- No guardar PII/secrets en artifacts.
- No instalar CMP por checklist sin entender tratamiento real.
- No añadir Clarity u otro tracker para completar el inventario.

## Cierre

I.2 ya no representa una implementación técnica paralela pendiente. Su owner técnico existe en E.8/#206. El estado correcto es **esperar/reutilizar esa autoridad y resolver aparte el drift factual de consentimiento**, no construir una segunda.