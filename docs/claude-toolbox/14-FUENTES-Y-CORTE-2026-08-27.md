# 14 — Fuentes primarias y corte 2026-08-27

## Regla

Este registro fija **qué se verificó** al documentar la toolbox. Comandos, endpoints, planes, nombres y capabilities pueden cambiar. Antes de instalar meses después, Claude debe reabrir la fuente primaria.

Estados:

- `VERIFIED`: documentación/vendor disponible al corte.
- `PILOT`: producto real, pero adopción pendiente.
- `MONITOR`: novedad/release reciente o integración cuya disponibilidad exacta hay que volver a confirmar.
- `SECONDARY`: útil solo como complemento.

## Anthropic — plugins/Claude Code

### Catálogo de plugins

- https://claude.com/plugins/
- Estado: VERIFIED.
- Uso: catálogo público; nombres/vendors/capabilities.

### Repositorio marketplace oficial

- https://github.com/anthropics/claude-plugins-official
- `.claude-plugin/marketplace.json`
- Estado: VERIFIED.
- Observación: el fichero actual contiene un catálogo muy amplio; no interpretar presencia como recomendación para este proyecto.

### Community marketplace

- https://github.com/anthropics/claude-plugins-community
- Estado: VERIFIED como canal de comunidad; software tercero sigue requiriendo review.

### Plugins Anthropic/vendor relevantes

- Frontend Design: https://claude.com/plugins/frontend-design
- Superpowers: https://claude.com/plugins/superpowers
- Code Review: https://claude.com/plugins/code-review
- Skill Creator: https://claude.com/plugins/skill-creator
- Code Simplifier: https://claude.com/plugins/code-simplifier
- Playwright: https://claude.com/plugins/playwright
- GitHub: catálogo Claude / vendor GitHub
- CLAUDE.md Management: https://claude.com/plugins/claude-md-management
- Feature Dev: https://claude.com/plugins/feature-dev
- PR Review Toolkit: https://claude.com/plugins/pr-review-toolkit
- Chrome DevTools: https://claude.com/plugins/chrome-devtools-mcp
- Modern Web Guidance: https://claude.com/plugins/modern-web-guidance
- Hookify: https://claude.com/plugins/hookify
- Security Guidance: https://claude.com/plugins/security-guidance
- Claude Code Setup: https://claude.com/plugins/claude-code-setup
- TypeScript LSP: https://claude.com/plugins/typescript-lsp
- Pyright LSP: https://claude.com/plugins/pyright-lsp
- Canva: https://claude.com/plugins/canva

Todos: VERIFIED como plugins existentes al corte; la clasificación para David está en `01`.

## Google Chrome

### Modern Web Guidance

- https://claude.com/plugins/modern-web-guidance
- Vendor: Google Chrome.
- Verificado: 102 modern web features, 129 casos, offline search, no key; Baseline/progressive enhancement; telemetry desactivable mediante `DISABLE_TELEMETRY=1` según página actual.

### Chrome DevTools MCP

- https://claude.com/plugins/chrome-devtools-mcp
- Upstream/repo: Google Chrome DevTools MCP.
- Verificado: 29 tools, Puppeteer/CDP, browser automation, mobile emulation, trace/network/console/screenshots/DOM/memory/Lighthouse/CrUX capabilities.

### Claude in Chrome security

- https://support.claude.com/es/articles/12902428-usa-claude-en-chrome-de-forma-segura
- Fecha visible: 7 julio 2026.
- Verificado: riesgo de prompt injection, recomendación de perfil separado y evitar sitios sensibles.

## Microsoft Playwright

- https://claude.com/plugins/playwright
- Upstream: https://github.com/microsoft/playwright-mcp
- VERIFIED.
- Verificado: accessibility-tree based automation, tabs, navigation, forms, screenshots/PDF, network/console, assertions.

## Figma

### Setup Claude Code

- https://help.figma.com/hc/en-us/articles/39888612464151-Claude-Code-and-Figma-Set-up-the-MCP-server
- https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/
- Estado: VERIFIED.

Instalación preferida al corte:

```bash
/plugin install figma@claude-plugins-official
```

MCP remoto:

```text
https://mcp.figma.com/mcp
```

Manual Claude Code:

```bash
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

OAuth. Figma recomienda remote para la mayoría de casos.

### MCP catalog

- https://www.figma.com/mcp-catalog/
- Estado: VERIFIED.
- Verificado: Claude Code compatible; remote/local; read/write; Design/Make/FigJam y capacidades listadas según cliente.

## Canva

- https://claude.com/plugins/canva
- Estado: VERIFIED.
- Vendor: Canva.
- Verificado: MCP + seis skills actuales (edit, resize, bulk create, brand check, design feedback, comment feedback); preview/approve en edits.

## BrowserStack

### Overview

- https://www.browserstack.com/docs/browserstack-mcp-server/overview
- Estado: VERIFIED.

### Remote MCP

- https://www.browserstack.com/docs/browserstack-mcp-server/get-started/remote-mcp-server
- Endpoint: `https://mcp.browserstack.com/mcp`
- Auth: OAuth.
- Estado: VERIFIED.

### Local MCP

