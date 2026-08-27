# 02 — Mobile: jerarquía y composición, no desktop encogido

**Autoridad conceptual:** contratos 16, 17 y 36 de Drive.  
**Problema operativo:** la implementación actual pasa QA de reflow, pero muchas escenas pierden su jerarquía al colapsar a una columna.

## 1. Principio rector

Mobile no es el breakpoint en el que se eliminan columnas.

Es otro medio editorial con:

- menos ancho;
- mayor profundidad de scroll;
- una mano como principal dispositivo de interacción;
- browser chrome dinámico;
- teclado virtual;
- cambio de orientación;
- distancia física menor a la pantalla;
- menor capacidad para leer relaciones laterales;
- mayor necesidad de saber dónde se está dentro de una página larga.

Por eso el objetivo no es conservar geometría, sino conservar **intención y jerarquía**.

## 2. Gramática de escena móvil

Toda escena importante debería poder describirse mediante cinco roles. No todos necesitan un elemento explícito.

### A. Llegada

Señala que comienza una región nueva.

Puede expresarse mediante:

- espacio;
- cambio de medida;
- label;
- posición;
- media;
- ruta/filete;
- cambio de densidad;
- alineación.

No necesita necesariamente un fondo distinto.

### B. Ancla

Es lo primero que el ojo debe reconocer dentro de esa escena.

Ejemplos:

- título de obra;
- portada;
- fecha de evento;
- nombre de herramienta;
- titular de artículo;
- retrato de autor.

Solo debe haber un ancla dominante por escena.

### C. Cuerpo

Explica, permite leer o permite actuar.

### D. Transición

Relaciona la escena con la siguiente. Puede ser continua o contrastada.

### E. Salida

Hace perceptible que la unidad terminó y ofrece una continuación cuando sea útil.

## 3. Doce variables de jerarquía antes de tocar color

Claude debe explorar primero:

1. escala relativa;
2. ancho/medida;
3. alineación;
4. gutter;
5. full-bleed selectivo;
6. posición de metadata;
7. espacio antes/después;
8. densidad;
9. media y crop;
10. relación texto-media;
11. línea/ruta;
12. orden DOM/narrativo.

Solo después debe evaluar superficies/color si resuelven un problema no resuelto por la composición.

## 4. Segmentación perceptual

Una página puede sentirse como «todo seguido» aunque tenga `padding` y bordes.

Claude debe evaluar al menos cinco principios de agrupación:

### Proximidad

Elementos que pertenecen juntos deben estar perceptualmente más cerca entre sí que del siguiente grupo.

### Similitud

Si todas las escenas usan exactamente el mismo heading, ancho y línea, el usuario las percibe como equivalentes aunque unas sean más importantes.

### Continuidad

Una ruta, alineación o borde puede hacer que dos elementos se entiendan como parte de un mismo recorrido.

### Figura/fondo

No implica usar un fondo de color en cada sección. Una imagen, un cambio de medida o un hueco amplio también pueden crear figura.

### Región común

Las cards son una forma de región común, pero no la única. En esta web deben ser excepción, no reflejo automático.

## 5. Ritmo vertical

No usar una única receta tipo:

```css
section { padding-block: 4rem; }
```

para toda la experiencia.

Definir roles semánticos de ritmo, por ejemplo:

- `continuity-tight` — la escena continúa;
- `section-standard` — nueva unidad normal;
- `chapter-break` — cambio de registro fuerte;
- `media-break` — imagen/material toma el relevo;
- `closing-space` — cierre antes de siguiente ruta.

Los nombres son conceptuales; no obligan a crear exactamente esos tokens.

### Regla

Dos escenas de importancia distinta no deberían producir la misma silueta vertical de forma sistemática.

## 6. Tipografía móvil

No se prescribe cambiar el stack actual.

### Problema a medir

Los H1/H2 fluidos pueden ser expresivos, pero un título ocupa demasiado poder visual cuando:

- llena casi toda la primera pantalla;
- aparece otro título de escala similar poco después;
- la media principal queda reducida;
- el deck parece metadata;
- el heading se parte en demasiadas líneas;
- el tamaño obliga a usar el mismo layout en todas las páginas.

### Evaluación

Medir:

- porcentaje de viewport ocupado por H1 + deck;
- número de líneas;
- `font-size/body-font-size`;
- line-height;
- espacio de salida;
- contraste de escala con H2;
- proporción entre heading y media.

### Regla

La misma fuente puede producir jerarquía muy distinta mediante medida, posición, masa y espacio. No resolver el problema añadiendo otra familia tipográfica.

## 7. Imágenes en móvil

### 7.1. Portadas

- mostrar completas salvo thumbnail claramente secundario;
- no recortar lomo/título;
- no hacerlas siempre full-width;
- probar escala relativa a título y CTA;
- considerar ligera salida de gutter cuando ayude a convertirlas en objeto;
- evitar mockup 3D genérico.

### 7.2. Retratos

- definir focal point por breakpoint;
- permitir full-bleed selectivo;
- no convertir automáticamente en avatar;
- preservar gesto/rostro/manos si son relevantes;
- evitar que un retrato enorme retrase toda la bio.

### 7.3. Evento/prensa

- ratio natural prioritario;
- usar pie/fecha/procedencia;
- no rellenar una cuadrícula solo porque haya varias imágenes.

### 7.4. Sin buen asset

Usar tipografía, espacio y estructura. No stock ni IA documental falsa.

## 8. Composición móvil por familia

## 8.1. Página de libro

Objetivo de los primeros segundos:

- identificar título;
- reconocer obra/autor;
- ver portada pronto;
- entender qué tipo de libro es;
- saber cuál es la acción principal.

Explorar al menos dos órdenes reales:

### Variante A

```text
título + descriptor
metadata mínima
portada
entrada
acción
ficha
sinopsis
fragmento/material
relacionados
```

### Variante B

```text
título
portada
entrada + acción
metadata/ficha
sinopsis
...
```

No elegir por gusto. Probar comprensión, scroll inicial y peso de portada.

## 8.2. Autor

No convertir a:

```text
H1 enorme
avatar
bio
cards
```

Explorar:

```text
identidad/título
retrato editorial con crop propio
bio breve
bio larga a medida distinta
hitos/obra como ledger
material real
contacto/prensa
```

La cronología puede usar fecha encima del hito y un filete lateral suave. No timeline de producto.

## 8.3. Cuaderno hub

El índice debe conservar escalas variables.

Mobile no necesita que todos los artículos tengan el mismo bloque.

Posibles roles:

- pieza principal;
- segundo foco;
- lista de archivo;
- grupo temático;
- ruta hacia obra relacionada.

Una lista vertical puede ser muy jerárquica si título, fecha, extracto y espacio cambian según importancia.

## 8.4. Artículo

Secuencia sugerida como modelo de evaluación, no template obligatorio:

```text
breadcrumb discreto
cabecera editorial
metadata
TOC/orientación compacta si aporta
prosa
cambio de capítulo perceptible
figura/nota/cita cuando corresponda
prosa
fuentes
FAQ si existe por contenido
cierre + relacionado principal
```

### TOC móvil

No debe parecer otra gran sección antes de empezar a leer.

Evaluar:

- `<details>` accesible;
- resumen compacto;
- listado visible si pocos elementos;
- ancla contextual.

No ocultar navegación esencial detrás de interacción inesperada.

## 8.5. Herramienta abierta

Tres regiones muy claras:

1. **hacer**;
2. **ver resultado**;
3. **entender / continuar**.

El resultado debe adquirir una escena propia cuando aparece.

No debe mezclarse visualmente con el texto metodológico por usar el mismo borde/heading.

## 8.6. Herramientas hub

El contrato de Drive pide «mesa de trabajo», no dashboard.

Explorar:

- filas de distinta densidad;
- agrupación por tarea;
- una herramienta destacada si los datos lo justifican;
- títulos como navegación;
- metadata funcional mínima.

Evitar grid uniforme de cards de producto.

## 8.7. Prensa / eventos

La fecha es una herramienta compositiva real.

Mobile:

```text
fecha/estado
nombre
lugar
material
texto breve
acción/fuente
```

La línea temporal puede vivir en margen si ayuda, pero cada evento no necesita nodo circular.

## 8.8. Directorios / editoriales / convocatorias

