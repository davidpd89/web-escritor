# M.1 · Auditoría live de cabeceras HTTP de seguridad

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `IMPLEMENT_NOW`.

## Veredicto

#135 consideró M.1 una de las mejoras de mayor valor/riesgo: observar las respuestas públicas reales y auditar CSP efectiva, HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, framing y redirects.

La clave es **live**: leer HTML o configuración del repo no demuestra qué cabeceras recibe el navegador.

## Hipótesis original

La lista inicial proponía confirmar en todas las respuestas servidas la existencia/consistencia de:

- `Content-Security-Policy`;
- `Strict-Transport-Security`;
- `X-Content-Type-Options`;
- protección de framing;
- políticas de referrer/permissions.

La descripción original contenía una premisa incorrecta: decía que la CSP era estricta y «sin `unsafe-inline`».

## Corrección factual de #135

La revisión detectó expresamente que la política actual contiene:

```text
style-src 'self' 'unsafe-inline'
```

Por tanto M.1 no puede partir de la ficción de una CSP sin inline styles.

El `main` actual sigue confirmándolo en `scripts/build-site-shell.py`, que documenta `unsafe-inline` como deuda conocida para estilos inline puntuales.

## Evolución histórica

### Revisión 108/108 → `IMPLEMENT_NOW`

- valor alto;
- auditoría live;
- corregir la premisa `unsafe-inline`;
- no perseguir scores por sí mismos.

### Matriz → `IMPLEMENTAR`

> auditor live de headers en producción: CSP/header vs meta, HSTS, nosniff, referrer, permissions policy, framing.

### Blueprint W8

#135 diseñó una primera implementación **report-only** con peticiones HEAD a rutas representativas y extracción de:

```text
strict-transport-security
x-content-type-options
referrer-policy
permissions-policy
content-security-policy
x-xss-protection
expect-ct
```

El blueprint prohíbe convertir ausencias directamente en hard fail antes de distinguir qué controla GitHub Pages/origin y qué requeriría proxy/Rules.

### Autoridad final → `IMPLEMENT_NOW`

> «Auditor live de headers: CSP efectiva, HSTS, nosniff, Referrer-Policy, Permissions-Policy, framing/CORP según aplique. Usar MDN HTTP Observatory como segunda opinión, no como “score SEO”.»

## Estado actual de `main`

### CSP meta sí existe

`scripts/build-site-shell.py` genera una meta CSP para páginas V1 públicas con:

- `default-src 'self'`;
- allowlists para GoatCounter/Metricool/Turnstile/Worker;
- `object-src 'none'`;
- `base-uri 'self'`;
- `form-action 'self'`;
- `style-src 'self' 'unsafe-inline'`;
- hashes por página para `speculationrules` inline ejecutables.

### `frame-ancestors` no está en la meta

El propio builder documenta correctamente que `frame-ancestors` se ignora cuando CSP se entrega por `<meta>` y que la protección efectiva requiere cabecera HTTP.

Esto es exactamente por lo que M.1 debe observar respuestas live.

### Repo ≠ cabeceras live

No se ha localizado una autoridad Git que permita afirmar por sí sola:

- HSTS efectivo;
- `X-Content-Type-Options: nosniff`;
- `Referrer-Policy` HTTP;
- `Permissions-Policy`;
- `frame-ancestors` por header;
- `Cross-Origin-Resource-Policy` si aplica.

La ausencia en Git tampoco demuestra ausencia en producción: origin/CDN puede añadirlas externamente.

## Auditoría propuesta por #135

Primer paso report-only sobre rutas representativas:

```text
/
/libros/samuel-entre-mundos/
/herramientas/
```

Conviene ampliar por familias si hay diferencias de serving:

```text
/
/las-manecillas-del-recuerdo/
/libros/samuel-entre-mundos/
/cuaderno/
/herramientas/
/asistente/
/lectores-beta/
```

Para cada una registrar:

```text
status
redirect_chain
content-security-policy
strict-transport-security
x-content-type-options
referrer-policy
permissions-policy
x-frame-options
cross-origin-resource-policy
server/cache headers relevantes
```

## CSP: comparar meta y header

Si existe CSP HTTP + CSP meta, el auditor debe comprobar que no sean contradictorias. El navegador aplica ambas políticas; una divergencia puede romper funcionalidad o dar una falsa sensación de seguridad.

Preguntas:

- ¿hay CSP por header?
- ¿hay solo meta CSP?
- ¿qué fuentes añade cada una?
- ¿`frame-ancestors` existe en header real?
- ¿se mantiene la allowlist mínima?
- ¿aparecen `unsafe-eval` o wildcards inesperados?

