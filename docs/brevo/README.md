# Brevo — plan maestro 2026 para davidportodiaz.com

**Fecha de corte:** 27 de agosto de 2026  
**Sitio:** `https://davidportodiaz.com/`  
**Objetivo:** convertir Brevo en la capa de relación con lectores, suscriptores y oportunidades profesionales del proyecto, aprovechando al máximo lo que aporta sin introducir complejidad, tracking, coste o riesgo que no estén justificados.

## Principio rector

Brevo no debe convertirse en «otra herramienta de marketing que hay que alimentar». Debe cumplir funciones concretas dentro de una arquitectura editorial:

1. **Captar consentimiento de forma fiable.**
2. **Recordar el contexto de cada contacto** sin recopilar datos innecesarios.
3. **Enviar comunicaciones pertinentes** según interés y relación.
4. **Automatizar lo repetible**, no la voz editorial.
5. **Dar visibilidad a entregabilidad, bajas, bounces y respuesta.**
6. **Gestionar relaciones profesionales** —prensa, librerías, clubes, festivales, podcasts— sin convertirlas en una lista de newsletter.
7. **Conectar datos y acciones mediante API, webhooks y MCP** con mínimo privilegio.
8. **No romper el modelo de privacidad actual** por activar funcionalidades que necesitan cookies o seguimiento individual.

## Estado real del proyecto que esta PR toma como base

No partimos de cero. En `main` ya existe una integración propia y razonablemente endurecida:

- `cloudflare-worker-subscribe.js` actúa como proxy entre la web y Brevo.
- El navegador no conoce la API key, IDs de listas, atributos arbitrarios ni el `templateId` de DOI.
- El cliente solo envía `{ email, source, result?, website? }`.
- `website` funciona como honeypot.
- `source` se valida contra una allowlist server-side.
- La suscripción usa el endpoint de **double opt-in** de Brevo.
- La lista general verificada el 20/08/2026 era la **ID 3 — «Lectores web»**, con 2 suscriptores reales en ese momento.
- La lista **ID 4 — «identified_contacts»** existía pero no es la lista canónica del sitio.
- El atributo `SOURCE` existe.
- El quiz de Noveris puede guardar `NOVERIS` con cuatro resultados acotados.
- Fuentes actuales: `home`, `fragmento`, `manecillas`, `cuaderno`, `popup`, `explore`, `quiz`, `lectores-beta`.
- `lectores-beta` está diseñado para una lista independiente mediante `BREVO_BETA_LIST_ID`; nunca debe caer en la lista general si falta configuración.
- Staging no debe crear contactos reales.
- Hay honeypot, comprobación de origen y rate limiting de Cloudflare; el rate limiter actualmente falla abierto si el binding falta o falla, por decisión de disponibilidad documentada.
- Existe `scripts/brevo/audit-brevo.py`, read-only, para inspeccionar cuenta, listas, atributos, campañas y templates.
- En la auditoría real del 20/08/2026 aparecieron 8 templates, incluidos nombres legacy `Bienvenida_Samuel_*` y `Automatización #2_step_*`.
- La relación exacta de esos templates con automatizaciones activas **no quedó verificada**: la API REST v3 probada no exponía esas automatizaciones en los paths utilizados y el estado debe revisarse en el panel o mediante una capacidad oficial más reciente.
- La cuenta usa autorización de IP para API; la auditoría local ya detectó rotación IPv6 y documentó el problema.

### Importante sobre la fecha de estos datos

Los datos de listas, número de contactos y templates anteriores son una fotografía real del **20/08/2026**, no una lectura live de la cuenta el 27/08/2026. Esta PR no inventa el estado actual del panel de Brevo.

## Arquitectura recomendada

### Capa 1 — Captación propia

Mantener los formularios de davidportodiaz.com y el Cloudflare Worker como entrada principal.

Razones:

- diseño y UX bajo control del sitio;
- no exponer secretos ni IDs de Brevo;
- coherencia con CSP y arquitectura actual;
- evita sustituir formularios ya integrados por widgets de terceros;
- permite validación, antiabuso y separación de propósitos en servidor;
- conserva la posibilidad de cambiar de proveedor sin rehacer cada página.

Los formularios nativos de Brevo siguen siendo útiles para casos puntuales —por ejemplo un formulario de preferencias alojado por Brevo—, pero no son la recomendación para reemplazar toda la captación actual.

### Capa 2 — Brevo como Reader CRM

Brevo conserva:

