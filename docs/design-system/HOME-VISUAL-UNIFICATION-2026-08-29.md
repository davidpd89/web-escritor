# HOME · contrato de unificación visual

Fecha: 2026-08-29  
Rama: `design/sitewide-visual-unification-home-2026-08-29`  
Ámbito de esta primera fase: **HOME** (`/`)  
Objetivo posterior: extender el mismo lenguaje visual página a página sin volver a introducir el diseño anterior.

## 1. Por qué existe esta PR

La HOME ya ha cambiado de lenguaje visual: azul + negro + dorado, marcos de esquina, líneas/rails conectados, títulos y eyebrows jerarquizados, enlaces de acción en Yellowtail y una fotografía de autor enmarcada con el nuevo sistema.

El problema actual no es definir otro diseño. Es **terminar de aplicar el diseño ya aprobado con consistencia microscópica**: cada borde, rail, separador, enlace, espacio y componente debe obedecer al mismo contrato.

Esta PR será la rama de trabajo dedicada a esa migración. Se empieza por la HOME. No se debe aprovechar para rediseñar contenidos, SEO, arquitectura o componentes de otras páginas salvo que un componente compartido sea imprescindible para corregir la HOME.

## 2. Baseline comprobado antes de empezar

El handoff de diseño indicaba que la ronda 7 seguía sin publicar. Ese dato ya está obsoleto.

Estado real de `main` al abrir esta rama:

- HEAD de partida: merge de PR **#162** (`291c8c677aaa7df635142687d1a6848e80ffcaa2`).
- #162 ya integró la tipografía Yellowtail en la regla base `.yale-text-link` y en `.home-event__link`.
- #162 ya aumentó el aire posterior a los section-breaks de 8px a 28px.
- #161 ya había añadido marcos de esquina a Samuel y a las portadas de «Libros y territorios», eliminado márgenes entre secciones que cortaban rails, corregido el enlace «Escribir», alternado los bordes de iconos sociales y añadido `?v=6` a `v1-home.css`.
- #160 ya había extendido eyebrows/títulos azul+dorado y sustituido parte de los grises por azul/dorado.

Regla: **no repetir esos cambios ni trabajar desde una ronda antigua**.

## 3. Sistema visual canónico que esta PR debe preservar

### Colores

- Azul principal: `#1d4f96`.
- Dorado: `#b8860b`.
- Negro/texto: conservar el negro del sistema actual donde corresponda.
- Azul del logotipo/«ESCRITOR»: `#0a4d9f`.

`#0a4d9f` es una excepción deliberada para elementos que deben coincidir con el azul impreso en el logotipo/header. **No debe convertirse en un segundo azul general de la página.**

### Motivos

1. Avatar/header: `assets/masthead-avatar-frame-blue.svg`.
2. Portadas: `assets/corner-bracket-blue-gold.svg`.
3. Separadores de sección: doble raya horizontal azul/dorada + rombo centrado.
4. Rails: raya vertical azul por `background-image`, no `border-left` subpíxel.
5. Eyebrows de sección: Yellowtail + subrayado `assets/highlight-8-blue-rect.png`.
6. H1/H2 de sección: relleno azul + trazo dorado fino/translúcido.
7. Acciones «Abrir / Ver / Todas…»: Yellowtail, azul principal, sin subrayado de texto.

## 4. Principios técnicos obligatorios

- No reintroducir `border-width` fraccional para rails que deben casar con otros trazos; usar gradientes de fondo.
- No usar `background:` shorthand sobre elementos que ya sostienen un rail mediante `background-image` salvo que se reponga expresamente el rail.
- Antes de declarar corregido un problema de cascada, buscar todas las reglas del selector en `v1-home.css`, `v1-home-editorial-v3.css` y hojas compartidas.
- Un rail que deba llegar al siguiente divisor necesita que el elemento que lo dibuja se estire hasta el final de su fila/columna.
- No restaurar `margin-top` entre secciones para «dar aire»: ese margen vuelve a separar físicamente el rail vertical del section-break. El aire debe resolverse **dentro** de la sección anterior o después del propio divisor.
- Verificación final: captura + medidas/`getComputedStyle`; una captura sola no cierra un bug.
- La revisión responsive forma parte del fix. No arreglar escritorio rompiendo ≤1100px o móvil.

---

# 5. Auditoría HOME · primera tanda

