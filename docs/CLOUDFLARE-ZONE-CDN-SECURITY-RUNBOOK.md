# Cloudflare — auditoría de zona, CDN, seguridad y Workers

Fecha de auditoría: 2026-08-23  
Base de código: `implementacion-web-2026@170798340935e7d0f6ffffbab5749ce98f073604`  
Ámbito: **Cloudflare únicamente**. Este documento no despliega, no modifica `main`, no cambia DNS en vivo y no contiene credenciales.

## 1. Conclusión ejecutiva

Cloudflare **sí existe en la arquitectura del proyecto**, pero la web principal no está aprovechando hoy la mayor parte de su red.

Evidencia del repositorio:

- `cloudflare-worker-subscribe.js` — Worker de newsletter; su lógica DOI/honeypot/rate limit tiene owner en #55.
- `cloudflare-worker-assistant.js` — Worker preparado para `/api/assistant*` con Workers AI, AI Search, D1, Turnstile y rate limits.
- `wrangler.assistant.example.jsonc` — configuración reproducible de los bindings del Asistente.
- `CNAME` + GitHub Pages — el origen público de la web sigue siendo GitHub Pages.
- no hay `CLOUDFLARE_API_TOKEN` versionado en el repo, que es lo correcto.

Evidencia de cuenta/operación:

- el 27/05/2026 Cloudflare notificó por correo que `davidportodiaz.com` se había añadido a la cuenta pero **no estaba usando sus nameservers**;
- el 22/06/2026 Cloudflare notificó que eliminó `davidportodiaz.com` de la cuenta por **setup incompleto de nameservers**.

Evidencia DNS pública disponible durante esta auditoría (debe revalidarse en tiempo real inmediatamente antes de tocar DNS):

- `davidportodiaz.com` resolvía a los cuatro IPv4 de GitHub Pages `185.199.108.153`, `.109.153`, `.110.153`, `.111.153`;
- nameservers observados: `launch1.spaceship.net` y `launch2.spaceship.net`;
- registrador: Spaceship;
- DNSSEC: `signedDelegation`, con DS publicado.

Por tanto, la oportunidad real no es «crear otro Worker», sino **terminar correctamente el onboarding de la zona en Cloudflare y poner la web pública detrás del proxy**. Eso permite aprovechar CDN, HTTP/3, compresión edge, DDoS/WAF, TLS endurecido, reglas de caché, observabilidad y rutas Worker en el dominio propio.

La migración debe hacerse de forma controlada porque **DNSSEC está activo**. Cambiar nameservers conservando un DS del proveedor anterior puede romper la cadena de confianza y dejar el dominio inaccesible.

## 2. Qué ya está cubierto y NO debe duplicar esta PR

| Área | Owner actual | Qué hace esta PR |
|---|---|---|
| Worker newsletter / DOI / honeypot / rate limiting | #55 | Solo documenta cómo alojarlo/operarlo en Cloudflare; no modifica su lógica |
| Runtime web, imágenes, popup | #61 | No modifica runtime |
| CSP del sitio | #62 | Cloudflare debe respetar/coordinarse con ese CSP; no crea una segunda política |
| Analítica de producto/eventos | #63 | Cloudflare Web Analytics solo se propone como RUM opcional, no como nueva taxonomía |
| Playwright/Node | #65 | No crea otra autoridad Node |
| Staging/post-deploy smoke | #58/#79/#1 | Define qué comprobar de Cloudflare cuando se despliegue |
| Pagefind | #91 | No altera búsqueda local |
| Diseño | #82–#90 | Ningún setting Cloudflare debe introducir transformaciones visuales no auditadas |

## 3. Estado objetivo recomendado

Arquitectura propuesta:

```text
Visitante
   ↓
Cloudflare DNS + proxy (davidportodiaz.com / www)
   ├─ CDN / TLS / HTTP/3 / compresión / WAF / DDoS
   ├─ /api/assistant* → Cloudflare Worker del Asistente
   └─ resto → GitHub Pages (origen estático)

Worker newsletter
   └─ conservar workers.dev inicialmente o migrar después a hostname/ruta propia
      solo si se decide expresamente y #55 está cerrado
```

No se propone migrar el hosting estático desde GitHub Pages a Cloudflare Workers/Pages. El beneficio se obtiene poniendo Cloudflare delante del origen actual, con menos riesgo y sin rehacer la publicación.

## 4. Fase 0 — preflight obligatorio antes de tocar nameservers

### 4.1 Inventario DNS

