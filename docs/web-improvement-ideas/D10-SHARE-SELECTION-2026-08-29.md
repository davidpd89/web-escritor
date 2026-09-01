# D.10 — Compartir citas seleccionadas

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`  
Estado efectivo: **`REJECT`**

## 1. Propósito de este documento

Este fichero reconstruye directamente la investigación histórica de la idea D.10 de PR #135. No resume solo la conclusión durable de #148: conserva la hipótesis original, las revisiones intermedias, los motivos de descarte, los límites de producto y la reconciliación con el repositorio actual.

La idea evaluada era añadir, al seleccionar texto en un artículo o fragmento literario, una UI flotante para compartir automáticamente esa cita con atribución al autor/sitio.

Este documento es **docs-only**. No implementa ningún botón flotante, listener de selección, Web Share API ni lógica de portapapeles.

## 2. Veredicto

**No implementar D.10 en el estado actual del producto.**

La conclusión de #135 fue que el patrón añade una superficie de interacción desproporcionada frente al valor probado:

- comportamiento de selección distinto entre ratón, touch y teclado;
- UI flotante que puede tapar contenido;
- edge cases de accesibilidad y foco;
- complejidad adicional en móvil;
- riesgo de compartir citas fuera de contexto;
- cuestiones de longitud/copyright en fragmentos literarios;
- mantenimiento de destinos sociales que cambian;
- poco valor demostrado frente a una buena tarjeta OG y CTAs de compartir simples.

El resultado histórico final fue `REJECT`, y la revalidación independiente mantuvo esa decisión.

## 3. Orden de autoridad utilizado

Para esta reconstrucción se usa este orden:

1. snapshot histórico real de #135: `8e72321...`;
2. investigación primaria y revisiones contenidas en ese snapshot;
3. evidencia del repositorio encontrada por #135;
4. autoridad final humana de #135;
5. revalidación independiente de #135;
6. `main` actual para comprobar que la situación no ha cambiado materialmente;
7. #148 solo como comprobación de consistencia.

Una conclusión posterior no borra una hipótesis anterior: las contradicciones se conservan y se resuelven explícitamente.

## 4. Hipótesis original

En `docs/IDEAS-MEJORA-WEB-2026-08-27.md`, D.10 se formuló como:

> permitir seleccionar texto de un artículo/extracto y ofrecer un control flotante para compartir la cita con atribución automática.

La motivación original se apoyaba en un patrón visto en blogs literarios y en la expectativa de generar tráfico social orgánico.

La hipótesis tenía tres supuestos implícitos:

1. que compartir una cita seleccionada reduce suficiente fricción;
2. que esa reducción de fricción produce difusión incremental relevante;
3. que el coste UX/a11y/mobile de la UI contextual es pequeño.

La revisión de #135 no consiguió evidencia suficiente para sostener esos tres supuestos en este sitio.

## 5. Evolución de la decisión

| Fase histórica | Decisión | Razón |
|---|---|---|
| Lista original | propuesta positiva | Patrón social aparentemente útil para contenido literario. |
| Revisión 108/108 | `REJECT` | UI flotante, edge cases mobile/copyright y poco valor probado. |
| Matriz final intermedia | `DEFERIR` | Social cards y CTA convencional ofrecen mejor retorno/riesgo. |
| Autoridad final #135 | `REJECT` | No añadir selección compartible; priorizar OG cards y CTAs simples. |
| Revalidación independiente | mantenida | Reader Mode/hover/share-selection siguen sin compensar. |
| Revalidación contra `main` 2026-08-29 | `REJECT` | No aparece una necesidad nueva que invalide la decisión. |

La oscilación `REJECT → DEFERIR → REJECT` no es una inconsistencia accidental. La matriz intermedia trató la idea como algo que podría reconsiderarse; la autoridad final volvió a cerrarla tras ponderar la superficie UX completa.

## 6. Qué descubrió realmente #135

### 6.1 No era una mejora SEO

La idea nació asociada a posible tráfico social, pero #135 eliminó cualquier lectura del tipo “esta función mejora SEO”. Compartir puede producir distribución; no existe un vínculo garantizado con ranking.

### 6.2 El coste no está en `navigator.share()`

Una implementación mínima de Web Share puede parecer pequeña, pero D.10 no era “añadir un botón compartir”. Era detectar selección y presentar un control contextual correcto.

Eso obliga a resolver:

- selección que atraviesa varios elementos;
- selecciones vacías o solo whitespace;
- selección dentro de enlaces/controles;
- cierre al cambiar selección;
- reposicionamiento con scroll/zoom/reflow;
- selección por touch handles;
- teclado y lectores de pantalla;
- ausencia de Web Share API;
- fallback de copiar enlace/cita;
- citas excesivamente largas;
- atribución/canonical URL;
- contenido cuyo uso promocional no conviene automatizar.

### 6.3 Mobile y accesibilidad cambian la ecuación

Un affordance que funciona con hover/mousedown en desktop no es equivalente en touch. Una UI flotante además debe entrar en un orden de foco razonable o mantenerse no intrusiva; ambas opciones requieren diseño y pruebas.

Por eso #135 agrupó conceptualmente D.10 con otros patrones “vistosos pero caros en estados” como D.7.

### 6.4 La alternativa ya existe conceptualmente

La distribución social puede apoyarse en superficies más simples:

- metadata Open Graph/Twitter específica y correcta;
- tarjetas sociales editoriales;
- compartir la URL completa;
- CTAs explícitos cuando una página realmente los necesite.

Esto evita acoplar compartir con el motor de selección del navegador.

## 7. Relación con otras ideas de #135

### D.7 — hover previews

Ambas fueron rechazadas por una razón parecida: interacción sofisticada que aporta principalmente en desktop y crea equivalencia difícil en touch/a11y.

### O.2 — social cards

La alternativa recomendada por #135 es reforzar las cards sociales existentes antes que añadir UI flotante de selección.

### F.4 — foco visible / Focus Not Obscured

Si D.10 existiera, tendría que cumplir estos contratos. Esa deuda potencial forma parte del coste real de la idea.

### C.4 — extractos/printables

La existencia de fragmentos literarios no implica que cualquier selección deba convertirse automáticamente en copy promocional compartible.

## 8. Reconciliación con `main` actual

La revisión actual no encuentra evidencia de que el producto necesite reabrir D.10.

No se ha encontrado una autoridad canónica que modele “share selected quote”, ni una necesidad producto documentada que requiera selección flotante.

Esto **no se usa como prueba absoluta de inexistencia**: un grep puede fallar y la conclusión de D.10 no depende de demostrar que no hay una línea concreta de JS. Depende de que el patrón siga sin justificar su coste.

La web sí ha evolucionado en dirección contraria a la complejidad gratuita:

- shell editorial común;
- QA de reflow;
- contratos de accesibilidad;
- cards sociales específicas en familias donde aportan valor.

Añadir D.10 ampliaría estados sin cerrar una fricción demostrada.

## 9. Propuestas descartadas

No hacer como parte de D.10:

- listener global de `selectionchange`;
- toolbar flotante sitewide;
- iconos de X/Facebook/WhatsApp acoplados a cada selección;
- copiar automáticamente sin acción explícita;
- truncar una cita arbitrariamente para encajar en una red;
- convertir la selección en imagen generada dinámicamente;
- añadir una librería solo para posicionar el popover;
- introducir tracking de texto seleccionado;
- registrar citas seleccionadas por usuarios;
- tratar shares como señal SEO.

## 10. Qué sí sobrevive de la idea

La investigación no rechaza compartir en general. Sobreviven principios útiles:

1. facilitar que una pieza editorial pueda compartirse;
2. mantener atribución/canonical correctos;
3. usar imágenes sociales relevantes y de buena calidad;
4. elegir un CTA explícito en páginas donde exista una necesidad real;
5. medir si el canal aporta antes de ampliar la interacción.

La diferencia es que esos principios no requieren un componente ligado a selección de texto.

## 11. Gate de reapertura

D.10 solo debería reconsiderarse si aparece evidencia concreta como:

- usuarios piden repetidamente compartir fragmentos concretos;
- analítica cualitativa demuestra que compartir la URL completa no cubre el caso;
- existe una familia editorial donde las citas son una unidad de distribución deliberada;
- hay diseño móvil/teclado/lector de pantalla resuelto;
- se define un límite de longitud y política editorial/copyright;
- se prueba contra reflow, zoom, text spacing y Focus Not Obscured;
- un piloto demuestra uso suficiente para justificar mantenimiento.

Sin esas condiciones, el estado sigue siendo `REJECT`.

## 12. Si se reabre: experimento mínimo correcto

Una reapertura no empezaría con una toolbar sitewide.

Orden:

1. seleccionar una única familia de artículos;
2. definir qué texto es compartible;
3. CTA estático/expreso antes que UI automática;
4. medir uso;
5. solo entonces probar selección contextual;
6. comprobar desktop + touch + teclado + screen reader;
7. retirar si no aporta uso incremental.

## 13. Evidencia primaria y límites

Las fuentes primarias de #135 se utilizaron principalmente para performance, accesibilidad y plataforma; la decisión D.10 es sobre todo de producto/UX y estado real del sitio.

Por ello este documento no inventa una “norma oficial” que prohíba share-selection. La conclusión es una decisión de coste/beneficio para este proyecto.

## 14. Pasadas tardías revisadas

Se comprobaron las generaciones posteriores de investigación de #135 disponibles en el snapshot: cuarta, quinta, sexta, séptima, octava, novena, décima, undécima, duodécima, decimotercera y posteriores de cierre.

No aparece una nueva evidencia específica que revierta D.10. La revalidación independiente cita expresamente `share-selection` entre las ideas D cuyo coste no compensa.

Las pasadas de accesibilidad refuerzan indirectamente el coste de una UI flotante, pero no crean una nueva decisión D.10.

## 15. Estado de verdad

- `DOCUMENTED`: sí, en esta PR.
- `IMPLEMENTED_IN_PR`: no; deliberadamente docs-only.
- `MERGED_MAIN`: no mientras la PR siga abierta.
- `CONFIGURED_LIVE`: no aplica.
- `VERIFIED_E2E`: no aplica a una idea rechazada.

## 16. DoD de esta PR documental

- [x] hipótesis original recuperada;
- [x] revisión inicial recuperada;
- [x] matriz intermedia recuperada;
- [x] autoridad final recuperada;
- [x] revalidación independiente recuperada;
- [x] contradicción `REJECT/DEFERIR/REJECT` explicada;
- [x] límites con O.2, D.7 y accesibilidad documentados;
- [x] `main` actual contrastado;
- [x] no se añade runtime;
- [x] no se presenta la idea como mejora SEO.

## 17. Inventario de fuentes históricas

Fuentes consultadas dentro del snapshot `8e72321...`:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`;
- pasadas R posteriores de #135 para comprobar si existía una reapertura específica.

Fuentes actuales contrastadas:

- `main` en `291c8c677aaa7df635142687d1a6848e80ffcaa2`;
- shell/runtime/metadata social existentes en el repositorio.

## 18. Conclusión

D.10 conserva el estado **`REJECT`**. La idea inicial era razonable como exploración, pero #135 la sometió a una evaluación más amplia y concluyó que una toolbar flotante de selección añade demasiada superficie mobile/a11y/editorial para un beneficio social no demostrado. La vía correcta es mantener compartir simple y mejorar las superficies sociales ya existentes cuando exista una necesidad medible.