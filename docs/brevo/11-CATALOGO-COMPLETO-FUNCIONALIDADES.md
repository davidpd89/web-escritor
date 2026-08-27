# 11 — Catálogo completo de funcionalidades Brevo y aplicabilidad

**Corte:** 2026-08-27  
**Objetivo:** no dejar capacidades relevantes fuera de la auditoría. Esta matriz clasifica el ecosistema Brevo por utilidad real para davidportodiaz.com.

Estados:

- `USAR` — ya encaja o debe implantarse.
- `EVALUAR` — útil si se cumple un gate.
- `DEFER` — no ahora; revisar al crecer.
- `N/A` — no encaja con el modelo actual.
- `PRESERVAR` — ya existe y no debe sustituirse sin motivo.

---

## A. Contactos y datos

### Contacts — `USAR`

Base de Reader CRM.

Usos:

- suscriptores;
- contactos profesionales;
- atributos;
- historial;
- blocklist;
- asociaciones con CRM.

Regla: no mezclar marketing y relación profesional por comodidad.

### Contact attributes — `USAR`

Actuales: `SOURCE`, `NOVERIS`.

Futuros solo bajo necesidad. Máxima minimización.

### Lists — `USAR`

Para propósito estable/consentimiento.

- Lectores web;
- Lectores beta.

No una lista por source.

### Segments — `USAR`

Para filtros dinámicos:

- source;
- preferencias;
- engagement;
- lifecycle;
- Noveris.

### Consent Groups — `EVALUAR PRIORITARIO`

Novedad API 2026. Ideal para temas/preferencias si feature enabled.

### Folders — `USAR LIGERO`

Organizar campañas/templates si empieza a haber volumen.

No crear jerarquía compleja con 10 campañas.

### Import/export — `USAR CON CONTROL`

Solo datos con origen/consentimiento legítimo.

API moderna: `/contacts/import` para bulk; no crear nueva dependencia de `/contacts/batch` deprecado 30/10/2026.

### Custom Objects — `DEFER`

Professional/Enterprise. No hay necesidad actual.

### Data feeds — `DEFER`

Starter/Professional según tipo. Podrían alimentar contenido dinámico, pero el sitio/repo ya es fuente canónica.

### Data Platform / warehouse / SFTP — `N/A AHORA`

Enterprise-scale.

---

## B. Captación

### Signup forms — `PRESERVAR ARQUITECTURA PROPIA`

Brevo tiene formularios nativos, pero la web ya tiene mejores puntos de captación integrados.

### Pop-up forms — `NO DUPLICAR`

Ya existe popup propio.

### Profile update form — `EVALUAR PRIORITARIO`

Muy útil como preference center, especialmente con Consent Groups/pixel tracking consent.

### GDPR blocks — `REFERENCIA`

Útiles en forms nativos. En forms propios debemos tener copy/evidencia equivalente apropiada.

### CAPTCHA/antiabuse forms — `YA RESUELTO PARCIALMENTE`

Worker: honeypot + rate limit + origin. No cambiar a widget externo por defecto.

### Double opt-in — `USAR / YA EXISTE`

Mantener.

---

## C. Email marketing

### Campaigns — `USAR`

Canal principal.

### Drag & Drop editor — `USAR`

Para campañas/templates, con QA de email clients.

### HTML/simple editor — `USAR CUANDO PROCEDA`

Útil para emails muy simples/editoriales.

### Brand Library — `USAR`

Centralizar logo, colores, fonts, redes.

### Templates — `USAR`

Consolidar legacy.

### Reusable sections — `USAR`

Cabecera, footer, legal, preferences.

### A/B testing — `DEFER HASTA MUESTRA`

Standard. No útil con microaudiencia.

### Send at best time / Aura — `DEFER HASTA HISTORIAL`

Standard. Útil cuando exista engagement suficiente y tracking policy compatible.

### Send in batches — `DEFER`

Solo para volumen/deliverability operacional.

### Frequency cap / marketing pressure — `EVALUAR SEGÚN PLAN/ESCALA`

Primero resolver con calendario/segmentos.

### Advanced reporting — `EVALUAR STANDARD`

Cuando se use de verdad.

### Heatmaps/geography/device — `DEFER`

No tomar decisiones con muestras mínimas.

### UTM tracking — `USAR`

Taxonomía estable.

### Conversion metrics — `USAR CON SEMÁNTICA HONESTA`

No purchase sin compra observable.

### Anonymous email tracking — `EVALUAR PRIORITARIO`

Puede ser pieza privacy-first si se quiere señal agregada sin tracking individual.

### Per-contact pixel tracking consent — `EVALUAR PRIORITARIO 2026`

Revisar feature/config antes de campañas regulares.

---

## D. Marketing Automation

### Automation editor — `USAR`

Welcome, source-aware, beta, reengagement.

### Triggers/actions/rules — `USAR`

Con inventario y QA.

### Contact-added-to-list trigger — `USAR CON CUIDADO`

Especialmente al superar 2.000 contacts en Free/Starter: Brevo documenta comportamientos concretos al alcanzar límite/upgradear.

