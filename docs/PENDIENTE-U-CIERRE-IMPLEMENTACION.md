# Cierre técnico U — Claude 601–EOF

Fecha: 2026-08-23  
Base: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`  
Fuente auditada: `claude pending.txt`, líneas 601–746 (EOF).

## U.1 implementado

La deuda independiente de recursos embebibles se cierra con una primera pieza real: `/herramientas/tarjeta-estoy-leyendo/`.

Contrato implementado:

- generación local de HTML autocontenido y Markdown;
- título y autoría obligatorios con límites;
- etiquetas controladas;
- escape de contenido hostil y ausencia de markup ejecutable del usuario;
- ningún script, iframe o tracker en el snippet exportado;
- backlink/referencia desactivado por defecto y opt-in visible con `nofollow`;
- CSP de la herramienta con `connect-src 'none'` y sin runtime global `script.js`;
- sin red, analítica o persistencia del contenido introducido;
- Clipboard API con fallback de selección manual;
- labels, `aria-live`, `noscript`, preview y QA responsive a 320 px.

## Autoridades y derivados

La herramienta está registrada en `data/tools-hub.json` y `data/content-registry.json`. Los builders vigentes regeneraron y comprobaron:

- `herramientas/index.html` → 18 herramientas;
- shell V1 de la página nueva;
- `sitemap.xml` → 55 URLs;
- `data/site-human-stats.generated.html`;
- `data/site-human-stats.generated.json`;
- bloque generado de `autor.html`.

No se conserva ningún workflow temporal de generación en el diff final.

## QA permanente

- `tests/test-tarjeta-estoy-leyendo.mjs`: validación, límites, determinismo, escape/XSS, referencia opt-in y Markdown.
- `qa/tarjeta-estoy-leyendo-browser.mjs`: 320 px + escritorio, ausencia de requests externos durante la acción, XSS inerte, Clipboard API, fallback manual y referencia opt-in.
- `.github/workflows/tools-publishing-browser-qa.yml`: ejecuta el browser QA nuevo dentro del workflow de herramientas ya existente.
- `scripts/audit-private-tools.py` cubre la nueva ruta mediante el wildcard global de CI.

## Coordinación

No duplicar owners ya existentes: #59 autores/revisor/Atlas/vídeo; #58 smoke/staging; #54 update-dates; #55 Brevo; #61 popup/runtime; #57 fechas/premios; #66 cross-engine; #78 visual/mobile; #81 estabilidad diaria de human-site-stats.

Observatorio, Pregunta del mes, `/lecturas/` y publicación del lab siguen gated por contenido/datos reales, no por código faltante.

No tocar `main`, no desplegar producción y no hacer merge/auto-merge desde esta PR.
