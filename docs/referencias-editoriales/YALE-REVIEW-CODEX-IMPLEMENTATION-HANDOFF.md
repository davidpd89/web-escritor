# The Yale Review → David Porto Díaz — handoff de implementación para CODEX

Fecha: 2026-08-25  
PR: #99  
Estado: laboratorio / clean-room / no runtime público

## 0. Objetivo

Este documento convierte la investigación de `yalereview.org/from-the-archives` en un plan ejecutable sobre el sistema real de `davidportodiaz.com`.

No propone copiar The Yale Review. La meta es reproducir **la cualidad** que hace que su web se sienta limpia, literaria, calmada y coherente:

- una sola retícula;
- jerarquía tipográfica fuerte pero no gigantesca;
- reglas en lugar de cajas;
- metadata pequeña y estable;
- fondo editorial neutro;
- variación de composición sin cambiar de lenguaje;
- muy poca elevación, radio o decoración de interfaz;
- contenido primero, conversión después.

La implementación debe conservar rutas, copy, SEO, schema, herramientas, banners V5, navegación y accesibilidad existentes.

---

# 1. Evidencia que manda

## A — verificado

1. La página `From the Archives` presenta una secuencia editorial extensa: H1 → vídeo → feature semanal → clusters temáticos → interludio/cita → Browse/filtros → ledger cronológico → paginación → footer/promoción.
2. Pentagram confirma GT Cinetype para el nameplate y la serif personalizada Yale de Matthew Carter para texto.
3. Yale describe Yale Display como una adaptación para gran tamaño con serifas más agudas, mayor contraste y tracking cerrado.
4. Meghan O'Rourke describe el sitio como deliberadamente libre de pop-ups, sobrecarga y sensacionalismo.
5. Yale News confirma la intención de una experiencia digital "beautiful, calm, contemplative" y usable tanto en teléfono como en ordenador.

Fuentes:

- https://yalereview.org/from-the-archives
- https://yalereview.org/article/editors-note
- https://news.yale.edu/2021/06/28/tyr-gives-readers-digital-space-read-and-contemplate
- https://www.pentagram.com/work/the-yale-review/story
- https://yaleidentity.yale.edu/core-identity-elements/yale-typefaces

---

# 2. Mapeo tipográfico: NO copiar fuentes propietarias

The Yale Review funciona por contraste entre una voz de marca y una voz editorial. Nuestra web ya tiene las piezas necesarias.

| Rol | Yale Review | David Porto actual | Decisión |
|---|---|---|---|
| Nameplate/marca | GT Cinetype | logo/identidad propia + `--font-ui` | NO imitar GT Cinetype. Mantener identidad propia. |
| Titular display | Yale/Yale Display | `--font-display: Instrument Serif` | Buen equivalente funcional. Mantener. |
| Lectura editorial | Yale serif | `--font-reading: Newsreader` | Buen equivalente funcional. Mantener. |
| UI/metadata | sans funcional | `--font-ui: Manrope` | Mantener. |

## Escala propuesta de laboratorio

No sustituir tokens globales de golpe. Probar primero estas escalas sobre las familias existentes:

```css
--yr-page-title: clamp(3rem, 5vw, 5.5rem);
--yr-section-title: clamp(2rem, 3.4vw, 3.75rem);
--yr-feature-title: clamp(2rem, 3.8vw, 4.25rem);
--yr-entry-title: clamp(1.35rem, 1.8vw, 2rem);
--yr-deck: clamp(1.05rem, 1.15vw, 1.22rem);
--yr-body: clamp(1.03rem, 1.06vw, 1.15rem);
--yr-meta: clamp(.74rem, .72rem + .08vw, .82rem);
```

### Razón

La web actual permite H1 de 7–8rem en varias familias. Esa escala tiene sentido para un hero narrativo puntual, pero no como gramática transversal. Yale obtiene jerarquía mediante contraste de tamaño + columnas + aire + reglas, no mediante titulares enormes en todas las páginas.

### Regla CODEX

