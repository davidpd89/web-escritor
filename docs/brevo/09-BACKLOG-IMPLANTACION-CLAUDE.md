# 09 — Backlog de implantación para Claude

**Objetivo:** que esta investigación se convierta en trabajo ejecutable y verificable, separando claramente cambios de cuenta, código, Cloudflare y decisiones humanas.

## Estados

- `TODO`
- `BLOCKED_ACCOUNT`
- `BLOCKED_DECISION`
- `READY_REPO`
- `DONE`
- `DEFER`
- `N/A`

## Tipos de actor

- `ACCOUNT`: requiere panel/cuenta Brevo.
- `CLOUDFLARE`: variables/bindings/deploy.
- `REPO`: código/documentación/tests.
- `MCP`: puede resolverse con MCP oficial una vez conectado.
- `HUMAN`: decisión editorial/legal/credencial.

---

# Fase 0 — Recuperar la verdad live

## BRV-001 — Snapshot read-only completo

Prioridad: `P0`  
Actor: `MCP + REPO`  
Estado inicial: `BLOCKED_ACCOUNT`

### Acción

Ejecutar auditoría contra la cuenta real y producir dos salidas:

1. snapshot local completo, protegido;
2. snapshot sanitizado agregable al repo.

### Incluir

- plan;
- listas y conteos;
- atributos;
- segmentos;
- consent groups/availability;
- campañas recientes agregadas;
- templates;
- senders;
- domains;
- webhooks;
- processes/imports;
- CRM pipelines/deals counts;
- Meetings/Conversations state;
- automations por panel/MCP si la herramienta los expone.

### No incluir

- emails/nombres/teléfonos;
- API keys;
- SMTP creds;
- MCP token;
- message bodies.

### Código propuesto

`scripts/brevo/snapshot-brevo.py`

Flags:

```text
--output <path>
--sanitized-output <path>
--check
--no-contacts
```

### Aceptación

- salida determinista;
- no secretos;
- no PII en sanitizado;
- errores de IP auth claros;
- exit nonzero en auth/config error;
- tests fixture.

---

## BRV-002 — Inventario de automatizaciones

Prioridad: `P0`  
Actor: `MCP/HUMAN`  
Estado: `BLOCKED_ACCOUNT`

Crear `docs/brevo/AUTOMATIONS-LIVE-INVENTORY.md` o snapshot sanitizado.

Por workflow:

- nombre/id;
- status;
- trigger;
- reentry;
- audience;
- exclusions;
- steps;
- delays;
- templates IDs/nombres;
- purpose;
- last modified;
- decision.

### Aceptación

No queda ningún template `Bienvenida_Samuel_*` o `Automatización #2_step_*` sin saber si está usado.

---

## BRV-003 — Verificar plan y billing

P0 · `ACCOUNT`

Registrar:

- plan;
- tier;
- monthly email allowance;
- stored contact allowance;
- add-ons;
- billing cadence;
- renewal date si procede.

No guardar datos de pago.

---

# Fase 1 — Cerrar la integración existente

## BRV-010 — Lista beta real

P0 · `ACCOUNT + CLOUDFLARE`

1. ✅ 2026-08-27 — Creada lista dedicada `Lectores beta`, **id `6`**, carpeta `Your first folder` (misma que `Lectores web`, id 3). Ver `docs/brevo/SNAPSHOT-LIVE.md`.
2. ✅ Obtenida ID: `6`.
3. ⏳ Pendiente — Configurar `BREVO_BETA_LIST_ID=6` como variable/secret del Worker en Cloudflare. No hecho por Claude: requiere tocar la config del Worker en producción (fuera del alcance sin autorización explícita, ver "Deploy" abajo).
4. No cambiar `BREVO_LIST_ID` general.
5. Smoke test con email controlado.
6. Confirmar contacto beta no entra en general.
7. Confirmar DOI.
8. Borrar/bloquear el contacto de prueba de forma apropiada tras test si procede.

### Aceptación

- beta falla cerrado si falta ID;
- beta va a lista separada;
- general no recibe alta;
- copy y purpose correctos.

### Deploy

No desplegar Worker sin autorización explícita.

---

## BRV-011 — Verificar DOI config

P0 · `ACCOUNT + CLOUDFLARE`

- template ID existe/activo;
- template contiene confirm link correcto;
- redirection URL correcta;
- lenguaje/copy coherente;
- Worker env corresponde.

### Smoke matrix