## HOME-01 · Samuel: rail vertical y separadores horizontales no se unen

**Estado:** CONFIRMADO / BUG ESTRUCTURAL  
**Prioridad:** alta

### Síntoma

En «Samuel entre mundos», las rayas horizontales bajo «Del cuaderno», «Crónica» y «Comprar» terminan sin tocar la raya vertical que separa visualmente el bloque del libro.

### Causa real

El DOM de `createYaleSamuelFeature()` construye:

```text
.yale-feature__grid--reverse
├── .yale-feature__stack
│   ├── .yale-feature-card  → horizontales
│   ├── .yale-feature-card  → horizontales
│   └── .yale-feature-card
└── .yale-feature-book      → vertical
```

La vertical vive hoy como `background-image` en `.yale-feature-book`, es decir, en el **segundo elemento de la grid**. Las horizontales viven en las tarjetas del **primer elemento**. Entre ambos existe:

```css
gap: clamp(1.75rem,4vw,3rem);
```

Por construcción, esas líneas no pueden tocarse. No es un problema de grosor ni de caché.

### Solución A — recomendada

En escritorio (`min-width:1101px`), mover visualmente el rail al borde derecho de `.yale-feature__stack` y retirar solo el `background-image` vertical de `.yale-feature-book`.

Ventajas:

- las horizontales terminan exactamente en el mismo borde que dibuja la vertical;
- conserva el `gap` editorial entre stack y ficha del libro;
- no altera el contenido ni el DOM;
- permite conservar el comportamiento actual de la versión apilada ≤1100px hasta validarlo específicamente.

Esquema objetivo:

```css
@media (min-width:1101px) {
  html.v1[data-lrb-home="true"] .yale-feature--samuel .yale-feature__stack {
    background-image:linear-gradient(90deg,#1d4f96,#1d4f96);
    background-repeat:no-repeat;
    background-size:2.5px 100%;
    background-position:top right;
  }

  html.v1[data-lrb-home="true"] .yale-feature--samuel .yale-feature-book {
    background-image:none;
  }
}
```

No retirar a ciegas el `padding-left` del libro: también participa en el espacio interior de la ficha.

### Solución B — descartada salvo problema visual de A

Eliminar/reducir el `gap` exterior y hacer que el rail siga viviendo en el libro.

Problema: obliga a rehacer el ritmo horizontal de toda la feature para resolver algo que puede solucionarse en el seam. Es más invasiva y acerca demasiado ambas columnas.

### QA

- 1440/1280: horizontales y vertical se tocan sin hueco.
- El rail conserva 2.5px visuales.
- La última tarjeta no crea una horizontal extra.
- ≤1100px: no aparece un rail lateral absurdo ni se pierde el rail previsto en la composición apilada.
- La sección siguiente sigue conectando correctamente donde corresponda.

---

## HOME-02 · «Eventos y encuentros»: foto principal sin marco del nuevo sistema

**Estado:** CONFIRMADO / INCONSISTENCIA VISUAL  
**Prioridad:** alta

### Síntoma

La fotografía destacada de la Feria del Libro aparece prácticamente desnuda; no recoge el tratamiento de marco mínimo que ya define la identidad en la fotografía del header/avatar.

### Estado actual

`.home-event__media` solo conserva un `border-bottom:1px solid #b8860b` y recorte 4/5 en desktop para el evento principal.

### Solución A — recomendada

Marco rectangular mínimo de dos tonos, sin redondeo ni ornamentación adicional:

```css
html.v1[data-lrb-home="true"] .home-event--lead .home-event__media {
  border:1px solid #1d4f96;
  box-shadow:0 0 0 2px #fff, 0 0 0 3px #b8860b;
}
```

Racional: traduce el doble anillo azul/dorado del avatar a una fotografía rectangular sin fingir que es una portada. Debe ser un detalle, no una tarjeta decorativa.

### Solución B

Reutilizar los corner brackets de las portadas.

No recomendada: el motivo ya significa «objeto/libro» en la HOME. Repetirlo en una foto de evento diluye esa semántica y carga demasiado el bloque.

### QA

- No cambia el aspect-ratio ni desplaza el layout.
- No queda cortado por `overflow` de un ancestro.
- 16:9 en ≤1100px sigue funcionando.
- Contraste visible sobre fondo blanco sin parecer un marco grueso.

