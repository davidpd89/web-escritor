# Cloudflare — segunda pasada final: SEO, edge headers, crawlers y observabilidad

Fecha: 2026-08-23  
Complementa: `docs/CLOUDFLARE-ZONE-CDN-SECURITY-RUNBOOK.md`  
PR owner: #92  
Ámbito: **solo Cloudflare**. No despliega, no toca `main`, no cambia DNS y no contiene secretos.

## 1. Objetivo de esta segunda pasada

La primera auditoría cubrió la migración segura de zona, DNSSEC, proxy, TLS, HTTP/3, CDN, WAF, Turnstile, Workers y rollback. Esta segunda pasada revisa productos/configuraciones menos obvios de Cloudflare con una regla estricta:

> solo entra algo si aporta una mejora concreta a descubrimiento, SEO técnico, rendimiento, seguridad, observabilidad o estabilidad del sitio actual y no duplica una autoridad ya existente.

No se recomienda contratar ni activar funciones por el mero hecho de existir.

## 2. Resumen de decisiones nuevas

| Función | Decisión | Momento | Motivo |
|---|---|---|---|
| Redirect canónico `www` → apex | **SÍ** | al activar proxy | evita doble hostname y conserva path/query |
| Response Header Transform Rules | **SÍ** | después de #62 y proxy estable | permite cabeceras HTTP reales que GitHub Pages no puede emitir |
| CSP `frame-ancestors 'none'` en header | **SÍ** | junto a headers edge | `<meta http-equiv=CSP>` no puede aplicar `frame-ancestors` |
| `X-Content-Type-Options: nosniff` | **SÍ** | headers edge | hardening de bajo riesgo |
| `Referrer-Policy: strict-origin-when-cross-origin` | **SÍ** | headers edge | política HTTP uniforme |
| Permissions Policy mínima | **SÍ, pequeña** | tras browser smoke | deshabilitar solo cámara/micrófono/geolocalización si ninguna ruta los usa |
| Crawler Hints / IndexNow | **CONDICIONAL** | cuando HTML sea cacheable + purge fiable | usa `MISS`; HTML no es cacheable por defecto, así que activarlo antes aporta poco a las páginas SEO |
| AI Crawl Control analytics | **SÍ, observación** | tras proxy | saber qué bots/IA consumen qué contenido sin bloquearlos |
| Cloudflare Managed `robots.txt` | **NO** | — | contradice el `robots.txt` editorial existente y bloquearía crawlers que hoy se permiten deliberadamente |
| Block AI Bots | **NO** | — | contradice la estrategia de descubrimiento |
| AI Labyrinth | **NO** | — | introduciría contenido-trampa y riesgo innecesario para una web que busca ser rastreable |
| Agent Readiness URL Scan | **SÍ** | post-launch/final QA | diagnóstico objetivo de descubrimiento por agentes; disponible vía dashboard/API |
| Markdown for Agents | **SOLO si ya se paga Pro/Business** | post-launch | útil para agentes, pero no justifica subir de plan por sí solo; requiere política explícita de Content Signals |
| Redirects for AI Training | **SOLO plan compatible y si se permite training** | post-launch | canonicaliza para crawlers de entrenamiento; no ayuda a Google/usuarios normales |
| Workers Logs / Observability | **SÍ** | antes de activar Workers en producción | errores e invocaciones reales; revisar PII antes en newsletter |
| Real-time logs / `wrangler tail` | **SÍ para despliegues** | smoke operativo | diagnóstico inmediato sin montar otra plataforma |
| Tiered Cache / Smart Topology | **OPCIONAL** | después de medir cache MISS | gratis y puede reducir origen, pero GitHub Pages ya es CDN; no es prioridad de lanzamiento |
| Always Online | **NO inicialmente** | — | en Free puede servir copias de Internet Archive de hasta 30 días; demasiado stale para agenda/disponibilidad/lanzamientos |
| Cache Reserve | **NO** | — | pago y orientado a proteger orígenes/egress; no resuelve un problema real aquí |
| Security Insights | **SÍ, revisar** | tras añadir zona | Cloudflare escanea configuración automáticamente; usarlo como gate operativo, no como sustituto de QA |
| Development Mode | **OFF en producción** | solo incidencias | desactiva temporalmente cache y degrada rendimiento |