- No cambiar `--text-hero` globalmente.
- Introducir topes por familia donde el H1 actual exceda el rango editorial.
- Mantener banners/libro si necesitan una escala mayor por dirección de arte.
- Cuaderno/artículos ya están cerca: modificar solo si la evidencia browser demuestra exceso.

---

# 3. Paleta: traducir funciones, no importar hex

NO convertir la paleta Pentagram en la paleta de David Porto.

Nuestro sistema ya tiene:

```css
--dp-ink: #171412;
--dp-paper: #F4EFE7;
--surface-page;
--surface-quiet;
--color-text;
--color-muted;
--color-border;
--dp-editorial-paper-soft;
--dp-editorial-paper-mid;
--dp-editorial-rule;
```

Eso cubre exactamente las funciones visuales que necesitamos.

## Decisión

1. Fondo general: papel/near-white del sistema V6.
2. Texto: tinta cálida, no `#000` puro.
3. Líneas: `--dp-editorial-rule` / `--color-border`.
4. Color: usar solo como acento semántico o editorial.
5. Evitar colorear cada bloque para diferenciarlo si la jerarquía puede explicarse con tipografía y retícula.

### Qué reducir

- fondos de tarjeta repetidos;
- degradados donde solo cumplen función decorativa;
- sombras suaves usadas para separar elementos que una regla puede separar mejor;
- múltiples colores de territorio en una misma pantalla sin necesidad semántica.

### Qué conservar

- art direction de banners de Home;
- color propio de obras cuando procede de portada/fotografía;
- estados de foco y contraste WCAG;
- superficies funcionales de herramientas cuando ayudan a operar.

---

# 4. Retícula propuesta

Usar la retícula actual; no introducir framework.

```css
--layout-max: 90rem;
--layout-wide: 76rem;
--page-gutter: clamp(1.25rem, 4vw, 4rem);
--grid-gap: clamp(1rem, 2vw, 2rem);
```

## Regla de composición

Pensar cada bloque en 12 columnas conceptuales:

- 12/12: H1, divisiones mayores, banners.
- 8/12 + 4/12: feature + contexto.
- 7/12 + 5/12: pieza principal + pieza secundaria.
- 4/12 + 4/12 + 4/12: tres piezas equivalentes solo cuando realmente lo sean.
- ledger: metadata estrecha + título/deck ancho + fecha/acción estrecha.

La retícula no tiene que existir en CSS como `repeat(12,1fr)` si las clases actuales ya resuelven esos spans con dos/tres columnas.

---

# 5. Líneas: el elemento que más hay que sistematizar

Yale usa reglas para dar estructura sin crear cajas.

## Contrato recomendado

```css
--yr-rule: 1px solid var(--dp-editorial-rule);
--yr-rule-strong: 2px solid color-mix(in srgb,var(--color-text) 70%,var(--dp-editorial-rule));
```

### Uso

- borde superior de secciones importantes;
- borde inferior de ledger rows;
- separación entre metadata y contenido cuando están en columnas;
- divisores de footer;
- filtros;
- nunca una línea solo porque “queda bonita”.

### No hacer

- regla + sombra + fondo + radio para explicar la misma separación;
- divisores negros de alto contraste entre todas las piezas;
- líneas verticales en móvil que creen columnas falsas.

---

# 6. Hover/focus

Yale no necesita levantar cards para demostrar interacción.

## Patrón para nuestra web

```css
.yr-link-title {
  text-decoration: none;
}
.yr-link-title:hover,
.yr-link-title:focus-visible {
  text-decoration-line: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: .18em;
  text-decoration-color: var(--color-accent);
}
```

En filas completas se admite un cambio tonal mínimo de superficie, pero NO `translateY`, zoom o sombra creciente.

Todos los focos deben seguir siendo más explícitos que los hovers.

---

# 7. Estado actual del repo: qué ya está bien

## `assets/v1-editorial.css`

Es la familia más cercana a Yale y debe ser la **referencia interna de transición**.

Ya contiene:

- `cuaderno-masthead` con retícula;
- feature desigual;
- metadata sticky;
- ledger sin cards;
- títulos serif;
- continuidad editorial con reglas;
- article header en 9fr/3fr;
- TOC + prosa + margen contextual;
- lectura en Newsreader;
- figuras con caption estructurado.

