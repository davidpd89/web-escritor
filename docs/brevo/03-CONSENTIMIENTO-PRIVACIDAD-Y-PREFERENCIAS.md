# 03 — Consentimiento, privacidad y preferencias

**Objetivo:** aprovechar Brevo sin degradar el modelo de privacidad de davidportodiaz.com ni confundir consentimiento para recibir emails con consentimiento para seguimiento individual.

> Este documento es una especificación técnica/operativa, no asesoramiento jurídico. Las decisiones legales definitivas deben validarse cuando sea necesario.

---

## 1. Principios

1. Consentimiento específico por propósito.
2. Double opt-in como estándar de alta.
3. Baja sencilla.
4. Preferencias modificables.
5. Tracking separado del consentimiento de marketing.
6. Minimización de datos.
7. Beta separado de newsletter.
8. No hacer opt-in implícito por usar una herramienta, descargar un recurso o escribir un email.
9. No importar contactos de otras relaciones al marketing sin base adecuada.
10. Guardar evidencia suficiente sin construir un perfil invasivo.

---

## 2. Double opt-in

El Worker actual usa el endpoint oficial de confirmación doble de Brevo. Mantenerlo.

### Estado UI correcto

Después de enviar el formulario:

- no decir `Ya estás suscrito`;
- decir que falta confirmar el email;
- explicar que revise bandeja/spam si procede;
- no disparar journeys de marketing como si estuviera confirmado.

### Template DOI

Debe ser funcional, no promocional.

Contenido recomendado:

- identidad del remitente;
- por qué recibe el mensaje;
- botón/enlace claro de confirmación;
- texto del propósito;
- contacto/privacidad;
- no introducir varios CTAs distractores.

### Versionado

Registrar internamente:

- template ID;
- versión editorial;
- fecha de activación;
- propósito cubierto.

No guardar el ID como dato público si no aporta valor; sí documentarlo en inventario operativo privado cuando corresponda.

---

## 3. Propósitos

### Newsletter general

Contrato actual público aproximado:

- avisos sobre eventos;
- nuevos libros;
- novedades del autor;
- sin boletines frecuentes.

Mientras ese copy siga publicado, las campañas deben respetarlo.

Si se quiere convertir la newsletter en un envío editorial semanal, primero cambiar la propuesta/consentimiento de forma transparente; no reinterpretar un consentimiento antiguo de forma expansiva.

### Lectores beta

Propósito:

- material no publicado;
- peticiones de feedback;
- comunicaciones del proceso beta.

No implica:

- newsletter general;
- promociones de otros libros;
- campañas de recursos;
- WhatsApp/SMS.

### CRM profesional

Una relación de prensa, club o librería no equivale a suscripción a marketing.

Gestionar en CRM y comunicarse en contexto de la relación.

---

## 4. Consent Groups — novedad 2026

Brevo incorporó endpoints oficiales para Consent Groups el 30/06/2026.

Representan categorías de preferencias opt-in/opt-out.

Endpoints, si la feature está habilitada:

- `GET /v3/contacts/consent-groups`
- `POST /v3/contacts/consent-groups`
- `GET /v3/contacts/consent-groups/{id}`
- `PUT /v3/contacts/consent-groups/{id}`
- `DELETE /v3/contacts/consent-groups/{id}`

La API devuelve `403 CONSENT_GROUP_NOT_ENABLED` si la cuenta no tiene la función.

La importación de contactos admite `consentGroupIds` y el detalle del contacto puede devolver sus grupos.

### Propuesta de grupos

Solo si la función está activa:

- `Novedades de libros`
- `Cuaderno y recursos`
- `Eventos y encuentros`

No crear un grupo por cada libro, sección o artículo salvo que haya volumen y una necesidad inequívoca.

### Preference center

Brevo permite incluir Consent Groups en formularios de alta/actualización de perfil.

Crear un formulario de actualización de preferencias que permita:

- consultar temas;
- cambiar temas;
- retirar tracking si se usa;
- baja total clara.

### Precaución crítica

Brevo documenta que `Unsubscribe from all` dentro de Consent Groups elimina al contacto de todos los grupos pero **no necesariamente cambia el global unsubscribe status**. Probar el flujo completo y mantener un enlace de baja total inequívoco.

