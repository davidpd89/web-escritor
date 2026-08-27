# 13 — Backlog ejecutable Claude Toolbox

## Convenciones

- **P0**: prerequisite/hardening o capacidad de valor inmediato.
- **P1**: siguiente capa tras estabilizar P0.
- **P2**: pilot/optimización.
- **P3**: condicional a escala/cuenta/necesidad.

Actores:

- `CLAUDE-LOCAL`: puede ejecutar en VS Code/local.
- `REPO`: requiere PR.
- `HUMAN`: acción/autorización/selección.
- `ACCOUNT`: login/OAuth/plan/key.
- `CI`: workflow/secret.

No marcar una tarea `DONE` por haber leído su documentación; hay criterion de aceptación.

---

## A. Saneamiento de Claude

### CTB-001 — P0 — REPO
**Dejar de versionar `.claude/settings.local.json`.**

Pasos:
1. inventariar contenido;
2. separar reglas compartibles;
3. añadir local file al `.gitignore`;
4. `git rm --cached` sin borrar copia local del usuario;
5. tests/PR.

Aceptación: main no trackea settings local; no se pierde policy compartida necesaria.

### CTB-002 — P0 — REPO
**Crear `.claude/settings.json` solo con policy de proyecto realmente compartible**, si tras CTB-001 existe alguna.

Aceptación: cero paths de usuario, cero secrets, cero permisos innecesariamente amplios.

### CTB-003 — P0 — CLAUDE-LOCAL/HUMAN
**Revisar permisos `git push`, `gh api *` y Bash genérico.**

Aceptación: minimum privilege compatible con workflow real.

### CTB-004 — P0 — REPO
**Añadir checklist “no secret in Claude config”** al CLAUDE/handoff apropiado.

### CTB-005 — P1 — CLAUDE-LOCAL
**Inventariar plugins/MCP ya instalados** con `/plugins` y `/mcp`.

Aceptación: tabla local/issue sanitizado con source/status, sin tokens.

---

## B. Stack P0

### CTB-010 — P0 — CLAUDE-LOCAL
Instalar `modern-web-guidance@claude-plugins-official`.

Aceptación: responde una consulta Baseline y no requiere key.

### CTB-011 — P0 — CLAUDE-LOCAL
Instalar `security-guidance@claude-plugins-official`.

### CTB-012 — P0 — CLAUDE-LOCAL
Instalar `typescript-lsp@claude-plugins-official`.

Aceptación: encuentra definitions/references de JS real.

### CTB-013 — P0 — CLAUDE-LOCAL
Instalar `pyright-lsp@claude-plugins-official`.

Aceptación: diagnósticos sobre script Python real.

### CTB-014 — P0 — CLAUDE-LOCAL
Instalar `claude-md-management@claude-plugins-official`.

Aceptación: audit read-only de memoria del proyecto; no auto-rewrite.

### CTB-015 — P0 — CLAUDE-LOCAL
Instalar `skill-creator@claude-plugins-official`.

### CTB-016 — P0 — CLAUDE-LOCAL
Instalar `hookify@claude-plugins-official`.

### CTB-017 — P0 — CLAUDE-LOCAL
Instalar `pr-review-toolkit@claude-plugins-official`.

### CTB-018 — P0 — CLAUDE-LOCAL
Instalar `context7@claude-plugins-official` sin API key.

### CTB-019 — P0 — CLAUDE-LOCAL
Verificar P0 en `/plugins`; registrar cualquier plugin que no cargue/renombrado.

---

## C. Browser

### CTB-020 — P0 — CLAUDE-LOCAL
Instalar `chrome-devtools-mcp@claude-plugins-official`.

### CTB-021 — P0 — CLAUDE-LOCAL
Ejecutar protocolo de observación Home 390/1440.

Aceptación: screenshots + geometría + console sin cambios de código.

### CTB-022 — P0 — CLAUDE-LOCAL
Instalar `playwright@claude-plugins-official`.

### CTB-023 — P0 — CLAUDE-LOCAL
Ejecutar journey Home → Manecillas → Back → Explorar.

### CTB-024 — P1 — REPO
Documentar regla: finding browser reproducible de P0/P1 se convierte en test Playwright cuando corresponda.

### CTB-025 — P1 — CLAUDE-LOCAL
Construir matriz de comandos/prompts de browser por familia: home/book/identity/editorial/tools/findability.

---

## D. GitHub/review

### CTB-030 — P0 — CLAUDE-LOCAL
Instalar `github@claude-plugins-official`.

### CTB-031 — P0 — CLAUDE-LOCAL
Validar lectura de PR/checks/diff sin mutación.

### CTB-032 — P1 — CLAUDE-LOCAL
Comparar workflow GitHub plugin vs `gh api *`; reducir shell permission si el plugin cubre la necesidad.

### CTB-033 — P1 — CLAUDE-LOCAL
Pilot PR Review Toolkit en cinco PRs históricos representativos.

