# H.2 · Welcome series automatizada

**Estado histórico final de PR #135:** `IMPLEMENT_AFTER_CURRENT_DEBT`  
**Estados previos:** `ALREADY_COVERED` → `IMPLEMENTAR TRAS E2E`  
**Decisión:** no añadir una secuencia de bienvenida hasta demostrar DOI, aislamiento de listas y entrega básica actuales.  
**Naturaleza:** documentación; no modifica Brevo ni activa automatizaciones.

## 1. Hipótesis original

H.2 proponía 3–4 emails tras confirmar DOI para presentar progresivamente el universo, en lugar de un único mensaje.

#135 redujo el alcance: la secuencia no es prioritaria si el journey base todavía no está probado. La arquitectura Brevo posterior incluso propone un welcome compacto de uno y, solo si aporta, un segundo email; no una secuencia larga por defecto.

## 2. Evolución

| Etapa | Estado | Consecuencia |
|---|---|---|
| Banco original | hipótesis | 3–4 emails tras DOI. |
| Revisión 108/108 | `ALREADY_COVERED` | El plan Brevo ya describía welcome journey. |
| Matriz | `IMPLEMENTAR TRAS E2E` | Primero DOI/entrega/aislamiento. |
| Autoridad final | `IMPLEMENT_AFTER_CURRENT_DEBT` | #136/correcciones de entrega no equivalen a welcome series live. |
| JSON | `IMPLEMENT_AFTER_CURRENT_DEBT` | Estado final. |
| Revalidación independiente | mantenido | No superponer automatización nueva a un journey incierto. |

## 3. Estado actual de `main`

La integración sí implementa una petición DOI segura: navegador → Worker → endpoint Brevo de doble confirmación. El cliente solo acepta como éxito `pending_confirmation`.

Pero el propio código/documentación vigente mantiene este gate:

- templates `Bienvenida_Samuel_*`/`Automatización #2_step_*` fueron observados históricamente;
- sus nombres no prueban que estén activos;
- la API usada no expuso el estado de workflows;
- hay que verificar en panel si una alta en `Lectores web` dispara algo;
- el copy del cliente evita prometer automáticamente el capítulo porque esa entrega no está demostrada.

Por tanto `DOCUMENTED`/`template exists` no es `CONFIGURED_LIVE` ni `VERIFIED_E2E`.

## 4. Incongruencia previa que bloquea expansión

La revalidación del lote detectó que `privacidad.html` afirma que los formularios generales exigen aceptar la política, pero el handler general recibe `gdprId` sin usarlo y Home no contiene `nl-gdpr-home`.

Antes de aumentar journeys hay que reconciliar esa base factual/consentimiento en su autoridad correspondiente.

## 5. Orden correcto

1. Verificar DOI real con dirección controlada.
2. Confirmar lista correcta y aislamiento beta.
3. Auditar workflows activos en panel Brevo.
4. Comprobar qué email se envía realmente tras confirmar.
5. Reconciliar copy/promesas/privacidad.
6. Probar baja y preferencias.
7. Solo entonces diseñar welcome incremental.

## 6. Diseño recomendado cuando se abra

Primer piloto mínimo:

- **Email 1:** bienvenida inmediata, qué recibirá, una acción útil y preferencias/baja.
- **Email 2 opcional:** varios días después, solo si existe contenido genuinamente útil y no repite la campaña de lanzamiento.

Segmentaciones específicas por Manecillas/Samuel solo después de H.1 y de consentimiento/preferencias claras.

No crear siete pasos ni varios funnels por `SOURCE` con una lista pequeña.

## 7. Contenido y límites

- hechos de libros/disponibilidad revisados por humano;
- no afirmar retailer/precio/fecha sin verificar;
- beta no entra en welcome general sin otro opt-in;
- DOI es confirmación, no email promocional;
- frecuencia compatible con la promesa pública de “sin boletines frecuentes”;
- templates base reutilizables, no uno completo por campaña.

## 8. Definition of Done futura

- [ ] DOI E2E demostrado;
- [ ] workflows legacy inventariados KEEP/REWRITE/PAUSE/ARCHIVE;
- [ ] aislamiento beta probado;
- [ ] consentimiento/copy reconciliado;
- [ ] welcome activado en cuenta correcta;
- [ ] entrada y reentrada documentadas;
- [ ] baja/preference links probados;
- [ ] QA Gmail/Outlook/mobile/plain text/dark mode/accesibilidad;
- [ ] email de prueba recibe exactamente la secuencia esperada;
- [ ] evidencia externa registra `CONFIGURED_LIVE`/`VERIFIED_E2E`.

## 9. Qué no hacer

- No activar por existir templates con nombres sugerentes.
- No duplicar journeys legacy sin auditarlos.
- No prometer capítulo/lead magnet no verificado.
- No mezclar beta y general.
- No añadir frecuencia artificial para “engagement”.
- No interpretar #136 u otra corrección parcial como serie implementada.

## 10. Trazabilidad #135

Banco original; revisión (`ALREADY_COVERED`); matriz (`IMPLEMENTAR TRAS E2E`); `docs/brevo/01` y `04`; JSON final; autoridad final; revalidación independiente. Las pasadas posteriores no aportan evidencia live que elimine el gate.

## 11. Cierre

H.2 sigue aprobado conceptualmente, pero **la automatización nueva viene después de la prueba de la automatización existente**. El deliverable correcto ahora es preservar ese orden y no convertir un plan Brevo en una afirmación de producción.