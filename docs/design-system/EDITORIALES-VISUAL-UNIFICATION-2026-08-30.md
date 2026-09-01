# Editoriales · unificación visual — 2026-08-30

## Alcance

PR #272, apilada sobre #271 (`design/metodologia-editorial-visual-unification-2026-08-30`).

Base exacta: `3db1ad58a18af6d9520ce905baf5728b23c5baf1`.

Ruta intervenida: `/editoriales/`.

No se modifica el HTML de la ruta ni el contenido editorial. Se preservan las tres editoriales verificadas, sus estados, filtros, búsqueda, navegación mediante hash, datos, URLs, fuentes, canonical, JSON-LD y comportamiento sin JavaScript. La única modificación de producción está en `assets/editoriales.css`; el resto del alcance son QA, workflow y este documento.

Las fichas individuales `/editoriales/minotauro/`, `/editoriales/nocturna-ediciones/` y `/editoriales/duermevela-ediciones/`, además de `/metodologia-editorial/`, quedan fuera del scope visual de esta PR.

## Diagnóstico del baseline

Antes de modificar producción se creó `qa/editoriales-index-design-browser.mjs` y un workflow dedicado. El baseline heredado de #271 se capturó antes de cerrar la dirección visual y mantuvo como autoridad funcional previa `qa/pro-resources-browser.mjs`.

La estructura existente era semánticamente válida y conservaba correctamente buscador, filtros, contador, estados y navegación. La deuda era visual y de jerarquía: el directorio se leía demasiado cerca de una herramienta/formulario genérico, las tres editoriales no transmitían la idea de expediente verificado y la relación entre datos, estado, comprobación y acción carecía de una gramática editorial propia.

Se decidió no alterar HTML ni datos para resolver esa deuda. El rediseño se apoya en scope CSS exclusivo y en un contrato browser específico que preserva el comportamiento existente.

## Dirección cerrada

La página se define como **registro editorial verificado**: una mesa de consulta fiable donde cada editorial se presenta como un expediente comprobado.

No debe parecer un dashboard, una tabla administrativa, otra página genérica de Herramientas ni una copia de Metodología.

La gramática visual implementada utiliza:

- azul editorial `#1d4f96`;
- azul profundo `#0d2c57`;
- dorado decorativo `#b8860b`;
- dorado textual AA `#9b6e00`;
- pale blue `#eefaff`;
- apertura manuscrita Yellowtail;
- H1 editorial de gran escala;
- doble regla azul/dorado;
- aviso superior tratado como bloque de confianza;
- finder convertido visualmente en mesa de consulta;
- tres expedientes numerados `01`–`03`;
- estados abiertos/cerrados legibles sin depender solo del color;
- acciones de cada expediente con tratamiento manuscrito/editorial;
- footer y navegación contextual alineados con la gramática del registro.

## Aislamiento

El scope de producción es estructuralmente exclusivo del hub mediante:

`main#contenido[data-editoriales-directory]`

combinado con el contexto Herramientas existente.

El contrato visita expresamente `/editoriales/minotauro/` y exige que la ficha individual:

- no tenga `data-editoriales-directory`;
- no reciba `--directory-blue`;
- no reciba `--method-blue`;
- no herede la numeración `publisher-record` del directorio.

La evidencia visual `publisher-control-1280.png` confirma que Minotauro conserva su gramática de ficha individual y no recibe hero, numeración ni tokens del registro.

## Implementación

La implementación de producción está limitada a `assets/editoriales.css`.

Se transformaron visualmente, sin cambiar su semántica ni comportamiento:

- hero y apertura editorial;
- nota de confianza;
- buscador y filtros;
- contador de resultados;
- directorio y fichas;
- badges de estado;
- géneros y fecha de comprobación;
- acciones de cada editorial;
- estado vacío;
- navegación contextual;
- footer;
- comportamiento responsive en los seams relevantes.

No se modifica ningún HTML.

## Defectos y correcciones durante la implementación

1. **Escala no monotónica del H1 en seams móviles.** La primera implementación hacía crecer el H1 al reducir el viewport en `641→640` y `390→389`. Se corrigió en `f0847d71af5660be358768d6404f225a842b10ce` (`fix(editoriales): keep heading scale monotonic at mobile seams`).

2. **Contrato responsive insuficientemente explícito.** Después de corregir la escala se endureció `qa/editoriales-index-design-browser.mjs` para comprobar de forma explícita `901/900`, `768/767`, `641/640` y `390/389`, además de exigir que el tamaño del H1 nunca aumente al estrechar un píxel en esos pares. El HEAD de código/QA resultante fue `1bc214178b7d507c41aff754fa9ba543eb4cdb7b`.

