# Metodología editorial · unificación visual — 2026-08-30

## Alcance

PR #271, apilada sobre #270 (`design/herramientas-visual-unification-2026-08-30`).

Base exacta: `1bfb41e03a01302ba8e5b74b2f77cd2a57fbb87c`.

Ruta intervenida: `/metodologia-editorial/`.

No se modifican el HTML de la ruta, su contenido editorial, los cinco estados cerrados, el canal de correcciones, URLs, canonical, JSON-LD, jerarquía de headings ni datos de editoriales. La única modificación de producción está en `assets/editoriales.css`; el resto del alcance son QA, workflow y este documento.

## Diagnóstico de baseline

Antes de modificar producción se creó `qa/metodologia-editorial-design-browser.mjs` y un workflow dedicado. El baseline heredado de #270 se verificó en 13 anchuras: 1728, 1440, 1280, 1024, 901, 900, 768, 767, 640, 390, 389, 360 y 320 px.

El primer run del capturador falló en las 13 anchuras porque contaba globalmente dos enlaces `mailto:`: el canal de correcciones del contenido y otro contacto del shell/footer. Era un falso negativo del QA, no un defecto de producción. Se corrigió el scope a `main#contenido` en `edaeca001b06b3d4c95d947a7196ee1ef3b4844d`.

El baseline verde posterior quedó registrado en el run `33308291163`, artifact `9731180361`, digest `sha256:af0993c3c004019a1f5fc707ed536623b58c3e5645c2de54572871f57c1b7294`.

La revisión visual del baseline confirmó una estructura semántica sana y cero overflow, pero una deuda clara de jerarquía: contenido comprimido a la izquierda en desktop, cinco bloques sin lectura de proceso, ledger de estados tratado como tabla técnica aislada y una columna móvil demasiado continua.

## Dirección cerrada

La página se define como **protocolo verificable / cuaderno de método**, no como otra herramienta, dashboard o ficha editorial.

Se conserva literalmente la estructura existente y se transforma solo su lectura visual:

- azul editorial `#1d4f96` y azul profundo `#0d2c57`;
- dorado decorativo `#b8860b`;
- dorado de texto AA `#9b6e00` para labels pequeños y numeración;
- apertura manuscrita Yellowtail y H1 editorial de gran escala;
- doble regla azul/dorado como transición del hero;
- cinco bloques metodológicos convertidos en pasos `01 /`–`05 /` mediante contador CSS;
- “Estados de recepción” tratado como diccionario de estados, 2 columnas y 1 columna a partir de 767 px;
- protocolo 2 columnas → 1 columna en 900 px;
- registros internos 2 columnas → 1 columna en 640 px;
- nota legal convertida en cierre de confianza con rail azul/dorado;
- navegación contextual y footer alineados con la misma gramática.

## Aislamiento de las fichas editoriales

La primera implementación usó un `:has()` demasiado amplio:

`main#contenido[data-family="tool"] .spec-ledger .editorial-fact`

Las fichas de editoriales también cumplen esa estructura, por lo que heredaron el sistema metodológico. El efecto real fue detectado por Pa11y y `Professional resources QA`: sus `<dt>` pasaron al dorado `#b8860b`, con contraste aproximado 3.25:1, y Lighthouse de recursos profesionales bajó a 0.96 de accesibilidad en las tres fichas auditadas.

La corrección de producción en `983a682c69933ddfcd3d832d72561b39f3b93cb2` hace el scope estructuralmente exclusivo:

`main#contenido[data-family="tool"] .tool-findings-block > .spec-ledger`

En Metodología el diccionario de estados está anidado dentro de un `tool-findings-block`; en las fichas editoriales su `spec-ledger` cuelga directamente de la sección. Además se separó `--method-gold-text:#9b6e00` del dorado decorativo.

El contrato final añade una visita de aislamiento a `/editoriales/minotauro/` y exige que no exista `--method-blue` ni numeración `method-step` en esa ficha. También genera `publisher-control-1280.png` como evidencia visual.

## Defectos y correcciones durante la implementación

1. **Falso negativo del canal de correcciones**: el baseline contaba el `mailto:` del footer además del del contenido. Corregido en QA, sin producción.

2. **Escala invertida del H1 en 768→767**: la primera regla móvil hacía que el H1 pasara de 56 px a aproximadamente 71.2 px al estrechar un píxel. Se corrigió en `99f0bdc22d6ca7768caef4de647e114323b02aa3` con una escala monotónica; el contrato lo verifica expresamente en 768/767 y 390/389.

