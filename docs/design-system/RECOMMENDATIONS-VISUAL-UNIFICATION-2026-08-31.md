# Recomendaciones — contrato de unificación visual · 2026-08-31

## Trazabilidad

Continúa la cadena `DISEÑO -` después de Editoriales · fichas verificadas individuales.

Recomendaciones pertenece al contexto Cuaderno, pero no quedó cubierta por #269: utiliza su propia capa `assets/v1-recommendations.css` sobre el sistema editorial compartido. Esta intervención cierra esa familia sin reabrir el índice del Cuaderno ni mezclar las listas con los artículos generales.

Mantener Draft y no mergear fuera de orden.

## Superficies

Públicas/indexables detectadas:

- `/recomendaciones/`
- `/recomendaciones/portal-fantasy-espanol/`
- `/recomendaciones/magia-con-coste/`

Documento metodológico relacionado:

- `/recomendaciones/politica-de-recomendaciones/` — `noindex, follow`; mantener ese estado salvo decisión SEO independiente.

Antes de producción, reconciliar sitemap, robots y canonical reales.

## Objetivo

Unificar Recomendaciones con el sistema editorial azul/negro/dorado manteniendo una identidad propia de **selección editorial documentada**.

No debe convertirse en:

- escaparate de afiliación;
- grid comercial de productos;
- ranking de badges;
- colección de cards de libros;
- clon visual de un artículo normal del Cuaderno.

La página debe comunicar selección, criterio, evidencia bibliográfica y transparencia.

## Arquitectura a preservar

La capa local `assets/v1-recommendations.css` ya define:

- hero;
- índice de listas;
- método;
- contexto;
- disclosure editorial;
- listas numeradas;
- metadata bibliográfica;
- badges informativos;
- acciones y afiliación;
- reglas de impresión.

La intervención debe evolucionar este owner, no crear una hoja distinta por cada lista.

## Dirección visual

### Hub

- tratar `/recomendaciones/` como puerta a una colección editorial curada;
- jerarquía clara entre explicación del criterio y listas disponibles;
- mantener estructura abierta/ledger; evitar tarjetas de catálogo;
- números/folios pueden actuar como sistema de navegación editorial;
- azul/dorado como jerarquía y reglas, no como fondos de producto.

### Listas

- preservar la numeración como posición editorial, no como score científico;
- cada libro debe leerse como entrada razonada: título → autor → por qué encaja → datos/edición → acción;
- `Samuel entre mundos` puede identificarse como obra propia, pero no debe parecer promocionalmente privilegiada de forma engañosa;
- afiliación y relación del autor deben seguir visibles y comprensibles;
- ISBN/edición/evidencia deben permanecer documentales y subordinados a la lectura.

### Política de Recomendaciones

- tratarla como documento metodológico/de transparencia;
- conservar `noindex, follow`;
- visualmente coherente con la familia, pero más sobria que las listas;
- no convertirla en landing SEO.

### Color / tipografía

Referencia:

- azul editorial `#1d4f96`
- azul profundo `#0d2c57`
- dorado `#b8860b`
- pale blue `#eefaff`
- texto/neutros como soporte principal.

Yellowtail, si se incorpora, solo en aperturas o acciones muy selectivas. Nunca en datos bibliográficos, disclosure, ISBN o criterio de evidencia.

## Transparencia y contenido a preservar

- canonical/robots;
- WebPage/ItemList/Book/Breadcrumb schema;
- número y orden de obras;
- títulos, autores, ISBN y ediciones verificadas;
- texto que explica que el orden no es una medición científica si existe;
- disclosure de afiliación;
- identificación de obra propia;
- criterio editorial/evidencia;
- enlaces Amazon con `rel` apropiado;
- fechas de revisión/publicación;
- navegación contextual Cuaderno;
- share/print si existen;
- impresión de las listas;
- funcionamiento sin JavaScript del contenido principal.

No añadir nuevos libros ni cambiar posiciones dentro de una PR de diseño.

## Relación con `v1-editorial.css`

Las listas cargan el sistema de artículo compartido. Cualquier cambio global en `v1-editorial.css` procedente de la PR de artículos/temas debe comprobarse aquí como aislamiento/compatibilidad. Evitar arreglos locales que dupliquen o contradigan el contrato de lectura larga.

## QA requerido

Contrato browser de la familia con las cuatro rutas.

### Cobertura

- 1440/1280;
- 1024;
- seams reales, incluido 760/759 o los que defina CSS;
- 768;
- 420/419 si el listado cambia de dos pistas a una;
- 390/360/320;
- zoom 200 %;
- text spacing;
- teclado/focus;
- no-JS;
- print;
- cero overflow.

### Contrato factual

- número exacto de listas del hub;
- número exacto y orden de entradas por lista;
- `Samuel entre mundos` conserva su posición/label de obra propia según HTML heredado;
- disclosure de afiliación presente;
- ISBN/enlaces preservados;
- política sigue `noindex, follow`;
- schema ItemList/Book intacto.

### Visual

- numeración no parece una puntuación;
- acciones no dominan sobre criterio editorial;
- disclosures visibles;
- metadata no parece dashboard;
- long titles/ISBN/URLs refluencian;
- aislamiento hacia artículos generales de Cuaderno y `/cuaderno/`.

No relajar gates ni ocultar overflow.

## Revisión humana

Comprobar especialmente:

- equilibrio entre utilidad editorial y afiliación;
- que Amazon no se convierta en el foco visual;
- diferencia entre recomendación externa y obra propia;
- densidad de diez entradas en desktop y móvil;
- legibilidad de posiciones/números;
- método y disclosures;
- impresión real de una lista.

Seguir `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md` antes del merge.

## Definition of Done

- hub + dos listas + política coherentes;
- transparencia/afiliación preservadas;
- schema/orden/datos bibliográficos intactos;
- estilo azul/dorado integrado sin comercializar la página;
- impresión preservada;
- Cuaderno/artículos aislados;
- responsive/zoom/text-spacing/teclado/no-JS verdes;
- evidencia revisada;
- CI verde;
- Draft y sin merge automático hasta revisión física.
