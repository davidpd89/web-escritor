# H.1 · Revalidación de producción — segmentación por intereses

**Fecha:** 2026-08-30  
**Base:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `IMPLEMENT_AFTER_CONSENT_CONTRACT_RECONCILIATION_AND_ACCOUNT_E2E · SOURCE_IS_NOT_PREFERENCE · CONSENT_GROUPS_PLAN_GATED · NO_CODE`

## Estado real

El Worker y la web ya capturan `SOURCE`, pero ese atributo describe **procedencia del formulario**, no consentimiento temático. No debe reinterpretarse como «interés elegido».

`docs/brevo/01-ESTADO-ACTUAL-Y-GAPS.md` documenta que la única auditoría real de cuenta conservada es la del 20/08/2026 y que automatizaciones/estado live siguen detrás de comprobación manual. No existe evidencia suficiente para afirmar que un preference center o Consent Groups estén configurados en la cuenta actual.

## Bloqueo previo detectado

Existe una incongruencia factual en `main`:

- `privacidad.html` afirma que los formularios de suscripción exigen aceptar la política;
- Home no contiene `nl-gdpr-home`;
- el handler genérico recibe `gdprId` pero no consulta/valida ese control;
- la validación explícita de checkbox localizada corresponde al flujo separado de lectores beta.

Antes de añadir más granularidad de consentimiento hay que reconciliar el contrato básico ya publicado.

## Consent Groups hoy

La documentación oficial actual de Brevo confirma que Consent Groups permiten preferencias por tema, pero siguen disponibles únicamente en planes **Professional y Enterprise**. Activarlos además hace obligatorio asociar campañas/automatizaciones a grupos de consentimiento.

No se recomienda upgrade solo para satisfacer H.1.

## Arquitectura correcta futura

Si la escala y el plan lo justifican:

- `Novedades de libros`;
- `Cuaderno y recursos`;
- `Eventos y encuentros`.

Pocos grupos estables, no uno por libro/página.

Si Consent Groups no están disponibles, una solución con listas/atributos solo es aceptable si conserva consentimiento específico, preference update, baja total inequívoca y trazabilidad; no usar `SOURCE` como sustituto.

## Definition of Done antes de implementar

1. corregir/reconciliar copy y comportamiento de consentimiento actual;
2. snapshot live read-only de cuenta;
3. confirmar plan/feature availability;
4. decidir modelo de preferencias;
5. E2E con contactos de prueba controlados;
6. actualizar privacidad y copy de alta;
7. comprobar baja total + cambio de preferencias;
8. no migrar contactos a intereses que nunca eligieron.

## Cierre

H.1 sigue siendo deseable a escala, pero no es una feature lista para código. El orden correcto es **consentimiento base → evidencia live → preferencias**, no segmentación primero.