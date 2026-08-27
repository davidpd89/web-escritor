# 03 — Stack P0 que Claude debe instalar

## Propósito

Este es el stack mínimo recomendado para una estación de Claude Code que vaya a trabajar de forma habitual en `web-escritor`. No incluye Figma, BrowserStack ni Cloudflare porque esos se activan por fase/cuenta. El P0 debe poder permanecer instalado sin convertir cada sesión en una consola con cien tools.

## Preflight

Antes de instalar:

```bash
claude --version
node --version
npm --version
git status
```

Después revisar:

```text
/plugins
/mcp
```

Y corregir el problema de `settings.local.json` versionado mediante una PR separada antes de introducir secretos.

---

## P0-01 — Modern Web Guidance

```bash
claude plugin install modern-web-guidance@claude-plugins-official
```

### Por qué aquí

Google Chrome mantiene el plugin con conocimiento actualizado de 102 features y 129 casos de uso web, incluyendo CSS/layout, HTML/DOM, JS/APIs, forms, accessibility y performance. No exige API key; usa búsqueda offline.

Este repo es estático y deliberadamente prioriza plataforma web nativa. Por tanto es un fit especialmente alto: Claude puede consultar Baseline/progressive enhancement antes de añadir una dependencia o un polyfill innecesario.

### Uso

```text
/modern-web-guidance container queries
/modern-web-guidance view transitions
/modern-web-guidance responsive images
```

O simplemente pedir una implementación; la skill puede activarse cuando el tema aplica.

### Guardrail

No adoptar una API nueva solo porque sea moderna. Debe pasar soporte + progressive enhancement + accesibilidad + rendimiento + contrato V1.

### Telemetría

Si se quiere desactivar la telemetría anónima documentada por el plugin:

```bash
set DISABLE_TELEMETRY=1
```

o equivalente persistente/local; nunca hace falta guardarlo como secreto.

---

## P0-02 — Chrome DevTools MCP

```bash
claude plugin install chrome-devtools-mcp@claude-plugins-official
```

### Por qué

Aporta 29 tools de navegador: navegación, interacción, screenshots, DOM snapshots, JS evaluation, console, network, performance traces, memory, Lighthouse y datos CrUX cuando estén disponibles.

### Uso obligatorio antes de opinar de UI

Ejemplos:

- “Abre `/autor.html` a 390×844. Mide H1, primera imagen, distancias entre secciones y altura visible. No propongas cambios todavía.”
- “Compara `/` y `/libros/` en 390 px: inventaría patrones de separación, densidad y media.”
- “Graba trace de Manecillas y separa problemas de rendering de problemas de diseño.”

### Regla

Primero observar, luego proponer. No usar `evaluate_script` para mutar producción.

---

## P0-03 — Playwright

```bash
claude plugin install playwright@claude-plugins-official
```

### Por qué

El MCP de Microsoft opera sobre la accessibility tree y es especialmente bueno para interacción determinista, formularios, navegación, assertions y reproducción de journeys.

El repo ya tiene `playwright@1.62.1` en `package.json`. Eso **no hace redundante** el plugin: uno es dependency de CI y tests versionados; el otro es una interfaz agentic para explorar. Tampoco autoriza al plugin a cambiar el lockfile.

### División con Chrome DevTools

- Chrome DevTools → inspección, CSS/DOM, traces, red, performance, visual debugging.
- Playwright → journeys, interactions, assertions, reproducibilidad y convertir un hallazgo en test.

### Cierre correcto

Hallazgo exploratorio importante → reproducir → escribir test Playwright normal en el repo → CI.

---

## P0-04 — GitHub

```bash
claude plugin install github@claude-plugins-official
```

### Por qué

Fuente directa de PR, issues, reviews, Actions, búsquedas y estado real. Reduce el patrón de copiar logs manualmente a Claude.

### Permiso

Comenzar read-first. Crear branch/commit/PR cuando la tarea lo exija. Merge y acciones destructivas siguen siendo decisiones explícitas.

---

## P0-05 — Security Guidance

```bash
claude plugin install security-guidance@claude-plugins-official
```

### Por qué

Hook preventivo Anthropic Verified sobre patrones como XSS (`innerHTML`), command injection en Actions/shell, `eval`, child process inseguro, pickle/os.system, etc.

Es barato porque trabaja antes de escribir. No sustituye security review ni CSP QA.

### Fit concreto

- HTML/JS sin framework → XSS DOM sigue siendo relevante.
- muchos GitHub Actions → expressions/shell injection es relevante.
- Workers → input validation/headers/secret handling.

---

## P0-06 — TypeScript LSP

```bash
claude plugin install typescript-lsp@claude-plugins-official
```