### CTB-034 — P2 — CLAUDE-LOCAL
Pilot `code-review@claude-plugins-official` contra mismos PRs.

### CTB-035 — P2 — HUMAN
Elegir política de reviewer principal/secundario según precision/duplication.

### CTB-036 — P2 — CLAUDE-LOCAL
Evaluar CodeRabbit solo si queremos reviewer SaaS independiente después de CTB-035.

---

## E. Guardrails

### CTB-040 — P0 — REPO/CLAUDE-LOCAL
Crear Hookify rule no-direct-main.

### CTB-041 — P0
Crear rule no-secret-in-versioned-file.

### CTB-042 — P0
Crear rule warn/block `wrangler deploy`/production mutation.

### CTB-043 — P0
Crear rule merge requiere autorización.

### CTB-044 — P1
Crear rule UI-change requires relevant QA reminder.

### CTB-045 — P1
Testear falsos positivos y escape de hooks.

Aceptación: hooks ayudan sin bloquear operaciones legítimas de lectura/test.

---

## F. Skills/plugin propio

### CTB-050 — P1 — CLAUDE-LOCAL
Instalar `plugin-dev@claude-plugins-official` durante desarrollo.

### CTB-051 — P1 — REPO
Crear skeleton `david-porto-web` según convención actual validada.

### CTB-052 — P1 — REPO
Crear Skill `observe-live`.

### CTB-053 — P1 — REPO
Crear Skill `mobile-hierarchy-audit`.

### CTB-054 — P1 — REPO
Crear Skill `design-critic`.

### CTB-055 — P1 — REPO
Crear eval dataset con casos positivos/negativos.

### CTB-056 — P1 — CLAUDE-LOCAL
Benchmark skills con Skill Creator vs baseline.

### CTB-057 — P1 — HUMAN
No promover skill si no mejora resultados o añade sesgo.

### CTB-058 — P2 — REPO
Crear `media-art-direction-review` si primeras tres funcionan.

### CTB-059 — P2 — REPO
Crear `public-artifact-review`.

### CTB-060 — P2 — REPO
Crear `factual-parity-review`.

### CTB-061 — P2 — REPO
Crear `pr-final-gate`.

### CTB-062 — P2 — REPO
Version/changelog/plugin docs.

### CTB-063 — P2
Deshabilitar plugin-dev fuera de mantenimiento si añade ruido.

---

## G. Figma/diseño

### CTB-070 — P1 — ACCOUNT
Confirmar cuenta/Figma file/lab a usar.

### CTB-071 — P1 — CLAUDE-LOCAL
Instalar `figma@claude-plugins-official`.

### CTB-072 — P1 — ACCOUNT
OAuth; no PAT si no hace falta.

### CTB-073 — P1
Test read-only frame/tokens/components.

### CTB-074 — P1
Test write únicamente dentro de lab aprobado.

### CTB-075 — P1 — CLAUDE-LOCAL
Pilot `frontend-design@claude-plugins-official` en un problema mobile medido.

### CTB-076 — P1
Instalar/pilot `playground@claude-plugins-official` si ayuda a prototipar sin contaminar repo.

### CTB-077 — P1
Pasar hipótesis por `design-critic`.

### CTB-078 — P1 — HUMAN
Selección humana antes de implementación visual mayor.

### CTB-079 — P2
Instalar Canva plugin solo para media/social/press workflow real.

### CTB-080 — P2
Pilot Adobe for Creativity si existe licencia y necesidad de retouch/vectorization.

---

## H. Real device y visual regression

### CTB-090 — P1 — ACCOUNT
Abrir/confirmar BrowserStack plan/trial.

### CTB-091 — P1
Conectar MCP remoto OAuth `https://mcp.browserstack.com/mcp`.

### CTB-092 — P1
Ejecutar matriz 10 escenarios iOS/Android.

### CTB-093 — P1
Registrar issues que no detecta emulación local.

### CTB-094 — P2 — HUMAN
Decidir adopción BrowserStack por valor observado.

### CTB-095 — P2
Pilot Percy si BrowserStack se consolida.

### CTB-096 — P2
Alternativamente pilot Chromatic+Playwright; no mantener ambos inicialmente.

### CTB-097 — P2 — REPO
Visual regression baselines solo para páginas/estados críticos.

---

## I. Accesibilidad especializada

### CTB-100 — P2 — ACCOUNT
Comprobar plan/coste axe DevTools Bundle.

### CTB-101 — P2
Conectar axe plugin/MCP por OAuth en una prueba.

### CTB-102 — P2
Comparar findings vs Pa11y + manual.

### CTB-103 — P2
Comprobar Stark connector availability/plan actual.

### CTB-104 — P2
A/B axe vs Stark solo si ambas son accesibles.

### CTB-105 — P2 — HUMAN
Elegir máximo una capa especializada pagada adicional, o ninguna.

