# 01 — Inventario y decisiones

## Leyenda

- **INSTALL_NOW**: alta relación valor/ruido, encaja directamente con este repo y puede permanecer disponible.
- **PILOT**: probar en una tarea acotada antes de consolidar.
- **ON_DEMAND**: útil, pero habilitar solo para la tarea que lo necesita.
- **DEFER**: capacidad real cuyo coste, privacidad, plan o complejidad no se justifican hoy.
- **REJECT**: solapa otra capacidad mejor o empuja un patrón que no queremos.

La clasificación no mide la calidad general del producto; mide su encaje **hoy** con `web-escritor`.

## Stack de decisión

| Herramienta | Tipo | Estado | Aporta aquí | Razón principal |
|---|---|---:|---|---|
| Modern Web Guidance | Claude plugin / Skill | **INSTALL_NOW** | estándares web actuales | Evita que Claude implemente APIs/patrones web obsoletos; funciona offline y sin key |
| Chrome DevTools | Claude plugin / MCP | **INSTALL_NOW** | navegador real, DOM, CSS, red, performance | Convierte opiniones sobre UI en observaciones medibles |
| Playwright | Claude plugin / MCP | **INSTALL_NOW** | interacción/browser QA reproducible | Complementa el Playwright de CI con exploración agentic; no sustituye tests versionados |
| GitHub | Claude plugin / MCP | **INSTALL_NOW** | PR/issues/actions/repo | Claude trabaja ya continuamente sobre GitHub |
| Security Guidance | Claude plugin / hook | **INSTALL_NOW** | prevención temprana de XSS/injection | Muy bajo coste y útil en HTML/JS/Actions |
| TypeScript LSP | Claude plugin / LSP | **INSTALL_NOW** | navegación y diagnósticos JS/MJS | El repo tiene bastante JS aunque no sea TS |
| Pyright LSP | Claude plugin / LSP | **INSTALL_NOW** | diagnósticos Python | El repo tiene numerosos scripts/tests Python |
| CLAUDE.md Management | Claude plugin | **INSTALL_NOW** | memoria técnica gobernada | Proyecto largo, muchos contratos y gotchas |
| Skill Creator | Claude plugin | **INSTALL_NOW** | crear/evaluar skills propias | Permite convertir criterios del proyecto en capacidades medibles |
| Hookify | Claude plugin | **INSTALL_NOW** | guardrails locales | Puede bloquear direct-main, secretos, deploy accidental, etc. |
| PR Review Toolkit | Claude plugin | **INSTALL_NOW** | revisión local especializada | Útil antes de pedir revisión remota; seis agentes concretos |
| Claude Code Setup | Claude plugin | **ON_DEMAND** | meta-auditor read-only | Ejecutar tras cambios grandes o trimestralmente; no dejarlo decidiendo el stack continuamente |
| Frontend Design | Claude plugin | **PILOT** | alternativas visuales no genéricas | Buen generador de hipótesis, pero nunca autoridad de diseño |
| Figma | Claude plugin + MCP | **PILOT** | contexto/tokens/canvas/design↔code | Alto valor cuando exista laboratorio Figma operativo |
| Playground | Claude plugin | **PILOT** | prototipos aislados | Experimentar motion/layout/data sin tocar producción |
| BrowserStack MCP | MCP remoto/local | **PILOT** | Safari/iOS/Android/dispositivos reales | Cierra el gap que emulación Chromium no puede cerrar |
| axe Accessibility | plugin + MCP Deque | **PILOT** | análisis/remediación especializada | Aporta conocimiento Deque, pero requiere plan; Pa11y ya existe |
| Stark connector | connector/MCP | **PILOT/MONITOR** | diseño+URL+source accessibility | Recién lanzado en 2026; verificar disponibilidad/plan de Claude Code antes de adoptar |
| Cloudflare | plugin + Skills/MCP | **ON_DEMAND** | Workers/Wrangler/performance | Relevante, pero de alto privilegio; lectura/diagnóstico por defecto |
| Context7 | plugin/MCP | **INSTALL_NOW** | documentación versionada | Reduce alucinaciones sobre APIs/librerías; anónimo funciona sin key |
| Feature Dev | Claude plugin | **ON_DEMAND** | cambios grandes en fases | Excelente para features grandes; burocrático para CSS/fix pequeño |
| Superpowers | Claude plugin | **PILOT** | debugging/TDD/subagents | Potente, pero puede duplicar workflows propios; probar antes de dejar always-on |
| Code Simplifier | Claude plugin | **ON_DEMAND** | claridad tras cambios | Bien para JS/Python; riesgo de “simplificar” CSS artesanal intencional |
| Code Review | Claude plugin | **PILOT** | revisión multiagente | Solapa parcialmente PR Review Toolkit; comparar resultados antes de mantener ambos |
| Claude Security | Claude plugin | **ON_DEMAND** | security review adversarial | Útil antes de releases/cambios sensibles, no en cada microcambio |
| Semgrep | Claude plugin/integration | **PILOT** | scanner determinista | Candidato si queremos una segunda capa SAST; elegirlo frente a Sonar/Aikido, no sumarlos |
| SonarQube | plugin/MCP | **DEFER** | quality/security platform | Requiere servicio/proyecto; excesivo mientras CI propio cubra el repo |
| Aikido Security | plugin/MCP | **DEFER** | SAST/secrets/IaC | Mismo problema de scanner soup; no hay necesidad actual demostrada |
| Serena | MCP | **PILOT** | búsqueda/refactor semántico | Puede ayudar JS/Python; menor rendimiento esperado en HTML/CSS dominante |
| Sourcegraph | MCP/integration | **DEFER** | navegación multi-repo | Sobrepotenciado para un único repo pequeño/mediano |
| Greptile | reviewer/API | **DEFER** | revisión externa | Solapa Code Review/PR Toolkit/GitHub; añade tercero y credencial |
| CodeRabbit | reviewer/CLI | **PILOT opcional** | revisión externa independiente | Solo A/B contra nuestro stack; no usar simultáneamente con varios reviewers SaaS |
| Firecrawl | plugin/MCP/API | **PILOT** | investigación/crawl de referencias | Útil para investigación estructurada; no copiar diseños ni scrapear indiscriminadamente |
| Exa | plugin/MCP/API | **PILOT** | investigación web profunda | Complementario para fuentes; mantener si supera al web search habitual en pruebas reales |
| SearchFit SEO | plugin tercero | **DEFER** | checks SEO secundarios | Las PR SEO/Search Console ya tienen autoridad primaria; ningún “SEO score” manda |
| PostHog | plugin/MCP | **DEFER** | analytics/experiments/session data | Supone nueva plataforma y decisión de privacidad; no instalar por curiosidad |
| Amplitude | plugin/MCP | **DEFER** | product analytics | Mismo solapamiento; no somos una app SaaS que necesite dos suites de producto |
| Sentry | plugin/MCP | **DEFER** | errores/runtime | Sitio estático; introducir Sentry solo si errores reales justifican tracking/SDK |
| Browser Use | MCP/browser cloud | **REJECT ahora** | browser automation | Chrome DevTools + Playwright + BrowserStack cubren mejor nuestras capas |
| Commit Commands | Claude plugin | **DEFER** | commit/push/PR | Claude ya tiene Git/GitHub; puede erosionar staging explícito y branch discipline |
| Remember | Claude plugin/hooks | **DEFER** | memoria automática | Ya existe documentación extensa; añade coste/contexto y persistencia difícil de gobernar |
| Adobe for Creativity | Claude plugin | **PILOT** | edición/vector/retouch | Interesante para assets reales; evaluar si hay licencia/flujo Adobe, no para layout web |
| Canva | Claude plugin/MCP | **PILOT** | social/press/media/brand check | Útil para piezas de campaña; no autoridad de diseño web |
| 42Crunch API Security | plugin | **DEFER** | OpenAPI/API security | No tenemos una API OpenAPI que justifique su stack hoy |
| Airtable | plugin/MCP | **DEFER** | ops database | Puede ser útil en outreach/editoriales, pero no mejora esta web directamente ahora |
| Plugin Developer Toolkit | Claude plugin | **ON_DEMAND** | construir plugin propio | Instalar mientras creemos/mantengamos `david-porto-web` plugin |
| MCP Server Dev | Claude plugin | **ON_DEMAND** | crear MCP propio | Solo si una necesidad no puede resolverse con Skills/hooks/CLI; evitar servidor por moda |