Antes de crear/cambiar nada:

1. Exportar o copiar **todos** los registros actuales en Spaceship.
2. Registrar al menos: `A`, `AAAA`, `CNAME`, `MX`, `TXT`, SPF, DKIM, DMARC, verificaciones, CAA y cualquier subdominio.
3. No importar a ciegas el escaneo automático de Cloudflare: comparar registro por registro.
4. Comprobar específicamente que no desaparezca ningún registro de correo.
5. No crear `*` wildcard. GitHub desaconseja los wildcards en custom domains por riesgo de takeover.

Para GitHub Pages, la referencia oficial actual para el apex es:

```text
A @ 185.199.108.153
A @ 185.199.109.153
A @ 185.199.110.153
A @ 185.199.111.153

AAAA @ 2606:50c0:8000::153
AAAA @ 2606:50c0:8001::153
AAAA @ 2606:50c0:8002::153
AAAA @ 2606:50c0:8003::153
```

GitHub recomienda además configurar la variante `www` junto al apex; si se usa, debe apuntar al hostname `github.io` correspondiente según la configuración real de Pages, no inventarse en este documento.

### 4.2 GitHub Pages

Antes de activar proxy:

- confirmar que `davidportodiaz.com` sigue siendo el custom domain configurado en Settings → Pages;
- confirmar **Enforce HTTPS**;
- comprobar que el certificado de GitHub Pages está válido y cubre el hostname;
- comprobar `CNAME` del repo;
- verificar que no hay mixed content `http://`.

### 4.3 DNSSEC — punto crítico

La evidencia pública de esta auditoría muestra un DS activo. Cloudflare advierte que, en una migración normal, no debe cambiarse a sus nameservers dejando el DS antiguo publicado.

Ruta conservadora si Spaceship no permite multi-signer DNSSEC:

1. Añadir la zona a Cloudflare y dejarla `Pending`.
2. Replicar y revisar todos los DNS records.
3. En el registrador/Spaceship, **eliminar/desactivar el DS/DNSSEC actual**.
4. Esperar a que expire el TTL del DS en la zona padre. Verificar con un resolver independiente (`dig DS davidportodiaz.com`). Cloudflare indica que puede requerir 24–48 h según el TLD/TTL.
5. Solo entonces cambiar en Spaceship los nameservers por los dos asignados por Cloudflare.
6. Esperar activación/propagación y comprobar resolución desde varios resolvers.
7. Activar DNSSEC en Cloudflare.
8. Copiar el nuevo DS que entrega Cloudflare al registrador.
9. Verificar de nuevo la cadena DNSSEC completa.

Cloudflare también documenta migración DNSSEC activa/multi-signer, pero exige que el proveedor anterior pueda publicar DNSKEY externos. No usar esa ruta salvo confirmar que Spaceship soporta exactamente ese flujo.

**Rollback DNSSEC:** si hubiera que volver atrás, retirar primero el DS correspondiente y respetar su TTL. No alternar nameservers con un DS incompatible.

## 5. Fase 1 — crear/recrear la zona Cloudflare

El correo confirma que la zona anterior fue retirada por setup incompleto, así que asumir que hay que **recrear o reañadir** `davidportodiaz.com` y verificar su estado actual antes de configurar settings.

### Dashboard

Cloudflare → Add a domain → `davidportodiaz.com` → plan apropiado → revisar records → recibir nameservers asignados.

### API

Cloudflare permite crear la zona con `POST /zones`. Usar token de API, no Global API Key.

Variables locales, nunca en git:

```bash
export CLOUDFLARE_API_TOKEN='...'
export CLOUDFLARE_ACCOUNT_ID='...'
```

Ejemplo conceptual:

```bash
curl 'https://api.cloudflare.com/client/v4/zones' \
  --request POST \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  --header 'Content-Type: application/json' \
  --data "{\"account\":{\"id\":\"$CLOUDFLARE_ACCOUNT_ID\"},\"name\":\"davidportodiaz.com\",\"type\":\"full\"}"
```

La actualización de **nameservers en el registrador** no la hace esta API de Cloudflare: debe realizarse en Spaceship (dashboard o API oficial de Spaceship si se decide y se dispone de ella). Cloudflare no puede sustituir ese paso externo.

## 6. Fase 2 — proxy + TLS

### 6.1 Activación progresiva

Primero migrar DNS con los records web en **DNS only** (nube gris). Confirmar que GitHub Pages sigue resolviendo y que HTTPS está sano. Después activar `Proxied` (nube naranja) en los hostnames web.

