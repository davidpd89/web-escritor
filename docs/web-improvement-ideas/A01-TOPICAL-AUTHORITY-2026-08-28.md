# A.1 · Auditoría de topical authority

Fecha de revisión: 2026-08-28
Idea original: organizar Cuaderno, Recomendaciones y Libros en clusters pilar + satélite explícitos.

## Veredicto

**PARTIAL_AUDIT / NO crear una arquitectura SEO paralela.**

La idea contiene una intuición útil —que las piezas relacionadas deben estar conectadas y que el sitio debe mostrar un propósito temático claro—, pero “topical authority” no es una feature de Google ni existe documentación oficial que diga que crear un número determinado de pillar pages o topic clusters produzca por sí mismo una mejora de ranking.

Google sí documenta señales/conceptos que justifican una auditoría temática real:

- contenido people-first, útil y completo;
- propósito/foco claro del sitio;
- experiencia/conocimiento demostrable;
- enlaces internos contextuales que ayuden a personas y a Google a encontrar páginas relacionadas;
- evitar producir gran cantidad de contenido para capturar búsquedas sin valor propio.

Por tanto, **sí merece mantener un mapa temático**, pero no construir páginas de relleno para “cubrir el cluster”.

## Evidencia primaria

1. Google Search Central · Creating helpful, reliable, people-first content
   https://developers.google.com/search/docs/fundamentals/creating-helpful-content
   - Google pregunta expresamente si el sitio tiene un propósito/foco primario y si el contenido demuestra experiencia/profundidad.
   - También advierte contra producir mucho contenido en muchos temas esperando captar tráfico.
   - E-E-A-T no es un ranking factor único; es un marco para evaluar señales de confianza/calidad.

2. Google Search Central · Link best practices
   https://developers.google.com/search/docs/crawling-indexing/links-crawlable
   - Google recomienda que toda página importante tenga al menos un enlace desde otra página del sitio.
   - Los enlaces internos y su anchor ayudan a usuarios y Google a entender la relación entre páginas.
   - No existe un número mágico de enlaces.

3. Google Search spam policies
   https://developers.google.com/search/docs/essentials/spam-policies
   - Doorway abuse y scaled content abuse hacen peligroso convertir “clusters” en cientos de páginas casi equivalentes orientadas a queries.

## Estado real del repo

No partimos de cero. Ya existen piezas que cumplen la función legítima de un cluster sin llamarlo así:

- `/cuaderno/temas/` y `/cuaderno/temas/fantasia-de-portales/`, generadas por `scripts/build-topic-collections.py`;
- `/recomendaciones/` como familia de descubrimiento;
- `/libros/` como hub de obras;
- hubs específicos de Samuel, Manecillas y Noveris;
- `data/content-registry.json` como inventario canónico;
- `scripts/check-internal-graph.py`, que detecta enlaces rotos, páginas indexables huérfanas, canonicals ausentes y colisiones;
- `scripts/check-global-discoverability.py`, que reconcilia registry/sitemap/mapa;
- navegación contextual y relaciones internas ya introducidas en PR anteriores.

La PR #35, ya integrada en la historia del proyecto, documenta específicamente el sistema de topic collections del Cuaderno. La PR #1 documentó un grafo con 0 huérfanas/0 enlaces internos rotos en el release auditado.

## Qué sí haría

### 1. Inventario de temas, no nuevas URLs

Derivar un informe desde `content-registry.json` con, como mínimo:

```json
{
  "topic": "fantasia-de-portales",
  "hub": "/cuaderno/temas/fantasia-de-portales/",
  "members": [
    "/cuaderno/que-es-el-portal-fantasy/",
    "/cuaderno/portal-fantasy-vs-fantasia-epica/",
    "/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/"
  ]
}
```

Solo si el registry no expresa ya suficiente relación. No crear un segundo registry si `relatedIds`, `parent`, `hub` o campos equivalentes ya resuelven el problema.

### 2. Medir cuatro cosas

- páginas importantes sin enlaces entrantes;
- hubs con miembros que no enlazan de vuelta al hub cuando sea útil para el lector;
- artículos que compiten por la misma intención principal;
- temas con muchas URLs de poco valor o sin demanda/propósito editorial claro.

### 3. Usar Search Console como evidencia de oportunidad

Antes de crear una nueva página pilar, exigir al menos una de estas señales:

- varias queries relacionadas ya aterrizan en páginas distintas y existe canibalización/confusión;
- hay varias piezas útiles que necesitan un índice humano;
- el lector tiene una tarea concreta que el hub resolvería mejor;
- existe contenido propio/original suficiente para que la página tenga valor aunque Google no existiera.

## Qué NO haría

- crear una pillar page por cada keyword;
- generar satélites solo para “completar el cluster”;
- repetir definiciones entre Cuaderno/Recomendaciones/Libros;
- usar densidad de keywords o número de páginas como KPI;
- medir “topical authority score” de una herramienta externa como si fuera una métrica de Google;
- crear páginas del tipo `portal-fantasy-para-X`, `portal-fantasy-para-Y` con cambios mínimos;
- convertir el mapa temático en una taxonomía visible más compleja que la navegación que ya funciona.

## Implementación propuesta si Claude quiere materializar el audit

### Opción A — reutilizar checker existente (preferida)

Extender `scripts/check-internal-graph.py --report` para producir JSON opcional:

```bash
python scripts/check-internal-graph.py --report --json artifacts/internal-graph.json
```

Campos útiles:

```json
{
  "url": "/cuaderno/que-es-el-portal-fantasy/",
  "inbound": 6,
  "outbound": 9,
  "hub": "/cuaderno/temas/fantasia-de-portales/",
  "topic": "fantasia-de-portales"
}
```

No imponer mínimos globales; solo reportar y dejar thresholds específicos en tests donde exista contrato editorial.

### Opción B — script separado

Solo si acoplar topic metadata al checker de enlaces lo complica demasiado:

`scripts/report-topic-coverage.py`

Entrada: `data/content-registry.json`.
Salida: `artifacts/topic-coverage.json`.
Modo `--check`: falla únicamente ante incoherencias objetivas (hub inexistente, miembro inexistente, IDs duplicados), no por “tener pocas páginas”.

## Tests

- ningún miembro declara un hub inexistente;
- ningún hub declara miembros inexistentes;
- toda URL indexable importante conserva al menos un inbound link, usando el contrato actual de `check-internal-graph.py`;
- no introducir una segunda taxonomía que contradiga `content-registry.json`;
- builder de topic collections sigue `--check` verde;
- sitemap/registry/global discoverability siguen verdes.

## Coste / beneficio

Beneficio esperado: **medio** como gobernanza editorial y enlazado interno; **no cuantificable como boost directo de ranking**.
Coste: bajo si se reutiliza el registry/checker; alto y no justificado si implica crear muchas páginas nuevas.
Riesgo: scaled content/canibalización si se interpreta como obligación de cubrir keywords.

## Definition of Done

- [ ] confirmar qué campos actuales del registry ya expresan topic/hub/related;
- [ ] ejecutar el checker actual y guardar baseline de inbounds/orphans;
- [ ] solo añadir metadata nueva si falta una relación que realmente usemos;
- [ ] no crear ninguna URL nueva solo para SEO;
- [ ] si se implementa JSON de cobertura, añadir test de schema/paridad;
- [ ] revisar con Search Console cualquier nueva oportunidad antes de construir un hub adicional.

## Recomendación de merge

**MERGE como decisión/plan.** No autoriza una “reestructuración SEO”. Autoriza únicamente una auditoría de relaciones temáticas sobre las autoridades ya existentes.