# C.7 · Mapa / línea temporal visual del universo narrativo

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `CONDITIONAL`.  
Revalidación actual: la parte «mapa funcional de Noveris» está materialmente implementada en `/universo/noveris/`.

## Veredicto

#135 consideró un mapa/línea temporal un activo potencialmente valioso si es **canon, útil, accesible y editorialmente real**. Rechazó que una ilustración IA decorativa por «engagement» satisfaga la idea.

`main` ha evolucionado después: `/universo/noveris/` ya contiene un mapa funcional real con texto explicativo y contenido de arquitectura del mundo. Por tanto no crear otro mapa por cumplir C.7. La línea temporal u otros mapas siguen condicionados a necesidad/canon.

## Hipótesis original

Crear contenido visual —mapa o línea temporal— de los universos narrativos, reutilizable en redes y citable como recurso único.

## Evolución histórica

### Primera revisión → `CONDITIONAL`

- valor alto potencial;
- coste alto;
- debe ser canon;
- útil y accesible;
- prototipo + versión textual;
- no IA decorativa.

### Matriz intermedia → `PILOTAR`

La matriz preserva el mismo núcleo:

> mapa/línea temporal solo si se produce como recurso editorial real y útil; evitar IA decorativa genérica.

### Autoridad final → `CONDITIONAL`

> «Mapa/línea temporal solo como pieza editorial real, humana y útil; no ilustración IA decorativa para “engagement”.»

### Revalidación independiente

C.7 se mantuvo.

## Trigger histórico

Avanzar solo si existe:

- suficiente canon estable;
- necesidad real de orientación/comprensión;
- fuente de verdad del contenido;
- estrategia de spoilers;
- capacidad de producir visual de calidad;
- alternativa textual accesible;
- mantenimiento cuando el canon cambie.

No basta que «los mapas se comparten mucho».

## Qué debe resolver un mapa útil

Ejemplos:

- relaciones espaciales relevantes;
- rutas/zonas que el lector necesita situar;
- facciones/instituciones si la geografía ayuda a entenderlas;
- cronología compleja que el texto solo hace difícil de seguir.

La visualización debe responder una pregunta, no decorar la página.

## Accesibilidad

#135 exigía versión textual. Contrato recomendado:

- `alt` conciso con propósito;
- explicación adyacente de la información relevante;
- leyenda legible;
- contraste suficiente;
- no depender solo del color;
- orden lógico en móvil;
- zoom/reflow sin perder acceso;
- si la imagen contiene detalles no resumibles en `alt`, ofrecer descripción extendida en HTML.

## Spoilers

- declarar si el mapa es safe-before-reading;
- no revelar localizaciones/relaciones secretas accidentalmente;
- metadata/alt no debe filtrar lo que la UI oculta;
- línea temporal avanzada puede necesitar una versión separada o warnings.

## Revalidación actual de Noveris

`universo/noveris/index.html` ya contiene:

- `figure` «Mapa funcional»;
- imagen `mapa-funcional-noveris-ciudad-fantastica.webp`;
- alt que identifica Grimlor, Hospital Arcano, Archivos de la Memoria, estadio de Glíder y Barrera;
- texto visible «Cómo se organiza Noveris»;
- figcaption;
- contenido textual posterior que explica ciudad, instituciones, barrera, magia y canalizadores;
- integración con el hub canónico de Samuel/Noveris.

Eso cumple sustancialmente el trigger del mapa y evita abrir una segunda superficie.

## Relación con B.9

B.9 y C.7 ahora convergen en `/universo/noveris/`: el glosario explica términos; el mapa explica relaciones espaciales. Deben compartir canon, no crear dos taxonomías.

## Relación con A.2

El visual debe vivir en/enlazarse desde el hub canónico. No crear micrositio de universo sin necesidad.

## Relación con O/social

Puede reutilizarse una versión/crop en redes si derechos y legibilidad lo permiten. La reutilización social es secundaria; el master editorial no debe diseñarse solo para una red.

## Línea temporal

La parte «línea temporal» no queda automáticamente implementada por existir el mapa. Reabrir solo si:

- hay cronología suficientemente compleja;
- puede publicarse sin spoilers indebidos;
- aporta orientación;
- existe canon autorizado.

No crear timeline por simetría con el mapa.

## Qué NO hacer

- mapa IA genérico sin fidelidad canónica;
- inventar geografía para llenar huecos;
- texto ilegible incrustado como única fuente;
- imagen sin equivalente accesible;
- mapa enorme que dañe CWV sin optimización;
- duplicar `/universo/noveris/`;
- crear una URL por cada región/lugar sin sustancia;
- mezclar borradores privados con canon público.

## QA futuro

- canon revisado;
- alt + descripción larga cuando haga falta;
- dimensiones/responsive explícitos;
- formatos modernos según pipeline existente;
- no overflow a 320/390;
- lectura de texto sin imagen;
- links a entidades canónicas;
- metadata social deliberada si se reutiliza;
- no spoilers no anunciados.

## Pasadas posteriores revisadas

Cuarta–decimoquinta no cambian el estado C.7. Las pasadas de media/Discover refuerzan optimización y relevancia de imágenes, pero no justifican crear otra visualización.

## Trazabilidad

- hipótesis original;
- revisión `CONDITIONAL`;
- matriz `PILOTAR`;
- autoridad final `CONDITIONAL`;
- revalidación independiente;
- `universo/noveris/index.html` como evidencia actual de trigger cumplido para mapa.

## Recomendación para Clara/Claude

**No crear otro mapa de Noveris.** Mantener/mejorar el existente. Evaluar una línea temporal u otra visualización únicamente con una pregunta editorial real, canon estable y alternativa textual accesible.