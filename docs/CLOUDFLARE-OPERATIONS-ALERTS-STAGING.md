# Cloudflare — cierre operativo: alertas, staging, Turnstile y certificados

Fecha: 2026-08-23  
PR owner: #92  
Complementa:
- `docs/CLOUDFLARE-ZONE-CDN-SECURITY-RUNBOOK.md`
- `docs/CLOUDFLARE-FINAL-OPTIMIZATION-ADDENDUM.md`

Ámbito: solo Cloudflare. Documento operativo; no cambia DNS, `main`, Workers live ni secretos.

## 1. Por qué existe esta tercera pasada

La web está ya en fase de estabilización. Esta pasada no busca más productos que activar, sino cubrir fallos de operación que pueden hacer que una configuración técnicamente buena falle en producción sin que nadie se entere.

Hallazgos nuevos que sí merecen owner:

1. Cloudflare Notifications ofrece alertas útiles incluso en Free y la primera auditoría no las convirtió en un checklist concreto.
2. El staging real del repo es `https://david-porto-preview.davidpd89.workers.dev` y el workflow `staging-smoke-test.yml` lo consulta diariamente. Cloudflare Workers ofrece ahora Access directamente sobre Workers y Preview URLs; es una forma limpia de evitar exposición pública accidental de preproducción.
3. Turnstile tiene analytics y buenas prácticas de separación staging/producción que deben formar parte del go-live del Asistente.
4. CAA puede endurecer emisión de certificados, pero con GitHub Pages como origen es fácil romper HTTPS. No debe añadirse “por seguridad” sin revisar ambas cadenas de certificados.
5. Si se activa cache HTML, la cache key de query strings debe decidirse con cuidado para no fragmentar cache ni romper herramientas; en Free no podemos excluir selectivamente parámetros concretos del cache key.

## 2. Cloudflare Notifications — P0 operativo

Cloudflare Notifications está disponible en todos los planes. En Free, el mecanismo disponible de forma general es email; webhooks requieren al menos Professional en la cuenta y PagerDuty Business o superior, salvo herencia por otra zona de mayor plan.

No necesitamos Slack, PagerDuty ni otra plataforma para obtener valor.

### 2.1 Alertas que SÍ deben configurarse si aparecen en `available_alerts`

Antes de crear nada por API, consultar la cuenta real:

```bash
curl "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/alerting/v3/available_alerts" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

No asumir que un tipo está disponible solo porque exista en documentación. El endpoint devuelve los tipos permitidos para esa cuenta/plan.

#### A. Universal SSL Alert — P0

Tipo API documentado:

```text
universal_ssl_event_type
```

Por qué importa aquí:

- el visitante verá el certificado edge de Cloudflare;
- el origen GitHub Pages seguirá teniendo su propio certificado;
- una incidencia de emisión/renovación edge puede dejar HTTPS degradado aunque el repositorio esté perfecto.

Cloudflare incluye Universal SSL Alert en todos los planes y notifica validación, emisión, renovación y expiración.

Acción: configurar email al propietario de la cuenta una vez la zona esté activa.

Fuente oficial:
https://developers.cloudflare.com/ssl/edge-certificates/universal-ssl/alerts/

#### B. HTTP DDoS Attack Alert — P0

Cloudflare documenta este aviso para clientes WAF/CDN en todos los planes. Se dispara cuando Cloudflare mitiga un ataque HTTP por encima del umbral estándar del producto.

No hay que responder bloqueando más tráfico automáticamente. El valor es saber que ha ocurrido y revisar Security Analytics/Eventos.

Fuente:
https://developers.cloudflare.com/ddos-protection/reference/alerts/

#### C. Security Insights — P0/P1

`security_insights_alert` aparece entre los tipos de Notification API y Cloudflare documenta Security Insights notifications en todos los planes.

Uso recomendado:

- activar solo después de que la zona esté configurada y el primer scan haya sido revisado;
- alertar sobre findings que realmente hayamos decidido vigilar;
- no “autoarreglar” cualquier finding por API.

Fuente:
https://developers.cloudflare.com/notifications/notification-available/

#### D. Workers observability alert — si `available_alerts` lo ofrece

Cloudflare documenta el payload `workers_observability_alert`, pero disponibilidad/configuración puede variar. Por eso el gate correcto es comprobar `available_alerts` en la cuenta y solo crear política si aparece.

Para el Asistente y newsletter, el orden correcto es:

1. sanitizar logs —especialmente #55—;
2. activar Workers Logs/observability;
3. definir qué condición representa fallo real;
4. si la cuenta ofrece `workers_observability_alert`, crear el aviso.

No añadir un servicio externo de monitoring solo para obtener esta capacidad antes de comprobar lo que Cloudflare ya ofrece.

Fuentes:
- https://developers.cloudflare.com/workers/observability/
- https://developers.cloudflare.com/notifications/reference/webhook-payload-schema/

### 2.2 Alertas que NO debemos vender como disponibles en Free

Cloudflare distingue claramente varios tipos de pago:

- `Security Events Alert` de WAF → Business/Enterprise;
- Advanced Security Events → Enterprise;
- Origin Error Rate / Advanced Error Rate → Enterprise;
- Health Checks status → Professional o superior.

No subir de plan solo para tener estas alertas. GitHub Actions + smoke de staging/producción + Workers Logs cubren el riesgo real de este proyecto con menos coste.

### 2.3 Notification History

Cloudflare mantiene historial de Notifications accesible por API. En Free/Pro/Business el histórico documentado es de 30 días.

```bash
curl "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/alerting/v3/history?page=1&per_page=25" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

