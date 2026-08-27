# 10 — Fuentes oficiales y cambios 2026

**Fecha de revisión:** 2026-08-27  
**Política:** usar documentación oficial de Brevo como fuente primaria. No convertir blogs SEO, agencias o respuestas antiguas de foros en autoridad sobre producto actual.

---

## 1. Pricing y planes

### Pricing plans

Fuente oficial:

`https://help.brevo.com/hc/es/articles/208589409-Información-sobre-los-planes-de-precios-de-Brevo`

Verificado 27/08/2026:

- Free 0 €/mes;
- Starter desde 7 €/mes;
- Standard desde 17 €/mes;
- Professional desde 499 €/mes;
- Enterprise custom;
- Free 300 emails/día, hasta 100.000 contactos;
- Standard añade unlimited automation contacts, A/B, AI send-time y reporting avanzado;
- Professional añade capabilities multicanal/data/scoring/push/WhatsApp, etc.;
- add-ons de créditos, IP dedicada, SSO según plan.

### Add-ons

`https://help.brevo.com/hc/es/articles/4409354969746-Personaliza-tu-plan-con-complementos`

Incluye:

- Sales packages;
- email credits;
- SMS/WhatsApp credits;
- dedicated IP;
- SSO.

### Free limits

`https://help.brevo.com/hc/es/articles/208580669-FAQ-Cuáles-son-los-límites-del-plan-Gratis`

Confirma:

- 2.000 contactos únicos en automations;
- alertas al 80 %/100 %;
- 1 user;
- sales free limits.

### Automation quotas

`https://help.brevo.com/hc/es/articles/9168632514066-¿Cuáles-son-las-diferentes-cuotas-que-se-aplican-en-Brevo`

Verificado:

- Free/Starter 2.000 contactos automation;
- Standard unlimited;
- processed event/step quotas.

---

## 2. Contactos, listas y segmentos

### Segments overview

`https://help.brevo.com/hc/es/articles/360021703959-Información-sobre-los-segmentos`

Hecho importante:

- listas dinámicas se convirtieron en estáticas el 01/01/2025;
- Brevo recomienda segmentos.

### Segment conditions

`https://help.brevo.com/hc/es/articles/14902945335954-Qué-condiciones-se-ofrecen-para-segmentar-mis-contactos`

- hasta 100 condiciones;
- atributos, actividad email/ecommerce/etc.;
- algunas condiciones aparecen tras existir eventos.

### Segment usage

`https://help.brevo.com/hc/es/articles/8423408941330-Use-segmentos-gestión-de-contactos-campañas-de-email-automatizaciones`

---

## 3. Consent Groups — NUEVO 2026

### Changelog 30/06/2026

`https://developers.brevo.com/changelog/2026/6/30`

Añade:

- GET/POST `/contacts/consent-groups`;
- GET/PUT/DELETE `/contacts/consent-groups/{id}`;
- `consentGroupIds` en import;
- `consentGroups` en contact detail;
- feature gate `CONSENT_GROUP_NOT_ENABLED`.

### Reference

`https://developers.brevo.com/reference/create-consent-group`

---

## 4. Formularios y preferencias

### Signup forms

`https://help.brevo.com/hc/en-us/articles/208771869-Create-a-sign-up-form-in-Brevo`

Cubre:

- embedded/full page;
- GDPR blocks;
- Consent Groups;
- double confirmation;
- custom confirmation page/email;
- DOUBLE OPT-IN attribute en formularios nativos.

### Profile update

`https://help.brevo.com/hc/es/articles/360003644360-Actualizar-sus-datos-y-preferencias-de-contactos-formulario-de-actualización-de-perfil`

Cubre:

- preferencias;
- listas;
- Consent Groups;
- confirmación.

### DOI para formularios externos

`https://help.brevo.com/hc/en-us/articles/27353832123026-Set-up-a-double-opt-in-process-for-a-sign-up-form-created-outside-of-Brevo`

Nota: nuestro Worker ya usa directamente el endpoint DOI oficial; no cambiar arquitectura solo porque exista este tutorial de automation.

---

## 5. Tracking y privacidad

### Brevo Tracker

`https://help.brevo.com/hc/es/articles/209465705-FAQ-qué-es-Brevo-tracker-y-cómo-se-instala`

Confirma:

- conecta web con Automation/Segments/Conversations;
- monitorea acciones/visitas;
- usa cookies propias o de terceros;
- envía datos a Brevo.

Por eso requiere gate de privacidad/CSP en esta web.

### Pixel tracking consent 2026

`https://help.brevo.com/hc/es/articles/37113920427922-Acerca-de-los-píxeles-de-seguimiento-de-email-y-la-recomendación-de-la-CNIL-en-Brevo`

