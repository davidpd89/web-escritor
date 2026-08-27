# 08 — Dirección de arte de media, fotografía y objetos reales

## 1. Principio

La identidad visual del proyecto debe ganar profundidad mediante **material real**, no mediante decoración sintética.

Fuentes válidas:

- portada física;
- libro fotografiado;
- retrato real;
- manuscrito;
- galeradas/correcciones autorizadas;
- firma;
- acreditación;
- evento;
- escenario;
- librería;
- recorte de prensa autorizado;
- objeto relacionado con el proceso real;
- documentos públicos con procedencia.

La web no necesita fabricar «atmósfera literaria» con tinteros, papel envejecido, grano, escritorios IA o mockups imposibles.

## 2. Problema actual

El sitio ya contiene media real y varios assets de buena calidad, pero no toda imagen tiene un **rol editorial explícito**.

Una imagen sin rol acaba tratándose como:

```text
imagen → width:100% → border → caption
```

Eso es correcto funcionalmente pero desaprovecha dirección de arte.

## 3. Roles de media

Cada asset usado en una composición debe declarar uno.

### `hero-object`

Portada/libro/retrato que define la escena.

### `documentary-evidence`

Evento, acreditación, recorte, manuscrito, fotografía que demuestra una historia real.

### `context`

Ayuda a comprender sin dominar.

### `transition`

Una imagen puede crear un cambio de capítulo o densidad.

### `thumbnail`

Navegación secundaria; crop permitido si no destruye información.

### `decorative`

Debe justificarse especialmente. Si no aporta, probablemente se elimina.

## 4. Inventario de assets

Crear una auditoría machine-readable futura, por ejemplo:

```json
{
  "path": "assets/...webp",
  "subject": "David Porto Díaz",
  "roleCandidates": ["hero-object", "documentary-evidence"],
  "source": "sesión propia",
  "rights": "owned-or-authorized",
  "naturalWidth": 0,
  "naturalHeight": 0,
  "focalPoints": {
    "portrait": {"x": 0.5, "y": 0.3}
  },
  "cropAllowed": true,
  "notes": "..."
}
```

No inventar rights/source si no están documentados.

## 5. Crop como decisión editorial

`object-fit: cover` no es una estrategia de arte.

Para cada imagen importante definir:

- sujeto;
- información que nunca puede recortarse;
- focal point;
- ratio desktop;
- ratio mobile;
- si necesita asset alternativo;
- posición del texto alrededor;
- si puede llegar a borde.

### Retrato

El focal point no tiene que ser siempre `50% 50%`.

Probar:

- rostro;
- gesto;
- manos;
- dirección de mirada;
- espacio negativo para composición.

### Portadas

No crop destructivo. La cubierta es una obra gráfica y debe reconocerse completa salvo miniatura secundaria.

## 6. Responsive images

Revisar que los assets prioritarios utilicen cuando corresponda:

- dimensiones intrínsecas;
- `srcset`;
- `sizes`;
- `<picture>` cuando formato/crop cambia de verdad;
- AVIF/WebP/JPEG según ladder actual;
- `fetchpriority` solo para candidato LCP claro;
- lazy loading para imágenes fuera de primera pantalla.

El repositorio ya tiene tooling de formatos; la dirección de arte debe integrarse con él, no duplicarlo.

## 7. Full-bleed selectivo

Una fotografía real puede romper el gutter y producir una transición fuerte en mobile.

Reglas:

- no en cada sección;
- texto esencial permanece en safe area/gutter;
- crop explícito;
- no genera horizontal overflow;
- el retorno al gutter forma parte de la composición;
- imagen conserva resolución suficiente.

## 8. Densidad de imágenes

No equilibrar una página con imágenes por simetría.

Una página puede tener:

- una gran imagen;
- dos documentos pequeños;
- largas zonas tipográficas;

si esa es la historia real.

Evitar:

- una imagen por sección;
- alternancia mecánica izquierda/derecha;
- tres fotos = galería automática;
- thumbnails uniformes para todo el archivo.

## 9. Fotografías de libro

Si necesitamos nuevo material, producir una shot list real.

### Manecillas

Posibles tomas, solo cuando el libro físico/material exista:

- portada frontal limpia;
- libro ligeramente abierto;
- lomo;
- detalle de páginas/edición;
- objeto en entorno real sobrio;
- mano sosteniendo libro si aporta escala/humanidad;
- fotografía en presentación/librería cuando exista.

### Samuel

Mismo principio, respetando su identidad propia.