### CTB-106 — P2
Instalar WAVE browser extension para revisión humana local si se desea; no necesita API.

---

## J. Seguridad

### CTB-110 — P1
Instalar Claude Security ON_DEMAND para cambios sensibles.

### CTB-111 — P2
Pilot Semgrep sobre baseline sin CI.

### CTB-112 — P2
Clasificar findings/falsos positivos.

### CTB-113 — P2
Añadir Semgrep CI solo si aporta findings únicos relevantes.

### CTB-114 — P3
Comparar Sonar/Aikido solo si Semgrep no cubre un requisito real.

### CTB-115 — P0
Auditar source/updates de todo plugin high privilege.

---

## K. Cloudflare

### CTB-120 — P1 — CLAUDE-LOCAL
Añadir marketplace `cloudflare/skills` cuando haya tarea Cloudflare.

### CTB-121 — P1
Instalar plugin Cloudflare.

### CTB-122 — P1
Primera prueba docs/read/local only.

### CTB-123 — P1
Verificar Hookify deploy guard.

### CTB-124 — P1 — HUMAN
Cualquier write/deploy production requiere instrucción explícita.

### CTB-125 — P2
Si hace falta token, crear identidad read-only/mínimo scope; no global key.

---

## L. Research

### CTB-130 — P2
Pilot Firecrawl en un benchmark concreto de 10 sitios/referencias.

### CTB-131 — P2
Crear key solo al iniciar pilot.

### CTB-132 — P2
Pilot Exa en 20 queries difíciles.

### CTB-133 — P2
Elegir 0/1/ambos solo si aportan fuentes mejores que web search.

### CTB-134 — P2
Documentar anti-copy/provenance de research visual.

---

## M. APIs/validadores

### CTB-140 — P1 — REPO
Pilot W3C Nu validation sobre public artifact.

### CTB-141 — P2
Comparar HTML-Validate vs W3C antes de añadir dependency.

### CTB-142 — P2
Ejecutar Stylelint read-only sobre CSS V1 y clasificar findings.

### CTB-143 — P2
Adoptar solo rules que detecten bugs/robustez, no formatting churn.

### CTB-144 — P2 — ACCOUNT
Crear CrUX API key solo cuando exista script/dashboard definido.

### CTB-145 — P2 — REPO
Script CrUX origin/PHONE histórico, si hay datos.

### CTB-146 — P2
Usar PSI API solo para diagnóstico puntual; no duplicar LHCI.

### CTB-147 — P3
WebPageTest key/pilot solo para problema de waterfall/filmstrip no resuelto.

### CTB-148 — P3
WAVE API solo si existe gap frente a Pa11y/axe.

---

## N. Analytics/monitoring opcional

### CTB-150 — P3
No instalar PostHog/Amplitude/Sentry plugins hasta que el producto esté realmente adoptado.

### CTB-151 — P3
Si surge necesidad de session replay/experiments/errors, abrir PR de producto/privacy separada antes de integrar SDK.

### CTB-152 — P3
No activar Clarity/tracking por recomendación de esta toolbox.

---

## O. Mantenimiento

### CTB-160 — P1
Ejecutar `claude-code-setup` tras consolidar P0 y guardar solo recomendaciones justificadas.

### CTB-161 — P2
Repetir trimestral o tras cambio grande de stack.

### CTB-162 — P1
Actualizar `tools-catalog.json` tras cada instalación/promoción/deprecación.

### CTB-163 — P1
Revisión mensual de `/plugins` y `/mcp` high privilege.

### CTB-164 — P1
Revisar auto-updates/changelog de plugins con account write/deploy.

### CTB-165 — P2
Deshabilitar plugins no usados 60–90 días salvo P0 de bajo coste.

### CTB-166 — P2
Rotar/revocar credenciales de pilots abandonados.

### CTB-167 — P2
Registrar incidents/false positives/tool failures en catálogo/changelog.

### CTB-168 — P2
Revalidar endpoints/comandos de esta documentación antes de una instalación meses después del corte 2026-08-27.

---

## Orden recomendado para Claude

```text
001–005
→ 010–019
→ 020–025
→ 030–045
→ 050–063
→ 070–078
→ 090–097
→ 100–106
→ resto por necesidad
```

No avanzar a SaaS/keys porque el backlog tenga una tarea: la dependencia (`ACCOUNT`, caso de uso real, pilot) manda.

## Definition of Done global

- P0 instalado y probado;
- settings locales fuera de Git;
- guardrails activos;
- browser evidence workflow funcionando;
- al menos tres Skills propias benchmarkeadas o descartadas con evidencia;
- Figma/BrowserStack/axe solo adoptados si pilots aportan valor;
- ningún secreto en repo;
- ningún nuevo tracker en producción;
- `tools-catalog.json` refleja estado real;
- Claude sabe tanto **qué usar** como **qué no usar**.