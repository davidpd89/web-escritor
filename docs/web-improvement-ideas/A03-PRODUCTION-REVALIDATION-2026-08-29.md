# A.3 · Revalidación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #152  
Decisión operativa: **READY_NO_CODE · ALREADY_COVERED STRONGLY**

## Decisión cerrada

No se crea otro crawler de enlaces internos, no se añade un “link score” y no se fusionan responsabilidades que hoy están correctamente separadas.

La cobertura actual se divide en tres autoridades complementarias:

1. `scripts/check-internal-graph.py`
   - enlaces internos rotos;
   - páginas indexables huérfanas;
   - canonicals ausentes;
   - colisiones de canonical;
   - informe opcional de inbound counts.
2. `scripts/check-navigation-coverage.py`
   - schema efectivo del `content-registry`;
   - `parentId`, `hubId`, `relatedIds`;
   - navegación pública;
   - sitemap↔registry;
   - jerarquía Obras y herramientas.
3. `scripts/check-global-discoverability.py`
   - inventario público;
   - registry↔sitemap↔HTML indexable;
   - mapa del sitio humano;
   - shell/discoverability y destinos canónicos críticos.

Estas responsabilidades se solapan solo donde es útil como defensa en profundidad; no existe el hueco que justificaría un segundo auditor.

## Revalidación con información oficial actual

Fuente primaria de Google:
https://developers.google.com/search/docs/crawling-indexing/links-crawlable

La documentación vigente confirma:

- una página importante debe recibir al menos un enlace desde otra página del sitio;
- los enlaces deben ser `<a href>` rastreables;
- el anchor text debe ser descriptivo, conciso y contextual;
- **no existe una cantidad ideal o mágica de enlaces** que una página deba contener.

Esto valida exactamente el modelo actual: comprobar integridad y findability, no perseguir densidades o puntuaciones artificiales.

Fuente complementaria:
https://developers.google.com/search/docs/fundamentals/ai-optimization-guide

La guía 2026 para Search generativa mantiene los fundamentos normales de crawling/indexación y no exige un grafo interno especial para IA.

## Evidencia del repo actual

`check-internal-graph.py` ya:

- analiza HTML real;
- extrae enlaces `<a href>`;
- resuelve enlaces relativos/canónicos;
- excluye assets y superficies `noindex`;
- emite `ERROR` para enlaces rotos y colisiones de canonical;
- emite `WARNING` para huérfanos y canonicals ausentes;
- permite inspeccionar inbound counts sin convertirlos en ranking interno.

`check-navigation-coverage.py` evita que las relaciones semánticas del registry queden sin resolver o que rutas no públicas aparezcan en navegación/sitemap.

`check-global-discoverability.py` comprueba que una página indexable exista realmente en las superficies públicas que corresponden.

Además, el workflow `content-index-check.yml` ejecuta estas comprobaciones en CI, de forma que la capacidad no es solo código muerto.

## Alternativas descartadas definitivamente

1. **Segundo crawler** — produciría findings duplicados y dos definiciones de “orphan”.
2. **PageRank/link equity score casero** — daría falsa precisión y no responde a un contrato de producto.
3. **Número mínimo de enlaces internos por página** — Google declara que no existe un número ideal mágico.
4. **Meter el `content-registry` dentro de `check-internal-graph.py`** — duplicaría validaciones que ya pertenecen a `check-navigation-coverage.py` y `check-global-discoverability.py`.
5. **Auto-insertar enlaces** — puede degradar copy y relevancia contextual; los enlaces editoriales deben existir por utilidad humana.

## Trigger de reapertura

Solo se modifica esta arquitectura si aparece un fallo reproducible que los tres checks actuales no pueden detectar o clasificar, con un consumidor claro para la nueva señal. La mejora debe extender el checker propietario de esa responsabilidad, no crear un cuarto auditor genérico.

## Definition of Done final

- [x] checker de grafo revalidado contra `main`;
- [x] checker de navegación revalidado;
- [x] checker global de discoverability revalidado;
- [x] ejecución en CI confirmada por workflow;
- [x] guía Google actual contrastada;
- [x] no existe gap de código neto;
- [x] scope de cada autoridad queda definido para evitar duplicaciones futuras.

**Conclusión:** A.3 está terminada y protegida por CI. Añadir más infraestructura genérica empeoraría la mantenibilidad sin aumentar cobertura útil.
