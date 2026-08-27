# 06 — Accesibilidad como diseño, no checklist final

## 1. Principio

Una web visualmente ambiciosa que pierde:

- orientación;
- lectura;
- foco;
- zoom;
- reflow;
- control táctil;
- reduced motion;

no está mejor diseñada.

La accesibilidad se usa aquí como **disciplina de diseño**: obliga a que jerarquía, interacción y composición sean comprensibles incluso cuando cambian capacidades, input y viewport.

## 2. Base que ya existe

El repositorio ya dispone de:

- focus visible;
- targets mínimos en muchos controles;
- `prefers-reduced-motion`;
- Pa11y baseline;
- reflow QA;
- browser QA;
- HTML semántico;
- labels;
- fallbacks/no-JS en distintas superficies.

No crear otra pila de scanners que devuelva los mismos issues.

## 3. Qué añade una herramienta experta

Probar **Stark MCP o axe MCP** para añadir:

- diagnóstico contextual;
- revisión de estados;
- remediación guiada;
- accessibility expertise dentro del flujo de Claude;
- governance/documentación;
- revisión anterior al merge.

Hacer piloto con la misma página antes de elegir.

## 4. Stark MCP

Servidor remoto:

```text
https://mcp.getstark.ai/mcp
```

Autenticación: OAuth.

Caso de uso ideal:

- Figma/design review;
- contraste y accesibilidad antes de código;
- governance de assets/proyectos cuando esté disponible en el plan;
- revisión de decisiones visuales.

No usar su salida como sustituto de WCAG ni de test manual.

## 5. axe MCP

Caso de uso ideal:

- página renderizada;
- scan por viewport/estado;
- análisis de problemas;
- explicación/remediación;
- acompañar cambio de código.

Autenticación según configuración oficial, mediante OAuth/API donde proceda.

Nunca guardar una API key en el repo.

## 6. Normativa base

WCAG 2.2 es la referencia normativa principal.

Esta PR se interesa especialmente por criterios que afectan directamente al diseño responsive.

## 6.1. Reflow

A 320 CSS px, el contenido debe poder leerse sin scroll bidimensional salvo excepciones esenciales.

Diseño implica:

- no esconder overflow;
- no forzar min-widths innecesarios;
- tablas con patrón móvil deliberado;
- headings que parten de forma razonable;
- dialogs operables;
- media adaptable.

## 6.2. Resize Text

El sistema debe tolerar ampliación de texto sin pérdida de información/función.

El uso de `clamp()` con `vw` debe probarse; no asumir que fluido = accesible.

## 6.3. Text Spacing

Probar overrides equivalentes a:

- line-height 1.5;
- paragraph spacing 2× font size;
- letter spacing .12em;
- word spacing .16em.

No debe perderse contenido ni función.

Este test es especialmente útil para detectar layouts «demasiado diseñados» que solo sobreviven con copy compacto.

## 6.4. Target Size

WCAG 2.2 AA incorpora un mínimo de 24×24 CSS px o separación equivalente en el criterio 2.5.8.

El proyecto ya usa a menudo 44 px, que es un objetivo más cómodo y coincide con el criterio AAA Enhanced para muchos controles.

Regla de producto:

- conservar 44×44 como objetivo interno para controles principales táctiles;
- no reducir targets para «hacer caber» navegación;
- si un link inline es texto corriente, aplicar la excepción que corresponda, no convertir cada enlace en botón enorme.

## 6.5. Focus

El focus debe:

- ser visible;
- no quedar bajo sticky header;
- distinguirse del estado normal;
- recorrer DOM lógico;
- volver al invocador al cerrar modal/dialog;
- permanecer visible con zoom/text spacing.

No diseñar hover que no tenga equivalente razonable en keyboard/touch.

## 6.6. Contrast

El contraste es requisito, no sistema visual.

No elegir una paleta únicamente porque un scanner marque verde.

Proceso:

1. decidir rol visual;
2. verificar contraste en todos los estados;
3. si falla, ajustar tono/peso/superficie;
4. comprobar que la jerarquía sigue funcionando.

Estados a revisar:

- default;
- hover;
- focus;
- active;
- disabled;
- muted metadata;
- border/hairline cuando transporta información;
- texto sobre media.

## 7. Accesibilidad y jerarquía perceptual

La segmentación visual debe tener respaldo estructural.

Ejemplo:

Si una nueva «escena» visual es realmente una sección temática, probablemente corresponde a un heading/section adecuados.

Pero no crear headings vacíos solo para justificar diseño.

La jerarquía visual y semántica deben converger.

## 8. DOM order vs visual order

CSS Grid/Flex puede recomponer desktop/mobile, pero:

