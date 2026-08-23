# W — Diseño final · PENDIENTE DISEÑO GPT líneas 1–100

Fecha de auditoría: 2026-08-23  
Fuente: `PENDIENTE DISEÑO GPT.txt` (Drive `1IFyKTP5S74P_Not8PEfX1_MKf9ztka7E`)  
Bloque auditado: **líneas 1–100 exactas**  
Base observada al abrir el bloque: `implementacion-web-2026@4694799edc6d9c9e729b896cadda1eef9726d083`

> Esta PR fija el owner y el contrato de implementación de la capa visual final de Home/cartografía. No autoriza merge a `main`, deploy ni publicación. La implementación deberá rebasarse sobre la rama de integración viva y sobre los owners funcionales ya abiertos.

## 1. Qué NO se duplica

Este bloque mezcla deuda visual real con elementos que ya tienen owner. Se separan explícitamente:

- navegación, cinco territorios, findability y rendering de `exploreShortcuts` / `exploreUtilities` → **#68**;
- QA mobile/resiliencia/microtipografía global → **#78**;
- geometría responsive de imágenes → **#61 H.3**;
- escalera AVIF/WebP y correspondencia de formatos → **#67 L.1**;
- CSP del shell → **#62**;
- contenido/SEO/paridad existente de Home → preservar; no se elimina desde esta PR para “hacerla más corta”.

Se ha dejado comentario específico en #68 para que `exploreShortcuts` y `site-map` no se conviertan en una segunda navegación hardcodeada durante el rediseño.

## 2. Hallazgo principal

La arquitectura V1-B ya existe, pero la Home sigue visualmente en un estado intermedio:

- el hero usa un territorio oscuro correcto como base, pero el fondo visible sigue siendo esencialmente `--territory-bg` + un gradiente sutil;
- la cartografía ya es HTML semántico + SVG y tiene estados hover/focus, pero se percibe principalmente como texto + markers cuadrados;
- las rutas no tienen entrada/dibujo progresivo;
- la timeline móvil es estructuralmente correcta pero estática;
- no existe todavía una continuidad visual entre Home y sus destinos mediante View Transitions;
- las familias tienen CSS propio, pero la Home todavía no expresa con suficiente claridad una materialidad diferente para Obras/Autor/Cuaderno/Herramientas/Prensa.

El problema no es de arquitectura. Es la distancia entre una base funcional correcta y una experiencia editorial visual con nivel de candidatura a premios.

## 3. W.1 — Hero final: fondo diseñado y materialidad real

### Objetivo

El hero debe dejar de sentirse como “fondo oscuro + retrato + portada flotante” sin introducir una escenografía artificial o una landing de efectos.

### Contrato

Mantener:

- H1, copy, CTA y jerarquía actuales salvo cambio editorial separado;
- retrato real de David;
- portada oficial de `Las manecillas del recuerdo`;
- contraste oscuro aprobado de V1-B;
- HTML semántico y orden DOM existentes cuando no haya motivo funcional para cambiarlos.

Añadir una composición de fondo por capas, no una sola imagen de relleno:

1. superficie base tipográfica/editorial;
2. profundidad obtenida con gradientes controlados, máscaras, líneas, tramado, textura o tratamiento gráfico propio;
3. relación visual entre retrato y portada, evitando que parezcan dos PNG “pegados” encima;
4. una señal gráfica discreta de ruta/tiempo/escritura que conecte con la cartografía posterior;
5. composición específica móvil, no simple reducción proporcional del desktop.

### Regla de assets — corregida por decisión del propietario

No existe una prohibición general de usar generación o adaptación asistida.

La regla real es:

- **sí** a fotografía/material real, portada real y assets autorizados;
- **sí** a extraer una especificación visual/JSON de una referencia real y reconstruir/adaptar composición, luz, textura, geometría o fondo para nuestro sistema;
- **sí** a fondos, texturas, ilustración abstracta, tratamientos y piezas gráficas generadas/retocadas cuando resuelvan un hueco de diseño concreto;
- **sí** a combinar material real con CSS/SVG/máscaras/composición gráfica;
- **no** a caras/personas documentales falsas, falsas fotos de eventos, falsas páginas de manuscrito o cualquier pieza que pueda interpretarse como evidencia real;
- **no** a la estética reconocible de “imagen IA genérica”: fantasía decorativa gratuita, glow, pseudo-lujo, steampunk, pergamino falso, escritorio de escritor, plumas, reloj cliché u objetos que solo existan para adornar;
- **no** a descargar/adaptar material de terceros sin revisar derechos y procedencia.