Aunque el sitio no sea TypeScript, el LSP soporta `.js`, `.mjs`, `.cjs`, etc. Aporta definitions, references y diagnostics.

Usarlo antes de refactors de `script.js`, assistant modules, Workers o builders JS.

---

## P0-07 — Pyright LSP

```bash
claude plugin install pyright-lsp@claude-plugins-official
```

El repo tiene muchos scripts/tests Python. Pyright aporta diagnósticos y type inference sin ejecutar los scripts.

No exigir que todo Python antiguo se convierta a typed Python como condición artificial. Se utiliza para descubrir errores y guiar refactors.

---

## P0-08 — CLAUDE.md Management

```bash
claude plugin install claude-md-management@claude-plugins-official
```

### Por qué

El proyecto acumula contratos técnicos, decisiones visuales, launch gates, fuentes de verdad y reglas de publicación. Sin mantenimiento, `CLAUDE.md` acaba enorme, contradictorio u obsoleto.

### Rutina

- tras una fase grande: `/revise-claude-md`;
- periódicamente: audit de calidad;
- solo incorporar learnings estables, nunca un diario de sesión.

### Regla

No duplicar dentro de `CLAUDE.md` las 15 guías extensas: debe enlazar/condensar lo operativo.

---

## P0-09 — Skill Creator

```bash
claude plugin install skill-creator@claude-plugins-official
```

### Por qué

Es la pieza que transforma nuestros contratos en comportamiento evaluable. Incluye Create/Eval/Improve/Benchmark y agentes Executor/Grader/Comparator/Analyzer.

### Primeras skills propias candidatas

- `david-mobile-hierarchy-audit`;
- `david-design-critic`;
- `david-public-artifact-review`;
- `david-book-fact-parity-review`;
- `david-pr-final-gate`.

Cada una con casos de evaluación positivos y negativos. Ejemplo: el design critic debe rechazar tanto un layout genérico IA como una propuesta “creativa” que rompa jerarquía móvil.

---

## P0-10 — Hookify

```bash
claude plugin install hookify@claude-plugins-official
```

### Primeras reglas propuestas

```text
/hookify Bloquea intentos de commit o push directamente sobre main en este proyecto
/hookify Advierte si se intenta escribir una API key, token o secret en archivos versionados
/hookify Advierte antes de cualquier wrangler deploy o comando de producción
/hookify Advierte si un cambio de UI se intenta cerrar sin ejecutar los tests de la familia afectada
```

No generar reglas a ciegas desde toda la conversación. Revisar cada hook como código de gobernanza.

---

## P0-11 — PR Review Toolkit

```bash
claude plugin install pr-review-toolkit@claude-plugins-official
```

Seis agentes especializados: comments, tests, silent failures, types, guidelines y simplification.

### Uso

Antes de declarar un PR listo:

- ejecutar solo los agentes aplicables;
- contrastar findings con logs/código;
- no corregir automáticamente “style issues” que contradigan dirección de arte;
- no reemplazar revisión visual con code review.

---

## P0-12 — Context7

```bash
claude plugin install context7@claude-plugins-official
```

### Por qué

Acceso a documentación versionada/actual de librerías y APIs. Muy útil para evitar responder desde conocimiento de una versión anterior.

### Key

Puede funcionar sin key. `CONTEXT7_API_KEY` solo se plantea si límites/uso lo justifican. No crear una key por anticipación.

### Uso

Consultar cuando la respuesta depende de versión de una dependencia/API. Para web platform pura, Modern Web Guidance/MDN/Chrome suelen ser autoridad más directa.

---

## Verificación tras instalación

No instalar los 12 y asumir que funcionan. Después de cada grupo:

```text
/plugins
/mcp
```

Pruebas mínimas:

1. Modern Web Guidance responde una consulta Baseline.
2. Chrome abre localhost y devuelve viewport/DOM.
3. Playwright navega Inicio→Manecillas sin modificar nada.
4. GitHub lee el PR activo.
5. Security Guidance dispara sobre un snippet de prueba no committeado o se confirma cargado.
6. LSP encuentra definición/referencia de una función JS y un diagnóstico Python.
7. CLAUDE.md Management genera audit sin editar hasta aprobación.
8. Skill Creator puede inicializar un skill de prueba fuera de producción.
9. Hookify lista reglas.
10. PR Toolkit analiza un diff pequeño.
11. Context7 recupera documentación de la versión indicada.

## Cuándo desinstalar del P0

Si durante 60–90 días una herramienta:

- no se usa;
- duplica consistentemente otra mejor;
- añade ruido/contexto;
- cambia a un modelo de permisos que ya no encaja;
- degrada estabilidad;

se rebaja en `tools-catalog.json` y se deshabilita/desinstala.