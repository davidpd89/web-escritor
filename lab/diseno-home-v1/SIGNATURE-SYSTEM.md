# 39 — SIGNATURE SYSTEM V1 — FIRMA VISUAL, MOTION Y FALLBACKS

Estado: AUTORITATIVO. Implementable encima de `tokens.css + base.css + shell.css`.
Objetivo: que la web tenga una identidad reconocible sin depender de ilustración generada, cards, gradientes ni una librería de motion.

## S1 — Coordenada editorial

Formato visual: `01 / OBRA`, `02 / CUADERNO`, `03 / HERRAMIENTAS` y folios `A–01`, `A–02` en rail/margen.

No son badges. Son tipografía Manrope 600, 0.70–0.78rem, tracking 0.10–0.14em, mayúsculas, color muted. Se alinean con hairlines de 1px.
Uso: encabezados de territorio, filas de archivo, navegación Explorar, breadcrumbs especializados.
No usar en párrafos ni botones.

## S2 — Ruta viva

Base semántica: lista real de enlaces.
Decoración desktop: SVG `aria-hidden="true"` detrás/al lado del atlas. La ruta se construye desde centros de anclas reales.
Mobile <768: NO recalcular mapa x/y; se convierte en espina vertical editorial.

Estados:
- sin JS: ruta estática completa;
- JS + no-preference: `pathLength` progresa de 0→1 por sección visible;
- reduced-motion: ruta completa, sin marcador móvil;
- resize/orientation: recalcular una vez mediante `ResizeObserver`, no por frame.

Límite de movimiento: 560–800ms para cambios discretos; nunca retrasar navegación.

## S3 — Seam / continuidad entre páginas

Solo pares semánticos aprobados:
- Home → Las manecillas;
- Libros → ficha de libro;
- Cuaderno → artículo (fase posterior).

Implementación preferida: View Transition MPA nativa.
`view-transition-name` se aplica al objeto inequívoco (cubierta/título), no a contenedores completos.
Fallback: navegación normal.
Reduced-motion: deshabilitar animación personalizada.

Prohibido: wipe global idéntico entre todas las páginas.

## S4 — Ledger

Componente principal para información comparable: fechas, premios, datos bibliográficos, eventos, prensa, herramientas y archivos.

Estructura: índice/folio + dato primario + dato secundario + acción textual.
Separación: línea, espacio y tipografía; NO fondo de tarjeta.
Hover/focus desktop: la línea activa gana opacidad/2px y el texto secundario aparece si ya existe en DOM; ningún contenido esencial depende de hover.

## S5 — Archivo desplegable

Uso exclusivo: Prensa/archivo de imágenes o un archivo visual abundante.

Base: ledger completo.
Enhancement amplio >1024 y motion permitido: una escena sticky puede ordenar 4–8 piezas reales por fases. Inspiración: Sticky Grid Scroll.
Nunca usar con 2–3 elementos ni crear imágenes de relleno.
No instalar GSAP/Lenis por este único efecto en V1; primero intentar sticky CSS + WAAPI/IntersectionObserver. Si más tarde se usa código MIT, añadir THIRD-PARTY-NOTICES.

## S6 — Objeto-libro

La cubierta se trata como objeto editorial real:
- proporción real;
- sombra única `--shadow-object`;
- nunca mockup 3D sintético;
- nunca card contenedora.

En desktop puede cambiar de escala/posición entre dos anclas de una misma página o mediante View Transition entre páginas. En móvil permanece en flujo.

## S7 — Instrument bench

Herramientas no se presentan como SaaS.

Hub:
- catálogo tipográfico numerado;
- 17 utilidades visibles;
- filtro por texto/categoría opcional;
- una columna de descripción/contexto aparece en desktop al focus/hover, pero el enlace funciona directamente;
- en móvil la descripción vive bajo el título o en `<details>` secundario si es extensa.

Detalle:
- intro breve;
- “mesa” de dos áreas: entrada y resultado;
- controles rectangulares 4–6px, no pills;
- privacidad/local processing como línea documental, no green badge;
- resultado en `<dl>`/tabla/lista según semántica;
- share/copy solo si aporta.

## S8 — Marginalia de lectura

Cuaderno/artículos/legales largos:
- ancho de lectura 62–68ch;
- rail opcional con folio, sección actual y acciones;
- Newsreader en lectura;
- las notas viven fuera de la medida de prosa en desktop y vuelven al flujo en móvil.

No usar tooltips para notas necesarias.

## S9 — Marca sin assets

Test obligatorio: desactivar logo, retrato y portadas. La web debe seguir siendo reconocible por:
- tipografía;
- coordenadas/folios;
- hairlines;
- composición asimétrica;
- atlas;
- ledger;
- ritmo;
- paleta.

Si queda “una web beige elegante”, Gate 0 falla.

## CSS/API contract

- `@view-transition { navigation:auto; }` solo cuando ambas páginas hayan pasado estático.
- `@supports (animation-timeline: scroll())` puede mejorar ruta/seams, nunca reemplazar base.
- no `transition: all`;
- no animar `width/height/top/left` por frame cuando puede usarse transform;
- nada crítico con `content-visibility` que rompa anchors;
- `prefers-reduced-motion` manda sobre parámetros de URL/lab;
- no JS = contenido/navegación completa.

## Budget de firmas por plantilla

Home: S1 + S2 + S3 + S6.
Libro: S1 + S3 + S6 + ledger.
Cuaderno: S1 + ledger + S8.
Artículo: S1 + S8.
Autor: S1 + ledger + retrato real.
Prensa: S1 + ledger + S5 opcional.
Eventos: S1 + ledger cronológico.
Herramientas hub: S1 + S7.
Herramienta: S1 + S7.
Secundarias: S1 + ledger/lectura cuando proceda; cero motion narrativo.

Máximo: una firma narrativa de motion fuerte por página.
