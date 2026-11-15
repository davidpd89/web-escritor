# Equipo de expertos automáticos

Esta lista está viva. La mantiene Opus y la lee cada experto antes de proponer nada, para no repetir lo que ya cubre otro.

Cada miembro sigue el mismo esquema:
- **Herramientas deterministas**: miden y pueden bloquear.
- **Experto LLM**: lee lo que han medido, propone y abre issues `experto`.
- **Revisores de PR**: comentan las PR; sus avisos bloquean la fusión, que es manual.

Todo es gratuito. El LLM es Claude por la cuenta (`CLAUDE_CODE_OAUTH_TOKEN`), sin pago por token.

## Expertos LLM (`empleados-expertos.yml`, 05:17 en Madrid)

| Día | Rol | Datos que prepara el workflow | Salida |
|---|---|---|---|
| lunes | investigador | (búsqueda web) | 1 issue con ≤5 herramientas nuevas |
| martes | seo | SiteOne Crawler v2.5.1 (MIT) sobre 300 URL del sitemap | ≤3 issues |
| miércoles | geo | robots/llms.txt/JSON-LD de 40 URL (`empleados_expertos.py geo`) | ≤3 issues |
| jueves | ux | muestra de 40 URL | ≤3 issues |
| viernes | rendimiento | SiteOne con recursos + `performance-budgets.json` | ≤3 issues |
| sábado | arquitecto | issues `fallo` + `.ci/` + código de la carga | ≤3 issues |
| domingo | tester | tests y código crítico | ≤3 issues |

Para lanzar un rol a mano: `gh workflow run empleados-expertos.yml -f rol=seo`.

Límites (condiciones de Fable, R3-14):
- `--max-turns 25` y `--permission-mode default`;
- solo puede leer el repositorio y crear o comentar issues;
- `contents: read` e `issues: write`.

Lo que ya existía: `revision-existente.yml` abre cada día una PR con código antiguo para que la revisen los bots.

## Revisores de PR (apps)

| Revisor | Coste | Estado |
|---|---|---|
| CodeRabbit | gratis en repos públicos | activo |
| Codex (ChatGPT) | incluido en la cuenta | activo |
| DeepSource | gratis en OSS | activo (arreglos en #1339) |
| SonarQube Cloud | gratis en repos públicos | activo (puerta de calidad en cada PR) |
| Gemini Code Assist | gratis | cerrado el 14/11 |
| Jules | gratis | solo lectura |

## Herramientas deterministas en CI

| Área | Herramienta | Workflow |
|---|---|---|
| rendimiento | Lighthouse CI 0.16 | `lighthouse-ci.yml`, `performance-budget-qa.yml` |
| accesibilidad | pa11y-ci 5 | `pa11y-baseline.yml`, `a11y-regressions-browser-qa.yml` |
| enlaces | propio | `broken-links.yml` |
| seguridad | CodeQL, supply chain npm | `codeql.yml`, `npm-supply-chain-watch.yml` |
| producción | smoke y cabeceras | `production-smoke-monitor.yml`, `live-security-headers-audit.yml` |

## Candidatos (investigación del 15/11, GPT por chat y WebSearch)

Pendiente de completar con las rondas de GPT (`scratchpad/gpt_respuestas`). Se priorizan los que son gratuitos, los que se automatizan sin intervención y los que detectan algo que hoy no mide nadie.

## Hueco abierto

Cubierto en parte por el turno de issues (#1374): el turno local de `night-autorepair.py` toma cada hora una issue `fallo` (primero) o `experto`, como mucho 3 al día. Abre la PR con las credenciales locales, así que la CI sí se dispara. Espera a los bots y corrige sus hilos (2 veces como mucho). Fusiona sin `--admin` y nunca durante la carga. Si no puede, cierra y etiqueta `necesita-david`.

Sigue abierto: si el PC está apagado, nadie consume las issues. Hacerlo desde Actions necesita un PAT o una app, porque las PR creadas con GITHUB_TOKEN no disparan la CI. Está en las preguntas de Fable, ronda 4.