- DOM debe seguir teniendo sentido;
- no usar `order` para crear una lectura visual que contradice la lectura accesible;
- no duplicar contenido para tener dos órdenes;
- no esconder una versión del texto con CSS solo para SEO/desktop.

Cuando mobile necesita orden propio, preferir un DOM que funcione naturalmente en mobile y usar grid en desktop para redistribuirlo.

## 9. Media

### Imágenes informativas

- alt útil;
- no repetir caption exacto si no aporta;
- no poner texto esencial incrustado sin alternativa;
- crop no elimina información semántica.

### Decorativas

- alt vacío cuando proceda;
- evitar que la «materialidad» genere ruido para screen reader.

### Portadas

El alt debe identificar obra/contexto, no describir cada elemento visual de portada salvo necesidad.

## 10. Motion

Motion aceptable si:

- refuerza relación;
- no transporta información exclusiva;
- no bloquea interacción;
- tiene reduced-motion;
- no provoca mareo/desorientación;
- no se repite de forma ambiental.

Test:

```text
prefers-reduced-motion: reduce
```

La página debe seguir pareciendo diseñada, no una versión rota sin animaciones.

## 11. Carousels

El contrato de diseño ya los rechaza para contenido principal.

Además reducen claridad y complican:

- focus;
- swipe;
- announcements;
- auto-advance;
- contenido oculto.

No introducir uno para «dar dinamismo».

## 12. Dialog / Explorar

Revisar:

- semántica `<dialog>`;
- título;
- focus inicial razonable;
- Escape;
- close button;
- focus return;
- scroll interno;
- altura baja;
- zoom;
- touch;
- current page;
- reduced motion.

No añadir un nuevo drawer mobile si el dialog existente ya resuelve la tarea.

## 13. Forms y herramientas

Diseño debe distinguir:

- label;
- hint;
- input;
- status;
- error;
- resultado;
- acción siguiente.

Error no solo por color.

No toast como único feedback.

Con teclado virtual:

- input visible;
- error visible;
- acción alcanzable;
- contenido escrito preservado.

## 14. Touch

No depender de:

- hover;
- drag preciso;
- gesture oculta;
- swipe como única navegación;
- tiny icons.

Una interacción de escritorio que en touch necesita explicación suele necesitar recomposición, no tooltips adicionales.

## 15. Cognitive load

Aunque WCAG automatizado no mida toda la carga cognitiva, el diseño debe revisar:

- demasiadas señales simultáneas;
- demasiadas opciones equivalentes;
- títulos enormes repetidos;
- navegación duplicada;
- CTAs repetidos;
- iconografía sin labels;
- cambios inesperados de patrón.

Reducir ruido puede mejorar simultáneamente UX y dirección de arte.

## 16. Protocolo de revisión con MCP

### Paso 1 — diseño

Figma frame aprobado provisionalmente.

### Paso 2 — implementación local/preview

Claude implementa rama pequeña.

### Paso 3 — scan

Stark/axe sobre:

- 390;
- 1440;
- estado interactivo.

### Paso 4 — manual

- teclado;
- screen-reader spot check si el componente lo requiere;
- zoom;
- text spacing;
- reduced motion;
- orientation;
- touch.

### Paso 5 — remediación

Corregir causa, no silenciar regla.

## 17. No usar accesibilidad como excusa para diseño plano

Es posible cumplir accesibilidad con composición editorial rica.

No concluir:

- «mejor todo blanco»;
- «mejor todo una columna siempre»;
- «mejor no usar imágenes grandes»;
- «mejor no usar motion nunca».

La accesibilidad establece constraints. La dirección de arte trabaja dentro de ellas.

## 18. Evidence pack

Cada familia relevante debe registrar:

```text
axe/Stark summary
keyboard PASS/FAIL
reflow 320 PASS/FAIL
zoom 200 PASS/FAIL
text spacing PASS/FAIL
reduced motion PASS/FAIL
orientation PASS/FAIL
focus under sticky PASS/FAIL
target-size exceptions noted
```

## 19. Gate de componentes nuevos

No introducir un nuevo patrón visual/interactivo si no tiene definidos:

- default;
- hover cuando aplique;
- focus;
- active;
- disabled si existe;
- keyboard;
- touch;
- reduced motion;
- error/empty/loading si aplica;
- 320;
- 200% zoom.

## 20. Criterio final

La accesibilidad debe funcionar como un crítico experto que pregunta:

> «¿Sigue siendo clara esta intención cuando el usuario no usa tu combinación ideal de pantalla, visión, motor e input?»

Si la respuesta es sí y la composición sigue teniendo personalidad, la solución es más fuerte, no menos creativa.