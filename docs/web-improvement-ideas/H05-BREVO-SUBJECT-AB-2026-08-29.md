# H.5 · Pruebas A/B de asunto en Brevo

**Estado histórico final de PR #135:** `DEFER`  
**Matriz:** `DEFERIR HASTA MUESTRA`  
**Decisión:** no usar A/B hasta disponer de una audiencia suficientemente grande para que el resultado sea interpretable.  
**Naturaleza:** documentación; no crea campañas.

## 1. Hipótesis original

Aprovechar el A/B nativo de Brevo para probar asuntos sin incorporar otra herramienta.

## 2. Evolución

#135 no rechazó la capacidad; rechazó usarla prematuramente. Revisión, matriz, autoridad final y JSON convergen en `DEFER` hasta tener muestra suficiente.

## 3. Revalidación oficial · 29/08/2026

La ayuda oficial de Brevo sigue indicando:

- A/B testing está disponible en el plan Standard según la página actual de planes;
- una campaña A/B solo puede dirigirse a destinatarios que ya hayan recibido antes una campaña de Brevo;
- para resultados estadísticamente relevantes, Brevo recomienda **al menos 5.000 destinatarios**;
- A/B no puede combinarse con Send time optimization.

Por tanto la cifra conservada por #135 sigue vigente hoy; no debe convertirse en un umbral universal de estadística, pero sí es evidencia suficiente para no ejecutar tests con una lista pequeña.

## 4. Estado del proyecto

El repo no contiene evidencia live de una audiencia que alcance ese orden de magnitud. El snapshot histórico del 20/08 observó 2 contactos en la lista general, dato que `docs/brevo/01` advierte no tratar como actual.

Sin un snapshot live nuevo no se debe ni afirmar escala ni abrir A/B.

## 5. Trigger futuro

- audiencia elegible suficientemente grande;
- historial de campañas estable;
- una sola hipótesis por test;
- métrica relevante definida;
- coste/plan justificado por necesidades reales, no solo por A/B;
- deliverability y tracking configurados de forma coherente con privacidad.

## 6. Qué probar primero cuando haya escala

1. asunto claro vs. curiosity moderada;
2. después CTA o longitud/estructura en tests separados;
3. nunca múltiples variables a la vez en un test simple.

No optimizar clickbait ni aperturas como único KPI. Clicks, respuestas y acciones posteriores aportan señal más robusta.

## 7. Qué no hacer

- No test A/B con decenas/cientos de contactos y declarar un “ganador”.
- No actualizar a Standard solo para sentir que se está optimizando.
- No mezclar A/B y send-time optimization esperando atribuir causalidad.
- No repetir tests sin registrar hipótesis/resultado.
- No usar opens como verdad absoluta.

## 8. Definition of Done si se reabre

- [ ] snapshot live de audiencia elegible;
- [ ] muestra suficiente;
- [ ] hipótesis y variable únicas;
- [ ] métrica primaria definida;
- [ ] variante editorialmente segura;
- [ ] resultado guardado en registro de experimentos;
- [ ] no hay cambio permanente si el resultado es inconcluyente.

## 9. Trazabilidad #135

Banco original; revisión (`DEFER`, >=5.000); matriz (`DEFERIR HASTA MUESTRA`); `docs/brevo/04`; JSON/autoridad final; revalidación independiente. La fuente oficial Brevo se volvió a comprobar el 29/08/2026 y mantiene la recomendación de 5.000.

## 10. Cierre

H.5 es una capacidad útil a escala, no una deuda actual. Hasta que haya muestra, ejecutar un A/B produciría precisión aparente sin información fiable.