3. **Medición tipográfica no estabilizada al regenerar evidencia.** Durante el cierre documental se regeneró `editoriales-visual-evidence` en el HEAD `4019447e8ac131b478964c138c70b8484eb6e1e4`. Al comparar ese artefacto con el anterior, las capturas de 768 y 389 px eran píxel a píxel idénticas en todo el contenido común, pero el JSON había registrado geometría distinta del H1 antes de la screenshot y el PNG conservaba únicamente una cola vacía adicional de 49/39 px. No era una regresión visual de producción: era una carrera de medición del propio QA, compatible con las métricas transitorias de las fuentes `font-display:optional` antes de que el layout quedara estabilizado.

   Se corrigió en `3a020d4beed3e69b3dfaf5df1bb67931253be7eb` (`test(editoriales): stabilize typography before visual measurements`). El contrato carga explícitamente Instrument Serif, Yellowtail, Newsreader y Manrope con `document.fonts.load()`, espera `document.fonts.ready`, dos ciclos de `requestAnimationFrame`, una segunda ventana de estabilidad y exige que ancho, alto, `max-width` y `font-size` del H1 no cambien antes de tomar medidas. Esta corrección endurece la fiabilidad del QA; no relaja ningún gate ni modifica producción.

No se relajaron thresholds ni gates para conseguir verde.

## Contrato visual final

`qa/editoriales-index-design-browser.mjs` recorre 14 viewports:

- 1728;
- 1440;
- 1280;
- 1024;
- 901 / 900;
- 768 / 767;
- 641 / 640;
- 390 / 389;
- 360;
- 320.

El contrato exige, entre otras condiciones:

- contexto `herramientas` y familia `tool` intactos;
- marker `data-editoriales-directory`;
- canonical y H1 exactos;
- navegación contextual activa en Editoriales;
- tres editoriales exactas: Minotauro `open/direct`, Nocturna Ediciones `open/direct` y Duermevela Ediciones `closed/no-direct`;
- buscador, filtros, contador y navegación por estado intactos;
- filtro `closed` devolviendo solo Duermevela;
- estado vacío funcional y visualmente integrado;
- cero overflow horizontal;
- ausencia de tokens exclusivos de Metodología;
- activación exclusiva de tokens del registro;
- H1 azul, apertura manuscrita y doble regla azul/dorado;
- bloque de confianza con rails azul/dorado;
- finder como grid/mesa de consulta;
- expedientes numerados;
- badges y acciones editoriales;
- seam `901/900` del hero;
- seams de filtros;
- seam `641/640` del expediente;
- escala tipográfica no creciente al estrechar en `901/900`, `768/767`, `641/640` y `390/389`;
- tipografías editoriales explícitamente cargadas antes de medir;
- geometría del H1 estable antes de registrar el snapshot;
- aislamiento de `/editoriales/minotauro/`.

`qa/pro-resources-browser.mjs` continúa siendo la autoridad funcional existente y no se sustituye ni debilita.

## Evidencia automática

### HEAD de código/QA previo al cierre documental

HEAD: `1bc214178b7d507c41aff754fa9ba543eb4cdb7b`.

En ese HEAD: **12/12 workflows completados con success**.

Run específico de Editoriales: `33312957046`.

Artefacto: `editoriales-visual-evidence`, ID `9732581576`.

Digest: `sha256:5170742f2a821531e99e1c5853b40e361873174dd50640f64fec3faec25b7786`.

### Artefacto intermedio que descubrió la carrera de medición

HEAD: `4019447e8ac131b478964c138c70b8484eb6e1e4`.

Run específico: `33317366334`.

Artifact: `9733876217`.

Digest: `sha256:a12b9dcb884f87b428cc1c075a676c94cc5e3abcf0b0fc1a718748052a83fbe2`.

La comparación con el artefacto anterior mostró que el contenido común de las capturas de 768 y 389 px era píxel a píxel idéntico, mientras el reporte había tomado métricas transitorias. Eso motivó el endurecimiento de `settleTypography()`.

### HEAD final de código/QA endurecido

HEAD: `a3929ea62417b2ecdcf2daf29b3c159b178bc0fc`.

En ese HEAD: **12/12 workflows completados con success**:

- Metodología editorial browser QA;
- Analytics taxonomy QA;
- Tool engine tests;
- Editoriales browser QA;
- Check content indexes;
- Runtime scoping QA;
- CSP public shell QA;
- Accessibility baseline (Pa11y);
- Cross-engine smoke;
- Sitewide Reflow QA;
- Professional resources QA;
- Lighthouse CI.

Run específico de Editoriales: `33317686082`.

Artefacto: `editoriales-visual-evidence`, ID `9733964632`.

Digest verificado: `sha256:5d0719ee3e8aa446306023f91ebe294f0a9ddbd395ab4559c105137e7699e1c1`.

El ZIP descargado coincide con ese digest. `editoriales-index-design-report.json` declara `phase: visual-system-contract`, `viewports: 14`, `failures: []` y `overflow: 0` en las 14 anchuras.

En las 14 mediciones `typographyState.loaded` es `true` y los valores `before`/`after` del H1 son estables. Se comprobaron además los seams tipográficos: el H1 no aumenta al reducir `901→900`, `768→767`, `641→640` ni `390→389`.

## Revisión visual final del artefacto

Se revisaron las capturas completas y estados incluidos en el artefacto final de `a3929ea62417b2ecdcf2daf29b3c159b178bc0fc`, con atención específica a:

- desktop 1728, 1440 y 1280;
- tablet 1024;
- seams 901/900, 768/767 y 641/640;
- móvil 390/389, 360 y 320;
- estado filtrado móvil;
- estado vacío móvil;
- control de aislamiento de Minotauro a 1280.

Resultado:

- desktop: hero, bloque de confianza, mesa de consulta y expedientes mantienen jerarquía editorial clara sin apariencia de dashboard;
- `901→900`: el hero pasa de dos columnas a una sin ruptura;
- `768→767`: la composición permanece estable y el H1 no crece al estrechar;
- `641→640`: los expedientes pasan de dos columnas internas a una y el H1 no crece;
- `390→389`: la escala del H1 sigue siendo monotónica y no aparece overflow;
- móvil: filtros, badges, acciones y footer siguen legibles y contenidos;
- estado filtrado: Duermevela queda como único expediente y el contador muestra una editorial;
- estado vacío: permanece integrado en el sistema visual y conserva los rails del registro;
- Minotauro: no recibe tokens, numeración ni gramática visual del hub;
- las capturas principales del artefacto endurecido vuelven a coincidir píxel a píxel con la evidencia estable previa; el estado filtrado solo elimina una cola vacía transitoria, sin modificar el contenido común;
- no se detecta ningún defecto visual objetivo pendiente en la evidencia automatizada final.

## Definition of Done

- [x] estado real de PR, base y HEAD comprobados antes de trabajar;
- [x] baseline real antes del rediseño;
- [x] contenido, datos, estados, URLs, canonical, JSON-LD y comportamiento preservados;
- [x] ningún HTML modificado;
- [x] dirección visual propia: registro editorial verificado;
- [x] scope estructural exclusivo del hub;
- [x] aislamiento frente a ficha individual verificado;
- [x] seams responsive comprobados;
- [x] defecto de escala `641/640` y `390/389` corregido;
- [x] interacción de filtros y estado vacío cubierta;
- [x] cero overflow en 14 viewports;
- [x] carrera de medición tipográfica diagnosticada sin confundirla con una regresión visual;
- [x] contrato endurecido para exigir tipografías cargadas y geometría estable antes de medir;
- [x] 12/12 workflows verdes en el HEAD final de código/QA `a3929ea62417b2ecdcf2daf29b3c159b178bc0fc`;
- [x] artefacto final descargado, digest verificado, reporte inspeccionado y capturas revisadas;
- [ ] revisión humana/física según `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.

## Revisión real multi-dispositivo

Pendiente. Los QA headless y la revisión de capturas permiten declarar la superficie cerrada técnicamente, pero no sustituyen la revisión humana/física exigida por `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.

No se debe marcar la PR como Ready ni mergearla antes de completar esa revisión y respetar el orden de la cadena.

## Estado

**Técnicamente cerrada por producción, QA, CI y revisión visual automatizada en el HEAD de código/QA `a3929ea62417b2ecdcf2daf29b3c159b178bc0fc`.**

Este documento constituye el último commit documental de #272. El HEAD resultante debe volver a completar con éxito los workflows aplicables; esa verificación final se registra en el body de la PR para evitar una cadena recursiva de commits documentales.

La PR debe permanecer **Draft, abierta y sin merge**.