Cambios/orientación 2026:

- consentimiento individual de tracking;
- seguimiento de opens/clicks por contacto;
- default recomendado por Brevo `No` para unknown en contexto de recomendación CNIL;
- revoke tracking link;
- revisión de marketing/automation/transactional por propósito.

No utilizar este artículo como sustituto de asesoramiento jurídico para España/UE.

---

## 6. Campaigns

### Create/send campaign + UTM

`https://help.brevo.com/hc/es/articles/4413566705298-Crear-y-enviar-una-campaña-de-email`

Incluye:

- Reply-To;
- UTM tracking;
- configuración de campaña.

### A/B

`https://help.brevo.com/hc/es/articles/4523165348626-Crear-una-campaña-de-prueba-A-B`

- subject/content;
- sample split;
- winner;
- incompatibilidades con Best time/batches.

### Best time / Aura

`https://help.brevo.com/hc/es/articles/4887607089810-Enviar-en-el-mejor-momento-optimizar-el-momento-de-envío-del-email`

- Campaigns + Automations;
- usa engagement;
- no disponible con A/B, dedicated IP warm-up o anonymous tracking;
- no usar para comunicaciones urgentes.

### Campaign reports / conversions

`https://help.brevo.com/hc/es/articles/19764406559506-Analizar-y-exportar-el-informe-de-su-campaña-de-email`

---

## 7. Deliverability

### Domain setup 2026 rollout

`https://help.brevo.com/hc/es/articles/35337929909778-Configurar-el-dominio-en-Brevo`

Nuevo flujo gradual:

- authentication;
- branded subdomain;
- dedicated IP association cuando aplique.

### Classic auth

`https://help.brevo.com/hc/es/articles/12163873383186-Autenticar-el-dominio-con-Brevo-código-Brevo-DKIM-DMARC`

### Dedicated IP

`https://help.brevo.com/hc/es/articles/209576665-Prácticas-recomendadas-para-gestionar-una-IP-dedicada`

Brevo recomienda:

- 3 campañas/semana a 3.000+ contactos;
- o >100.000 emails/mes;
- shared IP si no se sostiene ese volumen.

### Hard/soft bounces

`https://help.brevo.com/hc/es/articles/209435165-Qué-son-los-soft-bounces-y-los-hard-bounces-en-el-email`

Hard bounce -> Brevo blocklist automática.

### Deliverability best practices

`https://help.brevo.com/hc/es/articles/360020418259-Prácticas-recomendadas-para-mejorar-la-entregabilidad-de-los-emails`

---

## 8. CRM/Sales/Meetings

### Free sales features / add-ons

Fuente pricing/add-ons:

`https://help.brevo.com/hc/es/articles/4409354969746-Personaliza-tu-plan-con-complementos`

Incluye como base:

- 50 open deals;
- 1 pipeline;
- Meetings;
- live chat;
- reports/forecast;
- tasks/reminders;
- 1 calendar/mailbox;
- Conversations mobile.

### Meetings calendar

`https://help.brevo.com/hc/es/articles/6979087992594-Cómo-conectar-su-calendario-con-Meetings`

Google Calendar / Microsoft Outlook availability.

---

## 9. Conversations

### Section

`https://help.brevo.com/hc/es/sections/18476323901074-Conversaciones`

### Instagram Direct

`https://help.brevo.com/hc/es/articles/4416263637906-Responder-a-los-mensajes-directos-de-Instagram-con-Conversaciones`

Requiere cuenta profesional Instagram vinculada a Facebook Page.

### Team inbox/email

`https://help.brevo.com/hc/es/articles/10668659564818-Conectar-y-configurar-el-buzón-de-equipo-en-Conversaciones`

---

## 10. SMS / WhatsApp

### SMS pricing

`https://help.brevo.com/hc/es/articles/208717449-Países-admitidos-y-precios-de-los-SMS`

- créditos;
- packs;
- no caducan;
- país + longitud.

### WhatsApp pricing

`https://help.brevo.com/hc/es/articles/4416961286674-Países-admitidos-y-precios-de-los-mensajes-de-WhatsApp`

### Plan/add-ons

Ver pricing 2026: WhatsApp credits Professional/Enterprise.

---

## 11. API rate limits

`https://developers.brevo.com/docs/api-limits`

A fecha de corte, límites generales relevantes:

- SMTP send 1.000 RPS / 3.600.000 RPH;
- Events 10 RPS / 36.000 RPH;
- Contacts 10 RPS / 36.000 RPH;
- muchos otros endpoints 100 RPH;
- 429 on exceed;
- usar rate-limit headers;
- webhooks en vez de polling.

