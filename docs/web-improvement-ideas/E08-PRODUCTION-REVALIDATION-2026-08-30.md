# E.8 · Revalidación de producción — integraciones de terceros

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **IMPLEMENTED_IN_PR · THIRD_PARTY_REGISTRY · CSP_PRIVACY_EVIDENCE_GATED · OPTIONAL_AI_PROVIDERS_BLOCKED_PENDING_REVIEW · PRIVACY_COPY_CROSSFINDING_PENDING_SAFE_EDIT**.

## 1. Gap confirmado

La investigación histórica de #135 había llegado a proponer un registro/checker de terceros, pero esa autoridad no está presente en el `main` revalidado. El sitio sí tiene integraciones reales distribuidas entre `script.js`, el shell/CSP, Workers propios, el asistente y la política de privacidad.

E.8 se implementa como gobernanza de esas integraciones, no como otra herramienta de analítica ni como medición live inventada.

## 2. Separación de capas

El registro distingue tres capas porque tienen contratos diferentes:

### Browser

El navegador conecta directamente con el proveedor. Estos hosts deben ser coherentes con el CSP público.

Casos actuales:

- GoatCounter;
- Metricool;
- Cloudflare Turnstile cuando el modo remoto del asistente está habilitado.

### Browser → edge propio

El navegador conecta con infraestructura controlada por el proyecto, que después puede mediar otra integración.

Caso actual:

- `subscribe.davidpd89.workers.dev` para suscripción.

### Server-side

El navegador no conecta directamente con el proveedor y, por tanto, el host no debe añadirse artificialmente al CSP del navegador.

Casos actuales/capacidad actual:

- Brevo DOI desde el Worker de suscripción;
- Cloudflare AI Search + Workers AI desde el Worker del asistente;
- Groq/OpenRouter como proveedores opcionales de fallback en el Worker del asistente.

## 3. Autoridad añadida

`data/third-party-integrations.json` registra para cada integración:

- `id` estable;
- proveedor;
- capa;
- `status`;
- finalidad;
- trigger;
- failure mode;
- alcance de datos;
- decisión;
- owner files;
- evidencia literal en código/configuración;
- hosts/directivas CSP cuando aplica al navegador;
- evidencia de disclosure de privacidad cuando el proveedor está activo o condicional;
- gate de activación para capacidades opcionales deshabilitadas.

El registro no incluye meros enlaces salientes, afiliados, documentación histórica, Gmail usado manualmente ni dependencias vendorizadas sin tráfico de red.

## 4. Estado actual inventariado

### Activas

- **GoatCounter** — browser. `script.js` inyecta `https://gc.zgo.at/count.js` y configura `https://davidportodiaz.goatcounter.com/count`. CSP y privacidad contienen el contrato correspondiente.
- **Metricool** — browser. `script.js` inyecta `https://tracker.metricool.com/resources/be.js`. CSP permite script/connect/img para ese host y privacidad lo declara.
- **Cloudflare Worker de suscripción** — browser-to-edge. `script.js` POSTea a `https://subscribe.davidpd89.workers.dev`; CSP lo permite en `connect-src` y privacidad declara Cloudflare como intermediario técnico.
- **Brevo DOI** — server-side. `cloudflare-worker-subscribe.js` llama a `https://api.brevo.com/v3/contacts/doubleOptinConfirmation`; privacidad declara Brevo.

### Condicionales

- **Cloudflare Turnstile** — browser. Solo se carga cuando el asistente remoto está habilitado y una consulta llega a esa capa; el cliente cae a Pagefind/local si no puede usarla.
- **Cloudflare AI Search + Workers AI** — server-side. La configuración versionada mantiene `ASSISTANT_ENABLED="false"`; el código y privacidad describen la capacidad, pero esto no prueba un servicio live activo.

### Opcionales deshabilitadas

`cloudflare-worker-assistant.js` contiene una cadena de fallback que también soporta:

- Groq mediante `GROQ_API_KEY`;
- OpenRouter mediante `OPENROUTER_API_KEY`.

`wrangler.assistant.jsonc` contiene modelos/caps pero no valores de secrets y mantiene `ASSISTANT_ENABLED="false"`.