Útil tras un incidente para saber si Cloudflare avisó realmente y cuándo.

Fuente:
https://developers.cloudflare.com/notifications/notification-history/

### 2.4 Creación por API

Endpoint oficial:

```text
POST /accounts/{account_id}/alerting/v3/policies
```

Permiso mínimo documentado: `Notifications Write` o `Account Settings Write`. Preferir un token específico con `Notifications Write`, no Global API Key.

Ejemplo conceptual —no ejecutar hasta listar tipos disponibles—:

```bash
curl "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/alerting/v3/policies" \
  -X POST \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "alert_type": "universal_ssl_event_type",
    "enabled": true,
    "name": "davidportodiaz.com — Universal SSL",
    "mechanisms": {
      "email": [{"id": "REPLACE_WITH_ACCOUNT_EMAIL"}]
    }
  }'
```

No guardar el email operativo en documentación máquina si no hace falta; al ejecutar se obtiene de la cuenta/autorización real.

API:
https://developers.cloudflare.com/api/resources/alerting/subresources/policies/methods/create/

## 3. Proteger staging con Cloudflare Access

### 3.1 Estado real del repo

El workflow actual:

`.github/workflows/staging-smoke-test.yml`

usa:

```text
STAGING_BASE_URL=https://david-porto-preview.davidpd89.workers.dev
```

Es una superficie explícita de preproducción y se consulta mediante un workflow diario.

La URL puede contener antes que producción:

- diseño aún no aprobado;
- copy o assets que todavía cambian;
- funciones en staging;
- configuraciones que no queremos que un crawler confunda con producción.

Aunque `public-dist` y gates excluyan rutas privadas, “URL difícil de adivinar” no es control de acceso.

### 3.2 Capacidad nueva y relevante de Cloudflare

Desde agosto de 2026 Cloudflare permite colocar **Access directamente sobre un Worker o sobre sus Preview URLs**. También puede proteger todos los previews de Workers de una cuenta.

Fuentes:
- https://developers.cloudflare.com/workers/configuration/cloudflare-access/
- https://developers.cloudflare.com/workers/versions-and-deployments/preview-urls/

Cloudflare Zero Trust Free está orientado a equipos de menos de 50 usuarios y mantiene límite de 50 usuarios, suficiente de sobra para este staging.

### 3.3 Recomendación específica

**P1 antes del release final:** proteger el Worker de staging `david-porto-preview` con Access, pero **no** aplicar Access al Worker público del Asistente ni al dominio de producción.

Preferencia:

- Access sobre el staging Worker/hostname;
- Allow solo al email del propietario/revisores necesarios;
- mantener producción fuera de esa aplicación;
- no activar “Protect all Workers / All traffic” globalmente porque newsletter y Asistente deben seguir siendo públicos.

Si se desea un deny-by-default futuro, usar únicamente “previews only” con bypass explícito para Workers públicos; no hacerlo durante el lanzamiento sin pruebas.

### 3.4 El smoke programado debe seguir funcionando

Si Access protege staging, el workflow actual recibirá 403/login. No convertir la seguridad en un CI rojo permanente.