### CODEX

No reconstruir Cuaderno. Solo armonizar escala/color/líneas si el browser diff lo justifica.

---

# 8. Estado actual del repo: mayor divergencia

## `assets/v1-home-editorial-v3.css`

La Home actual tiene:

- banners aprobados;
- clusters editoriales;
- pero también grids con `padding:10px`, `gap:10px`, fondos de stone y piezas tratadas más como tiles.

No es un error. Es la decisión visual aprobada hasta ahora. Pero si queremos acercar el conjunto al grado de limpieza de Yale, esta es la zona que más puede simplificarse.

## Qué conservar

- orden editorial de Home;
- contenido y enlaces;
- banners V5 desktop/mobile;
- estructura lead + acompañantes;
- interludios necesarios;
- responsive actual.

## Qué probar

1. eliminar el fondo "tablero" de la grid;
2. reducir gaps visuales y reemplazarlos por hairlines;
3. hacer que las piezas compartan una misma superficie de papel;
4. reservar color para una o dos piezas especiales, no para cada card;
5. eliminar cualquier sombra de card que no comunique estado;
6. dejar más diferencia entre tamaños de pieza, no entre cajas.

### Regla

No aplicar esto a producción en una sola sustitución masiva. Hacer screenshot comparison Home 390/768/1440 antes/después.

---

# 9. Obras / Libro

La familia Libro puede conservar su teatralidad. Yale no debe borrar la identidad de la obra.

Aplicar solo:

- mismas reglas/hairlines que el resto;
- metadata con tamaño/tono global;
- CTAs sobrios;
- bloques relacionados como ledger cuando sea posible;
- márgenes alineados a `--page-gutter`;
- evitar cards decorativas añadidas alrededor del contenido.

La portada sigue siendo objeto visual principal. No convertirla en un archivo textual.

---

# 10. Herramientas

Herramientas necesita affordance funcional y no debe convertirse literalmente en una revista.

Traducción recomendada:

- herramienta destacada = feature editorial;
- resto = directorio/ledger de instrumentos;
- controles = rectangulares, claros, coherentes;
- evitar grids de cards idénticas cuando la prioridad es desigual;
- cada herramienta puede conservar su panel funcional interno.

La V6 ya rebaja visualmente `id-card`. El siguiente paso, si se aprueba, sería cambiar el hub, no los motores.

---

# 11. Autor / Prensa / Eventos

Usar una gramática de archivo documental:

- H1 contenido;
- intro de lectura;
- ledger cronológico;
- años/fechas como columna secundaria;
- fotos como documentos, no fondos decorativos;
- hairlines entre registros;
- CTA de prensa separado tras entregar información.

No usar cards distintas para cada aparición o evento si una fila editorial basta.

---

# 12. Header y navegación

NO copiar el header de Yale.

Su aprendizaje es estructural:

- marca;
- navegación editorial;
- acciones de conversión;
- búsqueda;
- subniveles visibles cuando aportan orientación.

Nuestro shell LRB/V4 ya resuelve estas funciones con otra estética. Mantenerlo y únicamente comprobar:

- que la barra contextual persiste en interiores;
- que el territorio actual queda claro;
- que no aparecen tres navegaciones compitiendo;
- que el header compacto no roba demasiado alto útil;
- que Explorar es una salida global clara.

---

# 13. Browse / filtros

El patrón Yale es útil para:

- Cuaderno;
- Editoriales;
- Convocatorias;
- Eventos;
- potencialmente Obras si aumenta el catálogo.

## Forma

- heading `Browse`/equivalente;
- selects sobrios;
- botón Apply/Filtrar;
- después ledger de resultados;
- reset visible cuando hay estado activo;
- query params si el filtro cambia contenido indexable/compartible.

No introducir filtros donde haya tan pocos elementos que solo añadan fricción.

---

# 14. Responsive

## Desktop >= 1024

- composición asimétrica;
- metadata en columna;
- títulos controlados, no hero-sized por defecto;
- ledger en 3 columnas funcionales.

## Tablet 640–1023

