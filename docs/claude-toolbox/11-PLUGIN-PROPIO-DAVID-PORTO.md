# 11 — Plugin/Skills propios `david-porto-web`

## Tesis

La mayor ventaja no está en instalar un plugin más de “web design”. Está en construir una capa pequeña que enseñe a Claude **qué significa calidad en este proyecto** y que orqueste herramientas externas con nuestros contratos.

Nombre conceptual:

```text
david-porto-web
```

No publicar en marketplace inicialmente. Debe vivir como proyecto interno y poder auditarse.

## 1. Herramientas para construirlo

Durante desarrollo:

```bash
/plugin install plugin-dev@claude-plugins-official
/plugin install skill-creator@claude-plugins-official
/plugin install hookify@claude-plugins-official
```

`plugin-dev` ayuda con estructura/manifests/hooks/MCP/agents; `skill-creator` evalúa las Skills; Hookify cubre guardrails sin escribir infraestructura innecesaria.

## 2. Qué NO debe contener

- API keys;
- Cloudflare tokens;
- deploy command automático;
- credenciales GitHub;
- assets/binarios grandes;
- toda la documentación de Drive copiada;
- prompts gigantes cargados en cada turno;
- un MCP propio sin necesidad;
- decisiones estéticas hardcoded (“usar crema”, “H1 72px”).

## 3. Arquitectura propuesta

```text
.claude/
  plugins/ or project plugin location (según convención actual validada)
    david-porto-web/
      .claude-plugin/
        plugin.json
      skills/
        observe-live/
        mobile-hierarchy-audit/
        design-critic/
        media-art-direction-review/
        public-artifact-review/
        factual-parity-review/
        pr-final-gate/
      agents/
        observer.md
        design-critic.md
        accessibility-reviewer.md
        performance-reviewer.md
      hooks/
        ...solo si aportan algo no cubierto por Hookify
```

La ruta exacta debe validarse con `plugin-dev`/documentación actual antes de implementarla.

## 4. Skill `observe-live`

### Problema

Claude tiende a proponer antes de medir.

### Procedimiento

1. verificar URL/branch/build;
2. Chrome DevTools screenshot + DOM/geometry;
3. viewport requerido;
4. console/network solo si relevante;
5. describir hechos;
6. separar `OBSERVED`, `INFERRED`, `UNKNOWN`;
7. no proponer solución salvo que el usuario lo haya pedido después del diagnóstico.

### Eval

Debe fallar si:

- dice “se ve plano” sin métrica/evidencia cuando tiene browser tool;
- inventa viewport;
- confunde desktop screenshot con mobile;
- recomienda color/tipografía sin identificar problema.

## 5. Skill `mobile-hierarchy-audit`

### Scorecard no numérico

- protagonista visible;
- límites de escenas;
- densidad cambiante;
- escala tipográfica proporcionada;
- media con función;
- orientación/navigation;
- CTA/next action;
- mobile-specific ordering;
- ausencia de “desktop grid collapsed to 1fr” como única estrategia.

### Output

```text
PAGE
VIEWPORT
OBSERVATIONS
SCENE MAP
HIERARCHY FAILURES
EVIDENCE
CONSTRAINTS FROM V1
HYPOTHESES TO TEST (max 3)
```

## 6. Skill `design-critic`

Su trabajo es **rechazar** propuestas débiles.

Checklist:

- ¿podría pertenecer a cualquier startup/autor?
- ¿usa bento/cards/pills/glass/gradient sin función?
- ¿la diferencia entre secciones depende solo de background alterno?
- ¿ha cambiado tipografía para ocultar falta de composición?
- ¿la imagen es material real o relleno?
- ¿respeta content/SEO/DOM?
- ¿mobile tiene composición propia?
- ¿motion explica algo?
- ¿se mantiene fuerte sin motion?
- ¿la referencia ha sido copiada demasiado literalmente?
- ¿hay una única idea fuerte o demasiados “wow moments”?

Resultado:

`PASS / REVISE / REJECT`, con razones y evidencia.

## 7. Skill `media-art-direction-review`

Inputs:

- asset;
- provenance;
- intrinsic size;
- current usage/crop;
- family/context;
- viewports.

Debe decidir:

- full image vs crop;
- focal point;
- `<picture>` variants;
- object-position por breakpoint si aplica;
- si no debe usarse;
- alt/caption role;
- performance requirements.

Prohibido inventar fotografía/documento para “hacerlo editorial”.

## 8. Skill `public-artifact-review`

Complementa tests existentes y entiende el contrato de `build-public-dist.py`:

- public allowlist;
- gated/internal exclusions;
- runtime essentials;
- machine-readable files;
- no leakage de docs/secrets/config.

