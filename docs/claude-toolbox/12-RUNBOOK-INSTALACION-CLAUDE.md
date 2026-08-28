# 12 — Runbook de instalación para Claude

## Principio

No ejecutar un script que instale 30 plugins. Se instala **una clase de capacidad cada vez**, se prueba y se registra si añade valor.

## Fase 0 — sanear configuración local

Antes de auth/MCP:

1. revisar `.claude/settings.local.json` actual;
2. crear PR separada para dejar de trackearlo y añadirlo a `.gitignore`;
3. mover únicamente políticas compartibles a `.claude/settings.json` si existen;
4. reducir permisos shell demasiado amplios cuando haya alternativa;
5. verificar que no existen tokens en git history reciente/configs.

Gate: ningún secreto nuevo hasta cerrar Fase 0.

## Fase 1 — núcleo sin cuentas externas

Instalar:

```bash
/plugin install modern-web-guidance@claude-plugins-official
/plugin install security-guidance@claude-plugins-official
/plugin install typescript-lsp@claude-plugins-official
/plugin install pyright-lsp@claude-plugins-official
/plugin install claude-md-management@claude-plugins-official
/plugin install skill-creator@claude-plugins-official
/plugin install hookify@claude-plugins-official
/plugin install pr-review-toolkit@claude-plugins-official
/plugin install context7@claude-plugins-official
```

No instalar todavía SaaS ni keys.

### Test 1

- Modern Web Guidance: consultar una feature web moderna.
- Security Guidance: confirmar plugin habilitado.
- TypeScript LSP: buscar references de una función JS real.
- Pyright: analizar un script Python.
- CLAUDE.md Management: ejecutar auditoría read-only.
- Skill Creator: listar/iniciar workflow sin escribir una skill definitiva.
- Hookify: crear una regla de warning de prueba y listar rules.
- PR Toolkit: analizar un PR pequeño.
- Context7: consultar docs actuales de una dependencia.

Gate: cada plugin tiene al menos una prueba exitosa; cualquier duplicación/ruido se registra.

## Fase 2 — browser agentic

```bash
/plugin install chrome-devtools-mcp@claude-plugins-official
/plugin install playwright@claude-plugins-official
```

### Test 2A — Chrome

1. levantar build local según runbook repo;
2. abrir Home;
3. viewport 390;
4. screenshot;
5. leer console;
6. obtener computed size del H1;
7. medir bounding rect de dos regiones;
8. no modificar nada.

### Test 2B — Playwright

1. Home;
2. abrir una ruta real;
3. volver atrás;
4. abrir/cerrar Explorar;
5. probar un formulario sin enviar a servicio real si existe modo local/seguro;
6. recoger accessibility-tree state.

Gate: Claude puede explicar qué tool usaría para inspección vs journey.

## Fase 3 — GitHub

```bash
/plugin install github@claude-plugins-official
```

### Test

- leer branch actual;
- leer un PR open/draft;
- listar checks;
- abrir un changed file;
- no escribir/mergear.

Después comparar si el plugin reduce necesidad de `gh api *` permisos genéricos.

## Fase 4 — guardrails reales

Con Hookify, convertir reglas aprobadas:

1. no main direct;
2. no secrets en repo;
3. warn deploy;
4. warn merge;
5. test gate por cambio UI.

No activar bloqueos que impidan comandos legítimos sin escape claro.

## Fase 5 — plugin propio

Instalar temporalmente:

```bash
/plugin install plugin-dev@claude-plugins-official
```

Crear primero:

- `observe-live`;
- `mobile-hierarchy-audit`;
- `design-critic`.

Usar Skill Creator:

1. Create;
2. Eval;
3. Improve;
4. Benchmark;
5. comparar contra baseline.

Gate: no expandir a siete skills hasta demostrar que las tres primeras mejoran outputs.

## Fase 6 — Figma

Solo cuando exista/preparemos fichero/lab Figma concreto:

```bash
/plugin install figma@claude-plugins-official
```

Autenticar OAuth.

### Test

- leer un frame;
- listar variables/componentes relevantes;
- mapear token vs repo;
- crear una hipótesis en canvas únicamente en área de lab;
- comprobar que no modifica otros assets.

No dar “rediseña todo el archivo” como primer test.

## Fase 7 — Frontend Design + Playground