- home;
- fragmento;
- Manecillas;
- Cuaderno;
- popup;
- explore;
- quiz;
- beta.

No hace falta crear 8 contactos permanentes; usar estrategia de test controlada.

---

## BRV-012 — RATE_LIMITER production check

P0 · `CLOUDFLARE`

Verificar:

- binding existe;
- namespace/config;
- límite previsto;
- respuesta 429;
- Worker logging en degraded mode;
- no bloqueo de alta normal.

Decisión aparte si se cambia fail-open.

---

## BRV-013 — Test contract del Worker

P1 · `REPO`

Crear `tests/test-brevo-subscribe-worker.mjs` o equivalente.

Tests:

- non-POST 405;
- wrong origin 403;
- invalid JSON 400;
- invalid email 400;
- unknown source 400;
- honeypot returns fake pending/no upstream;
- missing BREVO_API_KEY 500;
- missing list 500;
- beta missing beta list 500;
- beta never fallback general;
- invalid DOI template 500;
- invalid redirect 500;
- quiz enum only;
- no arbitrary attributes/listIds;
- upstream 201 accepted;
- upstream other 2xx rejected;
- upstream 4xx/5xx hidden as 502;
- timeout/network behavior;
- rate-limit 429.

Mock fetch; no Brevo live.

---

# Fase 2 — Dominio y entregabilidad

## BRV-020 — Auditar dominio

P0 · `ACCOUNT + HUMAN DNS`

Registrar status de:

- Brevo verification;
- DKIM;
- DMARC;
- sender;
- reply-to;
- new domain setup rollout;
- branded tracking domain si existe.

### Restricción

No cambiar DNS en esta PR documental.

---

## BRV-021 — Sender identity

P0 · `ACCOUNT + HUMAN`

Elegir From y Reply-To canónicos.

Acceptance:

- From reconocible;
- Reply-To monitorizado;
- sender verificado;
- no `no-reply` innecesario.

---

## BRV-022 — Deliverability baseline

P1 · `MCP/ACCOUNT`

Snapshot agregado:

- delivered;
- hard bounce;
- soft bounce;
- complaints;
- unsubscribes;
- blocklisted;
- campaign sample window.

No inferir tendencia con 2 contactos.

---

# Fase 3 — Consentimiento y preferencias

## BRV-030 — Detectar Consent Groups

P0/P1 · `MCP/API`

Call read-only:

`GET /v3/contacts/consent-groups`

Resultados:

- `200`: feature available; inventariar.
- `403 CONSENT_GROUP_NOT_ENABLED`: marcar `NOT AVAILABLE` y no tratar como fallo.

---

## BRV-031 — Diseñar Consent Groups

P1 · `HUMAN + ACCOUNT`

Solo si available.

Propuesta inicial:

- Novedades de libros;
- Cuaderno y recursos;
- Eventos y encuentros.

### Acceptance

- nombres entendibles;
- no duplican beta;
- no más grupos de los necesarios;
- unsubscribe semantics probadas.

---

## BRV-032 — Preference center

P1 · `ACCOUNT + REPO`

Opción A: formulario Profile Update nativo Brevo.

Opción B: UI propia + API segura.

Preferencia inicial: A si cumple accesibilidad/branding y reduce complejidad.

Debe permitir:

- actualizar preferencias;
- tracking consent si feature se usa;
- unsubscribe total claro.

### Repo

Si se enlaza desde web, añadir enlace donde corresponda después de validar URL real.

No inventar URL.

---

## BRV-033 — Pixel tracking policy

P0 antes de campañas recurrentes · `HUMAN/ACCOUNT`

Revisar:

- per-contact pixel tracking consent enabled?;
- unknown default?;
- anonymous tracking?;
- footer revoke link?;
- French contacts?;
- campaign/automation/transactional treatment.

### Recomendación técnica

Privacy-first: unknown => no individualized tracking.

### Repo

Si se cambia tracking, actualizar `privacidad.html`, cookie policy si procede y tests/QA.

---

# Fase 4 — Reader CRM

## BRV-040 — Crear segmentos base

P1 · `ACCOUNT/MCP`

Crear solo tras verificar atributos:

- source Manecillas;
- source Fragmento;
- source Cuaderno;
- source Quiz;
- Noveris x4;
- source general;
- beta si sirve operativamente;
- engagement segments solo si tracking policy permite.

### Acceptance

No convertir cada segmento en lista.

---

## BRV-041 — Revisar atributos

P1 · `ACCOUNT/MCP`

