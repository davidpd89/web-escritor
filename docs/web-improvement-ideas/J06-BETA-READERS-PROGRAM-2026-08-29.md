# J.6 · Programa de lectores beta / primeros lectores

**Estado histórico final de PR #135:** `PARTIAL_AUDIT`  
**Matriz intermedia:** `YA_CUBIERTO PARCIAL`  
**Regla:** el programa y buena parte de su arquitectura ya existen; verificar aislamiento/routing E2E y preservar el proceso para futuras obras antes de ampliarlo.

## 1. Hipótesis original

J.6 proponía formalizar un programa de “primeros lectores” con acceso anticipado a fragmentos/material de *Las manecillas del recuerdo*.

La inspección de #135 descubrió que la idea no partía de cero: el sitio ya había construido una página de lectores beta, un propósito separado y código Brevo específico. Además, para Manecillas la fase beta estaba ya muy avanzada/casi cerrada.

Por ello la idea pasó de “crear programa” a **auditar y conservar correctamente una capacidad ya parcialmente existente**.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Formalizar primeros lectores y acceso anticipado para Manecillas. |
| Revisión 108/108 | `PARTIAL_AUDIT` | Infra beta existe; Manecillas está cerca de cerrar esa fase; terminar aislamiento Brevo. |
| Matriz operativa | `YA_CUBIERTO PARCIAL` | Programa ya existe en arquitectura/Brevo; cerrar routing E2E antes de ampliar. |
| Repo/operación | separación por finalidad | Beta debe usar lista/consentimiento propios y nunca caer silenciosamente en newsletter general. |
| Autoridad final | `PARTIAL_AUDIT` | Verificar lo existente y preservar proceso para futuras obras. |
| Revalidación independiente | mantenido | Evitar identidad/moderación/comunidad adicional sin demanda. |

No debe degradarse esta conclusión a “hay que lanzar un programa beta nuevo”. La capacidad está parcialmente construida; lo que falta es evidencia operativa.

## 3. Estado real de `main` al 29/08/2026

### Página `/lectores-beta/`

La página actual:

- existe y está `noindex`;
- describe un **programa privado**;
- explica que el grupo es pequeño y la operación es manual;
- declara que no hay comunidad pública, perfiles ni foro;
- explica que no existe contraprestación económica;
- recoge email para la finalidad específica de lectores beta;
- incluye checkbox de consentimiento explícito;
- enlaza a privacidad;
- dice que la lista es independiente de la newsletter general.

Además existe una ruta distinta para autores que quieren enviar su manuscrito a valoración beta. Esa operación **no debe confundirse** con el programa de lectores que prueban material propio del autor.

### Cliente `script.js`

El handler beta:

- usa el mismo endpoint técnico de suscripción;
- valida email;
- valida específicamente `lectores-beta-gdpr`;
- envía `source: "lectores-beta"`;
- espera estado DOI `pending_confirmation`;
- muestra copy específico del programa;
- no reutiliza el propósito genérico de newsletter.

### Worker

`cloudflare-worker-subscribe.js` trata `lectores-beta` como finalidad/lista separada:

```text
SEPARATE_LIST_ENV_KEY["lectores-beta"] = "BREVO_BETA_LIST_ID"
```

Consecuencia crítica:

- beta no usa `BREVO_LIST_ID` general;
- si `BREVO_BETA_LIST_ID` falta o es inválida, el Worker falla cerrado;
- nunca debe hacer fallback silencioso a la lista general.

Esta frontera debe conservarse.

## 4. Qué NO demuestra el código

El repositorio demuestra diseño/implementación, pero no puede probar por sí solo:

- que la lista beta exista hoy en la cuenta Brevo;
- su ID real;
- que `BREVO_BETA_LIST_ID` esté configurada en el Worker desplegado;
- que el DOI real funcione en producción;
- que el contacto termine exclusivamente en la lista beta;
- que no exista un workflow live que lo añada después a otra lista;
- que unsubscribe/baja funcionen como se espera;
- que plantillas/automatizaciones actuales respeten la finalidad.

Por eso el estado correcto sigue siendo `PARTIAL_AUDIT`, no `ALREADY_COVERED` ni `VERIFIED_E2E`.

## 5. Momento editorial de Manecillas

La página canónica actual de *Las manecillas del recuerdo* declara publicación el **3 de septiembre de 2026**. La fecha de esta revalidación es **29 de agosto de 2026**.

Por tanto quedan pocos días para la publicación. No tiene sentido inventar ahora una nueva campaña de “lectura beta anticipada de Manecillas” solo para completar J.6.

La decisión de #135 sigue siendo más sólida:

- cerrar/verificar la infraestructura;
- no reabrir una fase editorial casi terminada;
- preservar el patrón para una futura obra donde exista tiempo real para feedback y cambios.

## 6. Checklist E2E imprescindible

Antes de decir que J.6 está operativa:

### Cuenta Brevo

- [ ] existe una lista beta separada;
- [ ] su propósito/nombre son inequívocos;
- [ ] no es la lista general `Lectores web`;
- [ ] no hay automatización que mezcle automáticamente ambas finalidades.

### Worker/configuración

