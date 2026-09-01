# F.1 · Revalidación de producción — Target Size sitewide

**Fecha:** 2026-08-30  
**Base revalidada:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**PR:** #207 · `ideas/f01-target-size-sitewide-2026-08-29`  
**Veredicto:** `IMPLEMENTED_IN_PR · SITEWIDE_ENFORCED · WCAG_EXCEPTIONS_CLASSIFIED · PRODUCT_CONTRACTS_PRESERVED`

## 1. Decisión

F.1 ya no es una propuesta documental. La PR integra una auditoría browser-based de Target Size dentro de la autoridad existente `Sitewide Reflow QA`, reutilizando su descubrimiento de rutas y evitando un crawler o un required check paralelo.

El gate aplica WCAG 2.2 SC 2.5.8 como baseline de 24×24 CSS px con sus excepciones pertinentes y, de forma separada, conserva los contratos de producto más estrictos ya existentes para el shell.

Fuente normativa vigente revisada:

- W3C/WAI · Understanding SC 2.5.8 Target Size (Minimum): `https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html`
- WCAG 2.2 · SC 2.5.8: `https://www.w3.org/TR/WCAG22/#target-size-minimum`

La norma exige 24×24 CSS px salvo excepciones como Spacing, Equivalent, Inline, User Agent Control o Essential. Los valores de 42/44 px del proyecto no se presentan como requisito WCAG: son contratos locales de UX que el QA protege deliberadamente.

## 2. Implementación real

La PR añade/extiende:

- `qa/target-size-audit.mjs`
  - geometría renderizada con `getBoundingClientRect()`;
  - clasificación por tamaño, spacing, inline y Equivalent;
  - exclusión correcta de targets no utilizables en `<details>` cerrados;
  - auditoría posterior con `<details>` expandidos para no perder esos targets;
  - Equivalent explícito y source-backed para el importador JSON de la ficha de objeto heredado;
  - contratos responsivos superiores para `.explore-trigger` y `.header-search`.
- `qa/target-size-audit.test.mjs`
  - geometría de spacing;
  - regresión 42→24;
  - contratos mobile/desktop del shell;
  - contrato Equivalent de importación JSON.
- `qa/sitewide-reflow-browser.mjs`
  - reutiliza las 76 rutas descubiertas por Reflow;
  - ejecuta Target Size en 390×900, 768×1000 y 1280×900;
  - añade un estado `expanded-details` cuando existen `<details>`;
  - conserva artifacts incluso para diagnóstico.
- `.github/workflows/sitewide-reflow-qa.yml`
  - ejecuta los unit tests;
  - activa `TARGET_SIZE_MODE=enforce` dentro del mismo required context.
- `publicar-web/index.html`
  - corrige los tres enlaces realmente insuficientes de la checklist noindex mediante un área activa mínima de 24px, sin convertir el mínimo WCAG en una regla visual global.

## 3. Baseline antes de endurecer el gate

La primera ejecución deliberadamente usó `TARGET_SIZE_MODE=report` para no bloquear con heurísticas sin validar.

Run `33301169547` sobre `a8a34c101fb6e5b7c22b7038e9605a3cf9e04c91`:

- 76 rutas;
- 152 checks de reflow;
- 228 checks iniciales de Target Size;
- 10.790 targets observados;
- 44 findings.

Los 44 findings se concentraban en cuatro patrones:

1. 30 enlaces `Fuente N` dentro de `<details>` de `/recursos/herramientas-para-escritores/`;
2. 9 observaciones de tres enlaces en `/publicar-web/`;
3. 3 observaciones del `input.sr-only` de importación JSON;
4. 2 observaciones del mismo `<summary>` de FAQ de Samuel en sus dos URLs equivalentes.

La clasificación reveló que el primer detector trataba descendientes de `<details>` cerrados como si fueran targets visibles. No se convirtió ese falso positivo en padding masivo.

## 4. Reconciliación de los findings

### 4.1 `Fuente N`

No se excluyen de la auditoría. El checker ignora correctamente los descendientes no utilizables mientras el `<details>` está cerrado y crea un segundo estado con los `<details>` abiertos.

