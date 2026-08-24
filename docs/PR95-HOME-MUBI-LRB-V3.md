# PR #95 — Home V3: banners MUBI + arquitectura editorial LRB

Fecha de decisión: 24/08/2026.

Este documento es **normativo para la PR #95**. No es una colección de ideas. Describe la composición que debe quedar visible al integrar esta rama y los únicos remates que dependen de assets locales que esta sesión no puede leer.

## 1. Dirección cerrada

La Home mezcla dos referencias de forma controlada:

- **MUBI Notebook** aporta el ritmo visual de grandes imágenes horizontales que separan territorios y funcionan como apertura de campaña.
- **London Review of Books** aporta la lógica editorial de lectura: papel, reglas, jerarquías de título/metadata/resumen, agrupaciones y eventos.
- La identidad, colores finales, contenidos, enlaces, tipografías y assets son propios de David Porto Díaz.

La página no debe convertirse en una sucesión de cards SaaS ni en una copia literal de ninguna referencia.

## 2. Patrón repetible obligatorio

Cada territorio principal sigue este ritmo:

1. banner fotográfico de ancho completo;
2. cluster editorial inmediatamente debajo;
3. cambio tonal/interludio cuando haga falta;
4. siguiente banner.

El banner no es un hero de pantalla completa. Es una franja panorámica relativamente baja, con presencia visual y poco texto.

### Desktop

- ancho: 100 % del viewport;
- altura CSS: `clamp(230px, 29vw, 410px)`;
- sujeto principal de la fotografía dentro de la zona central;
- texto en el tercio izquierdo/inferior con degradado solo para legibilidad;
- la imagen se recorta con `object-fit: cover`.

### Mobile

- altura aproximada: 310 px;
- se usa la misma imagen siempre que el foco central sobreviva al recorte;
- `object-position: center center`;
- degradado pasa a vertical para que título y subtítulo se lean sin tapar el centro visual.

### Recomendación de generación

Para los nuevos banners, generar/exportar idealmente a **2400 × 900 px** (o proporción panorámica equivalente). Mantener personajes/objetos esenciales dentro del **40 % central** del lienzo para que el mismo fichero funcione en 1440, 1024, 768 y 390 px.

No incrustar texto dentro de la imagen. El título/subtítulo se renderizan en HTML para accesibilidad, SEO, traducción y responsive.

## 3. Assets definitivos

Carpeta local de trabajo que Claude sí puede leer:

`C:\GIT\web-escritor\WEB DAVID PORTO nuevas ideas\DISEÑO Y DEMÁS\Imagenes generadas para implementar`

Copiar los banners definitivos al repo con estos nombres exactos:

- `assets/banners/manecillas-home-banner.webp`
- `assets/banners/samuel-home-banner.webp`
- `assets/banners/memoria-tierras-norte-home-banner.webp`
- `assets/banners/herramientas-home-banner.webp`

Se admiten `.jpg` con el mismo nombre base si todavía no existe WebP; el código prueba ambas extensiones.

Fallback temporal ya codificado:

- Manecillas → `assets/og-manecillas.webp`.
- Samuel → `assets/samuel_entre_mundos_3d.webp`.
- Memoria/Herramientas → fondo cromático diseñado, sin icono roto ni caja vacía.

Claude debe sustituir los fallbacks por las imágenes locales definitivas antes de pasar la PR a ready si David ya se las ha proporcionado.

## 4. Orden final de Home

Tras masthead + navegación:

1. **Banner Las manecillas del recuerdo**.
2. Cluster editorial Manecillas.
3. Interludio oscuro «El cuaderno».
4. **Banner Samuel entre mundos**.
5. Cluster editorial Samuel.
6. **Banner La memoria de las tierras del norte**.
7. Cluster editorial del relato / otras obras.
8. **Banner Herramientas para escritores**.
9. Cluster de herramientas.
10. Bloque **Eventos y encuentros**.
11. Bloque **Instala la web**.
12. FAQ existente.
13. Newsletter existente.
14. Footer existente.
15. Botón flotante **Volver arriba** cuando el usuario ya ha avanzado por la página.

La intro cinematográfica existente no se elimina en esta PR.

## 5. Cluster editorial: geometría cerrada

Cada cluster usa un patrón **1 + 2**:

- pieza principal a la izquierda, ocupando dos filas;
- dos piezas secundarias apiladas a la derecha;
- en móvil pasan a una columna vertical;
- no hay bordes redondeados;
- no hay sombras de tarjeta;
- hay reglas superiores, diferencias de papel y aire entre módulos.

Esto corresponde exactamente a la intención de «un cuadradito con el libro y mini texto; a la derecha dos artículos/piezas relacionadas» sin convertir la Home en una retícula genérica de seis tarjetas iguales.

### Manecillas

Principal:
- Las manecillas del recuerdo;
- portada actual como imagen interna;
- Monza Ediciones;
- 3 septiembre 2026.

Secundarias:
- «Entrar en la historia» → fragmentos;
- «David Porto Díaz» → autor/prensa, en bloque azul.

### Samuel

Principal:
- Samuel entre mundos;
- ficha y universo del libro.

