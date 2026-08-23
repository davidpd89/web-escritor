# AA — Diseño final · Cuaderno + artículos

Fuente de diseño: `21 — CUADERNO + ARTÍCULO MASTER SPEC V1` de Drive.
Base auditada: `implementacion-web-2026@4694799edc6d9c9e729b896cadda1eef9726d083`.

## Estado real

Esta familia también está avanzada:

- `/cuaderno/` ya usa masthead editorial, pieza destacada, archivo ledger y continuidad;
- `assets/v1-editorial.css` ya evita grid de cards y usa jerarquía desigual, tipografía editorial y ledger;
- los artículos ya tienen H1/deck, metadata, TOC, prosa Newsreader, figuras, blockquotes, tablas, fuentes, related y print;
- el reading progress existente es una función preservada del sitio y no se elimina por una preferencia histórica del master: se integra de forma discreta y se valida, no se duplica.

Por tanto AA es una PR de **refinamiento de lectura, ritmo, microtipografía y continuidad**, no una reconstrucción.

## Owner

### Cuaderno

- apertura de publicación editorial, no blog-template;
- títulos como interfaz;
- una pieza destacada cuando haya motivo real;
- archivo de filas/ledger, nunca 3×N cards;
- metadata textual, sin chips decorativos;
- imágenes solo cuando aporten;
- profundidad/agrupaciones visibles solo si el corpus real las justifica.

### Artículo

- H1/lead/meta con jerarquía fuerte;
- lectura Newsreader 58–72ch;
- TOC solo cuando estructura/longitud lo justifique;
- notas marginales en desktop e inline en viewport estrecho;
- figuras reales, captions, blockquotes, tablas y fuentes con composición editorial;
- related por relación real;
- share/copy/print subordinados a la lectura;
- newsletter sin interrumpir el primer tercio.

## Deltas a cerrar

1. Revisar artboards 320/390/768/1024/1440/1728 con títulos y URLs largos reales.
2. Aplicar microtipografía del doc 35 cuando se cruce ese contrato.
3. Evitar que el TOC sticky comprima lectura o oculte foco; inline cuando el viewport no lo sostenga.
4. Mantener el reading progress existente como función preservada pero sin convertirlo en elemento protagonista.
5. Preparar pareja semántica Cuaderno→artículo para View Transition solo si existe una media/título inequívoco y el doc 27 lo mantiene.
6. Validar print CSS con H1, autor, fecha, cuerpo, figuras/pies, fuentes y URL útil.
7. Preservar fechas published/modified honestas y schema actual.
8. No forzar hero image cuando no exista una imagen buena.
9. No crear filtros/búsqueda solo por decoración; dependen de volumen real.

## Coordinación

- #57 posee fechas visibles y SEO editorial.
- #63 posee taxonomía analítica; ningún texto de usuario entra aquí.
- #78 posee QA mobile/resiliencia global.
- #83 posee procedencia/media/color.
- #84 certifica identidad/craft final.
- #61 conserva runtime compartido y funciones legacy preservadas.
- #68 conserva arquitectura global/navigation.

## No hacer

- no borrar artículos o texto SEO para simplificar la composición;
- no grid uniforme de cards;
- no tabs/infinite scroll por comodidad;
- no hero image ficticia;
- no fade-up de cada H2 ni stagger de archivo;
- no social SDKs ni barra sticky lateral.

## Definition of Done

- Cuaderno parece publicación editorial viva y no blog de plantilla;
- artículos mantienen medida y ritmo de lectura excelentes;
- todos los layouts sobreviven a 320px/200% zoom/text spacing;
- TOC/notas/figuras/tablas/URLs largas tienen fallback robusto;
- print limpio;
- teclado/focus/reduced-motion correctos;
- contenido/SEO/schema preservados;
- #84 puede evaluar coherencia Home↔Cuaderno↔artículo sobre un SHA único.

PR DRAFT. No tocar `main`, no deploy, no auto-merge.