### Event-triggered automation — `EVALUAR`

Events API permite journeys por acciones explícitas.

### Multi-channel automation — `DEFER CANALES EXTRA`

Email sí; SMS/WhatsApp/push solo bajo gates.

### Automation logs — `USAR`

Diagnóstico y QA.

### Legacy automation — `AUDITAR`

No asumir que nombres de template equivalen a workflow activo.

---

## E. Email transaccional / Messaging API

### Transactional email API — `USAR CUANDO EL MENSAJE SEA REALMENTE TRANSACCIONAL`

El DOI ya usa endpoint específico de confirmación.

Otros casos futuros:

- confirmación operativa solicitada;
- receipt/booking si corresponde;
- servicio no promocional.

No enviar marketing por SMTP/API y llamarlo transaccional.

### SMTP relay — `DEFER`

No hace falta si endpoints API existentes cubren el caso.

### Transactional templates — `USAR CUANDO HAYA FLUJO`

Separar de marketing templates.

### Transactional webhooks — `EVALUAR PRIORITARIO`

Delivery/bounce/error observability.

### Transactional SMS — `DEFER`

No teléfonos/caso actual.

### Transactional WhatsApp — `DEFER`

Professional/Enterprise + Meta.

### Inbound Parsing — `DEFER / CASO ESPECÍFICO`

Brevo puede recibir email en un subdominio delegado, parsearlo y POSTear JSON por webhook.

Posibles usos futuros:

- sistema de replies estructurado;
- intake automatizado de respuestas de campañas/beta;
- mailbox-to-workflow.

No usar ahora porque:

- ya existe Gmail/email humano;
- requiere delegar MX de subdominio;
- procesa contenido personal;
- aumenta superficie de seguridad/privacidad.

Gate: flujo de email entrante de alto volumen y tratamiento definido.

---

## F. SMS

### SMS campaigns — `DEFER`

Créditos disponibles en todos los planes.

No recopilar teléfono sin proyecto.

### SMS transactional — `DEFER`

Mismo gate.

### SMS replies/webhooks — `DEFER`

Solo si canal existe.

---

## G. WhatsApp

### WhatsApp campaigns — `DEFER`

Professional/Enterprise.

### WhatsApp transactional — `DEFER`

### WhatsApp management/templates — `DEFER`

### WhatsApp Conversations inbox — `DEFER`

No existe necesidad/consentimiento/plan actual que lo justifique.

---

## H. Push

### Web Push — `DEFER`

Starter+ con límites por plan.

Requiere propuesta, permisos, likely Tracker/setup, privacidad y UX.

### Mobile Push — `N/A`

No app propia.

---

## I. Landing pages y overlays

### Landing Pages — `DEFER / TÁCTICO`

El sitio propio debe alojar activos SEO/editoriales.

Brevo solo para campañas temporales/no-code si aporta velocidad.

### Popup campaigns — `NO DUPLICAR`

Popup propio ya existe.

---

## J. CRM Sales

### Deals — `USAR`

Pipeline `Prensa y oportunidades`.

### Pipelines — `USAR`

1 gratuito suficiente de inicio.

### Companies — `USAR`

Medios/librerías/bibliotecas/etc.

### Tasks — `USAR`

Follow-ups.

### Notes — `USAR`

Contexto mínimo.

### Forecast/revenue reports — `USAR CON SEMÁNTICA CORRECTA`

No asignar revenue artificial a entrevistas/clubes.

### AI contact enrichment — `DEFER / PRIVACY REVIEW`

No enriquecer lectores por defecto.

### Contact scoring — `DEFER`

Professional; no escala suficiente.

---

## K. Meetings

### Booking pages — `EVALUAR`

Prensa/clubes/librerías.

### Google/Outlook calendar sync — `EVALUAR`

Mínimos permisos.

### Meeting types — `EVALUAR`

Pocos y claros.

### Video meeting integration — `EVALUAR`

Solo si se usa.

### Paid Meetings via Stripe — `N/A AHORA`

Brevo permite cobrar reuniones con Stripe.

No hay servicio de consultoría/mentoría de pago definido en este proyecto. No activar solo porque existe.

Gate futuro: servicio real, precio, fiscalidad/legal, soporte y propuesta clara.

---

## L. Conversations Platform

### Universal inbox — `EVALUAR`

Email + Instagram Direct pueden aportar ahorro de gestión.

### Instagram Direct — `EVALUAR`

Requiere professional Instagram + Facebook Page linked.

### Facebook Messenger — `EVALUAR`

### WhatsApp inbox — `DEFER`

### Live chat widget — `NO AHORA`

Duplica asistente y cambia privacidad/runtime.

### Chatbot — `NO AHORA`

Duplica asistente propio.

### Saved replies — `EVALUAR`

Útil si inbox se adopta.

### Agents/groups — `DEFER`

No hay equipo.

### Visitor intelligence / targeted chat — `DEFER`

Requiere tracking/escala.

---

## M. Phone

### Brevo Phone — `N/A AHORA`

Phone ofrece VoIP, número, inbound/outbound calls y call tracking, pero requiere Sales Advanced y actualmente los números disponibles se limitan a ciertos países documentados.

