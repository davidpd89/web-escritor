# H.1 · Segmentación de newsletter por interés

**Estado histórico final de PR #135:** `IMPLEMENT_AFTER_CURRENT_DEBT`  
**Estados previos:** `ALREADY_COVERED` → `IMPLEMENTAR TRAS E2E`  
**Decisión:** la segmentación aporta, pero solo después de demostrar DOI, routing, consentimiento y entrega actuales end-to-end.  
**Naturaleza de esta PR:** documentación; no cambia listas, segmentos ni cuenta Brevo.

## 1. Hipótesis original

H.1 proponía segmentar la newsletter por interés declarado: Samuel, Manecillas y general, usando capacidades ya disponibles en Brevo para reducir mensajes irrelevantes.

## 2. Evolución y contradicción histórica

| Etapa | Estado | Lectura correcta |
|---|---|---|
| Banco original | hipótesis | Dar a cada suscriptor contenido relevante. |
| Revisión 108/108 | `ALREADY_COVERED` | `docs/brevo/` ya diseñaba listas por propósito y segmentos/intereses. |
| Matriz operativa | `IMPLEMENTAR TRAS E2E` | El diseño no basta: primero journeys actuales. |
| Autoridad final | `IMPLEMENT_AFTER_CURRENT_DEBT` | Preferencias/segmentos sí, pero no encima de DOI/entrega inciertos. |
| JSON final | `IMPLEMENT_AFTER_CURRENT_DEBT` | Estado definitivo. |
| Revalidación independiente | mantenido con corrección | Consent Groups eran premium; no justificar upgrade solo por esa feature. |

La transición desde `ALREADY_COVERED` es importante: **documentado ≠ configurado en la cuenta ≠ verificado E2E**.

## 3. Estado real de `main` · 29/08/2026

La integración vigente sí ofrece una base sólida:

- formularios propios → `script.js` → Cloudflare Worker → Brevo DOI;
- navegador envía solo `email`, `source` y campos acotados;
- Worker valida `source` server-side;
- lista general históricamente `Lectores web` y beta separada por contrato;
- atributo `SOURCE` existe históricamente y recibe `home`, `fragmento`, `manecillas`, `cuaderno`, etc.;
- staging bloquea altas reales.

Pero hoy **no existe preferencia Samuel/Manecillas/general enviada por el formulario general**. `SOURCE` describe procedencia, no necesariamente consentimiento temático permanente.

Además, el propio `script.js` y `docs/brevo/01...` conservan un gate: que una alta DOI dispare correctamente las automatizaciones/entregas posteriores sigue requiriendo verificación live.

## 4. Hallazgo adicional de revalidación

La política de privacidad vigente afirma que el formulario general exige aceptar la política antes de enviarlo. Sin embargo:

- el handler `submitNewsletter(formId, emailId, gdprId, ...)` recibe `gdprId` pero no lo consulta;
- en la Home inspeccionada no se encontró `nl-gdpr-home`.

Esto debe verificarse/corregirse en la autoridad adecuada antes de ampliar preferencias. Esta PR no mezcla el arreglo porque es docs-only, pero H.1 no puede darse por listo sobre un consentimiento base inconsistente.

## 5. Brevo: revalidación oficial 29/08/2026

La documentación oficial actual mantiene dos opciones distintas:

- **Multi-list subscription** permite seleccionar intereses/listas en formularios;
- **Consent Groups** modelan consentimiento por tema, pero siguen disponibles solo en **Professional/Enterprise**.

Por tanto:

- no subir de plan solo para Consent Groups;
- usar listas/segmentos/atributos disponibles si resuelven la necesidad real y mantienen el consentimiento claro;
- Consent Groups solo si el plan cambia por otra razón o el business case lo justifica.

## 6. Arquitectura correcta

Separar tres conceptos:

1. **Propósito/consentimiento:** qué comunicaciones aceptó recibir.
2. **Interés:** qué tema prefiere.
3. **Procedencia (`SOURCE`):** desde qué superficie llegó.

No asumir `SOURCE=manecillas` = “consentimiento exclusivo para Manecillas”. Puede ser señal inicial, pero el usuario debe poder expresar/cambiar preferencias de forma inequívoca si se usa para segmentación persistente.

## 7. Gate previo obligatorio

Antes de implementar H.1:

- [ ] DOI general verificado en producción con dirección controlada;
- [ ] lista general correcta y aislamiento beta confirmado;
- [ ] automatizaciones existentes inventariadas en panel;
- [ ] promesas de copy ↔ entrega real reconciliadas;
- [ ] mecanismo de consentimiento general reconciliado con privacidad;
- [ ] baja/unsubscribe probado;
- [ ] plan Brevo/feature availability comprobado;
- [ ] modelo de preferencias elegido sin duplicar listas/atributos innecesarios.

## 8. Piloto recomendado

Cuando el gate esté verde, empezar pequeño:

- preferencias de alto nivel, no un grupo por cada URL;
- p.ej. `Obras/novedades`, `Cuaderno/recursos`, `Eventos` o la taxonomía que refleje campañas reales;
- preference center accesible;
- conservar baja total clara;
- medir si la segmentación reduce irrelevancia/bajas y mejora clicks/respuestas.

No crear una microsegmentación Samuel × Manecillas × Noveris × herramienta × fuente con una lista pequeña.

## 9. Qué no hacer

- No confundir documentación con configuración live.
- No inferir consentimiento temático solo desde `SOURCE`.
- No mezclar beta y newsletter general.
- No instalar Brevo Tracker para segmentar si basta información explícita.
- No pagar Professional solo por Consent Groups.
- No crear decenas de listas/grupos sin campañas reales.
- No activar automatizaciones nuevas antes de probar las existentes.

## 10. Definition of Done futura

- preferencias explícitas y comprensibles;
- cambio de preferencias disponible;
- unsubscribe total inequívoco;
- segmentación produce destinatarios correctos;
- beta permanece aislada;
- fixtures/tests no crean contactos reales;
- smoke E2E controlado demuestra DOI → preferencia → campaña/automation correcta;
- privacidad y copy describen el comportamiento real;
- estado se registra como `CONFIGURED_LIVE`/`VERIFIED_E2E` solo con evidencia externa.

## 11. Trazabilidad #135

Revisados: banco original; revisión 108/108 (`ALREADY_COVERED`); matriz (`IMPLEMENTAR TRAS E2E`); autoridades Brevo; JSON final (`IMPLEMENT_AFTER_CURRENT_DEBT`); autoridad final; revalidación independiente con corrección de plan; pasadas posteriores sin autorización para saltar el gate.

## 12. Cierre

H.1 sigue siendo una mejora válida, pero el orden es parte de la solución: **primero demostrar el journey que ya existe; después añadir preferencias**. La arquitectura documentada es una base, no una prueba de funcionamiento.