Dos opciones válidas:

**Opción A — Service Token para CI (preferida si Access se integra antes del lanzamiento):**

- crear Service Token de Access solo para staging;
- guardarlo como GitHub Actions Secrets, nunca en repo;
- la política de Access permite `Service Auth` para ese token;
- `tests/test-staging-smoke.mjs`/workflow envían:
  - `CF-Access-Client-Id`
  - `CF-Access-Client-Secret`
- la prueba humana sigue usando login normal.

**Opción B — dejar staging público hasta terminar #58/#79 y protegerlo inmediatamente después:**

Solo aceptable si:

- staging mantiene `noindex`/cabeceras adecuadas;
- no contiene contenido privado;
- existe fecha/owner explícito para activar Access.

No crear un bypass por user-agent o IP de GitHub Actions: sería frágil y más fácil de saltar.

### 3.5 Preview URLs de otros Workers

Cloudflare documenta que Preview URLs están públicas cuando están habilitadas. Para Workers que solo necesitan producción y no requieren previews compartibles:

```jsonc
{
  "preview_urls": false
}
```

No apagar previews a ciegas en todos los Workers: pueden ser útiles para #55/#91/Asistente. Decidir por Worker.

Para el Asistente, si se usan previews durante QA, preferir Access `Previews only` en lugar de ocultarlos por una URL aleatoria.

## 4. Turnstile — go-live con analytics y separación de entornos

El Worker actual del Asistente ya hace lo importante correctamente: llama a Siteverify server-side, verifica `success`, `action` y hostname, y falla cerrado ante error.

Eso significa que no necesitamos rediseñar Turnstile; solo completar operación.

### 4.1 Widget separado producción/staging

Cloudflare recomienda separar entornos. Crear widgets distintos:

- `davidportodiaz.com — assistant prod`
- `staging — assistant`

Motivos:

- hostnames distintos;
- analytics no mezcladas;
- rotar una secret sin romper otro entorno;
- detectar falsos positivos reales de producción.

No reutilizar la secret de producción en GitHub Actions o staging.

Fuente:
https://developers.cloudflare.com/turnstile/get-started/

### 4.2 Managed mode

Usar **Managed** salvo evidencia contraria. Cloudflare lo recomienda y decide cuándo requiere interacción. Invisible no mejora automáticamente UX si empeora diagnóstico/compatibilidad.

Fuente:
https://developers.cloudflare.com/turnstile/

### 4.3 Analytics post-launch

Revisar durante la primera semana:

- challenges issued;
- solved/unsolved;
- likely human/bot;
- interactive vs non-interactive solve rate;
- top hostname;
- browser/OS;
- anomalías por país/ASN/user agent.

No bloquear países/ASNs porque una gráfica tenga más fallos. Primero confirmar abuso real.

Un solve no sustituye Siteverify; el Worker actual ya lo valida.

Fuentes:
- https://developers.cloudflare.com/turnstile/turnstile-analytics/
- https://developers.cloudflare.com/turnstile/turnstile-analytics/challenge-outcomes/

## 5. CAA — NO añadir registros manuales en esta fase salvo que ya existan

CAA puede restringir qué autoridades certificadoras pueden emitir certificados. Es útil en organizaciones con política de PKI, pero aquí hay **dos cadenas de certificados públicas** que debemos conservar:

1. Cloudflare Universal SSL para visitante → edge;
2. GitHub Pages/Let's Encrypt para Cloudflare → origen cuando usamos Full (strict).

GitHub documenta que, si existen CAA, al menos debe permitirse:

```text
letsencrypt.org
```

Cloudflare Universal SSL puede usar distintas CAs. Cloudflare además añade CAA automáticamente cuando Universal SSL está activo **si ya existen CAA en la zona**, para mantener su capacidad de emitir certificados.

Decisión:

- si actualmente **no hay CAA**, no añadirlos ahora por una ganancia marginal justo antes del lanzamiento;
- si al importar DNS ya hay CAA, **no borrarlos**: auditarlos y comprobar que permiten Let's Encrypt para GitHub Pages y los issuers que Cloudflare necesita;
- después de estabilizar, se puede decidir una política CAA explícita con test de renovación;
- CT Monitoring sí sigue recomendado porque aporta visibilidad con menos riesgo de romper emisión.

