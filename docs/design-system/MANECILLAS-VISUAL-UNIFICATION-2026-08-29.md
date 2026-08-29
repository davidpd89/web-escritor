# Diseño — `/las-manecillas-del-recuerdo/` · contrato de unificación visual · 2026-08-29

## 1. Trazabilidad

Esta revisión continúa la cadena de diseño:

1. PR #163 — `Diseño - HOME · unificación visual azul/dorado`.
2. PR #174 — `Diseño - Libros · unificación visual del hub de Obras`.
3. Esta PR — ficha principal de `Las manecillas del recuerdo`.

La rama nace del HEAD cerrado de #174: `18e7877f7d0522a9b4b3dd384c36ad2eca6f812c`. No debe mergearse antes que #163 y #174. Una vez fusionadas las bases, retargetear sucesivamente a `main` manteniendo limpio el diff propio.

## 2. Alcance

Página: `/las-manecillas-del-recuerdo/`.

Es la ficha de la obra principal y debe sentirse como una página editorial de libro, no como otra HOME ni como una landing SaaS. Reutiliza el contrato ya aprobado:

- azul canónico `#1d4f96`;
- dorado `#b8860b`;
- azul de controles del header `#0a4d9f`;
- negro para contenido principal;
- grises/neutros para metadatos y rótulos internos;
- Yellowtail para aperturas de sección y acciones;
- `corner-bracket-blue-gold.svg` para portadas;
- rails de `2.5px`;
- separadores azul/dorado conectados;
- fondos blancos o azul muy pálido solo cuando existe una razón semántica de énfasis.

## 3. Contenido que se preserva

Esta PR es de diseño/UX. No modificar sin un motivo independiente y documentado:

- title, description, canonical, OG/Twitter y JSON-LD;
- ISBN `979-8-90514-935-1`, 272 páginas, Monza Ediciones, PVP 16 €, fecha 3 de septiembre de 2026;
- orden y texto de sinopsis, tres puertas, dedicatoria, fragmentos, texto de cubierta, disponibilidad y newsletter;
- destinos de enlaces/CTA;
- ausencia actual de un destino comercial propio verificado;
- navegación contextual `Manecillas`;
- formulario y comportamiento funcional de newsletter/compartir;
- portada y art direction/responsive existentes.

## 4. Inventario y cierres de diseño

### MAN-01 · barra contextual aún usa el contrato interior anterior

Debe adoptar el mismo tratamiento ya cerrado en `/libros/`: blanco, azul canónico, estado activo azul pálido y acento dorado. En móvil debe reflowar y dejar de ser sticky si ocupa varias filas.

### MAN-02 · hero demasiado separado del nuevo sistema

Actualmente la composición tiene una buena jerarquía editorial, pero usa display serif, hairlines grises, una portada con marco convencional y CTAs del sistema anterior.

Cierre:

- mantener portada + copy + ledger como composición propia;
- portada con corner brackets, sin marco fotográfico;
- clasificación de apertura en Yellowtail/dorado;
- H1 azul con fino contorno dorado;
- autor y fecha permanecen neutros;
- lead conserva serif de lectura;
- CTAs Yellowtail azules;
- ledger técnico conserva rótulos grises y valores negros, con reglas azul/dorado;
- introducir una costura/rail azul coherente donde la geometría lo permita sin forzarla en la composición apilada.

### MAN-03 · `book-seam` es una única línea neutral

Convertirlo en transición del sistema: doble regla azul/dorado con diamante centrado. Evitar márgenes que vuelvan a abrir la unión física entre secciones.

### MAN-04 · aperturas de secciones

`La novela`, `Tres puertas de entrada`, `Dedicatoria`, `Muestra de lectura`, `Texto de cubierta`, `Disponibilidad` y `Novedades` son aperturas de bloque y pueden usar Yellowtail/dorado con highlight azul.

Los rótulos internos (`Editorial`, `Género`, `Páginas`, `ISBN`, `Formato`, `PVP`, numeración 01/02/03 y otros metadatos) permanecen grises/neutros.

