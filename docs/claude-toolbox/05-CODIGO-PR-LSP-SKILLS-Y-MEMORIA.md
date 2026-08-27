# 05 — Código, PR, LSP, Skills y memoria

## 1. GitHub plugin — fuente de verdad de desarrollo

Instalación:

```bash
claude plugin install github@claude-plugins-official
```

### Casos de uso

- leer PR actual antes de continuar una tarea;
- inspeccionar changed files/diff/comments/checks;
- buscar un commit que introdujo un comportamiento;
- revisar Actions fallidas;
- crear issues/PRs cuando el usuario lo pida;
- mantener trazabilidad de decisiones.

### Regla

No usar `git push`/`gh api *` como sustituto automático del MCP si GitHub ofrece una tool más acotada. El permiso actual de `.claude/settings.local.json` es muy amplio y debe revisarse.

## 2. PR Review Toolkit — revisión local modular

```bash
claude plugin install pr-review-toolkit@claude-plugins-official
```

Los agentes publicados actualmente cubren:

- Comment Analyzer;
- PR Test Analyzer;
- Silent Failure Hunter;
- Type Design Analyzer;
- Code Reviewer;
- Code Simplifier.

### Aplicación selectiva

CSS/media-only:
- comments/guidelines/simplification solo si aportan;
- no inventar “type design”.

Worker/API/security:
- tests + silent failures + guidelines + security stack.

Python/builders:
- tests + error handling + Pyright + reviewer.

No ejecutar los seis por ritual si cuatro no tienen sentido.

## 3. Code Review — A/B, no acumulación

```bash
claude plugin install code-review@claude-plugins-official
```

Anthropic lo describe como revisión de PR multiagente con filtering por confianza. Es un buen candidato, pero solapa PR Review Toolkit.

### Pilot

Tomar 5 PRs reales de distinta clase:

- CSS responsive;
- Worker/security;
- Python builder;
- content/registry;
- accessibility.

Comparar:

- bugs reales encontrados;
- falsos positivos;
- findings duplicados;
- coste/contexto/tiempo;
- capacidad de respetar contratos del repo.

Elegir una política:

- PR Toolkit como preflight local + Code Review solo en P0/P1; o
- uno de los dos si no existe valor incremental.

## 4. TypeScript LSP — JS también

```bash
claude plugin install typescript-lsp@claude-plugins-official
```

Soporta `.js`, `.jsx`, `.mjs`, `.cjs`, TS variants. Debe convertirse en primer paso para:

- rename/refactor JS;
- encontrar listeners/exports/imports;
- assistant modules;
- Worker JS;
- scripts JS.

Antes de reemplazar una función, pedir referencias. Antes de borrar una export, pedir consumers.

## 5. Pyright LSP

```bash
claude plugin install pyright-lsp@claude-plugins-official
```

Casos:

- `scripts/build-public-dist.py`;
- checks/QA Python;
- generators;
- tests.

Pyright no sustituye ejecución de test. El flujo es `static diagnostics → patch → tests`.

## 6. Serena — symbol-level pilot

Serena aporta navegación/refactor semántico mediante LSP sobre muchos lenguajes.

### Por qué no P0

El repo tiene mucho HTML/CSS plano, donde su ventaja frente a GitHub search + LSP específicos es menor.

### Pilot válido

Un refactor transversal JS/Python con símbolos y referencias. Si reduce lecturas/errores de forma clara, mantener ON_DEMAND.

## 7. Feature Dev — solo cambios con arquitectura

```bash
claude plugin install feature-dev@claude-plugins-official
```

Flujo actual de siete fases y subagents explorer/architect/reviewer.

Úsese para:

- nueva funcionalidad del Cuaderno;
- búsqueda/filtros nuevos;
- nuevo sistema de eventos;
- integración técnica compleja;
- refactor de shell con varias familias.

No para:

- cambiar un `gap`;
- reparar un underline;
- corregir un alt;
- un bug CSS de una regla.

## 8. Superpowers — metodología opcional

```bash
claude plugin install superpowers@claude-plugins-official
```

Aporta TDD, debugging sistemático, brainstorming y subagent development.

### Pilot

Probarlo en un bug difícil y una feature intermedia. Si sus workflows duplican `Feature Dev` + nuestras skills sin mejorar calidad, no dejarlo always-on.

### Buena aplicación

Debugging: exigir root cause antes de parchear síntomas.

### Mala aplicación