---

## 12. Events API

### Guide

`https://developers.brevo.com/docs/events`

### Endpoints

`https://developers.brevo.com/docs/event-endpoints`

- GET events;
- POST event;
- batch;
- identifiers/properties.

### 2026 changes

`https://developers.brevo.com/changelog/2026/3/21`

Revisar status/payload de batch al implementar.

---

## 13. Webhooks

`https://developers.brevo.com/docs/how-to-use-webhooks`

- marketing + transactional;
- máximo 40 webhooks combinados;
- eventos de entrega/apertura/click/bounces/complaint/etc.;
- API management.

---

## 14. API key security

`https://help.brevo.com/hc/es/articles/209467485-Crear-o-eliminar-una-clave-API`

Verificado 2026:

- expiry entre 7 días y 1 año o no-expiry;
- key solo visible al crearla;
- inactive API keys expiran a 90 días;
- clave distinta por integración;
- proteger como password.

### Authorized IPs

`https://help.brevo.com/hc/es/articles/5740111683858-Autorizar-y-bloquear-direcciones-IP-para-la-seguridad-de-las-API-y-el-SMTP`

Brevo documenta learning phase y posterior bloqueo de IP desconocida si no aparecen IPs nuevas durante 30 días, además de gestión manual.

---

## 15. MCP — NUEVO/RELEVANTE 2026

### Help

`https://help.brevo.com/hc/es/articles/27978590646802-Qué-es-el-Protocolo-de-Contexto-Modelo-MCP`

Confirma:

- Claude Desktop;
- Claude Code;
- Cursor;
- Windsurf;
- VS Code;
- server principal 27 módulos;
- servidores individuales;
- token MCP desde API Keys & MCP;
- bearer header.

### Changelog 02/03/2026

`https://developers.brevo.com/changelog/2026/3/2`

Cambios:

- tokens ya no van en URL;
- `Authorization: Bearer`;
- 193 tools autogeneradas desde OpenAPI;
- rate limiting;
- más clientes soportados.

---

## 16. Deprecaciones/cambios API 2026

### `/contacts/batch`

`https://developers.brevo.com/changelog/2026/5/12`

- deprecated effective 30/10/2026;
- migrar a `/v3/contacts/import`.

### API spec overhaul

`https://developers.brevo.com/changelog`

17/04/2026: correcciones de spec con cambios potencialmente breaking para generated SDKs.

### Major SDK releases

`https://developers.brevo.com/changelog/2026/5/14`

- Node 6.0.0;
- PHP 5.0.0;
- Python 5.0.0;
- cambios breaking;
- mantener major anterior es opción soportada mientras se migra.

### OAuth scopes

`https://developers.brevo.com/changelog/2026/6/3`

Apps OAuth pueden declarar scopes granulares.

Para nuestra cuenta única no se recomienda construir OAuth app sin caso de uso.

---

## 17. Cambios que deben vigilarse después de esta fecha

Brevo está cambiando rápido en 2026. Antes de implementar cualquiera de estos puntos, volver a comprobar docs oficiales:

- Consent Groups disponibilidad/planes;
- MCP modules/permisos;
- Automation API/tool exposure;
- pricing;
- Web Push limits;
- pixel tracking consent;
- domain setup rollout;
- API rate limits;
- SDK latest versions;
- webhooks event schemas;
- deprecation `/contacts/batch`;
- Conversations/AI agent packaging;
- Professional feature matrix.

---

## 18. Regla de actualización de esta carpeta

Cuando cambie una función de Brevo:

1. fuente oficial;
2. fecha;
3. qué cambió;
4. impacto en davidportodiaz.com;
5. documentos afectados;
6. si cambia backlog;
7. no borrar contexto histórico útil, marcarlo superseded.

---

## 19. Fuentes internas del repositorio

Revisadas para esta PR:

- `cloudflare-worker-subscribe.js`
- `script.js`
- `scripts/brevo/audit-brevo.py`
- `privacidad.html`
- `.env.example`
- arquitectura/QA existente de staging y superficie pública.

Los comentarios en código sobre la cuenta real son evidencia histórica interna, no sustituyen una nueva lectura live.

---

## 20. Control de afirmaciones

Esta documentación **NO afirma** conocer a 27/08/2026:

- plan real actual;
- número actual de contactos;
- estado actual de automations;
- ID real actual de beta list;
- sender/domain auth status;
- webhooks existentes;
- Consent Groups availability;
- tracking pixel settings;
- API keys activas;
- Meetings/Conversations config;
- métricas de campañas.

Todo ello está convertido en checks explícitos del backlog.
