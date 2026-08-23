# Z — Diseño final · familia Libro

Fuente de diseño: `20 — BOOK MASTER SPEC V1 — MANECILLAS · SAMUEL · JAULA` de Drive.
Base auditada: `implementacion-web-2026@4694799edc6d9c9e729b896cadda1eef9726d083`.

## Estado real

La familia Libro ya existe en producción V1 y no necesita reconstruirse desde cero:

- `las-manecillas-del-recuerdo/index.html` usa `book-page`, `book-hero`, portada responsive, lead, CTA, metadata ledger y `v1-book.css`;
- `v1-book.css` ya implementa grid 12 columnas, portada dominante, H1 editorial, ledger, prosa, fragmento, disponibilidad, relacionados, newsletter y recomposición responsive;
- la arquitectura semántica y el SEO se conservan.

Por tanto esta PR es de **cierre visual y coherencia de familia**, no de reemplazo masivo.

## Owner

Cerrar la familia de páginas de obra según doc 20:

1. Manecillas como piloto interno de máxima calidad.
2. Samuel con la misma calidad de familia, pero acento local procedente de su material real.
3. Jaula en estado neutro mientras no exista media/copy público autorizado.

## Contrato visual

- portada oficial como objeto principal, sin card, mockup 3D, tilt, reflejo, glow o lomo inventado;
- metadata como ledger/hairlines, no chips;
- prosa Newsreader con medida editorial;
- jerarquía visual clara: portada → título → lead → acción → metadata → lectura/contexto → disponibilidad;
- disponibilidad/compras claras pero subordinadas a comprender el libro;
- relacionados editoriales, no ecommerce;
- fotografía/documentos solo cuando sean reales y aporten;
- lightbox solo si una imagen merece inspección y con `<dialog>` accesible;
- color/acento local únicamente desde material real trazado por #83.

## Deltas a revisar contra el repo actual

### Z.1 — Manecillas

Mantener la base actual y ajustar contra artboards 320/390/768/1024/1440/1728:

- balance portada / H1 / lead / CTA sin reducir el título hasta aspecto de ficha comercial;
- metadata marginal en desktop y en flujo en móvil;
- CTA visible sin sticky buy bar;
- portada completa en móvil, no full-bleed;
- sin ornamento técnico visible que parezca parte factual del libro si no lo es;
- sin pérdida del contenido SEO actual.

### Z.2 — Samuel

Comprobar paridad de componentes, ritmo y calidad con Manecillas. La diferencia debe proceder del contenido/material real, no de crear una segunda web temática.

### Z.3 — Jaula

Mientras siga gated/noindex:

- nada de portada ficticia;
- nada de lobos, jaulas, hadas, Pontevedra, género, fecha o claim inventados;
- si hace falta masa visual, usar geometría neutral inequívocamente no documental;
- no View Transition a un asset inexistente.

### Z.4 — Fragmento / contexto / prensa-eventos / disponibilidad

Revisar que cada bloque existente siga la gramática del master:

- fragmento como momento de lectura, no accordion que esconda el valor principal;
- contexto con una pieza dominante + secundarios;
- prensa/eventos como ledger;
- retailers como enlaces/acciones identificadas, no mosaico de logos;
- related con una pieza principal + 2–4 secundarios.

## Coordinación

- #82 posee View Transitions Home→Manecillas y materialidad narrativa de Home; Z solo prepara el destino para que la pareja funcione.
- #83 posee procedencia/media/color.
- #61 conserva dimensiones/srcset/sizes y runtime específico existente.
- #67 conserva AVIF/WebP y frescura técnica.
- #76 conserva relación estructurada Book↔fragmentos.
- #57 conserva fechas/SEO editorial.
- #78 conserva QA mobile/resiliencia global.
- #84 certifica visualmente el resultado final.

## No hacer

- no reescribir facts/schema por estética;
- no inventar retailer, precio, premio, reseña o fecha;
- no borrar texto SEO para acortar la página;
- no crear un componente visual nuevo si ya existe equivalente V1 reutilizable;
- no meter motion decorativo por sección.

## Definition of Done

- Manecillas, Samuel y el estado neutro de Jaula comparten una familia inequívoca;
- Manecillas sigue dominando globalmente sin degradar Samuel en su propia ficha;
- artboards 320/390/768/1024/1440/1728 revisados;
- sin overflow ni pérdida a 200% zoom/text spacing;
- keyboard/focus/reduced-motion correctos;
- portada/media consumen #83 y no inventan procedencia;
- SEO/DOM/facts preservados;
- #84 puede certificar la familia sin excepciones visuales no documentadas.

PR DRAFT. No tocar `main`, no deploy, no auto-merge.