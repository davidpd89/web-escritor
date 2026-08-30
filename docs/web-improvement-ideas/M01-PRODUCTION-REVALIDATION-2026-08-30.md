# M.1 · Revalidación de producción · cabeceras HTTP

Fecha: 2026-08-30  
Base de código contrastada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
Tree: `68d02e1fe8ac2cfa239f4a716929e992abb672fd`  
Auditor introducido en esta PR: `qa/live-security-headers.mjs`  
Primer run: `33325462091`  
Job: `99294682413`  
Artefacto: `live-security-headers-report` (`9736090213`)

## Veredicto actualizado

`IMPLEMENTED_IN_PR · LIVE_REPORT_ONLY · PRODUCTION_OBSERVED · OWNERSHIP_GAPS_IDENTIFIED`

M.1 ya no depende de inferencias sobre el HTML o el hosting. La PR incorpora un auditor reproducible que consulta la producción real, sigue redirects y conserva evidencia machine-readable sin convertir ausencias en hard fail.

## Alcance observado

Se auditó:

- entrada `http://davidportodiaz.com/`;
- `/`;
- `/las-manecillas-del-recuerdo/`;
- `/libros/samuel-entre-mundos/`;
- `/cuaderno/`;
- `/herramientas/`;
- `/asistente/`;
- `/lectores-beta/`.

Las siete rutas HTTPS devolvieron `200` y un patrón de cabeceras uniforme.

La entrada HTTP devolvió `301` a `https://davidportodiaz.com/` y terminó en `200`.

## Cabeceras observadas en HTTPS

En todas las rutas muestreadas:

```text
server: GitHub.com
strict-transport-security: max-age=31556952
cache-control: max-age=600
content-type: text/html; charset=utf-8
```

No se observó cabecera HTTP para:

```text
content-security-policy
x-content-type-options
referrer-policy
permissions-policy
x-frame-options
cross-origin-resource-policy
cross-origin-opener-policy
cross-origin-embedder-policy
```

Tampoco se observaron cabeceras obsoletas:

```text
x-xss-protection
expect-ct
public-key-pins
```

## Consecuencias

### HSTS

HSTS sí existe en producción con `max-age=31556952`.

No contiene `includeSubDomains` ni `preload`. M.2 debe partir de este hecho y no tratar HSTS host-only como ausente.

### CSP

No existe CSP por cabecera HTTP en las rutas muestreadas.

El sitio sí genera CSP por `<meta http-equiv="Content-Security-Policy">` mediante `scripts/build-site-shell.py`. Por tanto la política de carga de recursos existe, pero las capacidades que CSP no admite vía meta —en particular `frame-ancestors`— no están cubiertas por esa vía.

### Framing

No se observó:

- `Content-Security-Policy` HTTP con `frame-ancestors`;
- `X-Frame-Options`.

La muestra no aporta protección HTTP anti-framing.

### `nosniff`

No se observó `X-Content-Type-Options: nosniff`.

### Referrer / Permissions

No se observaron `Referrer-Policy` ni `Permissions-Policy` por cabecera HTTP.

Esto no implica que deba copiarse una plantilla genérica. Cada política debe decidirse contra las capacidades/terceros reales y contra la capa de hosting disponible.

### CORP / COOP / COEP

No se observaron. Su ausencia queda registrada; M.1 no recomienda añadir aislamiento cross-origin por score o checklist.

## Ownership confirmado

La respuesta live identifica `server: GitHub.com`, coherente con:

- `CNAME` → `davidportodiaz.com`;
- README de publicación con GitHub Pages;
- ausencia de configuración `_headers`/Netlify/Vercel en el repo;
- comentario técnico del builder que ya documenta la limitación de `frame-ancestors` vía meta.

Por tanto cualquier cabecera que GitHub Pages no permita controlar directamente requiere una decisión explícita de arquitectura/edge y no debe fingirse con un fichero que el hosting ignore.

## Qué implementa esta PR

### `qa/live-security-headers.mjs`

- usa Node 22 sin dependencias externas;
- sigue redirects manualmente hasta 8 hops;
- observa rutas representativas;
- registra cabeceras de seguridad y diagnóstico;
- distingue ausencia de header de fallo de observación;
- marca presencia de CSP HTTP, HSTS, nosniff y framing;
- registra cabeceras legacy si aparecen;
- escribe `artifacts/security-headers/live-security-headers.json`.

### `.github/workflows/live-security-headers-audit.yml`

- ejecuta el auditor en PR cuando cambia su contrato;
- permite `workflow_dispatch`;
- sube siempre el JSON como artefacto;
- no convierte headers ausentes en merge gate.

## Semántica del gate

`REPORT_ONLY` significa:

- header ausente → observación, no fallo;
- header presente → evidencia, no aprobación automática;
- endpoint no observable/error de red/redirect inválido → fallo del auditor;
- una futura corrección solo puede endurecerse cuando exista owner estable de esa capa.

## Evidencia del primer run

Run `33325462091` / job `99294682413` terminó `success`.

El auditor observó todas las rutas sin errores y subió `live-security-headers-report` como artefacto. El resultado elimina la ambigüedad principal de M.1: producción sí aporta HSTS desde GitHub Pages, pero no aporta el resto de cabeceras HTTP inventariadas en la muestra.

## Próximas decisiones, fuera de M.1

- M.2: decidir únicamente si algún día compensa `includeSubDomains`/preload; el HSTS host-only ya existe.
- M.3: el auditor de M.1 ya observa `X-XSS-Protection`, `Expect-CT` y HPKP; no crear otro checker.
- framing/nosniff/referrer/permissions: cualquier hardening requiere una capa que realmente controle respuestas HTTP y smoke posterior.

## Qué NO hacer

- añadir `_headers` si GitHub Pages no lo consume;
- añadir `frame-ancestors` al meta CSP;
- duplicar CSP meta + HTTP sin comprobar intersección efectiva;
- activar Cloudflare proxy solo para mejorar una puntuación;
- confundir HSTS host-only existente con preload;
- hacer hard fail por CORP/COOP/COEP sin requisito de arquitectura;
- crear un segundo auditor para M.3.

## Estado final de M.1

La parte de **observación** pedida por M.1 queda implementada y probada en esta PR. Los gaps detectados son entradas para decisiones posteriores de ownership/hardening, no cambios que deban mezclarse automáticamente en M.1.
