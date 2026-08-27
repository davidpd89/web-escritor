# 15 — Qué no instalar y anti-patrones

## 1. “Instala todo lo que tenga cinco estrellas”

REJECT.

Más plugins implican:

- más instructions/tools en contexto;
- más supply chain;
- más auth;
- más posibilidades de tool confusion;
- más updates;
- más superficies de prompt injection.

El objetivo es un **toolchain**, no una colección.

## 2. Tres browser MCP a la vez

Chrome DevTools + Playwright ya cubren inspección y journeys. BrowserStack añade real devices.

No añadir Browser Use, Browserbase, Puppeteer MCP y otros salvo un caso único demostrado.

## 3. Cinco scanners de seguridad

Security Guidance + tests + un security review on-demand + como máximo un scanner determinista adicional en pilot.

No Semgrep + Sonar + Aikido + Snyk + CodeQL + Claude Security solo porque todos existan. Si GitHub ya aporta una capa nativa, contarla en la matriz antes de sumar otra.

## 4. Dos product analytics suites

No PostHog + Amplitude + Clarity + GA + session replay “para tener más datos”. Toda telemetría debe justificar una decisión y privacy cost.

## 5. Plugin de “SEO score” como autoridad

REJECT.

No permitir que un score opaco anule:

- Google Search docs;
- Search Console real;
- source of truth;
- people-first content;
- performance real.

## 6. Plugin de diseño como director de arte

Frontend Design/Figma/Canva no reciben el prompt “mejora toda la web”.

No:

- bento por defecto;
- cards uniformes;
- gradients “premium”;
- glass;
- blobs;
- pills;
- fake grain;
- stock/AI archive;
- three-column features porque el plugin lo propone.

La herramienta genera/representa hipótesis; los contratos y evidencia gobiernan.

## 7. Generadores de UI/templates que sustituyen el código real

No introducir builders/low-code o una nueva framework solo porque un plugin genera pantallas más rápido. La web ya es un sistema estático deliberado.

Cualquier cambio de framework sería una decisión de arquitectura independiente con migración/SEO/perf/accessibility, no “tooling”.

## 8. MCP propio para todo

REJECT.

No construir servidor MCP para:

- leer JSON local;
- ejecutar un test;
- consultar un fichero;
- invocar un script;
- aplicar un checklist.

Skill/CLI/script primero.

## 9. API key porque la docs la menciona

REJECT.

Ejemplos:

- Context7 funciona sin key → empezar así.
- PSI puede usarse puntualmente sin key → no crearla si no automatizamos.
- BrowserStack remoto usa OAuth → no guardar access key si remote satisface.
- Figma remoto usa OAuth → no PAT por comodidad.

## 10. Secret en `.mcp.json`

BLOCK.

También bloqueado en:

- `.claude/settings*.json` versionado;
- markdown;
- `tools-catalog.json`;
- PR body;
- screenshots;
- sample commands con valor real.

## 11. `settings.local.json` versionado

El repo ya tiene este problema. No repetirlo al incorporar plugins.

“local” significa específico del usuario/máquina y debe salir de Git salvo una razón excepcional documentada; las políticas compartidas se modelan aparte.

## 12. Auto-update ciego de high-privilege plugin

No asumir que “ya confié una vez” significa aceptar para siempre nuevas hooks/tools/scopes. Revisar releases/cambios materiales.

## 13. Copiar un `npx` de Reddit/blog

REJECT.

Todo MCP local:

- package exacto;
- vendor/repo oficial;
- docs primaria;
- node requirement;
- auth;
- revisión de command.

## 14. Browser agent autenticado en todo

REJECT.

No usar perfil con Gmail, banca, admin panels, Figma personal, Cloudflare y navegación aleatoria simultáneamente. Separar research de operación.

## 15. Claude en Chrome como “QA completo”

No. Puede observar/interactuar, pero:

- no sustituye Playwright reproducible;
- no sustituye BrowserStack real devices;
- no sustituye a11y automation/manual;
- está expuesto a prompt injection de páginas.

## 16. Visual regression = diseño correcto

No. Un diff solo dice que algo cambió. Puede preservar un diseño mediocre para siempre.

Baseline se actualiza únicamente tras decisión visual consciente.

## 17. Lighthouse 100 = web excelente

REJECT.

Scores no miden dirección de arte, comprensión, posicionamiento, voz editorial ni toda la accesibilidad. Además el repo ya usa LHCI.

## 18. CrUX = diagnóstico instantáneo

No. CrUX es agregado/histórico y depende de muestra. No usarlo para decir “el commit de ayer empeoró LCP” sin diseño de análisis.

## 19. Axe/Pa11y/WAVE = accesibilidad completa

No scanner automatizado cubre:

- orden mental/focus útil;
- calidad de alt;
- facilidad cognitiva;
- screen reader UX completa;
- motion experience;
- touch ergonomics;
- claridad de copy.

Automated zero violations ≠ WCAG/UX completa.

## 20. Figma = navegador

No.

No valida:

- CSS cascade;
- browser chrome;
- keyboard;
- actual DOM order;
- loading;
- responsive content overflow;
- real fonts fallback;
- runtime interaction.

## 21. Canva = web design system

No. Usarlo para media/brand/social si aporta; no trasladar templates Canva a layout web.

## 22. LSP = tests

No. TypeScript/Pyright detectan clases de errores estáticos. Ejecutar tests sigue siendo obligatorio.

## 23. Code Review agents = CI

No. Un reviewer puede interpretar diff y hallar bugs; checks reproducibles siguen siendo contrato.

## 24. Code Simplifier sobre CSS completo

REJECT.

La aparente duplicación puede ser una compensación responsive necesaria. Solo simplificar con visual/browser regression.

## 25. Superpowers/Feature Dev para un fix de 3 líneas

REJECT como default. Elegir ceremonia proporcional al riesgo.

## 26. Claude Code Setup como installer automático

No. Es meta-auditor read-only. Sus recomendaciones vuelven al inventario/pilot.

## 27. Persistir todos los learnings

REJECT. `CLAUDE.md` no es un log. Solo conocimiento estable, accionable y no duplicado.

## 28. Firecrawl/Exa como fuente de verdad

No. Son retrieval/research. Verificar fuente primaria. No inferir facts de snippets agregados.

## 29. Copiar diseño de referencia

REJECT.

Extraer:

- principio;
- problema;
- mecanismo;
- tradeoff.

No copiar composición, marca o estética identificable.

## 30. Comprar SaaS por un plugin atractivo

No. Plugin disponible ≠ producto necesario.

Casos:

- Sentry solo tras necesidad real de error observability;
- PostHog solo tras decisión product analytics/privacy;
- axe paid solo si el pilot aporta valor incremental;
- BrowserStack plan solo si real-device QA lo justifica.

## 31. Activar tracking para que Claude “sepa más”

REJECT sin PR de privacidad/product analytics.

## 32. Herramienta que auto-fixea todo

No ejecutar:

- `stylelint --fix` masivo;
- HTML validator auto-fix masivo;
- accessibility auto-remediation masiva;
- “fix all” de scanner;

sin revisar diff y semantics.

## 33. Formatear código como proyecto de mejora

No mezclar formatter churn con cambio funcional/visual. Hace peor la revisión.

## 34. Plugin que requiere cambiar framework

Default REJECT. El plugin debe adaptarse al stack; el stack no cambia para acomodar el plugin.

## 35. Plugin que duplica una tool nativa de Claude sin ventaja

Ejemplo conceptual: otro filesystem/search tool sin semantics nuevas. No aporta.

## 36. API de screenshot redundante

Chrome/Playwright ya capturan. Solo adoptar un SaaS si aporta devices/histórico/diff/infra que no tenemos.

## 37. Icon/stock/AI asset APIs

No como capacidad base. El contrato V1 exige materialidad real y assets con provenance. No rellenar la web por disponibilidad de API.

## 38. “Prompt engineering plugin” genérico

REJECT salvo que aporte evals/skills concretos. El proyecto necesita evidencia, no prompts ornamentales.

## 39. Autonomía de merge/deploy

Bloqueada por política. Ningún plugin puede cambiar esa regla.

## 40. Tool selection por fama

Installs/stars/popularidad solo indican adopción, no fit. La decisión se basa en capability gap.

## 41. Tool selection por una demo

Una demo de proveedor muestra happy path. Pilot propio obligatorio para cuentas/paid tools.

## 42. Mezclar research y operación con privilegios altos

Separar sesiones/permissions. Especialmente si se navegan sitios desconocidos.

## 43. Copiar settings de otro IDE

VS Code, Claude Code, Cursor, Claude Desktop tienen formats/scopes distintos. Seguir la guía específica del cliente actual.

## 44. Mantener pilotos eternos

Todo `PILOT` tiene fecha/criterio de promoción o retirada. Si no produce evidencia, se cierra.

## 45. No actualizar esta documentación

También es anti-patrón. El ecosistema Claude/MCP está cambiando rápido en 2026. Un comando correcto hoy puede quedar obsoleto.

Antes de instalar tras varios meses: revalidar `14-FUENTES...`.

## Pregunta final de admisión

> Si quitamos esta herramienta, ¿qué pregunta importante sobre la web deja de poder responder Claude con suficiente calidad?

Si la respuesta es “ninguna, pero es cómoda/interesante”, no entra en el stack estable.