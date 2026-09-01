# C.8 · «Empieza aquí» por tipo/intención de lector

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado final: `PARTIAL_AUDIT`.

## Veredicto

#135 descubrió que `/empieza-aqui/` ya existía. Por eso la idea no es crear otra landing ni un quiz de perfiles: hay que **auditar y optimizar la página existente** usando rutas, búsquedas y abandono/demanda reales.

## Hipótesis original

Ampliar `empieza-aqui/` con rutas explícitas para diferentes lectores, p. ej. «si te gustó X, empieza por Y», reduciendo fricción de descubrimiento.

## Evolución

### Primera revisión → `PARTIAL_AUDIT`

- `/empieza-aqui/` ya existe;
- auditar rutas según tráfico/queries;
- optimizar sobre la URL actual;
- no crear duplicado.

### Matriz → `PILOTAR SOBRE EXISTENTE`

> mejorar rutas con analytics/search intents antes de crear otra landing.

### Autoridad final → `PARTIAL_AUDIT`

> «`empieza-aqui/` ya existe: medir rutas, búsquedas y abandono antes de ampliar.»

### Revalidación independiente

Estado mantenido.

## Estado actual observable

`empieza-aqui/index.html` sigue siendo una URL canónica indexable y se presenta como página de orientación:

- título «¿Por dónde empiezas?»;
- lead «Elige lo que vienes a buscar y entra por ahí»;
- índice/rutas para empezar;
- meta description que cubre obra actual, fantasía, autor, lecturas, herramientas, prensa y mapa;
- navegación hacia las áreas reales del sitio.

Esto reafirma que C.8 debe trabajar **sobre esta autoridad**, no crear `/para-ti/`, `/que-leer/` o un duplicado.

## Pregunta de auditoría correcta

No «¿podemos añadir más tarjetas?», sino:

- ¿qué tipos de visitantes llegan?
- ¿qué destinos buscan después?
- ¿qué queries conducen a la página?
- ¿qué rutas reciben clicks?
- ¿alguna intención importante queda sin salida?
- ¿hay rutas redundantes o con copy ambiguo?
- ¿móvil entiende la jerarquía sin exceso de opciones?

## Fuentes de evidencia

Prioridad:

1. Search Console/Bing para queries/landing;
2. analytics actual para clicks/navegación si la taxonomía ya lo permite;
3. búsqueda interna/Pagefind para intents/no-results;
4. preguntas reales de C.3;
5. testing cualitativo si hace falta.

No instalar otro tracker para responder C.8.

## Rutas editoriales, no pseudo-personas

Evitar perfiles inventados tipo «el lector aventurero» si no ayudan a decidir. Preferir necesidades observables:

- quiero conocer la obra actual;
- busco fantasía/Samuel/Noveris;
- quiero leer un fragmento;
- busco herramientas para escribir;
- quiero saber quién es el autor;
- soy prensa/profesional;
- busco recomendaciones/lecturas.

Las etiquetas exactas deben derivarse del catálogo y de la demanda actual.

## Relación con A.8/D.6

A.8 rechazó una página artificial de «orden de lectura» con dos libros no relacionados. D.6 rechazó un quiz general trivial. `/empieza-aqui/` es la alternativa válida: orientación sin fingir saga ni gamificación.

## Relación con D.11

Si una ruta lleva a un estado vacío/no disponible, D.11 debe ofrecer siguiente acción. C.8 no debe enviar a callejones sin salida.

## Relación con Pagefind

Queries internas sin resultado pueden descubrir necesidades. No confundir «no encontró resultado» con obligación de crear contenido; primero comprobar sinónimos/ranking y contenido existente.

## Diseño de auditoría posible

Reporte manual/machine-readable:

```text
route_label
href
intent
clicks/window (si existe)
landing_queries
has_clear_destination
mobile_order
notes
recommendation = KEEP | REWRITE | REORDER | ADD | REMOVE
```

Primer paso report-only; no modificar UI basándose en una semana ruidosa.

## Criterio para añadir una ruta

- necesidad real repetida;
- destino canónico existente y útil;
- no duplica otra opción;
- copy comprensible;
- suficiente prominencia proporcional a su importancia.

## Criterio para eliminar/reordenar

- ruta obsoleta;
- duplicidad;
- casi cero uso durante ventana razonable + sin importancia estratégica;
- destino cambiado;
- jerarquía que oculta la obra actual o tareas principales.

## Qué NO hacer

- nueva landing paralela;
- quiz artificial;
- 15 perfiles inventados;
- personalización opaca por tracking;
- ordenar solo por CTR si hay objetivos estratégicos;
- crear contenido para rellenar una ruta;
- esconder Samuel porque Manecillas sea principal;
- duplicar navegación global sin valor.

## QA si se modifica

- rutas crawlable HTML;
- foco/teclado;
- targets adecuados;
- reflow móvil;
- labels claros;
- canonical intacto;
- analytics events, si existen, no duplicados;
- destinos sin 404/noindex accidental;
- no dependencia JS para navegación esencial.

## Pasadas posteriores revisadas

Cuarta–decimoquinta: no cambian C.8. R.21/R.31 refuerzan usar demanda propia/externa con cautela. Pagefind ya existente puede ser fuente de señal, no otra implementación.

## Trazabilidad

- hipótesis original;
- revisión `PARTIAL_AUDIT`;
- repo cross-check de `/empieza-aqui/` existente;
- matriz `PILOTAR SOBRE EXISTENTE`;
- autoridad final `PARTIAL_AUDIT`;
- revalidación independiente;
- `empieza-aqui/index.html` actual.

## Recomendación para Clara/Claude

Ejecutar primero una auditoría sobre la URL existente. Solo después ajustar copy, orden o rutas concretas con evidencia. **No crear otra página de orientación.**