Estas capacidades se registran como `optional_disabled`, **no como integraciones activas**. Antes de poder activarlas el registro exige, entre otras cosas:

1. actualizar privacidad para identificar el proveedor y flujo de datos;
2. revisar condiciones/transferencias aplicables;
3. configurar secret fuera del repositorio;
4. ejecutar QA E2E/calidad/coste;
5. actualizar el propio registro antes del despliegue.

Esto evita que añadir un secret fuera de Git convierta silenciosamente una capacidad de código en un nuevo proveedor de producción no gobernado.

## 5. Checker

`scripts/check-third-party-integrations.py` valida:

- schema, ids, estados y capas;
- existencia de owners;
- evidencia literal declarada en owners;
- disclosure en `privacidad.html` cuando se exige;
- coherencia de `browser_hosts` con el CSP público de `index.html`;
- que integraciones `server_side` no introduzcan hosts CSP falsos;
- que `optional_disabled` tenga gate explícito y no finja disclosure activo.

La detección no hace grep global de toda URL externa porque produciría falsos positivos con enlaces editoriales, Amazon, fuentes documentales y material histórico. El contrato se ancla en los owners reales de runtime/configuración.

## 6. CI y merge gate

La PR añade:

- `tests/test-third-party-integrations.py`;
- `.github/workflows/third-party-integrations-qa.yml`;
- ejecución explícita del checker en `.github/workflows/required-merge-gate.yml`.

Por tanto, una futura modificación de un owner, CSP, privacidad o registro puede romper el contrato antes del merge.

## 7. Crossfinding: copy de consentimiento de newsletter

Durante la revalidación apareció una inconsistencia factual separada que **no se marca como corregida** en esta PR:

`privacidad.html` afirma actualmente que:

- «El formulario exige aceptar esta política antes de enviarlo»;
- en la descripción de Brevo, «El formulario exige marcar la casilla de aceptación de esta política antes de poder enviarlo».

Sin embargo, la inspección directa de Home y `/fragmento/` muestra formularios con email + botón, sin checkbox de privacidad, y el handler genérico `submitNewsletter(formId, emailId, gdprId, ...)` recibe un `gdprId` pero no lo consulta ni valida.

Esto es una divergencia **markup/runtime ↔ texto legal**, no una conclusión jurídica.

La corrección factual recomendada, si se mantiene el diseño DOI actual, es describir el flujo real:

- el envío inicia la solicitud de suscripción;
- la suscripción se completa mediante el correo de doble opt-in de Brevo;
- no se envía a Brevo un campo de checkbox/consentimiento independiente ni una timestamp de checkbox.

Alternativamente, si producto quiere recuperar una casilla explícita, debe implementarse y validarse de verdad en todas las superficies antes de mantener ese copy.

### Por qué no se edita aquí

El conector disponible reemplaza el HTML completo y `privacidad.html` es un fichero largo. No se reconstruye manualmente el documento entero para cambiar dos frases porque el riesgo de corrupción/regresión supera el valor de ese método. El crossfinding queda asignado para edición local/hunk segura y no se presenta como resuelto.

## 8. Qué no hace E.8

- no añade banner de consentimiento;
- no emite opinión legal sobre necesidad de consentimiento;
- no mide bytes live de terceros;
- no prueba que un secret externo esté o no configurado;
- no afirma que el asistente remoto esté activo cuando la configuración versionada dice `false`;
- no añade Groq/OpenRouter al CSP porque son server-side;
- no convierte enlaces a Amazon/redes/medios en “integraciones runtime”.

## 9. Relación con E.5

E.5 gobierna bytes/requests locales del artifact. E.8 gobierna dependencias de red/proveedores y sus boundaries de privacidad/CSP/activación.

Un third-party puede no añadir bytes al repo y aun tener coste de red/privacidad. Un bundle local puede crecer sin añadir proveedor externo. Son controles complementarios.

## 10. Estado para integración

E.8 pasa de backlog histórico a un contrato versionado y verificable. El único crossfinding abierto de esta revalidación es el copy factual del consentimiento de newsletter, que requiere una edición HTML segura y separada antes de considerarlo cerrado.