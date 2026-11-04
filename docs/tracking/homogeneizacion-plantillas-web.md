# Seguimiento futuro — Homogeneización de diseño, tipografía y plantillas de toda la web

**Estado:** INVESTIGACIÓN PENDIENTE · SIN IMPLEMENTACIÓN · BAJA PRIORIDAD (2026-11-04).

## Problema y objetivo

La web ha crecido por secciones con soluciones CSS, tamaños, fuentes, plantillas y excepciones específicas. Esto aumenta la posibilidad de que un cambio en una familia provoque reflow, inconsistencias visuales o nuevas correcciones puntuales. Queremos un **sistema editorial de diseño y generación compartido**: cualquier página nueva deberá ajustarse a un contrato de su familia, sin inventar estilos ni HTML distintos cada vez.

**El referente que ya funciona:** el catálogo de libros: `docs/contrato-tarjeta-libro.md`, datos normalizados, `scripts/build-reading-catalogue.py`, plantilla y pruebas comunes. Extender el método a las demás familias, sin rehacer el catálogo ni imponer un único diseño a todas.

## Evidencia para investigar

- `assets/v1-fonts.css` configura Newsreader, Instrument Serif, Manrope, Allura y fuentes de respaldo, incluyendo variantes cursivas y valores `size-adjust`, `ascent-override` y `descent-override`. `tests/test-v1-font-fallback-metrics-contract.py` comprueba valores concretos.
- En una investigación del **04-11-2026**, Claude detectó que ciertas fuentes de respaldo rendían entre **22 % y 77 % más anchas** que las webfonts esperadas en las mediciones realizadas. Un ajuste exploratorio redujo las diferencias medidas a aproximadamente **±2,3 %**. Son resultados del entorno de esa sesión, **no una validación multisistema** ni una razón para sustituir cifras sin comprobarlas. La carga inicial, las fuentes opcionales y las capturas de regresión pueden comportarse de forma distinta según navegador, caché y sistema operativo.
- Ya existe una base compartida (`assets/v1-shell.css`, `scripts/build-site-shell.py`), pero la coexistencia de varios estilos y excepciones por página exige inventariar qué reglas son deliberadas y cuáles son deuda técnica.
- El propio test de métricas fija números: si se corrigen los fallbacks, deben revisarse a la vez las pruebas y las líneas base visuales, **sin actualizar snapshots para ocultar una regresión**.

## Investigación y plan de aplicación futuros

1. **Inventariar por familia:** portada, libros y autores, editoriales, Cuaderno/artículos, obras y fragmentos, universo, convocatorias, prensa, herramientas, laboratorio, etc. Registrar fuentes y roles, tamaños, pesos, interlineados, espaciados, anchuras de lectura, breakpoints, componentes y overrides. Identificar duplicados, colisiones y excepciones necesarias.
2. **Definir un contrato tipográfico y de diseño único como fuente de verdad:** tokens por *función* (UI, lectura larga, títulos, destacado, textos auxiliares) y componentes reutilizables. No es obligatorio usar **una sola tipografía**: se permiten diferencias editoriales intencionadas, pero declaradas y limitadas. Los fallbacks deben conservar métricas compatibles y comportamiento comprobado.
3. **Diseñar plantillas/contratos por familia:** datos estructurados → normalización → plantilla común → comprobaciones → publicación. Una página nueva debe heredar estructura, cabecera/pie, tipografía, accesibilidad y responsive sin introducir CSS específico por defecto. Reutilizar los generadores y el shell existentes; no crear un CMS paralelo sin demostrar que hace falta.
4. **Validar en condiciones reales:** primera visita sin caché y visita con caché, fuente cargada y fallback, normal/cursiva, varios navegadores y plataformas, 320/768/1024/1440 px y zoom al 200 %. Medir CLS, saltos de línea y altura, desbordamientos, objetivos táctiles, contraste y regresión visual. Mantener pruebas representativas por familia y auditoría completa periódica, sin multiplicar GitHub Actions.
5. **Migrar gradualmente:** fijar métricas y capturas de referencia; pilotar en dos familias distintas; corregir reglas compartidas, no páginas individuales; comprobar paridad, SEO, accesibilidad, rendimiento y enlaces; extender únicamente después de resultados medidos. Preservar variantes especiales justificadas y documentadas.

## Criterios de aceptación futura

- Existe un inventario de diferencias y una decisión documentada: qué se unifica y qué se conserva por identidad editorial.
- Nuevas páginas de cada familia se crean desde sus datos y plantillas, con tokens y componentes compartidos, **sin retoques manuales por página** salvo excepciones justificadas.
- Los defectos comunes se corrigen una vez en el origen y una regresión automatizada impide que vuelvan.
- Primer render/fallback, CLS, accesibilidad, legibilidad y diseño responsive no empeoran respecto a la referencia verificada.
- Menos CSS duplicado y menos fallos repetidos en CI, con mediciones antes/después. Ninguna promesa de «cero fallos» sin evidencia.

## Fuera de alcance de esta PR

**Solo seguimiento/investigación futura.** No modificar ahora CSS, fuentes, HTML, plantillas, capturas, tests, reglas de CI ni despliegue; no iniciar migraciones ni fusionar esta PR como si implementase la mejora. Retomarla después de cerrar las prioridades actuales, convirtiendo el plan en PR de implementación pequeñas y verificables.
