# Banner art direction V5 — desktop + mobile

Este documento sustituye el contrato anterior de «una sola imagen 2400×900 para todos los viewports» en los banners panorámicos de Home.

## Por qué una sola imagen no funciona

Un banner corto de escritorio y un banner móvil cómodo tienen relaciones de aspecto incompatibles. Con `object-fit: cover`, una única imagen obliga a elegir entre:

- mostrarla completa y hacer el banner demasiado alto;
- mantener el banner bajo y recortar una parte importante;
- alejar el sujeto en desktop y verlo excesivamente cerca en móvil.

Por tanto, cada banner admite dos composiciones del mismo concepto.

## Formato desktop

- fichero maestro: **2400 × 600 px**;
- relación: **4:1**;
- WebP final;
- sin texto incrustado;
- cámara/encuadre abierto;
- sujeto o grupo principal dentro del **40 % central horizontal**;
- ningún elemento imprescindible en el 25 % exterior izquierdo ni derecho;
- sujeto principal ocupa aproximadamente **25–35 % del ancho** de la imagen;
- dejar fondo/arquitectura/pared/paisaje real a ambos lados, no estirar contenido artificialmente;
- dejar también aire vertical: no cortar coronillas, lomos, baldas, relojes, manos ni objetos clave.

Nombres:

- `assets/banners/manecillas-home-banner-desktop.webp`
- `assets/banners/samuel-home-banner-desktop.webp`
- `assets/banners/memoria-tierras-norte-home-banner-desktop.webp`
- `assets/banners/herramientas-home-banner-desktop.webp`

Altura de render:

- escritorio: `clamp(300px, 25vw, 400px)`;
- tablet: `clamp(230px, 30vw, 300px)`.

La imagen se renderiza con `cover` y foco central. El margen lateral amplio es parte de la composición, no un relleno posterior.

## Formato móvil

- fichero maestro: **1200 × 675 px**;
- relación: **16:9**;
- WebP final;
- misma escena, objetos y tono que desktop;
- recomponer, no recortar automáticamente el desktop;
- sujeto/grupo principal dentro del **60 % central horizontal**;
- sujeto principal ocupa aproximadamente **45–55 % del ancho**;
- debe verse algo de entorno a izquierda y derecha;
- evitar primeros planos y objetos tocando bordes;
- sin texto incrustado.

Nombres:

- `assets/banners/manecillas-home-banner-mobile.webp`
- `assets/banners/samuel-home-banner-mobile.webp`
- `assets/banners/memoria-tierras-norte-home-banner-mobile.webp`
- `assets/banners/herramientas-home-banner-mobile.webp`

Altura de render:

- hasta 599 px: `clamp(190px, 56vw, 240px)`;
- hasta 349 px: 185 px.

A 390 px de viewport el banner queda alrededor de 218 px de alto: panorámico, pero no un hero alto.

## Prompt base para generar la versión desktop

> Escena editorial fotográfica realista destinada a un banner web extremadamente panorámico y bajo, relación 4:1, 2400×600. Mantén el grupo principal centrado y relativamente pequeño, ocupando solo aproximadamente el 30 % del ancho total. Cámara más alejada, plano general, mucho entorno real y espacio negativo continuo a izquierda y derecha. Ningún objeto importante cerca de los bordes. El fondo debe continuar de forma natural hasta ambos extremos para permitir responsive y pequeños recortes. No primer plano, no zoom, no texto, no letras añadidas. El contenido esencial debe caber dentro del 40 % central horizontal y aproximadamente el 70 % central vertical.

Añadir después la descripción concreta de la escena y los objetos.

## Prompt base para generar la versión móvil

> Recompón exactamente la misma escena y los mismos objetos para un banner web móvil 16:9, 1200×675. No hagas un crop automático de la versión panorámica. Mantén el grupo principal centrado y todavía con aire alrededor, ocupando aproximadamente el 50 % del ancho, con fondo visible a ambos lados y por encima/debajo. Cámara a distancia media, no primer plano, no zoom, no objetos tocando los bordes, no texto. Conserva iluminación, materiales, proporciones, colores y posición relativa de los objetos de la versión desktop.

## Regla práctica de aprobación

Antes de aceptar una imagen:

1. A 1440×900 debe verse de borde a borde y el sujeto no debe parecer ampliado.
2. A 390×844 debe seguir viéndose entorno alrededor del sujeto.
3. Ningún elemento esencial puede depender de los extremos laterales.
4. Desktop y móvil deben parecer dos fotografías de la misma sesión, no dos diseños diferentes.
5. Si para que funcione hay que cambiar `object-position` más allá de un ajuste pequeño, la composición fuente está mal y debe regenerarse.

## Implementación

La capa `assets/v1-banner-art-direction-v5.css` se carga después de V4 y anula los `aspect-ratio` anteriores. Usa los ficheros desktop/mobile como capas art-directed. La imagen V4 existente queda debajo como fallback mientras los nuevos assets no existan.