## Qué instalaría en una estación nueva de Claude Code

### Núcleo estable

1. Modern Web Guidance.
2. Chrome DevTools.
3. Playwright.
4. GitHub.
5. Security Guidance.
6. TypeScript LSP.
7. Pyright LSP.
8. CLAUDE.md Management.
9. Skill Creator.
10. Hookify.
11. PR Review Toolkit.
12. Context7.

Esto ya cubre: navegador, pruebas, repo, seguridad preventiva, JS, Python, memoria, skills, guardrails, revisión y documentación actual.

### Se habilitan cuando empieza una fase concreta

- Figma → diseño/redlines/design-to-code.
- Frontend Design → hipótesis visuales.
- BrowserStack → validación real-device.
- axe/Stark → piloto de capa especializada de accesibilidad.
- Cloudflare → Worker/runtime/diagnóstico.
- Claude Security/Semgrep → security gate de cambios sensibles.
- Firecrawl/Exa → investigación de referencias.
- Canva/Adobe → assets y piezas externas.

## Qué NO significa `INSTALL_NOW`

No significa “dar permiso ilimitado”. Un plugin puede estar instalado y su MCP no autenticado, o puede estar deshabilitado salvo uso. La disponibilidad debe separarse de la autorización.

Ejemplos:

- GitHub: lectura amplia puede ser cotidiana; merge sigue siendo acción deliberada.
- Cloudflare: puede leer docs/config; deploy/secret mutation bloqueados.
- BrowserStack: OAuth con permisos de la cuenta; no subir builds/artefactos sensibles sin necesidad.
- Figma: comenzar leyendo un fichero/lab específico; no permitir modificaciones masivas a archivos de equipo.

## Regla contra el “plugin soup”

Antes de añadir una herramienta nueva, Claude debe responder cinco preguntas:

1. ¿Qué fallo concreto resuelve que el stack actual no resuelva?
2. ¿Qué evidencia producirá que podamos conservar/revisar?
3. ¿Qué permisos o datos nuevos recibe?
4. ¿Qué herramienta existente solapa?
5. ¿Qué condición hará que la desinstalemos?

Si no puede contestarlas, no se instala.