Secundarias:
- guía «¿Qué es el portal fantasy?»;
- crónica de la Feria del Libro de Madrid, en tono salvia.

### La memoria de las tierras del norte

Principal:
- relato en antología de Diversidad Literaria.

Secundarias:
- acceso a todas las obras;
- autor/trayectoria, en rosa empolvado muy suave.

### Herramientas

Principal:
- hub de herramientas gratuitas.

Secundarias:
- analizador de manuscrito;
- repeticiones/diálogo, con bloque azul.

## 6. Paleta cerrada para la Home V3

No improvisar un color diferente por sección. Usar esta familia ya implementada:

- papel base: `#f6f2e9`;
- papel claro: `#fbf9f4`;
- piedra: `#e6e1d7`;
- piedra profunda: `#d9d3c8`;
- tinta: `#1b1917`;
- metadata gris: `#6f6a64`;
- azul: `#d4e8ee`;
- tinta azul: `#254f60`;
- salvia: `#dfe6dc`;
- tinta salvia: `#3d5747`;
- rosa empolvado: `#eadedb`.

Los banners pueden tener fotografías con cromática propia, pero el UI alrededor usa esta paleta. Máximo una celda de color claramente protagonista dentro de cada cluster.

## 7. Profundidad / materialidad

Mantener lo implementado en `v1-lrb-material-v2.css` y continuar esta lógica:

- barra superior casi blanca;
- hairline y sombra mínima;
- masthead en papel cálido;
- navegación un tono más profunda;
- campo editorial de piedra/papel;
- módulos de papel con leves diferencias de tono;
- bloques azul/salvia/blush como interrupciones, no como sistema multicolor.

Objetivo: sensación de publicación impresa con capas. Evitar blanco puro continuo, divisores flotantes o cuadrícula pegada al texto.

## 8. Eventos

El bloque Home reutiliza únicamente eventos ya documentados en `eventos.html`:

- Feria del Libro de Madrid — 10/06/2026;
- Feria del Libro de Aranjuez — 23/05/2026;
- Presentación en La Vecinal — 31/01/2026;
- Presentación oficial de Samuel entre mundos en Bar Aleatorio — 15/01/2026.

Debajo aparece CTA editorial:

**¿Quieres organizar una presentación, firma o club de lectura?**

Destino: email de contacto con asunto predefinido. El enlace a `/eventos.html` sigue visible para el archivo completo.

## 9. Instalación de la web

El proyecto ya contiene `manifest.json` con `display: standalone`, iconos y shortcuts. La Home V3 incluye un bloque «Lleva la web contigo».

Comportamiento:

- si el navegador emite `beforeinstallprompt`, el botón abre el diálogo nativo;
- si la web ya está instalada, el botón queda desactivado y lo indica;
- iOS muestra instrucción «Compartir → Añadir a pantalla de inicio»;
- otros navegadores sin prompt muestran la instrucción equivalente;
- no crear un service worker de caché agresivo solo para forzar instalación en esta PR. Una estrategia offline requiere revisión separada porque puede servir HTML/assets obsoletos durante el lanzamiento.

## 10. Volver arriba

Botón circular de 44 × 44 px:

- aparece aproximadamente después de 720 px de scroll;
- esquina inferior derecha respetando safe areas;
- vuelve a `top: 0`;
- scroll suave salvo `prefers-reduced-motion`;
- oculto en impresión.

## 11. Responsive obligatorio

QA real, no solo inspección de CSS:

- 1440 × 900;
- 1024 × 768;
- 768 × 1024;
- 390 × 844;
- 320 px de ancho;
- zoom 200 %.

Comprobar en todos:

- sujeto central de banners no queda amputado;
- títulos no tapan la zona focal;
- no overflow horizontal;
- cluster 1+2 → una columna correctamente;
- el orden semántico coincide con el visual;
- botones y enlaces ≥44 px cuando actúan como controles;
- eventos 4 → 2 → 1 columnas;
- install block 2 → 1 columnas;
- back-to-top no tapa CTA, consentimiento ni botones importantes;
- contraste AA;
- `prefers-reduced-motion`.

## 12. Implementación ya incluida en esta PR

- `assets/v1-home-editorial-v3.css`
- `assets/v1-home-editorial-v3.js`
- carga desde `assets/v1-shell.css` / `assets/v1-shell.js`

La mejora es progresiva: si el JS V3 falla, la Home antigua sigue en el HTML y continúa siendo navegable. Solo después de construir correctamente el flujo nuevo, JS retira de la vista el `river-grid` y `promo-band` antiguos para evitar duplicados.

## 13. Pendiente antes de merge

Lo pendiente no es «diseñar» estos bloques: ya están definidos y codificados.

Claude debe:

1. incorporar el logo local exacto del masthead;
2. incorporar los cuatro banners definitivos cuando David se los entregue;
3. ajustar únicamente `object-position` si la fotografía concreta lo exige, sin alterar la arquitectura;
4. consolidar la estructura de header en `scripts/build-site-shell.py` como ya exige `PR95-CLAUDE-FINALIZATION.md`;
5. ejecutar QA real y tests del repo;
6. corregir cualquier regresión encontrada;
7. solo entonces marcar la PR ready/mergear cuando David lo autorice.