- email;
- estado de suscripción/bloqueo;
- consentimiento/preferencias;
- fuente de captación;
- intereses explícitos;
- engagement cuando exista base legítima para medirlo;
- eventos útiles;
- historial de comunicaciones;
- pertenencia a listas por propósito;
- segmentos dinámicos;
- journeys/automatizaciones.

### Capa 3 — CRM profesional

Usar Deals/Tasks/Meetings/Notes para relaciones como:

- medios y periodistas;
- podcasts;
- librerías;
- bibliotecas;
- clubes de lectura;
- ferias y festivales;
- centros educativos;
- colaboraciones;
- presentaciones y firmas.

No meter esos contactos en `Lectores web` salvo que se suscriban explícitamente a ese propósito.

### Capa 4 — Integración

- REST API para operaciones programáticas concretas.
- Events API para eventos explícitos y server-side cuando aporten valor.
- Webhooks para recibir cambios sin polling.
- MCP oficial de Brevo para auditoría y operación asistida por Claude, con token dedicado y módulos mínimos.

## Qué hacer primero

### P0 — antes de construir más marketing

- [ ] Ejecutar una nueva auditoría read-only de la cuenta y guardar un **snapshot sanitizado**, sin PII ni secretos.
- [ ] Confirmar el plan actual de Brevo; no inferirlo.
- [ ] Confirmar la lista general ID 3 y su estado actual.
- [ ] Crear o confirmar la lista separada real de lectores beta y configurar `BREVO_BETA_LIST_ID` en producción.
- [ ] Revisar en el panel todas las automatizaciones activas, pausadas y legacy.
- [ ] Identificar exactamente qué templates usan.
- [ ] Verificar el template DOI y el `BREVO_DOI_TEMPLATE_ID` de producción.
- [ ] Verificar `BREVO_DOI_REDIRECT_URL`.
- [ ] Verificar el binding `RATE_LIMITER` del Worker y realizar smoke tests reales.
- [ ] Revisar autenticación del dominio de envío: Brevo code/DKIM/DMARC y, si la cuenta muestra el nuevo flujo, su estado completo.
- [ ] Activar 2FA y revisar usuarios/API keys/IPs autorizadas.
- [ ] Crear una API key distinta por integración; no reutilizar una clave humana/local para el Worker, MCP y futuros jobs.
- [ ] Revisar remitente y Reply-To canónicos.
- [ ] Revisar bajas, blocklists, hard bounces y quejas.
- [ ] Decidir política 2026 de tracking de email antes de enviar campañas regulares.

### P1 — Reader CRM

- [ ] Mantener listas para **propósitos/consentimientos**, no para cada pequeño interés.
- [ ] Usar segmentos dinámicos para fuente, interés, engagement y comportamiento.
- [ ] Evaluar `Consent Groups` si están habilitados en la cuenta.
- [ ] Crear un formulario de actualización de preferencias.
- [ ] Diseñar journey de bienvenida general.
- [ ] Diseñar journey específico por `SOURCE` cuando tenga sentido.
- [ ] Diseñar journey separado de lectores beta.
- [ ] Crear segmentos de reactivación/no-engagement cuando haya volumen suficiente.
- [ ] Definir taxonomía de campañas, UTM y conversiones.
- [ ] Crear Brand Library y sistema de templates reutilizables.

### P1 — Profesional/CRM

- [ ] Crear pipeline `Prensa y oportunidades` usando el pipeline gratuito mientras sea suficiente.
- [ ] Definir estados y motivos de cierre.
- [ ] Usar Tasks y Notes para seguimiento.
- [ ] Evaluar una página de Meetings para prensa, clubes/librerías y colaboraciones.
- [ ] Valorar Conversations como bandeja unificada de Instagram/Facebook/email sin instalar necesariamente su widget en la web.

### P2 — Integración y observabilidad

- [ ] Añadir un snapshot auditor más completo y máquina-readable.
- [ ] Implementar receptor de webhooks en Cloudflare con autenticación/secret header, idempotencia y logging minimizado.
- [ ] Añadir monitor de entregabilidad y alertas de bounces/complaints.
- [ ] Usar Events API para acciones relevantes que hoy no registra Brevo.
- [ ] Preparar integración MCP oficial para Claude con token separado y servidores/módulos mínimos.
- [ ] Solo después, estudiar Tracker/Web Push/behavioral automation si hay caso de negocio y consentimiento apropiado.

## Qué NO hacer ahora

