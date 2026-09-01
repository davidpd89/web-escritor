# I.5 · Revisión periódica de minimización de datos

**Estado histórico final de PR #135:** `IMPLEMENT_AFTER_CURRENT_DEBT`  
**Matriz intermedia:** `IMPLEMENTAR`  
**Objetivo:** revisar periódicamente qué datos/campos/terceros existen, para qué sirven, cuánto se conservan y cómo se eliminan; retirar lo que dejó de tener finalidad.

## 1. Hipótesis original

I.5 proponía una auditoría anual explícita de data minimization: comparar datos personales realmente guardados por formularios/newsletter/club con los que realmente se usan y purgar lo innecesario.

A diferencia de ideas de “analytics” orientadas a recopilar más, I.5 reduce superficie. #135 la mantuvo como una de las mejoras de privacidad con mejor relación valor/coste.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Auditoría anual de datos guardados vs. usados. |
| Revisión 108/108 | `IMPLEMENT_AFTER_CURRENT_DEBT` | Inventario por campo: finalidad, base, retention, export/delete, owner. |
| Matriz operativa | `IMPLEMENTAR` | Revisión anual de data inventory, purpose, retention, deletion y third parties. |
| Blueprints W8 | implementación compartida | Extender el registro de terceros de E.8/I.2; no crear otra autoridad paralela. |
| Autoridad final | `IMPLEMENT_AFTER_CURRENT_DEBT` | Sí aporta, después de cerrar deuda actual y disponer de baseline fiable. |
| Revalidación independiente | mantenido | I.1–I.5 se mantienen; no aparece razón para ampliar tracking antes de minimizar. |

La bajada de `IMPLEMENTAR` a `IMPLEMENT_AFTER_CURRENT_DEBT` no reduce importancia: evita hacer una revisión periódica sobre un inventario aún incompleto/inconsistente.

## 3. Estado real de `main` al 29/08/2026

### Datos declarados públicamente

`privacidad.html` describe actualmente:

- email + origen de formulario para suscripciones;
- datos que una persona envía voluntariamente por correo;
- GoatCounter y Metricool para métricas agregadas;
- programa de lectores beta con finalidad/lista separadas;
- modo remoto del asistente actualmente desactivado en producción;
- proveedores como Brevo, Cloudflare, GoatCounter, Metricool y Gmail.

### Contrato técnico de newsletter

El Worker mantiene un contrato minimizado:

- email;
- `source` validado contra allowlist;
- `result` solo para quiz y enum acotado;
- honeypot `website`, no reenviado;
- API key/list IDs/atributos arbitrarios no controlados por navegador.

Esto es una buena frontera a preservar.

### Lectores beta

`/lectores-beta/` declara:

- grupo pequeño;
- operación manual;
- sin comunidad pública, perfiles ni foro;
- lista separada de newsletter general;
- consentimiento específico del programa.

### Gap de autoridad

`data/third-party-integrations.json`, creado dentro de la histórica #135 para E.8/I.2, **no existe en `main`** porque #135 no se fusionó.

Por tanto:

- #135 llegó a `IMPLEMENTED_IN_PR` para ese baseline;
- hoy `MERGED_MAIN=false`;
- I.5 no debe crear un segundo inventario;
- cuando se implemente I.2/E.8 en una rama aceptada, I.5 debe usar exactamente esa autoridad.

## 4. Drift actual relevante

La revalidación del lote I/H detectó un drift factual que ilustra por qué I.5 importa:

- la política afirma que el formulario general exige aceptar la política antes de enviar;
- el handler general `submitNewsletter(...)` recibe `gdprId` pero no lo utiliza;
- en Home no se localizó `nl-gdpr-home`;
- lectores beta sí dispone de checkbox propio y el handler beta sí lo valida.

I.5 **no decide aquí la solución jurídica/técnica**. Lo registra como ejemplo de por qué una auditoría debe comparar:

1. política declarada;
2. markup;
3. runtime;
4. datos realmente enviados/guardados;
5. configuración live del proveedor.

## 5. Qué debe contener la autoridad única de datos/terceros

No crear `annual-data-audit.json` separado si `third-party-integrations` puede sostener la información común.

Para cada tratamiento/integración conviene poder responder:

- dato/categoría;
- PII: sí/no;
- finalidad;
- superficie que lo origina;
- sistema/proveedor receptor;
- base/consentimiento según documentación vigente;
- storage/cookies observados;
- hosts de red;
- retención conocida/contractual;
- mecanismo de baja/supresión/export;
- owner operativo;
- fuente de privacidad/proveedor;
- `lastVerified`;
- `nextReview`;
- estado `LIVE / DISABLED / CONDITIONAL / REMOVED`.

No guardar secretos ni PII en el registro.

## 6. Cadencia correcta

“Anual” es un mínimo operativo, no una excusa para esperar doce meses ante cambios.

Revisar también cuando ocurra cualquiera de estos triggers:

- se añade un nuevo vendor/script/Worker;
- se activa Clarity/Brevo Tracker/u otro behavioral tracking;
- aparece un nuevo formulario o finalidad;
- se añade login/perfil/comunidad;
- cambia la automatización de Brevo;
- se añade almacenamiento local de contenido sensible;
- cambia la política de privacidad de un proveedor de forma material;
- se retira una feature pero permanece su dato/configuración;
- se abre venta directa y se empiezan a tratar datos de pedido/envío.

## 7. Procedimiento de auditoría

### Paso A — inventario factual

Enumerar todas las entradas de datos y terceros desde:

- HTML/formularios;
- JS/runtime;
- Workers;
- CSP/network hosts;
- políticas públicas;
- configuración externa cuando exista acceso autorizado.

### Paso B — finalidad

Por cada campo/evento:

> “¿Qué decisión/servicio actual necesita este dato?”

Si no hay respuesta concreta, candidato a retirada.

### Paso C — minimización

Preguntar:

- ¿podemos no recogerlo?
- ¿puede ser agregado?
- ¿puede ser enum en vez de texto libre?
- ¿puede procesarse client-side?
- ¿puede separarse por propósito?
- ¿hace falta conservarlo o basta uso transitorio?

### Paso D — retención y borrado

No aceptar “se conserva mientras sea necesario” como única especificación interna si el sistema permite concretar mejor.

Documentar:

- quién puede borrar;
- dónde se borra;
- qué sistemas secundarios existen;
- si hay export;
- qué ocurre tras unsubscribe;
- qué logs/backup podrían conservar datos y durante cuánto tiempo según el proveedor.

### Paso E — reconcile

Comparar:

- política pública;
- código;
- registro técnico;
- panel externo;
- copy de consentimiento;
- automatizaciones.

Los drifts se convierten en tareas pequeñas separadas, no se “arreglan” silenciosamente dentro del documento anual.

## 8. Salida de cada revisión

Debe producir una tabla resumida, por ejemplo:

| tratamiento | necesidad | minimización | retención | acción |
|---|---|---|---|---|
| newsletter email | necesaria | mantener | verificar proveedor | KEEP |
| `SOURCE` | útil para routing/reporting | enum/allowlist | revisar | KEEP |
| campo/evento sin uso | no demostrada | retirar | borrar según sistema | REMOVE |

Acciones permitidas:

- `KEEP`;
- `REDUCE`;
- `DOCUMENT`;
- `REMOVE`;
- `VERIFY_EXTERNAL`;
- `NO_DATA / UNKNOWN` cuando no hay evidencia.

No convertir desconocidos en afirmaciones.

## 9. Límites

I.5 no autoriza:

- borrar contactos/datos live sin autorización operativa y procedimiento;
- cambiar bases legales por intuición;
- afirmar cumplimiento jurídico total;
- introducir una CMP por checklist;
- almacenar copias de contactos para “auditar”; 
- añadir tracking para comprobar tracking;
- hacer export de PII al repo.

Es una gobernanza técnica/operativa, no asesoramiento jurídico.

## 10. Relación con otras ideas

- **E.8/I.2:** misma autoridad de integraciones; I.5 revisa periódicamente, no duplica.
- **G.5:** logging de preguntas solo tras definir minimización/retención.
- **H.1/H.2:** segmentación/journeys deben respetar propósito y evidencia de consentimiento.
- **I.3:** un evento sin pregunta vigente puede eliminarse en esta revisión.
- **I.4:** reporting agregado, no identity graph.
- **J.1/K.1:** foro o venta directa cambiarían radicalmente el inventario de datos y disparan revisión extraordinaria.
- **P.2:** manuscritos no deben persistirse por defecto.

## 11. Definition of Done de la capacidad

- [ ] existe una única autoridad compartida I.2/E.8/I.5;
- [ ] inventario cubre formularios, runtime, Workers y terceros live;
- [ ] no contiene PII/secretos;
- [ ] cada dato tiene finalidad/owner;
- [ ] retention/delete/export están documentados o marcados `UNKNOWN`;
- [ ] política pública se contrasta con comportamiento real;
- [ ] se documentan drifts;
- [ ] cada dato innecesario tiene acción de retirada separada y segura;
- [ ] existe `lastVerified`/próxima revisión;
- [ ] cambios materiales disparan revisión extraordinaria;
- [ ] no se afirma cumplimiento E2E sin comprobar paneles/configuración live.

## 12. Trazabilidad #135

Revisados:

- `IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis I.5;
- `IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — auditoría anual campo/finalidad/base/retention/export-delete/owner;
- `IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `IMPLEMENTAR`;
- overrides y repo cross-check;
- `IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — W8, extender `data/third-party-integrations.json`;
- baseline E.8/I.2 históricamente entregado en #135, no fusionado;
- autoridad machine-readable;
- `PR135-FINAL-AUTHORITY-2026-08-28.md` — `IMPLEMENT_AFTER_CURRENT_DEBT`;
- `PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — estado mantenido.

## 13. Cierre

I.5 debe funcionar como freno periódico a la entropía: cada nuevo formulario, integración o flujo tiende a añadir datos; esta revisión obliga a demostrar que siguen siendo necesarios y a retirar lo que dejó de serlo, usando una sola autoridad factual compartida con I.2/E.8.