Fuentes:
- https://developers.cloudflare.com/ssl/edge-certificates/caa-records/
- https://developers.cloudflare.com/ssl/reference/certificate-authorities/
- https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/troubleshooting-custom-domains-and-github-pages

## 6. Cache HTML y query strings — evitar una optimización peligrosa

El addendum anterior deja cache HTML como P2 después de purge fiable. Esta tercera pasada añade una condición importante.

Cloudflare usa el query string en el cache key estándar. Si cacheamos HTML, URLs como:

```text
/cuaderno/?utm_source=instagram
/cuaderno/?utm_source=newsletter
```

pueden crear entradas distintas aunque el HTML servido sea idéntico.

En Free existe la opción **Ignore Query String**, pero la documentación actual no ofrece en Free la granularidad de “ignora solo `utm_*` pero conserva otros parámetros”; selección `include/exclude` por parámetro es Enterprise.

Por tanto:

- **NO** activar `Ignore Query String` global sobre todo HTML sin revisar herramientas/rutas que puedan depender de query params en cliente;
- no pagar Enterprise solo para resolver UTM cache fragmentation;
- primero medir si existe fragmentación material en Cache Analytics;
- si no existe, mantener cache key estándar;
- si existe y el HTML realmente no cambia por query string en un scope concreto, aplicar `Ignore Query String` solo a ese scope validado;
- nunca aplicar a `/api/*`.

Esto evita sacrificar comportamiento correcto por perseguir cache-hit ratio.

Fuentes:
- https://developers.cloudflare.com/cache/how-to/cache-keys/
- https://developers.cloudflare.com/cache/how-to/cache-rules/settings/

## 7. Worker metrics y traces — usar lo nativo antes que Sentry

Workers ya ofrece:

- requests;
- errores por outcome;
- CPU/wall time;
- logs históricos;
- real-time logs;
- traces automáticos de fetch/bindings/handler.

Cloudflare recomienda observabilidad antes de producción.

Para este proyecto:

### Asistente

- logs: 100 % en ventana inicial si volumen bajo;
- traces: opcionales, muestreo pequeño si necesitamos localizar latencia entre AI Search/Workers AI/D1;
- no exportar a Sentry/Honeycomb/Grafana salvo que exista un problema real que no podamos diagnosticar con Cloudflare.

### Newsletter

- logs solo tras sanitizar #55;
- tracing no aporta suficiente valor para DOI de bajo volumen inicialmente.

Cloudflare indica que tracing cambia de modelo de coste a partir del 1/10/2026; no convertirlo en una dependencia permanente sin revisar uso/coste en esa fecha.

Fuentes:
- https://developers.cloudflare.com/workers/observability/
- https://developers.cloudflare.com/workers/observability/traces/
- https://developers.cloudflare.com/workers/observability/errors/

## 8. Budget alerts — solo si activamos productos de pago

Si la cuenta permanece en Free, no hay gasto que vigilar por estas funciones.

Si posteriormente se activa Workers Paid, R2, Images u otro producto usage-based, crear un Budget Alert bajo desde el primer día. Cloudflare procesa el uso con retraso diario, así que es control de coste, no circuit breaker en tiempo real.

No subir de plan para obtener esta alerta.

Fuente:
https://developers.cloudflare.com/billing/understand/usage-based-billing/

## 9. Lo revisado y descartado en esta pasada

### Cloudflare Access sobre producción pública

NO. El sitio, newsletter y Asistente deben ser accesibles públicamente. Access solo tiene sentido para staging/previews/admin futuro.

### Protect all Workers — All traffic

NO durante lanzamiento. Puede cerrar accidentalmente APIs públicas. Si algún día se usa la política global, debe haber bypass/allow explícito de los Workers públicos y pruebas.

### Health Checks de pago

NO contratar Professional solo para monitorizar GitHub Pages. El smoke de GitHub Actions y Cloudflare/GitHub disponibilidad ya cubren este sitio de forma proporcionada.

### Sentry/OTel externo

NO inicialmente. Cloudflare Logs/Metrics/Traces son suficientes para el volumen/arquitectura actual.

### WAF Security Events email en Free

No existe el alert estándar en Free según documentación actual; Security Events Alert es Business/Enterprise. No inventar una capacidad.

### CAA manual nuevo

NO prelaunch salvo CAA existente que deba preservarse/auditarse.

### Cache key complejo

NO. Granularidad avanzada de query params es Enterprise. No justificar upgrade.