No hay necesidad de central telefónica/ventas.

Gate futuro:

- equipo;
- volumen de llamadas;
- atención profesional recurrente;
- número/país compatible;
- política de grabaciones y privacidad.

---

## N. Ecommerce

### Products — `N/A AHORA`

### Orders — `N/A AHORA`

### Abandoned cart — `N/A`

### Back in stock — `N/A`

### AI product recommendations — `N/A`

### Ecommerce conversion/revenue — `N/A SIN CHECKOUT PROPIO`

Si algún día se vende directo desde la web, reabrir todo el bloque con integración real.

---

## O. Loyalty / Wallet

### Loyalty — `N/A`

### Points/tiers/rewards — `N/A`

### Mobile Wallet passes — `N/A`

### Wallet notifications — `N/A`

Podrían tener sentido con membresía/event ticket/club directo futuro, no hoy.

---

## P. Data Platform / Enterprise

### Data warehouse connectors — `N/A`

### SFTP — `N/A`

### Data transformation — `N/A`

### Custom objects — `DEFER`

### AI data analyst — `DEFER`

### Organization/subaccounts — `N/A`

### SAML SSO — `N/A`

### SLA/CSM — `N/A`

---

## Q. Integrations / API

### REST API — `USAR`

Ya utilizada para DOI.

### Official SDKs — `EVALUAR`

Pin major; revisar changelog.

### OAuth — `N/A PARA CUENTA ÚNICA`

Solo si construimos integración multi-account/third-party.

### Events API — `EVALUAR`

Eventos explícitos.

### Webhooks — `EVALUAR PRIORITARIO`

Entregabilidad/observabilidad.

### MCP — `USAR PRIORITARIO PARA CLAUDE`

Con token separado y módulos mínimos.

### External feeds — `DEFER`

Puede ayudar a poblar drafts/digests, no autoenviar contenido.

### Processes — `USAR PARA AUDIT/OPS`

Monitorizar imports/background jobs.

---

## R. Seguridad

### API key expiration — `USAR`

### One key per integration — `USAR`

### 2FA — `USAR`

### Authorized IPs — `USAR CON CAUTELA`

No romper Cloudflare Worker.

### SAML — `N/A`

### User permissions — `USAR`

Mínimo privilegio.

---

## S. Entregabilidad

### Domain authentication — `USAR P0`

### DKIM — `USAR P0`

### DMARC — `USAR P0`

### Brevo verification code — `USAR P0`

### Branded tracking subdomain — `EVALUAR`

### Shared IP — `USAR`

### Dedicated IP — `NO AHORA`

### Warm-up — `N/A mientras shared`

### Blocklist management — `USAR`

### Bounce monitoring — `USAR`

### Complaint monitoring — `USAR`

---

## T. IA de Brevo

### Aura / send-time optimization — `DEFER HASTA DATOS`

### AI segmentation — `DEFER`

### AI product recommendations — `N/A`

### AI contact enrichment — `DEFER / PRIVACY`

### AI Conversations agent — `NO AHORA`

### MCP + Claude — `USAR`

Diferenciar claramente estas funciones: “IA de Brevo” no es una sola feature.

---

## U. Reporting y analytics

### Basic campaign reporting — `USAR`

### Advanced reports — `EVALUAR STANDARD`

### Heatmaps — `DEFER HASTA MUESTRA`

### Geography/device/browser — `DEFER HASTA MUESTRA`

### Conversion reports — `USAR SI CONVERSION REAL`

### UTM — `USAR`

### Analytics Studio — `DEFER / PROFESSIONAL`

### CRM reports — `USAR CON PIPELINE`

---

## V. Resumen de priorización

### USAR / P0-P1

- custom forms + Worker;
- DOI;
- Contacts;
- Lists por propósito;
- Segments;
- SOURCE/NOVERIS;
- Campaigns;
- Templates/Brand Library;
- Automations;
- Domain auth;
- shared IP;
- blocklist/bounce monitoring;
- UTM;
- CRM Deals/Pipeline/Tasks;
- MCP limitado;
- API audit;
- Consent Groups si available;
- preference center.

### EVALUAR PRONTO

- webhooks;
- Events API;
- advanced reporting/Standard;
- Meetings;
- Conversations inbox;
- anonymous tracking/per-contact consent;
- conversion metric.

### DEFER

- Tracker;
- web push;
- SMS;
- WhatsApp;
- scoring;
- AI segmentation;
- custom objects;
- external feeds automation;
- Phone;
- paid Meetings.

### N/A ACTUAL

- mobile push;
- ecommerce flows;
- loyalty;
- Wallet;
- data warehouse/SFTP;
- SSO;
- Enterprise organization;
- dedicated IP.

---

## W. Regla de revisión semestral

Cada seis meses, volver a comprobar:

- catálogo Brevo;
- pricing;
- plan actual;
- audiencia;
- canales;
- nuevas APIs;
- deprecaciones;
- privacidad;
- si un `DEFER` pasó a tener un caso de negocio.

No convertir `DEFER` en deuda técnica: significa conscientemente no implantar todavía.
