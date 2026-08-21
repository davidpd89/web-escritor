# CUADERNO + ARTÍCULO V1 — MIGRACIÓN EJECUTABLE

Estado: scaffold de familia para Gate 4. Autoridad: 21 + 24 + 25 + 31 + 32 + 34 + 35 + 36.

## Fuente real auditada

- `cuaderno/index.html` de `implementacion-web-2026`.
- piloto: `cuaderno/fantasia-juvenil-espanola-portales-magia-coste/index.html`.
- baseline auditada: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`; refrescar drift antes de integrar.

No copiar el aspecto actual. Sí preservar contenido, rutas, schema, RSS, anchors y funciones enumerados en `data/cuaderno-preservation.json` y `data/article-preservation.json`.

## Por qué el HTML actual no es una referencia visual

Cuaderno actual conserva buena semántica y SEO, pero su composición depende de una columna estrecha y numerosos estilos inline. El artículo piloto repite esa estrategia y añade un bloque de definición redondeado, CTA inferior y FAQ con estilos locales. Es una baseline funcional, no la gramática V1.

## Scaffold V1

### `cuaderno.html`

Orden fijo:

1. shell global;
2. breadcrumb;
3. masthead editorial;
4. una pieza dominante;
5. ledger/archivo de todas las demás piezas;
6. utilidad `Sorpréndeme` subordinada y con fallback real;
7. continuidad con obra actual + Samuel + Autor;
8. newsletter;
9. footer global.

No transformar el archivo en tarjetas. Cuando haya 20, 50 o 100 piezas, la extensión natural es archivo/paginación/filtros textuales, no una cuadrícula de cards.

### `article-pilot.html`

Orden fijo:

1. shell + breadcrumb;
2. H1/lead/meta;
3. acciones subordinadas compartir/imprimir;
4. índice contextual cuando la longitud lo justifique;
5. prosa Newsreader;
6. nota AEO editorial si existe contenido equivalente;
7. H2/H3 y anchors originales;
8. FAQ nativa solo si existe contenido real;
9. continuidad editorial;
10. newsletter;
11. footer.

El lab contiene una muestra sustantiva del artículo para validar lectura. **Producción debe mantener el cuerpo completo actual**; no resumirlo para encajarlo en el scaffold.

## Decisiones cerradas

- Cuaderno no usa grid de posts.
- Primer artículo puede tener escala dominante, pero no se convierte en card hero.
- Archive = ledger con índice, tipo/tiempo, título y resumen.
- Imágenes solo si existe una fotografía/figura real que aporte; el índice funciona sin media.
- TOC no es global: aparece solo en artículos largos con estructura suficiente.
- progreso de lectura = enhancement discreto; no bloquea contenido, no altera historial, no scroll-jacking.
- share = Web Share → copiar enlace; sin SDKs sociales.
- print = CSS nativo; shell y utilidades no se imprimen.
- FAQ = `<details>`/`<summary>` sin dependencia.
- enlaces Samuel existentes se preservan; la continuidad global ya no convierte Samuel en el único CTA promocional porque Manecillas es la obra actual.
- newsletter mantiene IDs actuales y source `cuaderno`.
- `Sorpréndeme` conserva fallback `/mapa-del-sitio/` aunque su JS no cargue.

## Riesgo SEO detectado en el piloto

La FAQ visible actual y el `FAQPage` JSON-LD no son copias textualmente idénticas en al menos una respuesta. En integración NO copiar el JSON-LD a ciegas: reconstruir `FAQPage` desde las respuestas visibles finales o retirar ese schema si la FAQ deja de existir. Nunca conservar schema que describa contenido no visible.

## Responsive

- 1440+: masthead y artículo usan asimetría/rail; prosa no crece por tener más pantalla.
- 1024: rail de artículo sigue disponible, folio exterior desaparece.
- 768: índice editorial recompone a flujo; artículo mantiene navegación de secciones sin estrechar prosa.
- 390/320: una columna; títulos conservan escala editorial; TOC pasa a tira horizontal enlazable, no menú modal; acciones envuelven; formularios reutilizan base.

## Motion

No existe reveal global. El único comportamiento nuevo de esta familia es funcional:

- progreso de lectura;
- estado activo del TOC por `IntersectionObserver`;
- share/print.

No hay parallax, fade-up por párrafo, smooth-scroll obligatorio ni sticky storytelling.

## Gate 4

FALLA si ocurre cualquiera:

- parece un theme de blog;
- archive se resuelve con cards repetidas;
- prosa <58ch o excesivamente ancha en desktop;
- H1 largo fuerza fuente pequeña;
- TOC oculta/navega contenido con JS en vez de links reales;
- sin JS desaparece el artículo o su navegación principal;
- FAQ schema deja de corresponder a FAQ visible;
- se pierden RSS, rutas, anchors, fechas, author, internal links o newsletter;
- mobile pierde jerarquía editorial;
- reading progress o motion distraen de la lectura.
