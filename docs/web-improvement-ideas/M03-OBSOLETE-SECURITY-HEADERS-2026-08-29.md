# M.3 · Retirar cabeceras HTTP obsoletas si existieran

Fecha de reconstrucción: 2026-08-29  
Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `IMPLEMENT_AFTER_CURRENT_DEBT`.

## Veredicto reconciliado

M.3 no autoriza a “añadir todas las cabeceras de seguridad que suenen bien”. Su propósito es exactamente el contrario: detectar en las **respuestas públicas reales** cabeceras heredadas, contradictorias u obsoletas y retirarlas cuando exista evidencia.

La implementación futura debe compartir el mismo smoke live de M.1. No crear un segundo auditor de HTTP.

## Hipótesis original

La lista inicial proponía confirmar que no quedaran:

- `X-XSS-Protection`;
- `Expect-CT`;
- HPKP / `Public-Key-Pins`;
- otras cabeceras heredadas añadidas por checklists antiguas.

El valor era eliminar configuración obsoleta y evitar una falsa sensación de seguridad.

## Evolución en #135

### Primera revisión

La revisión técnica mantuvo la idea como trabajo útil, de coste bajo, pero subordinado a evidencia real de las respuestas.

### Matriz intermedia → `IMPLEMENTAR`

La matriz formuló la tarea como una extensión del smoke HTTP:

> detectar headers obsoletos/contradictorios; no reintroducir `X-XSS-Protection`, HPKP o `Expect-CT` por checklists antiguas.

### Blueprint W8

`IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` integra M.3 con M.1, I.2 e I.5 y propone un primer modo **report-only** que inspeccione, entre otros:

```text
strict-transport-security
x-content-type-options
referrer-policy
permissions-policy
content-security-policy
x-xss-protection
expect-ct
```

Regla crítica: no convertir una ausencia/presencia en hard fail hasta distinguir qué controla realmente el origin, GitHub Pages y cualquier capa de proxy.

### Autoridad final → `IMPLEMENT_AFTER_CURRENT_DEBT`

La autoridad final mantiene M.3 como trabajo posterior a la deuda actual.

### Revalidación independiente

La revalidación conserva M.1–M.5 sin cambios de estado. Además eleva seguridad nativa de GitHub como operación separada, pero no sustituye M.3.

## Revalidación actual de `main`

La búsqueda de código no encuentra declaraciones explícitas de `X-XSS-Protection` ni `Expect-CT`, pero eso **no demuestra** que las respuestas live no las incluyan: podrían proceder del hosting/origin/proxy.

Por tanto el estado correcto sigue siendo:

```text
repo evidence: no configuración explícita encontrada
live HTTP evidence: pendiente
status: IMPLEMENT_AFTER_CURRENT_DEBT
```

## Relación con M.1

M.1 es la auditoría live general de cabeceras. M.3 es una regla dentro de esa auditoría:

- M.1 pregunta qué cabeceras existen y son efectivas;
- M.3 detecta específicamente legado/contradicciones.

No crear `check-obsolete-headers.py` si el futuro smoke de M.1 ya puede emitir estos findings.

## Qué no reintroducir por checklist

### `X-XSS-Protection`

No usarlo como sustituto de CSP moderna ni reintroducirlo solo porque un scanner antiguo lo puntúe.

### HPKP / `Public-Key-Pins`

No recuperar HPKP como mecanismo de endurecimiento; el riesgo operativo y obsolescencia invalidan su uso moderno.

### `Expect-CT`

No añadirlo como requisito moderno por costumbre histórica.

La lista puede ampliarse si una fuente primaria actual demuestra que otra cabecera quedó obsoleta, pero el principio es evidence-first.

## Contradicciones a detectar

M.3 también debe cubrir configuraciones que, aun no siendo “obsoletas”, se contradigan entre capas:

- CSP meta diferente de CSP header;
- políticas duplicadas con valores incompatibles;
- HSTS diferente entre host/apex/subdominios;
- headers declarados solo en algunas familias de rutas;
- redirects que pierdan o cambien políticas de seguridad.

## Diseño de auditoría futuro

Primer paso, report-only:

```text
URL
status/redirect chain
header name
value
source/layer if inferible
finding = OK | OBSOLETE | CONTRADICTORY | UNKNOWN
```

Rutas mínimas:

- home;
- libro;
- Cuaderno;
- herramienta;
- 404;
- assets sensibles si aplica.

## Definition of Done

- auditoría sobre respuestas HTTPS reales;
- `X-XSS-Protection`, `Expect-CT`, HPKP y equivalentes inventariados;
- ninguna cabecera retirada sin saber qué capa la controla;
- contradicciones meta/header detectadas;
- redirects incluidos;
- primera adopción report-only;
- hard gates solo después de baseline confirmado;
- documentación de cualquier excepción.

## Qué NO hacer

- añadir cabeceras solo para conseguir A+;
- considerar código fuente como prueba de respuesta live;
- duplicar M.1;
- tocar Cloudflare/proxy sin necesidad;
- retirar una política válida por coincidir parcialmente con un nombre legacy;
- reintroducir mecanismos obsoletos porque un blog de seguridad antiguo los recomiende.

## Trazabilidad

- `IDEAS-MEJORA-WEB-2026-08-27.md` — idea original M.3;
- `IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — evaluación;
- `IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `IMPLEMENTAR`;
- `IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — W8;
- `data/web-improvement-decisions-2026-08-28.json` — `IMPLEMENT_AFTER_CURRENT_DEBT`;
- `PR135-FINAL-AUTHORITY-2026-08-28.md` — autoridad final;
- `PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — estado mantenido.

## Recomendación

Implementar M.3 **dentro del auditor live de M.1** después de la deuda prioritaria. Primero observar; después corregir únicamente lo que exista de verdad.