Registros de correo (`MX`, DKIM, etc.) nunca deben ponerse en proxy HTTP.

### 6.2 SSL/TLS: Full (strict)

Una vez el proxy esté activo y GitHub Pages presente certificado público válido:

- `SSL/TLS encryption mode`: **Full (strict)**.
- **No usar Flexible**.
- Universal SSL: **ON**.

API:

```bash
export CLOUDFLARE_ZONE_ID='...'

curl "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/settings/ssl" \
  --request PATCH \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  --json '{"value":"strict"}'
```

GitHub Pages usa certificados públicos para custom domains correctamente configurados, por lo que `Full (strict)` es el modo adecuado cuando el certificado del origen está sano.

### 6.3 Always Use HTTPS

Recomendado: **ON**, después de verificar HTTPS.

```bash
curl "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/settings/always_use_https" \
  --request PATCH \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  --json '{"value":"on"}'
```

Evitar cadenas de redirects redundantes. Comprobar `http → https` y `www ↔ apex` con `curl -I`.

### 6.4 TLS mínimo y TLS 1.3

Recomendación para este sitio público moderno:

- Minimum TLS: **1.2**.
- TLS 1.3: **ON**.
- 0-RTT: **OFF inicialmente**. No necesitamos asumir el riesgo/semántica de early data para obtener el beneficio principal de TLS 1.3.

```bash
curl "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/settings/min_tls_version" \
  --request PATCH \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  --json '{"value":"1.2"}'

curl "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/settings/tls_1_3" \
  --request PATCH \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  --json '{"value":"on"}'
```

No personalizar cipher suites sin una necesidad real; Cloudflare recomienda sus defaults y la personalización requiere producto adicional.

### 6.5 HSTS — deliberadamente tardío

HSTS **no debe activarse durante la migración DNS**. Cloudflare advierte que, una vez cacheado por los navegadores, pausar Cloudflare, volver a DNS-only o perder HTTPS puede dejar el sitio inaccesible durante el `max-age`.

Orden recomendado:

1. proxy estable;
2. Full (strict) estable;
3. HTTPS y redirects verificados en apex + `www` + subdominios reales;
4. esperar observación estable;
5. activar HSTS.

Primera configuración conservadora:

- HSTS: ON;
- `includeSubDomains`: OFF inicialmente;
- `preload`: OFF;
- No-Sniff: ON si el plan/settings lo permiten;
- max-age: usar inicialmente una duración prudente y aumentarla solo tras estabilidad.

Cloudflare documenta el setting API como `security_header`; para esta operación se recomienda **dashboard primero** por el riesgo y porque permite revisar visualmente todas las opciones antes de guardar. No activar preload hasta cumplir los requisitos de 12 meses y verificar todos los subdominios.

### 6.6 Certificate Transparency Monitoring

Recomendado: **ON**. Es opt-in y actualmente está disponible en todos los planes. Enviar las alertas a un correo operativo revisado.

Dashboard: SSL/TLS → Edge Certificates → Certificate Transparency Monitoring → Add Email.

No sustituye DNSSEC ni CAA, pero detecta certificados inesperados emitidos para el dominio.

## 7. Fase 3 — rendimiento y CDN

### 7.1 HTTP/3

Recomendado: **ON**. Disponible en todos los planes y útil especialmente en redes móviles/con pérdida.

```bash
curl "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/settings/http3" \
  --request PATCH \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  --json '{"value":"on"}'
```

Verificar después `Alt-Svc`/negociación HTTP/3 desde un cliente compatible.

### 7.2 Compresión

No crear una regla custom inicialmente. Cloudflare ya comprime tipos de texto y, en Free, la documentación actual indica Zstandard por defecto cuando el cliente lo admite, con fallbacks según configuración/cliente.

Validar `Content-Encoding` real para HTML/CSS/JS. Solo introducir Compression Rules si las mediciones justifican cambiar el comportamiento por defecto.

### 7.3 Caché estática

Al poner los hostnames en `Proxied`, Cloudflare ya puede cachear extensiones estáticas como imágenes, JS, CSS, fuentes, PDF, AVIF/WebP, etc. HTML y JSON **no se cachean por defecto**.

Para esta web eso es un buen punto de partida:

- conservar el comportamiento CDN por defecto para assets;
- Browser Cache TTL: **Respect Existing Headers** al principio;
- no poner un TTL de navegador largo de forma global porque muchos assets actuales tienen nombres estables (`styles.css`, `script.js`, etc.) y purgar Cloudflare **no borra la caché del navegador**;
- mantener `/api/*` fuera de cualquier regla de cache agresiva;
- no cachear respuestas de Workers/APIs con una regla «Cache Everything» global.