- No activar una IP dedicada: el volumen conocido está muy por debajo de lo que Brevo recomienda para mantener reputación propia.
- No pagar Professional por funciones vistosas que no tienen escala suficiente.
- No instalar Brevo Tracker de forma silenciosa: usa cookies y cambia el modelo de privacidad actual.
- No añadir el widget de chat de Brevo si duplica el asistente propio sin una necesidad clara.
- No recopilar teléfono solo «por si un día hacemos SMS/WhatsApp».
- No mezclar lectores beta con newsletter general.
- No meter prensa/librerías en campañas de marketing sin base/consentimiento adecuado.
- No tratar clics a Amazon u otra tienda como una compra real.
- No inferir ventas/revenue si el ecommerce ocurre fuera del dominio y no existe atribución fiable.
- No crear decenas de listas estáticas para intereses: usar segmentos y, cuando esté disponible, Consent Groups.
- No borrar automáticamente blocklisted/unsubscribed: conservar su estado evita reimportaciones accidentales y mantiene histórico.
- No automatizar la redacción final de newsletters sin revisión humana.
- No permitir que una automatización modifique consentimientos para «mejorar métricas».
- No guardar API keys en GitHub, docs, logs o variables públicas del cliente.

## Documentos de esta carpeta

1. [`01-ESTADO-ACTUAL-Y-GAPS.md`](./01-ESTADO-ACTUAL-Y-GAPS.md) — auditoría de lo que ya existe en repo/cuenta y qué falta verificar.
2. [`02-ARQUITECTURA-READER-CRM.md`](./02-ARQUITECTURA-READER-CRM.md) — modelo de contactos, listas, atributos, segmentos, lifecycle y objetivos.
3. [`03-CONSENTIMIENTO-PRIVACIDAD-Y-PREFERENCIAS.md`](./03-CONSENTIMIENTO-PRIVACIDAD-Y-PREFERENCIAS.md) — DOI, Consent Groups, tracking de email 2026, Tracker, RGPD y separación de propósitos.
4. [`04-CAMPANAS-AUTOMATIZACIONES-Y-CONTENIDO.md`](./04-CAMPANAS-AUTOMATIZACIONES-Y-CONTENIDO.md) — journeys, campañas, templates, A/B, send-time, conversiones y calendario editorial.
5. [`05-ENTREGABILIDAD-DOMINIO-Y-HIGIENE.md`](./05-ENTREGABILIDAD-DOMINIO-Y-HIGIENE.md) — dominio, DKIM/DMARC, IP, rebotes, blocklists, warming y playbooks.
6. [`06-API-EVENTS-WEBHOOKS-MCP-Y-SEGURIDAD.md`](./06-API-EVENTS-WEBHOOKS-MCP-Y-SEGURIDAD.md) — API, rate limits, Events, webhooks, MCP oficial, claves, IP allowlist y arquitectura futura.
7. [`07-CRM-MEETINGS-CONVERSATIONS-Y-CANALES.md`](./07-CRM-MEETINGS-CONVERSATIONS-Y-CANALES.md) — pipeline profesional, Meetings, Conversations, SMS, WhatsApp, web push, landing pages y casos de uso.
8. [`08-PLANES-COSTES-ESCALADO-Y-NO-APLICABLES.md`](./08-PLANES-COSTES-ESCALADO-Y-NO-APLICABLES.md) — Free/Starter/Standard/Professional/Enterprise y gates de upgrade.
9. [`09-BACKLOG-IMPLANTACION-CLAUDE.md`](./09-BACKLOG-IMPLANTACION-CLAUDE.md) — backlog ejecutable dividido entre cuenta, Cloudflare, repo y trabajo humano.
10. [`10-FUENTES-OFICIALES-Y-CAMBIOS-2026.md`](./10-FUENTES-OFICIALES-Y-CAMBIOS-2026.md) — registro de fuentes primarias y novedades 2026.

## Definición de éxito

Brevo estará bien aprovechado cuando:

- cada alta tenga propósito y fuente claros;
- cada contacto pueda gestionar sus preferencias;
- beta y newsletter no se mezclen;
- las automatizaciones estén inventariadas, probadas y tengan dueño;
- haya una bienvenida útil y no una secuencia promocional genérica;
- los emails estén autenticados y sean entregables;
- los datos de engagement se midan con una política de privacidad explícita;
- las relaciones de prensa/clubes tengan pipeline y seguimiento;
- Claude pueda auditar y operar de forma limitada mediante MCP/API sin secretos en repo;
- bounces, bajas y errores generen señales operativas;
- cada upgrade de plan tenga un motivo cuantificable;
- ninguna funcionalidad de Brevo se active solo porque existe.