---

## 5. Pixel tracking de email — cambio importante 2026

Brevo registra normalmente aperturas mediante pixel y clicks mediante links individualizados.

En 2026 Brevo añadió gestión de consentimiento de tracking por contacto y publicó orientación específica en respuesta a la recomendación de la CNIL para contactos franceses.

### Separar dos consentimientos

A. `Quiero recibir emails`.

B. `Acepto seguimiento individual de aperturas/clicks`.

No asumir que A implica B.

### Política conservadora recomendada

Si la cuenta activa la funcionalidad per-contact:

- comportamiento de consentimiento desconocido: **No rastrear individualmente**;
- recopilar consentimiento explícito si realmente se desea analítica individual;
- ofrecer revocación accesible;
- auditar campañas, automatizaciones y transaccionales de propósito comercial;
- valorar tracking totalmente anónimo si permite obtener señal agregada suficiente.

Brevo recomienda fuertemente el default `No` para contactos cuyo consentimiento de tracking es desconocido en el contexto de su guía 2026.

### Francia

Brevo documenta desde abril/julio de 2026 requisitos/recomendaciones específicos derivados de CNIL para emails a contactos franceses, incluido consentimiento separado y enlace para retirar seguimiento.

No extrapolar automáticamente esa redacción como regla jurídica idéntica para todos los países UE, pero usarla como razón adicional para una configuración privacy-first.

### Atributos Brevo-managed

Si se activa esta feature, Brevo gestiona campos de consentimiento de pixel. No crear manualmente atributos duplicados con nombres similares.

---

## 6. Opens no deben ser el KPI principal

Incluso fuera de privacidad:

- Apple Mail Privacy Protection y proxies alteran aperturas;
- imágenes bloqueadas producen falsos negativos;
- bots/filtros pueden producir actividad;
- el open no demuestra lectura ni intención.

Priorizar:

- entrega;
- clicks legítimos;
- respuestas;
- conversion events explícitos;
- UTM + analítica propia;
- reuniones;
- feedback;
- bajas/quejas.

---

## 7. Brevo Tracker

### Qué aporta

Brevo Tracker puede conectar actividad web con:

- Automations;
- Segments;
- Conversations;
- Web Push;
- eventos de páginas/acciones.

Brevo documenta que usa cookies propias o de terceros y envía actividad a la cuenta.

### Estado recomendado AHORA

**NO INSTALAR por defecto.**

La web actual mantiene una política deliberadamente ligera en cookies/tracking. El beneficio incremental con una lista diminuta no compensa aún:

- cambio de privacidad;
- consentimiento/cookie management;
- CSP;
- scripts extra;
- peso/rendimiento;
- complejidad de QA;
- riesgo de sobresegmentación.

### Gate para instalarlo en el futuro

Solo si se puede responder sí a todo:

- [ ] ¿Existe una automatización concreta que necesita comportamiento web?
- [ ] ¿Hay suficiente audiencia para que esa señal cambie decisiones?
- [ ] ¿Existe CMP/consentimiento adecuado?
- [ ] ¿Privacidad/cookies están actualizadas?
- [ ] ¿CSP actualizada?
- [ ] ¿Se ha medido coste de performance?
- [ ] ¿Se ha definido retención?
- [ ] ¿Existe forma de revocar?
- [ ] ¿No podemos resolverlo mejor con un evento explícito server-side?

---

## 8. Events API como alternativa más controlada

Para acciones concretas y con usuario identificado, Events API puede ser menos invasiva que rastrear toda la navegación.

Ejemplos futuros:

- `fragment_downloaded`
- `beta_feedback_submitted`
- `meeting_booked`
- `resource_downloaded`
- `retailer_link_clicked`

### Reglas

- registrar solo eventos útiles;
- no enviar texto libre sensible;
- no inventar `purchase_completed` si no observamos una venta;
- propiedades acotadas;
- server-side cuando sea posible;
- informar en privacidad si cambia el tratamiento.

---

## 9. Formularios nativos Brevo

Brevo ofrece:

- signup full-page/embedded;
- pop-up signup;
- GDPR blocks;
- DOI;
- confirmation pages/emails;
- profile update form;
- Consent Groups;
- preferencias/listas.