Confirmar:

- SOURCE;
- NOVERIS;
- tipos;
- valores.

Decidir si hace falta `INTERESTS` o si Consent Groups reemplazan esa necesidad.

No añadir FIRSTNAME/teléfono por defecto.

---

## BRV-042 — Welcome general

P1 · `ACCOUNT + HUMAN`

Crear/revisar template y automation.

Trigger: alta confirmada general.

Debe:

- explicar expectativa;
- tener una acción útil;
- preferencia/baja;
- no prometer frecuencia falsa.

---

## BRV-043 — Welcome por source

P2 · `ACCOUNT + HUMAN`

No crear hasta que haya suficiente tráfico por source.

Primero usar un workflow con ramas/bloques condicionales.

---

## BRV-044 — Beta workflow

P1 · `ACCOUNT + HUMAN`

Completamente separado del general.

Acceptance:

- onboarding;
- material;
- feedback;
- cierre;
- no cross-subscribe.

---

## BRV-045 — Re-engagement

P2 · `ACCOUNT`

No activar hasta suficiente historial.

Definir inactividad por oportunidades de interacción, no solo 90 días arbitrarios.

---

# Fase 5 — Campañas y medición

## BRV-050 — Brand Library

P1 · `ACCOUNT/HUMAN`

Configurar:

- logo final;
- colores;
- fonts email-safe;
- social canonical links.

No usar imágenes/logo viejos.

---

## BRV-051 — Consolidar templates

P1 · `ACCOUNT`

Objetivo: pocos templates base.

Archive/delete solo después de demostrar que no están usados por automation.

---

## BRV-052 — UTM convention

P1 · `ACCOUNT/REPO`

Aplicar:

- source brevo;
- medium email;
- campaign slug;
- content optional.

Añadir documentación a cualquier analytics taxonomy existente si procede.

---

## BRV-053 — Conversion metric

P1/P2 · `ACCOUNT/HUMAN`

Si el plan tiene 1 métrica, elegir una sola de alto valor.

Nunca `purchase` sin dato de compra.

Candidate: `retailer_link_clicked` una vez haya retailer URL verificada.

---

## BRV-054 — Campaign review template

P1 · `REPO`

Crear plantilla markdown reusable para postmortem de campaña, sin PII.

---

# Fase 6 — Webhooks y observabilidad

## BRV-060 — Webhook inventory

P1 · `ACCOUNT/MCP`

Listar webhooks existentes y event sets.

No crear duplicados.

---

## BRV-061 — Webhook receiver

P1/P2 · `REPO + CLOUDFLARE`

Implementar en branch separada:

- auth/custom secret;
- POST only;
- schema validation;
- size cap;
- idempotency;
- PII-minimal logs;
- events allowlist;
- tests;
- no deploy without authorization.

---

## BRV-062 — Deliverability alerts

P2 · `REPO`

Sobre webhooks/agregados:

- hard bounce spike;
- complaint;
- blocked/error spike;
- receiver failure.

No automatizar envío correctivo sin review.

---

# Fase 7 — Events API

## BRV-070 — Event schema registry

P2 · `REPO`

Archivo propuesto:

`data/brevo-event-registry.json`

Campos:

- event_name;
- purpose;
- trigger;
- identifiers;
- allowed properties;
- retention;
- consent/privacy note;
- consumers.

### Candidate events

- fragment_downloaded;
- resource_downloaded;
- beta_feedback_submitted;
- retailer_link_clicked.

No implementar todos; registrar solo los aprobados.

---

## BRV-071 — Events proxy

P2 · `REPO/CLOUDFLARE`

No permitir eventos arbitrarios desde browser.

Worker server-side whitelist similar a SOURCE_MAP.

No desplegar sin privacidad/consent check.

---

# Fase 8 — MCP para Claude

## BRV-080 — Crear MCP token dedicado

P1 · `ACCOUNT/HUMAN`

Nombre recomendado:

`claude-brevo-audit`

No commit.

---

## BRV-081 — Conectar servidores mínimos

P1 · `HUMAN`

Primera conexión:

- campaign_analytics;
- lists;
- segments;
- attributes;
- templates;
- senders;
- domains;
- processes.

Añadir contacts solo cuando se necesite.

No activar inicialmente SMS/WhatsApp/imports/users/IPs.

---

## BRV-082 — MCP live audit

P1 · `MCP`

Claude debe revisar:

- estado cuenta;
- campañas;
- segments;
- templates;
- domain;
- CRM;
- automation si disponible por toolset.