- https://www.browserstack.com/docs/browserstack-mcp-server/get-started/local-mcp
- Package: `@browserstack/mcp-server@latest` en docs actuales.
- Variables: `BROWSERSTACK_USERNAME`, `BROWSERSTACK_ACCESS_KEY`.
- Node: documentación actual indica v22+ en Get Started.
- Estado: VERIFIED.

### Tools

- https://www.browserstack.com/docs/browserstack-mcp-server/tools
- Estado: VERIFIED.

## Deque axe

- https://github.com/dequelabs/axe-accessibility
- https://www.deque.com/axe/mcp-server/
- Estado: PILOT/VERIFIED como producto.

Marketplace vendor:

```text
/plugin marketplace add dequelabs/axe-accessibility
/plugin install axe-accessibility
```

Setup:

```text
/axe-accessibility:mcp-setup
```

Auth actual:
- OAuth 2.0;
- API key `AXE_API_KEY` fallback.

El README al corte indica que axe DevTools for Web Bundle incluye acceso MCP y que OAuth usa Node 22 LTS+.

## Stark

- anuncio/información Stark sobre connector Claude, agosto 2026.
- Estado: MONITOR/PILOT.
- Regla: re-verificar soporte exacto Claude Code, plan y método de instalación antes de adoptar. No está tratado en esta toolbox como plugin oficial Anthropic confirmado.

## Context7

- Plugin visible en catálogo Claude: Context7 by Upstash.
- Server/documentación: https://context7.com / recursos Upstash oficiales.
- Estado: VERIFIED/P0.
- Verificado: documentación version-specific; puede funcionar sin API key; `CONTEXT7_API_KEY` solo para higher limits según setup vigente.

## Cloudflare

- https://developers.cloudflare.com/agent-setup/claude-code/
- Estado: VERIFIED.

Comandos documentados al corte:

```text
/plugin marketplace add cloudflare/skills
/plugin install cloudflare@cloudflare
```

Cloudflare describe Skills + MCP servers. Toda operación productiva queda gobernada por `08`.

## Google performance APIs

### CrUX API

- https://developer.chrome.com/docs/crux/api
- Estado: VERIFIED.
- Requiere Google Cloud API key habilitada para Chrome UX Report API.
- Endpoint: `POST https://chromeuxreport.googleapis.com/v1/records:queryRecord`.

### CrUX History API

- https://developer.chrome.com/docs/crux/history-api
- Estado: VERIFIED.
- Endpoint: `POST https://chromeuxreport.googleapis.com/v1/records:queryHistoryRecord`.
- Documentación visible al corte: seis meses de histórico; API key de CrUX.

### PageSpeed Insights API

- https://developers.google.com/speed/docs/insights/rest
- https://developers.google.com/speed/docs/insights/v5/get-started
- Estado: VERIFIED.
- Endpoint base v5: `https://pagespeedonline.googleapis.com` / `runPagespeed`.
- Puede usarse sin key de forma puntual; key recomendada para automatización frecuente.
- Importante: Google avisa que prevé retirar CrUX field data de PSI y recomienda CrUX/History para datos reales.

## W3C

### HTML Checker API

- https://validator.w3.org/docs/api.html
- Checker: https://validator.w3.org/nu/
- Estado: VERIFIED.
- Verificado: GET/POST y salida JSON/XML/GNU.

### WCAG/WAI

- https://www.w3.org/TR/WCAG22/
- https://www.w3.org/WAI/
- Autoridad normativa/guía, no plugin.

## HTML-Validate

- https://html-validate.org/usage/
- https://html-validate.org/usage/cli.html
- https://html-validate.org/usage/vscode.html
- Estado: PILOT.
- Al corte: major 11.x activo; CLI npm; extensión VS Code oficial/documentada.

## Stylelint

- https://stylelint.io/user-guide/get-started/
- Estado: PILOT.
- Setup actual oficial: `npm create stylelint@latest` o deps `stylelint` + standard config.

## WAVE/WebAIM

- https://wave.webaim.org/
- https://wave.webaim.org/extension/
- https://wave.webaim.org/api/
- Estado: browser extension SECONDARY; API DEFER.
- Verificado: extensions Chrome/Firefox/Edge; extension local no envía página al server según WebAIM; API por créditos.

## Repo `web-escritor`

### Package/QA

Fuente: `package.json` main al corte.

```json
{
  "@lhci/cli": "0.15.1",
  "pa11y-ci": "4.1.1",
  "pagefind": "^1.5.2",
  "playwright": "1.62.1"
}
```

Por eso no se recomiendan plugins/servicios que solo dupliquen esas cuatro capacidades.

### Claude config

Fuente: `.claude/settings.local.json` main al corte.

Hallazgo: fichero local versionado con paths específicos y permisos shell amplios. `.gitignore` al corte no lo excluye. Backlog CTB-001.

## Fuentes de terceros / caution

Cualquier GitHub issue sobre supply-chain/auto-update se usa solo como señal para reforzar review, no como política oficial ni afirmación de vulnerabilidad general.

## Cómo actualizar este registro

Cuando un comando falle o un proveedor cambie:

1. abrir URL primaria;
2. actualizar fecha/capability;
3. modificar docs + `tools-catalog.json` en PR;
4. no parchear solo el comando en un chat;
5. registrar si la decisión `INSTALL_NOW/PILOT/...` cambia.