Si durante los siguientes bloques aparece un manifiesto de media/proveniencia ya canónico, esta PR lo reutilizará. **No crear ahora un segundo JSON de autoridad en paralelo.**

## 4. W.2 — Cartografía final: más contexto visual, sin perder semántica

### Estado actual

`index.html` ya contiene el mapa navegable y `assets/v1-home.css` posiciona nodes/rutas. `assets/v1-shell.js` mantiene estados de hover/focus sin sustituir el enlace real.

### Objetivo

Elevar la cartografía desde diagrama funcional a pieza editorial reconocible.

### Contrato visual

Cada territorio/nodo puede activar una combinación controlada de:

- media real aprobada;
- recorte editorial;
- fragmento tipográfico;
- color/materialidad derivada del territorio;
- microcopy contextual;
- tratamiento de línea/ruta.

No convertir cada nodo en una card ni abrir mini-modales. El mapa debe seguir leyéndose como una composición única.

### Interacción

- hover y focus producen el mismo nivel de información esencial;
- ningún dato necesario existe solo en hover;
- touch navega con un toque: no introducir “primer toque = preview, segundo toque = entrar”;
- los cambios visuales no modifican el orden de tabulación;
- SVG sigue siendo decorativo respecto al `<nav>` HTML, no la autoridad interactiva.

## 5. W.3 — Motion narrativo selectivo

### Hero reveal

Una única entrada breve al cargar/mostrar Home:

- copy;
- retrato/portada;
- señal gráfica de ruta;
- sin secuencia teatral larga ni bloqueo de interacción.

El contenido debe estar disponible inmediatamente en DOM. Motion solo modifica presentación.

### Rutas desktop

Al entrar la cartografía en viewport:

- revelar una vez las rutas con `stroke-dasharray`/`stroke-dashoffset` o mecanismo equivalente;
- duración contenida y ligada al propósito, no al espectáculo;
- una vez reveladas, quedan estables;
- hover/focus posterior conserva la lógica actual de énfasis.

Preferencia de implementación: `IntersectionObserver` + clases de estado y CSS. Evitar una librería de animación global.

### Timeline móvil

La línea vertical puede expresar progreso mientras el usuario recorre el mapa, pero debe ser enhancement:

- base estática totalmente usable;
- progresión visual adicional en navegadores compatibles;
- no scroll-jacking;
- no alterar la velocidad ni posición del scroll;
- no depender de JS para descubrir enlaces.

### Microinteracción

- desplazamiento vertical máximo orientativo: 2–4 px;
- marker/ruta/subrayado pueden reforzarse de forma coordinada;
- nada de magnetic hover;
- nada de `transition: all`;
- no usar movimiento ambiental continuo si no aporta lectura o orientación.

## 6. W.4 — View Transitions como progressive enhancement

El bloque 1–100 conserva la continuidad entre páginas como parte de la experiencia final.

### Primeras parejas candidatas

- Home → `Las manecillas del recuerdo` mediante la portada;
- Home → Autor mediante el retrato;
- otras parejas solo después de demostrar que comparten un elemento visual real.

### Reglas

- navegación normal con `<a href>` sigue siendo la base;
- si el navegador no soporta View Transitions, no cambia nada funcional;
- no interceptar navegación solo para crear un efecto;
- `prefers-reduced-motion: reduce` elimina/reduce la transición;
- la transición no puede causar flash, salto de scroll, focus perdido ni doble representación del elemento;
- no aplicar nombres globales idénticos a varios elementos simultáneos;
- cualquier transición debe respetar el estado final de #68/#62 y el DOM real de las páginas destino.

Durante implementación se elegirá la forma MPA actual más simple y soportada por los navegadores objetivo; no reconstruir una API experimental antigua solo porque aparezca en documentación histórica.

## 7. W.5 — Materialidad por territorio sin crear cinco marcas distintas

Necesitamos personalidad reconocible, no cinco micrositios incompatibles.

Base común:

- Instrument Serif / Manrope / Newsreader;
- Paper/Ink;
- mismos principios de grid, foco, links y accesibilidad;
- mismos componentes semánticos.

Diferenciación permitida:

- Obras / Manecillas: portada, cobre/tono derivado real, ritmo más narrativo;
- Samuel: identidad propia subordinada al sistema común;
- Autor: retrato, espacio negativo, fotografía/documentación;
- Cuaderno: lectura editorial y estructura de publicación;
- Herramientas: precisión, estado, controles y utilidad;
- Prensa/Eventos: archivo/documento/fecha/material verificable.

