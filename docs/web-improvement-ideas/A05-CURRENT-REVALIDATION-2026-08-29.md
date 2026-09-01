# A.5 · Revalidación actual 2026-08-29

## Decisión cerrada

**Usar fuentes externas cuando mejoren verificabilidad y confianza; no como truco SEO.**

## Investigación actual

Google Search Central mantiene dos reglas útiles y suficientes:

1. enlazar a sitios externos puede ayudar a establecer confianza cuando se citan fuentes;
2. debe hacerse cuando tenga sentido para el lector y con contexto sobre lo que encontrará.

Google no prescribe una cuota de enlaces externos ni un beneficio de ranking por enlazar a dominios con determinada autoridad.

Fuente primaria:
- https://developers.google.com/search/docs/crawling-indexing/links-crawlable

La misma guía exige calificar enlaces compensados con `rel="sponsored"` o `nofollow`; para enlaces insertados por usuarios recomienda `ugc` o `nofollow`.

## Trigger objetivo

Añadir una fuente externa cuando una afirmación sea:

- normativa o procedimental;
- estadística o cuantitativa;
- atribuida a un tercero;
- temporal/cambiante;
- basada en un estudio, dataset o documentación externa;
- susceptible de generar una decisión del lector que mejore al poder verificar el origen.

No es obligatorio citar externamente:

- opinión o experiencia propia claramente presentada como tal;
- información sobre la propia obra cuyo origen canónico es el sitio/autor;
- ficción, sinopsis o proceso creativo propio salvo que se documente una investigación externa concreta.

## Jerarquía

1. fuente primaria/oficial;
2. estudio, paper o dataset original;
3. documentación del proveedor responsable;
4. fuente secundaria reputada cuando la primaria no resuelva la pregunta.

No usar DA/DR, listas de “authority sites” ni cuotas de enlaces como criterio editorial.

## QA permitido

La política no justifica un checker que obligue a insertar enlaces externos. Un QA automatizado solo es válido para errores objetivos, por ejemplo:

- enlace afiliado/pagado conocido sin `rel="sponsored"`;
- `target="_blank"` sin protecciones exigidas por el contrato del proyecto;
- URL externa rota si existe un proceso fiable que pueda comprobarla sin flakes.

## Estado para merge

`CONDITIONAL`. La PR cierra la política y los anti-patrones. No requiere runtime adicional mientras no aparezca un caso objetivo que el QA actual no cubra.