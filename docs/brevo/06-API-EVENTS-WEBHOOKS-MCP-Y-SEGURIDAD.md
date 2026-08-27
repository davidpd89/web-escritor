# 06 — API, Events, Webhooks, MCP y seguridad

**Objetivo:** permitir que el proyecto use Brevo programáticamente y que Claude pueda auditarlo en el futuro sin exponer secretos, depender de polling innecesario ni dar permisos mayores que los necesarios.

---

## 1. Arquitectura de integración recomendada

```text
Browser
  |
  | minimal subscription payload
  v
Cloudflare Worker subscribe
  |
  | Brevo REST API + server-side secret
  v
Brevo

Brevo
  |
  | authenticated webhooks
  v
Cloudflare webhook receiver (future)
  |
  +--> aggregate monitoring / alerts / storage minimised

Claude / local admin tooling
  |
  | dedicated MCP token or dedicated read API key
  v
Brevo MCP/API
```

### Principio

Separar credenciales por función:

- Worker de suscripción;
- auditoría local;
- MCP de Claude;
- futuro receptor/administrador de webhooks;
- CI/job si se crea.

No reutilizar una misma API key para todo.

---

## 2. API keys

Brevo permite crear claves con nombre y caducidad. Las claves solo se muestran al crearlas.

### Naming

- `prod-subscribe-worker`
- `local-read-audit`
- `claude-mcp-audit`
- `brevo-webhook-admin` si realmente se necesita

### Política

- una integración = una clave;
- nombre descriptivo;
- expiración razonable cuando sea viable;
- rotación documentada;
- revocar inmediatamente integraciones retiradas;
- nunca guardar en repo;
- nunca imprimir en logs;
- no colocar en JS/browser;
- no enviar por issue/PR/email no seguro.

### Claves inactivas

Brevo documenta expiración de API keys inactivas tras periodos de inactividad; contemplar rotación/monitorización y no tratar una clave olvidada como infraestructura permanente.

---

## 3. Authorized IPs

La cuenta real ya ha mostrado `401 unrecognised IP address` al ejecutar auditoría desde una IPv6 doméstica cambiante.

### Lo aprendido

- allowlisting de una IPv6 individual puede dejar de funcionar al rotar host address;
- el script documentó el prefijo `/64` observado como solución operativa local, sujeto a la interfaz/política real de Brevo.

### Precaución con Cloudflare

No asumir que el Worker tiene una única IP de salida estable que podamos allowlistear.

Antes de endurecer API IP restrictions:

1. identificar tráfico legítimo actual;
2. probar Worker de producción;
3. probar auditoría local;
4. probar MCP si se conecta;
5. confirmar arquitectura de egress;
6. tener rollback.

No romper altas reales por una allowlist teóricamente más segura.

---

## 4. Rate limits REST

Brevo documenta límites por endpoint y devuelve `429` cuando se superan.

Límites generales relevantes a fecha de corte:

- `POST /v3/smtp/email`: 1.000 RPS / 3.600.000 RPH;
- `POST /v3/events`: 10 RPS / 36.000 RPH;
- endpoints `/v3/contacts/...`: 10 RPS / 36.000 RPH;
- muchos otros endpoints: 100 RPH.

Usar headers `x-sib-ratelimit-*` cuando estén presentes.

### Regla de cliente

- retry solo cuando tenga sentido;
- exponential backoff + jitter para 429/5xx transitorios;
- respetar `Retry-After` si se devuelve;
- idempotencia para writes;
- paginación;
- no poll continuo;
- usar webhooks para eventos.

---

## 5. SDKs

Brevo mantiene SDKs oficiales, pero la API ha tenido cambios de especificación/SDK en 2026.

### Regla

No actualizar SDK major automáticamente.

Antes:

- leer changelog;
- pin de versión;
- test contract;
- staging/mock;
- revisar cambios de tipos/status codes.

Para scripts pequeños read-only, HTTP stdlib puede seguir siendo más transparente que añadir una dependencia grande.

---

## 6. Events API

Brevo Events permite:

- registrar interacciones;
- consultar historial de evento;
- segmentar por comportamiento;
- disparar automations.

### Endpoints relevantes

- `POST /v3/events`
- `POST /v3/events/batch`
- `GET /v3/events`

En marzo de 2026 Brevo añadió/actualizó capacidades de Events, incluido GET y batch; el batch tuvo cambios de status/response. No codificar status antiguos de memoria.

### Eventos propuestos para davidportodiaz.com

Solo cuando aporten decisión/automatización:

#### `fragment_downloaded`

Propiedades:

- `work_slug`
- `asset_type`
- `source_page`

#### `resource_downloaded`

- `resource_slug`
- `resource_category`

#### `beta_feedback_submitted`

- `project_slug`
- `feedback_round`

No enviar texto del feedback como event property.