3. **Fuga visual hacia fichas editoriales**: el scope inicial coincidía con Minotauro, Nocturna y Duermevela. Corregido en `983a682c69933ddfcd3d832d72561b39f3b93cb2`, sin cambiar las fichas ni relajar Pa11y/Lighthouse.

4. **Contraste del dorado textual**: `#b8860b` se mantiene para reglas, rails y acentos decorativos, pero el texto pequeño usa `#9b6e00` para cumplir AA.

5. **Cross-engine transitorio ajeno a la ruta**: en el HEAD `5da90a2de8350cc1bba16ad7d5139b61b54672bb` WebKit no llegó a considerar visible el trigger compacto de Explorar en HOME, mientras Chromium/Firefox y el resto de rutas pasaban. #271 no modifica HOME. El mismo cross-engine volvió a success completo en el HEAD final de código, por lo que no se reprodujo como regresión.

## Contrato visual final

`qa/metodologia-editorial-design-browser.mjs` exige en 13 viewports:

- contexto Herramientas, canonical, H1 y contenido intactos;
- cinco bloques metodológicos;
- cinco estados exactos: `open`, `closed`, `indirect`, `award_only`, `unknown`;
- canal de correcciones y nota legal;
- cero overflow horizontal;
- activación exclusiva de los tokens metodológicos;
- H1 azul, doble regla azul/dorado y navegación contextual coherente;
- contador CSS de los cinco pasos;
- dorado textual AA;
- seam 901/900 del protocolo;
- seam 768/767 del diccionario;
- seam 640 de cada registro;
- escala no creciente al estrechar 768→767 y 390→389;
- cierre de confianza azul/dorado;
- aislamiento real contra una ficha editorial.

## Evidencia automática final de código

HEAD de código revisado: `1b4699d1ba0bfd04e39e955c4b701f7a471c507d`.

En ese HEAD: **11/11 workflows completados con success**:

- Tool engine tests
- Runtime scoping QA
- Metodología editorial browser QA
- Analytics taxonomy QA
- Check content indexes
- CSP public shell QA
- Accessibility baseline (Pa11y)
- Cross-engine smoke
- Professional resources QA
- Sitewide Reflow QA
- Lighthouse CI

El artefacto `metodologia-editorial-evidence` del run `33310438528` (artifact `9731815033`) tiene digest `sha256:45747543a09d331d01397a70e029da985320e776f49c53909bd2d49d54c30374`.

`metodologia-editorial-design-report.json`: `failures: []`, `overflow: 0` en las 13 anchuras. El reporte confirma además `#9b6e00` en los labels de estado y los seams previstos.

## Revisión visual final

Revisadas manualmente las capturas completas de 1728 y 1440, los seams 901/900 y 768/767, móvil 390 y 320, además de la ficha de control Minotauro a 1280.

Resultado:

- desktop: jerarquía clara de protocolo, espacio negativo controlado y lectura en pasos sin sensación de dashboard;
- 901→900: la secuencia pasa de dos columnas a una sin salto roto;
- 768→767: el diccionario pasa de dos columnas a una y el H1 no crece al estrechar;
- 390/320: lectura, estados, correcciones y cierre legal siguen legibles y sin overflow;
- Minotauro conserva el diseño de ficha editorial heredado y no recibe tokens, numeración, hero ni dorados de Metodología;
- no se detecta otro defecto visual objetivo en las capturas finales.

## DoD

- [x] baseline real antes de diseñar;
- [x] contenido, estados, enlaces y semántica preservados;
- [x] dirección visual propia y distinta del hub Herramientas;
- [x] seams responsive verificados;
- [x] defecto de escala 768/767 corregido;
- [x] fuga a fichas editoriales diagnosticada y corregida sin relajar QA;
- [x] contraste AA recuperado;
- [x] aislamiento de ficha editorial incorporado al contrato;
- [x] 11/11 workflows verdes en HEAD de código;
- [x] capturas finales revisadas manualmente;
- [ ] revisión humana en dispositivos físicos según `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.

## Estado

**Técnicamente cerrado por código, CI y revisión visual de capturas.**

La PR debe permanecer **Draft, abierta y sin merge** hasta completar la revisión humana/física y respetar el orden de la cadena de PRs.

Este documento y el renombrado de los pasos del workflow constituyen el commit documental final; el HEAD resultante debe volver a verificarse en CI antes de considerar definitivo el cierre técnico de #271.