Guardar solo conclusiones/snapshot sanitizado.

---

# Fase 9 — CRM profesional

## BRV-090 — Pipeline `Prensa y oportunidades`

P1 · `ACCOUNT/MCP`

Usar pipeline gratuito si disponible.

Stages documentados en 07.

No convertir contactos profesionales en marketing contacts automáticamente.

---

## BRV-091 — Backfill de oportunidades activas

P1/P2 · `HUMAN/MCP`

Solo oportunidades reales en curso.

No importar una base gigantesca de leads fríos para llenar CRM.

---

## BRV-092 — Meetings

P2 · `ACCOUNT`

Crear solo si hay volumen:

- prensa;
- clubes/librerías;
- colaboración.

Conectar calendar con mínimo permiso y buffers.

---

## BRV-093 — Conversations inbox

P2 · `ACCOUNT`

Evaluar conectar Instagram profesional/email.

No instalar widget web.

---

# Fase 10 — Capacidades deferidas

## BRV-100 — Brevo Tracker

Estado: `DEFER`.

No instalar hasta completar gate privacidad/performance/caso de uso.

---

## BRV-101 — Web Push

`DEFER`.

No pedir browser permission sin contexto.

---

## BRV-102 — SMS

`DEFER`.

No recopilar teléfono.

---

## BRV-103 — WhatsApp

`DEFER`.

No upgrade Professional por esta única función.

---

## BRV-104 — Dedicated IP

`N/A NOW`.

Gate: volumen oficial recomendado por Brevo.

---

## BRV-105 — Mobile Push

`N/A`: no app.

---

## BRV-106 — Ecommerce/abandoned cart/back-in-stock

`N/A`: no checkout propio observable.

---

## BRV-107 — Loyalty/Wallet

`N/A`: no loyalty program/direct commerce.

---

## BRV-108 — AI scoring/segmentation Pro

`DEFER`: insufficient scale/ROI.

---

# Fase 11 — Plan y coste

## BRV-110 — Quarterly plan review

P2 · `ACCOUNT/HUMAN`

Cada trimestre:

- plan;
- coste;
- contacts;
- sends;
- automation contacts;
- premium features actually used;
- add-ons;
- downgrade/upgrade gate.

---

# Orden recomendado para Claude

1. Leer toda `docs/brevo/`.
2. Leer `cloudflare-worker-subscribe.js` y `script.js` actualizados en HEAD.
3. Ejecutar/read `scripts/brevo/audit-brevo.py` cuando exista credencial autorizada.
4. Con MCP, hacer snapshot live.
5. Cerrar BRV-001/002/003.
6. Cerrar beta/DOI/rate limiter.
7. Dominio/seguridad/tracking.
8. Reader CRM/segments/consent groups.
9. Welcome/beta automations.
10. CRM profesional.
11. Webhooks/Events solo cuando baseline esté estable.
12. Revisar plan; no comprar capacidades deferidas.

---

# Regla para PRs de implementación

No meter todo este backlog en una sola PR de código.

Separar por riesgo:

- PR A: tests/hardening Worker;
- PR B: snapshot tooling read-only;
- PR C: event registry;
- PR D: webhook receiver;
- PR E: privacy/CSP si Tracker/Conversations llega a aprobarse;
- cambios de cuenta Brevo se documentan pero no necesitan fingirse como código.

---

# Merge criteria de futuras PRs

- branch desde main actual;
- tests verdes;
- cero secretos;
- staging no escribe;
- no cambia consentimiento sin copy/legal review;
- no despliega Worker;
- no envía campaña;
- no crea listas/contactos live salvo tarea expresamente autorizada;
- no llama retailer click “sale”;
- beta sigue separada;
- rollback documentado para configuración operativa.

---

# Definición de “Brevo implantado al máximo razonable”

No significa activar todas las features.

Significa:

- la cuenta está auditada;
- el dominio está autenticado;
- captación/DOI son fiables;
- consentimiento/preferencias son correctos;
- Reader CRM está segmentado sin exceso;
- welcome y beta workflows están probados;
- campañas tienen UTM/reporting;
- deliverability se observa;
- CRM profesional se usa;
- Claude tiene acceso MCP limitado;
- webhooks/API eliminan trabajo manual donde merece la pena;
- plan/costes corresponden a escala;
- Tracker/WhatsApp/push/IP dedicada permanecen apagados hasta que sus gates se cumplan.