#### `meeting_booked`

Si Meetings ya crea una señal nativa, no duplicar innecesariamente.

#### `retailer_link_clicked`

- `work_slug`
- `retailer`
- `placement`

Solo si se decide que esta atribución es útil y se informa/trata correctamente.

No llamarlo `purchase`.

### Event naming

- lowercase snake_case;
- semántica estable;
- no PII en nombre;
- properties acotadas;
- schema documentado.

---

## 7. Batch events

Brevo soporta batch para reducir llamadas.

Usar solo si aparece volumen.

### Atención a changelog

No asumir que `204` es éxito del batch: Brevo cambió respuestas en 2026. Los clientes deben validar la especificación vigente.

---

## 8. Contact batch deprecado

Brevo ha anunciado deprecación de `/contacts/batch` con fecha efectiva 30/10/2026.

### Acción

No construir nueva automatización sobre ese endpoint.

Para operaciones masivas usar el flujo moderno de importación (`/v3/contacts/import`) o la API recomendada vigente.

Añadir test/grep futuro que evite introducir `/contacts/batch` en nuevo código.

---

## 9. Webhooks

Brevo permite webhooks de marketing y transaccionales; máximo documentado: **40** combinados.

### Eventos útiles

#### Transactional

- sent;
- delivered;
- opened;
- clicked;
- soft bounce;
- hard bounce;
- invalid;
- deferred;
- complaint;
- unsubscribed;
- blocked;
- error.

#### Marketing

Según endpoint/eventos disponibles:

- open;
- click;
- hardBounce;
- softBounce;
- delivered;
- spam;
- unsubscribe;
- contactDeleted;
- contactUpdated;
- listAddition;
- otros relevantes.

### No crear un webhook por cada evento

Agrupar eventos compatibles en pocos endpoints/contratos.

---

## 10. Receptor de webhook futuro

Propuesta:

`cloudflare-worker-brevo-webhooks.js` o Worker separado.

### Requisitos

- HTTPS;
- auth de webhook o custom secret header según configuración oficial disponible;
- método POST only;
- tamaño máximo;
- JSON validation;
- allowlist de event types;
- idempotencia;
- timestamp sanity;
- no reflejar body;
- respuesta rápida;
- procesamiento pesado async si se necesita;
- no logs de email/body completos;
- hashing/pseudonimización donde baste;
- retention corta de eventos crudos;
- agregados para reporting.

### Idempotencia

Construir una clave con los identificadores disponibles en payload + timestamp/event id; no asumir que Brevo nunca reintenta.

### Alertas

- hard bounce spike;
- complaint > baseline;
- error/blocked spike;
- webhook receiver down;
- no events durante una campaña que debería generarlos.

### PII

No convertir GitHub Actions logs en un datastore de emails.

---

## 11. Polling vs. webhooks

Usar API GET para:

- auditorías;
- snapshots;
- reconciliación;
- configuración.

Usar webhooks para:

- cambios/eventos continuos;
- entregabilidad;
- alertas.

Evitar un cron que pregunte cada minuto por estadísticas.

---

## 12. MCP oficial de Brevo — oportunidad 2026

Brevo ofrece servidor MCP oficial compatible con:

- Claude Desktop;
- Claude Code;
- Cursor;
- Windsurf;
- VS Code/GitHub Copilot;
- otros clientes MCP.

### Endpoint principal

`https://mcp.brevo.com/v1/brevo/mcp`

Da acceso combinado a **27 módulos**.

### Autenticación

Bearer token de MCP creado desde `Settings > SMTP & API > API Keys & MCP`.

El token solo se muestra al crearlo.

### No meter token en repo

Ejemplo conceptual:

```text
BREVO_MCP_TOKEN=<local secret>
Authorization: Bearer ${BREVO_MCP_TOKEN}
```

No commit de config con token literal.

---

## 13. Servidores MCP individuales

Brevo recomienda/permite endpoints más acotados; una superficie menor mejora control y puede mejorar calidad del agente.

Módulos oficiales documentados:

- contacts
- email_campaign_management
- campaign_analytics
- templates
- transac_templates
- deals
- companies
- tasks
- pipelines
- notes
- sms_campaigns
- whatsapp_campaigns
- whatsapp_management
- lists
- segments
- attributes
- contact_import_export
- folders
- groups
- senders
- domains
- ips
- accounts
- users
- webhooks_management
- external_feeds
- processes

### Estrategia para Claude

#### Fase 1 — read/audit

Conectar preferentemente módulos necesarios para inspección:

- campaign_analytics;
- lists;
- segments;
- attributes;
- templates;
- senders;
- domains;
- processes;
- contacts solo cuando la tarea necesita contactos y con cuidado de PII.

No dar inicialmente:

- campañas write;
- SMS;
- WhatsApp;
- imports masivos;
- usuarios;
- IP management.