## HSTS

M.1 debe observar si existe `Strict-Transport-Security` y su valor real. **No** debe añadir automáticamente `includeSubDomains` o `preload`: eso pertenece a M.2 y está diferido.

## `nosniff`

Comprobar `X-Content-Type-Options: nosniff` en respuestas relevantes. Si falta, primero determinar qué capa puede añadirlo sin introducir una configuración paralela inconsistente.

## Referrer Policy

Comprobar cabecera efectiva y cualquier meta equivalente. La política debe ser coherente con analítica/afiliación/privacidad; no endurecerla a ciegas si rompe atribución necesaria sin valorar el trade-off.

## Permissions Policy

Inventariar solo APIs relevantes. No crear una lista enorme de features negadas para obtener puntuación; una política explícita debe corresponder a capacidades reales del sitio.

## Framing

La meta CSP no puede resolver `frame-ancestors`. El auditor debe determinar la protección HTTP real (`frame-ancestors` y/o mecanismo legacy si aún fuera necesario por compatibilidad concreta).

## CORP/COOP/COEP

No añadir aislamiento cross-origin por checklist. Verificar primero si existe una necesidad real y si afectaría terceros, Turnstile, media o herramientas.

## Redirects

La auditoría debe comprobar también:

- HTTP→HTTPS;
- host canonical;
- ausencia de loops;
- respuesta final correcta;
- HSTS observado en HTTPS final.

## Headers obsoletos

M.3 cubre retirar `X-XSS-Protection`, `Expect-CT` o HPKP heredados. M.1 puede reportarlos, pero no debe mezclar implementación de M.3 dentro de esta PR documental.

Las búsquedas actuales del repo no localizan `X-XSS-Protection` ni `Expect-CT`, pero eso no sustituye el chequeo live.

## Segunda opinión externa

#135 aprobó MDN HTTP Observatory como contraste, no como objetivo de puntuación. Un A/A+ no demuestra por sí mismo que la política sea la adecuada para esta arquitectura.

## Diseño de artefacto futuro

Un reporte machine-readable podría incluir:

```json
{
  "checkedAt": "...",
  "url": "https://davidportodiaz.com/",
  "status": 200,
  "redirects": [],
  "headers": {
    "content-security-policy": null,
    "strict-transport-security": null,
    "x-content-type-options": null,
    "referrer-policy": null,
    "permissions-policy": null
  },
  "classification": "OBSERVED",
  "notes": []
}
```

No guardar cookies, tokens o contenido sensible.

## Fases correctas

### Fase 1 — report-only

Observar y clasificar.

### Fase 2 — decidir ownership

Por cada gap:

- GitHub Pages/origin;
- Cloudflare si el tráfico pasa por proxy;
- HTML meta;
- configuración externa.

### Fase 3 — corregir un gap real

PR/config específica, con smoke antes/después.

### Fase 4 — gate

Solo convertir un header en hard requirement cuando el proyecto controla de forma estable esa capa.

## Qué NO hacer

- afirmar «CSP estricta sin unsafe-inline»;
- añadir `frame-ancestors` a meta CSP y creer que funciona;
- activar Cloudflare proxy solo para obtener headers;
- añadir headers incompatibles para subir un score;
- mezclar M.2 HSTS preload;
- copiar una plantilla securityheaders.com sin revisar terceros;
- tratar ausencia en repo como ausencia live;
- tratar presencia en HTML como presencia HTTP.

## Definition of Done futura

- respuestas live auditadas en familias representativas;
- redirect chain registrada;
- CSP meta/header comparadas;
- HSTS observado sin activar preload automáticamente;
- nosniff/referrer/permissions/framing clasificados;
- ownership de cada gap identificado;
- observaciones externas usadas como segunda opinión;
- no secretos/PII en el artefacto;
- cambios posteriores acompañados de smoke real.

## Trazabilidad preservada

- hipótesis original;
- corrección factual `unsafe-inline`;
- revisión `IMPLEMENT_NOW`;
- matriz `IMPLEMENTAR`;
- blueprint W8 report-only;
- autoridad final `IMPLEMENT_NOW`;
- revalidación independiente;
- builder CSP actual y limitación de `frame-ancestors` vía meta.

## Recomendación para Clara/Claude

**Implementar la auditoría live report-only cuando se cierre la deuda prioritaria vigente.** No “arreglar headers” desde suposiciones. Primero observar qué entrega producción y quién controla cada capa.