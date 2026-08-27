# 01 — Estado actual de Brevo y gaps reales

**Corte:** 2026-08-27  
**Objetivo:** distinguir con precisión lo que ya existe, lo que fue verificado contra la cuenta el 20/08/2026 y lo que todavía necesita comprobación live.

---

## 1. Inventario de integración existente

### 1.1 Captación web

La web usa formularios propios y un Worker de Cloudflare como backend de suscripción. Esto es una buena base y debe conservarse.

Flujo actual:

`Formulario davidportodiaz.com -> script.js -> Cloudflare Worker -> Brevo DOI -> email de confirmación -> redirección`

Contrato del navegador:

```json
{
  "email": "...",
  "source": "home|fragmento|manecillas|cuaderno|popup|explore|quiz|lectores-beta",
  "result": "opcional, solo quiz",
  "website": "honeypot"
}
```

El cliente **no** controla:

- API key;
- ID de lista;
- atributos arbitrarios;
- `updateEnabled`;
- template DOI;
- URL de redirección.

El Worker compone esos datos server-side. Mantener esta frontera.

### 1.2 Fuentes conocidas

| Source | Uso | Lista prevista |
|---|---|---|
| `home` | formulario principal | general |
| `fragmento` | lector procedente de fragmento | general |
| `manecillas` | página de Manecillas | general |
| `cuaderno` | contenido editorial | general |
| `popup` | popup propio | general |
| `explore` | diálogo Explorar | general |
| `quiz` | quiz Noveris | general |
| `lectores-beta` | programa beta | **separada** |

El Worker convierte estas claves en valores del atributo Brevo `SOURCE`.

### 1.3 Quiz Noveris

Solo admite:

- `mensajero`;
- `sabio`;
- `silenciadora`;
- `guardian`.

Se almacena en `NOVERIS` únicamente si `source === "quiz"`. No convertir este campo en texto libre.

### 1.4 Protección existente

- CORS/origin limitado al dominio real.
- Honeypot.
- Validación de email cliente + servidor.
- Allowlist de fuentes.
- Rate-limit de Cloudflare.
- Staging bloqueado para altas reales.
- Errores upstream no se filtran al navegador.
- API key server-side.
- IDs de lista server-side.
- DOI en lugar de alta silenciosa.

### Gap operativo

El rate limiter está diseñado para **fail-open** si el binding no existe, es inválido o lanza error. Eso evita perder altas por un fallo de configuración, pero significa que el despliegue debe verificar de forma expresa `RATE_LIMITER`.

No cambiar esta política dentro de una PR documental. Si se quiere `fail-closed`, debe evaluarse como decisión separada porque cambia disponibilidad/antiabuso.

---

## 2. Estado de cuenta verificado el 20/08/2026

La auditoría real documentada por `scripts/brevo/audit-brevo.py` confirmó:

### Listas

- ID `3`: **Lectores web** — lista canónica de la newsletter del sitio.
- En aquella ejecución: **2 suscriptores reales**.
- ID `4`: **identified_contacts** — no es la lista canónica del sitio.
- En aquella ejecución: 0 suscriptores.

Nunca usar el número 2 como dato actual. Es una fotografía histórica.

### Atributos

- `SOURCE` existe.
- `NOVERIS` se usa por contrato del Worker; verificar que el atributo real continúa disponible y con tipo adecuado antes de depender de él en segmentos.

### Templates

La auditoría vio 8 plantillas. Entre los nombres observados había:

- `Bienvenida_Samuel_*`;
- `Automatización #2_step_*`.

Los nombres no prueban:

- que estén activas;
- que sigan siendo editorialmente correctas;
- que formen parte de una automatización activa;
- que una alta en lista 3 dispare actualmente un email;
- que el contenido sea compatible con el lanzamiento actual de Manecillas.

### Automatizaciones

Los endpoints REST probados por el script devolvieron 404. Por eso el estado real quedó como **gate manual**.

No interpretar “hay templates con nombre automatización” como “la automatización funciona”.

---

## 3. Variables/configuración que deben verificarse en producción

### Worker

- `BREVO_API_KEY`
- `BREVO_LIST_ID`
- `BREVO_BETA_LIST_ID`
- `BREVO_DOI_TEMPLATE_ID`
- `BREVO_DOI_REDIRECT_URL`
- binding `RATE_LIMITER`

### Valores que sí conocemos conceptualmente

- `BREVO_LIST_ID` debe resolver a la lista general canónica, históricamente ID 3.
- `BREVO_BETA_LIST_ID` debe ser una lista separada y real.
- redirect esperado: una URL HTTPS propia de confirmación.

### Valores que no deben escribirse en docs/repo

- API key real;
- token MCP;
- secretos de webhook;
- credenciales SMTP;
- claves OAuth;
- datos personales de contactos.

---

## 4. Staging y producción

El contrato actual evita que el host de preview genere contactos reales.

### Regla permanente

Ningún preview, test E2E o fixture debe:

- llamar a la cuenta real de Brevo;
- crear contactos reales;
- disparar DOI real;
- enviar campañas/emails reales;
- alterar listas/atributos/consentimientos.

### Tests futuros

Usar mocks/fixtures del contrato upstream para CI.

Los smoke tests contra Brevo real son una acción humana/operativa explícita y deben hacerse con direcciones de prueba controladas.

---

## 5. Privacidad actual

La política vigente dice que:

- suscripción recopila email + origen;
- newsletter general: eventos, libros y novedades del autor;
- lectores beta: propósito independiente;
- GoatCounter y Metricool se usan para métricas agregadas sin cookies;
- no se usa Clarity;
- el sitio mantiene una postura deliberadamente ligera en tracking.

