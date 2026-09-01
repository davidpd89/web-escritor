# G.5 · Preguntas frecuentes reales a partir del asistente

**Estado histórico final de PR #135:** `DEFER`  
**Etapa intermedia:** `CONDICIONAL PRIVACY-FIRST`  
**Decisión:** no almacenar consultas del asistente por curiosidad; solo reabrir con una pregunta de negocio/editorial concreta, minimización, agregación y retención definida.  
**Naturaleza de esta PR:** documentación; no añade logging ni telemetría.

## 1. Hipótesis original

G.5 proponía aprovechar preguntas reales realizadas al asistente para detectar dudas repetidas y convertirlas en FAQ o contenido del Cuaderno, siempre de forma agregada y sin PII.

La utilidad potencial es real, pero #135 detectó que la propuesta cambia el tratamiento de datos: para contar preguntas primero hay que recogerlas. Esa nueva captación no puede justificarse solo porque “quizá algún día sirva”.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Agregar preguntas del asistente y alimentar contenido real. |
| Revisión 108/108 | `DEFER` | Logging de preguntas cambia privacidad/PII; necesidad clara primero. |
| Matriz operativa | `CONDICIONAL PRIVACY-FIRST` | Solo con retención, minimización y sin guardar conversaciones innecesarias. |
| Autoridad final | `DEFER` | No almacenar conversaciones por curiosidad. |
| JSON final | `DEFER` | Estado machine-readable definitivo. |
| Revalidación independiente | mantenido | IA/analítica no debe abrir retención de prompts sin propósito. |

La etapa `CONDICIONAL PRIVACY-FIRST` explica cómo podría reabrirse; no convierte G.5 en una tarea pendiente.

## 3. Revalidación de `main` · 29/08/2026

La inspección actual de `assets/assistant.js` y `assets/assistant-config.js` muestra:

- búsqueda local/Pagefind como base;
- `remote: false` en la configuración actual;
- no se ha encontrado un mecanismo cliente que persista las preguntas para analítica editorial;
- no debe afirmarse que el asistente ya registra prompts.

La política de privacidad vigente además dice que la búsqueda local funciona en navegador y que el modo remoto está actualmente desactivado; si se activase, describe un identificador temporal de sesión y el envío técnico de la consulta para responderla. Eso **no equivale** a autorizar retención/analítica posterior de esas consultas.

## 4. Relación con C.3

C.3 sí recomienda convertir preguntas reales repetidas en contenido. G.5 no contradice esa idea: solo rechaza convertir el asistente en una nueva fuente de datos antes de demostrar que hace falta.

Fuentes de demanda menos invasivas pueden ser primero:

- Search Console/Bing agregados;
- preguntas recibidas voluntariamente por email/redes;
- feedback de clubes/lectores;
- observaciones editoriales documentadas.

Solo si esas fuentes no bastan y el asistente tiene uso suficiente podría reabrirse G.5.

## 5. Trigger estricto de reevaluación

Antes de escribir código debe existir un documento que responda:

1. ¿qué decisión concreta cambiará con el dato?;
2. ¿por qué no basta una fuente agregada ya existente?;
3. ¿qué campo mínimo se necesita?;
4. ¿se necesita texto crudo o basta una categoría/contador?;
5. ¿cómo se elimina PII/texto sensible accidental?;
6. ¿cuánto tiempo se conserva?;
7. ¿quién accede?;
8. ¿cómo se borra/exporta cuando corresponda?;
9. ¿qué cambio exige la política de privacidad?;
10. ¿qué volumen mínimo hace útil el análisis?

Si no hay respuestas, el estado sigue siendo `DEFER`.

## 6. Diseño privacy-first si algún día se activa

Preferir una arquitectura de **reducción temprana**:

`consulta → clasificación/local redaction → contador agregado → descarte del texto crudo`

antes que:

`consulta completa → base de datos indefinida → análisis futuro`

Cuando sea viable, registrar categorías cerradas o señales derivadas, no conversaciones completas.

Ejemplo conceptual:

```json
{
  "topic": "availability_manecillas",
  "count": 1,
  "period": "2026-W36"
}
```

No necesita email, IP, session id persistente ni texto literal para responder “¿qué temas se repiten?”.

## 7. Datos que no deben capturarse por defecto

- email o identidad del visitante;
- IP como clave editorial;
- conversación completa;
- texto seleccionado/manuscritos;
- URL con parámetros sensibles;
- identificadores cross-session;
- fingerprinting;
- datos derivados de otras herramientas para formar un perfil.

## 8. Riesgos

- Una consulta puede contener PII aunque no se solicite.
- Puede contener texto inédito/copyright del propio usuario.
- Un dataset pequeño puede llevar a conclusiones falsas.
- Guardar texto “por si acaso” crea deuda de privacidad y seguridad.
- El feedback del asistente puede estar sesgado por los ejemplos/UX del propio widget.
- Convertir cada pregunta rara en contenido produciría thin/scaled content.

## 9. Definition of Done si se reabre

- [ ] pregunta decisional explícita;
- [ ] volumen mínimo definido;
- [ ] schema de datos mínimo;
- [ ] no PII por diseño o redacción antes de persistir;
- [ ] retención y borrado definidos;
- [ ] política/consentimiento revisados cuando proceda;
- [ ] test que impida almacenar campos no autorizados;
- [ ] reporting agregado;
- [ ] C.3 consume solo patrones repetidos, no consultas individuales identificables;
- [ ] kill switch/eliminación del experimento si no cambia decisiones.

## 10. Qué no hacer

- No habilitar logging raw porque “los datos pueden ser útiles”.
- No añadir un analytics SaaS solo para prompts.
- No almacenar conversaciones para entrenar o perfilar sin una decisión separada.
- No mezclar session ids temporales del runtime con identidad de newsletter.
- No afirmar anonimato si se guarda texto libre sin revisar.
- No construir FAQ automáticamente desde frecuencia sin revisión editorial/canon.

## 11. Trazabilidad #135

Revisados:

- `IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original.
- `IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `DEFER` por privacidad/PII.
- `IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `CONDICIONAL PRIVACY-FIRST`.
- `data/web-improvement-decisions-2026-08-28.json` — final `DEFER`.
- `PR135-FINAL-AUTHORITY-2026-08-28.md` — minimización/retención/PII antes de preguntas del asistente.
- `PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — decisión mantenida.
- C.3/I.5 y documentos de privacidad/IA — relaciones revisadas.
- pasadas posteriores — no aportan un trigger que justifique logging actual.

## 12. Cierre

La idea de aprender de preguntas reales sigue siendo buena; la fuente no tiene por qué ser una base de conversaciones. G.5 queda diferida hasta poder demostrar que la señal del asistente es necesaria y que puede obtenerse con una huella de datos mínima.