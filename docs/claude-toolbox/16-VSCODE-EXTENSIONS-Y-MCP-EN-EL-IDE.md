# 16 — VS Code: qué extensiones sí ayudan y qué no confundir con plugins de Claude

## 1. Distinción esencial

En VS Code puedes ver varias clases de “plugins”:

1. **extensiones VS Code** — modifican el editor;
2. **Claude Code plugins** — añaden Skills/hooks/MCP/LSP/agents a Claude;
3. **MCP servers** — tools externas conectables desde clientes compatibles;
4. **browser extensions** — WAVE/axe/etc.;
5. **CLIs/dependencies de proyecto** — Stylelint, html-validate, Playwright, etc.

No instalar la misma capacidad cuatro veces porque aparece en cuatro galerías.

## 2. Claude Code en VS Code

La integración/extension de Claude Code es la superficie principal. El sistema de plugins de Claude se gestiona desde ella con `/plugins` y comparte configuración con CLI.

Regla: si una capacidad existe como **Claude plugin oficial**, preferir esa vía para que Claude pueda invocarla directamente, en vez de una extensión VS Code que solo muestra un panel al humano.

## 3. HTML-Validate VS Code

Extensión documentada por HTML-Validate:

```text
html-validate.vscode-html-validate
```

### Estado: PILOT

Instalar solo si se adopta HTML-Validate como validator local. La propia documentación recomienda dependencia local de proyecto para resultados consistentes, en lugar de depender exclusivamente de la versión bundled/global.

### Valor

- feedback HTML inmediato en editor;
- navega directamente a markup inválido.

### Limitación

Si W3C Nu + tests existentes cubren mejor y no añadimos `html-validate` al proyecto, no instalar la extensión por costumbre.

## 4. Stylelint VS Code

Estado: `PILOT AFTER CLI`.

Primero ejecutar Stylelint read-only sobre CSS real. Solo si se adopta config versionada tiene sentido que VS Code muestre esos diagnostics.

No instalar una extensión con reglas personales no reproducibles por CI/local dependency.

## 5. WAVE browser extension

No es VS Code, pero es más útil para revisión visual de accesibilidad que muchas extensiones editor-only.

WebAIM ofrece WAVE para Chrome/Firefox/Edge y afirma que la extensión procesa localmente la página, útil para localhost/dynamic pages.

Estado: `RECOMMENDED HUMAN SECOND LOOK`, no sustituto de Pa11y/axe/manual.

## 6. axe DevTools browser extension / tools

Si se adopta Deque/axe, seguir el producto/plan oficial. No instalar a la vez toda su suite de IDE/browser/MCP sin saber cuál es la fuente de findings que necesitamos.

MCP para Claude es preferible cuando queremos `analyze → remediate → verify` dentro del coding workflow.

## 7. BrowserStack MCP en VS Code

VS Code puede registrar MCP remoto `https://mcp.browserstack.com/mcp` y BrowserStack documenta un setup propio. Sin embargo, si el agente principal es Claude Code, mantener una sola configuración/auth por usuario siempre que sea posible.

No duplicar BrowserStack en:

- VS Code Copilot MCP;
- Claude Code MCP;
- Claude Desktop MCP;

si solo usamos uno para esta tarea.

## 8. Figma MCP en VS Code

Figma soporta VS Code y Claude Code. Elegir el cliente principal.

Para este proyecto, recomendación:

- Claude Code plugin Figma como vía de trabajo agentic;
- Figma UI para revisión humana;
- no duplicar configuración VS Code MCP salvo que otra herramienta del IDE necesite acceder al mismo server.

## 9. GitLens

Estado: `NO NEED FOR CLAUDE`.

Puede ser agradable para un humano, pero Claude ya tiene Git/GitHub, history/blame/commit APIs. No forma parte del stack agentic requerido.

## 10. Error Lens

Estado: `OPTIONAL HUMAN`.

Mejora visibilidad inline de diagnostics al humano. Claude obtiene diagnostics directamente vía LSP. No es una capacidad nueva de Claude.

## 11. Live Server / Live Preview

Estado: `NO STANDARDIZATION NEEDED`.

El repo ya tiene formas de servir/QA páginas. No introducir un runtime distinto solo porque una extensión abre localhost rápido. Usar el servidor que los tests/runbook esperan.

## 12. Prettier

Estado: `DO NOT INTRODUCE AS DESIGN TOOL`.

No mezclar un formateo masivo de HTML/CSS/JS con esta estrategia. Si el repo decide adoptar formatter, hacerlo como PR de code-style separada con diff review.

## 13. ESLint

Estado: `EVALUATE SEPARATELY`.

Puede aportar JS linting, pero no está en `package.json` actual. TypeScript LSP + tests ya cubren parte. Pilot solo si encontramos clases de bugs JS que LSP/tests no capturan.

No instalar extensión ESLint sin config/dependency versionada.

## 14. Style tooling visual que NO necesitamos

No instalar por defecto:

- color palette generators;
- CSS gradient generators;
- Tailwind IntelliSense (no usamos Tailwind);
- Bootstrap snippets;
- React snippets;
- icon pack insertors;
- AI UI generators;
- “web design copilot” genérico;
- design-to-code extension no conectada con Figma real.

Añaden sugerencias incompatibles con el stack/identidad.

## 15. Image preview / SVG tools

Pueden ser cómodos para el humano, pero antes de documentarlos como estándar preguntar qué gap resuelven. Chrome/Figma/ImageMagick ya cubren inspección y procesamiento principal.

## 16. Recommended Extensions del repo

No crear `.vscode/extensions.json` con 20 recomendaciones.

Si después de los pilots se consideran esenciales para cualquier colaborador, limitar a extensiones que:

- corresponden a una dependency/config versionada;
- tienen beneficio claro;
- no requieren cuenta/secreto;
- no alteran automáticamente archivos.

Ejemplo futuro posible si se adopta:

```json
{
  "recommendations": [
    "html-validate.vscode-html-validate"
  ]
}
```

Pero no añadirlo hasta decidir HTML-Validate.

## 17. MCP catalog de VS Code

VS Code puede facilitar añadir MCP servers, pero discovery no equivale a trust. Para cada server encontrado en UI aplicar la misma clasificación de `01-INVENTARIO`.

No pulsar Install basándose solo en nombre/descripción.

## 18. Qué debe ver David/Claude en VS Code al final

Un entorno limpio:

- Claude Code;
- diagnostics de LSP relevantes;
- Git diff/source control;
- quizá validator CSS/HTML si se adopta;
- MCPs gestionados por Claude/cliente principal;
- no una barra lateral con ocho asistentes y cuatro paneles de “AI review”.

## 19. Regla

> Una extensión de VS Code entra en el estándar del proyecto si mejora la experiencia de edición **y** sus resultados se pueden reproducir fuera de esa UI, o si aporta una capacidad humana claramente única.

De lo contrario puede quedar como preferencia personal del usuario, no como requisito de WEB DAVID PORTO.