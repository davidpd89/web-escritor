# H.4 · Revalidación de producción — win-back / re-engagement

**Fecha:** 2026-08-30  
**Base:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `DEFER · SCALE_AND_ENGAGEMENT_TRIGGER_NOT_MET · OPENS_NOT_PRIMARY_SIGNAL · NO_CODE`

## Estado real

La última cifra de contactos documentada en repo procede de una auditoría real del **20/08/2026** y fue una fotografía histórica de 2 suscriptores en la lista general. No debe reutilizarse como conteo actual.

No existe evidencia live actual que demuestre una población suficientemente grande de suscriptores inactivos como para que un win-back resuelva un problema real.

## Señal de engagement

`docs/brevo/03-CONSENTIMIENTO-PRIVACIDAD-Y-PREFERENCIAS.md` ya establece que las aperturas no deben ser KPI principal. La documentación actual de Brevo confirma que Apple Mail Privacy Protection y actividad de bots pueden inflar aperturas y clics, haciendo más difícil inferir comportamiento humano real.

Por tanto un futuro trigger no debe ser simplemente `no_open_90_days`.

## Señales preferidas si algún día hay escala

Combinación de evidencia más robusta, según disponibilidad y consentimiento:

- entrega real;
- clicks filtrados/legítimos;
- respuestas;
- acciones explícitas;
- visitas/conversiones agregadas mediante UTM + analítica propia;
- feedback;
- bajas/quejas;
- historial suficiente de campañas.

No instalar Brevo Tracker para conseguir la señal de H.4: el propio contrato de privacidad actual lo mantiene fuera por defecto.

## Trigger de reapertura

Solo cuando exista:

1. volumen material de contactos confirmados;
2. historial de envíos suficiente;
3. definición operacional de «inactivo» que no dependa solo de opens;
4. objetivo explícito (reactivar, reducir presión, limpiar audiencia, preferencias);
5. política de retención/supresión;
6. E2E de baja y preferencias;
7. medición de éxito.

## Diseño futuro mínimo

Si el trigger se cumple:

- un email útil de reactivación;
- opcional segundo recordatorio;
- después reducir presión/excluir de campañas frecuentes si no responde;
- no usar urgencia falsa ni amenazas de borrado que no sean ciertas.

## No implementar ahora

- No workflow win-back.
- No segmentos por apertura aislada.
- No tracking web adicional.
- No limpieza destructiva automática.
- No upgrade de plan por esta idea.

## Cierre

H.4 permanece `DEFER`. Optimizar re-engagement sin audiencia/historial demostrados sería construir complejidad alrededor de un problema todavía no medido.