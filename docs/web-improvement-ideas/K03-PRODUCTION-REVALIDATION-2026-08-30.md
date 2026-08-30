# K.3 · Revalidación de producción — afiliación

Fecha: 2026-08-30  
Base auditada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`

## Veredicto

`ALREADY_PARTIAL · REAL_AMAZON_AFFILIATE_DISCLOSED · EXPANSION_CONDITIONAL · NO_NEW_PROGRAMS`

## Evidencia directa

- La página de política de Recomendaciones explica públicamente que los enlaces con `tag=davidporto-21` son afiliados, que una compra puede generar comisión sin coste adicional y que la afiliación no determina inclusión ni orden.
- Samuel utiliza enlaces Amazon con `tag=davidporto-21` y atributos `rel` que incluyen `sponsored` y `nofollow`.
- `editorial-facts.json` conserva destinos de compra factuales de Samuel por separado; no todo destino comercial debe tratarse como afiliado.
- Las manecillas del recuerdo mantiene `purchaseUrl: null`, por lo que K.3 no autoriza crear enlaces afiliados o retailers no verificados para esa obra.

## Contrato

Un nuevo enlace afiliado solo entra cuando existen simultáneamente:

1. programa real y cuenta aprobada;
2. URL generada por ese programa;
3. destino comercial válido para la obra/producto;
4. disclosure visible aplicable;
5. marcado `rel="sponsored"` cuando corresponda;
6. criterio editorial independiente de la comisión.

No convertir todas las recomendaciones en afiliación ni inventar programas para completar cobertura.

Books2Read u otro agregador solo se reconsidera cuando exista una necesidad real de resolver múltiples retailers/ebook y una URL operativa verificable.

## Cierre

K.3 ya está parcialmente implementada de forma correcta. El trabajo futuro es ampliar caso por caso únicamente cuando exista un programa y destino real; no hace falta una nueva capa técnica.