La CSP actual permite el Worker de suscripción, no el Brevo Tracker.

### Consecuencia

Instalar Brevo Tracker **no es un cambio técnico neutro**. El Tracker usa cookies propias o de terceros y transmite actividad de navegación a Brevo. Antes de instalarlo se requiere:

1. decisión de producto;
2. evaluación de base legal/consentimiento;
3. mecanismo de consentimiento cuando corresponda;
4. actualización de privacidad/cookies;
5. CSP;
6. QA;
7. documentación de retención/uso;
8. forma de revocar.

---

## 6. Gaps P0

### G0.1 — Snapshot live de cuenta

Estado: `OPEN`.

Ejecutar auditoría read-only y ampliar cobertura para obtener, sin PII:

- plan;
- listas + conteos;
- folders;
- atributos y tipos;
- consent groups y availability;
- segmentos;
- campañas recientes con métricas agregadas;
- templates activos/inactivos;
- remitentes;
- dominios + estado de autenticación;
- webhooks;
- API key metadata sin secreto si la interfaz/API lo permite;
- procesos/imports recientes;
- bounces/blocklist agregados;
- conversion metrics;
- datos de CRM agregados;
- estado de Meetings/Conversations;
- automations, por MCP/panel si REST no las expone.

### G0.2 — Lectores beta

Estado: `OPEN hasta verificación live`.

Comprobar:

- que la lista existe;
- su ID;
- `BREVO_BETA_LIST_ID` configurada;
- alta real va solo a beta;
- DOI funciona;
- workflow beta no añade newsletter general;
- copy/consentimiento corresponde al programa beta.

### G0.3 — Automatizaciones legacy

Estado: `OPEN`.

Inventariar cada workflow:

- nombre;
- estado;
- trigger;
- filtros;
- reentrada;
- delay;
- emails/templates;
- listas/segmentos implicados;
- exclusiones;
- objetivo;
- propietario;
- última modificación;
- métricas;
- decisión `KEEP / REWRITE / PAUSE / DELETE AFTER ARCHIVE`.

### G0.4 — Dominio/remitente

Estado: `OPEN`.

Verificar:

- dominio de envío autenticado;
- DKIM;
- DMARC;
- Brevo code/verification;
- sender aprobado;
- From coherente;
- Reply-To que reciba respuestas;
- nuevo flujo de dominio si la cuenta lo tiene;
- branded tracking domain solo si realmente aporta y encaja con tracking policy.

### G0.5 — Tracking email 2026

Estado: `OPEN`.

Revisar en Brevo:

- si `Per-contact pixel tracking consent` está habilitado;
- comportamiento de contactos con consentimiento desconocido;
- tracking anónimo;
- plantillas con enlace de revocación del tracking;
- formulario para gestionar preferencias;
- contactos franceses, si existen;
- automatizaciones y transaccionales de propósito mixto.

No es asesoramiento jurídico: aplicar una configuración conservadora y validar jurídicamente la política final.

### G0.6 — Seguridad

Estado: `OPEN`.

- 2FA.
- usuarios activos.
- API keys: nombre, propósito, caducidad.
- revocar claves no usadas.
- una clave por integración.
- authorized IPs.
- comprobar que cualquier endurecimiento de IP no rompe el Worker.
- evitar claves sin caducidad salvo necesidad documentada.

---

## 7. Gaps P1

### Segmentación

Hoy `SOURCE` permite segmentación básica, pero faltan segmentos operativos formalizados.

### Preferencias

No existe todavía una arquitectura confirmada de Consent Groups + preference center.

### Welcome lifecycle

No está verificado qué ocurre inmediatamente después del DOI.

### Campaign taxonomy

Falta una nomenclatura consistente para campañas, UTM, objetivo y audiencia.

### Conversion taxonomy

Falta definir qué es una conversión real en este proyecto. Nunca usar “compra” si solo podemos observar un clic a retailer.

### CRM profesional

Brevo incluye herramientas gratuitas que todavía no constan integradas en el flujo editorial: deals, pipeline, tasks, meetings.

### Webhooks

No consta un receptor de eventos Brevo propio. Esto limita observabilidad y obliga a consultar panel/API.

### MCP

Brevo dispone en 2026 de servidor MCP oficial. No está configurado en este proyecto. Es una oportunidad directa para Claude.

---

## 8. Decisiones ya cerradas que no deben revertirse sin evidencia

- Formularios propios + Worker son una arquitectura válida.
- DOI debe mantenerse.
- Beta y newsletter general tienen propósitos diferentes.
- El navegador no decide lista ni atributos de Brevo.
- Staging no escribe en Brevo real.
- `SOURCE` es server-side.
- `NOVERIS` es enumerado.
- No prometer capítulo/regalo automático si el workflow no está probado.
- No comprar IP dedicada por “parecer más profesional”.
- No activar Tracker solo para conseguir más métricas.

---

## 9. Criterio de cierre de esta auditoría de estado

Este documento puede marcarse `VERIFIED` cuando exista un snapshot live fechado posterior a la implantación y podamos responder sin inferencia:

- qué plan hay;
- qué listas existen;
- qué segmentos existen;
- qué atributos/consent groups existen;
- qué automations están activas;
- qué templates usa cada una;
- qué dominio/remitente está autenticado;
- qué tracking está activo;
- qué webhooks/API integrations hay;
- cuál es la lista beta real;
- qué seguridad de cuenta/API está activa.