### 7.4 HTML: no hacer «Cache Everything» todavía

La web es estática, por lo que cachear HTML en edge puede tener valor. Sin embargo, en Free el Edge Cache TTL mínimo configurable es actualmente 2 horas y el proyecto actualiza contenido con frecuencia.

No activar cache HTML hasta tener:

1. regla explícita que excluya `/api/*` y endpoints dinámicos;
2. estrategia de purge integrada al despliegue;
3. smoke que compruebe que un deploy nuevo aparece inmediatamente;
4. confirmación de que no se ocultan cambios urgentes/editoriales.

Cuando exista ese mecanismo, puede evaluarse un Edge TTL bajo/controlado y purge por URL/prefix/host tras deploy.

API de purge:

```bash
curl "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/purge_cache" \
  --request POST \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  --json '{"files":["https://davidportodiaz.com/"]}'
```

Cloudflare recomienda purge granular por URL cuando sea posible. `purge_everything` debe reservarse para cambios globales.

### 7.5 Early Hints

**No activar como supuesto beneficio automático.** Cloudflare solo genera Early Hints cuando la respuesta final contiene cabeceras HTTP `Link` con `preload`/`preconnect`. GitHub Pages no permite que asumamos esas cabeceras desde este repo.

Procedimiento:

1. comprobar `curl -I` de páginas reales detrás de Cloudflare;
2. si no existen `Link` headers útiles, Early Hints no aporta el efecto esperado;
3. solo añadirlo si se introduce deliberadamente una capa capaz de emitir esos headers y se mide mejora.

### 7.6 Speed Brain

Cloudflare lo habilita por defecto en Free según su documentación actual, pero solo prefetches páginas elegibles para caché y no páginas que invoquen Worker.

El repo ya usa `speculationrules` en algunas páginas. Antes de dejar ambos mecanismos actuando:

- comprobar en navegador qué reglas llegan finalmente;
- evitar duplicar prefetches o descargar navegación innecesaria;
- medir transferencia/LCP/INP;
- si genera comportamiento redundante, desactivar Speed Brain y conservar la estrategia controlada por el sitio.

### 7.7 Rocket Loader

Recomendación: **OFF**.

Motivos específicos del repo:

- runtime modular y cargado por página;
- Service Worker/PWA;
- Turnstile;
- Pagefind dinámico;
- CSP estricta en #62;
- suites de browser QA que ya controlan orden/comportamiento JS.

Rocket Loader reescribe/difiere scripts y Cloudflare advierte que un CSP necesita cambios adicionales. No introducir esa variable durante el rediseño sin una prueba específica que demuestre una ganancia neta.

### 7.8 Cloudflare Fonts / transformaciones HTML / Email Obfuscation

No activar de forma global en la primera migración. Las transformaciones que reescriben contenido pueden cambiar HTML, provocar recompression y complicar CSP/QA. La web ya tiene sistema tipográfico y tratamiento editorial propio.

### 7.9 Image Resizing / Polish / Mirage

No adoptar ahora. #61 y #67 ya poseen responsive images + AVIF/WebP y #83 la procedencia visual. Una capa edge que transforme medios duplicaría autoridad y podría romper control editorial/QA. Evaluar solo si datos reales muestran un cuello de botella no resuelto por el pipeline actual.

### 7.10 Argo / productos de pago

No contratar por defecto. GitHub Pages + Cloudflare CDN para un sitio mayoritariamente estático debe medirse primero. Argo Smart Routing no es una prioridad sin evidencia de latencia/origen que lo justifique.

## 8. Fase 4 — seguridad edge

### 8.1 DDoS

Una vez el tráfico esté `Proxied`, la protección DDoS de Cloudflare está activa automáticamente en todos los planes. No necesita una regla propia.

### 8.2 WAF Free Managed Ruleset

En Free, Cloudflare despliega por defecto el **Cloudflare Free Managed Ruleset**, un subconjunto orientado a vulnerabilidades de alto impacto.

Acción:

- confirmar que está activo después de activar la zona;
- revisar Security → Events/Analytics los primeros días;
- no añadir excepciones preventivas sin evidencia de falso positivo;
- si se usa plan superior, evaluar Cloudflare Managed Ruleset/OWASP con rollout controlado.

### 8.3 Bot Fight Mode

