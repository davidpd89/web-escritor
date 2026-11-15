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

Se eligieron entre 13 rondas de GPT (unas 250 herramientas). Pasan el filtro las gratuitas que se automatizan sin intervención y que miden algo que hoy no mide nadie. Las fases van por orden de entrada, y cada fase empieza en modo aviso (issue), nunca bloqueando.

| Fase | Herramienta | Área | Licencia | Qué añade | Enlace |
|---|---|---|---|---|---|
| 1 | Lychee | enlaces | MIT/Apache | enlaces rotos de todo el sitemap, internos y a Amazon | https://github.com/lycheeverse/lychee |
| 1 | Ajv + PyLD / validator.schema.org | datos estructurados | MIT/BSD | JSON-LD válido por tipo (Book, Offer, BreadcrumbList), más allá de «parsea» | https://github.com/ajv-validator/ajv |
| 1 | html-validate | HTML | MIT | HTML inválido en las plantillas, que hoy no comprueba nadie | https://gitlab.com/html-validate/html-validate |
| 1 | osv-scanner + zizmor + actionlint + gitleaks | seguridad | Apache/MIT | auditoría semanal; issue solo con hallazgos NUEVOS | https://github.com/google/osv-scanner |
| 1 | IndexNow + GSC URL Inspection + CrUX API | indexado y rendimiento real | gratis (API) | avisa al buscador de las novedades del día; mide el INP y el LCP reales | https://www.indexnow.org/ |
| 2 | Unlighthouse | rendimiento/SEO | MIT | Lighthouse de todo el sitio, no solo de la muestra | https://github.com/harlan-zw/unlighthouse |
| 2 | Linkinator | enlaces | MIT | respaldo de Lychee, con el crawl desde la portada | https://github.com/JustinBeckwith/linkinator |
| 2 | Semgrep CE | estático | LGPL | reglas propias (p. ej., no meter el tag de Amazon a mano) | https://github.com/semgrep/semgrep |
| 2 | Renovate | dependencias | AGPL (app gratuita) | actualiza Actions y npm con PR agrupadas | https://github.com/renovatebot/renovate |
| 2 | Upptime / Gatus | disponibilidad | MIT/Apache | uptime desde Actions, con historial público | https://github.com/upptime/upptime |
| 2 | changedetection.io | vigilancia | Apache | cambios en las guías de Google o OpenAI, que avisan al investigador | https://github.com/dgtlmoon/changedetection.io |
| 3 | GitHub Agentic Workflows (gh-aw) | agentes | MIT | agentes en Actions con safe-outputs y modo staged; cierra el hueco del PC apagado | https://github.com/github/gh-aw |
| 3 | IBM Equal Access / Testaro | accesibilidad | Apache/MIT | segunda opinión, distinta de pa11y y axe | https://github.com/IBMa/equal-access |
| 3 | Browsertime | rendimiento | MIT | vídeos y métricas por página crítica | https://github.com/sitespeedio/browsertime |
| 3 | textlint (es) / LanguageTool | texto | MIT/LGPL | ortografía y estilo de las fichas en español | https://github.com/textlint/textlint |

Descartados por ahora:
- De pago o con cuota baja: Better Stack, StatusCake, Sentry SaaS.
- Si no hay PC encendido: todo lo que necesita un servidor propio (Uptime Kuma, GlitchTip, Huginn).
- Sin licencia verificada o de muy poco uso: las Actions de marketplace de la ronda 8.

Las guías de la ronda 6 (Google sobre la IA generativa, el INP de web.dev, WCAG 2.2/ACT y Baymard sobre las fichas y los filtros) pasan al prompt del investigador como fuentes. Se convierten en reglas comprobables, no en normas.

## Hueco abierto

Cubierto en parte por el turno de issues (#1374): el turno local de `night-autorepair.py` toma cada hora una issue `fallo` (primero) o `experto`, como mucho 3 al día. Abre la PR con las credenciales locales, así que la CI sí se dispara. Espera a los bots y corrige sus hilos (2 veces como mucho). Fusiona sin `--admin` y nunca durante la carga. Si no puede, cierra y etiqueta `necesita-david`.

Sigue abierto: si el PC está apagado, nadie consume las issues. Hacerlo desde Actions necesita un PAT o una app, porque las PR creadas con GITHUB_TOKEN no disparan la CI. Está en las preguntas de Fable, ronda 4.