No hacer el mismo mockup con fondo diferente para ambos libros.

## 10. Retrato del autor

Necesitamos tratar el retrato como una serie, no un único JPG reutilizado en todos los contextos.

Inventario deseable:

- retrato editorial vertical;
- medio cuerpo;
- horizontal con espacio negativo;
- evento/documental;
- press portrait limpio;
- avatar/crop pequeño solo para contextos funcionales.

No crear una sesión falsa con IA.

## 11. Producción física/craft

Si buscamos una huella visual específica:

- imprimir;
- escanear;
- fotografiar;
- escribir/anotar físicamente;
- usar recortes reales;
- crear sombras con objeto real;

antes de simularlo digitalmente.

La imperfección debe tener procedencia, no ser un filtro genérico.

## 12. Canva MCP

Canva puede ayudar en **producción de media**, no gobernar el layout web.

Servidor oficial:

```text
https://mcp.canva.com/mcp
```

Autenticación OAuth.

### Usos adecuados

- moodboard anotado;
- press one-sheet;
- assets sociales;
- variantes de banner/campaign;
- composiciones para estudiar crops;
- exportaciones de materiales promocionales;
- organización de Brand Kit si el plan lo permite.

### No usar para

- responsive web grid;
- typography CSS;
- breakpoints;
- DOM;
- components web;
- source of truth del diseño.

## 13. Figma para media web

Figma gobierna:

- crop aprobado por frame;
- relación media/texto;
- full-bleed;
- escala;
- frame variants;
- redlines.

Canva puede producir/organizar el asset; Figma y el navegador deciden su papel web.

## 14. Image QA

Para cada imagen nueva o modificada:

```text
[ ] source/provenance conocida
[ ] rights conocidas
[ ] role explícito
[ ] alt/caption decidido
[ ] dimensiones intrínsecas
[ ] responsive variants adecuadas
[ ] crop 390
[ ] crop 768
[ ] crop 1440
[ ] landscape cuando importa
[ ] no información cortada
[ ] no CLS material
[ ] bytes razonables
[ ] no LCP regresado
[ ] no borde/marco universal añadido por inercia
```

## 15. Alt vs caption

### Alt

Sirve para alternativa de la imagen en contexto.

### Caption

Puede aportar:

- fecha;
- lugar;
- autor de fotografía;
- procedencia;
- contexto;
- fuente.

No duplicar mecánicamente el alt en caption.

## 16. Imágenes de artículos

No poner hero editorial genérico en cada artículo.

Categorías:

- artículo que tiene evidencia visual real → usarla;
- artículo conceptual sin asset necesario → tipografía domina;
- guía que necesita diagramas → gráfico/diagrama real y accesible;
- crónica/evento → documental.

La ausencia de imagen puede ser una decisión de calidad.

## 17. Diagramas y gráficos

Cuando el contenido lo requiera:

- SVG/HTML cuando sea semántico/simple;
- texto alternativo;
- tabla de datos si el gráfico representa datos;
- no usar ilustración generativa solo para rellenar.

## 18. Media y rendimiento

Dirección de arte debe contemplar:

- candidato LCP;
- bytes iniciales;
- decode;
- responsive source selection;
- preload;
- layout shifts;
- lazy load.

Claude debe capturar trace cuando cambia una imagen de primera pantalla.

No aceptar:

> «Se ve mucho mejor»

si el cambio pasa de una portada de 90 KB a una foto de 2.5 MB sin razón.

## 19. Manifiesto visual

Proponer un fichero interno como:

```text
data/media-art-direction.json
```

para assets importantes, con:

- source;
- rights status;
- roles;
- focal points;
- allowed crops;
- alt seed/context;
- public/private;
- owner;
- verification date.

No hacerlo público por defecto: puede contener notas de producción.

## 20. Anti-slop de media

Rechazar:

- fotógrafo IA inexistente;
- «papel vintage» sintético;
- sombras imposibles;
- portada flotando en 3D cromado;
- profundidad de campo artificial sin propósito;
- mockup de MacBook/iPhone para mostrar la web;
- stock de persona escribiendo;
- bibliotecas falsas;
- plumas/tinteros;
- partículas/luz mágica genérica;
- imágenes cuya única justificación es «hacerlo más visual».

## 21. Criterio final

La media debe hacer que la web parezca más vinculada a **David, sus libros y su actividad real**, no más vinculada a una tendencia de diseño.

Cuando una fotografía real no existe, el sistema debe ser suficientemente fuerte para sostenerse con tipografía, espacio y estructura.