# M.4 · Monitorización externa independiente de disponibilidad/TLS/DNS

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `CONDITIONAL`.

## Veredicto

#135 empezó viendo UptimeRobot como una implementación sencilla, pero terminó afinando la decisión: **un monitor externo puede aportar valor, pero solo si se desea independencia respecto a GitHub Actions/Cloudflare y existe un canal operativo para recibir/actuar sobre alertas**.

Por tanto M.4 no es una deuda técnica obligatoria ni requiere SDK en la web.

## Hipótesis original

La idea inicial proponía:

> monitorización de expiración de certificado/DNS fuera de Cloudflare, como alerta independiente por si el propio panel de Cloudflare fallara.

El objetivo era detectar indisponibilidad fuera de la misma capa que sirve DNS/CDN.

## Evolución en #135

### Revisión inicial

La revisión consideró útil un monitor HTTP/TLS/DNS independiente, de coste bajo.

### Matriz intermedia → `IMPLEMENTAR`

La matriz llegó a proponer:

> UptimeRobot Free como monitor externo independiente (home + SSL/domain); alta requiere confirmación email.

### Revalidación independiente → rebaja práctica

La revalidación posterior revisó UptimeRobot Free y confirmó:

- hasta 50 monitores;
- intervalo de 5 minutos en Free;
- uso comercial permitido;
- sin tarjeta.

Pero corrigió la prioridad:

> primero es preferible un cron read-only que reutilice el smoke de producción; añadir UptimeRobot solo si se quiere independencia respecto a GitHub Actions.

### Autoridad final → `CONDITIONAL`

La autoridad final consolidó:

> monitor externo independiente como UptimeRobot puede ser útil; 5 min/free basta para este sitio, pero requiere una cuenta más.

## Qué problema resuelve realmente

Un monitor externo añade valor cuando detecta fallos que el propio pipeline no ve:

- sitio inaccesible entre despliegues;
- expiración/rotura de TLS;
- resolución DNS inesperada;
- respuesta HTTP 5xx/timeout;
- redirect roto;
- dominio caído aunque GitHub esté sano.

No sustituye:

- tests de PR;
- smoke post-deploy;
- auditoría de cabeceras M.1/M.3;
- Search Console;
- observabilidad de APIs específicas.

## Orden recomendado

1. reutilizar el smoke público existente en un cron read-only;
2. comprobar que alerta de forma fiable;
3. decidir si se necesita independencia de GitHub Actions;
4. solo entonces abrir cuenta/monitor externo.

## Configuración mínima si se activa

Monitores posibles:

```text
https://davidportodiaz.com/
HTTPS/TLS certificate
DNS/domain expiry only if the provider supports it meaningfully
```

No hace falta monitorizar cada página del sitio.

## Alertas

La feature solo existe de verdad si:

- hay destinatario válido;
- la alerta llega;
- existe una ruta de actuación;
- se prueba al menos una vez con incidente controlado o condición simulada.

`CONFIGURED_LIVE` no puede inferirse desde Git.

## Privacidad/performance

Preferir monitor server-side externo sin insertar JavaScript/SDK en las páginas.

M.4 no justifica:

- otro tracker cliente;
- cookies;
- beacon de RUM;
- panel público de uptime;
- status page si no hay necesidad.

## Riesgos

- fatiga de alertas;
- falso positivo por intervalo demasiado agresivo;
- cuenta externa olvidada;
- dependencia de un único email;
- monitor que solo prueba `/` y se vende como cobertura total;
- duplicar alertas de GitHub/Cloudflare sin utilidad.

## Trigger de implementación

```text
scheduled production smoke exists
AND owner wants independent monitoring
AND alert destination is operational
AND maintenance/account ownership is clear
```

## Pasadas posteriores

La revalidación independiente es el añadido más importante: mantiene M.4, pero rebaja la idea de `IMPLEMENTAR UptimeRobot` a una capacidad `CONDITIONAL` y recomienda primero cron read-only con tooling existente.

## Trazabilidad

- backlog original M.4;
- revisión 108/108;
- matriz `IMPLEMENTAR`;
- autoridad final `CONDITIONAL`;
- revalidación independiente y comprobación de UptimeRobot Free.

## Recomendación

No añadir SDK ni cuenta por checklist. Primero programar/reutilizar el smoke de producción; añadir un monitor externo solo si se quiere una segunda capa realmente independiente.