- [ ] `BREVO_BETA_LIST_ID` configurada en el entorno live;
- [ ] `BREVO_API_KEY`/DOI template/redirect correctos;
- [ ] rate limiting/bindings revisados;
- [ ] origen permitido correcto;
- [ ] no hay fallback a `BREVO_LIST_ID`.

### Alta real controlada

Con una dirección de prueba autorizada:

1. enviar formulario beta desde producción;
2. recibir DOI;
3. confirmar;
4. verificar que el contacto queda en beta;
5. verificar que no entra en newsletter general;
6. comprobar atributo `SOURCE` esperado;
7. comprobar copy/redirect;
8. probar baja/retirada del programa.

### Automatizaciones

- [ ] trigger correcto;
- [ ] contenido/material correcto;
- [ ] sin envío promocional ajeno al propósito;
- [ ] reentrada/delays razonables;
- [ ] workflow no sigue activo tras cerrar un proyecto beta si ya no procede.

## 7. Proceso reutilizable para futuras obras

Una futura beta debería separar fases:

### A. Definición

- objetivo del feedback;
- versión del manuscrito/material;
- tipo de lector buscado;
- número aproximado;
- calendario;
- qué cambios todavía son posibles.

### B. Captación

- consentimiento específico;
- expectativas claras;
- no prometer selección automática;
- criterios transparentes si hay cupo.

### C. Distribución

- canal seguro/adecuado;
- control de versión;
- rights/confidencialidad si aplica;
- no publicar material no autorizado en URLs indexables.

### D. Feedback

- preguntas concretas;
- minimizar PII;
- no convertir la participación en comunidad pública obligatoria;
- canal de retirada.

### E. Cierre

- agradecer;
- cerrar automatizaciones temporales;
- retirar material obsoleto;
- revisar retención;
- documentar aprendizajes para siguiente obra.

## 8. No mezclar beta con newsletter general

Esta es la restricción más importante de J.6.

Un lector que acepta recibir material beta y solicitudes de feedback **no ha aceptado automáticamente**:

- novedades generales;
- promociones de otros libros;
- campañas frecuentes;
- SMS/WhatsApp;
- seguimiento web individual.

Si desea newsletter general, necesita el flujo/consentimiento correspondiente.

No usar “segmentación” para borrar la separación de propósitos.

## 9. Operación manual no es un defecto

Con un grupo pequeño, operación manual puede ser mejor que automatizar:

- selección;
- envío de material;
- recordatorios;
- recogida de feedback;
- cierre.

Automatizar solo pasos repetitivos y seguros después de demostrar que el flujo real lo necesita. No convertir J.6 en CRM complejo.

## 10. Privacidad y datos

La revisión de I.5 debe incluir el programa beta:

- email;
- fuente/consentimiento;
- feedback recibido;
- posibles archivos/materiales;
- retención;
- baja;
- sistemas donde termina cada dato.

No almacenar en el repo:

- contactos;
- respuestas privadas identificables;
- manuscritos de terceros;
- secretos Brevo.

## 11. Relación con otras ideas

- **H.1/H.2:** primero cerrar evidencia E2E y separación de journeys.
- **I.2/I.5:** inventario, propósito, consentimiento y retención.
- **J.1:** beta no necesita foro/perfiles.
- **J.4:** participación beta no necesita badges.
- **J.5:** preguntas pueden reutilizarse editorialmente solo con permiso/contexto adecuados.
- **C.4:** cualquier fragmento/material beta está sujeto a derechos.

## 12. Qué no hacer

- No lanzar una nueva beta de Manecillas por calendario artificial a días de publicación.
- No considerar una lista “diseñada” como lista live verificada.
- No hacer fallback de beta a newsletter general.
- No suscribir automáticamente a marketing general.
- No crear perfiles/comunidad para lectores beta.
- No mezclar el flujo de lectores de obra propia con el servicio/ruta de manuscritos de otros autores.
- No guardar PII/material privado en Git.
- No afirmar E2E hasta ejecutar una prueba real controlada.

## 13. Definition of Done de la auditoría

- [ ] página/copy beta siguen alineados con finalidad;
- [ ] handler valida consentimiento específico;
- [ ] lista beta live verificada;
- [ ] `BREVO_BETA_LIST_ID` live verificada;
- [ ] DOI probado en producción con contacto controlado;
- [ ] contacto no aparece en lista general por el flujo beta;
- [ ] workflows live auditados;
- [ ] baja probada;
- [ ] retención/owner documentados;
- [ ] proceso de futura obra preservado;
- [ ] Manecillas no reabre una fase beta sin utilidad editorial real.

## 14. Trazabilidad #135

Revisados:

- banco original J.6;
- revisión 108/108: `PARTIAL_AUDIT`, infraestructura existente y fase Manecillas casi cerrada;
- matriz final: `YA_CUBIERTO PARCIAL`, terminar aislamiento/routing E2E;
- documentación/arquitectura Brevo;
- repo cross-check/overrides;
- autoridad machine-readable;
- autoridad humana final: `PARTIAL_AUDIT`;
- revalidación independiente: estados J mantenidos.

## 15. Cierre

J.6 no necesita otra “feature de beta readers”. Necesita demostrar que la separación ya diseñada funciona realmente de extremo a extremo y convertir ese patrón en un proceso reutilizable para la siguiente obra, sin forzar una nueva beta de Manecillas cuando la publicación ya es inminente.