## 10. Checklist operativo final de Cloudflare

### Antes de activar proxy

- [ ] `available_alerts` consultado por API.
- [ ] DNS/DS revalidado según runbook principal.
- [ ] CAA actual inventariado; si existe, compatibilidad GitHub + Cloudflare verificada.
- [ ] staging/previews inventariados.
- [ ] decisión Access staging tomada.
- [ ] #55 logs sanitizados antes de Workers Logs persistentes de newsletter.

### En la ventana de migración

- [ ] Universal SSL Alert creada si disponible.
- [ ] HTTP DDoS Attack Alert creada si disponible.
- [ ] Security Insights notification preparada/revisada cuando la zona genere findings.
- [ ] proxy/TLS/WAF/headers/redirects del runbook principal verificados.
- [ ] ningún Worker público cerrado por Access accidentalmente.

### Antes de habilitar Asistente IA

- [ ] Turnstile prod separado de staging.
- [ ] hostname/action correctos.
- [ ] Siteverify real pasa.
- [ ] Workers Logs activos sin prompt/context/token/IP añadidos a logs.
- [ ] Worker error metrics revisables.
- [ ] `workers_observability_alert` creado solo si la cuenta lo devuelve en `available_alerts`.

### Staging

- [ ] `david-porto-preview.davidpd89.workers.dev` no se considera secreto por URL.
- [ ] Access activado o excepción pública temporal documentada.
- [ ] si hay Access, smoke de GitHub Actions usa Service Token almacenado en Secrets.
- [ ] no hay bypass por user-agent/IP frágil.

### Primera semana

- [ ] Turnstile solve/failure rates revisadas.
- [ ] Security Analytics revisada con tráfico real.
- [ ] Notifications History comprobado si hubo incidencia.
- [ ] Worker outcomes/errores/latencias revisados.
- [ ] Cache Analytics revisada antes de cualquier nueva cache rule.
- [ ] no activar productos descartados por “optimizar” sin evidencia.

## 11. Fuentes oficiales

- Notifications: https://developers.cloudflare.com/notifications/
- Available notifications: https://developers.cloudflare.com/notifications/notification-available/
- Notification API: https://developers.cloudflare.com/api/resources/alerting/
- Universal SSL alerts: https://developers.cloudflare.com/ssl/edge-certificates/universal-ssl/alerts/
- DDoS alerts: https://developers.cloudflare.com/ddos-protection/reference/alerts/
- Notification history: https://developers.cloudflare.com/notifications/notification-history/
- Workers Access: https://developers.cloudflare.com/workers/configuration/cloudflare-access/
- Preview URLs: https://developers.cloudflare.com/workers/versions-and-deployments/preview-urls/
- Turnstile: https://developers.cloudflare.com/turnstile/
- Turnstile analytics: https://developers.cloudflare.com/turnstile/turnstile-analytics/
- Turnstile outcomes: https://developers.cloudflare.com/turnstile/turnstile-analytics/challenge-outcomes/
- CAA: https://developers.cloudflare.com/ssl/edge-certificates/caa-records/
- Cloudflare certificate authorities: https://developers.cloudflare.com/ssl/reference/certificate-authorities/
- Workers Observability: https://developers.cloudflare.com/workers/observability/
- Workers errors: https://developers.cloudflare.com/workers/observability/errors/
- Workers traces: https://developers.cloudflare.com/workers/observability/traces/
- Cache keys: https://developers.cloudflare.com/cache/how-to/cache-keys/
- Cache Rules settings: https://developers.cloudflare.com/cache/how-to/cache-rules/settings/
- GitHub Pages CAA requirement: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/troubleshooting-custom-domains-and-github-pages

## 12. Conclusión

Después de tres pasadas, la arquitectura recomendada no necesita más productos Cloudflare para ser sólida.

Lo adicional que sí merece ejecución es pequeño y concreto:

- alertas gratuitas que convierten fallos silenciosos en avisos;
- staging/previews protegidos con Access sin cerrar producción;
- Turnstile operado con separación prod/staging y analytics;
- CAA tratado como riesgo de compatibilidad, no como checkbox de seguridad;
- cache HTML/query strings solo después de medir;
- observabilidad nativa antes que añadir otra plataforma.

Cualquier función Cloudflare adicional debe entrar ya por evidencia post-launch, no por catálogo.