Forzar TDD ceremonioso para cada cambio documental/CSS cuando el test apropiado es visual/browser QA.

## 9. Code Simplifier

```bash
claude plugin install code-simplifier@claude-plugins-official
```

Uso ON_DEMAND al final de JS/Python complejo.

### Protección especial para CSS

El CSS V1 contiene geometría y excepciones responsive deliberadas. Un simplifier puede considerar “duplicación” algo que existe para preservar craft o una edge condition.

Por tanto:

- nunca ejecutar autónomamente sobre toda `assets/v1-*.css`;
- pasarle el contrato de comportamiento;
- comparar visual regression;
- solo aceptar simplificación que reduzca complejidad sin aplanar composición.

## 10. Skill Creator — convertir criterio en tests

```bash
claude plugin install skill-creator@claude-plugins-official
```

Capacidades publicadas: Create, Eval, Improve, Benchmark con Executor/Grader/Comparator/Analyzer.

### Skill 1 — `david-mobile-hierarchy-audit`

Inputs:
- URL/page;
- screenshots 390 + 1440;
- computed geometry;
- family contract.

Output estructurado:
- protagonist clarity;
- scene boundaries;
- type dominance;
- media usefulness;
- density curve;
- inherited-desktop symptoms;
- evidence references;
- no design solution until observation complete.

Eval negatives:
- debe rechazar “pon fondos alternos” sin análisis;
- debe detectar una página donde todo se convierte en 1fr;
- no debe penalizar blanco por sí mismo.

### Skill 2 — `david-design-critic`

Debe detectar:
- bento/card soup;
- generic centered hero;
- arbitrary gradient/glass/pills;
- fake materiality;
- design copied from reference;
- excessive type scale;
- mobile collapse;
- decorative motion;
- accessibility/performance tradeoff escondido.

### Skill 3 — `david-pr-final-gate`

Combinar evidencia de:
- diff;
- tests;
- browser;
- visual;
- accessibility;
- source-of-truth constraints.

No mergea; decide `PASS / BLOCK / NEEDS_HUMAN` con evidencia.

## 11. CLAUDE.md Management

```bash
claude plugin install claude-md-management@claude-plugins-official
```

### Objetivo

Un CLAUDE.md corto que enseñe:

- cómo arrancar;
- dónde están contratos;
- comandos obligatorios;
- source of truth;
- no-main/no-deploy;
- gotchas reales.

No pegar allí toda esta documentación. El plugin debe detectar duplicidad/obsolescencia y proponer, no auto-reescribir sin review.

## 12. Claude Code Setup — meta-auditor read-only

```bash
claude plugin install claude-code-setup@claude-plugins-official
```

El plugin actual analiza repo y recomienda top integrations por MCP/skills/hooks/subagents/commands sin escribir.

### Frecuencia

- una vez después de consolidar esta toolbox;
- tras un cambio grande de stack;
- trimestral.

### Regla

Sus sugerencias no se instalan automáticamente. Cada recomendación vuelve a las cinco preguntas del inventario.

## 13. Plugin Developer Toolkit

```bash
claude plugin install plugin-dev@claude-plugins-official
```

Instalar ON_DEMAND durante creación/mantenimiento del plugin propio del proyecto. Incluye skills para hooks, MCP, commands, agents y validación.

Retirarlo/deshabilitarlo cuando no estemos desarrollando plugins si añade contexto innecesario.

## 14. MCP Server Dev

Mismo criterio: solo si terminamos construyendo un MCP propio. Primero intentar:

1. Skill;
2. script/CLI;
3. hook;
4. subagent;
5. MCP si realmente necesitamos una interfaz de tools/resources persistente.

## 15. Commit Commands — no ahora

Automatizar commit/push/PR parece cómodo, pero el proyecto necesita staging selectivo y revisión de branch. Ya tenemos GitHub plugin + Git.

No instalar por defecto hasta demostrar que el plugin puede respetar:

- nunca `git add .`;
- nunca main directo;
- no push de files no relacionados;
- no merge automático;
- no ocultar diff.

## 16. Memoria automática “Remember” — no ahora

Un hook de memoria continua puede añadir contexto/coste y perpetuar decisiones obsoletas. El proyecto ya tiene Drive, repo docs, handoffs y CLAUDE.md.

La memoria debe ser curada:

`session learning → propuesta → CLAUDE.md/doc/source of truth`, no “todo lo dicho se recuerda”.