## 3. Canonicalización HTTP real: `www` → apex

### Por qué sí

El sitio y sus canonical actuales usan `https://davidportodiaz.com`. Una vez Cloudflare sea autoritativo/proxy, conviene que `www.davidportodiaz.com` tenga una única respuesta permanente hacia el apex, preservando ruta y query.

Objetivo:

```text
https://www.davidportodiaz.com/cuaderno/?x=1
→ 301
https://davidportodiaz.com/cuaderno/?x=1
```

No crear una segunda versión navegable de las páginas.

### Configuración recomendada

Cloudflare → Rules → Redirect Rules → Single Redirect.

Condición conceptual:

```text
http.host eq "www.davidportodiaz.com"
```

Destino dinámico:

```text
concat("https://davidportodiaz.com", http.request.uri.path)
```

- status: `301`;
- Preserve query string: **ON**.

Debe existir un registro DNS `www` proxied para que Cloudflare pueda evaluar la regla. Antes de inventar un destino DNS, revisar el record real importado desde Spaceship/GitHub Pages. Si `www` existe únicamente para redirección edge, Cloudflare documenta el patrón de un registro proxied de placeholder; aplicarlo solo después de confirmar que no se necesita ese hostname como origen de Pages.

### QA

Comprobar al menos:

```bash
curl -I https://www.davidportodiaz.com/
curl -I 'https://www.davidportodiaz.com/cuaderno/?utm_source=test'
curl -I http://www.davidportodiaz.com/
```

Criterio:

- un único hostname indexable: apex;
- path y query preservados;
- evitar cadenas de 2–3 redirects si Cloudflare puede resolver HTTPS + canonicalización de forma limpia;
- canonical HTML final sigue apuntando a apex.

Fuente oficial: https://developers.cloudflare.com/rules/url-forwarding/examples/redirect-www-to-root/

## 4. Cabeceras HTTP reales en Cloudflare

### 4.1 Por qué #92 cambia la arquitectura de #62

#62 existe porque GitHub Pages no permite controlar cabeceras HTTP arbitrarias y por ello genera CSP/Referrer/Permissions desde HTML.

Cuando la web esté detrás del proxy Cloudflare aparece una capacidad nueva: **Response Header Transform Rules** pueden añadir o reemplazar headers en el edge.

Esto no invalida #62 antes de la migración. Sí significa que el estado final no debe seguir afirmando que `<meta>` es la única vía posible.

Regla de ownership:

- #62 conserva la política funcional CSP y su QA;
- #92 añade únicamente capacidades de header que el origen no puede aplicar;
- no mantener dos políticas completas divergentes.

### 4.2 `frame-ancestors`

Prioridad alta porque `frame-ancestors` no funciona dentro de una CSP entregada por `<meta>`.

Recomendación edge:

```http
Content-Security-Policy: frame-ancestors 'none'
```

Si el origen/otro Worker ya entrega otra cabecera CSP, **no reemplazarla**. Múltiples políticas CSP se aplican de manera acumulativa/intersectada. La regla debe coordinarse con #62 y pasar browser QA real.

Alternativa legacy complementaria si se desea compatibilidad defensiva:

```http
X-Frame-Options: DENY
```

No sustituye CSP moderna, pero no introduce funcionalidad de aplicación.

### 4.3 Headers de bajo riesgo

Una única Response Header Transform Rule puede establecer, tras smoke:

```http
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
```

Permissions Policy: empezar deliberadamente pequeña, por ejemplo solo capacidades que esta web no utiliza:

```http
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

**No bloquear** clipboard, fullscreen u otras APIs a ciegas: varias herramientas usan copiar/portapapeles y el diseño/runtime final puede necesitar otras capacidades legítimas.

### 4.4 Scope

No aplicar indiscriminadamente una nueva CSP completa a `/api/*` ni a Workers JSON.

Expresión inicial segura para los headers documentales:

```text
not starts_with(http.request.uri.path, "/api/")
```

Después comprobar con Cloudflare Trace y navegador qué respuestas reciben la regla. Cloudflare advierte que Response Header Transform Rules también pueden afectar sus propias páginas de error.

### 4.5 API

La API usa Rulesets en la fase:

```text
http_response_headers_transform
```

Procedimiento correcto:

1. listar si ya existe ruleset de esa fase;
2. editar/reemplazar acumulativamente sus reglas;
3. no crear un segundo ruleset competidor;
4. conservar export/config de la regla en documentación;
5. comprobar por `curl -I` y navegador.

Fuente oficial: https://developers.cloudflare.com/rules/transform/response-header-modification/  
API: https://developers.cloudflare.com/rules/transform/response-header-modification/create-api/

## 5. Crawler Hints / IndexNow: útil, pero no activarlo de forma cosmética

Cloudflare Crawler Hints está disponible en todos los planes y usa señales de caché para avisar a motores cuando el contenido probablemente ha cambiado. Integra IndexNow.

Esto **no garantiza ranking**. Su valor es reducir latencia entre cambio/publicación y recrawl en motores compatibles.

### Condición técnica que importa aquí

La documentación actual indica que Crawler Hints usa `CF-Cache-Status: MISS` para inferir contenido actualizado.

Pero Cloudflare no hace cache de HTML por defecto: las páginas `.html` suelen ser `DYNAMIC` mientras no exista una Cache Rule que las haga elegibles.

Conclusión específica para esta web:

> no marcar Crawler Hints como «SEO resuelto» mientras las páginas HTML no participen realmente en la caché Cloudflare.

### Orden recomendado

1. Lanzar proxy con cache estándar de assets.
2. Medir headers y comportamiento real.
3. Cuando exista una Cache Rule segura para HTML + purge post-deploy probado, confirmar que una página recién purgada produce `MISS` y luego `HIT`.
4. Entonces activar **Crawler Hints**.
5. Verificar que páginas `noindex` siguen excluidas mediante sus metas/gates.

Esto hace innecesario escribir ahora un cliente IndexNow custom: usar primero la integración mantenida por Cloudflare.

Fuentes oficiales:
- https://developers.cloudflare.com/cache/advanced-configuration/crawler-hints/
- https://developers.cloudflare.com/cache/troubleshooting/investigating-uncached-responses/

Coordinación: #77 no debe crear una implementación IndexNow paralela mientras #92 posea esta vía.

## 6. Estrategia de HTML cache sin poner en riesgo publicación

La página es estática y, en principio, el HTML puede beneficiarse del edge. Pero una regla global sin purge puede servir durante horas una portada, fecha, disponibilidad o evento antiguo.

### No hacer para el primer minuto de producción

- no `Cache Everything` global sin exclusiones;
- no cachear `/api/*`;
- no forzar TTL largo de navegador;
- no asumir que purgar Cloudflare purga navegadores.

### Candidato post-launch

Cuando #58/#79 tengan smoke/purge coordinado:

- Cache Rule solo para `GET`/`HEAD` de contenido público;
- excluir `/api/*` y cualquier ruta dinámica/Worker;
- Edge TTL conservador del plan;
- Browser TTL respetar origen;
- purge granular tras cada publicación;
- smoke de varias URLs inmediatamente después del deploy.

La regla debe derivar del universo **público**, no convertir rutas gated en publicables.

Beneficios si se demuestra correcto:

- menor TTFB desde edge;
- Crawler Hints sí puede usar `MISS` de páginas reales;
- más consistencia ante latencia del origen.

No es requisito para lanzar si complica el release.

## 7. AI Crawl Control: usar visibilidad, no bloqueo

AI Crawl Control está disponible en todos los planes y permite observar qué servicios de IA acceden a la web y qué paths solicitan.

Para este proyecto la configuración inicial correcta es:

- **monitorizar**;
- no activar `Block AI Bots`;
- no crear WAF general contra crawlers de IA;
- revisar 24 h de métricas en Free cuando exista tráfico;
- usar la pestaña Directives para comprobar que `robots.txt` responde y detectar incumplimientos.

Fuente: https://developers.cloudflare.com/ai-crawl-control/

### 7.1 Managed `robots.txt`: OFF

El repo ya tiene una política explícita:

- `OAI-SearchBot` → Allow;
- `ChatGPT-User` → Allow;
- `GPTBot` → Allow;
- `PerplexityBot` → Allow;
- `Applebot-Extended` → Allow;
- `ClaudeBot`, `Claude-SearchBot`, `Claude-User` → Allow;
- `Google-Extended` → Allow;
- sitemap + `llms.txt`/`llms-full.txt` propios.

Cloudflare Managed `robots.txt` puede anteponer reglas que bloquean varios de esos crawlers y añade una política orientada a `ai-train=no`. Activarlo hoy **contradiría la autoridad editorial versionada en Git**.

Decisión: mantener **Managed robots.txt OFF**.

Fuente: https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/

### 7.2 Content Signals

Cloudflare distingue:

- `search`: índice/resultados de búsqueda;
- `ai-input`: uso en respuestas/RAG/grounding;
- `ai-train`: entrenamiento/fine-tuning.

Para descubrimiento del sitio, `search=yes` y `ai-input=yes` son coherentes con el objetivo. `ai-train` **no es un requisito SEO** y además expresa una decisión de uso/derechos distinta.

No añadir `Content-Signal: ai-train=yes/no` desde esta PR sin decisión humana explícita. El hecho de permitir un user-agent en `robots.txt` no debe convertirse silenciosamente en una nueva declaración jurídica de Content Signals.

## 8. Agent Readiness como QA final

Cloudflare URL Scanner puede ejecutar un análisis de **Agent Readiness** con seis grupos de señales, entre ellas discoverability, content accessibility, bot access control y protocol discovery.

Esto sí encaja como comprobación final porque el repo ya trabaja `robots.txt`, sitemap, JSON-LD, `llms.txt`, navegación humana y accesibilidad.

### Dashboard

Cloudflare → Security Center / Investigate → URL Scanner → escanear la Home y revisar `Agent Readiness`.

Después muestrear:

- Home;
- `/las-manecillas-del-recuerdo/`;
- `/autor.html`;
- `/cuaderno/`;
- un artículo;
- `/herramientas/`.

No perseguir una puntuación a base de añadir estándares no aplicables: cada finding debe contrastarse con la arquitectura real.

### API

URL Scanner permite:

```text
POST /accounts/{account_id}/urlscanner/v2/scan
```

con:

```json
{
  "url": "https://davidportodiaz.com/",
  "agentReadiness": true
}
```

Usar token específico de URL Scanner, no un token global.

Fuentes:
- https://developers.cloudflare.com/security-center/investigate/url-scanner/
- https://developers.cloudflare.com/api/resources/url_scanner/subresources/scans/methods/create/

## 9. Markdown for Agents: interesante, pero no justificar un upgrade de plan

Cloudflare puede convertir HTML a `text/markdown` por content negotiation cuando un agente pide:

```http
Accept: text/markdown
```

La conversión elimina navegación/scripts/estilos, conserva estructura y JSON-LD y añade contadores de tokens.

Puede complementar `llms.txt` y `llms-full.txt`, pero:

- actualmente requiere Pro/Business/Enterprise;
- no mejora por sí sola el ranking web tradicional;
- la web ya ofrece documentos máquina propios;
- no justifica pagar un plan solo por esta función.

### Riesgo que obliga a decidir antes

Si el origen no entrega `Content-Signal`, Cloudflare documenta como default de Markdown for Agents:

```text
ai-train=yes, search=yes, ai-input=yes
```

Por ello, **no habilitar** Markdown for Agents hasta fijar explícitamente la política de Content Signals. Si algún día se activa, el edge puede entregar una política explícita mediante header para que no se adopte un default por accidente.

API del setting en planes compatibles:

```text
PATCH /zones/{zone_id}/settings/content_converter
{"value":"on"}
```

Fuente: https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/

## 10. Redirects for AI Training: no es una prioridad SEO

En planes compatibles, Cloudflare puede devolver 301 a la URL canonical únicamente a crawlers verificados de entrenamiento cuando solicitan una duplicada. No cambia la respuesta para humanos, buscadores tradicionales o AI Search agents.

El repo ya tiene canonicales y validaciones. Por tanto:

- útil solo si se termina usando un plan compatible **y** se permite training;
- no contratar/activar por SEO general;
- no sustituye redirects normales para usuarios/search bots.

Fuente: https://developers.cloudflare.com/ai-crawl-control/reference/redirects-for-ai-training/

## 11. Workers Observability — sí antes de producción

Los Workers del Asistente y newsletter son backend real. Cloudflare recomienda no desplegar Workers de producción como una caja negra.

Workers Logs está incluido también en Workers Free y registra invocaciones, errores y `console.*`.

### Asistente

Añadir a la configuración Wrangler de producción cuando se materialice:

```jsonc
{
  "observability": {
    "enabled": true,
    "head_sampling_rate": 1
  }
}
```

Para el volumen inicial del sitio puede usarse 100 % durante la ventana de lanzamiento y reducir después si el tráfico/volumen lo aconseja.

No loggear:

- prompt/contexto completo;
- token Turnstile;
- IP explícita añadida manualmente;
- secretos/bindings;
- respuestas completas si contienen datos no necesarios.

El Worker del Asistente actual usa errores reducidos (`safeError`) en los puntos revisados, lo que es compatible con esta estrategia.

### Newsletter: gate previo de privacidad

El head actual de #55 todavía contiene:

```js
console.error(`Brevo DOI error ${brevoRes.status}:`, brevoBodyText.slice(0, 500));
```

Una respuesta de upstream podría contener datos que no queremos persistir en Workers Logs.

Antes de habilitar persistencia completa en newsletter:

- #55 debe dejar de registrar el body raw de Brevo;
- registrar solo status/code seguro y un identificador técnico no personal si hace falta;
- no registrar email;
- después habilitar observabilidad.

Esto se documenta también en #55; #92 no modifica su lógica.

### Smoke y diagnóstico

Durante despliegue:

```bash
npx wrangler tail <worker>
```

Real-time logs permite comprobar errores inmediatamente. Workers Logs persiste después para incidentes intermitentes.

Fuentes:
- https://developers.cloudflare.com/workers/observability/logs/workers-logs/
- https://developers.cloudflare.com/workers/observability/logs/real-time-logs/

## 12. Web Analytics / RUM: corrección importante para audiencia española

Cloudflare Web Analytics sí puede aportar LCP/INP/CLS reales y localizar elementos que dañan los Core Web Vitals.

Pero no debe venderse como «gratis y perfecto para nuestra audiencia» sin matiz.

En sitios proxied, Cloudflare ofrece distintos modos de setup y documenta expresamente una opción:

> Enable, excluding visitor data in the EU

Dado que la audiencia principal está en España, una configuración que excluya UE puede dejar fuera una parte material de la muestra que justamente queremos medir.

Decisión:

1. no activar un tercer analytics por inercia;
2. si #63 necesita RUM, decidir conscientemente el modo de instalación y revisar privacidad/CSP;
3. usarlo para CWV/diagnóstico, no duplicar eventos de negocio de GoatCounter/Metricool;
4. confirmar qué tráfico UE entra realmente en el modo elegido antes de basar decisiones de diseño en sus datos.

Fuente: https://developers.cloudflare.com/web-analytics/get-started/  
CWV: https://developers.cloudflare.com/web-analytics/data-metrics/core-web-vitals/

## 13. Tiered Cache: disponible, pero no P0

Tiered Cache y Smart Topology están disponibles en todos los planes. Reducen llamadas al origen mediante una jerarquía de caches.

Para un origen tradicional puede ser muy valioso. Aquí el origen es GitHub Pages, que ya se sirve mediante infraestructura CDN, y Cloudflare solo cacheará inicialmente assets estáticos.

Por tanto:

- no bloquear lanzamiento por Tiered Cache;
- medir Cache Analytics tras algunos días;
- si hay tasa de `MISS`/fetch a origen apreciable, activar Tiered Cache + Smart Topology;
- comparar TTFB/cache-hit antes/después;
- si la diferencia es irrelevante, no añadir más capas operativas.

API disponible:

```text
PATCH /zones/{zone_id}/argo/tiered_caching
{"value":"on"}
```

Smart Topology tiene endpoint propio de Cache API.

Fuente: https://developers.cloudflare.com/cache/how-to/tiered-cache/

## 14. Always Online: OFF inicialmente

Always Online puede usar Internet Archive cuando Cloudflare no logra conectar con el origen. En Free, la frecuencia de archivo documentada es cada 30 días.

Una copia de hasta 30 días puede mostrar:

- un evento ya celebrado como próximo;
- disponibilidad antigua del libro;
- portada/copy anterior al lanzamiento;
- información editorial que ya se corrigió.

Además muestra un banner de versión archivada.

GitHub Pages tiene alta disponibilidad y el repo ya cuenta con PWA/offline para otro tipo de fallo.

Decisión: **Always Online OFF inicialmente**. Revisarlo solo si hay evidencia real de caídas del origen suficientemente frecuentes para compensar la posibilidad de contenido stale.

Fuente: https://developers.cloudflare.com/cache/how-to/always-online/

## 15. Cache Reserve: NO

Cache Reserve es almacenamiento persistente sobre R2 y requiere producto de pago/uso. Su objetivo principal es reducir egress y proteger un origen de tráfico repetido.

GitHub Pages no nos está generando una factura de egress que necesitemos resolver y los assets de esta web son pequeños.

Decisión: no contratarlo.

Fuente: https://developers.cloudflare.com/cache/advanced-configuration/cache-reserve/

## 16. Security Insights como gate operativo

Una vez la zona esté activa, Cloudflare Security Insights revisa DNS, SSL/TLS, WAF y otras configuraciones y genera findings. Los planes reciben escaneos automáticos.

Usarlo así:

1. esperar al primer scan después de la migración;
2. revisar findings críticos/altos;
3. no aceptar automáticamente toda recomendación: contrastarla con GitHub Pages/Workers;
4. guardar en el checklist de release qué findings quedan aceptados y por qué;
5. repetir tras HSTS/WAF/rules significativos.

No sustituye #58/#62/#66/#79 ni Lighthouse.

Fuentes:
- https://developers.cloudflare.com/security-center/
- https://developers.cloudflare.com/security-center/get-started/

## 17. Settings que conviene dejar expresamente OFF/no tocar

### Development Mode

OFF en producción. Bypassea cache temporalmente durante 3 h; usar solo para diagnóstico urgente y apagar/esperar expiración antes de medir rendimiento.

### Browser Integrity Check

No convertirlo en requisito de lanzamiento. Puede desafiar clientes con user agents no estándar y el proyecto tiene interés explícito en crawlers/agentes. WAF administrado + DDoS + Turnstile/rate limiting cubren mejor las superficies de riesgo reales.

### AI Labyrinth

OFF. Está pensado para crawlers de IA que no respetan reglas y los conduce por contenido generado. Para un sitio cuyo objetivo es descubrimiento/citación, añadir un laberinto de contenido artificial en edge aporta más riesgo de gobernanza que beneficio.

### Managed robots.txt

OFF por conflicto directo con el fichero versionado.

### Email Obfuscation / HTML rewrites

OFF salvo evidencia de spam/problema concreto; no queremos que Cloudflare reescriba HTML que tiene QA, CSP y microtipografía propios.

### Automatic HTTPS Rewrites

No es necesario si el HTML final no contiene mixed-content y HTTPS ya es obligatorio. Corregir URLs en origen es preferible a reescribirlas en edge.

## 18. Prioridades finales para publicar

### P0 — hacer como parte de la migración Cloudflare

1. DNS/DNSSEC seguro del runbook principal.
2. Proxy + Full (strict) + HTTPS + TLS 1.2/1.3 + HTTP/3.
3. `www` → apex 301 preservando path/query.
4. Free Managed WAF/DDoS verificados, sin Bot Fight/AI blocks globales.
5. Response Header Transform Rule mínima, coordinada con #62:
   - CSP `frame-ancestors 'none'`;
   - `X-Content-Type-Options: nosniff`;
   - `Referrer-Policy: strict-origin-when-cross-origin`;
   - Permissions Policy mínima solo tras smoke.
6. Turnstile/Workers según sus owners.
7. Workers Observability para Asistente; newsletter solo después de sanitizar logs.
8. QA completo HTTP/DNS/cache/CSP/Worker.

### P1 — inmediatamente después de estabilizar producción

1. Security Insights review.
2. AI Crawl Control **analytics**, sin bloquear.
3. Agent Readiness scan de rutas representativas.
4. Cache Analytics para saber si necesitamos algo más.
5. RUM/CWV solo si #63 decide que la cobertura sirve a nuestra audiencia.

### P2 — solo si la evidencia lo justifica

1. cache HTML + purge post-deploy;
2. entonces Crawler Hints/IndexNow;
3. Tiered Cache/Smart Topology si hay misses/origin fetch relevantes;
4. Markdown for Agents si ya existe plan Pro/Business y Content Signals está decidido;
5. Redirects for AI Training solo si plan/política lo hacen pertinente.

### No hacer

- Cache Reserve;
- Always Online inicial;
- Managed robots.txt;
- Block AI Bots;
- AI Labyrinth;
- Rocket Loader;
- HSTS preload inicial;
- Browser TTL global largo;
- Cache Everything sin purge/exclusiones;
- Cloudflare image transformations duplicando el pipeline del repo;
- upgrade de plan solo por funciones AI/Markdown.

## 19. Definition of Done ampliada para #92

Cloudflare no se considera «terminado» porque el dashboard muestre la zona como Active. Debe demostrarse:

- NS/DS correctos y DNSSEC válido;
- apex y `www` tienen comportamiento canónico estable;
- una URL `www` profunda conserva path/query en 301;
- TLS Full (strict) y HTTPS sin loops;
- HTTP/3 disponible;
- assets estáticos muestran cache Cloudflare según corresponda;
- HTML no se considera cacheado si no se ha aprobado explícitamente esa fase;
- `/api/assistant*` no es cacheado;
- CSP funcional + `frame-ancestors` header pasan browser QA;
- no hay challenge/bot policy que bloquee Google/Bing/AI Search/usuarios legítimos;
- `robots.txt` servido sigue siendo el versionado por el proyecto, no uno reescrito por Managed robots;
- sitemap/llms/canonicals continúan accesibles;
- Worker logs no contienen secretos ni PII intencional;
- Security Insights revisado;
- Agent Readiness ejecutado como diagnóstico, no como score vanity;
- cualquier función P2 queda marcada como OFF/pendiente por evidencia, no como olvido.

## 20. Fuentes oficiales adicionales

- Crawler Hints: https://developers.cloudflare.com/cache/advanced-configuration/crawler-hints/
- Cache responses / DYNAMIC vs MISS: https://developers.cloudflare.com/cache/troubleshooting/investigating-uncached-responses/
- Redirect www → apex: https://developers.cloudflare.com/rules/url-forwarding/examples/redirect-www-to-root/
- Transform Rules: https://developers.cloudflare.com/rules/transform/
- Response Header Transform Rules: https://developers.cloudflare.com/rules/transform/response-header-modification/
- AI Crawl Control: https://developers.cloudflare.com/ai-crawl-control/
- Managed robots.txt: https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/
- Agent Readiness / URL Scanner: https://developers.cloudflare.com/security-center/investigate/url-scanner/
- Markdown for Agents: https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/
- Redirects for AI Training: https://developers.cloudflare.com/ai-crawl-control/reference/redirects-for-ai-training/
- Workers Logs: https://developers.cloudflare.com/workers/observability/logs/workers-logs/
- Real-time logs: https://developers.cloudflare.com/workers/observability/logs/real-time-logs/
- Web Analytics setup: https://developers.cloudflare.com/web-analytics/get-started/
- Core Web Vitals: https://developers.cloudflare.com/web-analytics/data-metrics/core-web-vitals/
- Tiered Cache: https://developers.cloudflare.com/cache/how-to/tiered-cache/
- Always Online: https://developers.cloudflare.com/cache/how-to/always-online/
- Cache Reserve: https://developers.cloudflare.com/cache/advanced-configuration/cache-reserve/
- Security Center: https://developers.cloudflare.com/security-center/

Todas las disponibilidades/settings deben volver a consultarse justo antes de ejecutar la migración: Cloudflare cambia con frecuencia productos, defaults y límites por plan.