Recomendación inicial: **OFF**.

Razón: en Free opera sobre todo el dominio, puede desafiar tráfico API/automatizado y **no puede excluirse con WAF custom rules**. Esta web quiere ser rastreable por Google, Bing y bots/search agents autorizados y además tiene endpoints Worker.

Es preferible:

- DDoS automático;
- Free Managed Ruleset;
- Turnstile en acciones costosas;
- rate limits del Worker;
- custom rules focalizadas cuando exista una amenaza concreta.

Si en el futuro se usa Super Bot Fight Mode (plan compatible), entonces sí es posible aplicar `Skip` selectivo.

### 8.4 Block AI Bots

**No activar** con la estrategia actual de descubrimiento. La web ha decidido explícitamente permitir descubrimiento por buscadores/IA y `robots.txt`/gates ya poseen esa política. No contradecirla desde Cloudflare.

### 8.5 WAF/custom rules para APIs

No bloquear por país, ASN o user-agent de forma preventiva.

Para `/api/assistant*`, la defensa primaria ya está en el Worker: origin allowlist, Turnstile, tres rate limiters y cuota D1. Cloudflare WAF puede añadir mitigación ante abuso observado, pero no debe sustituir ese contrato ni romper `OPTIONS`/CORS.

Para newsletter, respetar #55 y no crear una segunda política contradictoria.

### 8.6 Authenticated Origin Pulls / Origin CA

**No aplicar al GitHub Pages origin.** No controlamos el servidor GitHub para instalar un certificado Origin CA ni exigir mTLS desde Cloudflare. `Full (strict)` con el certificado público de GitHub es la opción adecuada.

## 9. Fase 5 — Turnstile

Turnstile ya forma parte del contrato del Asistente, pero debe materializarse en la cuenta antes de activar IA.

### Recomendación

- widget dedicado al Asistente;
- modo: `managed`;
- hostname obligatorio: `davidportodiaz.com`;
- añadir **solo** el hostname real de staging cuando esté decidido/activo;
- no usar dominios genéricos/wildcards;
- `TURNSTILE_SITE_KEY`: variable pública del Worker;
- `TURNSTILE_SECRET_KEY`: secreto del Worker, nunca git;
- validación server-side con Siteverify: ya está implementada en `cloudflare-worker-assistant.js`;
- sin pre-clearance inicialmente salvo necesidad demostrada.

### API

Requiere token con `Turnstile Sites Write` (o permiso equivalente documentado por Cloudflare):

```bash
curl "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/challenges/widgets" \
  --request POST \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  --json '{
    "domains":["davidportodiaz.com"],
    "mode":"managed",
    "name":"davidportodiaz.com — Asistente"
  }'
```

La API también permite actualizar el widget y rotar el secret. Si alguna clave se ha compartido fuera del gestor de secretos, rotarla antes de producción.

## 10. Fase 6 — Worker del Asistente en dominio propio

`cloudflare-worker-assistant.js` ya declara como ruta de producción deseada:

```text
https://davidportodiaz.com/api/assistant*
```

Cloudflare recomienda **Workers Routes** cuando hay un origen externo detrás del Worker; encaja con GitHub Pages. Un Custom Domain enviaría todo el hostname al Worker y no es lo que necesitamos para un único path.

Después de activar la zona, completar `wrangler.assistant.example.jsonc` en una configuración de despliegue no secreta y añadir una route del estilo:

```jsonc
{
  "workers_dev": false,
  "route": {
    "pattern": "davidportodiaz.com/api/assistant*",
    "zone_name": "davidportodiaz.com"
  }
}
```

Bindings que ya exige el código:

- `AI` → Workers AI;
- `ASSISTANT_SEARCH` → AI Search;
- `ASSISTANT_QUOTA_DB` → D1;
- `SESSION_RATE_LIMITER`;
- `IP_RATE_LIMITER`;
- `GLOBAL_RATE_LIMITER`;
- `TURNSTILE_SITE_KEY`;
- secret `TURNSTILE_SECRET_KEY`;
- `TURNSTILE_HOSTNAMES`.

Mantener `ASSISTANT_ENABLED=false` hasta que bindings, Turnstile, corpus y smoke estén completos. Activarlo es un paso operativo separado.

API alternativa para la route: `POST /zones/{zone_id}/workers/routes`. Wrangler es preferible como fuente de verdad porque el repo ya contiene configuración Worker y Cloudflare recomienda que el fichero Wrangler gobierne el despliegue.

## 11. Worker de newsletter

