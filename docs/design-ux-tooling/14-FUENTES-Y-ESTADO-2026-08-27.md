# 14 — Fuentes primarias y estado de verificación

**Corte original de esta revalidación:** 2026-08-27.  
**Reconciliación posterior:** 2026-08-27, después de PR #127/#128.  
**Regla:** cada fila es una afirmación de este corpus con su fuente/evidencia, no una promesa. Una observación de herramientas disponibles en una sesión concreta tampoco equivale a integración persistente del proyecto.

## Herramientas ya integradas en este repositorio (verificable por código)

| Herramienta | Versión pinneada | Fuente | Estado |
|---|---|---|---|
| Playwright | `1.62.1` (`package.json`) | `package.json` + lockfile de este repo | **Verificado — estado actual.** Usado por `qa/*.mjs`; PR #127 eliminó las instalaciones ad-hoc 1.55.0 que todavía quedaban en tres workflows. No volver a describir esa divergencia como pendiente. |
| Drift Playwright histórico | `1.55.0` vs `1.62.1` | historial previo a PR #127 | **RESUELTO por PR #127.** Se conserva como incidente/razón del lockfile único, no como estado vigente. Un nuevo `npm install --no-save playwright@...` en workflows debe tratarse como regresión. |
| `@lhci/cli` (Lighthouse CI) | `0.15.1` | `package.json`; usado en `lighthouserc.json` + workflows | Verificado — tooling CI/dev, no runtime público. |
| `pa11y-ci` | `4.1.1` | `package.json`; `pa11y-baseline` | Verificado — tooling CI/dev. |
| `pagefind` | `^1.5.2` | `package.json` | Verificado — usado para búsqueda estática del sitio. |

## MCP observados como disponibles en una sesión de Claude Code

Esta tabla es **histórica/sesión-específica**. Sirve para registrar qué pudo usar Claude en aquella sesión, no para afirmar que la misma capacidad esté instalada, autorizada o disponible en cualquier estación futura.

| MCP | Qué permite | Estado en el corte original |
|---|---|---|
| Figma (`mcp.figma.com/mcp`) | Leer contexto/screenshot/metadata, generar diseño desde código, Code Connect, FigJam/diagramas | Disponible en la sesión observada. No equivale a integración persistente ni a permiso de escritura sobre un fichero final. |
| Canva (`mcp.canva.com/mcp`) | Generar/editar diseños, exportar assets, carpetas/comentarios | Disponible en la sesión observada. No usado como autoridad del layout web. |
| Chrome DevTools MCP | Navegación real, screenshots, network/console, performance, a11y | Disponible/usado en la sesión observada. El navegador sigue siendo evidencia de comportamiento, no permiso de deploy. |
| Playwright MCP | Automatización browser agentic | Disponible en la sesión observada. Redundante en parte con Chrome DevTools MCP y distinto del Playwright versionado del repo. La vía canónica agentic sigue pendiente de decisión en #120. |
| `mcp-registry` | Descubrir/conectar MCP | Disponible en la sesión observada. No implica que los MCP descubiertos estén instalados. |

## Herramientas mencionadas en el corpus SIN integración persistente verificada

| Herramienta | Dónde se menciona | Estado |
|---|---|---|
| BrowserStack (Remote MCP / dispositivos reales) | `05-BROWSER-REAL-DEVICE-VISUAL-REGRESSION.md` | **PENDIENTE/ON_DEMAND.** No existe evidencia versionada de cuenta + conexión + prueba de dispositivo real. Cualquier claim de iOS/Android real requiere esa evidencia. |
| Percy / Chromatic | `05-BROWSER-REAL-DEVICE-VISUAL-REGRESSION.md` | **PENDIENTE.** El repo usa QA propia con Playwright; no adoptar un servicio por duplicación. |
| Stark | `06-ACCESIBILIDAD-COMO-DISENO.md` | **PENDIENTE.** Revalidar disponibilidad/auth actual antes de piloto; Pa11y + browser QA ya cubren parte del terreno. |
| Maze | `07-UX-RESEARCH-Y-COMPORTAMIENTO-REAL.md` | **PENDIENTE.** Sin cuenta/integración/evidencia de uso. |
| Microsoft Clarity | `07-UX-RESEARCH-Y-COMPORTAMIENTO-REAL.md` | **PENDIENTE/CONDICIONAL.** Requiere decisión de privacidad/consentimiento y necesidad de investigación; no añadir tracking solo para alimentar a un agente. |

## Relación con `docs/claude-toolbox/` (PR #120)

PR #120 cubre un catálogo más amplio de agent-tooling y sigue **DRAFT**. En el snapshot posterior a #128 su rama ya está refrescada contra `main` (`behind_by=0`) y tiene CI verde, pero aún falta la revalidación material de cada `INSTALL_NOW` y resolver contradicciones/prerequisites. Por tanto:

- este documento gobierna el contexto de diseño/UX;
- `docs/claude-toolbox/tools-catalog.json`, una vez mergeado y revalidado, gobernará instalación/operación general;
- si una herramienta aparece en ambos, la discrepancia debe ser deliberada y documentada, no accidental;
- ningún estado del catálogo significa por sí solo `INSTALLED`, `CONFIGURED_LIVE` o `VERIFIED_E2E`.

## Regla de mantenimiento

Cualquier PR que integre una herramienta hoy no verificada debe:

1. actualizar el estado con fecha y evidencia reproducible;
2. si requiere cuenta/credencial externa, separar `MERGED_MAIN` de `CONFIGURED_LIVE`/`VERIFIED_E2E` en `data/implementation-truth-ledger.json`;
3. no promover una herramienta a «en uso» solo porque aparezca disponible en una sesión concreta;
4. si cambia una versión compartida de browser QA, hacerlo desde `package.json`/lockfile y evitar instalaciones ad-hoc en workflows;
5. revalidar fuente, auth, privilegios y coste el día de activación cuando sean susceptibles de cambiar.
