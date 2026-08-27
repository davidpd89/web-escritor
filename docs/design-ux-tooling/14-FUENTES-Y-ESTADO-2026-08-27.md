# 14 — Fuentes primarias y estado de verificación

**Corte de esta revalidación:** 2026-08-27, contra `main` en este mismo checkout.
**Regla:** cada fila es una afirmación de esta corpus con su fuente primaria, no una promesa. Si un dato no se pudo verificar en este corte, queda marcado `PENDIENTE`, no se rellena con lo que "probablemente" sea cierto.

## Herramientas ya integradas en este repositorio (verificable por código)

| Herramienta | Versión pinneada | Fuente | Estado |
|---|---|---|---|
| Playwright | `1.62.1` (`package.json`) | `package.json` de este repo | Verificado — instalado, usado por `qa/*.mjs` |
| Playwright (ad-hoc, 3 workflows) | `1.55.0` | `.github/workflows/analytics-taxonomy-qa.yml`, `csp-public-shell-qa.yml`, `manecillas-funnel-qa.yml` (instalación `npm install --no-save playwright@1.55.0`) | **Inconsistencia real detectada en este corte**: contradice el propio propósito declarado en `package.json` ("evitar que cada workflow instale la suya"). No es teórico — son motores Chromium distintos corriendo gates distintos. Pendiente de unificar a `1.62.1` en una PR propia de CI, fuera de esta PR de documentación. |
| `@lhci/cli` (Lighthouse CI) | `0.15.1` | `package.json`; usado en `lighthouserc.json` + `.github/workflows/*.yml` | Verificado — ejecutado en vivo en esta sesión contra `autor.html`, `asistente/`, etc. |
| `pa11y-ci` | `4.1.1` | `package.json`; `.github/workflows/*.yml` (`pa11y-baseline`) | Verificado — check en verde en múltiples PR de esta tanda |
| `pagefind` | `^1.5.2` | `package.json` | Verificado — usado para búsqueda estática del sitio |

## MCP disponibles a Claude Code en este entorno (verificado por listado de herramientas de la propia sesión, no por documentación externa)

| MCP | Qué permite | Estado en este corte |
|---|---|---|
| Figma (`mcp.figma.com/mcp`) | Leer diseños Figma a código (`get_design_context`, `get_screenshot`, `get_metadata`), generar diseño desde código, Code Connect, FigJam/diagramas | Disponible como herramienta de esta sesión. No usado todavía en ninguna PR mergeada — cualquier `INSTALL_NOW` sobre Figma en `13-BACKLOG` sigue siendo recomendación, no integración activa. |
| Canva (`mcp.canva.com/mcp`) | Generar/editar diseños Canva, exportar assets, gestionar carpetas/comentarios | Disponible como herramienta de esta sesión. No usado todavía en ninguna PR mergeada. |
| Chrome DevTools MCP | Navegación real, screenshots, network/console, Lighthouse audit, performance trace, snapshot de accesibilidad | Disponible como herramienta de esta sesión (dos variantes: standalone y `plugin_chrome-devtools-mcp_chrome-devtools`). Usado activamente en esta sesión vía el navegador integrado (`mcp__Claude_Browser__*`) para verificar cambios reales antes de reportarlos. |
| Playwright MCP | Navegación/automatización de browser vía MCP (alternativa a Chrome DevTools MCP) | Disponible como herramienta de esta sesión. Redundante en parte con Chrome DevTools MCP y con el uso directo de `playwright` como dependencia de test — no se ha decidido cuál es la vía canónica para QA de diseño; **pendiente** de esa decisión en `13-BACKLOG` o en `docs/claude-toolbox` (ver más abajo). |
| `mcp-registry` (list/search/suggest connectors) | Descubrir e instalar nuevos MCP disponibles para el usuario | Disponible. No se ha usado para instalar nada nuevo en esta tanda. |

## Herramientas mencionadas en el corpus SIN integración verificada en este corte

| Herramienta | Dónde se menciona | Estado |
|---|---|---|
| BrowserStack (Remote MCP / dispositivos reales) | `05-BROWSER-REAL-DEVICE-VISUAL-REGRESSION.md` | **PENDIENTE** — no hay MCP de BrowserStack en la lista de herramientas de esta sesión ni token configurado en `.env`. Cualquier claim de "dispositivo real" sigue siendo aspiracional hasta que exista credencial + prueba. |
| Percy / Chromatic (visual regression as-a-service) | `05-BROWSER-REAL-DEVICE-VISUAL-REGRESSION.md` | **PENDIENTE** — no integrado; este repo usa comparación propia vía Playwright (`qa/*.mjs`), no un servicio de terceros. |
| Stark (`mcp.getstark.ai/mcp`) | `06-ACCESIBILIDAD-COMO-DISENO.md` | URL citada en el propio corpus, pero no aparece en la lista de MCP disponibles de esta sesión — **PENDIENTE** de confirmar si requiere instalación/autorización separada. El repo ya cubre buena parte de este terreno con `pa11y-ci` + Playwright a11y snapshots, verificado y en verde. |
| Maze (UX research) | `07-UX-RESEARCH-Y-COMPORTAMIENTO-REAL.md` | **PENDIENTE** — sin cuenta, sin integración, sin evidencia de uso. |
| Microsoft Clarity | `07-UX-RESEARCH-Y-COMPORTAMIENTO-REAL.md` | **PENDIENTE** — el sitio ya tiene GoatCounter + Metricool como analítica activa (ver `script.js`); Clarity sería una capa adicional, no reemplazo, y no está configurada. |

## Relación con `docs/claude-toolbox/` (PR #120)

PR #120 ("Claude Toolbox: plugins/MCP/Skills/APIs") cubre un catálogo más amplio de tooling de agente (no solo diseño/UX) y ya incluye su propia revalidación fechada (`18-REVALIDACION-2026-08-27.md`) contra las mismas familias de herramientas (Figma, BrowserStack, Canva, Chrome DevTools). **#120 sigue en draft y no mergeada** — no se trata su contenido como hecho consolidado aquí. Cuando #120 se mergee, este fichero debe enlazar a su `tools-catalog.json` en vez de mantener una segunda tabla paralela, para no tener dos fuentes de verdad sobre el mismo tooling.

## Regla de mantenimiento

Cualquier PR que integre una de las herramientas marcadas `PENDIENTE` arriba debe:

1. actualizar esta fila a `Verificado` con fecha y evidencia (test, log, captura);
2. si la integración requiere cuenta/credencial externa, reflejarlo también en `data/implementation-truth-ledger.json` con el estado real (`CONFIGURED_LIVE`/`VERIFIED_E2E`, nunca inferido);
3. no promover una herramienta a "en uso" solo porque su MCP aparezca disponible en el entorno de una sesión concreta — la disponibilidad de la herramienta y su uso real en el proyecto son cosas distintas.