```bash
/plugin install frontend-design@claude-plugins-official
/plugin install playground@claude-plugins-official
```

### Pilot

Un problema: jerarquía de artículo mobile.

1. Chrome observa;
2. contratos V1;
3. Frontend Design produce máximo tres hipótesis;
4. Playground/Figma visualiza las mejores;
5. design-critic las evalúa;
6. solo después se implementa una.

Gate: si el plugin tiende a imponer una estética genérica o a ignorar contenido real, mantenerlo deshabilitado salvo brainstorming controlado.

## Fase 8 — BrowserStack

Solo con cuenta/trial/plan.

Preferir remoto OAuth:

```text
https://mcp.browserstack.com/mcp
```

Si Claude Code requiere registro manual de remote MCP, seguir documentación BrowserStack/Claude vigente en ese momento; no inventar config.

### Pilot

- Safari iOS portrait;
- Safari iOS landscape;
- Chrome Android;
- teclado formulario;
- rotación;
- safe area;
- Explorar;
- Manecillas;
- artículo;
- herramienta.

Registrar issues únicos vs emulación local.

Gate: si aporta issues reales, adoptar. Si no, usarlo puntualmente.

## Fase 9 — accesibilidad especializada

### Opción A — axe

```text
/plugin marketplace add dequelabs/axe-accessibility
/plugin install axe-accessibility
/axe-accessibility:mcp-setup
```

Preferir OAuth.

### Opción B — Stark

Confirmar instalación/plan actual antes de activar.

### Pilot comparativo

Misma familia/páginas y mismos known issues. Medir:

- issues únicos;
- precisión;
- remediación útil;
- false positives;
- coste;
- integración Figma/source/live URL.

Elegir 0 o 1 suite pagada adicional.

## Fase 10 — Cloudflare

Solo cuando la tarea entra en Worker/runtime:

```text
/plugin marketplace add cloudflare/skills
/plugin install cloudflare@cloudflare
```

Primera sesión read/docs/local. No deploy.

Gate antes de cualquier write real: autorización del usuario + Hookify + diff/rollback/smoke plan.

## Fase 11 — security scanner adicional

Pilot Semgrep primero. No adoptar CI hasta haber clasificado baseline.

Si se evalúa Sonar/Aikido, hacer comparison, no acumulación.

## Fase 12 — research MCP

Probar Firecrawl y/o Exa únicamente con una tarea de research que hoy consuma tiempo.

No crear keys hasta empezar el pilot.

## Fase 13 — analytics/performance APIs

### CrUX

Crear Google Cloud key solo cuando haya un script/dashboard definido.

### WebPageTest

Crear key solo para un problema que necesite filmstrip/waterfall/locations beyond current stack.

### WAVE API

No adquirir créditos mientras Pa11y + manual + posible axe cubran la necesidad.

## Fase 14 — revisión del stack

Al terminar:

```text
/plugins
/mcp
```

Actualizar `tools-catalog.json`:

- installed;
- enabled;
- auth configured;
- last verified;
- actual use;
- incidents;
- decision.

Deshabilitar pilots no consolidados.

## Fase 15 — rutina por tipo de trabajo

### CSS/visual

`Modern Web Guidance → Chrome → contract → hypothesis → implementation → Chrome → Playwright → a11y → visual/device as needed`.

### JS feature

`LSP → Feature Dev if large → tests → browser → Security Guidance → PR Toolkit`.

### Python/generator

`Pyright → tests → public artifact checks → PR Toolkit`.

### Worker/API

`docs/Cloudflare → Security Guidance → local tests → Claude Security/Semgrep if sensitive → PR → explicit deploy authorization`.

### External research

`web/Firecrawl/Exa → source validation → no account-write tools in same session → save evidence`.

### Design exploration

`Chrome evidence → Figma/Frontend Design/Playground → design critic → human selection → implementation`.

## Fase 16 — regla para Claude futuro

Cuando Claude piense “necesito un plugin nuevo”:

1. buscar primero en `tools-catalog.json`;
2. ejecutar `claude-code-setup` read-only si la necesidad es amplia;
3. buscar official marketplace/vendor;
4. documentar por qué no basta stack actual;
5. pilot;
6. solo entonces promover a instalación estable.

No instalar durante una tarea crítica de producción una herramienta nueva que no haya pasado pilot salvo emergencia justificada.