#### Fase 2 — CRM

Añadir si se usa pipeline:

- deals;
- companies;
- tasks;
- pipelines;
- notes.

#### Fase 3 — writes de marketing

Solo cuando haya workflows claros y revisión humana:

- email_campaign_management;
- templates;
- webhooks_management.

### Regla de confirmación

Aunque el MCP pueda “crear campaña” o “añadir contacto”, las acciones de envío, borrado, import masivo, modificación de consentimiento o cambios de dominio/API deben requerir autorización explícita.

---

## 14. MCP como reemplazo parcial del audit manual

El script `audit-brevo.py` sigue siendo útil porque:

- es reproducible;
- auditable;
- no depende del modelo;
- puede producir snapshot estructurado.

MCP añade:

- acceso más amplio;
- preguntas naturales;
- módulos de CRM/campaign analytics;
- mejor trabajo de Claude sobre cuenta real.

### Recomendación

Usar ambos:

- script = baseline determinista;
- MCP = exploración/operación asistida.

---

## 15. Snapshot machine-readable futuro

Crear script:

`scripts/brevo/snapshot-brevo.py`

Salida local por defecto:

`.local/brevo-snapshot.json`

No commit si contiene PII.

### Snapshot sanitizado commit-able opcional

`docs/brevo/snapshots/YYYY-MM-DD-account-shape.json`

Solo agregados/config no sensible:

```json
{
  "date": "YYYY-MM-DD",
  "plan": "...",
  "lists": [{"id": 3, "name": "Lectores web", "count": 0}],
  "attributes": [{"name": "SOURCE", "type": "..."}],
  "segments": [{"name": "..."}],
  "templates": [{"id": 0, "name": "...", "active": true}],
  "domains": [{"domain": "...", "dkim": true, "dmarc": true}],
  "webhookEventSets": [],
  "consentGroupsEnabled": false
}
```

No:

- emails;
- names;
- phones;
- addresses;
- API keys;
- SMTP credentials;
- token MCP;
- message bodies.

---

## 16. CI futuro

Tests sin Brevo real:

- Worker source whitelist;
- beta fail-closed;
- no client listIds;
- no API key in JS;
- valid upstream contract fixtures;
- status handling;
- webhook validation fixtures;
- Events schemas;
- no deprecated `/contacts/batch`.

### No CI con credencial real por defecto

Un PR de cualquier fork/branch no debe poder escribir en Brevo.

Si se crea job live:

- manual `workflow_dispatch`;
- read-only key;
- protected environment;
- no PII en logs;
- timeout;
- concurrency;
- no write.

---

## 17. API security controls

- server-side only;
- least privilege where product supports it;
- separate key per integration;
- expirations;
- 2FA account;
- authorized IPs con rollout cuidadoso;
- secret scanning;
- no secret in `.env.example` values;
- local `.env.local` gitignored;
- rotate after accidental exposure;
- never redact and continue using a leaked key: revoke.

---

## 18. OAuth

Brevo añadió/extendió scopes OAuth en 2026.

### Para este proyecto

No construir una OAuth app para nuestra propia única cuenta sin necesidad.

API key/MCP token es más simple.

OAuth pasa a ser apropiado si algún día se crea:

- herramienta SaaS para terceros;
- integración que varias cuentas Brevo deban autorizar;
- producto público.

---

## 19. Error taxonomy para scripts

Normalizar:

- `auth_error`
- `ip_not_authorized`
- `rate_limited`
- `not_found`
- `feature_not_enabled`
- `invalid_payload`
- `upstream_5xx`
- `network_error`
- `timeout`

No reintentar `401` de IP allowlist sin cambiar configuración.

No esconder `403 CONSENT_GROUP_NOT_ENABLED` como fallo genérico: significa feature gate.

---

## 20. Auditoría de writes

Toda herramienta de write debe registrar localmente/agregado:

- actor/integration;
- operación;
- tipo de objeto;
- timestamp;
- resultado;
- request id si existe;
- nunca el secreto;
- PII minimizada.

Para Claude, resumir antes de acciones masivas:

- cuántos objetos;
- qué cambiará;
- rollback;
- si afecta consentimiento/envío.

---

## 21. DoD API/MCP

- [ ] una key por integración;
- [ ] 2FA;
- [ ] IP allowlist verificada sin romper Worker;
- [ ] snapshot read-only ampliado;
- [ ] no `/contacts/batch` nuevo;
- [ ] Events schema definido;
- [ ] receptor webhook diseñado/testeado antes de deploy;
- [ ] no PII en logs;
- [ ] MCP token dedicado fuera de repo;
- [ ] MCP empieza por módulos mínimos;
- [ ] writes sensibles requieren autorización;
- [ ] CI no escribe en Brevo real;
- [ ] SDK versions pinneadas si se adoptan.