### MAN-05 · títulos de sección y lectura

H2 principales deben entrar en la jerarquía azul/dorado sin perder la lectura larga. El cuerpo serif permanece negro. No convertir párrafos o texto de cubierta a sans-serif.

### MAN-06 · cita marginal

La cita debe seguir siendo secundaria. Darle rail azul y un fondo azul muy pálido o blanco controlado; no transformarla en una tarjeta pesada. En tablet/móvil debe ocupar ancho completo sin competir con el cuerpo.

### MAN-07 · Tres puertas de entrada

Conservar las tres columnas como bloque de ruptura en desktop. No convertirlas en tarjetas SaaS. Usar separación/rails azul-dorado y acciones/hover coherentes. En móvil pasan a una columna.

### MAN-08 · dedicatoria

Mantener su carácter de pausa editorial. Puede usar un rail azul y reglas azul/dorado; el bloque no debe competir con el hero ni recibir una caja pesada.

### MAN-09 · fragmentos / texto de cubierta

Son bloques de lectura: título azul/dorado, cuerpo negro serif, CTA Yellowtail. Las reglas grises antiguas se sustituyen por el sistema de separadores.

### MAN-10 · disponibilidad

Es información práctica y merece énfasis equivalente a `Lectores beta`/caja de Eventos: azul muy pálido, rail/borde azul y acento dorado. Mantener íntegramente el mensaje actual de que el enlace comercial se actualizará cuando exista un destino propio verificado.

### MAN-11 · newsletter

Mantener formulario y semántica. Adaptar fondo/bordes/botón/hover al sistema azul/dorado; no alterar validación ni endpoint.

### MAN-12 · shell

Header, Explorar, footer y Volver arriba deben seguir el contrato de #163/#174. Comprobar específicamente el launcher flotante del asistente: si invade lectura en determinados anchos, documentar/corregir solo en esta página manteniendo el acceso del header.

## 5. Responsive que debe validarse

- 1440×1000
- 1280×800
- 1200/1199 alrededor del cambio del hero/ledger
- 1024×768
- 900/899 alrededor del cambio principal de composición
- 768×1024 y 767×900
- 600×900
- 390×844
- 360×800

Especial atención a la cascada superpuesta de `1199`, `899`, `767` y `389` ya existente en `v1-book.css`.

## 6. QA visual/computed styles

Comprobar:

- portada visible y con bracket real en todos los breakpoints;
- H1 y aperturas con colores/tipografías correctos;
- rótulos internos neutros;
- CTAs sin recuperar botón negro/uppercase/subrayado antiguo;
- rail/separadores físicamente unidos;
- ningún bloque azul tapa o reduce legibilidad;
- hero y ledger sin solapamiento;
- tres puertas sin columnas huérfanas o texto estrecho;
- dedicatoria sin cortes de palabra;
- disponibilidad y newsletter sin overflow;
- header/context-nav/Explorar/footer/back-to-top con estados coherentes;
- launcher flotante sin tapar lectura;
- 200% zoom/text spacing y ausencia de overflow a 360/390px.

## 7. Fuera de alcance

- `/las-manecillas-del-recuerdo/fragmentos/` (tendrá su propia PR de diseño);
- `/libros/samuel-entre-mundos/`;
- contenido editorial, SEO o datos comerciales salvo regresión introducida por esta PR;
- cambios de navegación global fuera del scope necesario para mantener coherencia visual.

## 8. Definition of Done

- [ ] Diff propio limpio sobre #174.
- [ ] Diseño completo de hero, secciones, temas, dedicatoria, disponibilidad y newsletter adaptado.
- [ ] Contenido/SEO/structured data intactos.
- [ ] QA específico de Manecillas con capturas en breakpoints críticos.
- [ ] Lighthouse incluye y pasa la ruta (ya existe en la matriz general; verificar HEAD).
- [ ] Pa11y/Reflow/Cross-engine verdes.
- [ ] Revisión visual humana documentada antes del merge.
- [ ] Cualquier punto no certificable desde esta sesión queda explícitamente listado en la PR para Claude.