# Findability · orientación, mapa y recuperación — contrato de unificación visual · 2026-08-31

## Trazabilidad

Continúa la cadena `DISEÑO -` después de Recomendaciones.

Esta familia ya comparte `assets/v1-findability.css` y una arquitectura de orientación/recuperación. No debe fragmentarse en una PR por página.

Mantener Draft y no mergear fuera de orden.

## Superficies

- `/empieza-aqui/` — orientación inicial;
- `/mapa-del-sitio/` — índice completo;
- `/404.html` / respuesta 404 — recuperación;
- `/gracias-suscripcion/` — confirmación post-newsletter, `noindex` según contrato actual.

Reconciliar rutas, robots y canonical en el HEAD antes de producción.

## Objetivo

Unificar estas superficies con el sistema editorial azul/negro/dorado manteniendo su función principal: **reducir incertidumbre y ayudar a encontrar el siguiente destino**.

No convertir `Empieza aquí` en una nueva home, quiz o onboarding SaaS. No convertir el mapa en tarjetas promocionales. No sobre-diseñar 404/confirmación: deben resolver una tarea de forma clara y rápida.

## Arquitectura existente a preservar

`v1-findability.css` ya define la familia de orientation/site map/recovery. La intervención debe evolucionar ese owner con scope claro y sin afectar otras páginas.

La arquitectura histórica de `Empieza aquí` ya fue definida como un conjunto pequeño de rutas de entrada. No añadir nuevos recorridos, preguntas o un quiz dentro de una PR visual salvo evidencia/decisión independiente.

## Hallazgo objetivo ya verificado

`assets/v1-findability.css` contiene duplicado dos veces el mismo bloque responsive `@media(max-width:900px)`.

Es deuda de mantenimiento real. Durante esta PR:

- deduplicar de forma semánticamente equivalente;
- comprobar que no cambia accidentalmente la cascada;
- añadir QA de seams para impedir que la limpieza introduzca regresiones.

No hacer un refactor general del CSS más allá de lo necesario.

## Dirección visual

### Empieza aquí

- masthead/editorial orientation claro;
- destinos como rutas/índice, no cards de marketing;
- cada ruta debe explicar para quién/para qué sirve con jerarquía compacta;
- azul/dorado para folios, rails, reglas y estado actual;
- mantener suficiente neutralidad para que sea una página funcional.

### Mapa del sitio

- tratar como índice editorial estructurado;
- jerarquía por familias y niveles;
- enlaces densos pero legibles;
- no sacrificar completitud por estética;
- wrapping robusto de títulos largos;
- teclado/focus especialmente claro.

### 404

- mensaje breve, sin dramatización;
- ofrecer destinos útiles y búsqueda/asistente si el shell lo permite;
- no depender de JavaScript para la recuperación básica;
- foco y navegación visibles;
- conservar `noindex`/semántica de error.

### Gracias por suscribirte

- estado de éxito claro sin parecer checkout/conversión agresiva;
- explicar el siguiente paso si existe;
- enlaces de continuidad útiles;
- conservar `noindex` y no crear una nueva landing pública.

## Tokens

Referencia:

- azul `#1d4f96`
- azul profundo `#0d2c57`
- dorado `#b8860b`
- pálido `#eefaff`
- neutros para cuerpo y metadatos.

Yellowtail solo si aporta una apertura/acción clara; nunca para listas densas del mapa.

## Preservar

- robots/canonical donde correspondan;
- semántica 404;
- rutas/enlaces existentes;
- arquitectura de `Empieza aquí`;
- jerarquía del mapa;
- formulario/newsletter no debe duplicarse en la página de gracias;
- shell/no-JS;
- analytics existentes;
- PWA/back-to-top si aplica.

## QA requerido

Un contrato browser de familia con las cuatro superficies.

### Viewports

- 1440/1280;
- 1024;
- 901/900 para la deuda responsive conocida;
- 768;
- 411/410 si el CSS lo requiere;
- 390/360/320;
- zoom 200 %;
- text spacing;
- teclado/focus;
- no-JS;
- cero overflow.

### Contratos

- `Empieza aquí`: número/orden de rutas heredadas;
- mapa: grupos/enlaces fundamentales presentes;
- 404: recuperación disponible y noindex;
- gracias: estado de confirmación y noindex;
- deduplicación del media query sin cambiar geometría esperada;
- aislamiento frente a HOME y otras familias.

No relajar gates ni usar overflow oculto como parche.

## Revisión humana

Comprobar:

- que `Empieza aquí` no compita con HOME;
- scanabilidad del mapa;
- densidad en móvil;
- recovery en 404 con una mano/teclado;
- claridad del estado de suscripción;
- consistencia visual sin hacer que cuatro tareas distintas parezcan la misma plantilla.

Seguir `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.

## Definition of Done

- cuatro superficies coherentes;
- media query duplicada eliminada sin regresión;
- arquitectura/rutas/robots preservados;
- responsive/zoom/text-spacing/teclado/no-JS verdes;
- evidencia revisada;
- CI verde;
- Draft y sin merge hasta revisión física.