---

## HOME-03 · Separador anterior a «Para escribir»: demasiado pegado al final de Samuel

**Estado:** CONFIRMAR VISUALMENTE EN PLAYWRIGHT / CAUSA PROBABLE IDENTIFICADA  
**Prioridad:** alta

### Restricción importante

No devolver `margin-top` a `.yale-home-section`. #161 lo puso correctamente a `0` para evitar que el rail vertical se corte antes del section-break.

El cambio de #162 (`padding-top:28px`) da aire **después** del divisor, entre raya y título. No da aire entre el final visual de las tarjetas de Samuel y el divisor.

### Solución A — recomendada si la medición confirma el síntoma

Crear el aire al final de la feature de Samuel, no entre secciones. La caja que dibuja el rail debe incluir ese aire para que la vertical continúe hasta el divisor.

Candidato:

```css
html.v1[data-lrb-home="true"] .yale-feature--samuel .yale-feature__stack,
html.v1[data-lrb-home="true"] .yale-feature--samuel .yale-feature-book {
  padding-bottom:clamp(.9rem,1.6vw,1.25rem);
}
```

Antes de fijarlo hay que medir el resultado de HOME-01: si el rail pasa al stack en desktop, el padding inferior del stack mantiene la vertical durante ese espacio vacío hasta el divisor.

### Solución B

Añadir `padding-bottom` al grid exterior.

Peor si el rail lo dibuja un hijo: deja aire pero el rail podría terminar antes del divisor y reaparecería el bug que #161 corrigió.

### QA

- mínimo visual razonable entre contenido de Samuel y doble raya de «Para escribir»;
- vertical continua hasta la raya, sin hueco;
- no duplicar el espacio en móvil;
- no tocar el `padding-top:28px` general salvo evidencia nueva.

---

## HOME-04 · Eventos: hover todavía usa el azul antiguo

**Estado:** CONFIRMADO  
**Prioridad:** media

`.yale-text-link` ya usa:

```css
:hover / :focus-visible → #0d2c57
```

pero `.home-event__link` conserva:

```css
:hover / :focus-visible → #004f73
```

Ese color pertenece al lenguaje anterior y deja una excepción innecesaria precisamente en una clase que #162 pretendía unificar.

### Corrección

```css
html.v1[data-lrb-home="true"] .home-event__link:hover,
html.v1[data-lrb-home="true"] .home-event__link:focus-visible {
  color:#0d2c57;
}
```

### QA

Computed style de hover/focus idéntico al de `.yale-text-link`.

---

## HOME-05 · Azul del logotipo filtrado a botones de contenido

**Estado:** CONFIRMADO  
**Prioridad:** media

El contrato del handoff reserva `#0a4d9f` para el azul que debe coincidir exactamente con «ESCRITOR» en el logotipo/header.

Sin embargo la regla actual agrupa:

```css
.install-web__button,
.form-submit,
.header-buy
```

y aplica a los tres `#0a4d9f`.

Esto crea dos azules de identidad en el cuerpo de la HOME.

### Corrección

- `.header-buy`: conservar `#0a4d9f`.
- `.install-web__button` y `.form-submit`: `border-color` y `color` → `#1d4f96`.

No es necesario duplicar todas las propiedades del botón; basta separar/overridear color y borde.

### QA

- `header-buy`: `rgb(10,77,159)`.
- instalar/newsletter: `rgb(29,79,150)`.
- hover/focus no reintroducen colores legacy desde otra hoja.

---

## HOME-06 · Fotografías, portadas y decoraciones: mantener semántica distinta

**Estado:** CONTRATO PREVENTIVO  
**Prioridad:** media

Durante la extensión del diseño no convertir todos los medios en el mismo marco.

- Foto de autor/header → doble anillo/rombos.
- Portadas de libros → corner brackets azul/dorado.
- Foto de evento → marco rectangular mínimo de dos tonos.

La consistencia debe venir de color, grosor y ritmo, no de copiar el mismo adorno en cualquier imagen.

---

## HOME-07 · Acción-link: contrato único

**Estado:** CASI CERRADO; vigilar regresiones  
**Prioridad:** media

Después de #162, el aspecto canónico vive en `.yale-text-link` y Eventos mantiene `.home-event__link` por separado.

Al añadir nuevas acciones:

- siempre `addTextLink(..., 'yale-text-link')` cuando el rol sea una acción textual del sistema;
- no crear otro modificador para recuperar Yellowtail;
- no añadir subrayado convencional;
- no volver al sans uppercase del diseño anterior;
- si una clase especial existe por estructura, su tipografía/colores deben mantenerse sincronizados con `.yale-text-link`.

---

## HOME-08 · Gray/legacy colour sweep antes de cerrar HOME

**Estado:** AUDITORÍA PENDIENTE EN ESTA PR  
**Prioridad:** media

Antes de declarar la HOME terminada, buscar en todas las reglas efectivas que afecten a `data-lrb-home="true"`:

```text
#0075b8
#004f73
#d5d4d0
rgba(0,0,0,.18)
var(--color-border)
var(--color-accent*)
```

No todo uso de `var(--color-border)` es necesariamente incorrecto. Cada coincidencia debe clasificarse:

- legacy visual que debe migrar;
- neutro intencional;
- componente compartido fuera del alcance de HOME;
- estado hover/focus que debe sincronizarse.

No hacer un reemplazo global de texto.

---

# 6. Orden de implementación de esta primera ronda

1. HOME-01 · seam de Samuel.
2. HOME-02 · marco fotografía de Eventos.
3. HOME-03 · aire antes del section-break «Para escribir», una vez HOME-01 esté estable.
4. HOME-04 · hover de Eventos.
5. HOME-05 · azul de botones de contenido.
6. HOME-08 · barrido residual y clasificación.
7. QA desktop/tablet/mobile + computed styles.
8. Solo entonces suites completas y CI.

# 7. Viewports mínimos de QA

- 1440 × 1000 — desktop editorial.
- 1280 × 800 — desktop más compacto.
- 1024 × 768 — breakpoint donde features ya se apilan.
- 768 × 1024 — tablet.
- 390 × 844 — móvil moderno.
- 360 × 800 — móvil estrecho.

Para HOME-01 comprobar además 1100/1101px alrededor del breakpoint.

# 8. Checks concretos

Además de screenshots:

```js
// Ejemplos conceptuales; adaptar al harness Playwright del repo.
getComputedStyle(document.querySelector('.home-event__link')).fontFamily
getComputedStyle(document.querySelector('.install-web__button')).color
getComputedStyle(document.querySelector('.form-submit')).borderColor
getComputedStyle(document.querySelector('.header-buy')).color
getComputedStyle(document.querySelector('.yale-feature__stack')).backgroundImage
getComputedStyle(document.querySelector('.yale-feature-book')).backgroundImage
```

Y medir bounding boxes para confirmar que el endpoint de las horizontales de Samuel coincide con la x del rail con tolerancia subpíxel razonable.

# 9. Definition of Done de HOME

La HOME no se considera migrada solo porque «se ve azul y dorada».

Debe cumplirse:

- [ ] ningún marco gris legacy visible salvo neutro intencional documentado;
- [ ] portadas con corner brackets correctos;
- [ ] foto de evento integrada en el sistema sin copiar semántica de portada;
- [ ] rails y horizontales conectados donde forman un único motivo;
- [ ] ningún section-break corta un rail que deba llegar hasta él;
- [ ] aire consistente antes/después de separadores;
- [ ] todos los links de acción usan el tratamiento tipográfico aprobado;
- [ ] hover/focus no recuperan colores antiguos;
- [ ] `#0a4d9f` queda limitado a la excepción de header/logotipo;
- [ ] títulos/eyebrows siguen el contrato aprobado;
- [ ] desktop/tablet/mobile revisados;
- [ ] `getComputedStyle`/medidas confirman los fixes, no solo screenshots;
- [ ] suites `tests/*.py` y `tests/*.mjs` verdes antes de marcar la PR lista para merge;
- [ ] CI completo verde.

# 10. Qué NO entra todavía

- Rediseñar `/libros/`, `/cuaderno/`, `/autor`, herramientas, prensa, etc.
- Reescribir contenido editorial de esas páginas.
- Cambiar SEO/structured data salvo bug provocado por esta PR.
- Convertir toda la web de golpe mediante reemplazos globales.

Cuando HOME cierre, la siguiente página/familia reutilizará este mismo contrato y añadirá únicamente sus diferencias reales. La meta es que el antiguo sistema desaparezca de forma controlada, no crear una segunda capa de excepciones.