La Home debe insinuar esas diferencias en la cartografía sin cargar todas las hojas de estilo de las páginas destino ni duplicar componentes.

## 8. Home larga: restricción de preservación

Las líneas 51–55 señalan que Home contiene más piezas que la arquitectura mínima original: ensayo de Samuel, río ampliado y FAQ.

Esta PR **no puede resolverlo borrando contenido**.

Regla:

- contenido único/SEO existente se preserva hasta que tenga destino canónico aprobado;
- diseño puede cambiar jerarquía, ritmo, agrupación y presencia visual;
- no ocultar texto relevante con técnicas que lo conviertan en contenido SEO invisible;
- una futura migración editorial puede mover piezas, pero debe tener owner y paridad demostrable.

Por tanto, W debe conseguir que la Home larga se sienta deliberada mientras exista, no fingir la arquitectura minimalista eliminando información.

## 9. Arquitectura de implementación preferida

Evitar meter toda la experiencia en `assets/v1-shell.js`.

Preferencia:

- `assets/v1-home.css` → composición, materialidad, estados visuales de Home;
- un JS **scoped a Home** para reveal/progreso/ruta si realmente hace falta;
- `assets/v1-shell.js` solo cuando la conducta sea genuinamente sitewide;
- View Transitions compartidas en la capa CSS común apropiada, con nombres asignados únicamente por las familias consumidoras;
- ningún framework, GSAP global, Lenis, WebGL o dependencia de runtime nueva para resolver este paquete.

Antes de crear un archivo nuevo, comprobar si una autoridad posterior de los siguientes bloques ya define nombre/ubicación canónica.

## 10. QA y criterios de aceptación

W no se considera cerrado hasta demostrar:

### Funcional / semántico

- enlaces del mapa siguen funcionando sin JS;
- teclado/focus conserva el contrato actual;
- no se modifica sitemap/schema/canonical/copy editorial por motivos visuales;
- ninguna pieza única de Home desaparece sin migración explícita.

### Responsive

Validar al menos contra la matriz global de #78, incluyendo 320, 390, tablet, desktop y landscape bajo.

### Reduced motion

Con `prefers-reduced-motion: reduce`:

- hero visible sin espera;
- rutas visibles sin dibujo animado;
- timeline usable;
- View Transitions reducidas/desactivadas;
- ninguna información desaparece.

### Performance

- no meter vídeo de fondo en hero/mapa;
- no añadir assets enormes por defecto;
- media secundaria del mapa se carga de forma compatible con prioridad real;
- LCP/CLS se mide antes/después;
- ningún nuevo recurso visual bloquea contenido crítico sin justificación.

### Visual review

Capturas/evidencia mínima:

- Home 1440;
- Home 390;
- Home 320;
- cartografía con varios estados hover/focus;
- reduced motion;
- transición soportada y fallback sin soporte.

No usar pixel-diff como criterio creativo absoluto. La revisión visual es humana, apoyada por QA estructural.

## 11. Dependencias / orden de integración

1. Resolver/integrar la arquitectura de navegación de **#68** antes de cerrar W.
2. Rebasar W sobre el HEAD acumulado y no restaurar shell antiguo.
3. Coordinar CSP con **#62** si aparecen nuevos assets/estilos/scripts.
4. Usar #61/#67 para las garantías de imágenes, no duplicarlas.
5. Ejecutar #78 como gate global de mobile/resiliencia sobre el diseño final.
6. Release final sigue perteneciendo a #1/#58; W no publica.

## 12. Definition of Done

W está cerrada cuando:

- Hero deja de ser una composición genérica sin caer en decorativismo;
- cartografía tiene profundidad visual/contextual y sigue siendo navegación semántica;
- rutas tienen entrada narrativa selectiva;
- móvil tiene una progresión visual opcional y usable;
- microinteracciones están acotadas;
- al menos las parejas Home→Manecillas y Home→Autor tienen continuidad progresiva cuando el navegador lo soporte;
- reduced motion/fallback son completos;
- no hay pérdida de contenido/SEO/findability;
- no se ha creado una segunda autoridad de navegación o media;
- responsive/a11y/performance quedan verificados sobre el HEAD final acumulado.

## 13. Estado de este bloque

`PENDIENTE DISEÑO GPT.txt` líneas **1–100: CERRADAS**.

No se ha leído ni clasificado la línea 101 en esta PR. El siguiente bloque empieza exactamente en **101**.
