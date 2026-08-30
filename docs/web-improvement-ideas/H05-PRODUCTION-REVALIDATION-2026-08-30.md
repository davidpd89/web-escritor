# H.5 · Revalidación de producción — A/B de asuntos en Brevo

**Fecha:** 2026-08-30  
**Base:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `DEFER · SAMPLE_GATE_NOT_MET · BREVO_5000_GUIDANCE_CURRENT · NO_CAMPAIGN_CHANGE · NO_CODE`

## Estado actual

No existe en el repositorio evidencia live de que la lista elegible tenga una escala próxima a la necesaria para interpretar un A/B de asunto con rigor. El único conteo documentado procede del snapshot real del 20/08/2026 y se conserva expresamente como dato histórico, no como cifra actual.

Por tanto H.5 no es una deuda de implementación.

## Revalidación oficial de Brevo

La ayuda oficial de Brevo consultada el 30/08/2026 mantiene tres condiciones relevantes:

- los A/B solo pueden enviarse a destinatarios que ya hayan recibido una campaña previa;
- para resultados estadísticamente relevantes recomienda al menos **5.000 destinatarios**;
- una campaña A/B no puede usar simultáneamente `Send at best time`.

La cifra de 5.000 es recomendación operativa de Brevo para su producto, no una ley estadística universal. En este proyecto es una razón suficiente para no producir confidence theater con una audiencia pequeña.

## Qué debe existir antes de reabrir

1. snapshot live/read-only de audiencia elegible;
2. historial de campañas suficiente;
3. deliverability estable;
4. una hipótesis única;
5. métrica primaria registrada antes de enviar;
6. variantes editorialmente seguras;
7. suficiente muestra para interpretar el resultado;
8. decisión explícita de qué cambia si gana A, gana B o queda inconcluyente.

## Métrica

No usar apertura como verdad absoluta. H.4 y `docs/brevo/03` ya documentan las distorsiones de Apple MPP, proxies y bots. Cuando exista escala, clicks legítimos, respuestas y acciones posteriores deben complementar o sustituir la apertura según la hipótesis.

## No implementar ahora

- No campaña A/B.
- No upgrade de plan por esta idea.
- No dividir muestras pequeñas para obtener un «ganador» aparente.
- No mezclar A/B y send-time optimization.
- No testear múltiples variables a la vez.
- No cambiar permanentemente un asunto por una diferencia inconcluyente.

## Cierre

H.5 permanece `DEFER`. El trigger es muestra e historial reales, no la disponibilidad técnica del botón A/B en Brevo.