No duplica el test; enseña a Claude a interpretarlo y no romperlo durante refactor.

## 9. Skill `factual-parity-review`

Comprueba cambios que afecten a hechos de David/libros:

- source of truth;
- HTML;
- JSON-LD;
- press JSON;
- assistant/public facts;
- llms/AI surface;
- sitemaps/metadata cuando aplica.

Nunca corrige el hecho “por mayoría”; si hay contradicción, vuelve a la fuente de autoridad.

## 10. Skill `pr-final-gate`

No sustituye CI. Orquesta evidencia:

1. branch/diff scope;
2. tests obligatorios por familia;
3. CI;
4. browser evidence si UI;
5. accessibility si UI;
6. visual regression si layout;
7. source of truth si facts;
8. security si Worker/inputs;
9. docs/handoff si hay trabajo pendiente.

Resultado:

- `PASS_FOR_REVIEW`;
- `BLOCKED`;
- `NEEDS_HUMAN_VISUAL_DECISION`;
- `NEEDS_ACCOUNT_ACTION`.

Nunca `MERGED`.

## 11. Agents propios

### Observer

Tools: browser read/measure.  
No write.  
Prohibido diseñar.

### Design Critic

Recibe propuesta + evidencia, no el proceso creativo del autor de la propuesta. Busca objeciones.

### Accessibility Reviewer

Recibe DOM/axe/Pa11y/browser, no se deja seducir por estética.

### Performance Reviewer

Recibe changes + network/LHCI/CrUX; identifica coste de media/fonts/motion/JS.

### Implementer

Solo después de hipótesis aprobada. Tools de repo, tests, browser local.

## 12. Evals obligatorios

Skill Creator debe probar casos donde la respuesta correcta sea **no cambiar nada**.

Ejemplos:

- una página blanca y minimalista pero con jerarquía excelente → no penalizar por falta de color;
- una página con muchos backgrounds y cards pero mala narrativa → rechazar;
- H1 grande que sí funciona por contenido → no imponer “reducir todos los H1”;
- mobile que reordena contenido correctamente aunque se aparte de desktop → premiar;
- diseño visualmente llamativo con DOM order roto → bloquear;
- “foto IA de manuscrito” → rechazar materialidad falsa.

## 13. Benchmark

Para cada skill:

- 10–30 casos iniciales;
- expected findings;
- false-positive cases;
- A/B contra Claude sin Skill;
- variance en varias corridas cuando el output sea subjetivo;
- guardar resultados resumidos, no cadenas de pensamiento.

## 14. Tool routing

El plugin propio debe enseñar:

```text
question → authority/tool
```

Ejemplos:

- “¿por qué salta el layout?” → Chrome trace/DOM, no Figma.
- “¿cuál es el token de spacing diseñado?” → repo/Figma/contract.
- “¿funciona en iOS?” → BrowserStack/device, no Chrome emulation únicamente.
- “¿es accesible?” → browser + Pa11y/axe + manual.
- “¿esta API CSS está soportada?” → Modern Web Guidance/MDN.
- “¿rompimos un consumer JS?” → TypeScript LSP/tests.
- “¿está listo el PR?” → GitHub + PR gate.

## 15. Fuente de contratos

No copiar todos los Drive docs en cada skill. Crear un mapa corto de autoridades:

- diseño/art direction → docs 16/17 + redlines actuales;
- mobile runtime → doc 36;
- SEO/AI/Search Console → repo docs correspondientes;
- factual truth → data/editorial sources;
- public artifact → builder/tests.

La Skill carga/consulta la fuente necesaria cuando la tarea aplica.

## 16. Versionado

El plugin propio debe tener:

- versión;
- changelog;
- owner;
- `last_reviewed`;
- tests/evals;
- compatibilidad mínima Claude Code si aplica.

Un cambio de criterio importante no se mete silenciosamente.

## 17. No hacer un MCP propio todavía

No existe actualmente una necesidad demostrada de servidor propio. El repo y scripts locales ya pueden ser invocados por Claude.

Crear MCP propio solo si necesitamos exponer de forma estable una API estructurada, por ejemplo:

- design evidence database;
- source-of-truth query service;
- visual artifact catalog;

Y aun entonces comparar primero con un CLI JSON + Skill.

## 18. Definition of Done del plugin propio

- mejora benchmarks frente a Claude base;
- reduce generic-AI suggestions;
- obliga a evidence-first;
- no añade secretos;
- no puede deployar;
- no carga documentación masiva siempre;
- respeta tooling oficial;
- puede actualizarse sin romper CI;
- un nuevo Claude/colaborador puede entender el proyecto más rápido y cometer menos errores.