No moverlo automáticamente.

Hoy el frontend conoce el endpoint `subscribe.davidpd89.workers.dev` y #55 está cerrando su comportamiento. La migración de zona no exige cambiarlo.

Después de #55, puede evaluarse si conviene llevarlo a un hostname/ruta de `davidportodiaz.com` para homogeneidad/CSP. Esa decisión debe hacerse con cambio coordinado de endpoint + CSP + smoke; esta PR no inventa un subdominio ni modifica el Worker.

## 12. Cloudflare Web Analytics / RUM

Es una oportunidad útil pero **opcional**, no una activación automática.

Cloudflare Web Analytics proporciona RUM/Core Web Vitals sin cookies ni `localStorage` y Cloudflare documenta medición sin sampling. Esto sería especialmente útil porque Lighthouse ha mostrado variabilidad de LCP en `/asistente/` y necesitamos métricas de usuarios reales.

Pero la web ya usa GoatCounter y Metricool. Añadir un tercer sistema sin propósito claro sería ruido.

Decisión recomendada:

- activar Cloudflare Web Analytics **solo como observabilidad RUM/CWV** si queremos diagnosticar LCP/INP/CLS reales;
- coordinar con #63 y la política de privacidad;
- comprobar si Cloudflare inyecta beacon/configuración que requiere ampliar #62 CSP;
- no usarlo para crear otra taxonomía de conversiones.

Si no aporta una pregunta de rendimiento concreta, dejarlo OFF.

## 13. API vs dashboard — matriz operativa

| Tarea | API | Dashboard/manual | Recomendación |
|---|---:|---:|---|
| Crear/recrear zona | Sí (`POST /zones`) | Sí | API o dashboard |
| Revisar/importar DNS | Sí | Sí | Dashboard + doble comprobación humana |
| Cambiar nameservers en Spaceship | No desde Cloudflare | **Sí, externo** | Manual/registrar |
| Retirar DS antiguo en registrador | No desde Cloudflare | **Sí, externo** | Manual/registrar |
| Activar DNSSEC Cloudflare / obtener DS | Sí (`/zones/{id}/dnssec`) | Sí | Dashboard durante migración; API después |
| Proxy DNS record | Sí | Sí | API una vez verificado |
| Full (strict) | Sí | Sí | API reproducible |
| Always Use HTTPS | Sí | Sí | API reproducible |
| Minimum TLS 1.2 | Sí | Sí | API reproducible |
| TLS 1.3 | Sí | Sí | API reproducible |
| HTTP/3 | Sí | Sí | API reproducible |
| HSTS | Sí (`security_header`) | Sí | **Dashboard primero** por riesgo |
| CT Monitoring | No depender de automatización aquí | Sí | Dashboard |
| Cache Rules | Sí (Rulesets API) | Sí | Solo tras diseñar purge |
| Purge cache | Sí | Sí | API en deploy |
| WAF/Custom Rules | Sí (Rulesets API) | Sí | Dashboard para observación inicial; API si se estabiliza |
| Turnstile widget | Sí | Sí | API reproducible |
| Worker deploy | Sí/Wrangler | Sí | **Wrangler** |
| Worker route | Sí/Wrangler | Sí | **Wrangler** como fuente de verdad |
| Cloudflare Web Analytics | Depende del método | Sí | Dashboard y revisión #63/#62 |

## 14. Tokens/permisos — mínimo privilegio

No usar Global API Key en automatizaciones.

Separar, si es posible:

### Token de administración de zona (uso humano/ocasional)

- Zone Read;
- Zone Settings Write;
- DNS Read/Write;
- Rulesets/Firewall Write solo si se materializan reglas;
- Cache Purge.

### Token de despliegue Worker

- Workers Scripts Write;
- Workers Routes Write / permisos de zona necesarios;
- recursos de cuenta estrictamente requeridos por los bindings.

### Token Turnstile

- Turnstile Sites Write.

Guardar tokens en GitHub Secrets / gestor de secretos correspondiente, nunca en `.env` versionado ni documentación.

## 15. Configuraciones que NO recomiendo activar ahora