En ese estado los enlaces siguen midiéndose (63×15 CSS px en el baseline observado) y cumplen SC 2.5.8 por la excepción geométrica de **Spacing**: sus círculos de 24px no intersectan otros targets.

### 4.2 FAQ de Samuel

El `<summary>` «¿Puedo pedir un ejemplar firmado?» mide aproximadamente 21,2px de alto, pero dispone de separación suficiente respecto a targets adyacentes. Se mantiene como `spacing_exception` tanto en estado normal como expandido y en 390/768/1280 px.

No se infla visualmente el FAQ solo para alcanzar 24px cuando la propia norma permite spacing.

### 4.3 Importación JSON

El `input[type=file].sr-only` no recibe una excepción genérica por clase ni por ser visualmente oculto.

Existe una única excepción declarada:

- target: `[data-record-import]`;
- equivalente: `[data-record-open]`;
- evidencia: `assets/objeto-heredado.js`, donde el botón visible ejecuta `fileInput.click()`.

El auditor exige además que el control equivalente renderizado cumpla el mínimo. Los tests fijan esta relación para evitar que la allowlist se convierta en un escape hatch.

### 4.4 `/publicar-web/`

Los tres enlaces de la checklist noindex sí requerían una corrección real. La PR les proporciona `min-height:24px` mediante `inline-flex`, sin alterar el resto de la arquitectura ni crear una regla sitewide artificial.

## 5. Contratos de producto superiores

El gate mantiene por separado contratos que no proceden de WCAG sino del diseño del proyecto:

- `.explore-trigger`
  - ≤899px: mínimo 42×42;
  - ≥900px: mínimo 44×44.
- `.header-search`
  - ≤899px: mínimo 42px de ancho y 44px de alto;
  - ≥900px: mínimo 42px de ancho y 44px de alto.

Así una regresión silenciosa 42→24 puede fallar aunque 24px fuese suficiente para el baseline normativo.

## 6. Resultado final de CI

Run final `33303004114` sobre HEAD `2d5316dc4e79c066bbea19b46c5821549c5a18ee`:

- `TARGET_SIZE_MODE=enforce`;
- 76 rutas;
- 152 checks de reflow;
- 279 estados/checks de Target Size;
- 13.943 targets observados;
- 0 findings;
- 1.913 excepciones clasificadas y conservadas en artifact;
- 510 comprobaciones de contratos superiores del shell;
- 12/12 unit tests de Target Size verdes;
- Reflow, Pa11y, Required merge gate, CSP, Analytics, Runtime, Lighthouse, links y resto de workflows del commit: verdes.

Desglose de excepciones del artifact final:

- `spacing_exception`: 1.156;
- `inline_exception`: 589;
- `associated_label_target`: 165;
- `equivalent_target`: 3.

El volumen de excepciones no se interpreta como deuda automáticamente: son clasificaciones de targets undersized que cumplen por una vía explícita de SC 2.5.8. El artifact permite revisar cambios futuros en lugar de ocultarlos.

## 7. Definition of Done revalidada

- [x] cobertura sitewide reutilizando la autoridad de rutas existente;
- [x] targets no utilizables en `<details>` cerrados no generan falsos positivos;
- [x] esos mismos targets se auditan cuando el contenido se expande;
- [x] inline / spacing / Equivalent se clasifican explícitamente;
- [x] el Equivalent no es una allowlist genérica;
- [x] contratos propios de 42/44 px se protegen por separado;
- [x] existe regresión automática contra un shrink 42→24;
- [x] el reporte conserva URL/selector/dimensiones/motivo;
- [x] el gate está en `enforce` dentro de Sitewide Reflow;
- [x] Reflow y Pa11y permanecen verdes;
- [x] no se ha impuesto 42px a toda la web ni se han añadido paddings indiscriminados.

## 8. Cierre

F.1 queda implementada como capacidad real de QA y no como una campaña de rediseño masivo. El sitio se protege con la semántica correcta de WCAG 2.5.8, mantiene auditables sus excepciones y conserva simultáneamente los contratos superiores de interacción que forman parte del diseño del proyecto.
