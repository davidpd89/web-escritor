# A.2 · Página pilar por universo narrativo

Fecha de revisión: 2026-08-28
Idea original: crear una página central de referencia para Samuel y otra para Las manecillas del recuerdo que agregue y enlace todo el contenido disperso.

## Veredicto

**ALREADY_COVERED / MEJORAR LOS HUBS EXISTENTES, NO CREAR OTROS.**

La necesidad legítima —que cada obra/universo tenga un punto canónico desde el que el lector pueda entender la obra y seguir hacia fragmentos, universo, prensa y contenido relacionado— ya está implementada. Crear ahora nuevas páginas “pilar” paralelas duplicaría intención, enlaces y autoridad de URLs que ya funcionan como hubs.

## Fuentes primarias

1. Google Search Central · Creating helpful, reliable, people-first content
   https://developers.google.com/search/docs/fundamentals/creating-helpful-content
   - Google recomienda un propósito claro y contenido satisfactorio para personas.
   - No existe una regla de Google que exija una “pillar page” por entidad o un número determinado de satélites.

2. Google Search Central · Link best practices
   https://developers.google.com/search/docs/crawling-indexing/links-crawlable
   - Las páginas importantes deben estar enlazadas desde otras páginas del sitio.
   - Anchor text y enlaces internos ayudan a usuarios y Google a entender relaciones.
   - No hay un número mágico de enlaces.

3. Google Search spam policies
   https://developers.google.com/search/docs/essentials/spam-policies
   - Crear páginas muy similares para capturar variaciones de búsqueda puede acercarse a doorway/scaled content abuse.

## Evidencia del repo actual

### Samuel

`/libros/samuel-entre-mundos/` ya es la URL canónica de la obra y contiene:

- canonical propio;
- `WebPage` + `Book` con `@id` estable;
- `BreadcrumbList` Inicio → Libros → Samuel;
- section-context con la propia obra y rutas relacionadas;
- enlaces a Noveris, fragmento, compra, editorial y recursos del ecosistema.

Crear `/universos/samuel/`, `/samuel/` o una segunda “página pilar” sería duplicar una entidad que ya tiene URL de referencia.

### Las manecillas del recuerdo

`/las-manecillas-del-recuerdo/` ya funciona como hub:

- canonical;
- `WebPage` + `Book` con `@id`;
- `BreadcrumbList` Inicio → Libros → Manecillas;
- section-context con “La novela”, Fragmentos y Ficha de prensa;
- metadatos editoriales y relación con su muestra.

### Noveris

`/universo/noveris/` es la superficie canónica del universo/ciudad ficticia de Samuel. No crear un segundo “hub del universo Samuel” que compita con Samuel + Noveris salvo que aparezca una necesidad editorial distinta.

### Hub de obras

`/libros/` ya agrupa el catálogo. La navegación contextual y el registry ya permiten relacionar las piezas.

## Qué sí aporta esta idea

No una nueva URL, sino una **auditoría de completitud de los hubs actuales**.

Un hub debe responder, cuando el contenido exista realmente:

1. qué es la obra;
2. cuál es su estado editorial verificable;
3. cómo leer una muestra;
4. dónde comprar cuando exista URL real;
5. qué contenido propio amplía la obra/universo;
6. qué recursos de prensa/eventos existen;
7. cómo volver al catálogo de obras.

No todos los hubs necesitan todas las secciones. La regla es resolver tareas reales, no llenar una plantilla SEO.

## Plan de mejora

### Fase 1 · inventario automático

Derivar desde `content-registry.json` las relaciones de cada obra, usando campos ya existentes (`parent`, `hub`, `relatedIds` o equivalentes). No añadir otra fuente de verdad si esas relaciones ya existen.

Salida orientativa:

```json
{
  "entity": "samuel",
  "canonicalHub": "/libros/samuel-entre-mundos/",
  "related": [
    "/fragmento/",
    "/universo/noveris/",
    "/clubes-de-lectura/samuel-entre-mundos/"
  ]
}
```

### Fase 2 · auditoría humana

Para cada relación:

- ¿el enlace ayuda al lector en ese contexto?
- ¿el anchor explica el destino?
- ¿hay una URL más canónica?
- ¿la relación es factual/editorial o solo SEO?

### Fase 3 · únicamente corregir gaps

Ejemplos de cambios legítimos:

- una pieza del Cuaderno sobre Samuel no enlaza de vuelta a la ficha cuando sería útil;
- la ficha no enlaza a un fragmento ya existente;
- la ruta de prensa existe pero está escondida de la navegación contextual.

## Código / integración propuesta

Preferencia: ampliar un checker existente, no crear un framework.

Posible extensión de `scripts/check-internal-graph.py`:

```python
# pseudo-interface
python scripts/check-internal-graph.py --entity samuel --report
```

Salida:

```text
ENTITY samuel
hub: /libros/samuel-entre-mundos/
related registered: 7
related with path to hub: 7
hub outbound to related: 5
informational gaps: 2
```

Las “informational gaps” no deben fallar CI salvo que el registry declare una relación contractual concreta.

## Tests

- cada `canonicalHub` declarado existe y es indexable;
- no hay dos hubs canónicos declarados para la misma entidad;
- los IDs relacionados existen;
- cualquier relación marcada como `required` tiene enlace real;
- `check-internal-graph.py` continúa con 0 broken links/canonical collisions;
- `check-global-discoverability.py` y sitemap/registry continúan sincronizados.

## Qué NO hacer

- crear un segundo hub de Samuel porque una herramienta SEO sugiera “pillar page”;
- duplicar la sinopsis para generar más superficie indexable;
- crear páginas “universo de Manecillas” si no existe un universo editorial que el lector necesite navegar;
- convertir un hub en un índice de enlaces sin contenido propio;
- producir páginas por personaje/trope solo para completar un cluster.

## Coste / beneficio

Beneficio de auditar hubs existentes: **medio/alto**, porque mejora navegación, descubrimiento y claridad de entidad sin aumentar deuda de URLs.
Beneficio de crear dos páginas nuevas: **negativo** en el estado actual por duplicación/canibalización potencial.

## Definition of Done

- [ ] confirmar en `content-registry.json` cuál es el hub canónico de Samuel, Manecillas y Noveris;
- [ ] inventariar relaciones existentes;
- [ ] corregir solo enlaces contextualmente útiles que falten;
- [ ] mantener una sola URL canónica por entidad/obra;
- [ ] no crear nuevas páginas “pilar” salvo nueva necesidad editorial demostrada;
- [ ] suites de internal graph/discoverability verdes.

## Recomendación de merge

**MERGE como decisión “ALREADY_COVERED + audit”.** La idea no autoriza nuevas páginas. Deja un criterio claro para mejorar los hubs ya existentes sin duplicarlos.