- **Flexible SSL** — reduce seguridad origen↔Cloudflare.
- **Bot Fight Mode Free** — demasiado global/no exceptuable para esta arquitectura.
- **Block AI Bots** — contradice la estrategia de descubrimiento.
- **Rocket Loader** — riesgo de alterar runtime/CSP sin necesidad demostrada.
- **HSTS preload desde el primer día** — rollback peligroso.
- **includeSubDomains HSTS sin inventario completo**.
- **Cache Everything global** — riesgo de cachear APIs/HTML stale.
- **Browser TTL largo global** — assets actuales no están todos fingerprinted; purge edge no limpia browser cache.
- **AOP/Origin CA/AOPull para GitHub Pages** — no controlamos ese origen.
- **Image transformations automáticas** — duplican #61/#67/#83.
- **Zaraz** — no introducir otra capa de terceros mientras GoatCounter/Metricool ya existen.
- **Argo de pago** — medir antes.
- **wildcard DNS** — GitHub desaconseja su uso para Pages.
- **migrar todo el hosting a Workers/Pages** — fuera de alcance y sin necesidad demostrada.

## 16. Rollback

### Tras activar proxy pero antes de HSTS

Si aparece un problema edge:

1. pasar el hostname afectado de `Proxied` a `DNS only`;
2. confirmar que GitHub Pages vuelve a servir directamente;
3. revisar SSL/rules/cache;
4. purgar cache si procede.

### Después de HSTS

No usar «pasar a DNS only» como rollback automático: Cloudflare advierte que HSTS puede exigir que el hostname siga sirviendo HTTPS correctamente durante todo el `max-age`. Primero mantener HTTPS operativo y reducir/desactivar HSTS de forma planificada.

### Worker

- `ASSISTANT_ENABLED=false` es el kill switch funcional del Asistente;
- eliminar/desactivar la route devuelve `/api/assistant*` al origen, por lo que el cambio debe acompañarse del comportamiento esperado del frontend;
- no borrar bindings/D1 como primer mecanismo de rollback.

### DNSSEC

Nunca revertir nameservers conservando un DS incompatible. Tratar DS y NS como una operación coordinada con TTL.

## 17. QA posterior a la migración

### DNS

```bash
dig NS davidportodiaz.com
dig A davidportodiaz.com
dig AAAA davidportodiaz.com
dig DS davidportodiaz.com
```

Comprobar desde al menos dos resolvers independientes.

### HTTPS / proxy

```bash
curl -I https://davidportodiaz.com/
curl -I http://davidportodiaz.com/
curl -I https://www.davidportodiaz.com/
```

Esperado tras proxy:

- HTTPS válido;
- redirect canónico único;
- cabeceras Cloudflare (`cf-ray`, etc.) donde apliquen;
- sin redirect loops;
- CSP final de #62 sigue activa y sin errores.

### TLS

```bash
curl --tls-max 1.1 -I https://davidportodiaz.com/   # debe fallar si min TLS=1.2
curl --tlsv1.3 -I https://davidportodiaz.com/
```

### CDN

Probar dos veces un asset estático:

```bash
curl -I https://davidportodiaz.com/assets/<asset-real>
```

Revisar `CF-Cache-Status` (`MISS` inicial y `HIT` posterior cuando sea cacheable), `Content-Encoding` y `Age` si aplica.

No exigir `HIT` a HTML mientras no exista Cache Rule explícita.

### APIs

- `/api/assistant/config` no debe quedar cacheado;
- `POST /api/assistant` debe atravesar Worker/Turnstile/rate limits;
- `OPTIONS` debe conservar CORS esperado;
- newsletter debe seguir funcionando según #55;
- cero secretos en respuestas/logs.

### SEO/findability

- `robots.txt`;
- `sitemap.xml`;
- canonical;
- acceso Googlebot/Bingbot/OAI-SearchBot/Claude-SearchBot según política del repo;
- `Block AI Bots` debe permanecer OFF si se mantiene la política actual;
- comprobar que WAF no desafía bots deseados.

### Rendimiento

Después de propagación y calentamiento:

- Lighthouse sobre el mismo set del repo;
- comparar LCP/INP/CLS antes/después;
- si se habilita Web Analytics, revisar P75 real antes de activar optimizaciones adicionales;
- no atribuir una mejora a Cloudflare sin comparar datos.

## 18. Definition of Done de esta iniciativa

No considerar Cloudflare «terminado» hasta que exista evidencia de:

- [ ] zona `davidportodiaz.com` activa en Cloudflare;
- [ ] inventario DNS completo y correo intacto;
- [ ] DNSSEC migrado con cadena válida;
- [ ] apex y `www` según decisión real, sin wildcard;
- [ ] GitHub Pages Enforce HTTPS y certificado de origen sanos;
- [ ] hostnames web `Proxied`;
- [ ] Full (strict);
- [ ] Universal SSL activo;
- [ ] Always Use HTTPS;
- [ ] Minimum TLS 1.2;
- [ ] TLS 1.3 ON;
- [ ] HTTP/3 ON;
- [ ] compresión verificada;
- [ ] caché de assets verificada;
- [ ] APIs explícitamente fuera de cualquier caché HTML agresiva;
- [ ] Free Managed Ruleset/WAF revisado;
- [ ] Bot Fight Mode/Block AI Bots no contradicen la estrategia de crawlers;
- [ ] CT Monitoring activado si se acepta la alerta por email;
- [ ] HSTS solo después de estabilidad y con configuración prudente;
- [ ] Turnstile real del Asistente configurado;
- [ ] route `/api/assistant*` desplegada solo cuando el Worker esté listo;
- [ ] #62 CSP revalidada con Turnstile + Pagefind;
- [ ] smoke #58/#79 sobre staging/producción correspondiente;
- [ ] Lighthouse/CWV comparados antes/después;
- [ ] rollback documentado y comprobable.

## 19. Fuentes oficiales consultadas (vigentes a 23/08/2026)

Cloudflare:

- DNS onboarding / nameservers: https://developers.cloudflare.com/dns/get-started/
- Full setup: https://developers.cloudflare.com/dns/zone-setups/full-setup/setup/
- DNSSEC: https://developers.cloudflare.com/dns/dnssec/
- DNSSEC migration: https://developers.cloudflare.com/dns/dnssec/dnssec-active-migration/
- Full (strict): https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full-strict/
- Always Use HTTPS: https://developers.cloudflare.com/ssl/edge-certificates/additional-options/always-use-https/
- Minimum TLS: https://developers.cloudflare.com/ssl/edge-certificates/additional-options/minimum-tls/
- HSTS: https://developers.cloudflare.com/ssl/edge-certificates/additional-options/http-strict-transport-security/
- CT Monitoring: https://developers.cloudflare.com/ssl/edge-certificates/additional-options/certificate-transparency-monitoring/
- HTTP/3: https://developers.cloudflare.com/speed/optimization/protocol/http3/
- 0-RTT: https://developers.cloudflare.com/speed/optimization/protocol/0-rtt-connection-resumption/
- Compression: https://developers.cloudflare.com/speed/optimization/content/compression/
- Early Hints: https://developers.cloudflare.com/cache/advanced-configuration/early-hints/
- Speed Brain: https://developers.cloudflare.com/speed/optimization/content/speed-brain/
- Rocket Loader: https://developers.cloudflare.com/speed/optimization/content/rocket-loader/
- Cache defaults: https://developers.cloudflare.com/cache/concepts/default-cache-behavior/
- Cache TTL: https://developers.cloudflare.com/cache/how-to/edge-browser-cache-ttl/
- Purge: https://developers.cloudflare.com/cache/how-to/purge-cache/
- WAF: https://developers.cloudflare.com/waf/get-started/
- Managed Rules: https://developers.cloudflare.com/waf/managed-rules/
- Bot Fight Mode: https://developers.cloudflare.com/bots/get-started/bot-fight-mode/
- Turnstile API: https://developers.cloudflare.com/turnstile/get-started/widget-management/api/
- Turnstile hostnames: https://developers.cloudflare.com/turnstile/additional-configuration/hostname-management/
- Workers routing: https://developers.cloudflare.com/workers/configuration/routing/
- Workers routes: https://developers.cloudflare.com/workers/configuration/routing/routes/
- Wrangler config: https://developers.cloudflare.com/workers/wrangler/configuration/
- Web Analytics / CWV: https://developers.cloudflare.com/web-analytics/data-metrics/core-web-vitals/

GitHub Pages:

- HTTPS: https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https
- Custom domain: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
- Troubleshooting custom domain: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/troubleshooting-custom-domains-and-github-pages

## 20. Decisión de integración

Esta PR es **documentación + runbook**, no una mutación de infraestructura.

No debe cambiar DNS ni Cloudflare automáticamente al mergear. El cambio de nameservers/DNSSEC es una operación de infraestructura con riesgo de disponibilidad y requiere ejecutar el runbook cuando se decida, verificando el estado vivo inmediatamente antes.

Cuando se ejecute:

1. usar API para settings repetibles y Workers;
2. usar dashboard/manual para los puntos con riesgo humano alto (inventario DNS, registrador, DS/DNSSEC, primer HSTS);
3. dejar evidencia de cada fase;
4. revalidar #62/#58/#79/#1 contra la infraestructura resultante.