- pasar features complejas a 2 columnas simples o 1 según ancho;
- no reducir texto por debajo de legibilidad para conservar la retícula;
- metadata puede pasar sobre el título.

## Mobile <= 639

- una columna;
- mismo orden semántico;
- `--page-gutter` actual;
- reglas horizontales;
- categorías/fecha pequeñas pero >= tamaño usable;
- no cards comprimidas dos por fila;
- controles >=44px;
- imágenes `width:100%; height:auto` salvo art direction explícita.

---

# 15. Motion

La referencia se percibe calmada. En nuestra traducción:

- feedback 150–220ms;
- no reveal narrativo para cada fila;
- no hover con desplazamiento;
- banners pueden conservar su tratamiento actual;
- `prefers-reduced-motion` siempre elimina scroll suave/reveal no esencial.

---

# 16. Orden de implementación recomendado para CODEX

## Fase 0 — congelar evidencia

- capturas Home/Cuaderno/Obras/Herramientas/Autor/Prensa en 390 y 1440;
- registrar HEAD.

## Fase 1 — tokens funcionales, sin rediseño

- no cambiar fuentes;
- no importar hex Yale;
- consolidar que todos los interiores consumen papel/rule/muted V6;
- detectar hardcodes que contradicen esos tokens.

## Fase 2 — tipografía

- acotar H1/H2 excesivos por familia;
- mantener Instrument Serif + Newsreader + Manrope;
- validar 320/390/768/1024/1440/1728.

## Fase 3 — líneas y contenedores

- convertir separaciones redundantes en hairlines;
- retirar sombra/radio donde no sea funcional;
- mantener superficies funcionales de formularios/herramientas.

## Fase 4 — Home

- conservar banners y contenido;
- probar versión rule-based de clusters;
- screenshot diff;
- no mergear si empeora lectura o jerarquía.

## Fase 5 — familias

Orden recomendado:

1. Cuaderno: casi no tocar; usar como benchmark interno.
2. Autor/Prensa/Eventos: ledger documental.
3. Obras: limpiar metadata/relacionados.
4. Herramientas: jerarquía desigual en hub.
5. páginas auxiliares/findability/legal: asegurar mismo gutter/papel/rules.

## Fase 6 — QA

Obligatorio antes de integrar:

- Pa11y;
- Reflow;
- Chromium/Firefox/WebKit;
- Lighthouse;
- Global discoverability;
- 320,390,768,1024,1440,1728;
- no-JS en shell/rutas clave;
- keyboard/focus;
- `prefers-reduced-motion`;
- visual compare con baseline.

---

# 17. Definition of Done visual

La migración se considera lograda solo si:

1. Navegar Home → Libro → Cuaderno → Herramienta → Autor → Prensa parece una sola publicación.
2. El borde izquierdo de títulos/contenido coincide con el sistema de gutters salvo composiciones deliberadamente full-bleed.
3. La misma familia de regla separa contenido en todas partes.
4. Títulos grandes siguen siendo excepciones, no norma.
5. Metadata se reconoce instantáneamente en cualquier familia.
6. Hover no depende de movimiento/sombra.
7. No aparecen radios distintos sin razón funcional.
8. No hay una nueva paleta paralela a V1/V6.
9. No se pierden contenidos ni rutas por simplificar la composición.
10. Móvil no es una versión encogida: es una columna editorial coherente.
11. Ningún cambio sacrifica WCAG 2.2 AA.
12. La Home conserva la identidad propia de los banners y libros.

---

# 18. Qué NO debe hacer CODEX

- copiar CSS/DOM de yalereview.org;
- descargar o incluir GT Cinetype/Yale fonts;
- sustituir nuestras fuentes actuales solo por parecido;
- importar la paleta Pentagram como tokens literales sin necesidad;
- convertir toda la web en una réplica de `From the Archives`;
- borrar banners o portadas para ganar minimalismo;
- añadir animaciones porque la referencia parezca sofisticada;
- rediseñar motores de herramientas;
- alterar SEO/schema/rutas durante un cambio puramente visual;
- aplicar una refactorización global sin screenshots y browser QA.

La referencia debe reducir ruido y mejorar consistencia, no sustituir la identidad de David Porto Díaz.