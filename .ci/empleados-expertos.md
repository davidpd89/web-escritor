# Equipo de expertos automáticos

Esta lista está viva. La mantiene Opus y la lee cada experto antes de proponer nada, para no repetir lo que ya cubre otro.

Cada miembro sigue el mismo esquema:
- **Herramientas deterministas**: miden y pueden bloquear.
- **Experto LLM**: lee lo que han medido, propone y abre issues `experto`.
- **Revisores de PR**: comentan las PR; sus avisos bloquean la fusión, que es manual.

Todo es gratuito. El LLM de los expertos es **GitHub Models** (`openai/gpt-4.1`, con `gpt-4.1-mini` de respaldo), que se paga con el `GITHUB_TOKEN` del run (`models: read`): unas 50 peticiones diarias gratis y aquí se usa 1. Claude queda solo para emergencias (atascos y bloqueos en `night-autorepair.py`), nunca como revisor en bucle (decisión de David del 15/11).

## Plantilla (nombres)

| Puesto | Nombre | Quién es en realidad | Cuándo |
|---|---|---|---|
| Arquitecta | **Alba** | experto `arquitecto` (GitHub Models) + Fable en las sesiones de dirección | sábados + sesiones |
| Investigador | **Iker** | experto `investigador`: busca en GitHub repos activos y los compara con esta lista | lunes |
| SEO / Google | **Sara** | SiteOne Crawler + experto `seo` | martes |
| Posicionamiento en IA (GEO) | **Gael** | `empleados_expertos.py geo` (robots, llms.txt, JSON-LD) + experto `geo` | miércoles |
| UX | **Úrsula** | muestra de 40 URL + experto `ux`; pa11y y axe miden la accesibilidad | jueves |
| Rendimiento (frontend) | **Rita** | SiteOne con recursos, Lighthouse CI, presupuestos + experto `rendimiento` | viernes + cada PR |
| Tester automático | **Tomás** | pytest, smoke y QA de navegador en cada PR + experto `tester` (código sin test) | cada PR + domingos |
| Tester manual | **Marta** | QA de navegador real (`*-browser-qa.yml`) y pa11y sobre producción; la «mano» humana es David cuando quiere | diario |
| Seguridad | **Sergio** | zizmor, pip-audit y gitleaks (`security-weekly-audit.yml`), CodeQL + experto `seguridad` (cabeceras, ficheros sensibles, bots de IA) | domingos |
| Revisores de código | **Coral**, **Óscar**, **Diego**, **Sonia** | CodeRabbit, Codex, DeepSource y SonarCloud en cada PR | cada PR |
| Desarrollador de guardia (backend y frontend) | **Nico** | `night-autorepair.py` y el turno de issues: repara flujos críticos caídos e issues `fallo` | cada hora, solo si algo falla |
| Operaciones | **Olga** | la carga nocturna, precios, portadas, Telegram y deploy (workflows programados) | cada noche |

Los desarrolladores no programan funciones nuevas solos: el código nuevo sale de las sesiones de David con Opus/Fable o de la reparación de guardia.

## Expertos LLM (`empleados-expertos.yml`, 05:17 en Madrid)

| Día | Rol | Datos que prepara el workflow | Salida |
|---|---|---|---|
| lunes | investigador | repos de GitHub activos del último mes por temas (`datos_rol`) | ≤3 issues, una por herramienta |
| martes | seo | SiteOne Crawler v2.5.1 (MIT) sobre 300 URL del sitemap | ≤3 issues |
| miércoles | geo | robots/llms.txt/JSON-LD de 40 URL (`empleados_expertos.py geo`) | ≤3 issues |
| jueves | ux | muestra de 40 URL | ≤3 issues |
| viernes | rendimiento | SiteOne con recursos + `performance-budgets.json` | ≤3 issues |
| sábado | arquitecto | issues `fallo` + `.ci/` + código de la carga | ≤3 issues |
| domingo | tester | scripts que ningún test nombra | ≤3 issues |
| domingo 05:47 | seguridad | cabeceras, bots de IA en robots.txt, ficheros versionados con nombre sensible (`empleados_expertos.py seguridad`) | ≤3 issues |

Para lanzar un rol a mano: `gh workflow run empleados-expertos.yml -f rol=seo`.

Límites:
- el modelo no ejecuta nada: devuelve JSON y el script crea las issues (como mucho 3, sin repetir títulos abiertos, sin menciones @);
- `contents: read`, `issues: write` y `models: read`;
- si GitHub Models no responde, el run sale en rojo y no se gasta nada más.

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
| seguridad | CodeQL, supply chain npm; zizmor, pip-audit y gitleaks con línea base | `codeql.yml`, `npm-supply-chain-watch.yml`, `security-weekly-audit.yml` |
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