### Uso recomendado

No reemplazar los formularios propios actuales.

Sí considerar un formulario Brevo de **actualización de preferencias** si facilita el preference center y reduce código propio.

### Antes de usar un formulario externo/nativo

Comprobar:

- accesibilidad;
- estilo;
- CSP;
- cookies;
- dominio/hosting;
- atribución de source;
- DOI;
- comportamiento de baja;
- Consent Groups;
- analytics.

---

## 10. Popup

Ya existe popup propio.

No instalar popup Brevo adicional.

Un segundo sistema:

- duplica UX;
- aumenta frecuencia y fatiga;
- dificulta consent analytics;
- puede depender de Tracker;
- complica testing móvil.

Solo migrar si hay una mejora demostrable y se retira el actual.

---

## 11. Datos a no recopilar de entrada

### Nombre

No necesario para captación actual.

### Teléfono

No recopilar mientras no exista programa SMS/WhatsApp concreto.

### Dirección/fecha de nacimiento

No necesarias.

### Ubicación exacta

No necesaria.

### Género

No necesario.

### Intereses

Solo los explícitos y útiles.

### Actividad web completa

No sin caso de uso y decisión de tracking.

---

## 12. Importaciones

Antes de importar cualquier CSV:

- origen legítimo;
- consentimiento/purpose conocido;
- no mezclar listas históricas de otros contextos;
- deduplicar;
- validar campos;
- preservar opt-outs;
- usar el endpoint moderno de importación para automatización masiva;
- no usar endpoints de batch de contactos que Brevo haya deprecado.

Nunca “limpiar” la base importando de nuevo solo contactos activos si eso borra el conocimiento de las bajas.

---

## 13. Unsubscribe y blocklist

### Baja

Debe ser:

- visible;
- funcional;
- sin login;
- sin fricción artificial.

### Blocklisted

No borrar automáticamente.

Brevo bloquea automáticamente hard bounces; conservar ese estado protege la reputación y evita reenvío accidental.

### Re-suscripción

No desbloquear automáticamente porque una importación posterior incluya el email.

Exigir un flujo explícito de re-suscripción cuando corresponda.

---

## 14. Beta: matriz de consentimiento

| Acción | Beta | Newsletter general |
|---|---:|---:|
| Alta en `/lectores-beta/` | Sí | No |
| Newsletter general | No por defecto | Sí si opt-in separado |
| Material no publicado | Sí | No |
| Feedback beta | Sí | No |
| Novedades generales | Solo si opt-in adicional | Sí |
| Baja beta | Debe poder hacerse | No debe cambiar necesariamente general |
| Baja general | No debe borrar consentimiento beta automáticamente si siguen siendo propósitos distintos | Sí |

La UI y Brevo deben reflejar esta independencia.

---

## 15. Cambios de privacidad necesarios si se amplía Brevo

### Solo campañas/DOI actuales

La política ya describe el uso básico, pero revisar precisión final.

### Consent Groups

Describir preferencias si cambia la UX.

### Pixel tracking individual

Explicar:

- finalidad;
- datos;
- consentimiento;
- revocación;
- proveedor.

### Tracker

Actualizar:

- cookies;
- finalidades;
- proveedor;
- eventos;
- consentimiento;
- retención;
- transferencias/procesadores según corresponda.

### Conversations widget

Describir chat, identificadores y mensajes.

### SMS/WhatsApp

Consentimiento y canal separados; teléfono deja de ser dato opcional inexistente y pasa a ser dato tratado.

---

## 16. DoD privacidad/consentimiento

- [ ] DOI probado.
- [ ] Copy de consentimiento versionado.
- [ ] Beta separado.
- [ ] Consent Groups evaluados live.
- [ ] Preference center disponible si se adoptan grupos.
- [ ] Baja total probada.
- [ ] Tracking individual policy decidida.
- [ ] Contactos unknown no se rastrean individualmente si adoptamos política conservadora.
- [ ] Plantillas tienen enlace de baja y, cuando aplique, revocación de tracking.
- [ ] Tracker no instalado sin gate.
- [ ] No se recopilan teléfonos/nombres sin necesidad.
- [ ] Privacidad y CSP actualizadas antes de cualquier tracker/widget nuevo.