Diseño orientado a escaneo:

- nombre;
- estado/verificación;
- categorías útiles;
- acción;
- notas decisivas.

No intentar convertir cada ficha en mini landing.

La jerarquía puede salir de table/list/ledger responsive, no de cards.

## 9. Browser chrome y viewport real

Seguir doc 36.

### Probar

- Safari iOS, barras expandidas/retraídas;
- Chrome Android;
- `svh`/`dvh` donde proceda;
- safe areas;
- 390×600;
- 667×375 landscape;
- teclado virtual;
- rotación caliente;
- pinch zoom;
- 200 % text/browser zoom;
- Back y scroll restoration.

### No hacer

- `user-scalable=no`;
- `height:100vh` universal;
- `width:100vw` para layout normal;
- `overflow-x:hidden` para esconder una causa no resuelta;
- recalcular toda la UI con VisualViewport;
- barra inferior fixed global;
- portrait-only.

## 10. Safe areas

Si `viewport-fit=cover` está activo, ownership explícito de:

```css
env(safe-area-inset-top)
env(safe-area-inset-right)
env(safe-area-inset-bottom)
env(safe-area-inset-left)
```

Especialmente:

- header;
- dialog;
- controles de cierre;
- footer;
- media full-bleed con texto/control;
- cualquier acción sticky futura.

No sumar safe area en padre e hijo sin razón.

## 11. Orientación

Landscape móvil es un layout de **poca altura**, no un desktop pequeño.

Puede requerir:

- menor padding vertical;
- media secundaria pospuesta;
- alineación al inicio en vez de centrado;
- dialog scrollable;
- navegación compacta;
- hero con scroll normal.

No esconder contenido esencial.

## 12. Gutter y full-bleed

El gutter actual es una base útil.

La jerarquía puede mejorar cuando una escena seleccionada:

- rompe el gutter con media;
- mantiene texto dentro del gutter;
- vuelve al gutter en la escena siguiente.

Ese cambio produce un corte fuerte sin añadir color.

### Restricción

No hacer full-bleed de todo. Si todo llega al borde, deja de ser señal.

## 13. Test de «fin de escena»

Para cada transición importante, hacer esta pregunta:

> Si elimino el texto de los headings y miro la captura, ¿puedo saber que una unidad terminó y otra empieza?

Si la respuesta es no, revisar:

- ritmo;
- alineación;
- medida;
- media;
- densidad;
- gutter;
- espacio;
- relación de escala.

No saltar automáticamente a `background-color`.

## 14. Matriz mínima de pruebas

| Estado | 320 | 390 | 768 | landscape bajo | dispositivo real |
|---|---:|---:|---:|---:|---:|
| apertura | ✓ | ✓ | ✓ | ✓ | ✓ |
| navegación | ✓ | ✓ | ✓ | ✓ | ✓ |
| long scroll | ✓ | ✓ | ✓ | ✓ | ✓ |
| media/crop | ✓ | ✓ | ✓ | ✓ | ✓ |
| 200% zoom | ✓ | ✓ | ✓ | ✓ | según dispositivo |
| text spacing | ✓ | ✓ | ✓ | ✓ | — |
| reduced motion | ✓ | ✓ | ✓ | ✓ | ✓ |
| teclado/form | — | ✓ | ✓ | ✓ | ✓ |
| rotación | — | ✓ | ✓ | ✓ | ✓ |

## 15. Evidencia que Claude debe producir

Para cada familia que cambie:

1. screenshot antes 390;
2. screenshot después 390;
3. long-scroll before/after;
4. 320;
5. 768;
6. 1440;
7. landscape;
8. texto al 200 %;
9. reduced motion;
10. breve nota: qué jerarquía cambió y por qué;
11. visual-regression diff;
12. prueba en motor/dispositivo real cuando llegue a merge gate.

## 16. Criterio final

Una página móvil excelente no tiene que parecer más «diseñada».

Debe hacer que el usuario perciba con menor esfuerzo:

- dónde está;
- qué importa;
- qué pertenece junto;
- cuándo cambia de registro;
- dónde actuar;
- cómo continuar.

Y debe hacerlo conservando la identidad editorial, no importando patrones genéricos de aplicaciones.