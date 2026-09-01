# Contrato de revisión en dispositivos reales · cadena DISEÑO · 2026-08-29

## 1. Motivo

Los QA de viewport, Playwright y WebKit son necesarios pero no sustituyen un navegador ejecutándose en hardware real. Safari/iOS aplica políticas y ciclos de vida propios a vídeo, autoplay, backgrounding, caché, safe areas, teclado virtual y elementos fixed/sticky que pueden no reproducirse en una emulación de escritorio.

Este documento pasa a formar parte de la Definition of Done de todas las PR de la cadena `DISEÑO - ...` iniciada en #163.

## 2. Matriz mínima manual antes del merge

### iPhone / Safari iOS — obligatorio

Comprobar en al menos un iPhone físico:

- carga inicial desde pestaña nueva;
- recarga normal y recarga tras cerrar/reabrir Safari;
- navegación adelante/atrás y restauración desde back-forward cache;
- orientación vertical y horizontal;
- scroll largo;
- navegación, menús y submenús;
- elementos `position:fixed` y `position:sticky`;
- notch/Dynamic Island y `env(safe-area-inset-*)`;
- formularios con teclado virtual abierto/cerrado;
- focus visible y controles táctiles;
- imágenes y lazy loading;
- vídeo, animaciones y transiciones;
- retorno desde background después de bloquear el teléfono o cambiar de app.

Cuando sea posible, repetir al menos una pasada en un segundo tamaño/modelo de iPhone o versión distinta de iOS.

### Vídeo / autoplay / motion

Para cualquier vídeo o intro animada verificar explícitamente:

- `muted`;
- `playsinline`;
- autoplay y resultado real de `HTMLMediaElement.play()`;
- poster/primer frame;
- fallback si Safari rechaza la reproducción;
- comportamiento al volver de background;
- Low Power Mode / ahorro de batería;
- ahorro de datos;
- `prefers-reduced-motion` / opción iOS «Reducir movimiento» activada y desactivada.

Un fallback accesible debe ser deliberado. Una animación congelada indefinidamente en el primer frame no cuenta como fallback correcto.

### Android / Chrome — recomendado y obligatorio antes de publicación global

Comprobar en hardware real, cuando esté disponible:

- carga y scroll;
- menús;
- sticky/fixed;
- teclado virtual;
- vídeo/animaciones;
- responsive y densidad de pantalla.

### Tablet

Cuando la página tenga composición específica de tablet o seams relevantes, comprobar un tablet real además de los viewports automatizados.

### Escritorio

Mantener Chrome + Firefox y, cuando haya acceso a macOS, Safari. Edge debe entrar al menos en la revisión de publicación global.

## 3. Incidencia real abierta: intro HOME en iPhone

Se ha reproducido en un iPhone físico un defecto que los QA automáticos no detectaron:

- la intro inicial de HOME muestra únicamente la imagen/primer frame;
- no se reproduce la tinta;
- no se ejecuta la transición esperada.

La incidencia pertenece a #163 (`DISEÑO - HOME`) y debe investigarse allí antes del merge de HOME.

Revisar como mínimo:

1. atributos reales del `<video>` y sources compatibles con Safari;
2. `muted`, `playsinline`, autoplay y promesa devuelta por `play()`;
3. si la intro depende de un evento (`canplay`, `loadeddata`, `playing`, `ended`, etc.) que Safari no alcanza en ese escenario;
4. preload/poster y primer frame;
5. fallback ante autoplay rechazado o vídeo no reproducible;
6. Low Power Mode / Data Saver;
7. `prefers-reduced-motion`;
8. lifecycle `pageshow/pagehide`, background y bfcache;
9. orientación y cambios de viewport;
10. consola remota de Safari/Web Inspector si está disponible.

No considerar la intro HOME certificada en iOS hasta que un iPhone físico reproduzca el flujo correcto o se implemente un fallback deliberado equivalente.

## 4. Cómo documentarlo en cada PR

Cada PR `DISEÑO - ...` debe incluir un apartado `Revisión real multi-dispositivo` con:

- dispositivos probados realmente;
- navegador y, si se conoce, versión de SO;
- incidencias encontradas;
- incidencias corregidas;
- comprobaciones que no se pudieron hacer y quedan para Claude/mantenedor;
- confirmación separada de iPhone/Safari cuando la superficie incluya vídeo, motion, sticky/fixed o formularios.

Los tests automáticos pueden cerrar geometría, overflow, accesibilidad programática y contratos funcionales. No deben utilizarse como prueba de que un comportamiento específico de Safari/iOS funciona en hardware real.

## 5. Definition of Done global

Una página se puede declarar `cerrada técnicamente` cuando sus gates y capturas automatizadas están limpios. Para declararla `lista para merge` debe existir además revisión humana y, cuando aplique, revisión en dispositivo real según este contrato.

Una incidencia reproducible en hardware real prevalece sobre un CI verde.