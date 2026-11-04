# Revisión global de la web — 4/11/2026

Esta ronda amplía la revisión de Search Console, Bing y Ahrefs al sitio publicado y al candidato de publicación. Se registra cobertura concreta; un control automatizado no equivale a una revisión editorial manual ni prueba ausencia de cualquier defecto.

## Cobertura y resultados

| Área | Alcance | Resultado |
|---|---|---|
| Producción HTTP y metadatos | Las 1.326 URLs del sitemap servido | 1.326 respuestas correctas; sin incidencias de título, H1, canónica, idioma, noindex o sintaxis JSON-LD. |
| Inventario y formularios del candidato | 1.335 documentos públicos | Contrato de documento/formulario superado. |
| Enlazado y descubrimiento | Grafo interno, registro, sitemap y mapa humano | Cero errores y advertencias; las cinco continuaciones del catálogo están incluidas. |
| Fechas | 1.714 elementos `time`, 1.369 bloques JSON-LD | Control de semántica temporal superado. |
| Controles estáticos transversales | 11 comprobaciones de SEO, seguridad HTML, codificación, navegación, recursos y presupuestos | Las once pasan. |
| Navegador sobre el artefacto publicable | 1.342 páginas, 4.119 archivos permitidos | [CI superada, sin errores de consola/red](https://github.com/davidpd89/web-escritor/actions/runs/41892955034/job/126794886604). |
| Accesibilidad automática | Cuatro bloques del sitemap completo | Los cuatro superados en la CI del candidato. |
| Catálogo y compras | 537 libros; 536 ISBN importados, muestra de 12 fichas, 63 editoriales, 81 opciones de filtros y 11 dispositivos | Suites de filtros, compras, fechas, URL compartible, navegación sin JS, fallos controlados y dispositivos superadas. |
| Adaptación de pantalla y texto | Ocho bloques de rutas; móvil, tableta, escritorio, zoom y espaciado | En curso; registrar el resultado antes del cierre. |

Los recuentos difieren por alcance: producción aún no contiene las cinco continuaciones nuevas; los documentos públicos incluyen utilidades y exclusiones deliberadas que no aparecen en el sitemap indexable.

También se capturaron 32 vistas de 16 familias a 390 y 1.280 px, sin desbordamiento horizontal, y se inspeccionaron las vistas móviles de las 16 familias. El barrido de textos visibles en las 1.342 páginas publicables no encontró placeholders `undefined`, `NaN` o marcadores de plantilla. [Evidencia de las rutas de producción y controles](evidencias/web-2026-11-04.json).

## Correcciones y normalización

- El catálogo crecía por encima del límite de lectura: seis páginas estáticas con un máximo de 96 libros, canónicas propias y búsqueda global que solo se activa con todos los lotes verificados. El fallo conserva navegación y tarjetas estáticas.
- Integradas en este candidato las correcciones de las PR #1153 (perfil y ofertas históricas) y #1154 (informe Bing), sin conflictos. Corregidos imagen principal, propiedad inválida de evento y entidades HTML importadas. El detalle consta en el [informe Ahrefs](ahrefs-2026-11-04.md).
- Sincronizadas las versiones y hashes de recursos en documentos y generadores. Las pruebas comprueban todos los lotes y esperan a que la navegación o la búsqueda estén listas; no se rebajan los contratos de integridad.
- Fijado Ubuntu 24.04 en los workflows de navegador que usaban la etiqueta móvil `ubuntu-latest`, tras un fallo reproducido al instalar dependencias en Ubuntu 26.04 (repositorio Microsoft: HTTP 403).
- Migración evaluada de Lighthouse CI 0.15.1 a 0.16.0, con Lighthouse 13.6.0 y Node 22+. Overrides limitados a glob >=9 y minimatch >=7: `npm audit` completo y de producción reportan cero vulnerabilidades. La recogida y las aserciones de la portada pasan con los umbrales existentes; no se cambian puntuaciones mínimas ni líneas base para ocultar regresiones. Los workflows usan el ejecutable del lockfile, no una instalación global independiente. [Release oficial](https://github.com/GoogleChrome/lighthouse-ci/releases/tag/v0.16.0).

- Las 150 fichas del directorio editorial pasan a «Ficha editorial · fuentes y fechas» y el índice habla de fuentes: no se presenta como recepción verificada un estado `unknown`. Se conservan fechas, fuentes y estados; no se inventa una revisión nueva de disponibilidad. El generador y sus pruebas de paridad, semántica y permisos pasan.

## Límites y cierre

Queda integrar y publicar las correcciones, completar la CI del último candidato y comprobar el despliegue antes de repetir el rastreo externo. No se reenvían formularios reales ni se generan correos de prueba a personas: los flujos funcionales usan pruebas controladas.

Ahrefs AI Visibility y Broken Backlinks requieren ampliar el plan; Lost no está disponible. Se documentan como datos no accesibles, no como ceros. La puntuación AI y el tráfico modelado no sustituyen analítica ni citas observadas. La normalización conserva las diferencias editoriales entre familias; no introduce un rediseño general por una recomendación heurística.
