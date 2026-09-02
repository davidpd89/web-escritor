# H.2 · Revalidación de producción — welcome series

**Fecha:** 2026-08-30  
**Base:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `IMPLEMENT_AFTER_CONSENT_FIX_AND_LIVE_AUTOMATION_EVIDENCE · DOI_CONTRACT_STRONG · DELIVERY_NOT_VERIFIED · NO_CODE`

## Estado real

El contrato web/Worker de double opt-in está bien delimitado: formulario propio → Worker → Brevo DOI → confirmación. La UI posterior al submit dice correctamente que falta confirmar el correo y no afirma que la persona ya esté suscrita.

Esto no demuestra una welcome series activa. `docs/brevo/01-ESTADO-ACTUAL-Y-GAPS.md` conserva una auditoría del 20/08 que vio templates con nombres `Bienvenida_Samuel_*`, pero deja expresamente sin verificar si siguen activos, conectados a una automatización o editorialmente vigentes.

## Bloqueos previos

1. Reconciliar la incongruencia actual de consentimiento entre `privacidad.html`, los formularios generales y `script.js`.
2. Ejecutar auditoría live/read-only de automatizaciones antes de asumir que existe cualquier journey.
3. Revisar templates legacy de Samuel para impedir que nuevas altas de Manecillas entren por error.

## Diseño aprobado si se activa

Welcome compacto:

1. email inmediato tras DOI confirmado: identidad, expectativas, primera acción útil y gestión de preferencias;
2. opcionalmente un segundo email varios días después **solo si existe contenido realmente útil**.

No crear secuencia de 5–7 emails por defecto.

## Guardrails

- DOI no es welcome marketing.
- No disparar welcome antes de confirmación.
- No prometer descargas/capítulos que el journey no entregue realmente.
- No mezclar beta con newsletter general.
- No personalizar por `SOURCE` como si fuese consentimiento temático.
- No reactivar templates legacy sin auditarlos.
- Copy final humano y factual.

## Evidencia requerida

Antes de código o activación externa:

- workflow real identificado;
- trigger y reentrada;
- lista/audiencia;
- exclusiones;
- templates;
- delays;
- tracking/privacy;
- prueba con contacto controlado;
- evidencia de DOI → alta confirmada → welcome esperado;
- baja/preferencias verificadas.

## Cierre

H.2 no está rechazada. Está bloqueada por una secuencia correcta de trabajo: **consentimiento base → E2E live → welcome mínimo**. La existencia de templates no es evidencia de funcionamiento.

## Actualización — 2026-09-02

El bloqueo 1 de arriba ("reconciliar la incongruencia actual de consentimiento") está resuelto: el autor decidió que ningún formulario de newsletter del sitio exige casilla — email + enviar, sin excepción — y `privacidad.html` se corrigió para describirlo (PR #319). Los bloqueos 2 (auditoría live/read-only de automatizaciones) y 3 (revisar templates legacy de Samuel) siguen abiertos y sin evidencia; H.2 sigue sin poder activarse hasta que ambos se cierren con evidencia real, no solo el primero.